# Lorekeeper reliability and performance review plan

Status: proposed; implementation awaits review. Based on the current checkout
and reported in-game tests. Existing uncommitted auto-queue edits are included
in this review. No runtime changes are made by this document.

## Findings

1. `history/show.lua` synchronously loads history, checks the full cache and
   queue, invokes `story.lua` on a miss, and groups events. `story.lua` repeats
   history loading and builds/encodes the payload before checking duplicates.
   This scales with accumulated data on the game thread. The exact contribution
   of each operation to observed freezes has not been measured.
2. `history.load_snapshots` uses a per-dwarf disk index, but decodes its records
   on every call. It is not a parsed in-memory cache. Startup still scans the
   master history in `load_latest_signatures`, even with an existing index.
3. `build_story_input` repeats full thought/facet summaries for each change.
   Generation input grows much faster than a baseline plus differences needs.
4. `get_story_status` equates presence in the queue with processing, suppresses
   cache-read failures, and hides completed stories when newer records arrive.
   There is no worker heartbeat or durable per-job failure state.
5. `process_queue` normalizes the whole historical queue before filtering cached
   jobs. The 50-item limit therefore eventually blocks a queue even when few
   jobs remain pending. Content deduplication also drops distinct request IDs
   without mapping their shared result back to all callers.
6. `load_queue` falls back to CP437 for the entire file if any byte is invalid
   UTF-8. Mixed legacy/new lines can corrupt otherwise valid Unicode. A partial
   trailing append or malformed entry prevents processing other jobs.
7. Model subprocess execution has no timeout. Save processing is serial, so a
   hung invocation blocks other regions. There is no worker lock; concurrent
   instances can duplicate calls and overwrite each other's cache updates.
8. Collector cooldowns and last-scan metadata survive unload. Cooldown arithmetic
   uses a synthetic million-tick year rather than elapsed game time. Callback
   errors can leave `active` true without a functioning timer. Autostart checks
   world presence, not fortress/map readiness, and suppresses command output.
9. History index writes are not checked, and index completeness is represented
   by a marker without a source revision. Partial writes can leave derived data
   inconsistent with the authoritative log. Rebuilds write directly to indexes.
10. Name repair uses Lua patterns for literal names and can produce mixed UTF-8
    and display-encoded text. The input boundary needs correction and regression
    tests, not additional speculative conversion passes.
11. Windows setup lacks durable startup diagnostics and explicit long-running
    task settings. Its WSL conversion calls Trim before checking exit/output;
    embedded shell quoting does not support apostrophes in paths. Existing task
    exits have not been diagnosed sufficiently to attribute a cause.

## Proposed implementation order

### 1. Bound game-thread work

- Replace synchronous auto-queue with a small save-scoped, dwarf-specific
  request. Use a history revision tied to committed records, not only game time.
- Show the window immediately with identity, last prepared result, and status.
- Have Python read indexed history and publish a compact, paginated timeline
  independently of model generation. UI refresh reads only bounded status and
  result files; detailed history remains available through lazy pages.
- Build story inputs in Python from a baseline plus ordered changes, preserving
  raw history. Do not add collector-maintained narrative caches initially.
- Keep cold initialization and collector recovery bounded in batches; measure
  collector work before changing polling frequency. A deferred callback alone
  is not a performance fix if it still runs a large operation in one call.

### 2. Stabilize request and result lifecycle

- Capture a fixed revision for each job and finish it even as collection runs.
- Display completed older stories with their coverage and a newer-history
  label. Never misrepresent them as current or discard useful completed work.
- Keep one active job per dwarf; coalesce newer requests and rate-limit automatic
  updates. Merely collecting data must not generate model jobs for every dwarf.
- Publish queued, processing, ready, failed, and worker-unavailable states.
  Maintain heartbeat updates independently of blocking model calls.
- Use atomic publication and consistent save/revision keys; tolerate reads
  during appends without treating incomplete trailing records as permanent loss.

### 3. Harden the worker and persistence

- Filter completed work before bounded batching; preserve results for every ID
  when deduplicating equivalent content. Bound payload size as well as job count.
- Add subprocess timeout/cleanup, bounded retries with backoff, and a worker
  lock. Publish actionable errors without credentials or unnecessary save data.
- Decode legacy JSONL per line, preserve valid UTF-8, and explicitly report bad
  records while allowing unrelated work to proceed. New data uses one documented
  Unicode contract with display conversion exactly once at the UI boundary.
- Check append/index errors; make derived indexes rebuildable with validated
  revisions and atomic completion. Keep existing history authoritative.
- Add startup logs and explicit task lifetime/restart settings. Test the actual
  Windows action and login path; registration alone is not startup verification.

### 4. Correct collector lifecycle

- Scope/reset state on save changes, use correct elapsed-time arithmetic, and
  handle time rollback on loading earlier saves.
- Check fortress/map readiness and unit validity; expose initialization and
  errors honestly. Recover from timer failures without duplicate timers.
- Preserve manual stop for the active session and autostart on later loads.

### 5. Verification and documentation

- Cover mixed encodings, literal punctuation in names, Unicode display round
  trips, more than 50 historical jobs, duplicate IDs/content, malformed tails,
  concurrent workers, timeout recovery, and atomic result reads.
- Cover save switching, year boundaries, partial index writes, revision changes
  during generation, and repeated UI requests. Compare Python timeline output
  against existing Lua fixtures before replacing that path.
- Measure cold/warm window opening, refresh, collector callback duration, input
  size, and model duration separately on the real save and a larger fixture.
  Proposed UI target: typical open/refresh below 100 ms, with no unbounded history
  parsing or model waits on the game thread. This is a target, not a guarantee.
- Verify in-game while paused and collecting, with the watcher running/stopped,
  and after save reload. Record observed timings and restart requirements.
- Correct contradictory/stale documentation and record actual test evidence.
  Keep the agreed implementation in one commit after integration verification.

## Scope decision

Defer richer relationships/jobs/locations and major-event collection until this
workflow is reliable. Those features were requested earlier and remain pending;
adding more data now amplifies the unbounded reads. No new database or compiled
DFHack plugin is required for this plan.
