# Play-session handoff — 2026-09-07

## Current checkpoint

Model-owned routing supersedes the preset-only setup below. See
`docs/notes/model-owned-writers.md`: default `qwen-fast`, optional `qwen-compact`,
and separate `luna-literary`. Luna must never use Qwen strategies. Unknown models
and cross-model selections fail before model work. Both platform suites: 211 run,
204 passed, seven optional tests skipped. No commit/push authorized for this work.
Windows Codex CLI is absent; the Luna transport is available in WSL only for now.
Live isolated checks passed: Qwen annual 3.30s (seven anchors), quiet month 2.98s;
Luna full-context quiet month 13.04s. Quiet sample has no mandatory anchors.
Native worker restarted with Qwen selected, PID 18956, logs
`.lorekeeper/watcher-router.out.log` / `.err.log`; heartbeat matches, error log
empty. Recheck identity before future restarts. No Dwarf Fortress restart needed.

Latest Memoire speed work: preset `qwen3-personal-v7`, documented in
`docs/notes/qwen-personal-briefs.md`. Personal-fact compilation, relevant character
context, and shorter quiet chapters are implemented. Both platform suites:
202 run, 195 passed, seven optional live tests skipped. Isolated real monthly
pipeline: intro 7.02s, Limestone 5.60s with its heard-story anchor checked. Separate
quiet Slate check: 3.94s / 982 input tokens. Warm single-run timings, not latency
guarantees or narrative-quality acceptance. Four diagnostic months remain pending.
Native worker restarted with `.lorekeeper/watcher-v7.*.log`; no DF restart needed.
Checkpoint Python PID 29000, launcher 1956; heartbeat advances and error log is
empty. Recheck process identity before future restarts.
Press U for v7 preparation. No new commit/push or startup task.


Latest rewrite supersedes the v4 checkpoint below. See
`docs/notes/qwen-writing-rewrite.md`: preset `qwen3-anchored-v6`, compact monthly
briefs and Python-assembled annual facts with optional Qwen reflections. Real
Chronicle generated in 3.92s with all seven required checks and automatic reader
completion verified via DFHack. Optional reflections still need quality scrutiny;
named-reference/death-description omissions were added after inspecting that draft.
Memoire free prose still invents details despite a shorter prompt. No literary
acceptance is claimed. Finished annual chapters remain unchanged.
No DF restart needed; close/reopen Chronicles for the reader update.

Final post-guard checkpoint: native worker Python PID 8420, launcher 29328,
advancing heartbeat and empty `.lorekeeper/watcher-v6.err.log`; stdout is
`.lorekeeper/watcher-v6.out.log`. Recheck process identity before future restarts.
Both Windows and Linux suites: 195 run, 188 passed, seven optional tests skipped.
Focused DFHack request-progress tests passed. Final actual year-102 draft reached
ready in 3.61s, with seven mandatory checks passed and no omitted reflections.
An isolated full monthly preparation pass completed its intro in 13.72s, leaving
five months pending in the diagnostic book; this is not a full-book v6 acceptance.
The final Chronicle still contains poorly grounded imagery (e.g. a desert metaphor
beside dehydration); scope guards are not semantic verification. User should
review prose rather than infer quality from speed/coverage. No commit or push.
Live reload also exposed an old DFHack timer callback retaining the pre-rewrite
export function. `chronicle.lua` now rebinds the timer on module reload without
resetting the branch/runtime. Reopen the Chronicle reader to clear old UI handles.
Final callback-rebind verification: request ending `1788812715-5.request.json`
completed in 3.46s, all seven facts checked; live reader automatically displayed
Saved chapter with pending cleared and the original branch still selected.


Latest 2026-09-07 real-save tuning supersedes the 16K/q8 checkpoint below:
Qwen preset v4 uses 20,480 context with Flash Attention/q4_0 KV cache,
verified 37/37 layers / 100% GPU / 5.9 GB. Lossless prompt tables and disabled
truncation/context shifting address real requests losing their instructions.
Minkot's isolated book reached ready with all pending chapters; actual generation
took roughly 17–28s per passage across these checks. Both platform suites:
184 run, 177 passed, 7 optional live tests skipped. See
`docs/notes/qwen-real-save-tuning.md`. Live reader acceptance remains pending;
the saved diagnostic book is not published into the game. Tuned native worker
restarted: checkpoint Python PID 30224, launcher 12712; heartbeat advances and
error log is empty. Logs: `.lorekeeper/watcher-tuned.out.log` / `.err.log`.
Press U in the reader to retry a failed request; no DF restart.
Recheck current heartbeat/processes rather than assuming these PIDs stay valid.

2026-09-07 active work: user authorized Qwen3/Ollama and native Windows worker.
See `docs/notes/windows-ollama.md`. Windows Python 3.13 is installed; both platform
test suites pass. Real Qwen monthly test passed (~25s introduction, ~21s month);
annual test failed coverage for incidents 2/3. Worker cutover is deferred until
the failure is diagnosed with retained prose. See the dated note. The
existing WSL task was observed Running; do not launch a native worker against
the same saves until the old process is stopped and verified absent.

Later Qwen tuning resolved that mismatch: see `docs/notes/qwen-coverage-and-gpu.md`.
Full GPU verified (37/37 layers, 16K, Flash Attention + q8_0); final retained
monthly and annual tests pass (~10s intro/month, ~7s Chronicle). Editorial tests
are advisory; roles/dates/negation stay checked. Sparse Memoire prose still
invents unsupported backstory, so automated passes are not quality acceptance.
Cutover subsequently completed at the user's explicit request: WSL task
`Lorekeeper Queue Watcher` is Disabled (Windows administrator approval required),
WSL worker exited, and native Windows Python worker started against the Steam save
root with a matching advancing heartbeat and clean error log. Checkpoint Python
PID 2520, launcher 28660; recheck processes rather than assuming these stay valid.
Logs: ignored `.lorekeeper/watcher-windows.out.log` and `.err.log`. Explicit
settings: ollama / qwen3:8b / http://127.0.0.1:11434/api/generate. Full GPU verified.
No native scheduled task registered; startup after reboot is currently manual.
Player should select a dwarf, open Read memoire, then U. No DF restart required.
Actual in-game Qwen completion and quality acceptance remain pending.

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
