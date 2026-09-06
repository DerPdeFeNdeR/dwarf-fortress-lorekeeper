# The Lorekeeper implementation plan

## Product goal

When the player is viewing or has selected a dwarf, they can open a dedicated DFHack window that summarizes the dwarf's thoughts, personality, and related mental state in readable language. The vanilla Dwarf Fortress UI remains unchanged.

The first version should be read-only, local-first, and useful even when the model is unavailable.

## Initial scope

### In scope

- Steam Dwarf Fortress with the user's existing DFHack installation.
- A DFHack Lua command and GUI window.
- The currently selected/viewed dwarf as the initial target.
- Thought summaries and translations.
- Personality facets and basic mental-state context.
- A local glossary plus optional asynchronous OpenAI `gpt-5-mini` translation.
- Translation caching and raw-value preservation.
- A small event/history data format that can later power a separate history UI.

### Not in the first version

- Replacing or masking vanilla DF text.
- Changing dwarf thoughts, personality, or game state.
- Automatically translating every dwarf continuously.
- A full external web application.
- LLM-generated claims that are not grounded in captured DF data.

## Architecture

```text
Dwarf Fortress
    |
    v
DFHack Lua collector + summary window
    |                         \
    |                          \-- local glossary
    v
Local helper service
    |
    v
OpenAI API (gpt-5-mini, optional)
    |
    v
Translation cache + structured records
    |
    v
Future history UI
```

### Components

1. **DFHack package**
   - Read the selected dwarf through DFHack APIs.
   - Extract raw thoughts, personality values, stress/needs, relationships, profession, and identity fields where available.
   - Open a scrollable GUI window with a refresh and close action.
   - Never block rendering on a network request.

2. **Normalizer**
   - Convert DFHack objects/enums into a stable project schema.
   - Include game version, DFHack version, world/site identity, dwarf ID, and in-game time.
   - Retain raw source values beside normalized values.

3. **Translation layer**
   - Resolve known tokens with a local deterministic glossary first.
   - Send only unresolved or context-sensitive content to the local helper.
   - Require structured output with a translation, short explanation, category, and confidence/unknown flag.
   - Cache results using raw input, relevant context, language, prompt/schema version, and model.

4. **Local helper service**
   - Keep the OpenAI API key outside the DFHack scripts.
   - Accept localhost requests from DFHack or a file/queue bridge.
   - Return quickly with a pending state when translation is not cached.
   - Retry safely and enforce request/time/token limits.

5. **History storage**
   - Start with append-only JSONL records for easy debugging.
   - Move to SQLite when timeline and filtering queries are needed.
   - Deduplicate snapshots and record meaningful changes rather than every poll.

## Milestones

### Milestone 0: environment discovery

- Confirm DF version and DFHack version.
- Locate the active DFHack script path and a safe development install/copy workflow.
- Confirm the exact DFHack GUI APIs available in the installed version.
- Create a minimal script that reports whether a dwarf is selected.

**Exit criteria:** the script runs from DFHack and identifies the selected dwarf without changing game state.

### Milestone 1: raw dwarf inspector

- Implement a `lorekeeper/dump` command for the selected dwarf.
- Capture identity, thoughts, personality, stress/needs, profession, and relationships when available.
- Print and save raw data for a real fortress.
- Add fixture files from captured output for repeatable development.

**Exit criteria:** raw output can be compared against the dwarf's vanilla information screen.

### Milestone 2: first in-game summary window

- Add a hotkey or DFHack command to open the window.
- Display the dwarf name and identity.
- Display raw thoughts in a scrollable list.
- Add close, refresh, and loading/error states.
- Make the window work when the player changes the selected dwarf.

**Exit criteria:** selecting different dwarves and refreshing shows the correct dwarf without crashes or game-state changes.

### Milestone 3: deterministic translation

- Define a versioned translation schema.
- Build the first glossary for common thought categories and personality facets.
- Render translated text while retaining a raw/detail toggle.
- Mark unknown tokens clearly instead of inventing an explanation.

**Exit criteria:** known fixture inputs produce stable translations and unknown inputs remain visibly unknown.

### Milestone 4: optional `gpt-5-mini` helper

- Add a small local service using the OpenAI Responses API. **Implemented:**
  `helper/server.py` binds to localhost and keeps the API key outside DFHack.
- Add structured output validation and bounded prompts. **Implemented:** the
  helper uses a strict JSON schema, input limits, output limits, and a timeout.
- Translate only cache misses or explicitly requested details. **Implemented:**
  cache keys include raw input, context, language, model, prompt, and schema.
- Update the DFHack window when results arrive.
- Add cache persistence, timeout, retry, and API failure handling. **Partial:**
  persistence, timeout, and explicit failure handling are implemented; retry
  policy and DFHack/UI integration remain.
- **Codex CLI batch path implemented:** `helper/codex_batch.py` deduplicates
  queued jobs and sends up to 50 items through one read-only `codex exec` call.

**Exit criteria:** the game remains responsive with the helper offline, and repeated thoughts do not cause repeated API calls.

### Milestone 5: history records and UI foundation

- Emit meaningful thought/personality/event changes as JSONL.
- Add a SQLite importer/indexer when JSONL querying becomes awkward.
- Build a read-only dwarf timeline and detail view outside the game.
- Link history records back to raw source data and translation versions.

**Exit criteria:** a dwarf's thought history can be reviewed chronologically and regenerated when translation rules change.

## Current record shape

The implemented collector writes one `dwarf_snapshot` record per JSONL line.
The exact contract, including raw IDs and version/context metadata, is in
[`docs/schema.md`](docs/schema.md). The collector does not write translated
prose; glossary and model output remain a separate concern.

```json
{
  "schema_version": 1,
  "record_type": "dwarf_snapshot",
  "captured_at": "2026-09-06T16:40:19Z",
  "ingame_time": {"year": 102, "year_tick": 47611},
  "snapshot": {
    "schema_version": 1,
    "source": {"df_version": "...", "dfhack_version": "..."},
    "context": {"site_id": 123, "save_id": "region3"},
    "identity": {"id": 123, "name": "...", "profession": "Miner"},
    "soul_present": true,
    "mental_state": {"stress": 1000},
    "thoughts": [],
    "personality_facets": []
  }
}
```

## Design rules

- The DFHack Lua layer must remain responsive and must not contain secrets.
- Raw data is authoritative; generated text is an interpretation.
- Every generated explanation should be traceable to the input fields that produced it.
- Unknown data should be displayed as unknown, not silently guessed.
- Model, prompt, and schema versions must be recorded for reproducibility.
- Compatibility code should be isolated because DFHack and game screen APIs can change.
- Prefer small, testable modules over one large DFHack script.

## Current status

Milestones 0–3 are implemented for the current DF/DFHack environment:
selected-dwarf dumping, the read-only summary window, deterministic glossary
labels, JSONL recording, duplicate suppression, and the opt-in all-citizen
collector with pure policy tests. The collector policy is documented in
[`docs/decisions/0002-citizen-collector-policy.md`](docs/decisions/0002-citizen-collector-policy.md).

## Immediate next task

Finish the translation boundary before adding a model helper: define the
glossary output contract, then add a local asynchronous helper with bounded
requests and a persistent cache. The helper must preserve raw values, remain
optional, and never block the DFHack render loop. After that, build the
history importer and read-only timeline UI.
