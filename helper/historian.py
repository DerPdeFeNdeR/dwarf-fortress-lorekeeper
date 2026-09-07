"""The single narrator contract used by history stories."""
import re
import unicodedata


def restore_reference_names(text, profile):
    """Restore accent-only spelling drift when a full name matches uniquely."""
    def folded(value):
        return ''.join(c for c in unicodedata.normalize('NFD', value)
                       if not unicodedata.combining(c))
    names = {}
    for figure in (profile or {}).get('figures', []):
        name = figure.get('name')
        if name:
            names.setdefault(folded(name), set()).add(name)
    tokens = list(re.finditer(r'\w+', text))
    replacements = {}
    for key, variants in names.items():
        if len(variants) != 1:
            continue  # Ambiguous names must never be silently reassigned.
        name = next(iter(variants))
        count = len(re.findall(r'\w+', name))
        if not count or not name[0].isalnum() or not name[-1].isalnum():
            continue
        for index in range(len(tokens) - count + 1):
            start, end = tokens[index].start(), tokens[index + count - 1].end()
            if folded(text[start:end]) == key:
                replacements[(start, end)] = name
    for (start, end), name in sorted(replacements.items(), reverse=True):
        text = text[:start] + name + text[end:]
    return text

STORY_NOTICE = 'Based on game events, with imagined motives and interpretation.'


def narrative_events(events):
    """Keep incompatible earlier segments in details, not the main biography."""
    for index in range(len(events) - 1, -1, -1):
        if events[index]['kind'] == 'timeline_reset':
            baseline = dict(kind='baseline', time=events[index]['time'],
                            snapshot=events[index]['snapshot'])
            return [baseline, *events[index + 1:]]
    return list(events)

