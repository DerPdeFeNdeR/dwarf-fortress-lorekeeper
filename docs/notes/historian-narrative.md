# Single historian narrative — 2026-09-06

## Decision

The user replaced the proposed selectable narrators with one consistent
historian fitting the Dwarf Fortress setting. The voice is learned, observant,
proud of craft, and dryly witty. Tone changes with the subject: warmth and energy
for joys and everyday absurdities; gravity and compassion for grief or fear.
No narrator biography, invented world lore, or eyewitness claims are introduced.

`helper/historian.py` owns the narrative contract. `history_view.py` supplies it
to the existing asynchronous worker. Schema v7 invalidates earlier report-style
stories, including completed requests; regeneration still happens outside DF.
No narrator selection UI or game-loop/model dependency is added.

Raw numbers, gaps, and time resets stay out of story prose. Model explanation
is retained separately as `story_explanation`; the existing technical timeline
remains visible below the story. A future Details toggle can hide that timeline.
Following the user's review of repetitive v6 prose, only the latest segment
is supplied for the biography, starting from a fresh baseline. The full timeline
remains intact, including earlier segments and reset markers.

The user explicitly permits imagined internal motives to connect supported
experiences. These must fit known character context, use natural local markers
such as "perhaps", and never introduce fictitious people, relationships,
deeds, outcomes, or the identity of a deceased person. Generated stories carry
`story_notice`, shown outside the prose: "Based on game events, with imagined
motives and interpretation." Explanation distinguishes fact from interpretation.
The notice is preserved with its story during regeneration or cache reuse.

Narrative flair must not manufacture events. In particular, baseline birth or
death thoughts are not new events; repeated thoughts do not prove repeated
deaths; removed thoughts do not establish forgetting or resolution. Sparse
evidence should yield a short narrative, not fabricated drama. Unknown tokens
are not permission to invent a cause. No numeric stress-category thresholds
are introduced by this change.

## Validation

- 30 Python tests pass. Regression checks verify narrator instructions are
  wired into the worker request, only the latest segment enters model input,
  full timelines remain unmodified, schema migration regenerates stories, and
  the notice and explanation are stored separately from prose.
- One new DFHack test covers display-safe dashes/quotes/ellipsis while preserving
  accented names. Cached Unicode text is unchanged. This fixes the visible `?`
  punctuation issue; the user confirmed all 31 DFHack tests passed.
- Prompt assertions cannot guarantee literary quality or factual adherence.
  Real model output and in-game review remain necessary for future changes.
- On 2026-09-06 the user supplied Minkot's ready v7 narrative and approved its
  direction. It displays the separate interpretation notice, correct accented
  name and paragraphs, and one biography without the duplicated older segment.
  An imagined connection is marked with "Perhaps"; technical ticks and reset
  markers remain in the timeline below, not the prose. The user then confirmed
  `lorekeeper/test` reported all 31 tests passed.
- One bounded real worker call with synthetic work-satisfaction, performance-
  delight, and witnessed-death thoughts returned validated structured output.
  It preserved `Minkot Udistatír`, used mild humor for work/performance, treated
  death seriously, and put the baseline chronology caveat in explanation rather
  than prose. It did not read or modify the save. This is a smoke test, not a
  guarantee that all generated narratives will follow the contract.

## In-game test

A subsequent bounded v7 synthetic worker test connected high orderliness to
annoyance over a missing cup with "Perhaps", and identified that connection as
interpretation in explanation. It retained horror at death without inventing
the deceased or a relationship, and avoided claiming that work resolved grief.
Structured validation passed. No save data was used or modified by that test.

Restart the watcher to load Python changes; no DF restart is needed. Open
`lorekeeper/history/show` for a dwarf with history, wait in real time, then press
R. Expect natural narrative with preserved names and paragraphs, no raw ticks,
facet/stress scores, or recording-mechanism discussion within the prose. Check
that humor does not trivialize suffering and no unsupported scene is invented.
Confirm the interpretation notice is outside the prose and the latest segment
is not repeated as a second biography. Run `lorekeeper/test` (31 expected tests)
to check display punctuation and existing Lua behavior.
The timeline below remains the developer/debug view. Existing requests may
regenerate once after the schema change. This version completed the in-game
verification above; repeat it before publishing later game-facing changes.
