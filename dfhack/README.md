# Lorekeeper DFHack scripts

Use the [root Windows installation guide](../README.md#windows-developer-installation)
for prerequisites, script-path setup, autostart, the WSL watcher and first tests.
This directory contains repository-local Lua scripts, not a compiled plugin.
Nothing here automatically installs files or edits DFHack configuration.

## Commands

Run in the **DFHack launcher** (Ctrl+Shift+D), not PowerShell/WSL. Use slashes.

| Command | Purpose |
| --- | --- |
| `lorekeeper/memoire` | Player-facing selected-dwarf reader; legacy alias `lorekeeper/read` |
| `lorekeeper/chronicles` | Fortress annual reader; no selected dwarf required |
| `lorekeeper/history/show` | Bounded prepared debug timeline; opening requests preparation, R only rereads results |
| `lorekeeper/story` | Queue a small selected-dwarf view request without opening a window |
| `lorekeeper/collect start` | Start/resume citizen snapshot collection |
| `lorekeeper/collect status` | Collector counts/state; unchanged during pause is normal |
| `lorekeeper/collect stop` | Stop citizen snapshots for this session, not the annual/environment monitor |
| `lorekeeper/environment` | Read-only atmosphere observer status |
| `lorekeeper/autostart` | Register fortress-load startup and activate it for an already-loaded fortress |
| `lorekeeper/chronicle` | Start/inspect annual monitor; internal companion to the reader |
| `lorekeeper/test` | In-game regression suite; not `lorekeeper/tests` |
| `lorekeeper/profile` | Inspect bounded on-demand context and resolved references |
| `lorekeeper/dump` | Raw selected-unit identity, thoughts, stress and personality |
| `lorekeeper/history` | Legacy synchronous text timeline; may be slower than prepared readers |
| `lorekeeper/record` | Explicit selected-unit snapshot append, skipping unchanged signatures |
| `lorekeeper/show` | Legacy current-state summary, not a historical Memoire |
| `lorekeeper/translate` | Queue a legacy selected-unit explanation for the save watcher |
| `lorekeeper/tokens` / `lorekeeper/tokens copy` | Runtime token catalog / clipboard export |

Internal modules such as `snapshot` and `glossary` are not standalone narrative
commands. A command finishing successfully does not necessarily open a window.

## Reader behavior

Memoire controls: U requests updated evidence, I returns to the introduction,
N/P browse monthly chapters, D toggles debug details, Escape closes. Select another
dwarf by closing, changing the active unit sheet, and reopening. Story polling does
not recapture profiles or issue new model calls.

Chronicles controls: D requests Year so far, N/P browse chapters, R retries a failed
chapter, Escape closes. The monitor queues completed years after observed rollover;
opening the reader alone does not request a new draft. Good completed chapters are
immutable. Coverage warnings describe bounded collection, not permission to invent.

The debug history window supports R, N/P, Ctrl+C and Escape. It reads small prepared
files and polls once per real second, even while DF is paused. The old `history`
console command uses synchronous Lua history/index helpers; avoid it for latency
measurements of the player-facing readers.

## Overlays

`lorekeeper/overlay.biography` is the retained internal ID of the **Read Memoire**
unit-sheet panel; Ctrl+L activates it. `lorekeeper/overlay.chronicles` opens Fortress
Chronicles with Ctrl+H. Use `gui/overlay` for placement/enabling. Internal identifiers
remain stable to preserve saved settings despite the product rename.

```text
overlay enable lorekeeper/overlay.biography
overlay enable lorekeeper/overlay.chronicles
```

New overlay discovery without a path change can use:

```text
:lua require('plugins.overlay').rescan()
```

## Collection and restarts

The citizen collector checks in batches of 12 with a 100-game-tick interval and a
1,200-tick per-dwarf recording cooldown; full snapshot signatures use 500-point
stress bands. Annual/event/environment tasks are separate. None invokes a model
inside DFHack. Rich profiles/references are captured on demand, not for every dwarf
on every polling cycle.

Configuration files are relative to the **Dwarf Fortress** directory:
`dfhack-config/script-paths.txt` and `dfhack-config/init/dfhack.init`.
A changed script path requires a full game restart. For ordinary Lua edits, close
and rerun the command first; restart if DFHack does not reload a module. Loading
`lorekeeper/autostart` manually can activate the existing hook, but restart to test
future automatic startup after initialization-file edits.

Do not copy scripts over the DFHack installation or change user startup files from
repository automation. Documentation/setup steps require the user's explicit action.
