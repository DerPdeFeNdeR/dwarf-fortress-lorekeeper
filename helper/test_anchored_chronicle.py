import json
import unittest
from unittest.mock import patch

from anchored_chronicle import assemble, assemble_weave, paragraph_plan, weave_brief, woven_prose_is_safe
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

    def test_weave_replaces_each_anchor_and_preserves_flow(self):
        item = self.item()
        result = assemble_weave(item, {'p0': 'The year turned strangely. {{A0}} I kept my thoughts to myself. {{A1}}',
                                       'p1': 'Then came the other news: {{A0}}'})
        text = result['results'][0]['text']
        self.assertNotIn('{{A', text)
        self.assertIn('The year turned strangely. In Slate, Urist died.', text)
        self.assertIn('In Felsite, Doren created Bright Hope.', text)
        self.assertEqual(result['writing_diagnostics']['strategy'], 'woven_verified_facts')

    def test_weave_rejects_missing_or_repeated_anchor(self):
        result = assemble_weave(self.item(), {'p0': 'A remembered year.', 'p1': '{{A0}}'})
        self.assertEqual(result['writing_diagnostics']['repaired_anchors'], 2)
        self.assertIn('In Slate, Urist died.', result['results'][0]['text'])
        with self.assertRaises(ValueError):
            assemble_weave(self.item(), {'p0': '{{A0}} {{A0}} {{A1}}', 'p1': '{{A0}}'})

    def test_weave_allows_subjective_color_but_rejects_invented_crowd_reactions(self):
        self.assertTrue(woven_prose_is_safe('I thought it was swift and strange.'))
        self.assertTrue(woven_prose_is_safe('No one saw it and no one cared.'))

    def test_weave_removes_repeated_refrain(self):
        result = assemble_weave(self.item(), {'p0': 'This was a curious year indeed. {{A0}}',
                                              'p1': 'This was a curious year indeed. {{A0}}'})
        self.assertEqual(result['writing_diagnostics']['removed_repeated_sentences'], 1)

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
