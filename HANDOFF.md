# Playtest handoff — 2026-09-06

## Start here next session

The user approved the monthly-biography and cultural-chronicle batch and requested
commit/push before playing normally. Start with their playtest feedback; do not
begin another feature or regenerate dormant biographies automatically. Read
`AGENTS.md`, check `git status` and the latest commit before editing. This handoff
accompanies **Add monthly biographies and cultural chronicles**.

## Current behavior

- Read biography (`lorekeeper/read` or the unit-sheet button): introduction first,
  then significant recorded months newest-first. Each month is one paragraph;
  quiet months are omitted. N/P browse, I returns to introduction, U requests new
  evidence, D shows the technical timeline, Escape closes.
- Monthly updates revise a chapter; reopening alone does not append paragraphs.
  Saved chapters remain readable during background writing. Immutable revisions
  and written-evidence checkpoints preserve successful work.
- Heard stories include resolved subject, teller, organizations, listening date,
  and reaction. They are not transcripts or evidence the listener participated
  in their historical subject. Topic dates differ from performance dates.
- Organizations have current type/race context. The Oracular League is a human
  site government; The Letter of Safety is a dwarven civilization, not a document.
  Neither visited merely because a local storyteller discussed it.
- `lorekeeper/chronicles`: D requests Year so far. Finished annual chapters are
  written after observed rollover and remain immutable. Cultural performances
  now join historical events as a separate, deduplicated input.

## Architecture and limits

Profile schema 7, biography view schema 21, monthly protocol/book version 1.
Python: `monthly_biography`, `heard_stories`, `cultural_events`. Lua: `storytelling`,
`culture_index`, shared typed `references`.

Profiles remain on-demand, not part of citizen polling. The reader only reads
bounded prepared files; no model calls or history scans in the game loop.
One monthly chapter per dwarf per watcher pass. Model remains gpt-5.6-luna / low.
Previous prose is interpretation, never factual evidence. Missing required event
coverage fails visibly; no automatic coverage retry loop.

Partial coverage: profiles 160 references / 128 KiB; historical profile episodes 8;
annual historical selection 16; cultural index 128 incidents / 2 ms target per
batch, 256 retained per site/year, latest 4 selected tellings per annual request.
Current/previous year only. Monthly catalog shows introduction plus newest 99
months; older files remain on disk. Monthly manifest write guard is 1.9 MB.

## Verification and remaining checks

- Python: 115 passed, two opt-in integrations skipped in the ordinary suite.
- Actual DFHack: 88 passed.
- Real monthly integration: introduction 9.54 s, month 11.60 s; cached reopening
  made zero calls. In-game introduction-first selection and N/P navigation passed.
- Cultural scan: 656/656 incidents, zero errors; enriched Brow profile 94,535 bytes.
- First cultural draft omitted a required telling and correctly preserved old
  prose. After a prompt correction, one explicit retry passed in 17.35 s with all
  four named tellers. Actual Chronicle reader loaded the ready result.
- The user said the result looks good, confirmed biography content inclusion,
  and approved publication. Extended playtesting is now the next step.
- Still unverified: natural year-end rollover; long-lived monthly growth and
  capacity limits under real workloads. Narrative can still sound technical;
  anchor checks do not prove every prose claim.

## Environment and diagnostics

Shared WSL/Windows repository:
`C:\Users\contr\projects\dwarf-fortress-lorekeeper`.
Latest tested save: Steam Dwarf Fortress `save/region3`, Quickfortress, site 745.
Latest tested subject: unit 8420, Brow. Recheck current selection/game time after
the user has played rather than assuming they are unchanged.

Existing Windows task `Lorekeeper Queue Watcher` was last verified Running.
Do not register another task or launch a duplicate worker. It runs
`helper/watch_save_directory.py`; credentials remain outside the repository.
DFHack autostart is already configured; `lorekeeper/collect status` checks the
collector. Paused game time stops citizen scans, not background model generation.
No game restart is needed for this commit. Rerun changed scripts first; restart
only if modules stay cached or script paths change. Never alter game time for tests.

Tests from repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm python3 -m unittest discover -s helper -p 'test_*.py'
```

In-game: `lorekeeper/test`. Diagnose wrong names/dates/missing events using the
selected request/profile and saved monthly or annual result. Do not commit private
save dumps, generated books, credentials, or worker logs.

Details: [monthly biographies](docs/notes/monthly-biographies.md),
[heard stories](docs/notes/heard-stories.md),
[cultural chronicles](docs/notes/cultural-chronicles.md).
