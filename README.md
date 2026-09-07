# The Lorekeeper

Optional atmospheric context uses calendar labels, observed precipitation and
cached local geography. It never invents firsthand weather experiences or filler
chapters; moon phases remain unavailable pending verification.
`lorekeeper/environment` shows status. See [atmosphere notes](docs/notes/observed-atmosphere.md).

Named storytelling now carries the teller and historical subject separately, with
brief organization context when known. Fortress Chronicles include up to four
recent local tellings alongside supported historical events. Use **Year so far**
for an updated draft; completed annual chapters are not rewritten. Cultural
coverage is bounded, not exhaustive; see [cultural chronicle notes](docs/notes/cultural-chronicles.md).

Memoires now have an introduction/recollections section and significant monthly
chapters, headed by year and Dwarven month. Each opening starts at the introduction,
followed by the current/latest recorded month and then older months newest-first.
Each monthly chapter is one paragraph. In **Read Memoire**, use **N/P** to
browse, **I** for the introduction, **U** to check for important new developments,
and **D** for the technical timeline. Quiet months do not create filler passages.
Saved chapters remain readable while the watcher updates one chapter at a time.
Opening does not automatically add paragraphs. See
[monthly memoire notes](docs/notes/monthly-biographies.md) for dating rules,
storage limits, and verification.

First-person dwarf memoires and fortress chronicles, with voices shaped by the
dwarves' personalities. Memoires retain their introduction and monthly chapters;
annual chronicles keep one saved dwarf narrator for each fortress year.

## Read a memoire in-game

With Lorekeeper's scripts and background watcher installed, open a dwarf's unit
sheet and click **Read Memoire** in the Lorekeeper panel, or press **Ctrl+L**.
Alternatively run `lorekeeper/memoire` in the DFHack launcher (`lorekeeper/read`
remains an alias). The reader shows the memoire
without the technical timeline and updates automatically, even while paused.
You may close it and keep playing while the historian writes.

Memoires remember their saved prose. Unchanged evidence reuses it without a
model call; significant compatible new events can add a short continuation with the earlier
story supplied for narrative context. Corrected references, changed stable
character context, time reversals, and length limits instead require a fresh
version. Existing prose remains readable while an update is pending or fails.
See [incremental memoire behavior](docs/notes/incremental-biographies.md).
Routine developments accumulate instead of producing a paragraph on every visit.
When none qualify, the reader says **No significant new developments** and leaves
the saved memoire unchanged.
Named stories heard in performances can qualify as distinctive experiences. The
memoire distinguishes hearing about a historical event from participating in it,
and repeated tellings of the same subject do not automatically add more passages.

- **U:** update the memoire (existing prose stays visible while waiting).
- **D:** switch between story and technical details; **N/P:** browse chapters or
  timeline pages; **I:** return to the introduction in story mode.
- **Arrow keys, Page Up/Down, or mouse wheel:** scroll.
- **Escape:** close. To read another dwarf, close, select them, and reopen.

The separate `lorekeeper/history/show` debug command remains available. The
memoire panel starts near the upper-left of the screen while a unit sheet is
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
