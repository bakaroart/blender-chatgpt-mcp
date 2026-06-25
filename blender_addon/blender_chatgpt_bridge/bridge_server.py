from __future__ import annotations

import json
import shutil
import tempfile
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .command_queue import CommandQueue
from .dispatcher import BridgeContext, dispatch, is_mutating
from .path_sandbox import SafePathResolver
from .protocol import BRIDGE_VERSION, MAX_REQUEST_BYTES, PROTOCOL_VERSION, BridgeError, error_response
from .security import extract_bearer_token, is_valid_bridge_bind, token_matches
from .validation import validate_request_envelope


def _bpy() -> Any:
    import bpy

    return bpy


ERROR_HTTP_STATUS = {
    "AUTH_REQUIRED": 401,
    "AUTH_INVALID": 401,
    "REQUEST_TOO_LARGE": 413,
    "INVALID_JSON": 400,
    "INVALID_REQUEST": 400,
    "UNSUPPORTED_OPERATION": 400,
    "VALIDATION_ERROR": 400,
    "QUEUE_FULL": 429,
    "COMMAND_TIMEOUT": 504,
    "BRIDGE_STOPPING": 503,
    "OBJECT_NOT_FOUND": 409,
    "OBJECT_NAME_CONFLICT": 409,
    "MATERIAL_NOT_FOUND": 409,
    "INVALID_OBJECT_TYPE": 409,
    "CAMERA_NOT_FOUND": 409,
    "PROJECT_ROOT_NOT_CONFIGURED": 409,
    "PATH_OUTSIDE_PROJECT_ROOT": 400,
    "TARGET_ALREADY_EXISTS": 409,
    "RENDER_FAILED": 500,
    "BLENDER_CONTEXT_ERROR": 500,
    "PROTOCOL_VERSION_MISMATCH": 400,
    "INTERNAL_ERROR": 500,
}


class LocalHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], handler: type[BaseHTTPRequestHandler], controller: "BridgeController"):
        super().__init__(server_address, handler)
        self.controller = controller


class BridgeController:
    def __init__(
        self,
        port: int,
        token: str,
        project_root: str | None,
        normal_timeout: float,
        render_timeout: float,
        audit_log_path: str | None = None,
    ):
        self.host = "127.0.0.1"
        self.port = int(port)
        self.token = token
        self.project_root = project_root or None
        self.normal_timeout = float(normal_timeout)
        self.render_timeout = float(render_timeout)
        self.status = "stopped"
        self.last_error: str | None = None
        self.queue = CommandQueue(max_size=100)
        self.temp_dir = tempfile.mkdtemp(prefix="blender-mcp-preview-")
        self.blender_version = _bpy().app.version_string
        self.context = BridgeContext(self.project_root, self.temp_dir, self.normal_timeout, self.render_timeout)
        self.server: LocalHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.audit_log_path = self._resolve_audit_log(audit_log_path)

    def start(self) -> None:
        if self.status == "running":
            return
        if not is_valid_bridge_bind(self.host):
            raise BridgeError("INVALID_REQUEST", "Bridge must bind to 127.0.0.1.", status=400)
        if not self.token:
            raise BridgeError("AUTH_REQUIRED", "Bridge token is not configured.", status=401)
        self.status = "starting"
        self.server = LocalHTTPServer((self.host, self.port), BridgeRequestHandler, self)
        self.thread = threading.Thread(target=self.server.serve_forever, name="BlenderMCPBridgeHTTP", daemon=True)
        self.thread.start()
        self.status = "running"
        self._ensure_timer()

    def stop(self) -> None:
        self.status = "stopping"
        self.queue.shutdown()
        server = self.server
        self.server = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        self.thread = None
        self._unregister_timer()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.status = "stopped"

    def status_payload(self) -> dict[str, Any]:
        return {
            "ok": self.status == "running",
            "bridge_version": BRIDGE_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "blender_version": self.blender_version,
            "status": self.status,
            "bind_address": self.host,
            "port": self.port,
            "project_root_configured": bool(self.project_root),
            "queue_depth": self.queue.depth,
            "last_error": self.last_error,
        }

    def execute_pending(self) -> int:
        return self.queue.execute_pending(lambda operation, args: dispatch(operation, args, self.context))

    def audit(self, request_id: str | None, operation: str | None, duration_ms: int, success: bool, error_code: str | None = None) -> None:
        if not self.audit_log_path:
            return
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "request_id": request_id,
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "error_code": error_code,
        }
        try:
            with self.audit_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, separators=(",", ":")) + "\n")
        except OSError as exc:
            self.last_error = f"audit_log_failed:{type(exc).__name__}"

    def _resolve_audit_log(self, audit_log_path: str | None) -> Path | None:
        if not audit_log_path:
            return None
        if not self.project_root:
            raise BridgeError("PROJECT_ROOT_NOT_CONFIGURED", "Audit log requires a configured project root.", status=409)
        resolver = SafePathResolver(self.project_root)
        target = resolver.root / audit_log_path
        SafePathResolver._validate_relative_path(audit_log_path, ".jsonl")
        resolved = target.resolve(strict=False)
        if not str(resolved).startswith(str(resolver.root)):
            raise BridgeError("PATH_OUTSIDE_PROJECT_ROOT", "Audit log path is outside the project root.", status=400)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved

    def _ensure_timer(self) -> None:
        bpy = _bpy()
        if not bpy.app.timers.is_registered(_timer_tick):
            bpy.app.timers.register(_timer_tick, first_interval=0.05, persistent=True)

    def _unregister_timer(self) -> None:
        bpy = _bpy()
        if bpy.app.timers.is_registered(_timer_tick):
            bpy.app.timers.unregister(_timer_tick)


