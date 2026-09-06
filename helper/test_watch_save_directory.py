import tempfile
import unittest
from pathlib import Path

from watch_save_directory import process_directory_once


class SaveDirectoryWatcherTests(unittest.TestCase):
    def test_processes_queues_in_multiple_save_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            save_root = Path(directory)
            first_queue = save_root / "region1" / "lorekeeper-translation-queue.jsonl"
            second_queue = save_root / "region2" / "lorekeeper-translation-queue.jsonl"
            first_queue.parent.mkdir()
            second_queue.parent.mkdir()
            first_queue.write_text('{"id":"first"}\n')
            second_queue.write_text('{"id":"second"}\n')
            calls = []

            def fake_processor(queue_path, result_path):
                calls.append((queue_path, result_path))
                return 1

            count, states, errors = process_directory_once(save_root, {}, fake_processor)
            self.assertEqual(count, 2)
            self.assertEqual(errors, [])
            self.assertEqual(len(states), 2)
            self.assertEqual(len(calls), 2)

            count, states, errors = process_directory_once(save_root, states, fake_processor)
            self.assertEqual((count, errors), (0, []))
            self.assertEqual(len(states), 2)
            self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
