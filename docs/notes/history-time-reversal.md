# Recorded time reversal — 2026-09-06

## Evidence

The user verified automatic Windows logon task startup (`Running`) after
registering the updated task in administrator PowerShell. The history window
was responsive and displayed Minkot Udistatír's ready story, including accents.
This verifies startup and the normal workflow, not automatic recovery after a
forced worker failure.

A read-only check of Minkot's authoritative records (unit 6745) found 50 records,
including year 102 tick 112416 followed by tick 109747. The story had interpreted
thought differences around this reversal as removals. Loading an earlier save
is a possible explanation, but the log does not establish the cause.

## Decision

Preserve append order and raw records. Python starts a `timeline_reset` event
with a full fresh baseline whenever a dwarf's recorded (year, tick) decreases.
Do not calculate thought, profession, personality, or stress deltas across it.
Subsequent changes use the new baseline. The model is instructed to distinguish
segments and not infer causal continuity across them. Timeline pages label the
boundary explicitly. Schema v5 participates in revision hashing and bypasses
old ready/failed request state, so earlier stories are regenerated.

Sorting by game time would interleave observations from potentially different
playthrough branches. Deleting old records would lose evidence. Neither is done.

## Validation and limitations

- All 28 Python tests pass, including four new tests for baseline isolation,
  stress grouping, year rollover/equal timestamps, and old-schema regeneration
  through request/page/model-result publication with a mocked model.
- Read-only execution on Minkot's real records detects exactly one boundary,
  from tick 112416 to 109747. No save records were modified by this check.
- Detection is per dwarf: a rollback that does not produce a backward timestamp
  in that dwarf's observations cannot be detected by this rule. Explicit
  save-session/branch identity remains future work.
- On 2026-09-06 the user verified the regenerated ready story for Minkot:
  it distinguishes two segments, reports the reversal without asserting a cause,
  and treats the latest segment as a fresh baseline. Page 2 of 2 shows event 34
  as `timeline_reset` at tick 109747, with previous tick 112416 and the explicit
  message that changes across this boundary are not inferred. The displayed
  timeline retains all 50 records and contains 34 events.
- The debug `lorekeeper/history` command retains its legacy grouping behavior;
  this change targets Python-prepared `lorekeeper/history/show` and stories.

## Test procedure

Restart the watcher (not Dwarf Fortress) to load Python changes. Open Minkot's
`lorekeeper/history/show`, wait in real time while paused, then press R. Expect
a ready story separating the time-reversal segments without treating differences
across them as normal removals. Press N to locate the final timeline page and
verify the `timeline_reset`/fresh-baseline label. Other outstanding requests
may regenerate once because of the schema change. This procedure passed as
reported above; future changes still require verification before publishing.
