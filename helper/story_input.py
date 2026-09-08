"""Compact semantic story input; full diagnostic data remains on disk."""
import hashlib
import json
import re
from collections import Counter
from historian import narrative_events
from life_events import collect as collect_life_events
from historical_episodes import collect as collect_historical_episodes
from story_coverage import requirements
from heard_stories import collect as collect_heard_stories, anchor as story_anchor
from memoire_knowledge import personal_profile, VERSION as KNOWLEDGE_VERSION


def stable_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def thoughts(rows):
    counts = Counter()
    for row in rows:
        if row.get('thought', row.get('thought_id')) == -1 or row.get('unavailable'):
            continue
        value = {k: row[k] for k in ('thought_name', 'emotion_name', 'subthought',
                                     'reference_key', 'reference_status') if k in row}
        if not value:
            value = {k: row[k] for k in ('thought_id', 'emotion_id') if k in row}
        if value:
            counts[stable_json(value)] += row.get('count', 1)
    return [dict(json.loads(key), count=count) for key, count in sorted(counts.items())]


def compact_profile(profile):
    if not profile:
        return None
    result = {k: profile[k] for k in ('unit_id', 'histfig_id', 'figures',
              'relationships', 'friends', 'values', 'preferences', 'personality_facets',
              'mental_attributes', 'age', 'limitations') if k in profile}
    result['references'] = [r for r in profile.get('references', []) if r.get('status') == 'resolved']
    for key in ('emotions', 'shortterm_memories', 'longterm_memories'):
        result[key] = thoughts(profile.get(key, []))
    result['core_memories'] = []
    for row in profile.get('core_memories', []):
        memory = thoughts([row.get('memory', {})])
        if memory:
            result['core_memories'].append(dict(
                {k: v for k, v in row.items() if k != 'memory'}, memory=memory[0]))
    result['needs'] = []
    for row in profile.get('needs', []):
        need = {k: v for k, v in row.items() if k != 'focus_level'}
        if isinstance(row.get('focus_level'), (int, float)):
            need['focus_band'] = row['focus_level'] // 1000
        result['needs'].append(need)
    # Reordering DF vectors is not a narrative change.
    for key, value in result.items():
        if isinstance(value, list):
            result[key] = sorted(value, key=stable_json)
    return result


def build_story_input(identity, events, profile):
    profile = personal_profile(profile)
    selected = narrative_events(events)
    compact = []
    stress = []
    for event in selected:
        if event['kind'] == 'stress_trend':
            stress.append(event['to_stress'] // 1000)
            continue
        row = {k: v for k, v in event.items() if k not in ('snapshot', 'changes',
               'thoughts_added', 'thoughts_removed')}
        if 'snapshot' in event:
            snapshot = event['snapshot']
            row['snapshot'] = {k: snapshot[k] for k in ('identity', 'personality_facets') if k in snapshot}
            row['snapshot']['thoughts'] = thoughts(snapshot.get('thoughts', []))
            value = snapshot.get('mental_state', {}).get('stress')
            if value is not None:
                row['snapshot']['stress_band'] = value // 1000
                stress.append(value // 1000)
        for change in event.get('changes', []):
            match = re.fullmatch(r'stress changed from (-?\d+) to (-?\d+)', change)
            if match:
                stress.append(int(match[2]) // 1000)
        changes = [s for s in event.get('changes', []) if not s.startswith('stress changed')]
        if changes:
            row['changes'] = changes
        for key in ('thoughts_added', 'thoughts_removed'):
            if event.get(key):
                row[key] = thoughts(event[key])
        compact.append(row)
    episodes=collect_historical_episodes(profile)
    heard=collect_heard_stories(profile)
    return dict(knowledge_version=KNOWLEDGE_VERSION, identity=identity, events=compact,
                biography_profile=compact_profile(profile),
                life_events=collect_life_events(profile),
                historical_episodes=episodes, heard_stories=heard,
                required_event_coverage=requirements(episodes, (profile or {}).get('histfig_id'))
                    + story_anchor(identity, heard, first_person=True),
                stress_bands=list(dict.fromkeys(stress)), final_stress_band=stress[-1] if stress else None,
                numerical_note='Stress/focus bands are floor(value/1000), not diagnosed mental-state categories.')


def story_key(payload, version):
    return hashlib.sha256(stable_json([version, payload]).encode('utf-8')).hexdigest()
