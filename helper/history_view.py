"""Prepare bounded history views outside the game thread."""
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from codex_batch import run_batch, generation_settings
from process_queue import load_queue, load_results, write_results, repair_story_names
from historian import HISTORIAN_CONTEXT, STORY_NOTICE, restore_reference_names
from story_input import build_story_input, story_key, stable_json
from story_coverage import CoverageError, validate as validate_coverage
from biography_updates import APPEND_CONTEXT, load_memory, plan, checkpoint, make_memory

_source_cache = {}
VIEW_SCHEMA_VERSION = 17


def load_profile(directory, request):
    name = request.get('profile_file')
    if not name:
        return None
    if not isinstance(name, str) or '/' in name or '\\' in name or not name.endswith('.profile.json'):
        raise ValueError('Invalid biography profile filename')
    with (directory / name).open('rb') as source:
        raw = source.read(131073)
    if len(raw) > 131072:
        raise ValueError('Biography profile exceeds 128 KiB')
    profile = json.loads(raw.decode('utf-8'))
    if not isinstance(profile, dict) or profile.get('unit_id') != request['unit_id']:
        raise ValueError('Biography profile belongs to another dwarf')
    return profile


def profile_revision(revision, profile):
    if profile is None:
        return revision
    # Request time alone should not trigger fresh model work.
    context = {key: value for key, value in profile.items() if key != 'captured_at'}
    return hashlib.sha256(json.dumps([revision, context], sort_keys=True).encode()).hexdigest()


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
    jobs = []
    for path in sorted(directory.glob('*.request.json'), key=lambda p: p.stat().st_mtime_ns):
        prefix = path.name.split('.')[0]
        if prefix.isdigit():
            latest[prefix] = path
    for request_path in reversed(list(latest.values())):
        request = load_results(request_path)
        unit_id = request.get('unit_id')
        if not isinstance(unit_id, int) or unit_id < 0:
            continue
        output = directory / f'{unit_id}.json'
        previous = load_results(output)
        same_schema = previous.get('schema_version') == VIEW_SCHEMA_VERSION
        if previous.get('request') == request and previous.get('state') in ('ready', 'empty'):
            continue  # A schema deployment must not regenerate every dormant dwarf.
        if same_schema and previous.get('request') == request:
            if previous.get('state') == 'failed' and (
                    previous.get('attempts', 0) >= 3 or time.time() < previous.get('retry_at', 0)):
                continue
        started_at = time.time()
        preparation_start = time.perf_counter()
        records, events, revision = prepare_view(save, unit_id)
        try:
            profile = load_profile(directory, request)
        except (OSError, ValueError) as error:
            write_results(output, dict(state='failed', request=request,
                                      error='Could not load biography profile: ' + str(error)))
            continue
        revision = profile_revision(revision, profile)
        payload = build_story_input(records[-1]['snapshot']['identity'] if records else {}, events, profile)
        settings = generation_settings()
        semantic_key = story_key(payload, [VIEW_SCHEMA_VERSION, settings, HISTORIAN_CONTEXT])
        memory_path = directory / f'{unit_id}.biography-memory.json'
        memory = load_memory(memory_path, previous.get('story')) if same_schema else None
        if memory and memory.get('generation') != settings:
            memory = None
        update = plan(memory, previous, payload, records, request)
        state = dict(schema_version=VIEW_SCHEMA_VERSION,
                     request=request, revision=revision, record_count=len(records),
                     event_count=len(events), state='processing', updated_at=time.time(),
                     story=previous.get('story'), story_revision=previous.get('story_revision'),
                     story_explanation=previous.get('story_explanation'),
                     story_notice=previous.get('story_notice'),
                     story_key=previous.get('story_key'),
                     biography_update=dict(mode=update['mode'], reason=update['reason']),
                     generation=settings, story_generation=previous.get('story_generation'),
                     timings={'queue_seconds': max(0, started_at - request.get('nonce', started_at)),
                              'generation_seconds': 0, 'cache_hit': False})
        state['attempts'] = previous.get('attempts', 0) if same_schema and previous.get('request') == request else 0
        state['historical_event_coverage'] = (profile or {}).get('historical_events', {}).get('coverage', {})
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
        state['timings']['preparation_seconds'] = time.perf_counter() - preparation_start
        state['updated_at'] = time.time()
        if not records:
            state['state'] = 'empty'
            write_results(output, state)
            continue
        if update['mode'] == 'defer':
            # Keep the story's evidence checkpoint intact so minor developments
            # accumulate across visits. The prepared timeline is still current.
            state['state'] = 'ready'
            state['timings']['cache_hit'] = True
            state['timings']['total_seconds'] = time.time() - request.get('nonce', started_at)
            write_results(output, state)
            continue
        if update['reason'] in ('incompatible_history', 'timeline_reset', 'revised_timeline_or_reset'):
            state['story_key'] = None
        if same_schema and previous.get('story_key') == semantic_key and previous.get('story') and update['reason'] not in (
                'incompatible_history', 'timeline_reset', 'revised_timeline_or_reset'):
            try:
                state['story_coverage'] = validate_coverage(previous['story'], payload['required_event_coverage'])
            except CoverageError:
                state['story_key'] = None
        if same_schema and state.get('story_key') == semantic_key and previous.get('story'):
            state['state'] = 'ready'
            state['story_revision'] = revision
            state['timings']['cache_hit'] = True
            state['biography_update'] = dict(mode='reuse', reason='unchanged_evidence')
            if memory:
                write_results(memory_path, dict(memory, checkpoint=checkpoint(records, request)))
            state['timings']['total_seconds'] = time.time() - request.get('nonce', started_at)
            write_results(output, state)
            continue
        write_results(output, state)
        item = dict(id=f'history-v{VIEW_SCHEMA_VERSION}:{unit_id}:{revision}', kind='dwarf_history',
                    raw=stable_json(dict(update['payload'], schema_version=VIEW_SCHEMA_VERSION)),
                    context=HISTORIAN_CONTEXT + (APPEND_CONTEXT if update['mode']=='append' else ''))
        state['timings']['payload_bytes'] = len(item['raw'].encode('utf-8'))
        jobs.append((request_path, output, state, item, profile, semantic_key,
                     payload, checkpoint(records, request), memory))
    # Publish every discovered timeline before waiting for any model call.
    for job in jobs:
        complete_story(*job)


