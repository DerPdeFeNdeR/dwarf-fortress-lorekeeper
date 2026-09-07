import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chronicles import chapter_input, load_request, process_chronicles, chapter_key, CHRONICLE_CONTEXT
from historian import HISTORIAN_CONTEXT
from monthly_biography import intro_context, evidence_payload
from process_queue import write_results, load_results
from story_coverage import requirements, validate, CoverageError
from test_chronicles import request
from fortress_calendar import MONTHS, month_name
from story_input import compact_profile
from narrative_voice import MENTAL_VOICE_CONTEXT


def voice(year=102):
    return dict(version=1,status='selected',site_id=745,year=year,histfig_id=7,
                unit_id=17,name='Minkot Udistatír',personality_facets=dict(HUMOR=85,ORDERLINESS=90),
                values=[dict(name='CRAFTSMANSHIP',strength=40)],
                mental_attributes=dict(version=1,status='available',attributes={
                    'LINGUISTIC_ABILITY':dict(value=500,caste_median=1000,relative_level='lower'),
                    'MEMORY':dict(value=1800,caste_median=1000,relative_level='higher')}))


def death():
    return dict(id=1,kind='death',year=102,tick=10,site_id=745,
                participants=[dict(role='slayer',histfig_id=7,name='Minkot Udistatír',reference_status='resolved'),
                              dict(role='victim',histfig_id=8,name='Dòmas',reference_status='resolved')])


