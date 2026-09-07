# Memoire responsiveness — 2026-09-06

## Change

The player reported a long wait for Udib's first biography. Keep game display
work bounded and useful independently of model completion:

- Show the existing memoire immediately, or an explicitly non-generated
  overview (stress and up to three emotional entries) if no memoire exists.
- Poll prepared status once per wall-clock second while the window renders,
  including while paused. Rebuild choices only when status changes and preserve
  selection. R remains available; neither polling nor R recaptures the profile.
- Compact model input, retaining named references and meaningful character data.
  Deduplicate equivalent emotions into counts, omit recall timing/strength, and
  summarize stress/need focus in numerical 1000-point bands. These are not game
  diagnostic thresholds. Exact source data remains in history and profile files.
- Cache stories by semantic input separately from full timeline revisions.
  Within-band stress-only updates can reuse a story while refreshing the timeline.
- Publish all discovered same-save timeline pages before model calls; prioritize
  newer requests. Schema 12 applies on new requests without regenerating dormant
  completed dwarves after a worker restart.
- Record queue, preparation, model-queue, generation, and total seconds plus model
  input bytes and cache-hit status in prepared status JSON.

## Verification

41 Python tests and 42 tests through the running DFHack client passed.
Coverage includes semantic cache reuse/invalidation, preservation of named
references/counts, mixed-event final stress, dormant schema upgrades, publication
of multiple timelines before model work, and the immediate factual fallback.
`git diff --check` passed.

Restarted the installed watcher task. In the live selected-dwarf window (unit
4525), inspected processing then ready without invoking R or refresh. The game
remained paused and render polling advanced. The prior story remained available.

Single observed fresh request:

- Queue: 2.97 s; preparation: 0.52 s; model queue: 0.05 s.
- Generation: 24.34 s; total: 27.88 s.
- Compact input: 43,900 bytes versus approximately 103,030 bytes before this
  change (about 57% smaller). This does not guarantee proportional model speedup.

Reopening the same paused dwarf reported cache_hit=true, generation=0,
preparation=0.037 s, and total=2.21 s including watcher polling delay. These are
single samples, not UI frame-time measurements or worst-case guarantees.

## Remaining limits and user test

Fresh model generation remains slow. The watcher is still sequential: an
in-flight generation can delay newly arriving requests and other saves. The
worker still reads changed full history logs outside DF. Investigate measured
load times next rather than claiming generation latency is solved.

No DF restart is expected. Close/reopen `lorekeeper/history/show`; it requests
fresh preparation and should update automatically without R, even while paused.
Existing stories should stay readable during preparation. Check N/P pagination
and scrolling stay usable. A dwarf without cached prose should show a factual
overview first. Visual responsiveness/fallback confirmation by the user remains
pending for further latency comparisons. The user subsequently confirmed that
the window updated without R. Follow-up model testing is recorded in
`luna-biography-validation.md`.
