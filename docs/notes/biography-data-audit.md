# Biography data audit — 2026-09-06

Initial read-only audit followed by the on-demand implementation below.

## Current gaps

`snapshot.lua` reads `personality.emotions`, stress, and personality traits.
It retains subthought references but not emotion flags or timestamps. It does
not separately capture memories, values, preferences, needs, or relationships.
`history_view.py` compares thoughts by thought/emotion IDs, so same-category
reference replacements can disappear from the grouped timeline. Enriching
biographies requires revisiting semantic event identity without reintroducing
the old subthought-only recording churn.

## Sources and compatibility

The installed DFHack `devel/export-dt-ini.lua` references soul preferences,
personality values/needs, and emotion year/year_tick. Installed family-affairs
code uses historical figure links with `target_hf` for relationships. These
scripts were inspected only; no modifying commands were run.

Upstream [personality structures](https://raw.githubusercontent.com/DFHack/df-structures/master/df.personality.xml)
describe separate short-term, long-term, and core memories, memory-related flags,
and core-memory facet/value changes. The Death circumstance reference targets a
historical figure; witnessed-death/body thought names point toward incidents.
Reference interpretation is token-specific. Upstream master is not a verified
layout contract for the installed version: probe actual fields read-only before
implementing capture. Memory last-used dates must not be mislabeled as event dates.

## Minkot evidence

Existing unit 6745 records contain Death/SADNESS and UnexpectedDeath/UNEASINESS
with subthought 7068; WitnessDeath/HORROR uses 141. SawDeadBody references include
389, 238, 326, 390, 388, and 387. These are raw references, not resolved names.
Do not assume the witnessed death is the death associated with sadness. A live
historical-figure/incident lookup and relationship lookup are still needed.
Current relationship links would not alone prove the relationship at death.
The user subsequently resolved HF 7068 as Momuz Lilumuzol in the loaded game,
and, with Minkot selected, found `histfig_hf_link_spousest` targeting that figure.
The first diagnostic commands failed due to Lua argument parsing and an obsolete
function name; `:lua` and `dfhack.translation.translateName` are the verified forms.

## Next implementation boundary

Add a bounded selected-unit audit/profile capture, not a fortress-wide historical
event scan in a GUI callback. Probe thought and memory fields, resolve supported
reference types, and report unsupported/unresolved fields explicitly. Compare
the result against the selected dwarf's game UI before feeding it to the model.
Capture values (including relevant cultural defaults), preferences, needs, and
relationship context on demand. Keep richer profile context separate from the
high-frequency collector until meaningful change rules and cost are measured.

## On-demand implementation (awaiting game verification)

`profile.lua` reads capped sections on request: emotions and their timestamps/
flags, short/long/core memories, explicit values, needs, raw preference IDs,
current historical-figure links and resolved names, plus selected personality
facets. It reports unavailable/truncated sections. Core memory change fields
remain raw enums; cultural defaults and preference labels are not implemented.
This is an incremental profile, not a claim of complete biography coverage.

View requests reference immutable profile files, capped at 128 KiB. Python
validates paths, size, and matching unit identity; incorporates profile content
into revision hashing; and supplies it alongside the latest-segment narrative
events. Capture time alone does not invalidate cache. Schema v8 invalidates
old prepared results. Profile collection is only on open/request, not R or the
collector, and does not scan world event lists. Its game-thread latency still
needs measuring in-game. Old referenced profiles are pruned with superseded
requests after model processing; failed/unpublished writes may leave orphans.

All 33 Python tests pass, including bounded profile reads, ID/path checks,
cache identity, and fixture profile delivery through the request/model path.
Two new DFHack tests check supported versus unresolved reference kinds (33 total
expected). Live field compatibility, runtime cost, and model use of real profile
context remain unverified; do not publish before the in-game check.

Restart the watcher, then select Minkot and run `lorekeeper/test`,
`lorekeeper/profile`, and `lorekeeper/history/show`. No DF restart should be
needed; rerun the command first and restart only if changed modules stay stale.
Check profile counts/limitations and the Momuz spouse link, responsiveness, and
that the story does not conflate witnessed death with the named death reference.
