# Historical episodes — 2026-09-06

## Decision

Use a bounded session-local Lua index of explicit historical participants, with
Python selecting the compact narrative evidence. This extends the existing
on-demand family/friend event work without scanning world history in the reader.
No synchronous full scan, external Legends export, or persistent database is
required. A separate incremental task reuses history records the game retains.

The index starts through the existing autostart script or first profile capture.
It visits at most 128 records per frame callback, with a 2 ms CPU-time target
(not a hard wall-clock deadline), and polls for additions every 100 frames once
caught up. It discards state on unload, clock reversal, and event-vector shrink.
It is rebuilt on loading a fortress, not written to save files. Normal profiles
remain bounded files under the existing save-local view protocol.

Limits: 50,000 participant links, 32 retained events per indexed
figure, 32 participants per group. A fixed-size ring evicts oldest links at global
capacity. Per-figure retention favors milestones over travel and routine changes,
then newer event IDs within the same priority. Coverage is explicitly partial.
Requests include at most 8 selected indexed events, favoring kind diversity,
and 8 participant names each. Names use the shared 160-reference resolver budget.
The subject's known role is retained independently of the displayed-name cap.
No automatic generation occurs when the index finishes: Update/reopen captures
new evidence. The reader warns if its profile was captured during indexing;
Details exposes scan/error/truncation coverage.

## Contract and safety

Profile schema 5; prepared-story schema 16. Historical episodes participate in
model caching; index progress alone does not. Event IDs deduplicate records;
separate same-time records are not fused into a fabricated battle. Birth/death
reference-derived life events remain available alongside historical episodes.

Supported fields are verified against the primary
[DFHack history event structures](https://github.com/DFHack/df-structures/blob/master/df.history_event.xml):
simple battle group1/group2, site attacker, victim/slayer, woundee/wounder,
artifact creator and name_only flag, event year/seconds, and site. No outcomes,
criminal intent, emotions, strange moods, or relationships at the event are
inferred. An artifact naming event is not creation. Additional verified mappings
cover abduction, release, enslavement, ransom, reunions, travel, profession/state
changes, entity/personal link additions/removals, moods, and masterwork items.
Large entity/army battles, generalized accidents, and unretained events remain
unsupported. A spouse-link addition is a dated relationship record, not evidence
of a wedding ceremony. Position link changes are retained, but numeric position
references remain unnamed: installed definition index versus stable ID semantics
need additional validation before deriving titles. Ransom payer fields are omitted
because their documented original field names/namespaces conflict. No guesses.

## Validation

Live scan: 63,202 records, zero normalization errors, maximum observed batch
approximately 1 ms. Two enriched citizen captures measured approximately 5 ms
and 88–89 KiB each. These are samples, not worst-case FPS guarantees.
Real records resolved a named artifact at the current fortress and an earlier
attack/scuffle with named figures at another site. Numeric slayer attribution
was retained without guessing criminal intent. No private save dump was added.

Automated coverage includes participant roles, naming-only semantics, link and
per-figure limits, duplicate participants, partial-index disclosure, future dates,
unsupported types, episode bounds, Unicode artifact names, and cache behavior.
57 Python tests and 62 DFHack tests passed. A real schema-14 worker request
produced a memoire including the named artifact and creation year; generation
took 10.51 s, preparation 0.58 s, and total latency 12.63 s. An older conflicting
opening instruction was then restricted to cases without substantial historical
episodes. Narrative style and event selection remain subject to user review.
The user approved the initial historical-event memoires and subsequently
authorized publishing the combined expanded-event/coverage batch on 2026-09-06.
Rare-event live coverage limitations remain documented below.

## Expanded-type validation

60 Python and 69 DFHack tests passed. Live expanded scan: 63,202 records,
zero normalization errors, roughly 3 ms maximum observed batch (the CPU-time
target is cooperative, not a hard deadline). An initial scan filled the global
limit before reaching recent events; the bounded ring fixes this. Rebuilt index
retained 47,761 links and preserved the existing artifact plus a mood event and
organizational position change. A sampled expanded profile was 88,730 bytes and
about 5 ms to capture. Names/IDs are resolved only on demand, not while scanning.
Tests additionally cover captivity roles, escape/return flags, relationship
direction, profession endpoints, milestone protection, and full-capacity eviction.
The watcher was restarted for schema 15. No game restart or config edit needed.
A real schema-15 request completed in 15.05 s total (11.18 s generation,
0.50 s preparation) and included the recorded fey mood before artifact creation.
Not every newly supported type occurs in the exercised citizen profile; captivity
and other rare-event paths still need representative live user verification.

No game restart should be needed in this session; the index was started and the
existing watcher restarted. Select a dwarf, run `lorekeeper/read`, then U if
already open. D shows coverage. `lorekeeper/event_index` prints diagnostics.
On the next game launch, the already-enabled autostart hook starts the index.
No edits to the user's DFHack init or scheduled-task registration were made.
