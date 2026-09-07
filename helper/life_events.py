"""Derive bounded, evidence-linked life events from one current profile."""
import re

MAX_EVENTS = 24
FAMILY = {'mother', 'father', 'child', 'spouse', 'deceased_spouse', 'former_spouse'}


def known_time(details, prefix, captured):
    year, tick = details.get(prefix + '_year'), details.get(prefix + '_tick')
    if not isinstance(year, int) or year < 0:
        return None
    result = {'year': year}
    if isinstance(tick, int) and tick >= 0:
        result['tick'] = tick
    if isinstance(captured.get('year'), int):
        if (year, result.get('tick', 0)) > (captured['year'], captured.get('tick', 0)):
            return None
    return result


def collect(profile):
    if not profile:
        return {'events': [], 'limitations': ['No on-demand profile supplied.']}
    refs = {r['key']: r for r in profile.get('references', [])
            if r.get('status') == 'resolved' and r.get('key')}
    captured = profile.get('captured_at', {})
    relations, events = {}, {}
    for link in [*profile.get('relationships', []), *profile.get('friends', [])]:
        match = re.search(r'histfig_hf_link_(\w+)st', link.get('kind', ''))
        kind = match[1] if match else link.get('kind')
        if kind not in FAMILY | {'friend', 'close_friend', 'kindred_spirit'}:
            continue
        ref = refs.get(link.get('reference_key'), {})
        if ref.get('kind') != 'historical_figure':
            continue
        hf = ref['id']; details = ref.get('details', {})
        relations.setdefault(hf, []).append(kind)
        born = known_time(details, 'born', captured)
        died = known_time(details, 'died', captured)
        person = dict(histfig_id=hf, name=details.get('name'))
        if kind == 'child' and born:
            events[f'birth:{hf}'] = dict(kind='child_birth', person=person, time=born,
                source_keys=[ref['key']], relationship_observed_now='child',
                caveat='Child birth date; does not identify the other parent or a particular childbirth memory.')
        if died:
            events.setdefault(f'death:{hf}', dict(kind='death', person=person, time=died,
                source_keys=[ref['key']], involvement=[], emotions=[]))

    observations = []
    for section in ('emotions', 'shortterm_memories', 'longterm_memories'):
        observations.extend(profile.get(section, []))
    observations.extend(row.get('memory', {}) for row in profile.get('core_memories', []))
    for thought in observations:
        if thought.get('thought_name') not in {'WitnessDeath', 'SawDeadBody', 'Death', 'UnexpectedDeath'}:
            continue
        ref = refs.get(thought.get('reference_key'), {})
        details = ref.get('details', {})
        if ref.get('kind') == 'incident':
            when = known_time(dict(event_year=details.get('year'), event_tick=details.get('tick')), 'event', captured)
            if isinstance(details.get('year'), int) and details['year'] >= 0 and when is None:
                continue
            hf = details.get('victim_histfig_id')
            identity = f'death:{hf}' if isinstance(hf, int) and hf >= 0 else f'incident:{ref["id"]}'
            event = events.setdefault(identity, dict(kind='death', person=dict(
                histfig_id=hf, name=details.get('victim_name')), source_keys=[], involvement=[], emotions=[]))
            if when:
                event['time'] = when
            event['death_cause'] = details.get('death_cause')
            site = refs.get(details.get('site_reference'), {}).get('details', {})
            event['site_name'] = site.get('name')
            involvement = 'witnessed_death' if thought['thought_name'] == 'WitnessDeath' else 'saw_body'
        elif ref.get('kind') == 'historical_figure':
            identity = f'death:{ref["id"]}'
            if identity not in events:
                when = known_time(details, 'died', captured)
                if not when:
                    continue  # Retain the thought elsewhere; do not manufacture a confirmed death.
                events[identity] = dict(kind='death', person=dict(histfig_id=ref['id'], name=details.get('name')),
                    time=when, source_keys=[], involvement=[], emotions=[])
            event, involvement = events[identity], 'death_thought'
        else:
            continue
        event['source_keys'] = sorted(set([*event['source_keys'], ref['key']]))
        event['involvement'] = sorted(set([*event['involvement'], involvement]))
        emotion = thought.get('emotion_name')
        if emotion and emotion != 'ANYTHING':
            event['emotions'] = sorted(set([*event['emotions'], emotion]))

    for event in events.values():
        event['current_relationships'] = sorted(set(relations.get(event['person']['histfig_id'], [])))
        if event['kind'] == 'death':
            event['caveat'] = 'Death date is not body-sighting/recall date. Current links do not prove the bond at death or the subject knew of the death. Only listed involvement/emotions are supported.'
    def significance(event):
        if 'witnessed_death' in event.get('involvement', []): return 3
        if event['current_relationships'] and event.get('emotions'): return 4
        if event['kind'] == 'child_birth': return 2
        if event['current_relationships']: return 1
        return 0
    def priority(event):
        return (-significance(event), -(event.get('time', {}).get('year', -1)),
                -(event.get('time', {}).get('tick', -1)), str(event['person']['histfig_id']))
    ordered = sorted(events.values(), key=priority)
    focus = ordered[0] if ordered and significance(ordered[0]) > 0 else None
    return dict(events=ordered[:MAX_EVENTS], narrative_focus=focus, truncated=len(ordered) > MAX_EVENTS,
        limitations=['At most 24 events from bounded current-profile references; no world-history scan.',
                     'Friendship formation, marriages, other parents, and reactions are not inferred.'])
