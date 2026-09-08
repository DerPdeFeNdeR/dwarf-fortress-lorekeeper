import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from codex_batch import prepare_batch, run_batch
from model_adapters import ModelResponse
from writer_settings import generation_settings
import test_writing_brief as brief_fixtures
import test_anchored_chronicle as annual_fixtures
import test_monthly_biography as monthly_fixtures
from monthly_biography import read_json


class WriterRoutingTests(unittest.TestCase):
    def settings(self, profile, **overrides):
        with patch.dict(os.environ, {}, clear=True):
            return generation_settings(profile=profile, overrides=overrides)

    def test_qwen_thread_prepares_threaded_memoire_prompt(self):
        item = brief_fixtures.WritingBriefTests().item()
        prepared = prepare_batch([item], self.settings('qwen-thread'))
        self.assertEqual(prepared.strategy, 'personal-thread')
        self.assertIn('Continuity thread:', prepared.prompt)

    def test_strategy_and_model_rejections(self):
        for overrides in ({'strategies': {'memoire': 'personal-brief'}},
                          {'strategies': {'chronicle': 'compact'}},
                          {'model': 'qwen3:latest'},):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.settings('qwen-thread', **overrides)
        for profile in ('legacy-compact', 'legacy-thread', 'legacy-stream', 'qwen-thread-plus'):
            with self.assertRaises(ValueError):
                self.settings(profile)

    def test_chronicle_strategy_runs_and_records_stream_strategy(self):
        item = annual_fixtures.AnchoredChronicleTests().item()
        payload = {'text': 'An account mentions {{A0}}.'}
        adapter = Mock()
        adapter.generate.return_value = ModelResponse(payload, {'test': True})
        result = run_batch([item], settings=self.settings('qwen-thread', strategies={'chronicle': 'anchored-stream'}),
                           adapter=adapter)
        self.assertEqual(result['writing']['strategy'], 'anchored-stream')
        self.assertEqual(result['source'], 'ollama')
        self.assertEqual(result['generation'], self.settings('qwen-thread', strategies={'chronicle': 'anchored-stream'}))

    def test_strategy_and_model_tuning_have_separate_effects_and_cache_identity(self):
        base = self.settings('qwen-thread')
        item = brief_fixtures.WritingBriefTests().item()
        model_tuned = self.settings('qwen-thread', model_options={'temperature': 0.3})
        strategy_tuned = self.settings('qwen-thread', strategy_options={'memoire': {'quiet_words': [40, 70]}})
        self.assertNotEqual(base, model_tuned)
        self.assertNotEqual(base, strategy_tuned)
        self.assertEqual(prepare_batch([item], base), prepare_batch([item], model_tuned))
        self.assertNotEqual(prepare_batch([item], base), prepare_batch([item], strategy_tuned))
        self.assertIn('40-70 words', prepare_batch([item], strategy_tuned).prompt)

    def test_invalid_combinations_fail_before_model_work(self):
        for overrides in ({'provider': 'missing'}, {'strategies': {'memoire': 'anchored-stream'}},
                          {'model_options': {'num_ctx': -1}}, {'model_options': {'think': 'false'}},
                          {'strategy_options': {'memoire': {'quiet_words': [100, 20]}}}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.settings('qwen-thread', **overrides)

    def test_custom_profile_override_is_limited_to_qwen_thread(self):
        before = self.settings('qwen-thread')
        with tempfile.TemporaryDirectory() as root:
            config = Path(root)/'profiles.json'
            config.write_text(json.dumps({'profiles': {
                'qwen-thread': {
                    'model_options': {'temperature': 0.55},
                }
            }}), encoding='utf-8')
            with patch.dict(os.environ, {'LOREKEEPER_WRITER_CONFIG': str(config),
                                        'LOREKEEPER_WRITER_PROFILE': 'qwen-thread'}, clear=True):
                chosen = generation_settings()
            self.assertEqual(chosen['model_options']['temperature'], 0.55)
        self.assertEqual(self.settings('qwen-thread'), before)

    def test_fallback_provenance_names_the_strategy_actually_used(self):
        item = dict(id='empty-anchors', kind='fortress_year', raw='{"events":[]}', context='Write.')
        prepared = prepare_batch([item], self.settings('qwen-thread', strategies={'chronicle': 'anchored-stream'}))
        self.assertEqual(prepared.strategy, 'compact')
        self.assertEqual(prepared.provenance()['strategy_version'], prepared.version)

    def test_strategy_change_invalidates_book_but_failure_preserves_written_revision(self):
        fixture = monthly_fixtures.MonthlyBiographyTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.state['generation'] = self.settings('qwen-thread')
        fixture.run_book()
        book_path = fixture.directory/'1.monthly-book.json'
        original = read_json(book_path)['chapters']['intro']['file']
        fixture.run_book()
        self.assertEqual(len(fixture.calls), 1)
        fixture.state['generation'] = self.settings('qwen-thread', reasoning_effort='medium')
        with patch.object(fixture, 'generate', side_effect=RuntimeError('Model unavailable')):
            with self.assertRaises(RuntimeError):
                fixture.run_book()
        self.assertEqual(read_json(book_path)['chapters']['intro']['file'], original)
        self.assertEqual(read_json(fixture.directory/original)['generation']['strategies']['memoire'], 'personal-thread')
        fixture.run_book()
        self.assertEqual(len(fixture.calls), 2)
        self.assertNotEqual(read_json(book_path)['chapters']['intro']['file'], original)
