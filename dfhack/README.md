# The Lorekeeper — DFHack development scripts

This directory contains repository-local DFHack scripts. It is intentionally
not copied into the user's DFHack installation automatically.

## Install for development

The recommended development setup is to add this repository directory as a
DFHack script path. Open this file in a text editor (create it if it does not
exist):

```text
C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\dfhack-config\script-paths.txt
```

Add this line, using the Windows path format:

```text
+C:\Users\contr\projects\dwarf-fortress-lorekeeper\dfhack\scripts
```

The leading `+` tells DFHack to search this development directory before its
default script directories. DFHack reads the file at startup, so fully exit
and restart Dwarf Fortress after changing it. This keeps edits in the project
available without copying files into the DFHack installation.

The equivalent WSL path is:

```text
/mnt/c/Users/contr/projects/dwarf-fortress-lorekeeper/dfhack/scripts
```

The local DFHack installation discovered during Milestone 0 is:

```text
/mnt/c/Program Files (x86)/Steam/steamapps/common/DFHack
```

## First command

1. Start Dwarf Fortress through Steam.
2. Load a fortress save.
3. Select a dwarf with the normal `v` unit view or the unit list.
4. Open the DFHack console. On Windows, use the DFHack console window or the
   in-game DFHack console if enabled.
5. Run:

```text
lorekeeper/dump
```

The command is read-only and currently reports selected-unit identity data.
If no unit is selected, it will print a harmless message instead.

To open the first in-game summary window, select a dwarf and run:

```text
lorekeeper/show
```

Use `Ctrl-R` to refresh the selected dwarf, `Ctrl-C` to copy the visible
summary to the system clipboard, and `Esc` to close the window.

Useful troubleshooting commands:

```text
help lorekeeper/dump
ls lorekeeper
```

To export the active runtime token catalog, run:

```text
lorekeeper/tokens
```

To copy the catalog to the system clipboard:

```text
lorekeeper/tokens copy
```

To append one selected dwarf snapshot to the current fortress history file:

```text
lorekeeper/record
```

Records are written as newline-delimited JSON to the active save directory at
`lorekeeper-history.jsonl`. Repeating an unchanged snapshot for the same dwarf
is skipped. The command records only when explicitly run; it does not poll or
modify game state.

To inspect the selected dwarf's recorded timeline and detected changes:

```text
lorekeeper/history
```

This is currently a read-only text timeline. It reports the raw snapshot count
and a grouped event count, with baseline data, coalesced stress trends, and
discrete changes in profession, thoughts, stress, and personality facets. The
first history lookup builds a fortress-wide sidecar index in
`lorekeeper-history-index`; later dwarf lookups avoid rescanning the master
JSONL file.

To queue the selected dwarf's grouped history for an asynchronous Codex story:

```text
lorekeeper/story
```

This writes a JSONL job without waiting for Codex. Process it with
`helper/process_queue.py`; the structured result is cached beside the active
save for a later history/story view.

To read the cached story and grouped timeline in-game:

```text
lorekeeper/history/show
```

The window supports scrolling, refresh with `R`, copying with `Ctrl+C`, and
closing with `Esc`. It reports whether the latest story is ready, pending, or
not yet requested.

To start or stop the all-citizen background collector:

```text
lorekeeper/collect start
lorekeeper/collect status
lorekeeper/collect stop
```

The collector scans citizens in small batches, keeps signatures in memory,
and writes only changed snapshots. It limits each dwarf to one emitted record
per in-game day while still checking for changes. It is disabled by default
and stops when the world unloads.

To start the collector automatically whenever a fortress loads, add this line
to the DFHack initialization file:

```text
lorekeeper/autostart
```

The file is normally:

```text
C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\dfhack-config\dfhack.init
```

Fully exit and restart Dwarf Fortress after changing `dfhack.init`. The
collector can still be stopped or inspected with `lorekeeper/collect stop` and
`lorekeeper/collect status`.

To run the collector policy tests without writing to the history file:

```text
lorekeeper/test
```

To queue the selected dwarf for an asynchronous Codex explanation:

```text
lorekeeper/translate
```

This writes a structured request to `lorekeeper-translation-queue.jsonl` in
the active save directory. From WSL, run `helper/process_queue.py` with that
queue path and a result path named `lorekeeper-translation-cache.json`; then
run `lorekeeper/show` again or press refresh. The game-facing command never
waits for Codex and never contains an API key.

If DFHack cannot find the command, confirm the path has no quotes, restart the
game completely, and check that the repository file exists at
`dfhack/scripts/lorekeeper/dump.lua`.
