"""Bounded, explicit-participant episodes from the game-side event index."""
from life_events import known_time

SUPPORTED = {'battle', 'site_attack', 'death', 'wounding', 'artifact_creation',
             'abduction', 'release', 'enslavement', 'ransom', 'reunion', 'travel',
             'profession_change', 'whereabouts_change', 'entity_link_added',
             'entity_link_removed', 'relationship_added', 'relationship_removed',
             'mood_change', 'masterwork_item'}


def collect(profile):
    profile = profile or {}
    indexed = profile.get('historical_events', {})
    subject = profile.get('histfig_id')
    events, seen = [], set()
    for raw in indexed.get('events', [])[:8]:
        event_id = raw.get('id')
        if raw.get('kind') not in SUPPORTED or not isinstance(event_id, int) or event_id < 0:
            continue
        if event_id in seen or not raw.get('subject_roles'):
            continue
        when = known_time({'event_year': raw.get('year'), 'event_tick': raw.get('tick')},
                          'event', profile.get('captured_at', {}))
        if raw.get('year', -1) >= 0 and when is None:
            continue
        row = {key: value for key, value in raw.items() if key not in ('year', 'tick')}
        row['source_key'] = f'history_event:{event_id}'
        row['subject_histfig_id'] = subject
        row['time'] = when
        if row['kind'] == 'artifact_creation':
            if not isinstance(row.get('naming_only'), bool):
                continue
            if row['naming_only']:
                row['kind'] = 'artifact_naming'
        row['participants'] = raw.get('participants', [])[:8]
        seen.add(event_id)
        events.append(row)
    return {'events': events, 'limitations': [
        'Only explicitly indexed participants are linked to the subject; coverage is partial.',
        'A death or wound is not proof of a battle. Group1/group2 do not establish victor or attacker.',
        'Do not join separate records into one battle based only on date/site.',
        'Current friendships do not establish a friendship at the event; no emotions or motives are recorded here.',
        'Artifact naming is not creation; artifact creation does not by itself establish a strange mood.',
        'Travel does not imply immigration. Use only explicit return/escape flags.',
        'Relationship link direction matters. Link removal alone is not divorce or death.',
        'Entity membership is not appointment; unresolved position IDs are not job titles.',
        'Release/ransom records do not establish later safety or the means of rescue.',
    ]}
