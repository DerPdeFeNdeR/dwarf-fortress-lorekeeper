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
