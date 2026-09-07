"""Assemble verified annual facts with separately generated narrator reflection."""
import json
import re
from fortress_calendar import MONTHS
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


def schema(item):
    plan = paragraph_plan(json.loads(item['raw']))
    return {'type': 'object', 'additionalProperties': False,
            'required': [row['id'] for row in plan],
            'properties': {row['id']: {'type': 'string'} for row in plan}}


def assemble(item, response):
    raw = json.loads(item['raw'])
    plan = paragraph_plan(raw)
    if not isinstance(response, dict) or set(response) != {row['id'] for row in plan}:
        raise ValueError('Chronicle reflection count or identities do not match its plan')
    paragraphs, omitted = [], []
    for row in plan:
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


def editorial_reflection(text, raw):
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
    if any(name.casefold() in folded for name in names(raw) if name):
        return False
    return not re.search(r'\b(quick\w*|slow\w*|pain\w*|violent\w*|painless\w*|suffer\w*|'
                         r'kill\w*|dehydration|blood loss|neglect|guilt\w*)\b', folded)
