import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from event_methods import details
from story_coverage import requirements, validate, CoverageError
from memoire_knowledge import personal_profile


class EventMethodTests(unittest.TestCase):
    def event(self, cause='DROWN'):
        return dict(id=7, kind='death', death_cause=cause, participants=[
            dict(role='victim',name='Urist',reference_status='resolved'),
            dict(role='slayer',name='Feb',reference_status='resolved')])

    def test_recorded_cause_is_required_without_inventing_killing_mechanism(self):
        required = requirements(dict(events=[self.event()]), annual=True)
        text = required[0]['sentence']
        self.assertIn('Feb killed Urist; the cause of death was drowning', text)
        self.assertNotIn('Feb drowned', text)
        with self.assertRaises(CoverageError):
            validate('Feb killed Urist.', required)
        validate(text, required)
        validate('Feb killed Urist, with blood loss as the cause of death.',
                 requirements(dict(events=[self.event('BLEED')]), annual=True))

    def test_unknown_or_generic_causes_do_not_invent_methods(self):
        for cause in ('STRUCK_DOWN', 'MURDER', 'UNKNOWN', None):
            self.assertEqual(details(self.event(cause)), [])

    def test_impact_weapon_and_launcher_stay_distinct(self):
        event = self.event('SHOT')
        event['method'] = dict(status='available', source_event_id=7, weapons=[
            dict(status='resolved',role='impact_item',name='iron bolt'),
            dict(status='resolved',role='launcher',name='copper crossbow')])
        self.assertEqual(details(event), ['the cause of death was being shot',
            'the weapon was iron bolt', 'the launcher was copper crossbow'])

    def test_unrelated_or_unresolved_weapon_is_not_used(self):
        event = self.event(None)
        event['method'] = dict(status='available',source_event_id=8,weapons=[
            dict(status='resolved',role='impact_item',name='axe')])
        self.assertEqual(details(event), [])
        event['method']['source_event_id'] = 7
        event['method']['weapons'][0]['status'] = 'unavailable'
        self.assertEqual(details(event), [])

    def test_injury_details_do_not_imply_weapon_or_attack(self):
        event = dict(id=7,kind='wounding',method=dict(status='available',
            source_event_id=7,body_part='left hand',part_lost=True))
        self.assertEqual(details(event), ['the injured body part was left hand',
                                        'the body part was lost'])

    def test_verified_injury_type_is_specific_without_guessing_weapon(self):
        event = dict(id=7, kind='wounding', method=dict(status='available',
            source_event_id=7, injury_type='BLUDGEON'))
        self.assertEqual(details(event), ['the injury involved blunt trauma'])

    def test_memoire_does_not_gain_hidden_incident_methods(self):
        profile = dict(emotions=[dict(reference_key='incident:3')],references=[
            dict(key='incident:3',kind='incident',details=dict(victim_name='Urist',
                death_cause='DROWN',method=dict(weapon='axe')))])
        self.assertEqual(personal_profile(profile)['references'][0]['details'],
                         dict(victim_name='Urist'))

    def test_personal_perpetrator_method_is_retained_but_other_events_are_not(self):
        event = self.event('BLEED')
        event['subject_roles'] = ['slayer']
        event['participants'][1]['histfig_id'] = 8
        result = personal_profile(dict(histfig_id=8,historical_events=dict(events=[event])))
        self.assertEqual(result['historical_events']['events'][0]['death_cause'], 'BLEED')
        result = personal_profile(dict(histfig_id=9,historical_events=dict(events=[event])))
        self.assertEqual(result['historical_events']['events'], [])

    @unittest.skipUnless(os.environ.get('LOREKEEPER_LIVE_METHOD_TEST')=='1',
                         'Explicit opt-in: one method-aware chronicle call')
    def test_live_method_coverage_and_cached_reopen(self):
        from test_chronicles import request
        from chronicles import process_chronicles, chapter_key
        from process_queue import write_results, load_results
        event = self.event('BLEED')
        event.update(year=102,tick=10,site_id=745,method=dict(status='available',
            source_event_id=7,weapons=[dict(status='resolved',role='impact_item',name='iron axe')]))
        data = dict(request('draft',year=102),events=[event])
        with tempfile.TemporaryDirectory() as root:
            save=Path(root); directory=save/'lorekeeper-chronicles'
            write_results(directory/'a.request.json',data)
            process_chronicles(save)
            result=load_results(directory/(chapter_key(data)+'.chapter.json'))
            self.assertEqual(result['state'],'ready',result.get('error'))
            self.assertIn('blood loss',result['story'])
            self.assertIn('iron axe',result['story'])
            print(result['story'],flush=True)
            print('Method-aware generation seconds:',result['generation_seconds'],flush=True)
            with patch('chronicles.run_batch') as model:
                process_chronicles(save)
                model.assert_not_called()
