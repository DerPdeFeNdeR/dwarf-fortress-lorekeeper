# Named stories heard in performances

Date: 2026-09-06. Profile schema 6; memoire schema 18.

## Verified mapping

Read-only live inspection confirmed that WatchPerform.subthought points to an
incident. Guard `incident_type.Performance` before accessing `data.Performance`.
The active performance discriminator is `performance_event`, not `type`.
For `STORYTELLING_EVENT`, `reference_id` identifies the historical event being
told about. Poetry, music and dance use different reference namespaces; an ID
alone is never enough. Written-content storytelling references remain unsupported.

The reported election story resolved to an ADD_HF_ENTITY_LINK event in year 83,
with POSITION link type, a named elf, organization, and the office title sacred
brand. Its listening incident dates to year 102. The title comes from matching
the definition ID in that entity's positions, not an arbitrary vector index.
The position definition is observed now; the factual anchor conservatively says
"taking the office". Current/former assignments did not safely establish the
historical election location, so no location or season is invented.

Primary structure reference: [DFHack incident definitions](https://github.com/DFHack/df-structures/blob/master/df.incident.xml).

## Boundaries and persistence

- Lua `storytelling.lua` follows at most 8 story incidents and 4 performers per
  incident, inside the shared 160-reference/depth-2 profile budget. Position
  definition lookup visits at most 128 entries. Historical event lookup uses the
  typed `find`, not a full world scan. Unsupported subjects retain explicit status.
- Performance and historical-subject timestamps remain separate. Story participants
  are not promoted into the listener's historical episodes, family, or friends.
  Translated story-subject names use a separate `story_figure` namespace.
- Enrichment is on demand when a profile is requested, not added to the periodic
  collector. Captured structured data persists in profile/model-memory files.
  This does not promise preservation of every performance before the game forgets it.
- Python selects at most 8 named subjects, deduplicated by historical event ID.
  One resolved office story receives a required listener-framed factual sentence.
  This ensures a concrete subject isn't replaced entirely by generic performance
  enjoyment. Other consequential personal-event coverage remains required too.
- A new subject qualifies for significance, including an older experience newly
  resolved (revision rather than a falsely new occurrence). Repeated tellings and
  memory slots are deduplicated. The memoire sidecar retains up to 256 processed
  subject IDs across compatible revisions; at capacity, new subjects alone stop
  triggering generation rather than evicting IDs and creating replay loops.
- Existing source corrections still permit a safe rebuild. The subject ledger
  resets across incompatible history. Source/model payload changes invalidate
  legacy prepared memoires only when requested again, not fortress-wide.

The OpenAI Docs skill informed explicit separation of narrative instructions from
the supplied subject context; see [instruction following](https://developers.openai.com/api/docs/guides/prompt-engineering#message-roles-and-instruction-following).
No model or authentication configuration changed. Hearing a tale does not establish
political allegiance, knowing its characters, or attending the narrated event.
No invented story quotations are requested.

## Verification and handoff

- 98 Python tests passed (one opt-in model test skipped in the ordinary suite).
- 80 real DFHack tests passed, including union guards, typed subject lookup,
  unsupported written references, and office-definition matching.
- Full on-demand profile capture measured approximately 20 ms in the current save,
  reaching the shared 160-reference cap and resolving five story subjects. This
  is a sample, not a hard timing guarantee; unresolved budget-limited references
  remain explicit rather than guessed. No save clock was changed.
- The actual reader-to-watcher-to-model path completed successfully for the selected
  dwarf: 22.70 seconds model generation, 0.62 seconds preparation, 26.89 seconds
  total including queue wait. The generated memoire included the named office
  tale with an explicit listening frame; its required factual anchor passed.
  Generated prose remains subject to player review (including stylistic polish).
- Reopening the same live memoire reported `reuse / unchanged_evidence`, a cache
  hit with zero generation seconds and one occurrence of the named subject. No
  duplicate passage was added.
- Player verification of the regenerated memoire remains pending. Select the
  same dwarf and use Read memoire / `lorekeeper/read`. The named office story
  should appear as something heard, with year 83 attached to the narrated event.
  The historical location should not be fabricated. Repeated openings should
  not add repeated paragraphs about the same tale.

No game restart is expected; rerun the reader. The background watcher must restart
for Python changes. If DFHack retains an old module despite rerunning, restart DF
as a fallback. Do not commit or push until the user approves the game-facing result.
