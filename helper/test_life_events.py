import unittest
from life_events import collect
from story_input import build_story_input, story_key


def figure(id, **details):
    return dict(key=f'hf:{id}', kind='historical_figure', id=id, status='resolved',
                details=dict(name=f'Person {id}', **details))


class LifeEventTests(unittest.TestCase):
    def test_related_death_and_incident_merge_and_take_focus(self):
        ref=dict(key='incident:7',kind='incident',id=7,status='resolved',details=dict(
            victim_histfig_id=2,victim_name='Person 2',year=101,tick=12))
        profile=dict(references=[figure(2,died_year=101,died_tick=12),ref],
            friends=[dict(kind='close_friend',reference_key='hf:2')],
            emotions=[dict(thought_name='WitnessDeath',reference_key='incident:7',emotion_name='HORROR')])
        result=collect(profile)
        self.assertEqual(len(result['events']),1)
        self.assertEqual(result['narrative_focus']['current_relationships'],['close_friend'])
        self.assertEqual(result['narrative_focus']['involvement'],['witnessed_death'])
        self.assertEqual(result['narrative_focus']['source_keys'],['hf:2','incident:7'])

    def test_unresolved_reference_and_acquaintance_do_not_become_friend_events(self):
        profile=dict(references=[figure(2,died_year=101)],
            friends=[dict(kind='acquaintance',reference_key='hf:2')],
            emotions=[dict(thought_name='WitnessDeath',reference_key='missing')])
        self.assertEqual(collect(profile)['events'],[])

    def test_child_birth_and_related_death_have_source_dates(self):
        profile = dict(captured_at=dict(year=102,tick=100),
            references=[figure(1,born_year=98,born_tick=45,died_year=101,died_tick=20)],
            relationships=[dict(kind='histfig_hf_link_childst',reference_key='hf:1')])
        events = collect(profile)['events']
        self.assertEqual({e['kind'] for e in events}, {'child_birth','death'})
        self.assertEqual(next(e for e in events if e['kind']=='child_birth')['time'],dict(year=98,tick=45))
        death=next(e for e in events if e['kind']=='death')
        self.assertEqual(death['involvement'],[])
        self.assertEqual(death['emotions'],[])
        self.assertEqual(death['current_relationships'],['child'])
        self.assertEqual(collect(profile)['narrative_focus']['kind'],'child_birth')

    def test_incident_deduplicates_memories_without_confusing_body_with_death(self):
        ref=dict(key='incident:7',kind='incident',id=7,status='resolved',details=dict(
            victim_histfig_id=1,victim_name='Victim',year=100,tick=12,death_cause='THIRST'))
        memory=dict(thought_name='SawDeadBody',reference_key='incident:7',emotion_name='ANYTHING',year=102,year_tick=99)
        profile=dict(references=[ref],emotions=[memory],longterm_memories=[memory])
        events=collect(profile)['events']
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]['involvement'],['saw_body'])
        self.assertEqual(events[0]['emotions'],[])
        self.assertEqual(events[0]['time'],dict(year=100,tick=12))
        self.assertIsNone(collect(profile)['narrative_focus'])
        profile['captured_at']=dict(year=99,tick=0)
        self.assertEqual(collect(profile)['events'],[])

    def test_friend_death_is_named_but_not_mutual_or_known_to_subject(self):
        profile=dict(references=[figure(2,died_year=101,died_tick=12)],
            friends=[dict(kind='friend',reference_key='hf:2',directional=True)])
        event=collect(profile)['events'][0]
        self.assertEqual(event['current_relationships'],['friend'])
        self.assertEqual(event['person']['name'],'Person 2')
        self.assertEqual(event['involvement'],[])

    def test_missing_future_dates_and_spouse_link_do_not_create_milestones(self):
        profile=dict(captured_at=dict(year=102,tick=10),
            references=[figure(1,born_year=-1,died_year=103),figure(2,born_year=99)],
            relationships=[dict(kind='histfig_hf_link_childst',reference_key='hf:1'),
                           dict(kind='histfig_hf_link_spousest',reference_key='hf:2')])
        self.assertEqual(collect(profile)['events'],[])

    def test_memoire_retains_relationship_but_not_world_derived_birth(self):
        a=build_story_input({},[],dict(references=[figure(1,born_year=100)],
            relationships=[dict(kind='histfig_hf_link_childst',reference_key='hf:1')]))
        self.assertEqual(a['life_events']['events'],[])
        self.assertEqual(a['biography_profile']['figures'][0]['name'],'Person 1')
        self.assertNotEqual(story_key(a,13),story_key(build_story_input({},[],{}),13))

    def test_event_output_is_bounded_and_reports_truncation(self):
        profile=dict(references=[figure(i,born_year=100) for i in range(30)],
            relationships=[dict(kind='histfig_hf_link_childst',reference_key=f'hf:{i}') for i in range(30)])
        result=collect(profile)
        self.assertEqual(len(result['events']),24)
        self.assertTrue(result['truncated'])
