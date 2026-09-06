# The Lorekeeper project context

## User baseline

- The target game is the Steam version of Dwarf Fortress.
- DFHack is already installed and working in the user's game setup.
- The project should translate/explain in-game information, especially dwarf thoughts, personality, and related mental-state data.
- The project should also provide a history UI for reviewing changes and notable events over time.
- Primary UX requirement: when the player navigates to/selects a dwarf in Dwarf Fortress, the tool should open a dedicated DFHack UI window showing a readable summary of that dwarf's thoughts, personality, and related mental state. Keep the vanilla screen intact. In-place replacement of vanilla text is a possible later experiment, not the initial target.

## Working assumptions

- Treat DFHack as the integration boundary. Prefer DFHack Lua scripts and APIs before considering a compiled DFHack plugin.
- Keep game-facing collection separate from translation and presentation. The collector should emit stable, structured records rather than UI-ready prose.
- Do not overwrite or modify the user's DFHack installation from this repository unless explicitly requested. During development, use a documented copy/symlink/install step.
- Account for DF/DFHack updates: keep a small compatibility layer and record the game/DFHack version with collected data.
- Avoid storing only dwarf IDs. IDs can be useful within a world, but names, race, site/world identity, and timestamps should also be retained where available.
- Translation should be asynchronous and cached. Never block the DF render loop on a network/model request, and never put an API key in the DFHack Lua script. The initial cloud translation model is OpenAI `gpt-5-mini`; keep the model configurable for later benchmarking.
- The user-facing translation workflow must not require leaving Dwarf Fortress or
  manually processing a queue. The current `helper/process_queue.py` command is
  a development bridge only. The intended product workflow is a background
  local watcher that notices queued jobs, invokes the authenticated model
  client outside DFHack, writes the cache, and lets the in-game UI show pending
  or ready status.
- Translation caches must preserve Unicode names and prose. Write JSON with
  Unicode escapes when necessary to remain ASCII-safe for DFHack; never
  transliterate user-visible dwarf names as a workaround.
- History currently uses the append-only `lorekeeper-history.jsonl` file plus a
  fortress-wide sidecar index under `lorekeeper-history-index/`. The first
  history lookup builds that index in one pass; later dwarf lookups use the
  per-dwarf cache. New records update an existing index and create caches for
  new dwarves once they are recorded. Starting the collector prewarms the
  index during its existing history scan; `lorekeeper/autostart` can start the
  collector automatically on world load when enabled in `dfhack.init`.
- `lorekeeper/history` preserves raw records while presenting a grouped event
  timeline: baseline, coalesced stress trends, and discrete thought,
  profession, or personality changes.
- `lorekeeper/history/show` is the dedicated in-game history view. It displays
  the cached story above the grouped timeline and supports scrolling, refresh,
  copying, and closing without replacing the vanilla screen.
- The history view checks the latest timeline version and reports whether its
  story is ready, pending in the queue, or not yet requested; it must not show
  an older cached story as current.
- History story requests use a versioned compact payload with exact thought
  additions/removals, profession transitions, and personality facet changes.
  Change the request/schema version when the payload contract changes so stale
  cached stories are not reused.
- The local `helper/watch_queue.py` watcher is the hands-off development
  workflow: it monitors the active save queue, invokes Codex outside DFHack,
  and updates the cache while the player remains in-game. A future installer
  or launcher should start the save-directory watcher automatically. Prefer
  `helper/watch_save_directory.py` for startup because it follows all regions
  beneath the Dwarf Fortress save directory.
- `helper/start_watcher.sh` is the portable startup wrapper. It resolves the
  repository path and launches the save-directory watcher; Windows Task
  Scheduler registration remains an explicit user setup step.
- `helper/install_watcher_task.ps1` provides that explicit Windows Task
  Scheduler registration. It must be run by the user and accepts project/save
  path overrides; never register tasks automatically from repository actions.
- `dfhack/scripts/lorekeeper/autostart.lua` provides the explicit DFHack-side
  collector startup hook. It is enabled by adding `lorekeeper/autostart` to
  `dfhack.init`; repository actions must never edit the user's DFHack config.
- User preference: when the product is ready for broader use, prefer starting
  the translation watcher with DFHack/Dwarf Fortress startup rather than
  requiring a separate Windows login task. Keep model execution outside DFHack
  so the game loop and credentials remain isolated.
- Verified current Steam setup: the DFHack startup file is
  `C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\dfhack-config\init\dfhack.init`.
  Documentation must include the `init` subdirectory when instructing users
  to enable `lorekeeper/autostart`.

## Coding and review standard

Apply Bob Martin's Clean Code principles whenever writing or reviewing code, while using judgment appropriate to this project's Lua and game-integration constraints:

- Prefer clear, intention-revealing names over comments that explain vague code.
- Keep functions and modules small, focused, and responsible for one coherent thing.
- Separate collection, normalization, translation, caching, persistence, and UI concerns.
- Minimize side effects and make dependencies explicit, especially around DFHack state and network calls.
- Avoid duplication, speculative abstractions, clever code, and unnecessary framework complexity.
- Keep interfaces small and stable; hide implementation details behind focused modules.
- Handle errors explicitly and preserve useful diagnostic context.
- Write code that is easy to test; use fixtures for captured DFHack data and tests for translation rules and cache behavior.
- Test changes before committing or pushing them. For in-game behavior, wait for in-game verification when a local automated test cannot reproduce the behavior.
- Before committing or pushing, update the durable knowledge base when the
  implementation, workflow, or verified environment has changed: update
  `AGENTS.md` for lasting agent instructions and add a dated note or ADR for
  evidence and technical decisions. Do not rely on the conversation as the
  only record.
