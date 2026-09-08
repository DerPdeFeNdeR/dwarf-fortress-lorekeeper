"""On-demand monthly books. All history/model work stays outside DFHack."""
import copy
import json
import time

from biography_updates import checkpoint, digest
from biography_significance import assess
from heard_stories import anchor
from historian import HISTORIAN_CONTEXT, STORY_NOTICE, restore_reference_names
from process_queue import write_results, repair_story_names
from story_coverage import CoverageError, requirements, validate
import re
from story_input import stable_json
from fortress_calendar import MONTH_TICKS, MONTHS
from environment import ATMOSPHERE_CONTEXT, personal as personal_environment

VERSION = 2  # Archive old evidence/prose so omniscient passages cannot seed new chapters.
CHAPTER_CONTEXT = """
This is ONE chapter of a monthly memoire, overriding full-biography length and
opening instructions. Return only its prose. A monthly chapter must be exactly
ONE narrative paragraph, normally 100-180 words, never more than 300 words.
The introduction may use 1-3 short paragraphs. Do not include a heading.
Rewrite this chapter as one coherent passage
when updating it; do not append another list or repeat its opening portrait.
For Introduction and recollections, write a short character introduction and
undated memories. Never assign a date to a memory from its capture/recall time.
For a monthly chapter, only chapter_evidence supplies events for that month.
Observation rows date noticing a change, NOT the original occurrence of a thought.
Describe changing recollections without claiming an old death/birth happened then.
A heard story belongs to heard_time, not the year of the story's subject.
biography_profile is CURRENT context, not proof of past values or relationships.
prior_narrative and previous_chapter are generated interpretation, never evidence.
Use them for restrained callbacks, not new facts or repetition. Do not summarize
other months. Use natural storytelling, not a likes/dislikes inventory. Keep
technical evidence limitations and writing-process commentary out of the prose.
Integrate every required_event_coverage sentence verbatim in this chapter.
""" + ATMOSPHERE_CONTEXT


def month_key(when):
    when = when or {}
    year, tick = when.get('year'), when.get('tick', when.get('year_tick'))
    if (type(year) is not int or year < 0 or type(tick) is not int
            or not 0 <= tick < 12 * MONTH_TICKS):
        return None
    return f'{year:06d}-{tick // MONTH_TICKS:02d}'


def chapter_text(key, text):
    """Keep monthly prose one paragraph without dropping facts or Unicode."""
    return text.strip() if key == 'intro' else ' '.join(text.split())


def title(key):
    if key == 'intro':
        return 'Introduction and recollections'
    year, month = map(int, key.split('-'))
    return f'Year {year} / {MONTHS[month]}'


def partition(payload, request):
    """Only verified dates get months; baseline thoughts remain recollections."""
    groups = {'intro': {}}
    now = (request.get('year', 0), request.get('tick', 0))
    def add(source, row, when, identity):
        when = when or {}
        year = when.get('year')
        tick = when.get('tick', when.get('year_tick'))
        if type(year) is int and (year, tick if type(tick) is int else 0) > now:
            return
        key = month_key(when) or 'intro'
        groups.setdefault(key, {})[source + ':' + str(identity)] = dict(source=source, value=row)
    for row in payload.get('events', []):
        if row['kind'] == 'baseline':
            groups['intro']['baseline'] = dict(source='baseline', value=row)
        else:
            # Stable observation identity permits correcting enrichment in place.
            add('observation', row, row.get('time'), stable_json(row.get('time')))
    for row in payload.get('historical_episodes', {}).get('events', []):
        add('historical', row, row.get('time'), row['source_key'])
    for row in payload.get('life_events', {}).get('events', []):
        add('life', row, row.get('time'), stable_json([row.get('kind'), row.get('source_keys'),
            (row.get('person') or {}).get('histfig_id')]))
    for row in payload.get('heard_stories', []):
        add('heard', row, row.get('heard_time'), row['subject_key'])
    return groups


def read_json(path, limit=2000000):
    if not path.exists():
        return {}
    with path.open('rb') as source:
        raw = source.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Monthly memoire storage limit exceeded')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('Invalid monthly memoire document')
    return value


def compatible(book, records, request):
    old = book.get('checkpoint', {})
    count = old.get('record_count', -1)
    current = checkpoint(records, request)
    return (0 <= count <= len(records) and digest(records[:count]) == old.get('records_digest')
            and current['resets'] == old.get('resets')
            and current['requested_time'] >= old.get('requested_time', [0, 0]))


