# ADR 0007: Personality-shaped dwarf narrators

Date: 2026-09-06. Status: implemented and published in `8dd7a66`;
extended player verification continues.

## Context

The user wants each memoire told by its subject, and each annual fortress
history told by a randomly chosen dwarf, preferably one with an eventful year.
This explicitly replaces the single external historian; it does not introduce
selectable voices or change the model.

## Decision

- Monthly memoires become first-person memoires. Preserve introduction-first
  navigation, one paragraph per significant month, lazy generation, and cached
  continuity. Character context shapes delivery, not invented external facts.
- Annual narrator selection uses weighted reservoir sampling among living adult
  dwarf citizens on the map. Weight is 1 plus up to 8 unique retained events from
  that fortress and year involving the dwarf. Quiet citizens retain a chance.
- Save identity and personality/value snapshot under the save's chronicle folder
  in `<site>-<year>.narrator.json` before sending a model request. Keep the same
  narrator across drafts, finalization, retries, and recording branches/reloads
  in that save. The voice is a literary device, not proof of presence throughout
  the year. A later missing/dead narrator does not cause a reroll.
- No eligible citizen yields a labeled external chronicler for that year. Corrupt
  or unreadable saved choices fail visibly instead of being overwritten.
- A factual anchor becomes first person only on an exact historical-figure-ID
  match. Other people's events remain reported history. Listening to a tale does
  not establish participation in its subject. Never invent dialogue, sources,
  outcomes, literacy, an appointment to write, or access to others' thoughts.
- Keep the interpretation notice. Attribute the displayed story, not pending
  work. Existing finished annual chapters remain immutable. New requests lazily
  revise existing monthly prose through the writer fingerprint without deleting
  old revisions; no bulk dormant-book regeneration.
- Mental attributes also shape delivery: four effective values and caste-relative
  editorial bands, not an invented overall intelligence score. Lower values favor
  simpler prose, not factual mistakes or caricature. Enrich older saved voices once
  without changing narrator identity or prior personality snapshots.
- Within annual accounts, use known event months and mention the chapter year at
  most once. Keep a heard tale's historical date separate from its performance date.

## Alternatives and consequences

Selecting a narrator on every request would change voices during retries. Asking
the model to choose would make selection unauditable. Capturing all citizens'
full profiles would add needless game work. Instead, scan active units in batches
of 32 with a 2 ms target, then capture only the chosen dwarf's small voice card.
This is not an exhaustive measure of eventfulness; the historical index is bounded.

Personality changes can affect future autobiographical delivery. An annual voice
snapshot stays fixed. Old external narration may remain visible while replacement
work is pending, explicitly without attribution to the new dwarf.
