import json
import unittest
from unittest.mock import patch

from anchored_chronicle import assemble, paragraph_plan
from codex_batch import run_batch
from model_adapters import ModelResponse
from story_coverage import validate


class AnchoredChronicleTests(unittest.TestCase):
    def test_out_of_scope_reflection_is_omitted_without_losing_facts(self):
        item = self.item()
        raw = json.loads(item['raw'])
        raw['events'] = [{'participants': [{'name': 'Urist'}]}]
        item['raw'] = json.dumps(raw)
        for reflection in ('I wonder how Urist felt.', 'I think it was a slow death.'):
            result = assemble(item, {'p0': reflection, 'p1': ''})
            self.assertNotIn(reflection, result['results'][0]['text'])
            self.assertEqual(result['writing_diagnostics']['omitted_reflections'], ['p0'])
            validate(result['results'][0]['text'], raw['required_event_coverage'])

    def item(self):
        rows = [{'event_id': 1, 'sentence': 'In Slate, Urist died.', 'clauses': [['Urist died']]},
                {'event_id': 2, 'sentence': 'In Felsite, Doren created Bright Hope.', 'clauses': [['Doren created Bright Hope']]},
                {'event_id': 3, 'sentence': 'In Slate, Minkot died.', 'clauses': [['Minkot died']]}]
        return dict(id='year', kind='fortress_year', raw=json.dumps({'required_event_coverage': rows}))

    def test_assembly_retains_all_facts_even_when_reflections_are_empty(self):
        item = self.item()
        result = assemble(item, {'p0': '', 'p1': 'I find some comfort in an act of making.'})
        text = result['results'][0]['text']
        self.assertLess(text.index('Minkot died'), text.index('Doren created'))
        self.assertEqual(validate(text, json.loads(item['raw'])['required_event_coverage'])['checked_event_ids'], [1, 2, 3])
        self.assertEqual(len(text.split('\n\n')), 2)

    def test_wrong_plan_and_excessive_reflections_fail_without_partial_publication(self):
        for response in ({'p0': ''}, {'p0': '', 'p1': '', 'p2': ''},
                         {'p0': None, 'p1': ''}, {'p0': 'word ' * 46, 'p1': ''}):
            with self.subTest(response=response), self.assertRaises(ValueError):
                assemble(self.item(), response)

    def test_live_adapter_uses_fixed_plan_and_preserves_cache_envelope(self):
        with patch('model_adapters.OllamaAdapter.generate', return_value=ModelResponse({'p0': '', 'p1': ''}, {})) as generate:
            result = run_batch([self.item()], settings={'provider': 'ollama', 'model': 'qwen3:8b'})
        self.assertEqual(generate.call_args.kwargs['schema']['required'], ['p0', 'p1'])
        self.assertEqual(result['results'][0]['id'], 'year')
        self.assertEqual(result['source'], 'ollama')
