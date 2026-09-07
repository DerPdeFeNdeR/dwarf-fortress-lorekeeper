import copy
import unittest

from memoire_knowledge import personal_profile
from story_input import build_story_input
from test_heard_stories import profile as heard_profile


class MemoireKnowledgeTests(unittest.TestCase):
    def test_family_identity_does_not_disclose_world_life_events(self):
        source = dict(histfig_id=1, relationships=[dict(reference_key='hf:2')],
            figures=[dict(id=2, name='Partner', death_year=102)],
            references=[dict(key='hf:2', id=2, kind='historical_figure', status='resolved',
                             details=dict(name='Partner', death_year=102, birth_year=80)),
                        dict(key='hf:3', id=3, kind='historical_figure', status='resolved',
                             details=dict(name='Stranger'))])
        original = copy.deepcopy(source)
        result = personal_profile(source)
        self.assertEqual(result['references'][0]['details'], {'name': 'Partner'})
        self.assertEqual(result['figures'], [dict(id=2, name='Partner')])
        self.assertEqual(len(result['references']), 1)
        self.assertEqual(source, original)

    def test_witness_identifies_victim_without_secret_incident_details(self):
        source = dict(emotions=[dict(thought_name='WitnessDeath', reference_key='incident:1')],
            references=[dict(key='incident:1', kind='incident', status='resolved',
                details=dict(victim_name='Dattle', victim_histfig_id=4,
                             killer='Unknown killer', death_cause='poison', year=100, site=745))])
        result = personal_profile(source)
        self.assertEqual(result['references'][0]['details'],
                         dict(victim_name='Dattle', victim_histfig_id=4))

    def test_personal_participation_requires_identity_and_role(self):
        def event(identity, role, kind='death'):
            return dict(kind=kind, subject_roles=[role],
                        participants=[dict(histfig_id=identity, role=role)])
        source = dict(histfig_id=1, historical_events=dict(events=[
            event(1, 'slayer'), event(2, 'slayer'), event(1, 'victim'),
            event(1, 'subject', 'relationship_removed')]))
        result = personal_profile(source)
        self.assertEqual(result['historical_events']['events'],
                         [source['historical_events']['events'][0]])

    def test_battle_participation_does_not_reveal_every_combatant(self):
        source = dict(histfig_id=1, historical_events=dict(events=[dict(kind='battle',
            subject_roles=['combatant'], participants=[dict(histfig_id=1, role='combatant'),
                                                      dict(histfig_id=2, role='combatant')])]))
        result = personal_profile(source)
        self.assertEqual(result['historical_events']['events'][0]['participants'],
                         [dict(histfig_id=1, role='combatant')])
        self.assertEqual(len(source['historical_events']['events'][0]['participants']), 2)

    def test_heard_topic_stays_hearsay_not_personal_history(self):
        source = heard_profile()
        source['references'][0]['details']['performers'] = [dict(name='Storyteller')]
        result = build_story_input(dict(name='Urist'), [], source)
        self.assertEqual(len(result['heard_stories']), 1)
        self.assertEqual(result['historical_episodes']['events'], [])
        self.assertIn('Storyteller', str(result['biography_profile']['references']))
        self.assertIn('I heard', result['required_event_coverage'][0]['sentence'])

    def test_reference_order_is_stable(self):
        source = heard_profile()
        reversed_source = copy.deepcopy(source)
        reversed_source['references'].reverse()
        self.assertEqual(personal_profile(source), personal_profile(reversed_source))
