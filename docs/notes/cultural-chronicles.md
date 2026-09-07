# Named storytellers and cultural chronicles — 2026-09-06

Publication checkpoint: the user subsequently approved the result and requested
commit/push before normal play. See `../../HANDOFF.md`. Pending-review statements
below describe earlier development checks; extended playtesting and natural annual
rollover remain pending, not approval to publish this batch.

The user asked what The Oracular League and The Letter of Safety meant in Brow's
introduction, and requested these local tellings in the Fortress Chronicle,
including the storyteller when available. These names refer to organizations,
not travelers or (despite its name) a physical letter.

## Verified reference mapping

Read-only live checks found entity 742 to be `SiteGovernment`, race human, named
The Oracular League; entity 311 is `Civilization`, race dwarf, The Letter of Safety.
These are **current classifications**, not proof of their historical form.

- Incident 652: Othdo Adeaspa tells about Laka Colorstyles taking the office of
  lord in The Oracular League in year 77.
- Incident 646: Eral Vabôkulåb tells about Cog Rackphrased taking the office of
  monarch in The Letter of Safety in year 35.
- Both are local performances at site 745 in year 102. The narrated appointments
  must not be recorded as appointments at Quickfortress in year 102.

The incident Performance union/discriminator was previously verified against
[DFHack incident structures](https://github.com/DFHack/df-structures/blob/master/df.incident.xml).
`df.global.world.incidents.all` is the live incident vector (656 at verification).
The existing bounded performer lookup reads up to four participant historical
figures. Missing speakers remain unnamed; no invented audience or quotations.

## Implementation

`references.lua` enriches entity references with name/type/race and
`classification_observed_now`. `event_index.enrich` carries entity details into
story subjects. Profile schema 7 / biography view schema 21 invalidate prior
enrichment on fresh requests; unchanged dormant requests are not regenerated.
Heard-story anchors now include resolved storytellers. The historian explains
organization context and avoids suggesting a visit merely because of a telling.
These prompt boundaries follow [OpenAI instruction/context guidance](https://developers.openai.com/api/docs/guides/prompt-engineering#message-roles-and-instruction-following).

`culture_index.lua` scans incidents incrementally from the annual monitor, at most
128 records with a 2 ms target per batch. No names or model work during scans.
Retain only the active site/current and previous year, at most 256 each. Deduplicate
by incident ID. At chapter export, select the latest four tellings and resolve one
per frame using the existing shared 256-reference budget. The 16 historical events
remain separate; the request stays capped at 128 KiB. There is no guarantee that
every cultural event survives the retention/selection limits.

Optional `cultural_events` extends the annual request without breaking old requests.
Python filters by explicit incident namespace, site, telling year/time, performance
type, and duplicate ID. Topic chronology is checked independently. Selected named
office/organization subjects receive teller-framed required coverage sentences.
Missing coverage fails visibly instead of silently dropping the cultural section.
Cultural-only chapters can generate. Finished annual chapters remain immutable;
only a fresh year-so-far draft includes newly added support immediately.

## Verification and restart

- 115 Python tests passed (two opt-in integrations skipped); 88 live DFHack tests
  passed. New tests cover deduplication, wrong site/year, future/poem references,
  namespace collisions, unknown tellers, teller anchors, and cultural-only output.
- Live culture scan: 656/656, zero errors. Four selected tellings resolved all
  storytellers: Othdo Adeaspa, Ilral Idumåm, Eral Vabôkulåb, Zuglar Ishëmnish.
- Live enriched Brow profile: 94,535 bytes, below 128 KiB.
- Existing watcher restarted and annual timer reloaded while preserving its branch.
  A real year-so-far draft was requested for end-to-end checking.
- The first live draft omitted incident 652 and failed coverage; prior prose was
  preserved. After strengthening explicit per-anchor checking, one deliberate
  retry passed in 17.35 s with incident IDs 625, 646, 648, 652 and all four named
  tellers. The result explains the two organization types and retains topic years
  separately. Its style still has technical commentary and needs player review;
  coverage validation is not a proof of every narrative claim.
- The actual `lorekeeper/chronicles` reader opened the ready draft and exposed
  all four cultural event IDs and named-storyteller prose successfully.
- Player visual acceptance and natural annual rollover remain pending. No commit
  or push as part of this change.

No DF restart expected. Reopen Read biography for updated references. Open
`lorekeeper/chronicles` and use D (Year so far) to request a current draft; it updates
asynchronously even while the game is paused. If modules remain cached, restart DF
as fallback. No init/config edits or scheduled-task registration were performed.
