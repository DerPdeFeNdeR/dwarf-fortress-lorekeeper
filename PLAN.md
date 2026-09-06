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

- Add a small local service using the OpenAI Responses API.
- Add structured output validation and bounded prompts.
- Translate only cache misses or explicitly requested details.
- Update the DFHack window when results arrive.
- Add cache persistence, timeout, retry, and API failure handling.

**Exit criteria:** the game remains responsive with the helper offline, and repeated thoughts do not cause repeated API calls.

### Milestone 5: history records and UI foundation

- Emit meaningful thought/personality/event changes as JSONL.
- Add a SQLite importer/indexer when JSONL querying becomes awkward.
- Build a read-only dwarf timeline and detail view outside the game.
- Link history records back to raw source data and translation versions.

**Exit criteria:** a dwarf's thought history can be reviewed chronologically and regenerated when translation rules change.

## Proposed record shape

```json
{
  "schema_version": 1,
  "record_type": "thought",
  "game_version": "unknown",
  "dfhack_version": "unknown",
  "world_id": "...",
  "site_id": "...",
  "dwarf_id": 123,
  "dwarf_name": "...",
  "ingame_tick": 456789,
  "captured_at": "2026-09-06T00:00:00Z",
  "raw": {
    "category": "...",
    "severity": 0,
    "text_tokens": ["..."]
  },
  "normalized": {
    "category": "...",
    "severity": 0
  },
  "translation": {
    "text": "...",
    "source": "glossary",
    "model": null,
    "prompt_version": "1",
    "confidence": "high"
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

## Immediate next task

Milestone 0 environment discovery and Milestone 1 raw selected-dwarf inspection are complete: `lorekeeper/dump` successfully displayed Mistêm Woundcolored's identity, raw thoughts/emotions, severities, stress, and all personality facets under DF 0.53.16 / DFHack 53.16-r1.1. The first read-only summary window is now implemented as `lorekeeper/show`; the next task is to test its layout, scrolling, refresh behavior, and no-selection handling in-game. Do not add history polling until the summary data model is stable.
