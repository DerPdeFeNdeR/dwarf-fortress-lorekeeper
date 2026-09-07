"""Conservative continuation planning; prose is context, never factual evidence."""
import hashlib
import json

from story_input import stable_json
from biography_significance import assess

MEMORY_VERSION = 1
MAX_MEMORY_BYTES = 1200000
APPEND_CONTEXT = """
This request is an incremental continuation, overriding the full-biography opening
and length instructions above. Return ONLY one or two new paragraphs, at most
180 words and 2000 UTF-8 bytes. Do not rewrite, summarize, or repeat the existing
biography. Continue its voice and use natural callbacks when the facts support
them. Do not introduce another opening portrait or closing recap.

prior_narrative is previous model prose, NOT a source of verified facts. Its
imagined motives remain interpretation, even when repeated. verified_context and
the current biography_profile provide game evidence; keep current observations
distinct from historical facts. Only events, heard_stories, and new historical/life episodes in
this request are candidates for new passages. Thought recall/removal is not a
new death, birth, reconciliation, or reversal of an experience. Do not invent
connections between people or events to produce continuity. Locally signal any
imagined motive. Integrate every required_event_coverage sentence in the NEW text.
"""


def digest(value):
    return hashlib.sha256(stable_json(value).encode('utf-8')).hexdigest()


def load_memory(path, story):
    try:
        with path.open('rb') as source:
            raw = source.read(MAX_MEMORY_BYTES + 1)
        if len(raw) > MAX_MEMORY_BYTES:
            return None
        memory = json.loads(raw)
        if (isinstance(memory, dict) and memory.get('version') == MEMORY_VERSION
                and memory.get('story_digest') == digest(story)
                and isinstance(memory.get('payload'), dict)):
            return memory
    except (OSError, ValueError):
        pass
    return None


def checkpoint(records, request):
    times = [(r['ingame_time']['year'], r['ingame_time']['year_tick']) for r in records]
    return dict(record_count=len(records), records_digest=digest(records),
                resets=sum(b < a for a, b in zip(times, times[1:])),
                requested_time=[request.get('year', 0), request.get('tick', 0)])


def newer_rows(old, current):
    """Existing event changes/removals require revision, not a new occurrence."""
    if current[:len(old)] == old:
        return current[len(old):]
    return None


