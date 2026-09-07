import copy
import unittest

from memoire_brief import compile_personal, thought_fact, relevant_references


class MemoireBriefTests(unittest.TestCase):
    def test_organization_membership_and_whereabouts_never_become_a_journey(self):
        raw = self.raw()
        raw['biography_profile']['histfig_id'] = 7
        raw['chapter_evidence'] = {
            'membership': dict(source='historical', value=dict(kind='entity_link_removed', subject_histfig_id=7,
                link_type='MEMBER', entity_name='The Abbey')),
            'location': dict(source='historical', value=dict(kind='whereabouts_change', subject_histfig_id=7,
                site_name='Quickfortress', state='settler'))}
        brief, _ = compile_personal(raw)
        self.assertEqual(brief['chapter_evidence']['membership']['fact'], 'My membership in The Abbey ended.')
        self.assertIn('not travel', brief['chapter_evidence']['membership']['knowledge'])
        self.assertEqual(brief['chapter_evidence']['location']['fact'], 'My whereabouts were Quickfortress.')
        raw['biography_profile']['histfig_id'] = 8
        other, _ = compile_personal(raw)
        self.assertEqual(other['chapter_evidence']['membership'], raw['chapter_evidence']['membership'])

    def raw(self):
        return dict(chapter_title='Year 102 / Slate', identity={'name': 'Urist'},
                    biography_profile={}, chapter_evidence={}, required_event_coverage=[])

    def test_typed_body_sighting_is_not_witnessing_or_an_inferred_emotion(self):
        row = dict(thought_name='SawDeadBody', emotion_name='ANYTHING', reference_key='incident:1', count=2)
        ref = dict(status='resolved', kind='incident', details={'victim_name': 'Kangaroo Doe', 'death_cause': 'STRANGLED'})
        result = thought_fact(row, {'incident:1': ref})
        self.assertEqual(result['fact'], 'I saw the dead body of Kangaroo Doe.')
        self.assertEqual(result['reaction'], 'unspecified')
        self.assertEqual(result['count'], 2)
        self.assertNotIn('reference_key', result)
        self.assertNotIn('STRANGLED', str(result))
        wrong_kind = dict(ref, kind='historical_figure')
        self.assertNotIn('Kangaroo', thought_fact(row, {'incident:1': wrong_kind})['fact'])
        row['thought_name'] = 'WitnessDeath'
        self.assertEqual(thought_fact(row, {'incident:1': ref})['fact'], 'I witnessed the death of Kangaroo Doe.')

    def test_observations_preserve_counts_removals_and_time_scope(self):
        raw = self.raw()
        raw['chapter_evidence']['change'] = dict(source='observation', value=dict(time={'year': 102, 'tick': 10},
            thoughts_removed=[dict(thought_name='SawDeadBody', count=3)],
            thoughts_added=[dict(thought_name='UnknownThought', emotion_name='INTEREST', count=2)]))
        before = copy.deepcopy(raw)
        brief, length = compile_personal(raw)
        event = brief['chapter_evidence']['change']
        self.assertIn('not the date', event['date_scope'])
        self.assertEqual(event['observation']['thoughts_removed'][0]['count'], 3)
        self.assertEqual(event['observation']['thoughts_added'][0]['thought'], 'UnknownThought')
        self.assertEqual(raw, before)
        self.assertEqual(length, '60-100 words')

    def test_only_reachable_references_and_related_people_enter_a_month(self):
        raw = self.raw()
        raw['chapter_evidence']['event'] = dict(source='other', value={'name': 'Doren', 'reference_key': 'a'})
        raw['biography_profile'] = dict(relationships=[{'target_name': 'Doren'}, {'target_name': 'Unrelated'}],
            references=[{'key': 'a', 'details': {'reference_key': 'b'}},
                        {'key': 'b', 'details': {'reference_key': 'a'}}, {'key': 'c', 'name': 'Unrelated'}])
        brief, _ = compile_personal(raw)
        context = brief['current_character_context']
        self.assertEqual(context['relationships'], [{'target_name': 'Doren'}])
        self.assertEqual([r['key'] for r in context['references']], ['a', 'b'])
        self.assertNotIn('Unrelated', str(brief))

    def test_death_date_does_not_become_body_sighting_date(self):
        raw = self.raw()
        raw['chapter_evidence']['life'] = dict(source='life', value=dict(kind='death', person={'name': 'Doren'},
            involvement=['saw_body'], time={'year': 80}, emotions=[]))
        brief, length = compile_personal(raw)
        event = brief['chapter_evidence']['life']
        self.assertEqual(event['facts'], ['I saw the dead body of Doren.'])
        self.assertEqual(event['event_date'], {'year': 80})
        self.assertIn('not date of seeing', event['date_scope'])
        self.assertEqual(length, '100-180 words')

    def test_heard_story_keeps_teller_topic_year_and_listening_time(self):
        from test_heard_stories import profile
        from heard_stories import collect, anchor
        stories = collect(profile())
        self.assertTrue(stories)
        raw = self.raw()
        raw['chapter_evidence'] = {'heard': dict(source='heard', value=stories[0])}
        raw['required_event_coverage'] = anchor(raw['identity'], stories, first_person=True)
        brief, _ = compile_personal(raw)
        row = brief['chapter_evidence']['heard']
        self.assertEqual(row['heard_time'], stories[0]['heard_time'])
        self.assertEqual(row['facts'][0], raw['required_event_coverage'][0]['sentence'])
        self.assertIn('never firsthand', row['knowledge'])

    def test_required_fact_size_and_busy_month_override_short_target(self):
        raw = self.raw()
        raw['required_event_coverage'] = [{'sentence': 'word ' * 71}]
        self.assertEqual(compile_personal(raw)[1], '100-180 words')
        raw['required_event_coverage'] = []
        raw['chapter_evidence'] = {str(i): {'source': 'unknown', 'value': {}} for i in range(4)}
        self.assertEqual(compile_personal(raw)[1], '100-180 words')