def complete_story(request_path, output, state, item, profile, semantic_key,
                   payload, records_checkpoint, memory):
    generation_start = time.perf_counter()
    request = state['request']
    state['timings']['model_queue_seconds'] = max(0, time.time() - state['updated_at'])
    try:
        if len(item['raw'].encode('utf-8')) > 200000:
            raise ValueError('History exceeds the current story size limit; timeline is available.')
        result = run_batch([item], settings=state['generation'])['results'][0]
        repair_story_names([item], [result])
        result['text'] = restore_reference_names(result['text'], profile)
        text = result['text'].strip()
        if not text:
            raise ValueError('Generated biography is empty.')
        validate_coverage(text, json.loads(item['raw']).get('required_event_coverage', []))
        if state['biography_update']['mode'] == 'append':
            if len(text.encode('utf-8')) > 2000:
                raise ValueError('Biography continuation exceeds the size limit.')
            if any(p.strip() in state['story'] for p in text.split('\n\n') if p.strip()):
                raise ValueError('Biography continuation repeats an existing paragraph.')
            text = state['story'] + '\n\n' + text
        if len(text.encode('utf-8')) > 8000:
            raise ValueError('Generated story exceeds the display size limit.')
        coverage = validate_coverage(text, payload.get('required_event_coverage', []))
        next_memory = make_memory(payload, records_checkpoint, text,
                                  state['biography_update']['mode'], memory, state['generation'])
        write_results(output.with_name(f"{request['unit_id']}.biography-memory.json"), next_memory)
        state.update(state='ready', story=text, story_revision=state['revision'],
                     story_explanation=result.get('explanation', ''),
                     story_notice=STORY_NOTICE, story_key=semantic_key,
                     story_generation=state['generation'], story_coverage=coverage)
    except CoverageError as error:
        # No hidden regeneration loop: keep the previous prose, visibly failed.
        state.update(state='failed', error=str(error), attempts=3,
                     retry_at=time.time()+300, error_kind='event_coverage')
    except Exception as error:
        state['attempts'] += 1
        state.update(state='failed', error=str(error)[-500:],
                     retry_at=time.time() + min(300, 15 * 2 ** state['attempts']))
    state['updated_at'] = time.time()
    state['timings']['generation_seconds'] = time.perf_counter() - generation_start
    state['timings']['total_seconds'] = state['updated_at'] - request.get('nonce', state['updated_at'])
    write_results(output, state)
    directory, unit_id, revision = output.parent, request['unit_id'], state['revision']
    # Only generated superseded page/request files are disposable.
    for page in directory.glob(f'{unit_id}.*.json'):
        parts = page.name.split('.')
        if len(parts) == 4 and len(parts[1]) == 64 and parts[2].isdigit() and parts[1] != revision:
            page.unlink(missing_ok=True)
    for old in directory.glob(f'{unit_id}.*.request.json'):
        if old != request_path and old.stat().st_mtime_ns <= request_path.stat().st_mtime_ns:
            old_profile = load_results(old).get('profile_file', '')
            if (isinstance(old_profile, str) and old_profile.startswith(f'{unit_id}.')
                    and old_profile.endswith('.profile.json')
                    and '/' not in old_profile and '\\' not in old_profile):
                (directory / old_profile).unlink(missing_ok=True)
            old.unlink(missing_ok=True)
