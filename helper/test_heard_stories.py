import copy
import unittest

from heard_stories import collect, anchor
from biography_significance import assess
from biography_updates import make_memory, checkpoint, plan
from story_input import build_story_input
from test_history_view import record


def profile():
    topic = dict(id=41, status='resolved', kind='entity_link_added', link_type='POSITION',
                 year=83, tick=58800, entity_name='The Copper Order',
                 participants=[dict(role='subject', name='Elda Elmcloak', reference_status='resolved')],
                 office=dict(status='resolved', name='copper voice', elected=True, definition_observed_now=True))
    return dict(unit_id=1, captured_at=dict(year=102, tick=200),
        emotions=[dict(thought_name='WatchPerform', emotion_name='INTEREST', reference_key='performance:9')],
        references=[dict(key='performance:9', id=9, kind='performance_incident', status='resolved',
            details=dict(performance_type='STORYTELLING_EVENT', year=102, tick=100,
                         subject_reference='subject:41', performers=[])),
            dict(key='subject:41', id=41, kind='story_subject', status='resolved', details=topic)])


class HeardStoryTests(unittest.TestCase):
    def test_listening_and_subject_dates_and_roles_are_separate(self):
        stories = collect(profile())
        self.assertEqual(stories[0]['heard_time'], {'year': 102, 'tick': 100})
        self.assertEqual(stories[0]['topic']['year'], 83)
        self.assertEqual(stories[0]['listener_role'], 'audience')
        self.assertNotIn('subject_roles', stories[0])
        payload = build_story_input({'name': 'Urist'}, [], profile())
        self.assertEqual(payload['historical_episodes']['events'], [])
        self.assertIn('Urist heard with interest a story about Elda Elmcloak', payload['required_event_coverage'][0]['sentence'])

    def test_repeated_performances_and_memory_slots_deduplicate_subject(self):
        data = profile()
        repeat = copy.deepcopy(data['references'][0])
        repeat.update(key='performance:10', id=10)
        repeat['details']['tick'] = 150
        data['references'].append(repeat)
        data['emotions'].append(dict(thought_name='WatchPerform', emotion_name='INTEREST', reference_key='performance:10'))
        data['shortterm_memories'] = data['emotions']
        self.assertEqual(len(collect(data)), 1)
        old = {'heard_stories': collect(profile())}
        current = {'heard_stories': collect(data)}
        self.assertIsNone(assess(old, current, [], []))

    def test_poetry_wrong_namespace_unsupported_and_future_dates_are_excluded(self):
        for change in ('poetry', 'namespace', 'unsupported', 'future'):
            data = profile()
            if change == 'poetry': data['references'][0]['details']['performance_type'] = 'POETRY_RECITAL'
            if change == 'namespace': data['references'][1]['kind'] = 'historical_figure'
            if change == 'unsupported': data['references'][1]['details']['status'] = 'unsupported_event'
            if change == 'future': data['references'][0]['details']['year'] = 103
            self.assertEqual(collect(data), [])

    def test_performing_does_not_claim_listening(self):
        data = profile(); data['emotions'][0]['thought_name'] = 'Perform'
        self.assertEqual(collect(data), [])

    def test_anchor_never_assigns_the_office_to_the_listener(self):
        sentence = anchor({'name': 'Urist, Miner'}, collect(profile()))[0]['sentence']
        self.assertIn('Urist heard with interest a story about Elda Elmcloak taking the office', sentence)
        self.assertNotIn('Urist took', sentence)
        self.assertNotIn('elected', sentence)  # Current definition is not the dated selection mechanism.

    def test_persistent_subject_ledger_prevents_reappearance_trigger(self):
        current = {'heard_stories': collect(profile())}
        self.assertEqual(assess({}, current, [], []), 'new_story_subject')
        self.assertIsNone(assess({'known_story_subjects': ['history_event:41']}, current, [], []))

    def test_new_listening_can_append_but_old_newly_resolved_listening_rebuilds(self):
        records = [record(10, 0)]
        empty = build_story_input({'name': 'Urist'}, [], None)
        memory = make_memory(empty, checkpoint(records, {'year': 102, 'tick': 10}),
                             'Prior prose.', 'rebuild', None, {})
        payload = dict(empty, heard_stories=collect(profile()))
        update = plan(memory, {'story': 'Prior prose.'}, payload, records, {'year': 102, 'tick': 200})
        self.assertEqual(update['mode'], 'append')
        self.assertEqual(update['payload']['heard_stories'][0]['subject_key'], 'history_event:41')
        memory['checkpoint']['requested_time'] = [102, 150]
        self.assertEqual(plan(memory, {'story': 'Prior prose.'}, payload, records,
                              {'year': 102, 'tick': 200})['mode'], 'rebuild')
