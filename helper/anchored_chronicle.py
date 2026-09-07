"""Prepare and assemble annual fact anchors and narrator prose."""
import json
import re
from fortress_calendar import MONTHS, MONTH_TICKS
from writing_brief import voice_guide, explicit_values


def paragraph_plan(raw):
    groups = {}
    for row in raw.get('required_event_coverage', []):
        sentence = row['sentence']
        month = next((index for index, name in enumerate(MONTHS)
                      if sentence.startswith(f'In {name}, ')), len(MONTHS))
        groups.setdefault(month, []).append(sentence)
    return [{'id': f'p{index}', 'facts': groups[month]} for index, month in enumerate(sorted(groups))]


def supported(item):
    if item['kind'] != 'fortress_year':
        return False
    return bool(json.loads(item['raw']).get('required_event_coverage'))


def narrator_mood(raw, narrator):
    narrator_id = narrator.get('histfig_id')
    if not isinstance(narrator_id, int):
        return []
    moods = []
    for event in raw.get('events', []):
        if event.get('kind') != 'mood_change' or event.get('mood') is None:
            continue
        if any(row.get('histfig_id') == narrator_id and row.get('role') == 'subject'
               for row in event.get('participants', [])):
            moods.append({key: event[key] for key in ('mood', 'reason', 'month') if event.get(key) is not None})
    return moods[-4:]


