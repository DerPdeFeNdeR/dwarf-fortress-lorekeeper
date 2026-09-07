# Annual fortress chronicles

Date: 2026-09-06

## Implementation and limits

- Lua: `chronicle.lua` monitors time, `event_index.lua` retains site/year evidence,
  `chronicles.lua` reads prepared chapters. The existing autostart hook starts both
  the index and monitor. No additional DFHack configuration line is needed.
- Python: `chronicles.py`, invoked by `watch_save_directory.py`, handles at most
  one annual model job per watcher cycle. Memoire and annual preparation errors
  are isolated. Existing model configuration remains unchanged.
- Buckets retain at most 256 events per year for the current/previous year. Select
  up to 16 by importance/diversity. Resolution yields after each event and caps
  reference lookups at 256. Export is at most 128 KiB. The existing index uses a
  128-event / approximately 2 ms batch target, not a hard real-time guarantee.
- Explicit site references only. A destination associated with ransom/enslavement
  is not assumed to be where the original capture happened. Unsupported events,
  site-less events, and arbitrary population/economic facts are not reconstructed.
- Empty evidence produces an explicit empty chapter without a model call, never a
  claim that nothing happened. Coverage metadata remains outside narrative prose.
- Each load/time reversal creates a distinct branch. Requests, immutable final
  chapters, and replaceable drafts are stored beneath `lorekeeper-chronicles/` in
  the save. The catalog exposes 100 newest chapters; older files and request audit
  inputs remain on disk. Automatic retention/pruning is not implemented.
- UI reads at most 64 KiB per catalog/chapter and polls once per real second.
  Completed prose is capped at 16 KiB UTF-8 before ASCII-safe JSON encoding.

## Verified

- 76 Python tests passed using `PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm python3
  -m unittest discover -s helper -p 'test_*.py'`.
- 75 real DFHack tests passed with `lorekeeper/test`, including rollover,
  deduplication, time reversal, bounded catch-up, and site bucket isolation/caps.
- A real current-year draft was captured through Lua, processed by the scheduled
  watcher, and published ready in 15.57 seconds. The full event index had scanned
  63,202 events before capture. The draft used 16 selected events; its two required
  named-death factual sentences passed coverage validation. Private generated
  prose and save files are not committed.
- `lorekeeper/chronicles` opened successfully through the live DFHack runner.
  The overlay was rescanned and the existing watcher task restarted (Running).

## Layout acceptance and playtest handoff

Footer follow-up: all hotkey labels now have explicit widths, including the
right-anchored Close control, to prevent it overwriting Year so far. The
Chronicles overlay default is x=6, y=10 (the user requested moving 75% back
from x=18 toward the original x=2), to the right of the left-edge warning
buttons. Existing saved overlay positions are not automatically migrated by a
code update; use `overlay position lorekeeper/overlay.chronicles 6 10` or
`gui/overlay` to adjust that widget only. The user confirmed this position works
and all five footer controls display separately on 2026-09-06.

No game clock changes were made. Natural year-end rollover has **not** been observed
live; the transition logic has automated coverage, not a completed live-year test.
Extended-play responsiveness, scrolling, automatic refresh, and natural annual
generation remain playtest observations to collect, not claims of completed testing.

The user approved this commit checkpoint with the year-end caveat and plans to
play normally afterward, recording bugs and desired improvements. On resumption,
review those observations before starting another feature batch. Useful report
details are the action/command, expected versus actual behavior, displayed status,
approximate delay, game year, and whether a save was reloaded. No private save data
needs to be committed. Do not change the game calendar just to force this test.

1. No restart required for this linked development setup. Open
   `lorekeeper/chronicles`, or click Fortress chronicles / Ctrl+H.
2. Press D for Year so far. Stay paused or close the window and play; model work
   runs independently. The draft should appear without pressing refresh.
3. Scroll; use N/P if multiple chapters exist. R is available only for a failure.
4. Later, leave the monitor active through a natural new year. The completed year's
   chapter should be queued and appear automatically. Reopening must not regenerate
   an already published finished chapter.

New installations still require the documented script path and watcher setup.
Script-path changes require a restart; this feature itself does not edit the
user's DFHack init file or register a Windows task.
