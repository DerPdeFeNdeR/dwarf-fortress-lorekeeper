"""Listening experiences, deliberately separate from personal historical episodes."""
from life_events import known_time


def collect(profile):
    profile = profile or {}
    refs = {row['key']: row for row in profile.get('references', []) if row.get('key') and row.get('status') == 'resolved'}
    rows = []
    for section in ('emotions', 'shortterm_memories', 'longterm_memories'):
        rows.extend(profile.get(section, []))
    rows.extend(row.get('memory', {}) for row in profile.get('core_memories', []))
    subjects = {}
    for thought in rows:
        if thought.get('thought_name') != 'WatchPerform':
            continue
        ref = refs.get(thought.get('reference_key'), {})
        if ref.get('kind') != 'performance_incident':
            continue
        performance = ref.get('details', {})
        topic_ref = refs.get(performance.get('subject_reference'), {})
        topic = topic_ref.get('details', {})
        if (performance.get('performance_type') != 'STORYTELLING_EVENT'
                or topic_ref.get('kind') != 'story_subject' or topic.get('status') != 'resolved'):
            continue
        when = known_time({'heard_year': performance.get('year'), 'heard_tick': performance.get('tick')},
                          'heard', profile.get('captured_at', {}))
        if not when:
            continue
        if not (topic.get('entity_name') or topic.get('site_name') or topic.get('artifact_name')
                or any(p.get('name') for p in topic.get('participants', []) if p.get('reference_status') == 'resolved')):
            continue
        if topic.get('year', -1) >= 0 and not known_time(
                {'event_year': topic['year'], 'event_tick': topic.get('tick')}, 'event', when):
            continue
        key = f"history_event:{topic['id']}"
        row = dict(subject_key=key, kind='heard_story', topic=topic, heard_time=when,
                   reaction=thought.get('emotion_name'), performers=performance.get('performers', []),
                   performance_id=ref['id'], site_id=performance.get('site_id'), listener_role='audience',
                   caveat='The listener heard about this event; attendance at the historical event is not established.')
        # One subject, not one paragraph for every performance or memory recall.
        if key not in subjects or row['performance_id'] < subjects[key]['performance_id']:
            subjects[key] = row
    return sorted(subjects.values(), key=lambda row: (
        row['topic'].get('link_type') == 'POSITION', row['topic'].get('year', -1), row['subject_key']), reverse=True)[:8]


def anchor(identity, stories):
    """One named office story gets an explicit listening anchor, never an action by the listener."""
    listener = identity.get('name', '').split(',', 1)[0]
    if not listener:
        return []
    for story in stories:
        subject = office_subject(story['topic'])
        if not subject:
            continue
        reaction = ' with interest' if story.get('reaction') == 'INTEREST' else ''
        names = storyteller_names(story)
        told_by = ' from ' + ' and '.join(names) if names else ''
        sentence = f"{listener} heard{reaction} a story{told_by} about {subject}."
        return [dict(event_id='heard:' + story['subject_key'], kind='heard_story', sentence=sentence)]
    return []


def storyteller_names(story):
    return list(dict.fromkeys(p['name'] for p in story.get('performers', [])[:4]
        if p.get('reference_status') == 'resolved' and p.get('name')))


def office_subject(topic):
    person = next((p.get('name') for p in topic.get('participants', [])
                   if p.get('role') == 'subject' and p.get('reference_status') == 'resolved'), None)
    office = topic.get('office') or {}
    if (topic.get('kind') != 'entity_link_added' or topic.get('link_type') != 'POSITION'
            or not person or office.get('status') != 'resolved' or not office.get('name')
            or not topic.get('entity_name')):
        return None
    year = topic.get('year', -1)
    when = f' in year {year}' if isinstance(year, int) and year >= 0 else ''
    return f"{person} taking the office of {office['name']} in {topic['entity_name']}{when}"
