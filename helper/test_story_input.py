import copy
import json
import os
from writer_settings import resolve_settings
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from history_view import build_timeline, process_views
from process_queue import write_results, load_results
from story_input import build_story_input, story_key, stable_json
from test_history_view import record


class StoryInputTests(unittest.TestCase):
    def test_model_and_effort_changes_invalidate_new_requests_only(self):
        with tempfile.TemporaryDirectory() as root:
            save = Path(root); views = save / 'lorekeeper-views'
            (save / 'lorekeeper-history.jsonl').write_text(json.dumps(record(1, -100)) + '\n')
            request_path = views / '1.request.json'
            with patch('history_view.run_batch', return_value={'results': [dict(text='Story')]}) as model:
                for nonce, name, effort in [(1, 'gpt-5.6-luna', 'low'),
                                             (2, 'gpt-5.6-luna', 'low'),
                                             (3, 'gpt-5.6-luna', 'medium'),
                                             (4, 'qwen3:8b', 'medium')]:
                    profile = 'qwen-fast' if name == 'qwen3:8b' else 'luna-literary'
                    with patch.dict(os.environ, LOREKEEPER_WRITER_PROFILE=profile, LOREKEEPER_REASONING_EFFORT=effort):
                        write_results(request_path, dict(unit_id=1, nonce=nonce))
                        process_views(save)
                        result = load_results(views / '1.json')
                self.assertEqual(result['story_generation'], resolve_settings(dict(provider='ollama', model=name, reasoning_effort=effort)))
                self.assertEqual(model.call_count, 3)
                self.assertEqual(model.call_args.kwargs['settings']['model'], 'qwen3:8b')
                process_views(save)  # Same completed request: no background regeneration.
                self.assertEqual(model.call_count, 3)
                with patch.dict(os.environ, LOREKEEPER_WRITER_PROFILE='qwen-fast', LOREKEEPER_REASONING_EFFORT='medium'):
                    with patch('history_view.HISTORIAN_CONTEXT', 'Updated historian rules'):
                        write_results(request_path, dict(unit_id=1, nonce=5))
                        process_views(save)
                self.assertEqual(model.call_count, 4)

    def test_final_stress_includes_changes_with_other_events(self):
        events = [dict(kind='baseline', snapshot=dict(mental_state=dict(stress=-100))),
                  dict(kind='stress_trend', to_stress=-1200),
                  dict(kind='change', changes=['stress changed from -1200 to -3400',
                                               'thoughts changed: 1 added, 0 removed'])]
        payload = build_story_input({}, events, None)
        self.assertEqual(payload['final_stress_band'], -4)
        self.assertEqual(payload['stress_bands'], [-1, -2, -4])

    def test_dormant_old_schema_story_is_not_regenerated_until_requested(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); views=save/'lorekeeper-views'
            request=dict(unit_id=1,nonce=1)
            write_results(views/'1.request.json',request)
            write_results(views/'1.json',dict(schema_version=1,state='ready',request=request,story='Old'))
            with patch('history_view.run_batch') as model:
                process_views(save)
                model.assert_not_called()

    def test_compaction_preserves_names_references_and_counts(self):
        thought = dict(thought_name='WitnessDeath', emotion_name='HORROR', subthought=141,
                       reference_key='incident:141:nil', year_tick=10, relative_strength=20)
        profile = dict(figures=[dict(id=3, name='Tirist Sobìrrith')],
                       emotions=[thought, thought], relationships=[dict(target_hf=3, kind='child',reference_key='hf:3')],
                       references=[dict(key='incident:141:nil', id=141,kind='incident',status='resolved',
                                        details=dict(victim_name='Dattle Brown')),
                                   dict(key='hf:3',id=3,kind='historical_figure',status='resolved',
                                        details=dict(name='Tirist Sobìrrith'))])
        payload = build_story_input({}, [], profile)
        compact = payload['biography_profile']
        self.assertEqual(compact['figures'], profile['figures'])
        self.assertEqual(compact['emotions'][0]['count'], 2)
        self.assertEqual(sorted(compact['references'],key=lambda r:r['key']),
                         sorted(profile['references'],key=lambda r:r['key']))
        self.assertNotIn('relative_strength', stable_json(payload))
        changed = copy.deepcopy(profile)
        changed['emotions'][0]['relative_strength'] = 50
        changed['emotions'][0]['year_tick'] = 11
        self.assertEqual(story_key(payload, 1), story_key(build_story_input({}, [], changed), 1))
        changed['relationships'][0]['kind'] = 'spouse'
        self.assertNotEqual(story_key(payload, 1), story_key(build_story_input({}, [], changed), 1))

    def test_stress_within_band_does_not_trigger_generation(self):
        a = build_story_input({}, build_timeline([record(1,-100), record(2,-120)]), None)
        b = build_story_input({}, build_timeline([record(1,-100), record(2,-120), record(3,-140)]), None)
        self.assertEqual(story_key(a,1), story_key(b,1))
        c = build_story_input({}, build_timeline([record(1,-100), record(2,-1200)]), None)
        self.assertNotEqual(story_key(a,1), story_key(c,1))

    def test_identical_semantics_reuse_story_and_report_timing(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); views=save/'lorekeeper-views'
            source=save/'lorekeeper-history.jsonl'
            rows=[record(1,-100),record(2,-120)]
            source.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            path=views/'1.request.json'
            write_results(path,dict(unit_id=1,nonce=1))
            with patch('history_view.run_batch',return_value={'results':[dict(id='test',text='Cached story') ]}) as model:
                process_views(save)
                rows.append(record(3,-140))
                source.write_text(''.join(json.dumps(r)+'\n' for r in rows))
                write_results(path,dict(unit_id=1,nonce=2))
                process_views(save)
                self.assertEqual(model.call_count,1)
            result=load_results(views/'1.json')
            self.assertTrue(result['timings']['cache_hit'])
            self.assertEqual(result['timings']['generation_seconds'],0)
            self.assertEqual(result['story_revision'],result['revision'])

    def test_all_discovered_pages_publish_before_generation(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); views=save/'lorekeeper-views'
            a,b=record(1,0),record(1,0)
            b['snapshot']['identity']['id']=2
            (save/'lorekeeper-history.jsonl').write_text(json.dumps(a)+'\n'+json.dumps(b)+'\n')
            for unit_id in (1,2): write_results(views/f'{unit_id}.request.json',dict(unit_id=unit_id))
            def generate(items, **kwargs):
                self.assertTrue(list(views.glob('1.*.0.json')))
                self.assertTrue(list(views.glob('2.*.0.json')))
                return {'results':[dict(id=items[0]['id'],text='Story')]}
            with patch('history_view.run_batch',side_effect=generate): process_views(save)
            self.assertIn('generation_seconds',load_results(views/'1.json')['timings'])
