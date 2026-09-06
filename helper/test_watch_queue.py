import tempfile
import unittest
from pathlib import Path

from watch_queue import process_if_changed


class WatchQueueTests(unittest.TestCase):
    def test_processes_changed_queue_once(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = Path(directory) / "queue.jsonl"
            results = Path(directory) / "results.json"
            queue.write_text('{"id":"job"}\n')
            calls = []

            def fake_processor(queue_path, result_path):
                calls.append((queue_path, result_path))
                return 1

            count, state, error = process_if_changed(queue, results, None, fake_processor)
            self.assertEqual((count, error), (1, None))
            self.assertIsNotNone(state)
            self.assertEqual(len(calls), 1)

            count, next_state, error = process_if_changed(
                queue, results, state, fake_processor)
            self.assertEqual((count, next_state, error), (0, state, None))
            self.assertEqual(len(calls), 1)

    def test_retries_after_processing_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = Path(directory) / "queue.jsonl"
            results = Path(directory) / "results.json"
            queue.write_text('{"id":"job"}\n')

            def failing_processor(_queue_path, _result_path):
                raise ValueError("partial JSON")

            count, state, error = process_if_changed(queue, results, None, failing_processor)
            self.assertEqual((count, state), (0, None))
            self.assertIsInstance(error, ValueError)


if __name__ == "__main__":
    unittest.main()
