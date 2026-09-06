# History index verification

Date: 2026-09-06

## Verified environment

- Dwarf Fortress: Steam `v0.53.16 win64 STEAM`
- DFHack: `53.16-r1.1`
- Save: `region3`
- Selected dwarf: Eral èrithbomrek, Fisherdwarf, unit `4068`

## Test procedure

1. Run `lorekeeper/history` for Eral.
2. Confirm the existing 14 records load and changes are reported.
3. Select another dwarf with history and run `lorekeeper/history`.
4. Repeat the lookup for that dwarf.

The first lookup builds the fortress-wide sidecar index. The second lookup for
another dwarf was substantially faster and did not require another full scan.
The timeline reported stress changes and a thought addition for Eral.

## Design notes

- The master JSONL remains the authoritative append-only history.
- The sidecar index is stored in the active save as
  `lorekeeper-history-index/<unit-id>.jsonl` with a `.complete` marker.
- Existing CP437 history records are decoded through `dfhack.df2utf()` when
  needed; new snapshots store UTF-8 and convert only for DFHack console output.
- New dwarves do not need index maintenance manually. Once a snapshot is
  recorded by `lorekeeper/record` or the collector, their sidecar is created or
  updated automatically.
- The collector is still manually started. Automatic incremental index
  initialization remains a future improvement so the first lookup need not
  perform the one-pass build interactively.

## Automated checks

```text
TMPDIR=/dev/shm python3 -m unittest discover -s helper -p 'test_*.py'
```

Result: 12 tests passed. `git diff --check` also passed.
