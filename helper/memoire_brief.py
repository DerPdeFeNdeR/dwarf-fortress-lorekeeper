"""Small personal writing briefs; input must already pass personal-knowledge filtering."""
import json
from heard_stories import anchor


CONSEQUENTIAL = {'death', 'wounding', 'abduction', 'release', 'enslavement', 'ransom', 'artifact_creation'}
EXPERIENCES = {
    'SawDeadBody': 'I saw a dead body',
    'WitnessDeath': 'I witnessed a death',
    'WatchPerform': 'I watched a performance',
    'SatisfiedAtWork': 'I felt satisfaction at work',
    'LackWell': 'I lacked access to a well',
    'LackCup': 'I lacked a drinking vessel',
    'Argument': 'I had an argument',
}


def reference_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('reference_key', 'key', 'subject_reference') and isinstance(item, str):
                yield item
            else:
                yield from reference_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from reference_keys(item)


def relevant_references(value, profile):
    references = {row['key']: row for row in profile.get('references', []) if row.get('key')}
    pending = set(reference_keys(value))
    selected = {}
    while pending:
        key = pending.pop()
        if key in selected or key not in references:
            continue
        selected[key] = references[key]
        pending.update(set(reference_keys(references[key])) - selected.keys())
    return [selected[key] for key in sorted(selected)]


def thought_fact(row, references):
    thought = row.get('thought_name')
    phrase = EXPERIENCES.get(thought)
    reference = references.get(row.get('reference_key'), {})
    details = reference.get('details') or {}
    victim = details.get('victim_name') if reference.get('status') == 'resolved' and reference.get('kind') == 'incident' else None
    if victim and thought == 'SawDeadBody':
        phrase = f'I saw the dead body of {victim}'
    elif victim and thought == 'WitnessDeath':
        phrase = f'I witnessed the death of {victim}'
    if not phrase:
        # Unknown thought semantics remain labeled data, never guessed English.
        return dict(thought=thought, reaction=row.get('emotion_name'), count=row.get('count', 1),
                    reference_key=row.get('reference_key'), interpretation='Meaning not translated; do not guess.')
    reaction = row.get('emotion_name')
    result = dict(fact=phrase + '.', reaction=reaction if reaction not in (None, 'ANYTHING') else 'unspecified',
                  count=row.get('count', 1))
    # The resolved personal fact is sufficient; do not expose an incident's
    # hidden method or a performance's historical subject as extra personal facts.
    if thought not in ('SawDeadBody', 'WitnessDeath', 'WatchPerform'):
        result['reference_key'] = row.get('reference_key')
    return result


def selected_thoughts(rows, references):
    selected, seen = [], set()
    for row in rows:
        key = row.get('thought_name')
        if key not in seen:
            selected.append(thought_fact(row, references)); seen.add(key)
        if len(selected) == 8:
            break
    return selected


def personal_event(row, required_ids, identity, references, narrator_id):
    source, value = row.get('source'), row.get('value')
    if not isinstance(value, dict):
        return row  # Preserve unfamiliar input, rather than silently dropping it.
    if source == 'life' and value.get('kind') == 'death':
        name = (value.get('person') or {}).get('name')
        involvement = value.get('involvement') or []
        facts = []
        if name and 'saw_body' in involvement:
            facts.append(f'I saw the dead body of {name}.')
        if name and 'witnessed_death' in involvement:
            facts.append(f'I witnessed the death of {name}.')
        if facts:
            return dict(facts=facts, reactions=[emotion for emotion in value.get('emotions') or []
                                               if emotion != 'ANYTHING'],
                        event_date=value.get('time'),
                        date_scope='Death date, not date of seeing the body or recalling it.',
                        knowledge='Only listed involvement; no inferred grief, cause or witnessing.')
    if source == 'heard':
        facts = anchor(identity, [value], first_person=True)
        if facts:
            return dict(facts=[r['sentence'] for r in facts], heard_time=value.get('heard_time'),
                        reaction=value.get('reaction'),
                        organization_context=(value.get('topic') or {}).get('entity_details'),
                        knowledge='Heard tale, never firsthand participation. Topic year is inside the fact.')
    if source == 'historical' and value.get('id') in required_ids:
        return dict(required_event_id=value['id'], time=value.get('time'))
    if source == 'historical' and isinstance(narrator_id, int) and value.get('subject_histfig_id') == narrator_id:
        kind = value.get('kind')
        if kind in ('entity_link_added', 'entity_link_removed') and value.get('link_type') == 'MEMBER' and value.get('entity_name'):
            action = 'began' if kind == 'entity_link_added' else 'ended'
            return dict(fact=f"My membership in {value['entity_name']} {action}.", time=value.get('time'),
                        organization_context=value.get('entity_details'),
                        knowledge='Organization membership, not travel, immigration or an appointment.')
        if kind == 'whereabouts_change' and value.get('site_name'):
            return dict(fact=f"My whereabouts were {value['site_name']}.", time=value.get('time'),
                        status=value.get('state'), knowledge='Location observation, not proof of immigration or a journey.')
        if kind == 'profession_change' and value.get('new_job'):
            return dict(fact=f"My occupation changed to {value['new_job'].lower().replace('_', ' ')}.",
                        time=value.get('time'), knowledge='No duties, routines, motives or duration of service supplied.')
    if source == 'observation':
        event = dict(value)
        for field in ('thoughts_added', 'thoughts_removed'):
            if field in event:
                event[field] = [thought_fact(thought, references) for thought in event[field]]
        return dict(observation=event, date_scope='Observation time, not the date of the original experiences.')
    return row