class BridgeRequestHandler(BaseHTTPRequestHandler):
    server: LocalHTTPServer

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._json(200, {"ok": True, "bridge_version": BRIDGE_VERSION, "blender_version": self.server.controller.blender_version, "status": self.server.controller.status})
            return
        if self.path == "/v1/status":
            if not self._authenticated():
                return
            self._json(200, self.server.controller.status_payload())
            return
        self._json(404, error_response("INVALID_REQUEST", "Endpoint not found."))

    def do_POST(self) -> None:
        if self.path != "/v1/commands":
            self._json(404, error_response("INVALID_REQUEST", "Endpoint not found."))
            return
        controller = self.server.controller
        started = time.monotonic()
        request_id = None
        operation = None
        try:
            if not self._authenticated():
                return
            payload = self._read_json()
            request_id, operation, args = validate_request_envelope(payload)
            job = controller.queue.submit(request_id, operation, args, is_mutating(operation))
            timeout = controller.render_timeout if operation == "render_preview" else controller.normal_timeout
            if not job.event.wait(timeout):
                job.cancel_before_start()
                raise BridgeError("COMMAND_TIMEOUT", "Command timed out.", status=504)
            response = job.response or error_response("INTERNAL_ERROR", "Command did not produce a result.", request_id)
            status = 200 if response.get("ok") else ERROR_HTTP_STATUS.get(response["error"]["code"], 500)
            controller.audit(request_id, operation, int((time.monotonic() - started) * 1000), bool(response.get("ok")), None if response.get("ok") else response["error"]["code"])
            self._json(status, response)
        except BridgeError as exc:
            controller.last_error = exc.code
            controller.audit(request_id, operation, int((time.monotonic() - started) * 1000), False, exc.code)
            self._json(exc.status, error_response(exc.code, exc.message, request_id, exc.details))
        except Exception as exc:  # noqa: BLE001 - external response is sanitized.
            controller.last_error = type(exc).__name__
            controller.audit(request_id, operation, int((time.monotonic() - started) * 1000), False, "INTERNAL_ERROR")
            self._json(500, error_response("INTERNAL_ERROR", "Unexpected bridge failure.", request_id))

    def _authenticated(self) -> bool:
        token = extract_bearer_token(self.headers.get("Authorization"))
        expected = self.server.controller.token
        if not token:
            self._json(401, error_response("AUTH_REQUIRED", "Authentication is required."))
            return False
        if not token_matches(expected, token):
            self._json(401, error_response("AUTH_INVALID", "Authentication failed."))
            return False
        return True

    def _read_json(self) -> Any:
        content_length_raw = self.headers.get("Content-Length")
        if content_length_raw is None:
            raise BridgeError("INVALID_REQUEST", "Content-Length is required.", status=400)
        try:
            content_length = int(content_length_raw)
        except ValueError as exc:
            raise BridgeError("INVALID_REQUEST", "Content-Length is invalid.", status=400) from exc
        if content_length > MAX_REQUEST_BYTES:
            raise BridgeError("REQUEST_TOO_LARGE", "Request body exceeds 1 MB.", status=413)
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise BridgeError("INVALID_JSON", "Request body must be UTF-8 JSON.", status=400) from exc
        except json.JSONDecodeError as exc:
            raise BridgeError("INVALID_JSON", "Request body is not valid JSON.", status=400) from exc

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


_controller: BridgeController | None = None


def start_bridge(port: int, token: str, project_root: str | None, normal_timeout: float, render_timeout: float, audit_log_path: str | None = None) -> BridgeController:
    global _controller
    if _controller and _controller.status in {"starting", "running"}:
        return _controller
    _controller = BridgeController(port, token, project_root, normal_timeout, render_timeout, audit_log_path)
    _controller.start()
    return _controller


def stop_bridge() -> None:
    global _controller
    if _controller is not None:
        _controller.stop()
    _controller = None


def get_status() -> dict[str, Any]:
    if _controller is None:
        return {"status": "stopped", "queue_depth": 0, "last_error": None}
    return _controller.status_payload()


def _timer_tick() -> float | None:
    if _controller is None or _controller.status not in {"starting", "running"}:
        return None
    _controller.execute_pending()
    return 0.05
