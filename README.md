# The Lorekeeper

An in-world historian and storyteller for Dwarf Fortress dwarf thoughts, personality, and fortress history.

## Read a biography in-game

With Lorekeeper's scripts and background watcher installed, open a dwarf's unit
sheet and click **Read biography** in the Lorekeeper panel, or press **Ctrl+L**.
Alternatively run `lorekeeper/read` in the DFHack launcher. The reader shows the biography
without the technical timeline and updates automatically, even while paused.
You may close it and keep playing while the historian writes.

Biographies remember their saved prose. Unchanged evidence reuses it without a
model call; significant compatible new events can add a short continuation with the earlier
story supplied for narrative context. Corrected references, changed stable
character context, time reversals, and length limits instead require a fresh
version. Existing prose remains readable while an update is pending or fails.
See [incremental biography behavior](docs/notes/incremental-biographies.md).
Routine developments accumulate instead of producing a paragraph on every visit.
When none qualify, the reader says **No significant new developments** and leaves
the saved biography unchanged.

- **U:** update the biography (existing prose stays visible while waiting).
- **D:** switch between story and technical details; **N/P:** page the details.
- **Arrow keys, Page Up/Down, or mouse wheel:** scroll.
- **Escape:** close. To read another dwarf, close, select them, and reopen.

The separate `lorekeeper/history/show` debug command remains available. The
biography panel starts near the upper-left of the screen while a unit sheet is
open. Use `gui/overlay` to move it, or disable it with
`overlay disable lorekeeper/overlay.biography`. Re-enable it with
`overlay enable lorekeeper/overlay.biography`.

New installations discover the overlay when DFHack loads its overlays. During
development, load a newly added overlay without restarting by running
`:lua require('plugins.overlay').rescan()` in the DFHack launcher. If a new script
path was added instead, restart DF as described in the installation instructions.

## Fortress chronicles

Click **Fortress chronicles** in the Lorekeeper panel (Ctrl+H), or run
`lorekeeper/chronicles`. No dwarf needs to be selected.

- **D — Year so far:** request or update a current-year draft.
- **N/P:** browse saved chapters; scroll within each chapter normally.
- **R:** explicitly retry a failed chapter. Successful finished chapters are immutable.
- **Escape:** close and keep playing. The reader updates automatically, including while paused.

With the existing `lorekeeper/autostart` setup enabled, the annual monitor starts
when the fortress loads and queues the completed year after the calendar rolls
over. The background watcher writes the chapter; no model call runs inside DFHack.
Running `lorekeeper/chronicles` also starts the monitor for the current session.
You do not need to start the dwarf snapshot collector to request a draft.

This first version selects up to 16 supported events explicitly associated with
the fortress, rather than claiming a complete account of every activity. Coverage
warnings stay outside the prose. Each fortress load starts a separate recording
branch; earlier chapters remain browsable and are not silently merged after a
reload. See [annual chronicle scope and validation](docs/notes/annual-chronicles.md).

Project context and working assumptions are in [AGENTS.md](AGENTS.md). The phased implementation roadmap is in [PLAN.md](PLAN.md). Technical decisions are recorded in [docs/decisions](docs/decisions), and environment discoveries are kept in [docs/notes](docs/notes).
