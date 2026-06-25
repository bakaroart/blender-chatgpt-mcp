from __future__ import annotations

import math
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender_addon"))

from blender_chatgpt_bridge.protocol import BridgeError
from blender_chatgpt_bridge.security import extract_bearer_token, generate_token, token_matches
from blender_chatgpt_bridge.validation import validate_operation_args, validate_request_envelope


class SecurityValidationTests(unittest.TestCase):
    def test_token_generation_and_compare(self) -> None:
        token = generate_token()
        self.assertGreaterEqual(len(token), 43)
        self.assertTrue(token_matches(token, token))
        self.assertFalse(token_matches(token, token + "x"))
        self.assertEqual(extract_bearer_token(f"Bearer {token}"), token)

    def test_request_envelope_rejects_unknown_operation(self) -> None:
        with self.assertRaises(BridgeError) as ctx:
            validate_request_envelope({"request_id": str(uuid.uuid4()), "operation": "execute_python", "args": {}})
        self.assertEqual(ctx.exception.code, "UNSUPPORTED_OPERATION")

    def test_rejects_nan_and_bad_delete_selectors(self) -> None:
        with self.assertRaises(BridgeError):
            validate_request_envelope({"request_id": str(uuid.uuid4()), "operation": "set_transform", "args": {"name": "Cube", "location": [math.nan, 0, 0]}})
        with self.assertRaises(BridgeError):
            validate_operation_args("delete_objects", {"names": ["Cube*"]})

    def test_render_and_save_validation(self) -> None:
        with self.assertRaises(BridgeError):
            validate_operation_args("render_preview", {"width": 1024, "height": 1025})
        with self.assertRaises(BridgeError):
            validate_operation_args("save_copy", {"relative_path": "../scene.blend"})
        self.assertEqual(validate_operation_args("save_copy", {"relative_path": "scene.blend"})["relative_path"], "scene.blend")


if __name__ == "__main__":
    unittest.main()
