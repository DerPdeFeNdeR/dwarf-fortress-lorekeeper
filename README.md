# The Lorekeeper

An in-world historian and storyteller for Dwarf Fortress dwarf thoughts, personality, and fortress history.

## Read a biography in-game

With Lorekeeper's scripts and background watcher installed, open a dwarf's unit
sheet and click **Read biography** in the Lorekeeper panel, or press **Ctrl+L**.
Alternatively run `lorekeeper/read` in the DFHack launcher. The reader shows the biography
without the technical timeline and updates automatically, even while paused.
You may close it and keep playing while the historian writes.

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

Project context and working assumptions are in [AGENTS.md](AGENTS.md). The phased implementation roadmap is in [PLAN.md](PLAN.md). Technical decisions are recorded in [docs/decisions](docs/decisions), and environment discoveries are kept in [docs/notes](docs/notes). The intended first implementation is a read-only DFHack Lua collector and dedicated in-game summary window that exports structured, versioned records for a later history UI.