def evidence_payload(evidence, identity, narrator_id=None):
    rows = list(evidence.values())
    episodes = {'events': [r['value'] for r in rows if r['source'] == 'historical']}
    heard = [r['value'] for r in rows if r['source'] == 'heard']
    return dict(events=[r['value'] for r in rows if r['source'] == 'observation'],
                historical_episodes=episodes, heard_stories=heard,
                required_event_coverage=requirements(episodes, narrator_id)
                    + anchor(identity, heard, first_person=True))


def important(old, current, identity):
    if any(key not in current for key in old):
        return True
    additions = {key: row for key, row in current.items() if key not in old}
    if any(key in old and row != old[key] for key, row in current.items()):
        return True  # A correction is an explicit exception to stable closed months.
    if any(row['source'] == 'life' for row in additions.values()):
        return True
    before, after = evidence_payload(old, identity), evidence_payload(current, identity)
    delta = evidence_payload(additions, identity)
    if any(any(s.startswith('profession changed') for s in e.get('changes', []))
           for e in delta['events']):
        return True
    return bool(assess(before, after, delta['events'], delta['historical_episodes']['events']))


def intro_context(payload):
    profile = payload.get('biography_profile') or {}
    return dict(identity=payload.get('identity'), profile={k: profile[k] for k in (
        'relationships', 'friends', 'values', 'preferences', 'personality_facets',
        'mental_attributes', 'age') if k in profile})


def publish_catalog(directory, unit, book, state):
    entries = []
    for key in sorted(book['chapters'], reverse=True):
        row = book['chapters'][key]
        if row.get('file'):
            entries.append(dict(key=key, title=title(key), file=row['file']))
    # Introduction first, then the newest recorded month and older months.
    intro = [r for r in entries if r['key'] == 'intro']
    monthly = [r for r in entries if r['key'] != 'intro']
    state['chapters'] = intro + monthly[:99]
    state['chapters_truncated'] = len(monthly) > 99
    state['monthly_version'] = VERSION
    if entries:
        selected = state['chapters'][0]
        chapter = read_json(directory / selected['file'], 65536)
        state['story'] = chapter['text']
        state['story_notice'] = STORY_NOTICE


def save_book(path, book):
    if len(json.dumps(book, ensure_ascii=True, indent=2, sort_keys=True).encode()) > 1900000:
        raise ValueError('Monthly memoire evidence capacity reached; saved chapters are preserved.')
    write_results(path, book)


