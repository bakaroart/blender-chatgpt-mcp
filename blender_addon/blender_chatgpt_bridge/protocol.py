from __future__ import annotations

from dataclasses import dataclass
from typing import Any

BRIDGE_VERSION = "0.1.0"
PROTOCOL_VERSION = "1.0.0"
MAX_REQUEST_BYTES = 1024 * 1024
MAX_SCENE_OBJECTS = 500
MAX_MATERIAL_SLOTS = 32
MAX_PREVIEW_BYTES = 2 * 1024 * 1024

ERROR_CODES = {
    "AUTH_REQUIRED",
    "AUTH_INVALID",
    "REQUEST_TOO_LARGE",
    "INVALID_JSON",
    "INVALID_REQUEST",
    "UNSUPPORTED_OPERATION",
    "VALIDATION_ERROR",
    "QUEUE_FULL",
    "COMMAND_TIMEOUT",
    "BRIDGE_STOPPING",
    "OBJECT_NOT_FOUND",
    "OBJECT_NAME_CONFLICT",
    "MATERIAL_NOT_FOUND",
    "INVALID_OBJECT_TYPE",
    "CAMERA_NOT_FOUND",
    "PROJECT_ROOT_NOT_CONFIGURED",
    "PATH_OUTSIDE_PROJECT_ROOT",
    "TARGET_ALREADY_EXISTS",
    "RENDER_FAILED",
    "BLENDER_CONTEXT_ERROR",
    "PROTOCOL_VERSION_MISMATCH",
    "INTERNAL_ERROR",
}


@dataclass
class BridgeError(Exception):
    code: str
    message: str
    status: int = 400
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.code not in ERROR_CODES:
            self.code = "INTERNAL_ERROR"
        Exception.__init__(self, self.message)


def success_response(request_id: str, result: Any, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "request_id": request_id,
        "result": result,
        "warnings": warnings or [],
    }


def error_response(
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "request_id": request_id,
        "error": {
            "code": code if code in ERROR_CODES else "INTERNAL_ERROR",
            "message": message,
            "details": details or {},
        },
    }
