import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from process_queue import load_results, process_queue, write_results


class QueueTests(unittest.TestCase):
    def test_processes_only_uncached_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = root / 'queue.jsonl'
            results = root / 'results.json'
            queue.write_text(
                '\n'.join([
                    json.dumps({'id': 'a', 'kind': 'thought', 'raw': 'Talked'}),
                    json.dumps({'id': 'b', 'kind': 'thought', 'raw': 'SatisfiedAtWork'}),
                ]) + '\n'
            )
            results.write_text(json.dumps({'a': {'text': 'cached'}}))

            with patch('process_queue.run_batch') as run_batch:
                run_batch.return_value = {
                    'results': [{'id': 'b', 'text': 'Satisfied', 'explanation': 'Work',
                                 'category': 'work', 'confidence': 'high'}]
                }
                self.assertEqual(process_queue(queue, results), 1)
                run_batch.assert_called_once()
                self.assertEqual(run_batch.call_args.args[0][0]['id'], 'b')

            data = json.loads(results.read_text())
            self.assertEqual(data['a']['text'], 'cached')
            self.assertEqual(data['b']['text'], 'Satisfied')

    def test_empty_or_fully_cached_queue_does_not_call_codex(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = root / 'queue.jsonl'
            results = root / 'results.json'
            queue.write_text('')
            with patch('process_queue.run_batch') as run_batch:
                self.assertEqual(process_queue(queue, results), 0)
                run_batch.assert_not_called()

    def test_reads_dfhack_cp437_queue_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = root / 'queue.jsonl'
            results = root / 'results.json'
            queue.write_bytes(
                (json.dumps({'id': 'a', 'kind': 'dwarf_summary',
                             'raw': 'Eral èrithbomrek'}) + '\n').encode('cp437')
            )

            with patch('process_queue.run_batch') as run_batch:
                run_batch.return_value = {
                    'results': [{'id': 'a', 'text': 'Summary', 'explanation': 'Context',
                                 'category': 'dwarf', 'confidence': 'high'}]
                }
                self.assertEqual(process_queue(queue, results), 1)
                self.assertEqual(run_batch.call_args.args[0][0]['raw'], 'Eral èrithbomrek')

    def test_writes_cache_in_dfhack_cp437_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'results.json'
            write_results(path, {'a': {'text': 'Eral èrithbomrek'}})
            self.assertEqual(load_results(path)['a']['text'], 'Eral èrithbomrek')
            self.assertNotIn(b'\xc3\xa8', path.read_bytes())
            self.assertIn(b'\\u00e8', path.read_bytes())


if __name__ == '__main__':
    unittest.main()
