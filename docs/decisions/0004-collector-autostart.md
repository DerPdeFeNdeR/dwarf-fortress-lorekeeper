# ADR-004: Start the collector on world load

**Status:** accepted  
**Date:** 2026-09-06

## Context

The collector was previously opt-in and required `lorekeeper/collect start`
after each game launch. That made the full-history workflow easy to forget,
while the external translation watcher already starts automatically at Windows
login.

## Decision

Provide `lorekeeper/autostart`, a small DFHack initialization script that
registers a fortress-load callback and runs `lorekeeper/collect start`.
Users explicitly enable it in `dfhack-config/init/dfhack.init` under the game
directory. The hook now also starts supported-event indexing and the annual /
environment monitor. External watcher startup still requires separate setup.
The existing collector command remains available for status, stop, and manual
recovery.

## Consequences

- New fortress sessions begin collecting without a repeated user command.
- The collector still stops when the world unloads and does not run at the
  main menu.
- Enabling the hook requires one edit to `dfhack.init` and a full game restart.
- Collection remains inside DFHack; translation and model execution remain in
  the external watcher.