class NarrationTests(unittest.TestCase):
    def test_annual_month_labels_and_unknown_dates(self):
        for i,month in enumerate(MONTHS):
            self.assertEqual(month_name(dict(tick=i*33600)),month)
            self.assertEqual(month_name(dict(tick=(i+1)*33600-1)),month)
        for tick in (-1,None,403200,True,'33600'):
            self.assertIsNone(month_name(dict(tick=tick)))
        data=dict(request('draft',year=102),captured_tick=100000,events=[dict(death(),tick=33600)])
        payload=chapter_input(data)
        self.assertEqual(payload['events'][0]['month'],'Slate')
        self.assertEqual(payload['required_event_coverage'][0]['sentence'],
                         'In Slate, Minkot Udistatír killed Dòmas.')
        data['events'][0]['tick']=-1
        payload=chapter_input(data)
        self.assertIsNone(payload['events'][0]['month'])
        self.assertEqual(payload['required_event_coverage'][0]['sentence'],
                         'Minkot Udistatír killed Dòmas.')

    def test_mental_attributes_reach_both_voice_paths_without_becoming_facts(self):
        profile=voice()
        self.assertEqual(compact_profile(profile)['mental_attributes'],profile['mental_attributes'])
        self.assertEqual(intro_context(dict(biography_profile=profile))['profile']['mental_attributes'],
                         profile['mental_attributes'])
        self.assertIn(MENTAL_VOICE_CONTEXT,HISTORIAN_CONTEXT)
        self.assertIn(MENTAL_VOICE_CONTEXT,CHRONICLE_CONTEXT)
        self.assertIn('Lower memory must NOT invent forgetting',MENTAL_VOICE_CONTEXT)
        self.assertIn('never licenses new events',MENTAL_VOICE_CONTEXT)
        data=dict(request('draft',year=102),narrator=profile)
        self.assertEqual(chapter_input(data)['narrator']['mental_attributes'],profile['mental_attributes'])
    def test_first_person_anchors_use_ids_not_names_or_assumed_roles(self):
        episode=dict(events=[death()])
        self.assertEqual(requirements(episode,7)[0]['sentence'],'I killed Dòmas.')
        self.assertEqual(requirements(episode,8)[0]['sentence'],'Minkot Udistatír killed me.')
        self.assertEqual(requirements(episode,9)[0]['sentence'],'Minkot Udistatír killed Dòmas.')
        episode['events'][0]['participants'][1]['name']='Minkot Udistatír'
        self.assertEqual(requirements(episode,7)[0]['sentence'],'I killed Minkot Udistatír.')
        with self.assertRaises(CoverageError):
            validate('I had a pleasant year.', requirements(episode,7))

    def test_passive_and_active_first_person_coverage(self):
        for kind,role,expected in [('wounding','wounded','I was wounded.'),
                                  ('abduction','abducted','I was abducted.'),
                                  ('release','rescued_hfs','I was freed.'),
                                  ('enslavement','enslaved','I was enslaved.'),
                                  ('ransom','ransomed','I was ransomed.')]:
            event=dict(id=1,kind=kind,participants=[dict(role=role,histfig_id=7,
                       name='Minkot',reference_status='resolved')])
            self.assertEqual(requirements(dict(events=[event]),7)[0]['sentence'],expected)

    def test_monthly_payload_keeps_first_person_coverage_and_voice_context(self):
        payload=dict(identity=dict(name='Minkot'),biography_profile=voice())
        self.assertEqual(intro_context(payload)['profile']['personality_facets']['HUMOR'],85)
        evidence={'history_event:1':dict(source='historical',value=death())}
        self.assertEqual(evidence_payload(evidence,payload['identity'],7)['required_event_coverage'][0]['sentence'],
                         'I killed Dòmas.')
        self.assertIn('first-person memoire',HISTORIAN_CONTEXT)
        self.assertIn('Never invent how the narrator learned them',HISTORIAN_CONTEXT)
        self.assertIn('not automatically witnessed',CHRONICLE_CONTEXT)

    def test_annual_voice_validates_year_site_and_identity(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'request.json'
            data=dict(request('draft',year=102),schema_version=2,narrator=voice())
            write_results(path,data)
            self.assertEqual(load_request(path)['narrator']['name'],'Minkot Udistatír')
            for invalid in (None,dict(voice(),year=101),dict(voice(),site_id=9),dict(voice(),histfig_id=-1)):
                write_results(path,dict(data,narrator=invalid))
                with self.assertRaises(ValueError): load_request(path)

    def test_annual_voice_reaches_model_and_cached_reopen_and_retry_preserve_it(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            data=dict(request('draft',year=102),schema_version=2,narrator=voice(),events=[death()])
            write_results(directory/'a.request.json',data)
            def generate(items,**kwargs):
                payload=json.loads(items[0]['raw'])
                self.assertEqual(payload['narrator'],voice())
                return dict(results=[dict(text=payload['required_event_coverage'][0]['sentence'])])
            with patch('chronicles.run_batch',side_effect=generate) as model:
                process_chronicles(save); process_chronicles(save)
                self.assertEqual(model.call_count,1)
            state=load_results(directory/(chapter_key(data)+'.chapter.json'))
            self.assertEqual(state['story_narrator'],voice())
            write_results(directory/'b.request.json',dict(data,nonce='2'))
            with patch('chronicles.run_batch',side_effect=RuntimeError('offline')):
                process_chronicles(save)
            state=load_results(directory/(chapter_key(data)+'.chapter.json'))
            self.assertEqual(state['story_narrator'],voice())
            self.assertIn('I killed Dòmas.',state['story'])
            write_results(directory/'c.request.json',dict(data,retry_nonce='3'))
            with patch('chronicles.run_batch',side_effect=generate): process_chronicles(save)
            self.assertEqual(load_results(directory/(chapter_key(data)+'.chapter.json'))['state'],'ready')

    @unittest.skipUnless(os.environ.get('LOREKEEPER_LIVE_NARRATOR_TEST')=='1',
                         'Explicit opt-in: one real annual narrator model call')
    def test_live_annual_narrator_and_cached_reopen(self):
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            event=dict(id=1,kind='artifact_creation',naming_only=False,site_id=745,year=102,tick=10,
                artifact_name='The Copper Promise',participants=[dict(role='creator',histfig_id=7,
                name='Minkot Udistatír',reference_status='resolved')])
            data=dict(request('draft',year=102),schema_version=2,narrator=voice(),events=[event])
            write_results(directory/'a.request.json',data)
            process_chronicles(save)
            state=load_results(directory/(chapter_key(data)+'.chapter.json'))
            self.assertEqual(state['state'],'ready',state.get('error'))
            self.assertIn('I created The Copper Promise',state['story'])
            self.assertIn('Granite',state['story'])
            self.assertLessEqual(state['story'].lower().count('year 102'),1)
            self.assertNotRegex(state['story'],r'(?i)\b(supplied|payload|dataset)\b')
            self.assertEqual(state['story_narrator'],voice())
            print('Annual narrator seconds:',state['generation_seconds'],flush=True)
            print(state['story'],flush=True)
            with patch('chronicles.run_batch') as model:
                process_chronicles(save)
                model.assert_not_called()
