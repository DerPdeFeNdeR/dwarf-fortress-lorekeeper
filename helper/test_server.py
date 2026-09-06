import json
import tempfile
import unittest
from pathlib import Path

from server import TranslationService


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.calls = []

        def fake_request(api_key, model, prompt):
            self.calls.append((api_key, model, json.loads(prompt)))
            return {
                "text": "Had a conversation",
                "explanation": "The dwarf experienced a social interaction.",
                "category": "social",
                "confidence": "high",
            }

        self.service = TranslationService(
            cache_path=Path(self.directory.name) / "cache.json",
            api_key="test-key",
            request_fn=fake_request,
        )

    def tearDown(self):
        self.directory.cleanup()

    def test_first_request_calls_model_and_persists_result(self):
        result, cached = self.service.translate(
            {"kind": "thought", "raw": "Talked", "context": "emotion=FONDNESS"}
        )
        self.assertFalse(cached)
        self.assertEqual(result["source"], "model")
        self.assertEqual(result["cache"], "miss")
        self.assertEqual(len(self.calls), 1)

        second_service = TranslationService(
            cache_path=self.service.cache_path,
            api_key="test-key",
            request_fn=lambda *_: self.fail("cache miss unexpectedly called model"),
        )
        cached_result, was_cached = second_service.translate(
            {"kind": "thought", "raw": "Talked", "context": "emotion=FONDNESS"}
        )
        self.assertTrue(was_cached)
        self.assertEqual(cached_result["cache"], "hit")

    def test_different_context_has_different_cache_entry(self):
        self.service.translate({"kind": "thought", "raw": "Talked", "context": "A"})
        self.service.translate({"kind": "thought", "raw": "Talked", "context": "B"})
        self.assertEqual(len(self.calls), 2)

    def test_missing_api_key_is_offline_safe(self):
        service = TranslationService(
            cache_path=Path(self.directory.name) / "offline.json",
            api_key="",
        )
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            service.translate({"kind": "thought", "raw": "Talked"})

    def test_input_limits_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "raw"):
            self.service.translate({"kind": "thought", "raw": "x" * 513})


if __name__ == "__main__":
    unittest.main()
