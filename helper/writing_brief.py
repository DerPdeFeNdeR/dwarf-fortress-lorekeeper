"""Qwen writing tasks compiled from already verified, knowledge-filtered evidence.

This module selects presentation context, never establishes personal knowledge.
Raw requests and production coverage requirements remain unchanged for audit.
"""
import json
from model_input import compact_raw
from memoire_brief import compile_personal


RULES = """Write readable literary prose using only this writing brief.
Names, actions, roles, dates and outcomes are facts; preserve them exactly.
Never invent dialogue, attendance, sources, sensory details, occupation routines,
causes, relationships, or fortress conditions. A profession is only a current title.
Voice instructions affect delivery, never facts or past personality. Express voice
through phrasing, not a list of traits. Interpretation of the narrator's own motives
must be signaled as interpretation. Another person's private thoughts may be
speculated about only when the brief supplies a reason (such as an observed action,
a stated thought or emotion, a known relationship, or a heard tale). Phrase that
inference as uncertain interpretation, never as inside knowledge.
The narrator may be unreliable about impressions, significance, and atmosphere;
those can be colored by personality and mood. Keep supplied facts, names, dates,
roles, and outcomes exact even when the narrator's interpretation is mistaken.
Supplied mood and emotional reactions may color the narrator's tone and attention,
but do not turn another dwarf's mood into the narrator's feeling or invent a mood
when none is supplied. Stable personality shapes the voice; mood shapes this telling.
Be warm for joys, restrained and compassionate for hardship. No caricatures,
writing-process commentary, evidence disclaimers, headings, or bullet lists.
Seeing a body is not witnessing death. Killed does not mean murdered. ANYTHING
supplies no emotion. Missing cups/wells say nothing about drink quality.
Heard tales retain the teller and listening framing: their subjects' dates and
actions are not the listener's experiences or the date of the telling. Explain
supplied organization types at first mention; never invent visits or affiliations.
Current relationships do not prove historical bonds or awareness of others' lives.
Include EVERY required fact sentence in the prose exactly once, unchanged.
Build connected prose around these sentences. Do not negate them or put them in
quotation marks. They outrank brevity. Use all required facts before adding reflection.
Return only the requested JSON with the request id and prose text.
"""

VOICE_FACETS = {
    'GREGARIOUSNESS': ('Use a reserved delivery.', 'Use an open, conversational delivery.'),
    'HUMOR': ('Keep the delivery earnest.', 'Allow gentle dry humor when the events permit it.'),
    'ASSERTIVENESS': ('Use a reflective delivery.', 'Use direct, decisive phrasing.'),
    'PRIVACY': ('Allow some emotional openness.', 'Keep emotional expression restrained.'),
    'IMAGINATION': ('Prefer concrete phrasing.', 'Allow restrained imagery without new sensory facts.'),
}
MENTAL_DELIVERY = {
    'LINGUISTIC_ABILITY': ('Use short, plain, grammatical sentences.', 'Use varied sentence structure.'),
    'ANALYTICAL_ABILITY': ('Keep organization straightforward.', 'Organize reflections carefully without inventing causes.'),
    'CREATIVITY': ('Favor concrete wording.', 'Allow restrained figurative language.'),
    'MEMORY': ('Stay focused on the supplied events; never invent forgetting.',
               'Emphasize supplied concrete details; never add missing ones.'),
}


def voice_guide(profile):
    facets = profile.get('personality_facets') or {}
    if isinstance(facets, list):
        facets = {row.get('facet_name'): row.get('value') for row in facets}
    guide = []
    for name, choices in VOICE_FACETS.items():
        value = facets.get(name)
        if isinstance(value, (int, float)) and (value <= 25 or value >= 75):
            guide.append(choices[int(value >= 75)])
    mental = (profile.get('mental_attributes') or {}).get('attributes') or {}
    for name, choices in MENTAL_DELIVERY.items():
        band = (mental.get(name) or {}).get('relative_level')
        if band in ('lower', 'higher'):
            guide.append(choices[int(band == 'higher')])
    return guide or ['Use natural, readable prose without an exaggerated voice.']


def explicit_values(profile):
    result = []
    for row in profile.get('values') or []:
        value = row.get('strength')
        if isinstance(value, (int, float)) and row.get('name'):
            stance = 'favors' if value > 0 else 'disfavors' if value < 0 else 'neutral about'
            result.append(f"{stance} {row['name'].lower()}; current explicit value, not past behavior")
    return result


def is_writing_task(item):
    if item['kind'] == 'fortress_year':
        return True
    if item['kind'] != 'dwarf_history':
        return False
    try:
        raw = json.loads(item['raw'])
        return isinstance(raw, dict) and 'chapter_evidence' in raw and 'chapter_title' in raw
    except (ValueError, TypeError):
        return False