def event_weather(raw):
    """Return optional same-day weather matches without making them events."""
    environment = raw.get('environment') or {}
    observations = environment.get('weather') if isinstance(environment, dict) else None
    if not isinstance(observations, list):
        return []
    result = []
    for event in raw.get('events', []):
        tick = event.get('tick')
        if not isinstance(tick, int):
            continue
        match = next((row for row in observations
                      if isinstance(row, dict) and isinstance(row.get('tick'), int)
                      and row['tick'] // 1200 == tick // 1200), None)
        if match:
            result.append(dict(event_id=event.get('id'),
                               month=MONTHS[tick // MONTH_TICKS] if 0 <= tick < 12 * MONTH_TICKS else None,
                               day=tick // 1200 % 28 + 1, weather=match.get('weather')))
    return [row for row in result if row.get('event_id') is not None and row.get('weather')]


def brief(item):
    raw = json.loads(item['raw'])
    narrator = raw.get('narrator') or {}
    context = dict(narrator={key: narrator[key] for key in ('status', 'name', 'values') if key in narrator},
                   voice=voice_guide(narrator), paragraphs=paragraph_plan(raw))
    context['narrator']['values'] = explicit_values(narrator)
    instructions = """Write ONE short reflective sentence for each paragraph id.
The application has already written each paragraph's facts; it will append your
reflection. Never repeat, paraphrase, correct or add to those facts. Return only
the requested JSON. An empty reflection is acceptable when nothing grounded fits.
Use the selected dwarf narrator's first-person voice (I/my), or an impersonal
reflection if no dwarf is selected. The voice guide affects phrasing only.
Never name a person, place, artifact or organization in the reflection; those
names are already in the factual sentences. Never describe the speed, pain,
violence or experience of death. Write only the narrator's present attitude. Use
"I find", "I think", "I would", or "Perhaps I" for a selected dwarf. Do not
describe how an event or death happened, what it felt like, or another person's
reaction. Do not make general medical claims or assertions about an artifact.
Examples of acceptable reflection: "I would rather remember the name than dress
the loss in grand words." "I find some comfort in an act of making."
"Perhaps I give titles less weight than the people who carry them."
These are examples of scope, not lines to copy in every paragraph.
Reflect with restraint and personality. Do not invent
events, intentions, causes, blame, neglect, guilt, sensory details, quotations,
visits, witnesses, rituals, shared emotions, past experience, or relationships.
Do not describe the fortress or its people beyond the supplied facts. Do not
claim attendance, knowing a person, hearing a tale, grief or memories merely
because you narrate history. Do not turn an artifact name into its properties.
Use perhaps/might for interpretations; never invent another person's motives.
Avoid stock stone-and-ale metaphors, repeated expressions, and writing-process
commentary. Joy may be warm; hardship requires compassion. Never make a death
into a joke. Each reflection must be at most 45 words, with no heading or list.
"""
    return instructions, json.dumps(context, ensure_ascii=False, separators=(',', ':'))


def weave_brief(item):
    """Give Qwen control of paragraph flow while keeping facts replaceable."""
    raw = json.loads(item['raw'])
    narrator = raw.get('narrator') or {}
    plan = paragraph_plan(raw)
    context = dict(narrator={key: narrator[key] for key in ('status', 'name', 'values') if key in narrator},
                   voice=voice_guide(narrator), mood=narrator_mood(raw, narrator), paragraphs=[])
    context['narrator']['values'] = explicit_values(narrator)
    for row in plan:
        context['paragraphs'].append(dict(id=row['id'],
            anchors=[f'{{{{A{index}}}}}' for index in range(len(row['facts']))], facts=row['facts']))
    instructions = """Write one complete, natural paragraph for each paragraph id.
Write as the saved dwarf narrator in first person when one is selected. Compose
all paragraphs as one remembered year with a deliberate arc. Make the voice
specific through rhythm, attention, restraint, and attitude. Give each paragraph
a beginning, a turn, and a close instead of a list. Use every supplied
anchor marker exactly once, in order, where it fits: {{A0}}, {{A1}}, and so on.
The application replaces markers with verified facts; do not alter or summarize
their wording. Write connective prose around them. The narrator may be mistaken
or biased about impressions, significance, or atmosphere; signal that uncertainty
with natural first-person phrasing. Subjective descriptors such as swift, grim,
or strange are welcome. Do not invent a new named person, event, dialogue,
witness, relationship, concrete physical detail, cause, or outcome.
Use interpretation for the narrator's attitude and, when the brief gives a reason,
for another dwarf's possible motives or feelings. Such inferences must be hedged
with perhaps, I think, or I wonder; never present unrecorded private thoughts as
inside knowledge. Never claim the narrator witnessed an event unless the supplied
fact says so. Avoid repeating any sentence or refrain across paragraphs. Keep each
paragraph under 150 words. Return only the requested JSON."""
    return instructions, json.dumps(context, ensure_ascii=False, separators=(',', ':'))


def schema(item):
    plan = paragraph_plan(json.loads(item['raw']))
    return {'type': 'object', 'additionalProperties': False,
            'required': [row['id'] for row in plan],
            'properties': {row['id']: {'type': 'string'} for row in plan}}


def weave_schema(item):
    return schema(item)


def stream_brief(item):
    """Ask Qwen for one connected train of thought with global fact anchors."""
    raw = json.loads(item['raw'])
    narrator = raw.get('narrator') or {}
    facts = [sentence for row in paragraph_plan(raw) for sentence in row['facts']]
    context = dict(narrator={key: narrator[key] for key in ('status', 'name', 'values') if key in narrator},
                   voice=voice_guide(narrator), mood=narrator_mood(raw, narrator),
                   calendar=[dict(index=index, month=month) for index, month in enumerate(MONTHS)],
                   event_weather=event_weather(raw),
                   anchors=[dict(id=f'A{index}', fact=fact) for index, fact in enumerate(facts)])
    context['narrator']['values'] = explicit_values(narrator)
    instructions = """Write one continuous Fortress Chronicle as a remembered train of thought.
Return one JSON object with a single `text` string. Write 4 to 6 readable paragraphs,
separated by a blank line. Write as the saved dwarf narrator
in first person when one is selected. Let memories, questions, comparisons, and
uncertainty carry the reader from one event to the next. The calendar runs in
this order: Granite, Slate, Felsite, Hematite, Malachite, Galena, Limestone,
Sandstone, Timber, Moonstone, Opal, Obsidian. Use that order when moving through
events; do not sort months alphabetically or infer a different sequence. Use each event as a
transition: let its consequence, contrast, or remembered meaning lead naturally
into the next event and the narrator's interpretation. Choose natural paragraph
breaks yourself; do not make every paragraph follow the same shape, and do not
reserve a fact for the end of a paragraph. Use every anchor marker exactly once,
in chronological order. The application replaces each marker with its verified
fact; do not alter, summarize, or repeat the fact. Never restate an event after
its anchor has appeared. Write connective prose around
the markers so they feel part of the narrator's thought rather than a report.
Do not add extra "In <month>" date openings around anchors. Let the supplied
anchors carry exact dates; use natural links such as "by then", "that season",
"later that year", or "afterward" when a transition needs a time reference.
Same-day weather is optional atmosphere, not an event or required fact. Use it
only when the event_id and day match, and never infer weather from a month or biome.
Personality, values, mental attributes, and supplied moods should affect what the
narrator notices, dwells on, and how they phrase uncertainty. The narrator may be
unreliable about impressions and significance. Another dwarf's possible motives
or feelings may be wondered about only when the brief gives a reason, and must be
hedged as inference, never stated as inside knowledge. Never invent a new named
person, event, dialogue, witness, relationship, concrete physical detail, cause,
or outcome. Never claim eyewitness knowledge unless supplied. Avoid repeated
sentences, stock refrains, and writing-process commentary. Keep the Chronicle
under 900 words. Return only the JSON object."""
    return instructions, json.dumps(context, ensure_ascii=False, separators=(',', ':'))


def stream_schema(item):
    return {'type': 'object', 'additionalProperties': False,
            'required': ['text'], 'properties': {'text': {'type': 'string'}}}


def assemble_stream(item, response):
    raw = json.loads(item['raw'])
    facts = [sentence for row in paragraph_plan(raw) for sentence in row['facts']]
    if not isinstance(response, dict) or set(response) != {'text'}:
        raise ValueError('Chronicle stream response must contain only text')
    text = response['text']
    if not isinstance(text, str) or len(text.split()) > 900:
        raise ValueError('Chronicle stream must be under 900 words')
    repaired = 0
    for index, fact in enumerate(facts):
        marker = f'{{{{A{index}}}}}'
        if text.count(marker) == 0 and text.count(fact) == 1:
            text = text.replace(fact, marker)
        elif text.count(marker) == 0 and text.count(fact) == 0:
            sentences = re.split(r'(?<=[.!?])\s+', text.strip()) if text.strip() else []
            slot = min(len(sentences), max(1, ((index + 1) * len(sentences)) // (len(facts) + 1)))
            sentences.insert(slot, marker)
            text = ' '.join(sentences)
            repaired += 1
        if text.count(marker) != 1:
            raise ValueError(f'Chronicle stream anchor {marker} must appear exactly once')
        text = text.replace(marker, fact)
    if re.search(r'\{\{A\d+\}\}', text):
        raise ValueError('Chronicle stream contains an unresolved anchor')
    seen, seen_facts = set(), set()
    fact_keys = {fact_key(fact) for fact in facts}
    removed = 0
    cleaned_paragraphs = []
    for paragraph in re.split(r'\n\s*\n+', text.strip()):
        kept = []
        for sentence in re.split(r'(?<=[.!?])\s+', paragraph.strip()):
            sentence = sentence.strip()
            if not sentence:
                continue
            key = sentence_key(sentence)
            normalized_fact = fact_key(sentence)
            is_fact = normalized_fact in fact_keys
            if key in seen and (not is_fact or normalized_fact in seen_facts):
                removed += 1
                continue
            if key:
                seen.add(key)
            if is_fact:
                seen_facts.add(normalized_fact)
            kept.append(sentence)
        if kept:
            cleaned_paragraphs.append(' '.join(kept))
    if len(cleaned_paragraphs) == 1:
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_paragraphs[0])
        paragraph_count = min(6, max(4, len(sentences) // 5)) if len(sentences) >= 12 else 2
        size, remainder = divmod(len(sentences), paragraph_count)
        shaped, start = [], 0
        for index in range(paragraph_count):
            end = start + size + (1 if index < remainder else 0)
            shaped.append(' '.join(sentences[start:end]))
            start = end
        cleaned_paragraphs = shaped
    fact_keys = {fact_key(fact) for fact in facts}
    shifted_openings = 0
    for index in range(1, len(cleaned_paragraphs)):
        current = re.split(r'(?<=[.!?])\s+', cleaned_paragraphs[index].strip())
        previous = re.split(r'(?<=[.!?])\s+', cleaned_paragraphs[index - 1].strip())
        if (len(previous) > 2 and current
                and fact_key(current[0]) in fact_keys):
            current.insert(0, previous.pop())
            cleaned_paragraphs[index - 1] = ' '.join(previous)
            cleaned_paragraphs[index] = ' '.join(current)
            shifted_openings += 1
    return {'results': [dict(id=item['id'], text='\n\n'.join(cleaned_paragraphs))],
            'writing_diagnostics': {'strategy': 'stream_verified_facts',
                                    'repaired_anchors': repaired,
                                    'removed_repeated_sentences': removed,
                                    'paragraphs': len(cleaned_paragraphs),
                                    'shifted_fact_openings': shifted_openings}}


def assemble(item, response):
    raw = json.loads(item['raw'])
    plan = paragraph_plan(raw)
    if not isinstance(response, dict) or set(response) != {row['id'] for row in plan}:
        raise ValueError('Chronicle reflection count or identities do not match its plan')
    paragraphs, omitted = [], []
    for paragraph_index, row in enumerate(plan):
        reflection = response[row['id']]
        if not isinstance(reflection, str) or len(reflection.split()) > 45 or '\n' in reflection:
            raise ValueError('Chronicle reflection must be one short passage')
        if not editorial_reflection(reflection, raw):
            omitted.append(row['id'])
            reflection = ''
        paragraphs.append(' '.join(row['facts']) + (' ' + reflection.strip() if reflection.strip() else ''))
    return {'results': [dict(id=item['id'], text='\n\n'.join(paragraphs))],
            'writing_diagnostics': {'omitted_reflections': omitted,
                                    'strategy': 'verified_facts_with_optional_reflection'}}


def assemble_weave(item, response):
    raw = json.loads(item['raw'])
    plan = paragraph_plan(raw)
    if not isinstance(response, dict) or set(response) != {row['id'] for row in plan}:
        raise ValueError('Chronicle woven paragraph count or identities do not match its plan')
    paragraphs = []
    repaired_anchors = 0
    generated_sentences = set()
    removed_repeated_sentences = 0
    for paragraph_index, row in enumerate(plan):
        text = response[row['id']]
        if not isinstance(text, str) or len(text.split()) > 150 or '\n' in text:
            raise ValueError('Chronicle woven paragraph must be one short passage')
        for index, fact in enumerate(row['facts']):
            # Qwen occasionally repeats an anchor before its marker; remove that
            # duplicate so the verified clause remains the single source of truth.
            text = text.replace(fact, '').strip()
            marker = f'{{{{A{index}}}}}'
            if text.count(marker) == 0 and text.count(fact) == 1:
                # Repair the common case where Qwen includes the exact anchor
                # but forgets to emit its marker.
                text = text.replace(fact, marker)
            elif text.count(marker) == 0 and text.count(fact) == 0:
                # Keep publication robust when Qwen returns prose without the
                # marker or exact anchor. Insert the verified sentence at a
                # sentence boundary so facts do not always become the ending.
                parts = re.split(r'(?<=[.!?])\s+', text.strip()) if text.strip() else []
                slot = min(len(parts), max(1, ((paragraph_index + index + 1) * len(parts))
                             // (len(row['facts']) + 1)))
                parts.insert(slot, marker)
                text = ' '.join(parts).strip()
                repaired_anchors += 1
            if text.count(marker) != 1:
                raise ValueError(f'Chronicle anchor {marker} must appear exactly once')
            text = text.replace(marker, fact)
        if re.search(r'\{\{A\d+\}\}', text):
            raise ValueError('Chronicle woven prose contains an unresolved anchor')
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        kept = []
        facts = set(row['facts'])
        for sentence in sentences:
            key = sentence_key(sentence)
            if key in generated_sentences and sentence.strip() not in facts:
                removed_repeated_sentences += 1
                continue
            if key:
                generated_sentences.add(key)
            kept.append(sentence)
        paragraphs.append(' '.join(kept).strip())
    return {'results': [dict(id=item['id'], text='\n\n'.join(paragraphs))],
            'writing_diagnostics': {'strategy': 'woven_verified_facts', 'paragraphs': len(plan),
                                    'repaired_anchors': repaired_anchors,
                                    'removed_repeated_sentences': removed_repeated_sentences}}


def editorial_reflection(text, raw, reject_names=True):
    """Bounded scope guard, not semantic verification of arbitrary generated prose."""
    def names(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('name', 'site_name', 'artifact_name', 'entity_name', 'target_name') and isinstance(item, str):
                    yield item
                else:
                    yield from names(item)
        elif isinstance(value, list):
            for item in value:
                yield from names(item)
    folded = text.casefold()
    if reject_names and any(name.casefold() in folded for name in names(raw) if name):
        return False
    return not re.search(r'\b(quick\w*|slow\w*|pain\w*|violent\w*|painless\w*|suffer\w*|'
                         r'kill\w*|dehydration|blood loss|neglect|guilt\w*)\b', folded)


def woven_prose_is_safe(text):
    """Compatibility hook: subjective and unreliable narrator color is allowed."""
    return isinstance(text, str) and bool(text.strip())


def sentence_key(sentence):
    sentence = re.sub(r'\s+', ' ', sentence.strip().casefold())
    return sentence if len(sentence.split()) > 4 else ''


def fact_key(sentence):
    """Normalize an anchor for duplicate detection without changing display text."""
    sentence = re.sub(r'^in (granite|slate|felsite|hematite|malachite|galena|'
                      r'limestone|sandstone|timber|moonstone|opal|obsidian),\s+',
                      '', sentence.strip().casefold())
    return re.sub(r'\s+', ' ', sentence)
