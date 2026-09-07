# 0008 — Shared observed atmosphere

Date: 2026-09-06

Use calendar context and one shared fortress observation log for occasional
narrative atmosphere. Do not expand each dwarf's periodic snapshot or scan the
map. Resolve representative geography once per session; observe central-cell
precipitation at a modest game-time interval. Python handles bounded parsing.

Historical weather reconstruction, Earth-derived moon cycles, whole-map scans,
and weather-triggered prose generation were rejected for accuracy and overhead.
Current weather must never describe old events. Personal memoires cannot inherit
firsthand experience from fortress observations. Moon phases stay unavailable
until verified against DF. Missing optional scenery is preferable to invention.

Consequences: short weather changes can be missed; geography is representative,
not every embark tile. Existing autostart integration is reused, and the player
need not run another collector. See [implementation and tests](../notes/observed-atmosphere.md).
