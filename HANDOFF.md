# Narration handoff — 2026-09-06

## Start here next session

The user authorized committing/pushing this complete batch on 2026-09-06 and is
switching to normal gameplay to collect bugs and feature ideas. Do not start new
development or regenerate stories automatically on the next session: first ask
about play-session findings and inspect repository state. Preserve saves and
cached prose. This publication authorization supersedes the earlier hold notes
below; it does not claim every remaining manual test has passed.

Remaining gameplay checks: natural rain/snow transitions, year rollover,
other/mixed-biome fortresses, and the corrected chronicle's narrative quality.
No restart required for this checkpoint; the observer is active and the existing
watcher was restarted successfully. No additional setup is needed to keep playing.

Final verification: 176 Python tests (169 passed, seven opt-in skipped), 115
actual DFHack tests, separate live atmosphere and insertion-only correction
checks passed. Year-102 draft recovered to ready with all six required event
checks, including incidents 667/680. Reopen `lorekeeper/chronicles`; do not request
another draft just to see the recovery. No DF restart required. Automatic repair
is one attempt per request, including across a crash; unsupported repairs fail
closed. Publication is now authorized; extended gameplay verification continues.

Latest batch: optional calendar/weather/geography (view schema 26) and one bounded
annual coverage-correction pass. Extended player verification continues.
See `docs/notes/observed-atmosphere.md` and `docs/notes/chronicle-correction.md`.
Observer activated without DF restart/config changes. Moon phases remain
unavailable. Shared weather never enters personal Memoire inputs or triggers
new monthly prose. Prior draft remains visible if correction cannot be verified.

## Earlier implementation checkpoints (historical)

Coverage follow-up: the year-102 draft failed on storytelling incident 667.
Its old rejected prose was not retained, so the original cause cannot be proven.
New coverage failures preserve a separate latest-candidate diagnostic;
annual errors say Chronicle. Appointment alternatives and small spelled-out
years are accepted without dropping teller/subject/office/entity/year checks.
No automatic retry loop or commit/push. See `docs/notes/chronicle-rejections.md`.
Verification complete: 155 Python tests (150 passed, 5 opt-in skipped).
The actual year-102 retry exposed a different victim-first/pronoun mismatch;
the saved candidate then passed all seven corrected checks and was explicitly
recovered to ready without a second model call. Watcher reloaded. Reopen
`lorekeeper/chronicles` to review; no game restart or new draft request needed.

Latest follow-up adds on-demand event causes, recorded weapon/launcher details,
and wound injury/body-part information. See `docs/notes/event-methods.md`.
View schema is now 25. Python: 149 tests (144 passed, 5 opt-in skipped); actual
DFHack: 110 passed; separate live method generation/cache check passed in 6.20 s.
Test with U in a Memoire or D in Chronicles; unknown methods remain unspecified.

Latest follow-up: annual prose now shares month context and explains subjects at
first mention. Coverage accepts bounded factual clauses instead of whole fixed
sentences; Memoire validation is unchanged. A reflective month mention is allowed;
avoid repetitive month introductions. See `docs/notes/chronicle-prose.md`.
No commit/push yet; request a new year-so-far draft with D for player review.
Python: 140 tests (136 passed, 4 opt-in skipped); separate live grouped-month
test passed in 9.38 s, including cached reopen. Watcher restarted and Running.
No game restart required; no completed annual chapter was rewritten.

The monthly/cultural batch was published as 416cc73. The user then requested both
first-person dwarf memoires and randomly selected personality-shaped annual dwarf
narrators. That new batch is implemented, not committed/pushed; player acceptance
is pending. Read `AGENTS.md`, check the worktree, and review
[dwarf narrator verification](docs/notes/dwarf-narrators.md) before continuing.
Do not regenerate dormant books automatically or republish without authorization.

## Current behavior

- Read Memoire (`lorekeeper/memoire`, legacy `lorekeeper/read`, or the unit-sheet button): introduction first,
  then significant recorded months newest-first. Each month is one paragraph;
  quiet months are omitted. N/P browse, I returns to introduction, U requests new
  evidence, D shows the technical timeline, Escape closes.
- New memoires use the subject dwarf's first-person voice. Annual drafts and
  new completed chapters use one saved weighted-random dwarf narrator per site/year.
  Existing completed annual chapters are immutable; old monthly prose updates lazily.
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

Profile schema 9, memoire view schema 25, monthly protocol 1 / book version 2;
annual request schema 2. `narrator.lua` captures small bounded voice cards, not
all citizens' memoire profiles. Saved narrator files live only in the save.
Python: `monthly_biography`, `heard_stories`, `cultural_events`. Lua: `storytelling`,
`culture_index`, shared typed `references`.

Individual model inputs now pass through `memoire_knowledge.personal_profile`.
Only personal participation, retained memories/thoughts and explicit heard tales
provide events. Relationships supply identities, not world-derived life dates;
witnessed incidents supply victims, not unseen killers/causes/dates. Raw diagnostic
profiles and broader annual chronicles remain intact. Book v1 is archived rather
than supplying its prose/evidence to v2. See `docs/notes/memoire-knowledge.md`.

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

Current narration batch: 123 Python passes / 3 opt-in skips; 105 actual DFHack
passes. Real monthly introduction/month generation and cached reopening passed.
Real annual draft chose Doren Zulbanetas (HF 7498); choice survived retry, and
the successful draft passed seven factual anchors. See the narrator note for
timings, a rejected first attempt, and narrative-quality caveats. Natural annual
rollover and player acceptance of the new voices remain pending.

The user subsequently requested mental-attribute voice cues and month-based dates
instead of repeating the annual year. Four mental attributes now augment both
voice paths; saved annual identity is preserved through one-time enrichment.
Annual factual anchors use known months; unknown months are not guessed, and
historical years within heard tales stay intact. No model or startup-config change.

Prior monthly/cultural publication evidence:

- Python: 115 passed, two opt-in integrations skipped in the ordinary suite.
- Actual DFHack: 88 passed.
- Real monthly integration: introduction 9.54 s, month 11.60 s; cached reopening
  made zero calls. In-game introduction-first selection and N/P navigation passed.
- Cultural scan: 656/656 incidents, zero errors; enriched Brow profile 94,535 bytes.
- First cultural draft omitted a required telling and correctly preserved old
  prose. After a prompt correction, one explicit retry passed in 17.35 s with all
  four named tellers. Actual Chronicle reader loaded the ready result.
- The user said the result looks good, confirmed memoire content inclusion,
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

Details: [monthly memoires](docs/notes/monthly-biographies.md),
[heard stories](docs/notes/heard-stories.md),
[cultural chronicles](docs/notes/cultural-chronicles.md).