def process(directory, state, payload, records, profile, generate):
    """Publish at most one changed chapter per watcher cycle; resume pending work."""
    unit = state['request']['unit_id']
    path = directory / f'{unit}.monthly-book.json'
    book = read_json(path)
    if book and (book.get('version') != VERSION or not compatible(book, records, state['request'])):
        # Immutable revision files and this archived manifest retain the old branch.
        write_results(directory / f'{unit}.monthly-archive.{digest(book)}.json', book)
        book = {}
        state['story'] = None
    if not book:
        book = dict(version=VERSION, chapters={}, heard={})
    candidates = partition(payload, state['request'])
    # Hearing the same tale next month is not a fresh chapter. Keep its first
    # saved listening date, but allow corrected subject details at that location.
    for key, evidence in list(candidates.items()):
        for identity, row in list(evidence.items()):
            if row['source'] != 'heard':
                continue
            location = book['heard'].setdefault(identity, key)
            prior = book['chapters'].get(location, {}).get('evidence', {}).get(identity)
            if prior and all(prior['value'].get(k) == row['value'].get(k)
                             for k in ('topic','performers','site_id')):
                del evidence[identity]
                continue
            if location != key:
                del evidence[identity]
                if prior:
                    corrected = copy.deepcopy(prior)
                    for k in ('topic','performers','site_id'):
                        corrected['value'][k] = row['value'].get(k)
                    candidates.setdefault(location, {})[identity] = corrected
    if len(book['chapters']) > 1200 or len(book['heard']) > 2000:
        raise ValueError('Monthly archive capacity reached; saved chapters remain available.')
    pending = []
    context = intro_context(payload)
    writer = digest([VERSION, state['generation'], HISTORIAN_CONTEXT, CHAPTER_CONTEXT])
    for key, incoming in candidates.items():
        # A corrected event date moves that event, rather than duplicating it
        # in two months. Old immutable chapter revisions remain on disk.
        for identity, row in incoming.items():
            if row['source'] not in ('historical', 'life'):
                continue
            for other_key, other in book['chapters'].items():
                if other_key != key:
                    other['evidence'].pop(identity, None)
        chapter = book['chapters'].setdefault(key, dict(evidence={}, written={}))
        chapter['evidence'].update(incoming)
    for key, chapter in book['chapters'].items():
        if key != 'intro' and not chapter['evidence']:
            chapter.pop('file', None)
            chapter['written'] = {}
            continue
        changed = (important(chapter['written'], chapter['evidence'], payload['identity'])
                   if key != 'intro' else not chapter.get('file') or chapter.get('context') != context
                   or chapter['written'] != chapter['evidence'])
        if chapter.get('file') and chapter.get('writer') != writer:
            changed = True
        if changed:
            pending.append(key)
    book['checkpoint'] = checkpoint(records, state['request'])
    # Save pending evidence without advancing a chapter's written checkpoint.
    save_book(path, book)
    publish_catalog(directory, unit, book, state)
    if not pending:
        state.update(state='ready', biography_update=dict(mode='defer', reason='no_significant_developments'))
        state['timings']['cache_hit'] = True
        return
    # Prepare the opening page first, then newest-to-oldest monthly chapters.
    months = sorted((k for k in pending if k != 'intro'), reverse=True)
    key = 'intro' if 'intro' in pending else months[0]
    chapter = book['chapters'][key]
    evidence = chapter['evidence']
    required = evidence_payload(evidence, payload['identity'],
        (payload.get('biography_profile') or {}).get('histfig_id'))['required_event_coverage']
    earlier = sorted((k for k, v in book['chapters'].items() if k != 'intro' and k < key and v.get('file')), reverse=True)[:2]
    if book['chapters'].get('intro', {}).get('file') and key != 'intro':
        earlier.append('intro')
    prior = [read_json(directory / book['chapters'][k]['file'], 65536)['text'] for k in earlier]
    raw = dict(identity=payload['identity'], chapter_title=title(key), chapter_evidence=evidence,
               environment=personal_environment(directory.parent,state['request'],key),
               biography_profile=payload.get('biography_profile'), required_event_coverage=required,
               prior_narrative=dict(kind='generated_interpretation', text='\n\n'.join(prior)[:12000]),
               previous_chapter=read_json(directory / chapter['file'], 65536).get('text') if chapter.get('file') else None)
    item = dict(id=f'monthly:{unit}:{key}:{digest(raw)}', kind='dwarf_history',
                raw=stable_json(raw), context=HISTORIAN_CONTEXT + CHAPTER_CONTEXT)
    if len(item['raw'].encode()) > 200000:
        raise ValueError('Monthly chapter evidence exceeds the model input limit')
    state.update(state='processing', biography_update=dict(mode='monthly', reason='significant_chapter_update'))
    state['pending_chapters'] = len(pending)
    state['timings']['payload_bytes'] = len(item['raw'].encode())
    write_results(directory / f'{unit}.json', state)
    start = time.perf_counter()
    batch = generate([item], settings=state['generation'])
    result = batch['results'][0]
    repair_story_names([item], [result])
    text = chapter_text(key, restore_reference_names(result['text'], profile))
    if not text or len(text.encode()) > 8000:
        raise ValueError('Monthly chapter is empty or exceeds 8000 bytes')
    try:
        coverage = validate(text, required)
    except CoverageError:
        if state['generation']['strategies'].get('memoire') != 'personal-thread':
            raise
        # Qwen sometimes omits a required sentence despite the prompt. Insert
        # only the missing verified facts into the existing paragraph; do not
        # invent connective prose or retry the model.
        present = set()
        for row in required:
            if row['event_id'] not in present:
                try:
                    validate(text, [row])
                    present.add(row['event_id'])
                except CoverageError:
                    pass
        missing = [row['sentence'] for row in required if row['event_id'] not in present]
        sentences = re.split(r'(?<=[.!?])\s+', text.strip()) if text.strip() else []
        for index, sentence in enumerate(missing):
            slot = min(len(sentences), max(1, ((index + 1) * len(sentences)) // (len(missing) + 1)))
            sentences.insert(slot, sentence)
        text = ' '.join(sentences)
        coverage = validate(text, required)
    document = dict(title=title(key), key=key, evidence_digest=digest(evidence),
                    text=text, coverage=coverage, generation=state['generation'])
    document.update(writing=batch.get('writing'), model_metrics=batch.get('model_metrics'))
    filename = f'{unit}.monthly.{digest(document)}.json'
    write_results(directory / filename, document)
    chapter.update(file=filename, written=copy.deepcopy(evidence), context=context, writer=writer)
    save_book(path, book)
    publish_catalog(directory, unit, book, state)
    state.update(state='processing' if len(pending) > 1 else 'ready', story_revision=state['revision'],
                 pending_chapters=len(pending)-1, story_generation=state['generation'])
    state['timings']['generation_seconds'] = time.perf_counter() - start
