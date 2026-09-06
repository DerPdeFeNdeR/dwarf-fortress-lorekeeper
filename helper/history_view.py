"""Prepare bounded history views outside the game thread."""
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from codex_batch import run_batch
from process_queue import load_queue, load_results, write_results, repair_story_names

_source_cache = {}
VIEW_SCHEMA_VERSION = 5


def time_key(record):
    when = record['ingame_time']
    return when['year'], when['year_tick']


def thought_counts(snapshot):
    return Counter((t.get('thought_id'), t.get('emotion_id'))
                   for t in snapshot.get('thoughts', []))


def build_timeline(records):
    events = []
    if not records:
        return events
    first = records[0]
    events.append({'kind': 'baseline', 'time': first['ingame_time'],
                   'snapshot': first['snapshot']})
    for previous, current in zip(records, records[1:]):
        if time_key(current) < time_key(previous):
            events.append(dict(kind='timeline_reset', time=current['ingame_time'],
                               previous_time=previous['ingame_time'],
                               snapshot=current['snapshot']))
            continue
        a, b = previous['snapshot'], current['snapshot']
        changes = []
        if a['identity'].get('profession') != b['identity'].get('profession'):
            changes.append('profession changed from %s to %s' % (
                a['identity'].get('profession'), b['identity'].get('profession')))
        old, new = a.get('mental_state', {}).get('stress'), b.get('mental_state', {}).get('stress')
        if old is not None and new is not None and old != new:
            changes.append(f'stress changed from {old} to {new}')
        ac, bc = thought_counts(a), thought_counts(b)
        added, removed = bc - ac, ac - bc
        if added or removed:
            changes.append(f'thoughts changed: {sum(added.values())} added, {sum(removed.values())} removed')
        facets = {f['facet_id']: f['value'] for f in a.get('personality_facets', [])}
        delta = [dict(f, from_value=facets.get(f['facet_id']))
                 for f in b.get('personality_facets', []) if facets.get(f['facet_id']) != f['value']]
        if delta:
            changes.append(f'personality facets changed: {len(delta)}')
        if not changes:
            continue
        if len(changes) == 1 and changes[0].startswith('stress changed'):
            if events[-1]['kind'] == 'stress_trend':
                event = events[-1]
                event.update(to_stress=new, time=current['ingame_time'], count=event['count'] + 1)
            else:
                events.append(dict(kind='stress_trend', start_time=previous['ingame_time'],
                                   time=current['ingame_time'], from_stress=old, to_stress=new, count=1))
            continue
        def examples(snapshot, counts):
            found = {(t.get('thought_id'), t.get('emotion_id')): t for t in snapshot.get('thoughts', [])}
            return [dict(found[key], count=count) for key, count in sorted(counts.items(), key=str)]
        events.append(dict(kind='change', time=current['ingame_time'], changes=changes,
                           thoughts_added=examples(b, added), thoughts_removed=examples(a, removed),
                           personality_changes=delta))
    return events


def prepare_view(save, unit_id):
    # Read the authoritative log: indexes may be incomplete after interrupted writes.
    source = save / 'lorekeeper-history.jsonl'
    stat = source.stat() if source.exists() else None
    key = (str(source), stat.st_size, stat.st_mtime_ns) if stat else (str(source), 0, 0)
    if _source_cache.get('key') != key:
        by_unit = {}
        for record in load_queue(source):
            if not isinstance(record, dict) or record.get('record_type') != 'dwarf_snapshot':
                continue
            identity = record.get('snapshot', {}).get('identity', {})
            by_unit.setdefault(identity.get('id'), []).append(record)
        _source_cache.clear()  # Retain only one save's parsed history.
        _source_cache.update(key=key, records=by_unit)
    records = _source_cache['records'].get(unit_id, [])
    revision = hashlib.sha256(json.dumps(
        {'schema_version': VIEW_SCHEMA_VERSION, 'records': records},
        sort_keys=True).encode()).hexdigest()
    events = build_timeline(records)
    return records, events, revision


