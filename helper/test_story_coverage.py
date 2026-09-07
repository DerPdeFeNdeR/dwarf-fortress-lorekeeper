import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from story_coverage import CoverageError, requirements, validate
from history_view import process_views
from process_queue import write_results, load_results
from test_history_view import record


def death():
    return dict(id=123,kind='death',subject_roles=['slayer'],
                time={'year':101}, site_name='Testfort', participants=[
                    dict(role='slayer',name='Urist',reference_status='resolved'),
                    dict(role='victim',name='Tirist Sobìrrith',reference_status='resolved')])


class CoverageTests(unittest.TestCase):
    def test_killing_anchor_preserves_responsibility_without_intent(self):
        rows=requirements({'events':[death()]})
        self.assertEqual(rows[0]['sentence'],
                         'In year 101, Urist killed Tirist Sobìrrith at Testfort.')
        self.assertNotIn('murder',rows[0]['sentence'])
        self.assertNotIn('child',rows[0]['sentence'])

    def test_names_alone_or_other_death_do_not_pass(self):
        rows=requirements({'events':[death()]})
        for text in ('Urist liked crafting. Tirist Sobìrrith was a friend.',
                     'Urist witnessed a death.', 'Urist did not kill Tirist Sobìrrith.'):
            with self.assertRaises(CoverageError): validate(text,rows)

    def test_whitespace_and_unicode_normalization_are_harmless(self):
        rows=requirements({'events':[death()]})
        text=rows[0]['sentence'].replace(' ', '\n').replace('ì','i\u0300')
        self.assertEqual(validate(text,rows)['checked_event_ids'],[123])

    def test_artifact_and_killing_are_both_required(self):
        item=dict(id=124,kind='artifact_creation',artifact_name='Copper Hope',
                  participants=[dict(role='creator',name='Urist',reference_status='resolved')])
        rows=requirements({'events':[death(),item]})
        self.assertEqual(len(rows),2)
        with self.assertRaises(CoverageError): validate(rows[1]['sentence'],rows)
        validate(' '.join(row['sentence'] for row in rows),rows)

    def test_empty_and_noncritical_input_does_not_force_padding(self):
        self.assertEqual(requirements({'events':[dict(id=1,kind='travel')]}),[])
        validate('A short portrait.',[])

    def test_failed_coverage_keeps_old_story_and_does_not_auto_retry(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); views=save/'lorekeeper-views'
            raw=death(); raw.update(year=101,tick=1)
            profile=dict(unit_id=1,histfig_id=1,captured_at=dict(year=102,tick=1),
                         historical_events=dict(events=[raw]))
            write_results(views/'1.profile.json',profile)
            write_results(views/'1.request.json',dict(unit_id=1,profile_file='1.profile.json'))
            write_results(views/'1.json',dict(story='Older biography.',state='ready',request={'nonce':0}))
            (save/'lorekeeper-history.jsonl').write_text(json.dumps(record(1,0))+'\n')
            with patch('history_view.run_batch',return_value={'results':[dict(text='A pleasant life.') ]}) as model:
                process_views(save); process_views(save)
                self.assertEqual(model.call_count,1)
            state=load_results(views/'1.json')
            self.assertEqual(state['state'],'failed')
            self.assertEqual(state['story'],'Older biography.')
            self.assertEqual(state['error_kind'],'event_coverage')

    def test_success_stores_coverage_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); views=save/'lorekeeper-views'
            raw=death(); raw.update(year=101,tick=1)
            write_results(views/'1.profile.json',dict(unit_id=1,histfig_id=1,
                captured_at=dict(year=102,tick=1),historical_events=dict(events=[raw])))
            write_results(views/'1.request.json',dict(unit_id=1,profile_file='1.profile.json'))
            (save/'lorekeeper-history.jsonl').write_text(json.dumps(record(1,0))+'\n')
            def generate(items,**kwargs):
                payload=json.loads(items[0]['raw'])
                return {'results':[dict(text=payload['required_event_coverage'][0]['sentence'])]}
            with patch('history_view.run_batch',side_effect=generate): process_views(save)
            state=load_results(views/'1.json')
            self.assertEqual(state['state'],'ready')
            self.assertEqual(state['story_coverage']['checked_event_ids'],[123])
