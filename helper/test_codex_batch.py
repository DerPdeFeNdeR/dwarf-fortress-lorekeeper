import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from codex_batch import build_prompt, normalize_items, run_batch, generation_settings


class CodexBatchTests(unittest.TestCase):
    def test_worker_defaults_are_explicit_and_overridable(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(generation_settings(), dict(model='gpt-5.6-luna', reasoning_effort='low'))
        with patch.dict(os.environ, LOREKEEPER_MODEL='gpt-5.6-luna', LOREKEEPER_REASONING_EFFORT='medium'):
            self.assertEqual(generation_settings()['reasoning_effort'], 'medium')
        with patch.dict(os.environ, LOREKEEPER_MODEL=''):
            with self.assertRaises(ValueError): generation_settings()
        with patch.dict(os.environ, LOREKEEPER_REASONING_EFFORT='invalid'):
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
            self.assertEqual(result['generation'], dict(model='gpt-5.6-luna', reasoning_effort='low'))
            self.assertEqual(result["results"][0]["id"], "a")

    def test_empty_batch_does_not_launch_codex(self):
        def fail_runner(*_args, **_kwargs):
            self.fail("Codex should not run for an empty batch")

        self.assertEqual(run_batch([], runner=fail_runner)["results"], [])


if __name__ == "__main__":
    unittest.main()
