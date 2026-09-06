# Collector verification — 2026-09-06

Environment: DF 0.53.16 win64 STEAM, DFHack 53.16-r1.1.

## Verified behavior

- `lorekeeper/test` runs the pure snapshot/signature/deduplication/cooldown
  tests without writing to the history file.
- `lorekeeper/record` creates the active save directory and appends JSONL.
- Repeating an unchanged dwarf snapshot is skipped.
- A new dwarf snapshot is appended and reported as recorded.
- `lorekeeper/collect start` starts an all-citizen scan; `status` reports
  scanned and recorded counts; `stop` stops future scans.
- The collector scanned 1,700 snapshots for 68–69 citizens in a test run.

## Tuning observation

An initial signature that included every `subthought` and exact stress value
produced 925 records and a 9.8 MB history file during a short test. The
signature was changed to ignore subthought-only changes, count thought
combinations independent of list order, use 500-point stress bands, and limit
emission to one snapshot per dwarf per 1,200 game ticks.

The existing test history is runtime save data and is intentionally not
checked into the repository.
