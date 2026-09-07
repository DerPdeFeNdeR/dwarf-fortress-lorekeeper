# Typed memoire references — 2026-09-06

## Contract

The user requested general reference resolution so memoires use specific
people, places, and objects. `references.lua` centralizes provider lookup,
typed keys (kind, ID, extra discriminator), deduplication, and explicit status.
This is not a promise that every DF reference meaning has been reverse engineered.
Unmapped thought types retain their token-specific namespace and raw subthought.

Providers cover historical figures, units, incidents, sites, entities, items,
materials, creature/plant raws, colors/shapes, item types/subtypes, and artistic
forms. Profile callers connect supported thoughts, relationships, deity needs,
and type-appropriate preference fields. No recursive reflection over DF objects
or world-wide scans are used. Generic providers not exercised by the selected
profile remain unverified on the installed build and report lookup errors.

Each capture has a fresh cache: no game pointers or stale names survive profile
completion or a save switch. At most 160 records and two link levels are resolved.
Oversize profiles retain the existing 128 KiB rejection. A missing victim unit
can fall back to the incident's historical-figure reference. Preferences use
the installed `unitpref_type` and `mattype`/`matindex` fields, not guessed aliases.
Only the union fields meaningful to each preference kind are interpreted.

Profile schema 2 / worker schema 11 invalidate old output. Prompt guidance uses
resolved family/victim names, without fabricating relationships or identifying
incident IDs as people. Raw timelines remain untouched. Earlier uncommitted
profile work is included in this working batch; no commit/push yet.

## Evidence

- User verified Minkot's profile fields and family links; Momuz is a spouse.
- User inspected incident 141: victim unit 8421, event year 100 tick 390137.
  This matches her long-term witnessed-death memory. The unit lookup identifies
  `Dattle Brown` Obokkudust, Metalcrafter. A separate read-only live lookup
  revealed incident victim_hf.hfid / visual_hfid / historical_hfid all 12569.
- Installed `assign-preferences.lua` verifies preference type/field conventions;
  installed `deathcause.lua` uses incident lookups and unit references.
- Via the installed `hack/dfhack-run.exe`, 40 Lua tests passed, including seven
  shared-resolver checks. All 34 Python tests passed. These counts include the
  earlier on-demand profile tests.
- Live Minkot capture resolves the incident victim, site Quickfortress, materials
  including phyllite/electrum/clear glass, and musical form The Azure Incenses.
  One material reference remained missing; unsupported thoughts stayed explicit.
  A timed capture measured 0.005 seconds with os.clock and 79 entries; this is a
  single CPU-time sample, not a worst-case UI latency benchmark.
- The watcher was restarted and a fresh selected-dwarf story requested through
  DFHack. The ready story named Momuz, three children, Dattle Brown, Quickfortress,
  and several material preferences. It identified the witnessed death in year
  100 without calling the victim Momuz. Visual responsiveness still needs review.
- That real result changed Tirist Sobìrrith to Sobîrrith. The final worker restores
  accent-only differences for uniquely matching full figure names, retaining the
  captured spelling; ambiguous matches remain untouched. A regression test covers
  both cases. Schema 10 regenerates the prior schema-9 result. Tests verify the
  correction; the final rendering still awaits the user's in-game review.

## Remaining coverage

Unverified thought subthought meanings remain unsupported, not inferred from
matching numeric IDs. The historian may not use them as named facts. Cultural
default values and broader historical relationships remain outside this change.
The profile debug output lists resolved and unresolved references for further
field-by-field validation. Current links do not prove relationships at event time.

## Test

The user subsequently verified the ready story's family/victim names, accents,
and responsive UI. They requested removal of writing-process commentary
("no invented speakers") and a blank line before the timeline. The prompt now
explicitly excludes such commentary, and the UI adds a blank display row after
the biography. Schema 11 regenerates earlier prose. New tests cover the prompt
rule and empty display row; the user subsequently confirmed the polished result.
All 35 Python tests and 41 tests invoked through the live DFHack client passed
after these polish changes. The watcher was restarted to load the new prompt.

No DF restart should be needed. Reopen `lorekeeper/history/show` for Minkot and
press R after completion. Verify relevant family names and Dattle Brown appear
naturally, without saying she witnessed Momuz's death. Keep the performance check
and confirm names with accents render correctly. `lorekeeper/profile` displays
reference statuses. The subsequent responsiveness batch adds automatic refresh
and more tests; see `biography-responsiveness.md` for current validation.
