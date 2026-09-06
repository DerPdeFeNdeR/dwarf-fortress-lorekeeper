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

The grouped timeline was verified for Mistêm Oslandakas:

- 30 raw records were summarized as 18 events.
- Consecutive stress-only changes were coalesced into stress trends.
- Thought changes remained discrete events alongside any stress change at the
  same snapshot.
- `lorekeeper/test` reported 23 passing DFHack tests.

The dedicated history window was then verified for Mistêm:

- `lorekeeper/history/show` displayed the cached story with high confidence.
- It displayed 30 records and 18 grouped timeline events.
- The window rendered the accented dwarf name correctly and remained usable for
  scrolling through the timeline.

The enriched history-story path was verified afterward:

- `lorekeeper/test` reported 25 passing DFHack tests.
- `lorekeeper/story` queued the versioned `dwarf-history-v2` request.
- The Codex helper processed one fresh job and returned a high-confidence
  story using the exact timeline inputs.

The hands-off watcher path was verified afterward:

- The watcher monitored the active region queue in a separate WSL session.
- A collector run increased Mistêm's timeline to 32 records and 20 events.
- `lorekeeper/story` queued the fresh story while the game remained open.
- The watcher automatically processed one job, and the in-game history window
  displayed the updated cached story after refresh.

The story lifecycle status was then verified during the same run. The history
window displayed the current cached story after the watcher completed; because
processing finished before the window opened, the transient pending state was
not visible. The modal window pauses the game while open, and `R` rereads the
cache without requiring a restart.

The save-directory watcher was also smoke-tested against the real Dwarf
Fortress save directory with `--once`; it discovered the save queues and
completed with zero pending jobs. Its unit test confirms that multiple region
queues are processed independently and that unchanged queues are not rerun.

Unicode cache handling was verified with the active save. The helper now writes
escaped Unicode rather than transliterating model text, and the in-game history
window displays `Mistêm Oslandakas` correctly after the watcher processes a
fresh story job. A later Doren story exposed CP437 mojibake in model-generated
name text; the queue processor now repairs that known form and story requests
use version 3 so the corrected path is regenerated.
The in-game history view also repairs that form at display time so existing
caches remain readable without destructive save-file edits.

The collector prewarm path was also verified:

- `lorekeeper/collect start` started for 68 citizens.
- `lorekeeper/collect status` reported 828 scans and 68 records written.
- `lorekeeper/collect stop` completed normally.
- `lorekeeper/history` then loaded 30 records for Mistêm Oslandakas and
  reported stress and thought changes.

## Design notes

- The master JSONL remains the authoritative append-only history.
- The sidecar index is stored in the active save as
  `lorekeeper-history-index/<unit-id>.jsonl` with a `.complete` marker.
- Existing CP437 history records are decoded through `dfhack.df2utf()` when
  needed; new snapshots store UTF-8 and convert only for DFHack console output.
- New dwarves do not need index maintenance manually. Once a snapshot is
  recorded by `lorekeeper/record` or the collector, their sidecar is created or
  updated automatically.
- The collector prewarms the index during its startup scan. The optional
  `lorekeeper/autostart` hook now starts it on world load when enabled in
  `dfhack.init`.

## Automated checks

```text
TMPDIR=/dev/shm python3 -m unittest discover -s helper -p 'test_*.py'
```

Result: 15 tests passed. `git diff --check` also passed.
