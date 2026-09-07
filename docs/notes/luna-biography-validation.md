# Luna memoire trial — 2026-09-06

The user requested `gpt-5.6-luna` after observing working automatic refresh.
The former worker omitted model/effort flags and inherited local
`gpt-6-astra` / `medium`. The new explicit default is Luna / low, overridable
through worker environment variables without modifying personal Codex settings.

Official [Luna documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
confirms low reasoning and structured output support. It describes Luna as
roughly the earlier nano tier; this was disclosed to correct the prior distinction
between Luna and nano. The exact requested Luna model is retained, with the same
historian prompt, JSON schema, authenticated Codex path, sandbox, and timeout.
No API credentials, new billing path, or silent fallback model were introduced.

Memoire cache identity now includes model, reasoning effort, and historian
prompt content. Prepared status
records `generation` for the request and `story_generation` for successfully
generated prose. Old unlabelled stories are not retroactively assigned a model.
New requests regenerate if settings differ; unchanged completed requests remain
dormant. The legacy token queue keeps its existing ID-based retention behavior.

43 Python tests passed, including explicit invocation flags, configuration
validation, returned settings, and model/effort cache invalidation. The first real
Luna run used the existing Udib profile and compact input (43,900 bytes), returned
valid structured output in 11.57 seconds, and required no game-cache modification.
The prior Astra sample took 24.34 seconds. This is a single comparison, not a
controlled latency distribution or a general speed guarantee.

Reviewed output used concrete animal-body references and an explicitly tentative
internal motive. It did not conflate seeing bodies with witnessing death in the
memoire itself. It omitted family detail from the short narrative; the user
still needs to judge narrative quality and preferred emphasis in-game.

The installed watcher was restarted to activate the defaults and a fresh
selected-dwarf history request was submitted for end-to-end verification.
That first watcher run took 11.17 s generation, 0.54 s preparation, and 16.28 s
total including 4.54 s polling/queue delay. However, its prose incorrectly turned
body sightings into witnessed deaths and generalized cup/well complaints into
drink quality. Added narrowly targeted prompt distinctions rather than weakening
the factual contract. Prompt content now participates in cache identity so new
requests do not reuse the incorrect version. Restarted and requested a second
live result for review. This demonstrates why fast completion alone is not a
quality pass, and why user story review remains required.
The corrected live result completed in 11.12 s generation / 14.52 s total and
described seeing bodies, missing cups, and missing well access distinctly. It
preserved concrete names and a locally signaled imagined motive. Broader style
and factual reliability still require more dwarf samples.
No Dwarf Fortress restart is required. Reopen `lorekeeper/history/show`, wait for
the automatically displayed result, and compare both speed and historian voice.

## Checkpoint acceptance

The user confirmed automatic updates without R, said Luna's quality is good
enough, and accepted keeping low reasoning and the current wait for now. They
then authorized committing/pushing this checkpoint before a separate story-first
reader milestone. Final regression checks: 43 Python tests and 42 tests run
through the live DFHack client passed. Earlier broader quality limitations remain;
this acceptance is not evidence that all dwarves or reference types are covered.