def build_brief(item, options=None):
    raw = json.loads(item['raw'])
    required = raw.get('required_event_coverage', [])
    if item['kind'] == 'fortress_year':
        narrator = raw.get('narrator') or {}
        brief = {key: value for key, value in raw.items()
                 if key not in ('required_event_coverage', 'narrator')}
        brief['narrator'] = {key: narrator[key] for key in
                            ('status', 'name', 'histfig_id', 'values') if key in narrator}
        brief['narrator']['values'] = explicit_values(narrator)
        brief['voice'] = voice_guide(narrator)
        task = ('Write the fortress year as 4-8 connected paragraphs, at most 900 words. '
                'For sparse events use fewer paragraphs. Keep chronological month order. '
                'The year heading is supplied by the reader. Use the saved dwarf narrator\'s '
                'first-person voice when selected; otherwise use an unnamed external chronicler. '
                'Fortress events are reported history, never assumed eyewitness experience. '
                'A draft covers only the year so far. Do not repeat the opening month for nearby events. ')
        if raw.get('section_index'):
            task += ('This request is ONE section of the year: write 1-2 paragraphs for its events only. '
                     'Do not introduce yourself, summarize the whole year, or invent events in other seasons. ')
    else:
        profile = raw.get('biography_profile') or {}
        intro = raw['chapter_title'] == 'Introduction and recollections'
        brief, length = compile_personal(raw, options)
        intro_words = (options or {}).get('intro_words', [80, 140])
        brief['current_character_context']['values'] = explicit_values(profile)
        brief['voice'] = voice_guide(profile)
        task = ('Write in the named dwarf\'s first person. ' +
                (f'Write a short introduction and undated recollections in 1-3 paragraphs, normally {intro_words[0]}-{intro_words[1]} words. '
                 'Choose two or three recollections; do not catalogue every body sighting or repeat a recollection. '
                 'Do not date baseline memories by their observation time. ' if intro else
                 f'Write exactly one paragraph for this month, normally {length}. '
                 'Only chapter_evidence supplies this month\'s events. Do not repeat a character introduction. ')
                + 'Observations date noticing a change, not the original experience. '
                'Current character context guides reflection but supplies no new events for this month. '
                'Include every required fact even if it takes more words; never truncate a fact to fit. ')
    # Keep the validator's complete contract outside the prompt; one factual rendering
    # is easier for an 8B writer to follow than dozens of alternative clause patterns.
    brief['required_facts'] = [row['sentence'] for row in required]
    return task + RULES, compact_raw(json.dumps(brief, ensure_ascii=False))


def build_threaded_brief(item, options=None):
    """Personal Memoire variant with a small continuity thread, still evidence-bound."""
    prompt, evidence = build_brief(item, options)
    raw = json.loads(item['raw'])
    prior = raw.get('previous_chapter') or raw.get('prior_narrative')
    if isinstance(prior, dict):
        prior = prior.get('text')
    if isinstance(prior, str) and prior.strip():
        thread = compact_raw(json.dumps({'previous_passage_for_continuity': prior[-1200:]}, ensure_ascii=False))
    else:
        thread = '{"previous_passage_for_continuity":null}'
    guidance = """Continue a personal memory thread when one is supplied. Do not copy
the previous passage or treat its interpretations as facts. Let the current
month's evidence change, deepen, complicate, or answer an earlier concern.
Vary the opening: begin with an attention, question, reaction, or transition,
not automatically with 'I remember'. When several facts share the month, treat
them as a connected constellation: let contrast, consequence, accumulation, or a
shared concern join them instead of giving each fact its own event-then-reaction
sentence. Connect supplied facts to the dwarf's values, interests, supported
relationships, thoughts, or emotions when relevant. When several consequential
facts are available, choose one primary thread and weave in one or two meaningful
supporting moments. Group routine observations quietly or leave them out; do not
let one striking fact erase all other important things that happened in the month.
Treat supplied dwarf thoughts as direct evidence of what this dwarf noticed,
remembered, or felt. A death-related thought establishes awareness of the death
and its emotional weight, but never eyewitness attendance. Use the thought's
reaction as the dwarf's inner response; do not invent a stronger emotion when the
reaction is unspecified.
End with a present feeling or unresolved thought rather than a repeated summary.
This is a loose movement, not a visible formula; keep one natural paragraph.
"""
    return guidance + '\nContinuity thread:\n' + thread + '\n\n' + prompt, evidence


def prose_schema(items):
    return {'type': 'object', 'additionalProperties': False, 'required': ['results'],
            'properties': {'results': {'type': 'array', 'minItems': len(items), 'maxItems': len(items),
                'items': {'type': 'object', 'additionalProperties': False, 'required': ['id', 'text'],
                          'properties': {'id': {'type': 'string', 'enum': [item['id'] for item in items]},
                                         'text': {'type': 'string', 'minLength': 1}}}}}}


def adapt_prose(response):
    """Preserve the existing cache envelope without asking a writer to classify itself."""
    if not isinstance(response, dict) or not isinstance(response.get('results'), list):
        raise ValueError('Writer response needs a results array')
    rows = []
    for row in response['results']:
        if not isinstance(row, dict) or set(row) != {'id', 'text'}:
            raise ValueError('Writer result needs exactly id and text')
        rows.append(dict(row, explanation='Generated literary interpretation of supplied game events.',
                         category='narrative', confidence='low'))
    return dict(results=rows)