def plan(memory, previous, payload, records, request):
    result = dict(mode='rebuild', reason='first_or_legacy_version', payload=payload)
    if not memory or not previous.get('story'):
        return result
    old = memory['payload']
    count = memory.get('checkpoint', {}).get('record_count', -1)
    prior_time = memory.get('checkpoint', {}).get('requested_time', [0, 0])
    last_request = previous.get('request') or {}
    observed_time = max(prior_time, [last_request.get('year', 0), last_request.get('tick', 0)])
    if (count < 0 or count > len(records)
            or digest(records[:count]) != memory['checkpoint'].get('records_digest')
            or [request.get('year', 0), request.get('tick', 0)] < observed_time):
        return dict(result, reason='incompatible_history')
    if checkpoint(records, request)['resets'] != memory['checkpoint'].get('resets'):
        return dict(result, reason='timeline_reset')
    # Compact input starts from the latest reset baseline; never join segments.
    additions = newer_rows(old.get('events', []), payload.get('events', []))
    if additions is None:
        return dict(result, reason='revised_timeline_or_reset')
    # Enrichment and changed stable character facts need a new edition.
    stable_fields = ('identity', 'life_events')
    if any(old.get(key) != payload.get(key) for key in stable_fields):
        return dict(result, reason='revised_character_context')
    old_profile, profile = old.get('biography_profile') or {}, payload.get('biography_profile') or {}
    transient = {'emotions', 'shortterm_memories', 'longterm_memories', 'needs', 'personality_facets',
                 'references', 'figures', 'limitations'}
    if ({k: v for k, v in old_profile.items() if k not in transient}
            != {k: v for k, v in profile.items() if k not in transient}):
        return dict(result, reason='enriched_or_changed_references')
    # Merely discovering an additional reference is not a new life event.
    # Correcting an already resolved name/detail does require revision.
    for section, key in (('references', 'key'), ('figures', 'id')):
        prior = {row.get(key): row for row in old_profile.get(section, []) if row.get(key) is not None}
        for row in profile.get(section, []):
            if row.get(key) in prior and prior[row[key]] != row:
                return dict(result, reason='enriched_or_changed_references')
    old_episodes = {row['source_key']: row for row in old.get('historical_episodes', {}).get('events', [])}
    episodes = payload.get('historical_episodes', {}).get('events', [])
    current = {row['source_key']: row for row in episodes}
    if any(key in current and current[key] != row for key, row in old_episodes.items()):
        return dict(result, reason='revised_historical_evidence')
    new_episodes = [row for row in episodes if row['source_key'] not in old_episodes]
    heard_before = {row['subject_key']: row for row in old.get('heard_stories', [])}
    heard_now = payload.get('heard_stories', [])
    if any(row['subject_key'] in heard_before and row['topic'] != heard_before[row['subject_key']]['topic']
           for row in heard_now):
        return dict(result, reason='corrected_story_subject')
    known_subjects = set(memory.get('heard_subjects', [])) | set(heard_before)
    heard_new = [row for row in heard_now if row['subject_key'] not in known_subjects] if len(known_subjects)<256 else []
    significant = assess(dict(old, known_story_subjects=sorted(known_subjects)), payload, additions, new_episodes)
    if not significant:
        return dict(result, mode='reuse' if old == payload else 'defer', reason='no_significant_developments')
    if any(key not in current for key in old_episodes):
        return dict(result, reason='revised_historical_evidence')
    last_time = prior_time
    for row in new_episodes:
        when = row.get('time') or {}
        if 'year' not in when or [when['year'], when.get('tick', 0)] <= last_time:
            return dict(result, reason='newly_discovered_old_event')
    for row in heard_new:
        when = row['heard_time']
        if [when['year'], when.get('tick', 0)] <= prior_time:
            return dict(result, reason='newly_resolved_old_listening_experience')
    if not additions and not new_episodes and not heard_new:
        return dict(result, reason='context_only_change')
    story = previous['story']
    if len(story.encode('utf-8')) > 5500 or memory.get('continuations', 0) >= 4:
        return dict(result, reason='consolidation_limit')
    old_anchors = {r['sentence'] for r in old.get('required_event_coverage', [])}
    incremental = dict(payload, events=additions,
                       heard_stories=heard_new,
                       historical_episodes=dict(payload.get('historical_episodes', {}), events=new_episodes),
                       life_events={'events': []},
                       required_event_coverage=[r for r in payload['required_event_coverage']
                                                if r['sentence'] not in old_anchors],
                       prior_narrative={'text': story, 'evidence_status': 'generated_interpretation'},
                       verified_context={'identity': old.get('identity'),
                                         'baseline': old.get('events', [])[:1],
                                         'life_events': old.get('life_events'),
                                         'heard_stories': old.get('heard_stories', []),
                                         'historical_episodes': old.get('historical_episodes')})
    return dict(mode='append', reason=significant, payload=incremental)


def make_memory(payload, records_checkpoint, story, mode, previous_memory, generation):
    heard_subjects = list((previous_memory or {}).get('heard_subjects', []))
    for row in payload.get('heard_stories', []):
        if row['subject_key'] not in heard_subjects and len(heard_subjects)<256:
            heard_subjects.append(row['subject_key'])
    return dict(version=MEMORY_VERSION, payload=payload, checkpoint=records_checkpoint,
                heard_subjects=heard_subjects,
                story_digest=digest(story), generation=generation,
                continuations=(previous_memory or {}).get('continuations', 0) + 1 if mode == 'append' else 0)
