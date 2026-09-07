# Faster personal chapters — 2026-09-07

The user approved personal-fact compilation, relevant character context, and
shorter quiet chapters (ideas 1, 2, 3). Worker polling behavior and the annual
writing strategy were not changed in this batch.

`helper/memoire_brief.py` operates only on the existing knowledge-filtered input:

- Typed incident references become body-sighting or witnessed-death facts, retaining
  counts and distinguishing unspecified emotion from any particular reaction.
  Incident methods and performance subjects are not exposed through these brief
  facts. Unknown thought meanings remain explicitly untranslated structured data.
- Life-event body sightings retain their personal involvement and date caveat:
  a death date never dates the sighting or recollection. Heard office stories use
  the existing first-person anchor builder with teller, topic year, listening time
  and supplied organization classification kept separate.
- Supported own membership, whereabouts and profession changes become explicit
  personal facts after checking the subject's historical-figure identity. Membership
  is not travel or appointment; whereabouts is not proof of immigration. Other
  event types remain structured instead of receiving a guessed translation.
- Observation additions/removals retain counts and observation-time scope.
  Mandatory historical facts remain in the unchanged required-fact list.
- Monthly character context includes related names appearing in chapter evidence
  or mandatory facts, relevant preferences, the short voice guide and explicit
  values. Only reachable typed references are included; reference cycles terminate.
  Generated earlier prose and other months' emotion lists stay excluded.
- Introductions retain a broader bounded portrait: at most eight current links
  per relationship/friend collection, six preferences, and eight distinct thought
  types per baseline/recollection selection. This is editorial selection of optional
  context, not a change to raw history or a claim of exhaustive personal memory.
  Every chapter evidence row and mandatory factual anchor remains represented.

Quiet months target 60–100 words. More than three evidence rows, consequential
events, or more than 70 mandatory-fact words select 100–180. Introductions target
80–140 words in 1–3 paragraphs, choosing a few recollections rather than a body
sighting inventory. Targets are editorial prompts, not hard truncation limits;
required facts outrank brevity. Existing final paragraph, size and coverage checks
remain in force. No second writing call, fallback fiction, or automatic retry was
added. Preset `qwen3-personal-v7` prevents stale writer reuse on an explicit Update.

## Verification

Linux and native Windows Python each ran 202 tests: 195 passed and seven optional
live tests skipped. New tests exercise typed reference misuse, seeing versus
witnessing, unspecified reactions, observation removals/counts, date scope, linked
reference cycles, unrelated people, personal HF identity, membership versus travel,
and mandatory-fact length overrides. Source inputs remain unmodified.

Real captured Minkot requests were evaluated in ignored local files, not published
to the game's book. An initial quiet-month candidate confused raw membership data
with travel; the explicit membership/whereabouts compiler was added before the
final check. Final quiet Slate request: 982 input tokens, 114 output tokens,
3.94 seconds (0.46s prompt evaluation, 3.36s generation). Its initial form had
1,263 input tokens and took 4.24s.

The captured introduction fell from the earlier 10,462 tokens to 2,914 in the first
compact check. That attempt still spent 11.66s generating repetitive prose, so the
final introduction prompt asks for 80–140 words and a few recollections. The final
isolated full monthly pipeline completed introduction in 7.02s and Limestone in
5.60s, with Limestone's required heard-story fact passing unchanged. Four months
remain pending in that diagnostic book; no full-book v7 acceptance is claimed.

These are individual warm-model measurements, not a statistical latency guarantee.
Free prose can still invent details, generalize from values or produce weak
reflection; required-fact checks do not prove every sentence. Review narrative
quality in play. Model/context/GPU settings remain unchanged from v6.

The native watcher was restarted with v7, using ignored
`.lorekeeper/watcher-v7.out.log` / `.err.log`. See HANDOFF.md for the latest process
checkpoint. Press U in Memoire to request the new writer. No Dwarf Fortress restart
is required; only Python code changed. No startup task, commit or push was created.
