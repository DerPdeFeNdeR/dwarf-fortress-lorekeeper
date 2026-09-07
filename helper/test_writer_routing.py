import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from codex_batch import prepare_batch, run_batch
from model_adapters import ModelResponse
from writer_settings import generation_settings, resolve_settings
import test_writing_brief as brief_fixtures
import test_anchored_chronicle as annual_fixtures
import test_monthly_biography as monthly_fixtures
from monthly_biography import read_json


class WriterRoutingTests(unittest.TestCase):
    def settings(self, profile, **overrides):
        with patch.dict(os.environ, {}, clear=True):
            return generation_settings(profile=profile, overrides=overrides)

    def test_models_have_distinct_prompts_and_schemas(self):
        item = brief_fixtures.WritingBriefTests().item()
        qwen = prepare_batch([item], self.settings('qwen-fast'))
        luna = prepare_batch([item], self.settings('luna-literary'))
        self.assertNotEqual(qwen.prompt, luna.prompt)
        self.assertNotEqual(qwen.schema, luna.schema)
        with patch('writing_strategies.build_brief', side_effect=AssertionError('Qwen path')):
            self.assertEqual(prepare_batch([item], self.settings('luna-literary')), luna)

    def test_cross_model_strategies_and_unregistered_models_are_rejected(self):
        for profile, strategies in [('luna-literary', {'memoire': 'personal-brief'}),
                ('luna-literary', {'chronicle': 'anchored'}),
                ('luna-literary', {'chronicle': 'compact'}),
                ('qwen-fast', {'memoire': 'luna-literary'})]:
            with self.subTest(profile=profile, strategies=strategies), self.assertRaises(ValueError):
                self.settings(profile, strategies=strategies)
        for profile in ('luna-fast', 'qwen-literary'):
            with self.assertRaises(ValueError):
                self.settings(profile)
        with self.assertRaises(ValueError):
            self.settings('qwen-fast', model='unknown-model')
        with self.assertRaises(ValueError):
            self.settings('qwen-fast', model='gpt-5.6-luna')

    def test_each_model_uses_only_its_own_annual_strategies(self):
        item = annual_fixtures.AnchoredChronicleTests().item()
        for profile, strategies in [('qwen-fast', ('anchored', 'compact')),
                                    ('qwen-weave', ('anchored-weave',)),
                                    ('luna-literary', ('luna-literary',))]:
            for strategy in strategies:
                with self.subTest(profile=profile, strategy=strategy):
                    settings = self.settings(profile, strategies={'chronicle': strategy})
                    if strategy == 'anchored':
                        payload = {'p0': '', 'p1': ''}
                    elif strategy == 'anchored-weave':
                        payload = {'p0': '{{A0}} {{A1}}', 'p1': '{{A0}}'}
                    else:
                        row = dict(id=item['id'], text='Urist died.')
                        if strategy == 'luna-literary':
                            row.update(explanation='Facts.', category='narrative', confidence='low')
                        payload = {'results': [row]}
                    adapter = Mock()
                    adapter.generate.return_value = ModelResponse(payload, {'test': True})
                    result = run_batch([item], settings=settings, adapter=adapter)
                    self.assertEqual(result['writing']['strategy'], strategy)
                    self.assertEqual(result['source'], settings['provider'])
                    self.assertEqual(result['generation'], settings)

    def test_codex_receives_strategy_schema_and_cleans_up_files(self):
        item = annual_fixtures.AnchoredChronicleTests().item()
        paths = []
        def runner(command, **kwargs):
            schema_path = Path(command[command.index('--output-schema')+1])
            paths.append(schema_path)
            schema = json.loads(schema_path.read_text())
            self.assertEqual(schema['required'], ['results'])
            self.assertIn(item['raw'], kwargs['input'].replace('\\"', '"'))
            self.assertNotIn('ONE short reflective sentence', kwargs['input'])
            self.assertIn('"low"', command[command.index('-c')+1])
            Path(command[command.index('-o')+1]).write_text(json.dumps({'results': [dict(
                id=item['id'], text='Urist died.', explanation='Facts.', category='narrative', confidence='high')]}))
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        result = run_batch([item], settings=self.settings('luna-literary'), runner=runner)
        self.assertIn('Urist died.', result['results'][0]['text'])
        self.assertTrue(all(not path.exists() for path in paths))

    def test_strategy_and_model_tuning_have_separate_effects_and_cache_identity(self):
        base = self.settings('qwen-fast')
        item = brief_fixtures.WritingBriefTests().item()
        model_tuned = self.settings('qwen-fast', model_options={'temperature': 0.3})
        strategy_tuned = self.settings('qwen-fast', strategy_options={'memoire': {'quiet_words': [40, 70]}})
        self.assertNotEqual(base, model_tuned)
        self.assertEqual(prepare_batch([item], base), prepare_batch([item], model_tuned))
        self.assertNotEqual(prepare_batch([item], base), prepare_batch([item], strategy_tuned))
        self.assertIn('40-70 words', prepare_batch([item], strategy_tuned).prompt)
        self.assertEqual(resolve_settings(base), base)

    def test_invalid_combinations_fail_before_model_work(self):
        for overrides in ({'provider': 'missing'}, {'strategies': {'memoire': 'anchored'}},
                          {'model_options': {'num_ctx': -1}}, {'model_options': {'think': 'false'}},
                          {'strategy_options': {'memoire': {'quiet_words': [100, 20]}}}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.settings('qwen-fast', **overrides)
        with self.assertRaises(ValueError):
            self.settings('luna-literary', model_options={'temperature': 0.5})

    def test_custom_profile_and_environment_overrides_do_not_mutate_defaults(self):
        before = self.settings('qwen-fast')
        with tempfile.TemporaryDirectory() as root:
            config = Path(root)/'profiles.json'
            config.write_text(json.dumps({'profiles': {'experiment': {
                'provider': 'ollama', 'model': 'qwen3:8b',
                'strategies': {'memoire': 'personal-brief', 'chronicle': 'compact'}}}}))
            with patch.dict(os.environ, {'LOREKEEPER_WRITER_CONFIG': str(config),
                    'LOREKEEPER_WRITER_PROFILE': 'experiment', 'LOREKEEPER_MEMOIRE_STRATEGY': 'personal-brief'}, clear=True):
                chosen = generation_settings()
            self.assertEqual(chosen['model'], 'qwen3:8b')
            self.assertEqual(chosen['strategies'], {'memoire': 'personal-brief', 'chronicle': 'compact'})
        self.assertEqual(self.settings('qwen-fast'), before)

    def test_fallback_provenance_names_the_strategy_actually_used(self):
        item = dict(id='empty-anchors', kind='fortress_year', raw='{"events":[]}', context='Write.')
        prepared = prepare_batch([item], self.settings('qwen-fast'))
        self.assertEqual(prepared.strategy, 'compact')
        self.assertEqual(prepared.provenance()['strategy_version'], prepared.version)

    def test_strategy_change_invalidates_book_but_failure_preserves_written_revision(self):
        fixture = monthly_fixtures.MonthlyBiographyTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.state['generation'] = self.settings('qwen-fast')
        fixture.run_book()
        book_path = fixture.directory/'1.monthly-book.json'
        original = read_json(book_path)['chapters']['intro']['file']
        fixture.run_book()
        self.assertEqual(len(fixture.calls), 1)
        fixture.state['generation'] = self.settings('luna-literary')
        with patch.object(fixture, 'generate', side_effect=RuntimeError('Model unavailable')):
            with self.assertRaises(RuntimeError):
                fixture.run_book()
        self.assertEqual(read_json(book_path)['chapters']['intro']['file'], original)
        self.assertEqual(read_json(fixture.directory/original)['generation']['strategies']['memoire'], 'personal-brief')
        fixture.run_book()
        self.assertEqual(len(fixture.calls), 2)
        self.assertNotEqual(read_json(book_path)['chapters']['intro']['file'], original)
