from __future__ import annotations

import os
import re
from pathlib import Path

from .protocol import BridgeError


class SafePathResolver:
    def __init__(self, project_root: str | os.PathLike[str] | None):
        if not project_root:
            raise BridgeError("PROJECT_ROOT_NOT_CONFIGURED", "Project root is not configured.", status=409)
        self.root = Path(project_root).expanduser().resolve()

    def resolve_new_file(self, relative_path: str, create_directories: bool = False, suffix: str = ".blend") -> Path:
        self._validate_relative_path(relative_path, suffix)
        target = (self.root / relative_path).resolve(strict=False)
        try:
            common = os.path.commonpath([str(self.root), str(target)])
        except ValueError as exc:
            raise BridgeError("PATH_OUTSIDE_PROJECT_ROOT", "Target path is outside the project root.", status=400) from exc
        if common != str(self.root):
            raise BridgeError("PATH_OUTSIDE_PROJECT_ROOT", "Target path is outside the project root.", status=400)
        if target.exists():
            raise BridgeError("TARGET_ALREADY_EXISTS", "Target file already exists.", status=409)
        parent = target.parent
        if not parent.exists():
            if create_directories:
                parent.mkdir(parents=True, exist_ok=True)
            else:
                raise BridgeError("INVALID_REQUEST", "Target parent directory does not exist.", status=400)
        return target

    @staticmethod
    def _validate_relative_path(relative_path: str, suffix: str) -> None:
        if not isinstance(relative_path, str) or not relative_path:
            raise BridgeError("VALIDATION_ERROR", "A relative path is required.", status=400)
        if "\0" in relative_path:
            raise BridgeError("VALIDATION_ERROR", "Path contains a null byte.", status=400)
        if Path(relative_path).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", relative_path):
            raise BridgeError("PATH_OUTSIDE_PROJECT_ROOT", "Absolute paths are not allowed.", status=400)
        parts = re.split(r"[\\/]+", relative_path)
        if any(part in ("", ".", "..") for part in parts):
            raise BridgeError("PATH_OUTSIDE_PROJECT_ROOT", "Path traversal is not allowed.", status=400)
        if not relative_path.lower().endswith(suffix):
            raise BridgeError("VALIDATION_ERROR", f"Path must end in {suffix}.", status=400)
