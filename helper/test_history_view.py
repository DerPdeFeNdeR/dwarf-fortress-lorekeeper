import json
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch
from history_view import VIEW_SCHEMA_VERSION, build_timeline, process_views, load_profile, profile_revision
from process_queue import load_queue, load_results, process_queue, write_results
from codex_batch import run_process
from worker_runtime import worker_runtime
from historian import HISTORIAN_CONTEXT, STORY_NOTICE, narrative_events, restore_reference_names
from story_input import compact_profile, build_story_input, story_key


def record(tick, stress):
    return dict(record_type='dwarf_snapshot', ingame_time=dict(year=102,year_tick=tick),
                snapshot=dict(identity=dict(id=1,name='Test ò',profession='Miner'),
                              mental_state=dict(stress=stress),thoughts=[],personality_facets=[]))


class HistoryViewTests(unittest.TestCase):
    def test_historian_keeps_writing_process_commentary_out_of_narrative(self):
        self.assertIn('never comment on the writing process', HISTORIAN_CONTEXT)
        self.assertIn('do not explain that omission', HISTORIAN_CONTEXT)
    def test_reference_names_restore_accents_without_guessing_ambiguous_names(self):
        profile = dict(figures=[dict(name='Tirist Sobìrrith')])
        self.assertEqual(restore_reference_names('Tirist Sobîrrith smiled.', profile),
                         'Tirist Sobìrrith smiled.')
        profile['figures'].append(dict(name='Tirist Sobírrith'))
        self.assertEqual(restore_reference_names('Tirist Sobîrrith smiled.', profile),
                         'Tirist Sobîrrith smiled.')
    def test_profile_reader_is_bounded_and_checks_identity(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            request = dict(unit_id=1, profile_file='1.profile.json')
            write_results(directory / request['profile_file'], dict(unit_id=1))
            self.assertEqual(load_profile(directory, request)['unit_id'], 1)
            with self.assertRaises(ValueError):
                load_profile(directory, dict(unit_id=2, profile_file=request['profile_file']))
            with self.assertRaises(ValueError):
                load_profile(directory, dict(unit_id=1, profile_file='../1.profile.json'))
            (directory / request['profile_file']).write_bytes(b' ' * 131073)
            with self.assertRaises(ValueError):
                load_profile(directory, request)

    def test_profile_revision_ignores_capture_time_but_not_relationships(self):
        a = dict(unit_id=1, captured_at=dict(tick=1), relationships=[])
        b = dict(a, captured_at=dict(tick=2))
        self.assertEqual(profile_revision('base', a), profile_revision('base', b))
        b['relationships'] = [dict(target_hf=7068, kind='spousest')]
        self.assertNotEqual(profile_revision('base', a), profile_revision('base', b))

    def test_profile_reaches_model_with_resolved_spouse_context(self):
        with tempfile.TemporaryDirectory() as root:
            save = Path(root)
            views = save / 'lorekeeper-views'
            profile = dict(unit_id=1, figures=[dict(id=7068, name='Momuz Lilumuzol')],
                           relationships=[dict(target_hf=7068, kind='histfig_hf_link_spousest')])
            write_results(views / '1.profile.json', profile)
            write_results(views / '1.request.json', dict(unit_id=1, profile_file='1.profile.json'))
            (save / 'lorekeeper-history.jsonl').write_text(json.dumps(record(1, 0)) + '\n')
            def generate(items, **kwargs):
                self.assertEqual(json.loads(items[0]['raw'])['biography_profile'], compact_profile(profile))
                return {'results': [dict(id=items[0]['id'], text='A biography.') ]}
            with patch('history_view.run_batch', side_effect=generate):
                process_views(save)
            self.assertEqual(load_results(views / '1.json')['state'], 'ready')
    def test_historian_contract_preserves_tone_and_factual_boundaries(self):
        for instruction in ('one consistent', 'dry wit', 'gravity and compassion',
                            'Preserve Unicode names exactly', 'Never invent dialogue',
                            'baseline parenthood', 'removed thought',
                            'explanation field, not text', 'latest recorded segment',
                            'may imagine plausible internal motives',
                            'Never present\nan imagined motive as a game-confirmed fact'):
            self.assertIn(instruction, HISTORIAN_CONTEXT)

    def test_process_timeout_is_bounded(self):
        with self.assertRaisesRegex(RuntimeError, 'time limit'):
            run_process([sys.executable, '-c', 'import time; time.sleep(5)'],
                        input='', timeout=0.05, encoding='utf-8')

    def test_duplicate_worker_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with worker_runtime(Path(root)):
                with self.assertRaisesRegex(RuntimeError, 'already owns'):
                    with worker_runtime(Path(root)):
                        self.fail('duplicate worker started')

    def test_stress_trends_coalesce(self):
        events=build_timeline([record(1,0),record(2,-10),record(3,-20)])
        self.assertEqual(len(events),2)
        self.assertEqual(events[1]['count'],2)
        self.assertEqual(events[1]['to_stress'],-20)

    def test_backward_time_creates_baseline_without_false_changes(self):
        old, new = record(112416, -1000), record(109747, -200)
        old['snapshot']['thoughts'] = [dict(thought_id='Death', emotion_id='SADNESS')]
        new['snapshot']['identity']['profession'] = 'Carver'
        new['snapshot']['personality_facets'] = [dict(facet_id='BRAVERY', value=70)]
        original = json.dumps([old, new], sort_keys=True)
        events = build_timeline([old, new])
        self.assertEqual(events[1]['kind'], 'timeline_reset')
        self.assertEqual(events[1]['snapshot'], new['snapshot'])
        self.assertNotIn('changes', events[1])
        self.assertNotIn('thoughts_removed', events[1])
        self.assertEqual(json.dumps([old, new], sort_keys=True), original)

    def test_stress_trends_do_not_cross_reset(self):
        events = build_timeline([record(10, 0), record(20, -10),
                                 record(5, -100), record(6, -110), record(7, -120)])
        self.assertEqual([e['kind'] for e in events],
                         ['baseline', 'stress_trend', 'timeline_reset', 'stress_trend'])
        self.assertEqual(events[-1]['from_stress'], -100)
        self.assertEqual(events[-1]['count'], 2)

    def test_time_comparison_handles_years_and_equal_ticks(self):
        a, b = record(400000, 0), record(10, -10)
        b['ingame_time']['year'] = 103
        self.assertEqual(build_timeline([a, b])[1]['kind'], 'stress_trend')
        self.assertEqual(build_timeline([b, a])[1]['kind'], 'timeline_reset')
        self.assertEqual(build_timeline([record(10, 0), record(10, -1)])[1]['kind'],
                         'stress_trend')

    def test_old_schema_is_regenerated_with_reset_page_and_payload(self):
        with tempfile.TemporaryDirectory() as root:
            save = Path(root)
            views = save / 'lorekeeper-views'
            request = dict(unit_id=1, year=102, tick=5)
            write_results(views / '1.request.json', request)
            write_results(views / '1.json', dict(request=dict(request, nonce=0), state='ready',
                          revision='old', story_revision='old', story='Old story', updated_at=10**12))
            source = save / 'lorekeeper-history.jsonl'
            contents = ''.join(json.dumps(r) + '\n' for r in [record(20, 0), record(5, -100)])
            source.write_text(contents)
            def generate(items, **kwargs):
                payload = json.loads(items[0]['raw'])
                self.assertEqual(items[0]['context'], HISTORIAN_CONTEXT)
                self.assertEqual(payload['schema_version'], VIEW_SCHEMA_VERSION)
                self.assertEqual(len(payload['events']), 1)
                self.assertEqual(payload['events'][0]['kind'], 'baseline')
                self.assertEqual(payload['events'][0]['time']['year_tick'], 5)
                page = load_results(next(views.glob('1.*.0.json')))
                self.assertTrue(any('Fresh baseline' in line for line in page['lines']))
                return {'results': [dict(id=items[0]['id'], text='The miner took pride in work.',
                                        explanation='Time reversal; separate observations.') ]}
            with patch('history_view.run_batch', side_effect=generate) as model:
                process_views(save)
                process_views(save)
                self.assertEqual(model.call_count, 1)
            self.assertEqual(load_results(views / '1.json')['schema_version'], VIEW_SCHEMA_VERSION)
            self.assertEqual(load_results(views / '1.json')['story_explanation'],
                             'Time reversal; separate observations.')
            self.assertNotIn('Time reversal', load_results(views / '1.json')['story'])
            self.assertEqual(load_results(views / '1.json')['story_notice'], STORY_NOTICE)
            self.assertEqual(source.read_text(), contents)

    def test_narrative_uses_latest_segment_without_mutating_full_timeline(self):
        events = build_timeline([record(20, 0), record(5, -10), record(6, -20),
                                 record(1, -30), record(2, -40)])
        original = json.dumps(events, sort_keys=True)
        selected = narrative_events(events)
        self.assertEqual([e['kind'] for e in selected], ['baseline', 'stress_trend'])
        self.assertEqual(selected[0]['time']['year_tick'], 1)
        self.assertEqual(json.dumps(events, sort_keys=True), original)
        self.assertEqual(narrative_events([]), [])
        ordinary = build_timeline([record(1, 0), record(2, -10)])
        self.assertEqual(narrative_events(ordinary), ordinary)

    def test_mixed_encodings_and_incomplete_tail(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'q'
            path.write_bytes(b'{"name":"\x95"}\n'+ '{"name":"ò"}\n'.encode()+b'{"partial":')
            self.assertEqual([x['name'] for x in load_queue(path)],['ò','ò'])

    def test_completed_queue_does_not_hit_batch_limit(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'q'
            result=Path(root)/'r'
            path.write_text(''.join(json.dumps(dict(id=str(i),kind='x',raw=str(i)))+'\n' for i in range(70)))
            write_results(result,{str(i):{'text':'done'} for i in range(70)})
            self.assertEqual(process_queue(path,result),0)

    def test_equivalent_requests_each_receive_result(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'q'
            result=Path(root)/'r'
            path.write_text(''.join(json.dumps(dict(id=i,kind='x',raw='same'))+'\n' for i in ('a','b')))
            with patch('process_queue.run_batch',return_value={'results':[dict(id='a',text='done')]}):
                self.assertEqual(process_queue(path,result),2)
            self.assertEqual(load_results(result)['b']['id'],'b')

    def test_model_failure_leaves_timeline_readable(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root)
            views=save/'lorekeeper-views'
            write_results(views/'1.request.json',dict(unit_id=1,year=102,tick=3))
            (save/'lorekeeper-history.jsonl').write_text(json.dumps(record(1,0))+'\n')
            with patch('history_view.run_batch',side_effect=TimeoutError('deadline exceeded')):
                process_views(save)
            self.assertEqual(load_results(views/'1.json')['state'],'failed')
            self.assertTrue(list(views.glob('1.*.0.json')))

    def test_prepares_page_before_model_and_deduplicates_request(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root)
            views=save/'lorekeeper-views'
            write_results(views/'1.request.json',dict(unit_id=1,year=102,tick=3))
            (save/'lorekeeper-history.jsonl').write_text(json.dumps(record(1,0))+'\n')
            def generate(items, **kwargs):
                self.assertTrue(list(views.glob('1.*.0.json')))
                self.assertEqual(load_results(views/'1.json')['state'],'processing')
                return {'results':[dict(id=items[0]['id'],text='Test ò was a miner.')]}
            with patch('history_view.run_batch',side_effect=generate) as model:
                process_views(save)
                process_views(save)
                self.assertEqual(model.call_count,1)
            self.assertEqual(load_results(views/'1.json')['state'],'ready')
