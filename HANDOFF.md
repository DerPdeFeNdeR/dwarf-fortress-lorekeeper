# The Lorekeeper - agent handoff

## Current project location

- Windows path: C:\Users\contr\projects\dwarf-fortress-lorekeeper
- WSL path: /mnt/c/Users/contr/projects/dwarf-fortress-lorekeeper
- Do not rename this directory again during this session. The workspace sandbox was originally rooted at dwarf-translator, and WSL tools show a stale/inaccessible mount after the rename. A new agent session should be opened with the new directory as its workspace root.

## User goals

- Build an in-world historian/storyteller for Steam Dwarf Fortress.
- Use DFHack.
- Let the player select a dwarf and open a dedicated Lorekeeper summary window.
- Summarize thoughts, personality, stress, relationships, and eventually fortress history.
- Preserve the vanilla UI; do not replace vanilla thought text for the initial version.
- Use OpenAI gpt-5-mini to generate a grounded story from the dwarf's full state, rather than deterministic sentence-by-sentence translation.

## Verified environment

- DF version: v0.53.16 win64 STEAM
- DFHack version: 53.16-r1.1
- DFHack install: C:\Program Files (x86)\Steam\steamapps\common\DFHack
- DFHack config: C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\dfhack-config\script-paths.txt
- Configured script path:
  +C:/Users/contr/projects/dwarf-fortress-lorekeeper/dfhack/scripts

## Working commands

Open DFHack's in-game launcher with the backtick key, then run:

- lorekeeper/dump - read-only selected-unit dump
- lorekeeper/show - first summary window
- lorekeeper/tokens - runtime token catalog
- lorekeeper/tokens copy - copy token catalog to the system clipboard

The dump was successfully tested on selected dwarf Mistem Woundcolored (unit 6137). It reports identity, thoughts/emotions, severities, stress, and personality facets. The summary window and clipboard copy were also implemented; footer spacing was fixed.

## Important DFHack 53.16 field findings

- Selected unit: dfhack.gui.getSelectedUnit(true)
- Soul/personality: unit.status.current_soul.personality
- Thoughts/emotions: personality.emotions
- Thought type: thought.thought
- Emotion type: thought.type
- Severity: thought.severity
- Strength: thought.relative_strength
- Personality facets: personality.traits
- World syndromes: df.global.world.raws.mat_table.syndromes.all
- personality.traits uses string keys; thought/emotion records use numeric enum IDs.
- Syndrome vectors contain blank reserved slots; skip empty syn_name values.
- Raw severity can be negative or very large, so it is not a simple happiness scale.
- Thought None and emotion ANYTHING are sentinel values.
- subthought IDs need context-specific interpretation, especially for Syndrome.

## Code and documentation

- AGENTS.md - goals, Clean Code standard, architecture assumptions, project memory rules.
- PLAN.md - phased roadmap.
- dfhack/scripts/lorekeeper/dump.lua - selected-unit/raw data inspector.
- dfhack/scripts/lorekeeper/show.lua - read-only summary window, refresh/copy/close.
- dfhack/scripts/lorekeeper/tokens.lua - runtime token catalog.
- docs/decisions - ADRs.
- docs/notes - environment and test notes.

## Immediate next implementation

1. Build a structured snapshot function shared by dump.lua and show.lua.
2. Add a temporary story placeholder section in show.lua.
3. Add a local helper service later; keep API keys out of DFHack Lua.
4. Send the full structured snapshot plus a compact token reference to gpt-5-mini.
5. Cache responses by snapshot hash, model, prompt version, and schema version.
6. Never block the DF render loop; show loading/error/fallback states.

## Git status

The project has not yet been initialized into a usable Git repository. No remote is configured, no author identity is configured, and the stored GitHub CLI token is invalid. Before committing, ask the user for the desired Git author name/email and remote repository URL, or have them authenticate with gh auth login.
