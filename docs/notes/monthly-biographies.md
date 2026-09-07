# Monthly biographies — 2026-09-06

Publication checkpoint: the user approved the monthly/cultural batch for commit
and normal play. Current profile/view schemas are 7/21; schema-19/20 discussion
below records earlier iterations. See `../../HANDOFF.md` for the new-session
starting point and remaining long-running playtest coverage.

## Decision and behavior

The user requested a developing biography organized by months within years, with
only important developments. Keep a short introduction/recollections section.
The existing Read biography button remains the entry point; N/P browse saved
chapters in introduction-first order, then current/latest recorded month followed
by older months newest-first. Every opening starts at introduction. I returns to
the introduction, U requests a fresh bounded
capture, D switches to technical timeline pages. No idle model generation.

Each month is exactly one narrative paragraph (normally 100-180 words); the
introduction may have 1-3 short paragraphs. Monthly whitespace is normalized
before coverage validation and publication without dropping facts or accents.
Current-month updates replace that chapter coherently, not append two paragraphs
per opening. Quiet months are omitted. Completed chapters keep their prose when
unchanged or when bounded profile entries disappear. Significant newly discovered
events and corrected evidence can revise an older month. Corrected dates move an
event, not duplicate it in two months. Old revision files are retained.

## Evidence and narrative

- Exact historical/life-event dates select their month. A heard tale uses its
  listening date, not its subject's historical date. The subject ledger prevents
  a repeated tale in another month from causing another passage.
- Unknown dates and initial snapshot thoughts belong to recollections. An observed
  thought change is dated as an observation, not proof its event occurred then.
- Current profile context is not proof of past values/relationships. Prior chapter
  prose is explicitly labeled generated interpretation; only supplied evidence
  supports events. Up to two earlier saved chapters plus introduction provide
  bounded continuity. No selectable narrator or model change.
- Monthly dated milestones/life events/new story subjects bypass routine filters.
  Ordinary thought additions retain the 8 occurrences / 3 types / 3 observation
  threshold. New death thoughts and profession changes qualify directly. Quiet
  month transitions, removals alone, and reopen counts do not create chapters.
- Required named-event anchors are checked per chapter before publication.

Calendar constants were verified in installed DFHack `set-timeskip-duration.lua`
and `position.lua`: 33,600 fortress ticks/month, 12 months/year, Granite through
Obsidian. Unknown/out-of-range ticks are not assigned a month. Primary sources:
[DFHack timeskip script](https://github.com/DFHack/scripts/blob/master/set-timeskip-duration.lua),
[DFHack calendar names](https://github.com/DFHack/scripts/blob/master/position.lua).
Prompt instructions separate rules, facts, and prior prose following
[OpenAI instruction/context guidance](https://developers.openai.com/api/docs/guides/prompt-engineering#message-roles-and-instruction-following).

## Persistence, performance, and limits

`monthly_biography.py` owns the Python-only `<unit>.monthly-book.json` manifest,
written-evidence checkpoints, and immutable `<unit>.monthly.<digest>.json` chapters
under `lorekeeper-views`. Schema 20 / request monthly_version 1 opt into this path;
old protocol requests retain the legacy implementation. Existing biographies remain
readable during lazy migration. No bulk migration of dormant dwarves.

Introduction is generated first, then months newest-first. One model call per dwarf
per watcher pass; timelines/catalogs publish before model
work. A failed chapter keeps published prose and does not advance its written
checkpoint. Pending evidence persists so small additions accumulate. Explicit U
retries failed requests. Background passes resume unfinished chapter sets.

Game-side chapter reads are capped at 64 KiB and filenames are constrained to the
selected unit. Chapter prose is capped at 8,000 UTF-8 bytes, model input 200 KB,
prior prose 12,000 characters. The manifest read limit is 2 MB (write guard 1.9 MB),
up to 1,200 chapter buckets / 2,000 heard-subject identities. Capacity errors are
visible; they do not silently erase old prose. The UI exposes the newest 99 monthly
chapters plus introduction; older chapters remain on disk. Long-term archive
pagination beyond this window is not implemented.

Backward request time, record-prefix changes, or added timeline resets archive the
manifest and start a separate book. The raw technical timeline remains unchanged.
Historical source coverage is still bounded and incomplete. Important experiences
forgotten before any on-demand profile capture may remain unavailable.

## Verification and handoff

- Automated tests cover month/year boundaries, invalid/unknown/future dates,
  listening vs narrated-event dates, quiet months, cached reopening, one chapter
  per pass, same-month replacement, bounded profile eviction, failed generation,
  archived reversals, and repeated story subjects across months.
- Opt-in real integration test:
  `LOREKEEPER_LIVE_MONTHLY_TEST=1 python3 -m unittest test_monthly_biography.MonthlyBiographyTests.test_live_monthly_generation_and_cached_reopen`
  from `helper/`. Passed with isolated synthetic save and real authenticated model:
  monthly chapter 9.51 s, introduction 9.90 s; reopen made zero model calls.
- Actual player acceptance of monthly navigation and narrative remains pending.
  Natural annual fortress rollover remains separately unverified.

### Single-paragraph / introduction-first revision

The user subsequently requested exactly one paragraph per month and introduction
as the first page, followed by the current/latest recorded month and older months.
Schema 20 and the chapter writer fingerprint invalidate old writing on a fresh
request; no dormant biography migration is triggered. Opening selects `intro`
explicitly and background refresh retains an explicitly selected month.

Validation: 110 Python tests passed, with two opt-in integrations skipped in the
ordinary suite; 85 DFHack tests passed. The revised opt-in real monthly test also
passed separately (introduction 9.54 s, month 11.60 s), confirming chapter order,
single-paragraph monthly output and zero model calls on cached reopening.
The existing watcher was restarted successfully. Live reader inspection confirmed
introduction selected and first in the prepared catalog; simulated N opened the
latest recorded month and P returned to introduction. Player visual acceptance
is still required before publication.

No DF restart should be needed: rerun `lorekeeper/read` or Read biography. The
watcher must restart to load changed Python modules (existing task restarted during
development). If DFHack retains an old module, restart DF as fallback; no script
path, startup config, scheduled-task registration, or model setting changed.

Suggested player check: open a dwarf with history, confirm introduction is page 1,
press N for the latest recorded month (one paragraph), then older months. Use P/I
and I, verify the game stays responsive during writing, then close/reopen with no
game-time changes and confirm saved chapters appear without new prose. Continue
normal play and use U after an important development; the affected month should
update rather than duplicate itself. No need to start an already running collector.
