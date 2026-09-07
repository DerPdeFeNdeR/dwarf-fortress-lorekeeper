# The Lorekeeper

An in-world historian and storyteller for Dwarf Fortress dwarf thoughts, personality, and fortress history.

## Read a biography in-game

With Lorekeeper's scripts and background watcher installed, select a dwarf and
run `lorekeeper/read` in the DFHack launcher. The reader shows the biography
without the technical timeline and updates automatically, even while paused.
You may close it and keep playing while the historian writes.

- **U:** update the biography (existing prose stays visible while waiting).
- **D:** switch between story and technical details; **N/P:** page the details.
- **Arrow keys, Page Up/Down, or mouse wheel:** scroll.
- **Escape:** close. To read another dwarf, close, select them, and reopen.

The separate `lorekeeper/history/show` debug command remains available. A button
on the vanilla dwarf screen is planned separately; it is not installed yet.

Project context and working assumptions are in [AGENTS.md](AGENTS.md). The phased implementation roadmap is in [PLAN.md](PLAN.md). Technical decisions are recorded in [docs/decisions](docs/decisions), and environment discoveries are kept in [docs/notes](docs/notes). The intended first implementation is a read-only DFHack Lua collector and dedicated in-game summary window that exports structured, versioned records for a later history UI.