def character_context(profile, evidence, intro):
    text = json.dumps(evidence, ensure_ascii=False)
    context = {}
    for field in ('relationships', 'friends'):
        rows = profile.get(field) or []
        context[field] = (rows[:8] if intro else [row for row in rows
            if any(isinstance(row.get(key), str) and row[key] and row[key] in text
                   for key in ('name', 'target_name'))])
    preferences = profile.get('preferences') or []
    if intro:
        context['preferences'] = preferences[:6]
    else:
        # A current interest is relevant only when its resolved subject is in this chapter.
        context['preferences'] = [row for row in preferences if any(
            isinstance(ref.get('details'), dict) and ref['details'].get('name')
            and ref['details']['name'] in text for ref in relevant_references(row, profile))]
    return context


def compile_personal(raw, options=None):
    profile = raw.get('biography_profile') or {}
    intro = raw['chapter_title'] == 'Introduction and recollections'
    required_ids = {row.get('event_id') for row in raw.get('required_event_coverage', [])}
    refs = {row['key']: row for row in profile.get('references', []) if row.get('key')}
    evidence = {}
    for key, row in raw['chapter_evidence'].items():
        if row.get('source') == 'baseline':
            snapshot = (row.get('value') or {}).get('snapshot') or {}
            evidence[key] = dict(scope='Undated baseline recollections, not new events.',
                thoughts=selected_thoughts(snapshot.get('thoughts', []), refs))
        else:
            evidence[key] = personal_event(row, required_ids, raw.get('identity') or {}, refs, profile.get('histfig_id'))
    context = character_context(profile, [evidence, raw.get('required_event_coverage', [])], intro)
    if intro:
        # A bounded diverse selection supports a portrait without repeating every emotion.
        rows = list(profile.get('emotions') or [])
        for field in ('shortterm_memories', 'longterm_memories'):
            rows.extend(profile.get(field) or [])
        rows.extend(row.get('memory', {}) for row in profile.get('core_memories') or [])
        context['undated_recollections'] = selected_thoughts(rows, refs)
    # References can only be reached from selected facts/context; no global profile dump.
    context['references'] = relevant_references([evidence, context], profile)
    busy = len(evidence) > 3 or any((row.get('value') or {}).get('kind') in CONSEQUENTIAL
                                  for row in raw['chapter_evidence'].values())
    required_words = sum(len(row['sentence'].split()) for row in raw.get('required_event_coverage', []))
    key = 'busy_words' if busy or required_words > 70 else 'quiet_words'
    bounds = (options or {}).get(key, [100, 180] if key=='busy_words' else [60, 100])
    length = f'{bounds[0]}-{bounds[1]} words'
    brief = {key: raw[key] for key in ('identity', 'chapter_title', 'environment') if key in raw}
    brief.update(chapter_evidence=evidence, current_character_context=context)
    return brief, length
