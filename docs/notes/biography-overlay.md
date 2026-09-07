# Unit-sheet biography entry — 2026-09-06

`lorekeeper/overlay.lua` exports the module-loadable overlay
`lorekeeper/overlay.biography`. It defaults enabled with a movable 27x3 panel at
{x=2,y=6}, separate from the vanilla unit pane. Its Read biography label supports
both clicks and Ctrl+L. Focus is restricted to `dwarfmode/ViewSheets/UNIT` and
the active predicate excludes closed sheets, invalid IDs, and customization.

Activation rechecks that the selected unit matches the active sheet before
running the existing reader. No unit pointers are retained. Idle work is limited
to UI-state checks: no profiles, logs, caches, network calls, or collector work.
DFHack owns discovery and saved position/enable preferences. No init-file changes
or watcher restart are needed; the agent loaded it with overlay.rescan().

Sources: [official overlay guide](https://docs.dfhack.org/en/stable/docs/dev/overlay-dev-guide.html),
installed `internal/unit-info-viewer/skills-progress.lua` (unit-sheet focus paths),
and installed `plugins/overlay.lua` (module discovery and world-load rescan).

## Verification

- 52 live DFHack regression tests and 43 Python tests passed; diff check passed.
- `isOverlayEnabled('lorekeeper/overlay.biography')` returned true after rescan.
- Live focus was `dwarfmode/ViewSheets/UNIT/Overview`; panel body was 25x1 at 2,6.
- `require('gui').simulateInput` sent Ctrl+L through the vanilla screen, opening
  the reader for the matching unit 4525. An initial attempt used the wrong
  namespace (`dfhack.gui.simulateInput`); the installed helper resolved that
  diagnostic error. No production code depended on the wrong namespace.
- Pure eligibility tests cover closed/non-unit sheets, invalid IDs, and editing.

The user subsequently confirmed the entry works in-game. Other UI scales and
overlay combinations remain untested. Persistence across a full restart is
framework-supported but has not been retested for this new widget.

## In-game test

No restart required in this development session: the overlay has been rescanned.
Close the biography reader with Escape, leaving the vanilla unit sheet open.
Find the Lorekeeper panel near the upper-left and click Read biography. Check the
name matches the unit sheet. Close it, select another dwarf, and try Ctrl+L.
Check the panel disappears when the unit sheet is closed and does not interfere
with normal controls. `gui/overlay` allows moving it if the default position is
inconvenient; `lorekeeper/read` remains a command-line fallback.
