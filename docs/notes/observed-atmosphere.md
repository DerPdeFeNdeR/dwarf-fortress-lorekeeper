# Observed atmosphere — 2026-09-06

Shared `lorekeeper-environment/<site>-<branch>-<year>.jsonl` logs record
central-cell precipitation changes and daily checkpoints. The chronicle monitor
samples once per 120 game ticks; no map scan, extra timer, model call, or full-log
read occurs in the game loop. A single cached site-anchor world biome and named
region describe representative geography, not every embark tile or underground
room. Each file is limited to 4,096 observations / 2 MB, each row to 4 KiB.

Small request references include a committed byte count. Python validates that
prefix, branch, site, year and chronology; caches up to eight parsed prefixes;
and supplies at most one dated weather observation per month to annual prose.
Precipitation is preferred over a no-precipitation checkpoint, not inferred to be
typical of the whole month. Future observations and other branches are excluded.
Missing optional context cannot block generation.

Personal monthly chapters receive only their calendar. Introduction context can
include current geography, but shared weather never enters personal model inputs.
Only a dwarf's own thoughts/memories support firsthand weather experience.
Atmosphere is optional, not required coverage or a significant monthly event.
It is attached after significance selection so weather alone cannot create or
revise passages. Current conditions never become scenery for older events.

Moon phases are unavailable: no verified DF calculation/interface was established.
Do not approximate Earth cycles or infer moonlight, clouds, snow cover, temperature,
or visibility from calendar labels. Existing completed annual chapters stay intact.

Verified against DF 0.53.16 / DFHack 53.16-r1.1: `ReadCurrentWeather`,
`maps.getRegionBiome(site.pos.x,site.pos.y)`, `maps.getBiomeType`, and directly
indexed region names. [DFHack World.cpp](https://github.com/DFHack/dfhack/blob/master/library/modules/World.cpp)
documents calendar arithmetic and the central `current_weather[2][2]` read.
Actual Lua output parsed in Python with dated summer/Malachite weather and the
verified temperate-shrubland setting. No private save fixture added to repository.

115 actual DFHack tests passed. A synthetic live annual generation passed coverage
in 6.04 seconds and cached reopening made no model call. The earlier empty fixture
skipped generation and is not counted as a live model test. Atmosphere can be
omitted by the narrator. 1,000 idle observation calls measured 16 ms total;
this is not a full FPS benchmark or a guarantee of disk latency.

Observer activated in-place; existing watcher restarted. No startup configuration
or task registration changes. No DF restart required. View schema 26 invalidates
explicitly requested prepared views; dormant books are not regenerated.

Player checks: `lorekeeper/environment` should report observing and biome.
Play unpaused, repeat; samples advance, records only change when warranted.
`lorekeeper/chronicles` opens the annual reader; D requests a new draft.
`lorekeeper/memoire` opens a selected dwarf; U requests updates. Verify responsive
UI and no unsupported personal weather claims. Natural weather transitions,
year rollover, mixed-biome embarks, and other forts remain player checks.
No weather manipulation, commit, or push performed.
