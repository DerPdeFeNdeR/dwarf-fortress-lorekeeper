# Play-session handoff — 2026-09-07

## Current checkpoint

Implementation batch **8dd7a66** was committed and pushed to main. The user is
playing to collect bugs and ideas. The subsequent documentation audit updates
installation instructions and project memory only; check Git status for its
publication state. Do not assume the earlier commit authorization covers new work.

Start the next session by asking about play-session findings and inspecting the
worktree. Do not regenerate stories, restart the watcher, modify DFHack setup,
or start new development automatically. Preserve saves and cached prose.

## What is implemented

- First-person dwarf Memoires: personality-shaped introduction first, then
  significant months newest-first. One paragraph per month; quiet months omitted.
  Updates revise chapters, not append paragraphs every time a reader opens.
- Annual Fortress Chronicles: one saved dwarf narrator per site/year, explicit
  year-so-far drafts and chapters queued after observed year rollover.
  Finished chapters are immutable.
- Typed references enrich supported events, family/friends, preferences and heard
  stories. A heard historical story is not firsthand participation.
- Personal knowledge filtering excludes unseen world events from Memoires.
  Raw diagnostics and fortress-wide Chronicles have broader scope.
- Bounded game-facing capture; Python prepares timelines and invokes Codex.
  Readers poll prepared files without scanning history or making model calls.
- Optional observed weather enriches annual context. Personal chapters may use
  their calendar, and introductions the current fortress setting, not shared
  weather. Moon phases remain unavailable; atmosphere does not trigger new prose.
- Annual omission failures allow one persisted insertion-only correction attempt.
  Failure preserves the previous draft and a separate rejected diagnostic.
  This is not a retry loop, a style rewrite, or proof that all prose is factual.

## Startup and controls

The root [README](README.md) is the Windows developer installation guide.
DFHack autostart handles collection, event indexing and the annual/environment
monitor. The separate Windows logon task runs the WSL watcher. Launching the
watcher with DFHack remains a future preference, not implemented behavior.

In-game:

- `lorekeeper/memoire`: U updates evidence, I introduction, N/P months, D details.
- `lorekeeper/chronicles`: D year-so-far draft, N/P chapters, R retry failure.
- `lorekeeper/history/show`: technical timeline; R rereads prepared results.
- `lorekeeper/collect status`: collection state. Pausing stops simulation-driven
  scans, not background model generation.

Existing development setup: shared checkout at
`C:\Users\contr\projects\dwarf-fortress-lorekeeper`, Steam DF 0.53.16 /
DFHack 53.16-r1.1, WSL user `contramonk`, save `region3`, site 745.
Recheck selection, time and worker state; these are not live guarantees.
Windows task: `Lorekeeper Queue Watcher`. Do not launch a duplicate.
Default WSL log: `~/.local/state/lorekeeper/watcher.log`.

## Contracts and verification

Profile 9; prepared view 26; monthly protocol 1 / book 2; annual request 2.
See [contracts](docs/schema.md) and [worker guide](helper/README.md).
Default model: `gpt-5.6-luna`, low reasoning; other accounts may lack access.
Do not change personal Codex settings for Lorekeeper.

Published checkpoint evidence (2026-09-06):

- Python: 176 tests, 169 passed and seven opt-in live tests skipped.
- Actual DFHack: 115 tests passed.
- Separate live atmosphere and insertion-only correction checks passed.
- Year-102 draft recovered to ready with all six required event checks,
  including incidents 667/680. Coverage checks are not full truth verification.

Remaining play checks: natural weather transitions and annual rollover,
mixed-biome/other fortresses, long-lived monthly growth/capacity, narrative quality.
A clean-machine Windows installation has not been reproduced by the documentation
audit. Do not turn these into claimed passes.

Tests from repository root in WSL:

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm python3 -m unittest discover -s helper -p 'test_*.py'
```

In-game: `lorekeeper/test`. Do not interrupt a play session to run it without
coordination. Never alter game time for tests or commit private save/model data.

Documentation-only changes need no restart. Python changes need a watcher restart;
rerun Lua commands first, restart DF if modules remain cached. Script-path changes
require a full DF restart. Test before publishing; update durable notes and obtain
commit/push authorization for new work.

## Evidence links

- [Documentation audit](docs/notes/documentation-audit.md)
- [Narrator design and tests](docs/notes/dwarf-narrators.md)
- [Personal knowledge](docs/notes/memoire-knowledge.md)
- [Monthly chapters](docs/notes/monthly-biographies.md)
- [Heard stories](docs/notes/heard-stories.md)
- [Cultural Chronicles](docs/notes/cultural-chronicles.md)
- [Atmosphere](docs/notes/observed-atmosphere.md)
- [Annual correction](docs/notes/chronicle-correction.md)

Older notes are checkpoint evidence, not current setup instructions.
