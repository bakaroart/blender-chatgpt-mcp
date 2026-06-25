from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender_addon"))

from blender_chatgpt_bridge.command_queue import CommandQueue
from blender_chatgpt_bridge.path_sandbox import SafePathResolver
from blender_chatgpt_bridge.protocol import BridgeError


class PathQueueTests(unittest.TestCase):
    def test_path_sandbox_rejects_escape_and_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resolver = SafePathResolver(root)
            target = resolver.resolve_new_file("nested/file.blend", create_directories=True)
            self.assertTrue(str(target).startswith(str(root.resolve())))
            target.write_text("exists", encoding="utf-8")
            with self.assertRaises(BridgeError) as ctx:
                resolver.resolve_new_file("nested/file.blend")
            self.assertEqual(ctx.exception.code, "TARGET_ALREADY_EXISTS")
            with self.assertRaises(BridgeError):
                resolver.resolve_new_file("../escape.blend")

    def test_queue_full_and_deduplication(self) -> None:
        queue = CommandQueue(max_size=1)
        first = queue.submit("req-1", "get_status", {}, False)
        duplicate = queue.submit("req-1", "get_status", {}, False)
        self.assertIs(first, duplicate)
        with self.assertRaises(BridgeError) as ctx:
            queue.submit("req-2", "get_status", {}, False)
        self.assertEqual(ctx.exception.code, "QUEUE_FULL")

    def test_queue_timeout_cancellation_prevents_execution(self) -> None:
        queue = CommandQueue(max_size=1)
        job = queue.submit("req-1", "create_primitive", {}, True)
        job.cancel_before_start()
        calls: list[str] = []
        queue.execute_pending(lambda operation, _args: calls.append(operation))
        self.assertEqual(calls, [])
        self.assertTrue(job.event.is_set())
        self.assertFalse(job.response["ok"])


if __name__ == "__main__":
    unittest.main()
