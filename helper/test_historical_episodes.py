import unittest
from historical_episodes import collect
from story_input import build_story_input, story_key


def profile(*events):
    return dict(histfig_id=1, captured_at=dict(year=10, tick=100),
                historical_events=dict(events=list(events)))


def event(**changes):
    return dict(dict(id=3, kind='battle', year=9, tick=10,
                     subject_roles=['group2'], participants=[dict(histfig_id=1, role='group2')]), **changes)


class HistoricalEpisodeTests(unittest.TestCase):
    def test_extended_events_retain_typed_details_without_inference(self):
        for kind in ('abduction','release','enslavement','ransom','reunion',
                     'travel','profession_change','whereabouts_change',
                     'entity_link_added','entity_link_removed','relationship_added',
                     'relationship_removed','mood_change','masterwork_item'):
            with self.subTest(kind=kind):
                row=collect(profile(event(kind=kind,subject_roles=['subject'])))['events'][0]
                self.assertEqual(row['kind'],kind)
                self.assertNotIn('outcome',row)

    def test_travel_flags_and_link_direction_survive(self):
        rows=collect(profile(event(kind='travel',is_return=False,is_escape=True),
                             event(id=4,kind='relationship_added',type='MOTHER',
                                   subject_roles=['target'])))['events']
        self.assertTrue(rows[0]['is_escape'])
        self.assertFalse(rows[0]['is_return'])
        self.assertEqual(rows[1]['subject_roles'],['target'])
        self.assertEqual(rows[1]['type'],'MOTHER')

    def test_profession_transition_is_cache_relevant(self):
        a=profile(event(kind='profession_change',old_job='MINER',new_job='MASON'))
        b=profile(event(kind='profession_change',old_job='MINER',new_job='CARPENTER'))
        self.assertNotEqual(story_key(build_story_input({},[],a),15),
                            story_key(build_story_input({},[],b),15))

    def test_preserves_role_without_inventing_outcome(self):
        row = collect(profile(event()))['events'][0]
        self.assertEqual(row['subject_roles'], ['group2'])
        self.assertEqual(row['source_key'], 'history_event:3')
        self.assertNotIn('victor', row)

    def test_rejects_future_unsupported_and_unlinked(self):
        self.assertEqual(collect(profile(event(year=11), event(kind='siege'),
                                        event(subject_roles=[])))['events'], [])

    def test_naming_not_creation_and_unknown_flag_rejected(self):
        rows = collect(profile(event(kind='artifact_creation', naming_only=True),
                               event(id=4, kind='artifact_creation')))['events']
        self.assertEqual([r['kind'] for r in rows], ['artifact_naming'])

    def test_deduplicates_and_bounds(self):
        self.assertEqual(len(collect(profile(event(), event()))['events']), 1)
        self.assertEqual(len(collect(profile(*(event(id=i) for i in range(20))))['events']), 8)

    def test_schema_payload_cache_tracks_events_not_index_progress(self):
        a = profile(event())
        b = profile(event())
        b['historical_events']['coverage'] = {'scanned': 100}
        payload = build_story_input({}, [], a)
        self.assertEqual(payload, build_story_input({}, [], b))
        b['historical_events']['events'][0]['subtype'] = 'SCUFFLE'
        self.assertNotEqual(story_key(payload,14), story_key(build_story_input({}, [], b),14))

    def test_keeps_artifact_unicode_and_distinct_same_date_events(self):
        rows = collect(profile(event(kind='artifact_creation', naming_only=False,
                                     artifact_name='Ûrist'), event(id=4)))['events']
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['artifact_name'],'Ûrist')
