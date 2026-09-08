import copy
import json
import unittest
from unittest.mock import patch

from codex_batch import run_batch
from model_adapters import ModelResponse
from test_model_input import expand
from writing_brief import build_brief, build_threaded_brief, voice_guide, explicit_values
from evaluate_writing import annual_sections


class WritingBriefTests(unittest.TestCase):
    def test_value_direction_is_explicit_without_inventing_past_behavior(self):
        rows = explicit_values({'values': [{'name': 'TRADITION', 'strength': -48},
                                          {'name': 'COOPERATION', 'strength': 50}]})
        self.assertTrue(rows[0].startswith('disfavors tradition'))
        self.assertTrue(rows[1].startswith('favors cooperation'))
        self.assertTrue(all('not past behavior' in row for row in rows))

    def test_section_plan_assigns_all_events_and_anchors_once(self):
        raw = dict(events=[{'id': 1, 'time': {'tick': 50000}}, {'id': 2, 'time': {}}],
                   cultural_events=[{'source_key': 'incident:3', 'time': {'tick': 220000}}],
                   required_event_coverage=[{'event_id': key, 'sentence': 'Fact.'} for key in (1, 2, 'incident:3')])
        item = dict(id='year', kind='fortress_year', raw=json.dumps(raw))
        sections = [json.loads(row['raw']) for row in annual_sections(item)]
        self.assertEqual(len(sections), 3)
        self.assertEqual([e['id'] for s in sections for e in s['events']], [2, 1])
        self.assertEqual([r['event_id'] for s in sections for r in s['required_event_coverage']], [2, 1, 'incident:3'])
        raw['required_event_coverage'].append({'event_id': 'missing', 'sentence': 'Fact.'})
        with self.assertRaises(ValueError):
            annual_sections(dict(item, raw=json.dumps(raw)))

    def item(self, intro=False):
        return dict(id='monthly:1', kind='dwarf_history', context='Legacy instructions',
                    raw=json.dumps(dict(chapter_title='Introduction and recollections' if intro else 'Year 102 / Slate',
                        chapter_evidence={'heard': {'teller': 'Urist ò', 'year': 35}},
                        identity={'name': 'Minkot'}, prior_narrative={'text': 'Invented siege'},
                        previous_chapter='Invented occupation routine',
                        biography_profile={'emotions': [{'thought_name': 'Old memory'}],
                                           'references': [{'name': 'Urist ò'}], 'values': [{'name': 'HARMONY'}]},
                        required_event_coverage=[{'sentence': 'I heard a story from Urist ò.'}]),ensure_ascii=False))

    def test_month_excludes_other_months_and_generated_prose_preserves_evidence(self):
        item = self.item()
        before = copy.deepcopy(item)
        instructions, encoded = build_brief(item)
        brief = expand(json.loads(encoded))
        self.assertEqual(item, before)
        self.assertNotIn('Invented', encoded)
        self.assertNotIn('Old memory', encoded)
        self.assertEqual(brief['chapter_evidence'], json.loads(item['raw'])['chapter_evidence'])
        self.assertEqual(brief['required_facts'], ['I heard a story from Urist ò.'])
        self.assertEqual(brief['current_character_context']['references'], [])
        self.assertIn('exactly one paragraph', instructions)

    def test_thread_uses_only_current_draft_and_blocks_preference_as_event(self):
        item = self.item()
        instructions, encoded = build_threaded_brief(item)
        self.assertIn('Every month must earn its concrete details', instructions)
        self.assertIn('preference is never evidence', instructions)
        self.assertIn('Invented occupation routine', instructions)
        self.assertNotIn('Invented siege', instructions)

    def test_introduction_keeps_undated_memories(self):
        instructions, encoded = build_brief(self.item(True))
        self.assertIn('Old memory', encoded)
        self.assertIn('Do not date baseline memories', instructions)

    def test_voice_uses_supported_traits_not_profession_and_unknown_is_neutral(self):
        self.assertEqual(voice_guide({}), voice_guide({'profession': 'Soldier'}))
        guide = voice_guide({'personality_facets': {'HUMOR': 90},
                            'mental_attributes': {'attributes': {
                                'LINGUISTIC_ABILITY': {'relative_level': 'lower'},
                                'MEMORY': {'relative_level': 'higher'}}}})
        self.assertIn('Use short, plain, grammatical sentences.', guide)
        self.assertTrue(any('never add missing' in row for row in guide))

    def test_age_uses_dwarf_life_stages_and_separate_editorial_band(self):
        self.assertTrue(any('baby' in row and 'adult reasoning' in row
                            for row in voice_guide({'age': {'life_stage': 'baby'}})))
        self.assertTrue(any('young perspective' in row
                            for row in voice_guide({'age': {'life_stage': 'child'}})))
        child = voice_guide({'age': {'life_stage': 'child'}})
        self.assertTrue(any('Avoid adult abstractions' in row for row in child))
        self.assertTrue(any('grounded perspective' in row
                            for row in voice_guide({'age': {'life_stage': 'adult'}})))
        guide = voice_guide({'age': {'life_stage': 'adult', 'narrative_band': 'older_adult'}})
        self.assertTrue(any('older adult' in row for row in guide))
        self.assertFalse(any('elder life stage' in row.lower() for row in guide))

    def test_annual_narrator_brief_preserves_age_metadata(self):
        raw = dict(events=[], cultural_events=[], narrator={
            'status': 'selected', 'name': 'Doren', 'histfig_id': 7,
            'age': {'years': 80, 'life_stage': 'adult', 'narrative_band': 'older_adult'}},
                   required_event_coverage=[])
        _, encoded = build_brief(dict(kind='fortress_year', raw=json.dumps(raw)))
        brief = expand(json.loads(encoded))
        self.assertEqual(brief['narrator']['age']['life_stage'], 'adult')
        self.assertEqual(brief['narrator']['age']['narrative_band'], 'older_adult')

    def test_prose_schema_and_adapter_reject_wrong_ids_and_incomplete_fields(self):
        item = self.item()
        with patch('model_adapters.OllamaAdapter.generate', return_value=ModelResponse({'results': [{'id': item['id'], 'text': 'I heard a story.'}]}, {})) as generate:
            result = run_batch([item], settings={'provider': 'ollama', 'model': 'qwen3:8b'})
        schema = generate.call_args.kwargs['schema']['properties']['results']['items']
        self.assertEqual(set(schema['properties']), {'id', 'text'})
        self.assertEqual(result['results'][0]['confidence'], 'low')
        for response in ({'results': [{'id': 'wrong', 'text': 'Story'}]},
                         {'results': [{'id': item['id']}]}, {'results': []}):
            with self.subTest(response=response), patch('model_adapters.OllamaAdapter.generate', return_value=ModelResponse(response, {})):
                with self.assertRaises(ValueError):
                    run_batch([item], settings={'provider': 'ollama', 'model': 'qwen3:8b'})

    def test_annual_retains_every_event_and_required_fact_without_clause_alternatives(self):
        raw = dict(events=[{'id': 1, 'victim': 'Urist'}], cultural_events=[{'teller': 'Doren'}],
                   narrator={'status': 'selected', 'histfig_id': 7, 'name': 'Doren'},
                   required_event_coverage=[{'sentence': 'Urist died.', 'clauses': [['Urist died']]}])
        _, encoded = build_brief(dict(kind='fortress_year', raw=json.dumps(raw)))
        brief = expand(json.loads(encoded))
        self.assertEqual(brief['events'], raw['events'])
        self.assertEqual(brief['cultural_events'], raw['cultural_events'])
        self.assertEqual(brief['narrator']['histfig_id'], 7)
        self.assertEqual(brief['required_facts'], ['Urist died.'])
        self.assertNotIn('clauses', brief)
