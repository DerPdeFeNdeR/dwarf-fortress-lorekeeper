# Dwarf narrators — 2026-09-06

Implements [ADR 0007](../decisions/0007-dwarf-narrators.md). Current routing uses
the cleanup `qwen-thread` profile (`qwen3:8b`) and current profile schema 9, history-view
schema 23, monthly protocol/book
version 1, annual request schema 2 (legacy schema 1 accepted).

## Implementation

- `narrator.lua`: 23 bounded personality facets, selection weights and saved annual
  identity. Active-unit batches of 32 / 2 ms target; existing per-figure historical
  buckets supply at most 32 retained events. Voice capture includes at most 32
  explicit values, no full profiles or world-history scans. Files capped at 32 KiB.
- `historian.py`: first-person memoire contract, retaining all existing factual,
  memory, reference, and interpretation boundaries. `monthly_biography.py` includes
  voice traits in introduction context; the writer fingerprint updates old prose
  on a fresh request while retaining prior revision files.
- `story_coverage.py`: ID-based I/me anchors preserve perpetrator/victim roles and
  Unicode names. `heard_stories.py` uses first-person listening anchors only in
  autobiographies. Annual cultural anchors remain reported local performances.
- `chronicles.py`: saved voice in model context and story provenance. The UI shows
  “Narrated by …”; old prose retained on failure keeps its own attribution.
- Mental-attribute addition: four bounded `getMentalAttrValue` reads for linguistic
  ability, analytical ability, creativity, and memory, with the selected caste's
  `attributes.ment_att_range[id][3]` median. Relative voice bands are lower below
  75% of that median, higher above 125%, typical between; these are editorial
  choices, not DF description tiers or intelligence labels. Missing baselines
  yield unknown. Raw values stay in captured data; never print them in prose.
  Shared `narrative_voice.py` instructions affect delivery only. Lower memory must
  not manufacture forgetting or omit facts; creativity cannot invent events.
- Annual voices created before this addition are enriched once from the same
  unit/HF identity, preserving name, traits, and selection. Unavailable/mismatched
  identities gain an unavailable marker, not replacement attributes or a reroll.
  New draft requests carry the enrichment; published final chapters are untouched.
- Annual local-event anchors now say “In Granite, …” rather than “In year 102, …”.
  `fortress_calendar.py` shares calendar constants with monthly books. Valid ticks
  yield months; unknown, negative, or out-of-range ticks yield no month. Only the
  chapter opening may mention its year. Historical years inside told stories are
  preserved, since they describe the topic, not the telling.

Narration rules are separate from factual input and prior generated interpretation,
following [OpenAI instruction/context guidance](https://developers.openai.com/api/docs/guides/prompt-engineering#message-roles-and-instruction-following).
Eligibility uses the installed APIs, cross-checked against the
[DFHack units API](https://docs.dfhack.org/en/53.11-r1/docs/dev/Lua%20API.html).

## Verification

- Python: 126 tests, 123 passed, 3 explicit live integrations skipped in the normal
  suite. Tests cover first-person actor/object roles, nonmatching IDs and duplicate
  names, required facts, voice transport, invalid narrator requests, cache reuse,
  failed update provenance, and lazy writer-version migration.
- Actual DFHack: 105 tests passed, including weighted draws, bounded event bonuses,
  saved choice reuse, corrupt/wrong-year rejection, sparse voice capture, and
  old-story attribution.
  New checks cover month boundaries, unknown dates, separate story-subject years,
  mental-attribute transport, four-read capture, missing data, editorial bands,
  and one-time enrichment without identity replacement.
- Real model monthly test: introduction 9.83 s and month 9.75 s, both first person;
  cached reopening made no model call. Isolated synthetic save, not private data
  committed as a fixture.
- Real annual model test: first-person artifact anchor and preserved voice; cached
  reopening made no call. A first result included technical wording; strengthened
  prose instructions and a later check passed in 6.70 s. Model prose still needs
  player review; exact anchor coverage does not prove every generated claim.
- Actual Quickfortress draft selected Doren Zulbanetas, Wood Burner (unit 7800,
  HF 7498), from 33 eligible citizens, total weight 55. Voice persisted as
  `745-102.narrator.json`. A repeated read did not recapture or rewrite it.
- Initial real draft omitted event 77070 and correctly preserved old prose. One
  explicit retry passed all 3 historical and 4 cultural anchors in 16.71 s.
  Additional prompt guidance discourages writing-process commentary, interpreting
  artifact names as materials, and treating narrator values as fortress conditions.
- Live selected-dwarf profile returned schema 8 and its HUMOR value. No game time
  was changed. Natural annual rollover remains unverified; reload persistence is
  covered by reading the durable voice, not a new Windows/game restart this turn.
- Actual Chronicles window opened ready and its first displayed line was
  “Narrated by Doren Zulbanetas, Wood Burner”. The existing watcher was restarted
  with the narration code and verified Running; no startup configuration changed.
- Mental layout was checked read-only in the installed game: Doren's effective
  linguistic/analytical/creativity/memory values were 447/1075/873/1873; his
  linguistic caste median was 1000. The installed `assign-attributes.lua` reads
  the median from the fourth raw range entry; it was inspected, never executed.
- Windows refused `os.rename` when enrichment tried to replace the original saved
  narrator. The correction writes `<site>-<year>.narrator.mental.json` once, then
  reads it on later requests. The original narrator file is never replaced. An
  in-game regression verifies one companion write and unchanged identity.
- Updated live profile: schema 9, mental attributes available. An isolated real
  annual generation used the exact Granite first-person anchor and reused cache
  without another call (7.73 s). A real fortress attempt omitted death event 77070
  and was rejected; the previous draft remained readable with its own provenance.
- After strengthening exact death-anchor instructions, one explicit retry produced
  a ready Quickfortress draft in 12.74 s with all seven required anchors. Local
  events use Slate/Felsite/Hematite; the narrated historical subjects retain years
  62/35/83/77. Doren and the original saved personality remain unchanged; the new
  mental companion is included. The output remains fairly factual; personality
  distinctiveness and literary quality need player review, not just anchor tests.

## Player test

No Dwarf Fortress restart is normally needed. Close/reopen changed windows. If a
module stays cached, restart as a fallback. The existing watcher must be restarted
after Python edits; no new task registration or DFHack config change is needed.

1. Run `lorekeeper/test` (105 passes).
2. Select a dwarf, click Read memoire or run `lorekeeper/read`. Use U if an older
   result is still shown. Expect I/my narration, preserved names, introduction
   first, and single-paragraph monthly chapters via N/P. Completion is automatic;
   the game can remain paused and the collector need not run for this test.
3. Run `lorekeeper/chronicles`. Use D for Year so far. Expect a named dwarf narrator
   above the prose; reopen or request the draft again and verify the same narrator.
   Finished older annual chapters intentionally keep their original narration.
4. Review that heard tales remain heard tales and that unrelated fortress events
   are not claimed as firsthand experiences. Report voice quality and responsiveness.

Do not commit or push this batch until player verification/authorization. Keep
private generated books, saved narrator identities, and logs out of the repository.