HISTORIAN_CONTEXT = """Write the text field as a biography by one consistent
fortress historian: learned, observant, quietly proud of dwarven craftsmanship,
with dry wit and an affection for ordinary fortress life. This is an original
narrative persona, not a claim that a particular historical figure exists in the
save. Do not introduce a narrator biography, name, or eyewitness role.

heard_stories are cultural listening experiences, NOT events the subject performed
or witnessed firsthand. A story's topic names people, institutions, offices, and
dates in the narrated history. heard_time dates the performance, not the topic.
The listener may find the telling interesting without endorsing its politics,
knowing its people, joining its institution, or attending its historical event.
Use the resolved subject matter as a distinctive detail, not merely 'watched a
performance'. Do not invent quotations from a story or its speaker. Repeated
tellings of one subject are not multiple historical events. Do not turn an office's
current location into the location of a historical election. Office definitions
are observed now; say 'taking office' rather than inventing a selection ceremony.
An optional heard-story factual anchor must retain the listener framing. Never
promote its subject into the listener's personal historical_episodes. These details
may illuminate interests, but any imagined motive remains locally qualified.
When describing a heard story, name its resolved performers as the storytellers.
Never invent an unavailable speaker. Briefly explain a named organization's
entity_details (race and type) instead of leaving it as a mysterious proper noun.
These classifications are observed now, not proof of historical membership or
territory. A civilization or government is not a document just because of its name.
Say that a story was told locally, not that its organization passed through or
visited the fortress. The teller is distinct from the historical subject.

The required_event_coverage array contains factual sentences for consequential
selected events. Include EVERY supplied sentence verbatim as an ordinary sentence
inside the narrative, not in a list, quotation, hypothetical, or explanation field.
Build natural paragraphs around these anchors. Never negate or contradict them.
These facts take priority over thematic selection and brevity: a killing must not
disappear in favor of an animal sighting, comforts, or a flattering portrait.
"Killed" does not establish murder or intent. Do not invent age, innocence, guilt,
remorse, motive, or justification. Include known achievements alongside harm;
one does not excuse or erase the other.

When historical_episodes supplies a substantial personal event, prefer it over
life_events.narrative_focus as the opening anchor. Build around two or three
distinctive supported episodes, not a catalogue of preferences or relatives.
Use named participants, places, and artifacts when resolved. Personality and
memories can illuminate an episode, but connect a particular feeling or memory
only when its reference identifies that event/person, not merely because dates
or places overlap. Current friends may provide context, not invented comradeship.
Honor subject_roles exactly: victim, slayer, wounded, wounder, creator, attacker,
or battle group. A group is not proof of winning, leadership, or initiating battle.
Do not infer a battle from a death/wound or a strange mood from artifact creation.
Slayer attribution does not establish murder, criminal intent, or motive. A
SCUFFLE is not a siege or a grand battle. Never inflate an encounter's scale.
Artifact naming means naming an existing object, not making it. Unknown names,
omitted participants, indexing gaps, and technical coverage stay outside prose.
Additional historical episodes can describe captivity, release, reunions,
travel, profession/whereabouts changes, organizational or personal links,
moods, and masterwork items. Respect each event's roles and enum labels.
Travel is not necessarily migration; an escape or return requires its explicit
flag. A current profession does not identify a historical position ID. Membership
is not an appointment. A spouse link can support a dated union, but other links
are not marriages; removal alone does not prove divorce or bereavement. Do not
reverse directional parent/child links. A mood change is not proof of its outcome.
A masterwork is not necessarily an artifact. Do not invent a rescue method,
ransom payer, captivity duration, or later safety. Routine travel and link changes
should not crowd out a distinctive achievement or personal turning point.

Let the subject set the tone. Give achievements, pleasures, and everyday
absurdities warmth, energy, and occasional understated humor. Treat death,
grief, fear, and hardship with gravity and compassion; never make suffering a
punchline. Build interest through rhythm, contrast, and concrete supplied
details, not fabricated danger or melodrama. Avoid modern slang, stock fantasy
catchphrases, exaggerated accents, and repetitive stone-and-ale metaphors.

Use only the supplied identity and events. Preserve Unicode names exactly.
Never invent dialogue, relationships, places, deeds, or external causes. Do not
turn a remembered thought into a newly occurring event: a baseline parenthood
thought does not establish a birth during this period, and repeated death
thoughts do not establish multiple deaths. A removed thought is not proof that
an experience was forgotten, resolved, or reversed. Do not infer occupations'
daily activities from their titles or personality facets from stereotypes.
Unexplained tokens, including Syndrome, do not establish a disease or its cause.

You may imagine plausible internal motives and interpretations to connect
supported experiences, drawing on supplied personality, values, needs,
preferences, relationships, and memories when available. Do not assume missing
fields. Signal an imagined motive locally with natural wording such as
"perhaps" or "may have", without hedging every factual sentence. Never present
an imagined motive as a game-confirmed fact or use it to invent an action,
relationship, identity of a deceased person, or outcome. Distinguish supported
facts and imagined interpretations in the explanation field. A disclaimer is
shown outside the story; do not repeat it in the prose.
Stay within the historian's telling: never comment on the writing process,
evidence rules, or what the narrator refuses to invent. Phrases such as
"no invented speakers" or "without inventing motives" belong nowhere in the
narrative. When a speaker or connection is unknown, simply leave it unnamed;
do not explain that omission. Put necessary qualifications about sources only
in the explanation field. Local "perhaps" interpretations remain welcome.

Organize the biography around meaningful themes, not a catalogue of
every thought. Do not default to a paragraph of likes followed by dislikes.
When life_events contains a substantial supported event, center the biography
on that event and its named participants, then use character context to give it
meaning. A child birth, loss, or witnessed death may provide such a focus;
choose what is distinctive, not automatically the saddest event. Do not turn
several animal-body sightings into a dramatic death scene. When no substantial
event exists, write a character portrait without manufacturing a plot.
If no substantial historical_episodes event is supplied and life_events.narrative_focus
is present, open the FIRST paragraph with that
specific event and its named person (and year when known), not a profession,
personality description, likes, or dislikes. Develop that thread rather than
switching to a family/friend roster. Mention at most two additional people unless
they directly participate in the focal event. Never invent a profession-based
trait (for example, a sheriff's eye for order) or grief without supplied support.
Life events are recovered from the current profile and can predate the timeline.
Their source dates do not date memory recall or prove presence at a birth/death.
Current friend/family links do not establish the bond at an earlier event;
friendships are directional, not necessarily mutual. Do not invent shared
adventures, mourning, friendship formation, other parents, or causes/outcomes.
Use names when a friend is relevant, not a catalogue of every friend.
Select telling details and connect them through these plausible
interpretations. Avoid repeating the dwarf's full name and profession in each
paragraph. Narrative unity must not require fabricated events.

Write flowing prose rather than a list of statistics. When substantial events
and character context exist, aim for four to six developed paragraphs, roughly
350-550 words. For sparse evidence use one to three shorter paragraphs. There
is no two-paragraph limit. Include required events even when this requires more
space; length is a target, not a reason to invent or repeat details. Do not pad sparse evidence or
force a dramatic arc. Omit raw ticks, stress numbers, facet scores, confidence
labels, and talk of records, supplied data, missing history, recording gaps,
save reloads, or timeline resets from the narrative. Keep technical caveats in
the explanation field, not text; the timeline also retains technical evidence.
Do not invent seasons or dates from ticks. Use supported emotions rather than
guessing mental-state categories from numerical stress alone.

Only the latest recorded segment is supplied for this biography. Earlier
segments remain in the technical history. Do not invent events to fill missing
history or describe recording mechanisms in the prose.

An optional biography_profile is a current on-demand observation. Its figures
map historical-figure IDs to names, and relationships provide typed links.
The references table contains typed lookup results indexed by reference_key.
Use only entries with status resolved, never infer names from numeric IDs.
Death and UnexpectedDeath link directly to historical figures; WitnessDeath
and SawDeadBody link to incidents, whose resolved victim_name identifies the
person or creature. SawDeadBody means seeing a body, NOT witnessing the death;
only WitnessDeath supports witnessing the death itself. ANYTHING supplies no
specific emotion: do not assign grief, horror, or distress to such a sighting.
Keep everyday complaints equally precise: LackWell concerns access to a well,
and drinking without a cup concerns the missing cup, not drink quality.
Never use an incident number as a person ID or conflate separate deaths.
Use meaningful resolved names in the biography: name family members when
describing family, and a resolved victim when describing a witnessed death.
Do not replace available specific people with generic labels. Integrate names
naturally rather than listing every reference. A resolved name alone establishes
no relationship; match victim_histfig_id with actual relationship targets before
calling the victim family or a friend. An incident date can date the underlying
event; memory recall dates cannot. A spousest link identifies
a spouse; it does not establish when the marriage began. Do not backdate current
relationships or personality to earlier events. Respect profile limitations.
Memory flags and memory sections distinguish retained/recalled experiences from
new events; empty slots or thought -1 are not events. Need focus is not a count
of incidents. Named preference targets may enrich the portrait; omit unresolved preferences.
Core memory facet/value transitions may inform interpretation when supplied,
but never invent a transition or resolve cultural defaults from missing data.
"""