- Test the real integration path before publishing it. A mocked unit test is
  not enough for a CLI, network, DFHack, or game integration: run one bounded
  end-to-end check when credentials and the local environment permit it, and
  document any untested boundary explicitly.
- When handing off a game-facing change, explicitly tell the user whether Dwarf Fortress must be restarted. A restart is required after changing DFHack script-path configuration; otherwise, first try rerunning the command, and recommend a restart if DFHack does not reload a changed or newly added module.
- Refactor toward clarity when touching nearby code, but do not make unrelated rewrites.
- During review, prioritize correctness, readability, maintainability, and regression risk over personal stylistic preference.

## Project memory and documentation

- Treat version-controlled project documentation as the durable source of project memory; do not rely on conversational memory.
- Keep stable user goals, constraints, and working assumptions here in `AGENTS.md`.
- Record significant technical choices in `docs/decisions/` as short Architecture Decision Records (ADRs), including the decision, context, alternatives, and consequences.
- Record verified environment discoveries, compatibility findings, and test procedures in `docs/notes/`.
- Update documentation when a decision changes; do not accumulate contradictory instructions.
- Prefer concise, dated, evidence-based notes. Link to the relevant code, command output, save fixture, or official documentation when practical.
- Do not store secrets, API keys, private save data, or large generated dumps in the repository.

## Recommended first architecture

1. **DFHack collector (Lua):** read selected dwarf data and detect changes on a modest interval or relevant state changes. Start with thoughts, personality facets, current stress/needs, relationships, profession, and location.
2. **Stable data contract:** write newline-delimited JSON or another append-only format with a schema version. Use records such as `dwarf_snapshot`, `thought`, `personality_change`, and `event`; include world/site identity, dwarf ID, in-game time, collection time, and source/version metadata.
3. **Translation layer:** use a local deterministic glossary for known DF/DFHack enums and thought tokens. Use a low-cost, fast model only for unknown or context-sensitive cases, through a local helper service. Cache by raw text/tokens, relevant context, language, prompt/schema version, and model; always preserve the raw value alongside the translation.
4. **History storage:** begin with JSONL files for easy inspection and portability; move to SQLite when querying by dwarf, date, event type, or relationships becomes important.
5. **In-game summary view:** use DFHack GUI/view-screen facilities to detect the currently viewed or selected dwarf and open a dedicated, scrollable summary window. Group translated thoughts by category and severity, then show personality facets, stress/needs, relationships, and a concise overall interpretation. Preserve raw values and an “explain details” view for debugging and unknown translations. Keep the window independent of vanilla screen layout where possible.
6. **History UI:** build a read-only desktop/web viewer for longer-term review. Useful views are a timeline, dwarf detail page, thought/personality breakdown, and filters by severity, category, and date.

## Verified workflow discoveries

- The optional Codex translation backend is a batch worker, not a synchronous
  DFHack dependency. `helper/codex_batch.py` deduplicates requests and sends
  up to 50 items through one `codex exec --ephemeral --sandbox read-only`
  invocation with JSON Schema output.
- On 2026-09-06, `codex login status` reported `Logged in using ChatGPT`, and
  a real two-item batch returned validated structured results. This verifies
  the local Codex CLI path.
- On 2026-09-06, the full selected-dwarf path was verified in-game: a selected
  dwarf was queued with `lorekeeper/translate`, processed with
  `python3 helper/process_queue.py <queue.jsonl>`, and displayed by
  `lorekeeper/show` after refresh. `show` currently presents a current-state
  summary, not a historical story.
- DFHack UI text uses a CP437-oriented display path while Codex returns Unicode.
  Translation cache display fields are therefore ASCII-safe/transliterated;
  the authoritative snapshot and the Identity section retain the original
  dwarf name and raw values.
- Codex CLI may reuse ChatGPT-managed authentication for local workflows.
  Platform API keys are a separate usage-billed path. Never copy Codex auth
  files or API keys into the repository, DFHack scripts, queue data, or logs.
- Before claiming a Codex backend is game-ready, add and run a DFHack-facing
  queue command and verify that `lorekeeper/show` remains responsive while a
  batch is pending. Report restart requirements explicitly.

## Suggested milestone order

- Verify the installed DFHack version and locate its script path.
- Build a read-only `dump` command for one selected dwarf; validate the raw fields against the game UI.
- Build the smallest in-game summary window for the currently viewed dwarf, starting with translated thoughts and a close/refresh hotkey.
- Add a small polling collector and JSONL export, with fixtures from a real save for repeatable tests.
- Implement glossary-based translation and confidence/unknown handling for fields that are not understood yet.
- Add the local model helper only after the glossary path works; default it to OpenAI `gpt-5-mini` and return a temporary fallback while uncached text is being translated.
- Add SQLite indexing and the first timeline/detail UI.
- Add incremental collection, deduplication, privacy/retention controls, and only then consider an in-game overlay.

## Technical references

- DFHack Lua API: https://docs.dfhack.org/en/stable/docs/dev/Lua%20API.html
- DFHack overlay development: https://docs.dfhack.org/en/stable/docs/dev/overlay-dev-guide.html
