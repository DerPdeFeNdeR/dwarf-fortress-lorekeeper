import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from codex_batch import build_prompt, build_ollama_prompt, normalize_items, run_batch, generation_settings
from writer_settings import resolve_settings


class CodexBatchTests(unittest.TestCase):
    def test_worker_defaults_are_explicit_and_overridable(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = generation_settings()
            self.assertEqual(settings['model'], 'qwen3:8b')
            self.assertEqual(settings['strategies'], {'memoire': 'personal-brief', 'chronicle': 'anchored'})
            self.assertFalse(settings['model_options']['think'])
        with patch.dict(os.environ, LOREKEEPER_WRITER_PROFILE='luna-literary', LOREKEEPER_REASONING_EFFORT='medium'):
            self.assertEqual(generation_settings()['reasoning_effort'], 'medium')
        with patch.dict(os.environ, LOREKEEPER_MODEL=''):
            with self.assertRaises(ValueError): generation_settings()
        with patch.dict(os.environ, LOREKEEPER_REASONING_EFFORT='invalid'):
            with self.assertRaises(ValueError): generation_settings()
        with patch.dict(os.environ, LOREKEEPER_PROVIDER='invalid'):
            with self.assertRaises(ValueError): generation_settings()

    def test_normalize_deduplicates_equivalent_requests(self):
        items = [
            {"id": "a", "kind": "thought", "raw": "Talked"},
            {"id": "b", "kind": "thought", "raw": "Talked"},
            {"id": "c", "kind": "emotion", "raw": "FONDNESS"},
        ]
        normalized = normalize_items(items)
        self.assertEqual([item["id"] for item in normalized], ["a", "c"])

    def test_prompt_contains_only_structured_batch(self):
        prompt = build_prompt([{"id": "a", "kind": "thought", "raw": "Talked"}])
        self.assertIn('"raw": "Talked"', prompt)
        self.assertIn("Do not inspect, edit, or create files", prompt)

    def test_ollama_receives_direct_instructions_and_unchanged_evidence(self):
        prompt = build_ollama_prompt([dict(id='a', kind='dwarf_history',
            context='First instruction.\nSecond instruction.', raw='{"name":"Test ò"}')])
        self.assertIn('First instruction.\nSecond instruction.', prompt)
        self.assertIn('{"name":"Test ò"}', prompt)
        self.assertIn('profession supplies no personality', prompt)

    def test_run_batch_validates_and_wraps_results(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "codex-output.json"

            def fake_runner(command, **kwargs):
                self.assertEqual(command[command.index('--model') + 1], 'gpt-5.6-luna')
                self.assertEqual(command[command.index('-c') + 1], 'model_reasoning_effort="low"')
                output_path.write_text(
                    json.dumps(
                        {
                            "results": [
                                {
                                    "id": "a",
                                    "text": "Had a conversation",
                                    "explanation": "Social interaction.",
                                    "category": "social",
                                    "confidence": "high",
                                }
                            ]
                        }
                    )
                )
                command_output_path = Path(command[command.index("-o") + 1])
                command_output_path.write_text(output_path.read_text())
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = run_batch(
                [{"id": "a", "kind": "thought", "raw": "Talked"}],
                runner=fake_runner,
                settings=dict(model='gpt-5.6-luna', reasoning_effort='low'),
            )
            self.assertEqual(result["source"], "codex-cli")
            self.assertEqual(result['generation'], resolve_settings(dict(provider='codex-cli', model='gpt-5.6-luna', reasoning_effort='low')))
            self.assertEqual(result["results"][0]["id"], "a")

    def test_empty_batch_does_not_launch_codex(self):
        def fail_runner(*_args, **_kwargs):
            self.fail("Codex should not run for an empty batch")

        self.assertEqual(run_batch([], runner=fail_runner)["results"], [])

    def test_truncated_ollama_output_is_not_published(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'{"done":true,"done_reason":"length","response":"{}"}'
        with patch('model_adapters.urllib.request.urlopen', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                run_batch([dict(id='a', kind='thought', raw='Talked')],
                          settings=dict(provider='ollama', model='qwen3:8b'))

    def test_ollama_uses_structured_nonthinking_request(self):
        response = {"results": [{"id": "a", "text": "Had a conversation",
                                  "explanation": "Social interaction.",
                                  "category": "social", "confidence": "high"}]}
        http_response = MagicMock()
        http_response.__enter__.return_value = http_response
        http_response.read.return_value = json.dumps({"done": True, "done_reason": "stop", "response": json.dumps(response)}).encode()
        with patch('model_adapters.urllib.request.urlopen', return_value=http_response) as request:
            result = run_batch([{"id": "a", "kind": "thought", "raw": "Talked"}],
                               settings=dict(provider='ollama', model='qwen3:8b', reasoning_effort='low'))
        payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(payload['model'], 'qwen3:8b')
        self.assertFalse(payload['think'])
        self.assertFalse(payload['stream'])
        self.assertFalse(payload['truncate'])
        self.assertFalse(payload['shift'])
        self.assertEqual(payload['format']['properties']['results']['minItems'], 1)
        self.assertEqual(payload['format']['properties']['results']['maxItems'], 1)
        self.assertEqual(payload['format']['properties']['results']['items']['properties']['id']['enum'], ['a'])
        self.assertEqual(result['source'], 'ollama')


if __name__ == "__main__":
    unittest.main()
