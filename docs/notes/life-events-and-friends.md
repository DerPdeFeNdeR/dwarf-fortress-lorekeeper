# On-demand life events and friends — 2026-09-06

## Scope

The user requested event-led biographies instead of lists of likes/dislikes, and
explicitly added friends. Capture remains on demand; no collector changes, global
history scans, or recursive friendship graph traversal were introduced.

Profile schema 3 enriches already resolved historical figures with born_year,
born_seconds (exported as born_tick), died_year, and died_seconds (died_tick).
Incident references include the installed death_type token. Friendship capture
reads hf.info.relationships.hf_visual, at most 128 contacts and 32 friends, sharing
the existing 160-reference budget. Missing/truncated containers remain explicit.

The primary [DFHack structure definition](https://github.com/DFHack/df-structures/blob/master/df.history_figure.xml)
documents core.love: 50–74 friend, 75–99 close friend, 100 kindred spirit. These
are directional observations, not proof of mutual bonds, when friendship began,
or shared adventures. Capture excludes acquaintances. Other relationship
containers/identity aliases are not resolved by this implementation.

The Python worker derives at most 24 evidence-linked life events and chooses a
focus from supported losses, witnessed deaths, or child births. Multiple memories
of one incident deduplicate. Related-figure death and incident references merge
by historical figure; separate animal incidents without a figure remain separate.
Dates in the future relative to capture are excluded. Unknown dates stay unknown.
The model payload is schema 13; only new requests regenerate, not dormant views.

These events are derived from the current profile and may precede recorded
snapshots. They do not resurrect observations from an abandoned timeline segment.
No marriage date, other parent, birth attendance, emotional reaction, or awareness
of a relative/friend's death is inferred. Body sightings are not witnessed deaths.
Raw profiles retain evidence; the player-facing story does not show technical IDs.

## Live evidence

- Verified historical-figure date fields on the known family figures. For example,
  HF 11527 has birth year 98 and death year 101; this is not proof Minkot knew of
  the death or that any particular thought concerns it.
- Incident 141's death_type is THIRST; its known victim remains Dattle Brown,
  distinct from family members and friends.
- Selected unit 3637 had four friends; Minkot (6745) had seven. Examples include
  Doren and Sodel as close friends from Minkot's viewpoint. Player comparison
  against the vanilla Relationships tab remains desirable.
- Capture samples: 5 ms / 87,387 bytes (3637), 3 ms / 63,538 bytes (6745).
  These are single CPU-time samples, not a worst-case FPS guarantee.
- Restarted watcher and exercised the real selected-dwarf reader. Initial output
  still used a generic portrait, so added an explicit deterministic narrative
  focus and opening instruction. Revised output opens with Erush's birth in 101.
- Revised run: 52,734 input bytes, 0.56 s preparation, 12.47 s generation,
  16.46 s total. It still lists too many names and drifts into summary prose;
  this is not an unconditional narrative-quality pass. Further stylistic review
  should follow user feedback rather than assuming the prompt enforces every rule.

## Tests and handoff

55 DFHack tests include friendship thresholds, contact bounds, and direction.
51 Python tests passed. Coverage includes birth/death dates, unknown/future dates, friend deaths,
acquaintance exclusion, incident deduplication and merging, factual involvement,
event limits, focus selection, and model payload/cache participation.

No game restart should be necessary; the watcher was restarted by the agent.
With a dwarf selected, open Read biography or run `lorekeeper/read`, then press U
if already open. Wait for automatic completion; no need to unpause or start the
collector just to test existing history. `lorekeeper/profile` now prints friend
names and directional labels. Compare those with the vanilla relationship tab.
Try Minkot and a second dwarf; check that named events improve individuality and
that neither a current bond nor a remembered feeling is presented as a new event.
The user subsequently authorized committing/pushing the combined biography
batch on 2026-09-06; see biography-event-coverage.md for final validation.
