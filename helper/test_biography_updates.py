import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from biography_updates import checkpoint, make_memory, plan, load_memory
from history_view import process_views
from process_queue import load_results, write_results
from story_input import build_story_input
from test_history_view import record


class BiographyUpdateTests(unittest.TestCase):
    def setUp(self):
        self.records = [record(10, 0)]
        self.request = dict(unit_id=1, year=102, tick=10, nonce=1)
        self.payload = build_story_input(self.records[0]['snapshot']['identity'],
            [dict(kind='baseline', time=self.records[0]['ingame_time'], snapshot=self.records[0]['snapshot'])], None)
        self.previous = dict(story='Test ò valued the work. Perhaps it offered comfort.')
        self.memory = make_memory(self.payload, checkpoint(self.records, self.request),
                                  self.previous['story'], 'rebuild', None, {})

    def updated(self):
        payload = dict(self.payload, events=self.payload['events'] + [dict(kind='change',
            time=dict(year=102, year_tick=20), thoughts_added=[dict(thought_name='WitnessDeath', emotion_name='HORROR')])])
        return payload

    def test_continuation_separates_generated_prose_from_evidence(self):
        update = plan(self.memory, self.previous, self.updated(), self.records, dict(self.request, tick=20))
        self.assertEqual(update['mode'], 'append')
        self.assertEqual(update['payload']['prior_narrative']['text'], self.previous['story'])
        self.assertEqual(update['payload']['prior_narrative']['evidence_status'], 'generated_interpretation')
        self.assertNotIn('Perhaps', json.dumps(update['payload']['verified_context']))
        self.assertEqual(len(update['payload']['events']), 1)

    def test_changed_identity_and_enriched_names_rebuild(self):
        for payload in (dict(self.updated(), identity={'name': 'Corrected'}),
                        dict(self.updated(), biography_profile={'relationships': [{'kind': 'spouse'}]})):
            self.assertEqual(plan(self.memory, self.previous, payload, self.records, self.request)['mode'], 'rebuild')

    def test_rewinds_truncation_and_changed_records_do_not_append(self):
        for records, request in (([], self.request), ([record(10, 9)], self.request),
                                  (self.records, dict(self.request, tick=5)),
                                  (self.records + [record(5, 0)], self.request)):
            self.assertEqual(plan(self.memory, self.previous, self.updated(), records, request)['mode'], 'rebuild')

    def test_limits_consolidate_before_unbounded_growth(self):
        for memory, previous in ((dict(self.memory, continuations=4), self.previous),
                                  (self.memory, dict(story='é' * 2800))):
            self.assertEqual(plan(memory, previous, self.updated(), self.records, self.request)['reason'], 'consolidation_limit')

    def test_newly_discovered_old_event_is_not_a_continuation(self):
        payload = dict(self.updated(), historical_episodes={'events': [dict(source_key='event:1', kind='death', time={'year': 101})]})
        self.assertEqual(plan(self.memory, self.previous, payload, self.records, self.request)['reason'], 'newly_discovered_old_event')

    def test_continuation_requires_only_new_anchors(self):
        old_anchor = dict(event_id=1, sentence='Domas died.')
        new_anchor = dict(event_id=2, sentence='Urist created the Crown.')
        old = dict(self.payload, required_event_coverage=[old_anchor])
        memory = dict(self.memory, payload=old)
        payload = dict(self.updated(), required_event_coverage=[old_anchor, new_anchor])
        update = plan(memory, self.previous, payload, self.records, self.request)
        self.assertEqual(update['payload']['required_event_coverage'], [new_anchor])

    def test_changed_existing_episode_requires_revision(self):
        event = dict(source_key='history_event:1', kind='death', time={'year': 101}, name='Old')
        memory = dict(self.memory, payload=dict(self.payload, historical_episodes={'events': [event]}))
        payload = dict(self.updated(), historical_episodes={'events': [dict(event, name='Corrected')]})
        self.assertEqual(plan(memory, self.previous, payload, self.records, self.request)['mode'], 'rebuild')

    def test_sidecar_is_bound_to_published_prose(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'memory.json'
            write_results(path, self.memory)
            self.assertIsNotNone(load_memory(path, self.previous['story']))
            self.assertIsNone(load_memory(path, 'Another story'))

    @unittest.skipUnless(os.environ.get('LOREKEEPER_LIVE_BIOGRAPHY_TEST') == '1',
                         'Explicit opt-in required: invokes authenticated model twice')
    def test_live_model_initial_continuation_and_cache(self):
        """Synthetic isolated save, real process_views and authenticated model."""
        with tempfile.TemporaryDirectory() as root:
            save = Path(root); views = save/'lorekeeper-views'
            log = save/'lorekeeper-history.jsonl'
            first = record(10, 0)
            first['snapshot']['thoughts'] = [dict(thought_id=1, emotion_id=1,
                thought_name='SatisfiedAtWork', emotion_name='SATISFACTION')]
            log.write_text(json.dumps(first) + '\n')
            write_results(views/'1.request.json', self.request)
            process_views(save)
            initial = load_results(views/'1.json')
            self.assertEqual(initial['state'], 'ready', initial.get('error'))
            later = record(20, 0)
            later['snapshot']['thoughts'] = first['snapshot']['thoughts'] + [dict(thought_id=2,
                emotion_id=2, thought_name='WitnessDeath', emotion_name='HORROR')]
            with log.open('a') as file: file.write(json.dumps(later) + '\n')
            write_results(views/'1.request.json', dict(self.request, tick=20, nonce=2))
            process_views(save)
            continued = load_results(views/'1.json')
            self.assertEqual(continued['state'], 'ready', continued.get('error'))
            self.assertEqual(continued['biography_update']['mode'], 'append')
            self.assertTrue(continued['story'].startswith(initial['story'] + '\n\n'))
            write_results(views/'1.request.json', dict(self.request, tick=20, nonce=3))
            with patch('history_view.run_batch') as model:
                process_views(save)
                model.assert_not_called()
            print('Live memoire timing:', {'initial_seconds': initial['timings']['generation_seconds'],
                  'append_seconds': continued['timings']['generation_seconds']}, flush=True)

    def test_process_reuses_and_appends_then_preserves_success_on_failure(self):
        with tempfile.TemporaryDirectory() as root:
            save = Path(root); views = save/'lorekeeper-views'
            log = save/'lorekeeper-history.jsonl'
            log.write_text(json.dumps(record(10, 0)) + '\n')
            write_results(views/'1.request.json', self.request)
            with patch('history_view.run_batch', return_value={'results':[dict(text=self.previous['story'])]}) as model:
                process_views(save)
                write_results(views/'1.request.json', dict(self.request, nonce=2))
                process_views(save)
                self.assertEqual(model.call_count, 1)
            self.assertEqual(load_results(views/'1.json')['biography_update']['mode'], 'reuse')
            later = record(20, 0)
            later['snapshot']['thoughts'] = [dict(thought_id='WitnessDeath', emotion_id='HORROR')]
            with log.open('a') as file: file.write(json.dumps(later) + '\n')
            write_results(views/'1.request.json', dict(self.request, tick=20, nonce=3))
            def generate(items, **kwargs):
                raw = json.loads(items[0]['raw'])
                self.assertEqual(raw['prior_narrative']['text'], self.previous['story'])
                return {'results':[dict(text='Witnessing death later brought horror.') ]}
            with patch('history_view.run_batch', side_effect=generate): process_views(save)
            published = load_results(views/'1.json')
            self.assertEqual(published['biography_update']['mode'], 'append')
            self.assertEqual(published['story'], self.previous['story'] + '\n\nWitnessing death later brought horror.')
            before = (views/'1.biography-memory.json').read_bytes()
            third = record(30, 0)
            third['snapshot']['thoughts'] = later['snapshot']['thoughts'] + [dict(thought_id='UnexpectedDeath', emotion_id='SADNESS')]
            with log.open('a') as file: file.write(json.dumps(third) + '\n')
            write_results(views/'1.request.json', dict(self.request, tick=30, nonce=4))
            with patch('history_view.run_batch', side_effect=RuntimeError('offline')): process_views(save)
            self.assertEqual(load_results(views/'1.json')['story'], published['story'])
            self.assertEqual((views/'1.biography-memory.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
