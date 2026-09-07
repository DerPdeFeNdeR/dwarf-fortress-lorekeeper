# Lorekeeper roadmap

Updated for published playtest checkpoint **8dd7a66** (2026-09-06).
This replaces the original summary-window/API-prototype milestone plan; historical
implementation evidence remains in Git and [dated notes](docs/notes/README.md).

## Product goal

Make the people and history of a Dwarf Fortress world readable as engaging,
character-driven stories without leaving the game. First-person monthly Memoires
use the subject's voice and personal knowledge; annual Fortress Chronicles use a
saved dwarf narrator and bounded local historical evidence. Keep vanilla UI and
simulation intact, preserve source data, and run model work outside DFHack.

## Implemented

- Steam DFHack integration, raw inspectors, local glossary and regression tests.
- Batched citizen snapshots and append-only history; on-demand rich profiles.
- Bounded event, relationship, incident, storyteller and object-reference resolution.
- Player-facing Memoire and Chronicle windows/overlays, separate debug timelines.
- First-person narration shaped by personality/values and supported mental attributes.
- Monthly introduction/chapters, significance filtering, cache reuse and prior prose.
- Annual draft/observed-rollover workflow with fixed per-year narrator and immutable
  completed chapters; selected event coverage and one bounded correction pass.
- Shared sampled atmosphere and calendar context; personal-knowledge safeguards.
- WSL save-directory watcher, explicit Windows-logon installer and DFHack collection
  autostart. No model request or heavy history parsing in the reader callback.

## Current priority: developer playtesting

The user authorized publication and is playing to report bugs and desired changes.
Documentation must distinguish implemented features from verified behavior.

1. Record performance, narrative-quality and coverage issues with reproduction steps.
2. Verify natural annual rollover and extended monthly growth on live saves.
3. Exercise different fortresses, versions, mixed-biome environments and weather changes.
4. Verify fresh Windows setup using the [README](README.md), including post-logon
   watcher startup. Existing-machine validation is not a clean-machine install test.
5. Add regression coverage for confirmed bugs before further expansion.

## Future work—not promises or current installation requirements

- A packaged installation experience and starting/signaling the external worker
  with DFHack/game startup rather than a separate Windows logon task.
- Broader supported event/reference coverage, with explicit accuracy/performance limits.
- Verified moon phases if a reliable DF interface/calculation is established.
- Storage/retention improvements if measured growth warrants them. SQLite and an
  external web viewer are not implemented and are not prerequisites.

## Delivery rules

Test offline policies and a bounded real integration path where available; use
in-game verification for visual/behavioral changes. Preserve unrelated work and
private saves. Update durable documentation before publication, report restart
requirements, and commit/push only when authorized. Do not infer permission for new
features from a playtest handoff.
