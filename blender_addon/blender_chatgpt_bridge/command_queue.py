from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from typing import Any, Callable

from .protocol import BridgeError, error_response, success_response


@dataclass
class CommandJob:
    request_id: str
    operation: str
    args: dict[str, Any]
    mutating: bool
    created_at: float = field(default_factory=time.monotonic)
    event: threading.Event = field(default_factory=threading.Event)
    started: bool = False
    canceled: bool = False
    response: dict[str, Any] | None = None

    def cancel_before_start(self) -> None:
        if not self.started:
            self.canceled = True

    def set_error(self, error: BridgeError) -> None:
        self.response = error_response(error.code, error.message, self.request_id, error.details)
        self.event.set()

    def set_result(self, result: Any) -> None:
        self.response = success_response(self.request_id, result)
        self.event.set()


class CommandQueue:
    def __init__(self, max_size: int = 100, dedupe_seconds: float = 300.0):
        self.max_size = max_size
        self.dedupe_seconds = dedupe_seconds
        self._queue: deque[CommandJob] = deque()
        self._inflight: dict[str, CommandJob] = {}
        self._completed: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()
        self._lock = threading.Lock()
        self._stopping = False

    @property
    def depth(self) -> int:
        with self._lock:
            return len(self._queue)

    def submit(self, request_id: str, operation: str, args: dict[str, Any], mutating: bool) -> CommandJob:
        with self._lock:
            self._prune_completed_locked()
            if request_id in self._completed:
                job = CommandJob(request_id, operation, args, mutating)
                job.response = self._completed[request_id][1]
                job.event.set()
                return job
            if request_id in self._inflight:
                return self._inflight[request_id]
            if self._stopping:
                raise BridgeError("BRIDGE_STOPPING", "Bridge is stopping.", status=503)
            if len(self._queue) >= self.max_size:
                raise BridgeError("QUEUE_FULL", "Command queue is full.", status=429)
            job = CommandJob(request_id, operation, args, mutating)
            self._queue.append(job)
            self._inflight[request_id] = job
            return job

    def execute_pending(self, dispatcher: Callable[[str, dict[str, Any]], Any], limit: int = 4) -> int:
        count = 0
        while count < limit:
            with self._lock:
                if not self._queue:
                    return count
                job = self._queue.popleft()
            if job.canceled:
                job.set_error(BridgeError("COMMAND_TIMEOUT", "Command timed out before execution.", status=504))
                self._finish(job)
                count += 1
                continue
            job.started = True
            try:
                result = dispatcher(job.operation, job.args)
                job.set_result(result)
            except BridgeError as exc:
                job.set_error(exc)
            except Exception as exc:  # noqa: BLE001 - sanitized at the bridge boundary.
                job.set_error(BridgeError("INTERNAL_ERROR", "Unexpected Blender operation failure.", status=500, details={"type": type(exc).__name__}))
            finally:
                self._finish(job)
                count += 1
        return count

    def shutdown(self) -> None:
        with self._lock:
            self._stopping = True
            jobs = list(self._queue) + list(self._inflight.values())
            self._queue.clear()
        for job in jobs:
            if not job.event.is_set():
                job.set_error(BridgeError("BRIDGE_STOPPING", "Bridge is stopping.", status=503))

    def _finish(self, job: CommandJob) -> None:
        with self._lock:
            self._inflight.pop(job.request_id, None)
            if job.response is not None:
                self._completed[job.request_id] = (time.monotonic(), job.response)
            self._prune_completed_locked()

    def _prune_completed_locked(self) -> None:
        cutoff = time.monotonic() - self.dedupe_seconds
        while self._completed and next(iter(self._completed.values()))[0] < cutoff:
            self._completed.popitem(last=False)