def process_views(save):
    directory = save / 'lorekeeper-views'
    latest = {}
    for path in sorted(directory.glob('*.request.json'), key=lambda p: p.stat().st_mtime_ns):
        prefix = path.name.split('.')[0]
        if prefix.isdigit():
            latest[prefix] = path
    for request_path in latest.values():
        request = load_results(request_path)
        unit_id = request.get('unit_id')
        if not isinstance(unit_id, int) or unit_id < 0:
            continue
        output = directory / f'{unit_id}.json'
        previous = load_results(output)
        same_schema = previous.get('schema_version') == VIEW_SCHEMA_VERSION
        if same_schema and previous.get('request') == request:
            if previous.get('state') in ('ready', 'empty'):
                continue
            if previous.get('state') == 'failed' and (
                    previous.get('attempts', 0) >= 3 or time.time() < previous.get('retry_at', 0)):
                continue
        if same_schema and previous.get('state') == 'ready' and time.time() - previous.get('updated_at', 0) < 30:
            continue  # Coalesce rapid reopen requests without repeated model calls.
        records, events, revision = prepare_view(save, unit_id)
        state = dict(schema_version=VIEW_SCHEMA_VERSION,
                     request=request, revision=revision, record_count=len(records),
                     event_count=len(events), state='processing', updated_at=time.time(),
                     story=previous.get('story'), story_revision=previous.get('story_revision'))
        state['attempts'] = previous.get('attempts', 0) if same_schema and previous.get('request') == request else 0
        # Pages stay bounded even for long histories. Publish before model work.
        for page, offset in enumerate(range(0, len(events), 20)):
            lines = []
            for index, event in enumerate(events[offset:offset + 20], offset + 1):
                when = event['time']
                lines.append(f"[{index}] {event['kind']}: year {when['year']}, tick {when['year_tick']}")
                lines.extend(event.get('changes', []))
                if event['kind'] == 'timeline_reset':
                    before = event['previous_time']
                    lines.append('New timeline segment: recorded game time moved backward from '
                                 f"year {before['year']}, tick {before['year_tick']}.")
                    lines.append('Fresh baseline; changes across this boundary are not inferred.')
                if event['kind'] == 'stress_trend':
                    lines.append(f"Stress: {event['from_stress']} to {event['to_stress']}")
            write_results(directory / f'{unit_id}.{revision}.{page}.json', {'lines': lines})
        state['pages'] = (len(events) + 19) // 20
        if not records:
            state['state'] = 'empty'
            write_results(output, state)
            continue
        if previous.get('story_revision') == revision:
            state['state'] = 'ready'
            write_results(output, state)
            continue
        write_results(output, state)
        item = dict(id=f'history-v{VIEW_SCHEMA_VERSION}:{unit_id}:{revision}', kind='dwarf_history',
                    raw=json.dumps({'schema_version': VIEW_SCHEMA_VERSION,
                                    'identity': records[-1]['snapshot']['identity'], 'events': events}),
                    context=('Write a concise factual history using only supplied events. Preserve Unicode names exactly. '
                             'A timeline_reset starts a separate recorded segment with a fresh baseline. '
                             'Time moved backward, possibly after loading an earlier save; the cause is unconfirmed. '
                             'Do not infer thought removals, stress changes, or causal continuity across segments. '
                             'Distinguish earlier recorded segments from the latest segment.'))
        try:
            if len(item['raw'].encode()) > 200000:
                raise ValueError('History exceeds the current story size limit; timeline is available.')
            result = run_batch([item])['results'][0]
            repair_story_names([item], [result])
            if len(result['text'].encode('utf-8')) > 8000:
                raise ValueError('Generated story exceeds the display size limit.')
            state.update(state='ready', story=result['text'], story_revision=revision)
        except Exception as error:
            state['attempts'] += 1
            state.update(state='failed', error=str(error)[-500:],
                         retry_at=time.time() + min(300, 15 * 2 ** state['attempts']))
        state['updated_at'] = time.time()
        write_results(output, state)
        # Only generated superseded page/request files are disposable.
        for page in directory.glob(f'{unit_id}.*.json'):
            parts = page.name.split('.')
            if len(parts) == 4 and len(parts[1]) == 64 and parts[2].isdigit() and parts[1] != revision:
                page.unlink(missing_ok=True)
        for old in directory.glob(f'{unit_id}.*.request.json'):
            if old != request_path and old.stat().st_mtime_ns <= request_path.stat().st_mtime_ns:
                old.unlink(missing_ok=True)
