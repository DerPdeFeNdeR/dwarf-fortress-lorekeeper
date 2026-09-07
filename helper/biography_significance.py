"""Editorial thresholds, not diagnoses or claims of complete event coverage."""
from story_input import stable_json

ROUTINE_EVENT_KINDS = {'travel', 'whereabouts_change', 'masterwork_item'}
IMPORTANT_THOUGHTS = {'Death', 'UnexpectedDeath', 'WitnessDeath'}
ROUTINE_ADDITIONS = 8
ROUTINE_VARIETY = 3
ROUTINE_OBSERVATIONS = 3
FACET_DELTA = 10
STRESS_BAND_DELTA = 10


def thought_key(thought):
    return stable_json({key: value for key, value in thought.items() if key != 'count'})


def prior_thoughts(payload):
    rows = []
    for event in payload.get('events', []):
        rows.extend(event.get('snapshot', {}).get('thoughts', []))
        rows.extend(event.get('thoughts_added', []))
    profile = payload.get('biography_profile') or {}
    for key in ('emotions', 'shortterm_memories', 'longterm_memories'):
        rows.extend(profile.get(key, []))
    rows.extend(row['memory'] for row in profile.get('core_memories', []) if row.get('memory'))
    return {thought_key(row) for row in rows}


def facets(payload):
    values = {}
    for event in payload.get('events', []):
        for row in event.get('snapshot', {}).get('personality_facets', []) + event.get('personality_changes', []):
            values[str(row['facet_id'])] = row['value']
    values.update((payload.get('biography_profile') or {}).get('personality_facets', {}))
    return values


def assess(old, current, additions, episodes):
    known_subjects = set(old.get('known_story_subjects', [])) | {row['subject_key'] for row in old.get('heard_stories', [])}
    if len(known_subjects)<256 and any(row['subject_key'] not in known_subjects for row in current.get('heard_stories', [])):
        return 'new_story_subject'
    old_anchors = {r['sentence'] for r in old.get('required_event_coverage', [])}
    if any(r['sentence'] not in old_anchors for r in current.get('required_event_coverage', []) if r.get('kind')!='heard_story'):
        return 'consequential_event'
    if any(row.get('kind') not in ROUTINE_EVENT_KINDS for row in episodes):
        return 'historical_milestone'
    before, after = facets(old), facets(current)
    if any(isinstance(value, (int, float)) and isinstance(before.get(key), (int, float))
           and abs(value-before[key]) >= FACET_DELTA for key, value in after.items()):
        return 'personality_change'
    before, after = old.get('final_stress_band'), current.get('final_stress_band')
    if isinstance(before, (int, float)) and isinstance(after, (int, float)) and abs(after-before) >= STRESS_BAND_DELTA:
        return 'large_stress_change'
    known = prior_thoughts(old)
    count, kinds, observations = 0, set(), set()
    for event in additions:
        for thought in event.get('thoughts_added', []):
            token = thought.get('thought_name', thought.get('thought_id'))
            if token in IMPORTANT_THOUGHTS and thought_key(thought) not in known:
                return 'new_death_related_experience'
            count += max(0, thought.get('count', 1))
            kinds.add(str(token))
            observations.add(stable_json(event.get('time')))
    # Removed thoughts and repeated openings contribute nothing. Counts come
    # only from additions since the last successfully written biography.
    for event in episodes:
        count += 1
        kinds.add(event.get('kind'))
        observations.add(stable_json(event.get('time')))
    if count >= ROUTINE_ADDITIONS and len(kinds) >= ROUTINE_VARIETY and len(observations) >= ROUTINE_OBSERVATIONS:
        return 'accumulated_varied_developments'
    return None
