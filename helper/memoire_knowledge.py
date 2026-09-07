"""Restrict individual narration to personal evidence, not world omniscience."""
import copy

VERSION = 1
SECTIONS = ('emotions', 'shortterm_memories', 'longterm_memories', 'core_memories',
            'relationships', 'friends', 'needs', 'preferences')


def referenced_keys(value, available):
    if isinstance(value, str):
        return {value} if value in available else set()
    if isinstance(value, dict):
        return set().union(set(), *(referenced_keys(v, available) for v in value.values()))
    if isinstance(value, list):
        return set().union(set(), *(referenced_keys(v, available) for v in value))
    return set()


def personal_profile(profile):
    if not profile:
        return profile
    result = copy.deepcopy(profile)
    available = {r['key']: r for r in profile.get('references', []) if r.get('key')}
    pending = referenced_keys({k: profile.get(k) for k in SECTIONS}, available)
    retained = {}
    while pending:
        key = pending.pop()
        if key in retained:
            continue
        ref = copy.deepcopy(available[key])
        details = ref.get('details') or {}
        if ref.get('kind') == 'historical_figure':
            # Family/friend links establish identity, not knowledge of their life events.
            ref['details'] = {k: details[k] for k in ('name',) if k in details}
        elif ref.get('kind') == 'incident':
            # A death/body thought identifies its victim, not secret cause, killer,
            # actual death date, or where an unwitnessed death occurred.
            ref['details'] = {k: details[k] for k in ('victim_name', 'victim_histfig_id') if k in details}
        elif ref.get('kind') not in ('performance_incident', 'story_subject'):
            ref['details'] = {k: details[k] for k in ('name', 'material_name', 'type_name') if k in details}
        retained[key] = ref
        pending.update(referenced_keys(ref.get('details'), available) - retained.keys())
    result['references'] = [retained[key] for key in sorted(retained)]
    result['figures'] = [dict(id=r['id'], name=r['details']['name']) for r in result['references']
                         if r.get('kind') == 'historical_figure' and r.get('status') == 'resolved'
                         and r.get('details', {}).get('name')]
    subject = profile.get('histfig_id')
    indexed = result.get('historical_events') or {}
    personal = []
    for event in indexed.get('events', [])[:8]:
        roles = set(event.get('subject_roles', []))
        matched = [p for p in event.get('participants', [])
                   if type(subject) is int and subject >= 0 and p.get('histfig_id') == subject
                   and p.get('role') in roles]
        if not matched or (event.get('kind') == 'death' and all(p['role'] == 'victim' for p in matched)):
            continue
        if event.get('kind') in ('relationship_added', 'relationship_removed'):
            continue  # A recorded social-link change is not evidence of a disclosed conversation.
        if event.get('kind') in ('battle', 'site_attack'):
            # Participation does not reveal the names of every other combatant.
            event['participants'] = matched
        personal.append(event)
    result['historical_events'] = dict(indexed, events=personal)
    result.setdefault('limitations', []).append(
        'Memoire knowledge: personal participation, retained thoughts/memories, and explicitly heard tales only. '
        'Relationships alone do not supply others\' life events; no secret death causes/dates or private thoughts.')
    return result
