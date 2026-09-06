# Reliability batch validation

2026-09-06: core in-game workflow verified by the user; remaining boundaries
are listed below.

## Current changes

- `history/show` and `story` write small requests. Python prepares timelines and
  story payloads. The GUI reads at most 64 KiB per result/page and displays 20
  timeline events per page (N/P keys). R reads prepared results without issuing
  additional model work. Reopening requests a current view.
- Generated pages are published before model generation; an older story remains
  readable with its revision status. Generation has a 180-second timeout and
  cleans up its process group. Failed views retry at most three times with backoff.
- Requests coalesce by dwarf; model input uses baseline plus changes, with a
  200 KB input limit and 8 KB story limit. Large histories still show a timeline.
- Worker heartbeat runs independently of model execution; a directory lock
  prevents duplicate all-save watchers. Legacy cache writes use a separate lock.
- Mixed legacy/new JSONL decodes per line. Incomplete trailing writes wait for
  completion; malformed complete lines warn rather than preventing other jobs.
- Completed jobs are filtered before the 50-job limit. Equivalent content
  returns results for every request ID. Existing save logs are preserved.
- Collector initializes in 16-record slices, clears state on map/world unload,
  resolves unit IDs per scan, handles callback failure, and uses 403200 ticks per
  year. Autostart waits for a fortress map. Index write failures invalidate the
  completion marker for recovery.
- Startup wrapper logs to ~/.local/state/lorekeeper/watcher.log (or XDG_STATE_HOME).
  Windows registration specifies unlimited duration and three restart attempts.

## Evidence and limits

- 24 Python tests passed during implementation.
- Read-only preparation against region3, dwarf 3535: 48 records, 35 grouped
  events in approximately 0.464 seconds outside DFHack. This is not a UI timing.
- On 2026-09-06, the user verified collector autostart after restarting,
  processing-to-ready story completion for Lolor, responsive opening/refresh,
  and N/P timeline pagination with the story retained above it. Windows logon
  task state was not separately reported in this test. No game installation
  configuration or scheduled task was changed by this batch.
- The same test exposed `??` between story paragraphs. The display path now
  splits line endings before UTF-8-to-DF conversion and retains empty lines.
  Four DFHack regression checks cover paragraph breaks, CRLF/CR/tabs, accented
  names, and wrapping. The user subsequently reported all 30 DFHack tests passed
  and supplied Lolor's ready story with correctly rendered blank paragraphs.
- Final checks: all 24 Python tests, shell syntax, and Windows installer `-WhatIf`
  passed. The dry run did not register a task. Installed recovery settings remain
  unchanged (72-hour limit, no restart attempts, battery restrictions); the
  updated installer requires explicit user registration to apply its settings.
- Remaining unverified boundaries: automatic Windows logon recovery with the new
  settings, clipboard output, watcher-off UI behavior, and switching saves in
  one game session. Tests exercise malformed/partial JSONL and worker failure
  with fixtures, not deliberate corruption of the user's save. No numerical
  cold/warm UI benchmark was recorded; responsiveness is user-reported.
- Python reads the authoritative master log to avoid trusting legacy indexes;
  a save/size/modification-time keyed parsed cache avoids repeated reads of
  unchanged data. Only one save is retained in memory. Old generated pages and
  requests are pruned after publication. This is a simpler recovery approach
  than extending the legacy index protocol, which remains for the debug command.
  Richer snapshot fields remain deferred as agreed in the review plan.
- Official lifecycle reference: https://docs.dfhack.org/en/50.11-r1/docs/dev/Lua%20API.html
- Calendar reference: https://docs.dfhack.org/en/52.03-r1/docs/tools/set-timeskip-duration.html

## Repeatable integration procedure

Restart the watcher to load changed Python. Restart DF to reload the collector
and changed module state. Select a recorded dwarf and open history/show. Confirm
prompt opening while paused, prepared timeline before model completion, R reads
completion, N/P page correctly, and accented names/copy work. Repeat with ongoing
collection, watcher stopped, malformed legacy data, and a save unload/reload.
Record cold/warm timing separately. Core opening/refresh, completion, pagination,
and paragraph rendering were verified above; do not infer that all failure and
lifecycle scenarios have been validated from that successful path.
