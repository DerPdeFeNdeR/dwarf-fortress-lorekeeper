# The Lorekeeper project context

## Current handoff

- Read `HANDOFF.md` when starting the next session. On 2026-09-06 the user requested
  first-person monthly memoires and personality-shaped annual dwarf narrators.
  This narration batch is implemented but not committed; player acceptance is pending.
  Natural annual rollover and extended monthly growth remain unverified in play.

## User baseline

- The target game is the Steam version of Dwarf Fortress.
- DFHack is already installed and working in the user's game setup.
- The project should translate/explain in-game information, especially dwarf thoughts, personality, and related mental-state data.
- The project should also provide a history UI for reviewing changes and notable events over time.
- Memoires are first-person accounts in the subject dwarf's voice, shaped by
  supplied personality, values, interests, and relationships, not selectable voices.
  This replaces the earlier single external historian design. Annual chronicles
  use a randomly chosen living adult dwarf citizen, weighted toward involvement
  in retained local events that year. Save the choice and voice snapshot per
  save/site/year before generation; drafts, retries, and reloads cannot reroll it.
  Voice affects delivery, not evidence. Never infer personality from occupation or
  turn traits into caricatures or facts about fortress conditions. Narrators may
  recount others' deeds in fortress chronicles but cannot claim eyewitness attendance or invented sources.
  Heard stories retain their teller and listening framing, never firsthand history.
  Tone follows the events: lively and warm for joys or absurdities,
  restrained and compassionate for grief and hardship. Plausible internal motives
  and interpretations may be imagined from known character context and signaled
  as interpretation. Never invent events, dialogue, people, relationships, or
  outcomes. Display "Based on game events, with imagined motives and interpretation."
  outside the story. Use only the latest segment for the main memoire; retain
  earlier segments in the technical timeline. Technical gaps and resets belong
  outside the narrative; do not make them events in the dwarf's life.
- Narrator mental attributes (linguistic ability, analytical ability, creativity,
  memory) also shape literary delivery. Capture only those four effective values
  and caste medians; lower/typical/higher voice bands are editorial, not diagnoses
  or DF description tiers. Missing attributes stay unknown. Never make lower
  scores produce broken grammar, mockery, invented forgetting, or factual errors.
  New profiles include these on demand; saved annual voices gain them once for
  the same verified HF identity, without rerolling or replacing existing traits.
  Older annual voice enrichment uses a separate `.narrator.mental.json` companion;
  Windows Lua rename cannot replace an existing file. Keep the original choice
  immutable and validate the companion's site/year/HF before reuse.
- Primary UX requirement: when the player navigates to/selects a dwarf in Dwarf Fortress, the tool should open a dedicated DFHack UI window showing a readable summary of that dwarf's thoughts, personality, and related mental state. Keep the vanilla screen intact. In-place replacement of vanilla text is a possible later experiment, not the initial target.
- Individual Memoires must stay within personal knowledge: own supported actions,
  thoughts/memories, witnessed events and explicitly heard tales. A family/friend
  link alone does not establish knowledge of their life events. Filter model input
  with `helper/memoire_knowledge.py`; retain raw profiles for technical diagnostics.
  Do not fabricate rumors or conversations to bridge missing knowledge. Annual
  chronicles retain their broader historical scope. Schema 24 and monthly-book
  version 2 prevent old omniscient prose from seeding new passages.
- Use **Memoire** (the user's spelling) throughout the product. The canonical
  command is `lorekeeper/memoire`; `lorekeeper/read` remains compatible. Keep
  existing storage/protocol identifiers and `lorekeeper/overlay.biography` stable
  so renaming never loses data or saved overlay settings.
- The player-facing reader is `lorekeeper/memoire`, separate
  from the technical `lorekeeper/history/show` view. Prioritize readable prose,
  a secondary interpretation notice, simple update/details/close controls, and
  automatic completion while keeping an older story readable. Build the reader
  before adding a selected-dwarf-screen entry button. Do not expose ticks, raw
  traits, or event counts by default in the player-facing reader.
  U explicitly requests updated preparation; D toggles technical details without
  requesting work, and N/P page those details. In story mode N/P browse monthly
  chapters: introduction first, then current/latest recorded month and older
  months newest-first (year/month headings). Every opening starts on introduction;
  background refresh preserves an explicitly selected month. I returns to introduction.
  Escape closes the reader. Opening
  captures the selected dwarf once; automatic polling does not recapture. The
  player must close/select another dwarf/reopen to switch subjects for now.
  The user approved the reader in-game on 2026-09-06; see
  `docs/notes/biography-reader.md` for checks and remaining coverage limits.
  The vanilla-screen entry is `lorekeeper/overlay.biography`: a movable panel
  visible on fortress-mode unit sheets, with a clickable Read memoire label
  and Ctrl+L shortcut. It defaults on when discovered by the overlay framework;
  honor saved enable/position preferences. No idle collection, file polling, or
  model work belongs in this overlay. It rechecks the active unit at activation.
  Shortcut integration passed and the user confirmed the button works in-game.
- The user accepted Luna with low reasoning and its roughly 11-second measured
  generation time for now. Automatic in-game updates without R were verified.
  Further model comparisons, no-reasoning trials, and speculative memoire
  pre-generation are deferred; do not silently enable them.

## Working assumptions

- Atmosphere is optional. The chronicle monitor samples central-cell weather
  every 120 game ticks, logging changes/daily checkpoints in shared branch/year
  `lorekeeper-environment` files. Cache one site-anchor biome/region; no map scans
  or per-dwarf periodic atmosphere capture. Python reads bounded committed prefixes.
  Never apply current weather to old events. Personal Memoire inputs exclude
  shared weather; firsthand experiences need personal thoughts/memories. Moon
  phases stay unavailable until verified. Weather alone cannot create chapters.
  See `docs/notes/observed-atmosphere.md`.
- Annual coverage failures permit one bounded sentence-index correction per
  request, persisted before the model call. Recheck every fact, preserve prior
  good prose on failure, retain candidate/response diagnostics, and never silently
  loop or weaken coverage. See `docs/notes/chronicle-correction.md`.

- Treat DFHack as the integration boundary. Prefer DFHack Lua scripts and APIs before considering a compiled DFHack plugin.
- Keep game-facing collection separate from translation and presentation. The collector should emit stable, structured records rather than UI-ready prose.
- Do not overwrite or modify the user's DFHack installation from this repository unless explicitly requested. During development, use a documented copy/symlink/install step.
- Account for DF/DFHack updates: keep a small compatibility layer and record the game/DFHack version with collected data.
- Avoid storing only dwarf IDs. IDs can be useful within a world, but names, race, site/world identity, and timestamps should also be retained where available.
- Translation should be asynchronous and cached. Never block the DF render loop on a network/model request, and never put an API key in the DFHack Lua script. The optional HTTP API prototype defaults to `gpt-5-mini`; the active Codex watcher explicitly defaults to `gpt-5.6-luna` with low reasoning.
- Keep the worker's model and effort independent of interactive Codex defaults.
  `LOREKEEPER_MODEL` and `LOREKEEPER_REASONING_EFFORT` configure its invocation;
  never change the user's personal Codex config for Lorekeeper. Memoire cache
  keys include both settings and the historian prompt. Save requested generation settings separately from
  the provenance of the displayed story; failed replacements keep old prose.
  Reopening requests a new model version, not a bulk regeneration of dormant
  biographies. See `docs/notes/luna-biography-validation.md` for validation.
- The user-facing translation workflow must not require leaving Dwarf Fortress or
  manually processing a queue. The current `helper/process_queue.py` command is
  a development bridge only. The intended product workflow is a background
  local watcher that notices queued jobs, invokes the authenticated model
  client outside DFHack, writes the cache, and lets the in-game UI show pending
  or ready status.
- Translation caches must preserve Unicode names and prose. Write JSON with
  Unicode escapes when necessary to remain ASCII-safe for DFHack; never
  transliterate user-visible dwarf names as a workaround.
- History currently uses the append-only `lorekeeper-history.jsonl` file plus a
  fortress-wide sidecar index under `lorekeeper-history-index/`. The first
  history lookup builds that index in one pass; later dwarf lookups use the
  per-dwarf cache. New records update an existing index and create caches for
  new dwarves once they are recorded. Starting the collector prewarms the
  index during its existing history scan; `lorekeeper/autostart` can start the
  collector automatically on world load when enabled in `dfhack.init`.
- `lorekeeper/history` preserves raw records while presenting a grouped event
  timeline: baseline, coalesced stress trends, and discrete thought,
  profession, or personality changes.
- `lorekeeper/history/show` is the dedicated in-game history view. It displays
  the cached story above the grouped timeline and supports scrolling, refresh,
  copying, and closing without replacing the vanilla screen.
- The history view normalizes known CP437-mojibake dwarf names in cached story
  prose before rendering, while retaining the original cache text for audit.
- Opening the history view requests preparation for the selected dwarf. R reads
  prepared results without requesting new work; reopening requests newer history.
  The open window also polls bounded prepared status once per wall-clock second,
  including while DF is paused; unchanged status must not rebuild the display.
  Keep a previous memoire visible, or immediately show a small explicitly
  factual overview when none exists. The player may close the window and play
  while generation continues outside DFHack.
  Legacy schema-18 memoires use a Python-only `.biography-memory.json` sidecar for
  conservative incremental continuation. Unchanged evidence reuses prose; compatible
  new events append with prior prose explicitly labeled interpretation and separate
  verified context. Reference corrections, old-event discovery, time reversal,
  stable-context changes, or length limits rebuild instead. Never advance the
  checkpoint after a failed update or feed invented motives back as verified facts.
  New reader requests use schema 25 / monthly protocol 1: a short introduction
  and recollections plus significant monthly chapters. Reopening checks evidence
  on demand; it does not write a passage merely because another month passed.
  Each month is exactly one narrative paragraph; the introduction may have 1-3.
  Prompt for a single coherent passage and normalize monthly whitespace before
  coverage validation/publication, preserving Unicode and facts. Prepare introduction
  before months. Update the existing month's passage rather than append another portrait.
  Preserve completed months except important newly discovered evidence, corrections,
  or an explicitly requested writer-version update. Date heard stories by listening
  time, never their historical subject's date. Unknown dates/baseline memories go
  in recollections; snapshot timestamps date observations, not original events.
  Python keeps a per-dwarf monthly manifest and immutable chapter revision files.
  Time reversal/incompatible history archives the old manifest without merging
  branches. One chapter per watcher pass; no model calls or log scans in the reader.
  The catalog exposes the newest 99 monthly chapters plus introduction, retaining
  older files on disk. See `docs/notes/monthly-biographies.md` for limits and tests.
  The significance filter defers routine changes without a model call or advancing
  the written-evidence checkpoint. Minor additions accumulate (8 occurrences,
  3 types, 3 observation times); consequential events bypass that threshold.
  Reference corrections and branch changes still require safe revision. Treat
  thresholds as editorial tuning, not game/medical classifications. See the note
  below for personality/stress thresholds and exact suppression rules.
  See `docs/notes/incremental-biographies.md`; automated and live model testing
  passed. On 2026-09-06 the user explicitly approved commit/push before extended
  in-game verification and will play to collect feedback. Treat this as a playtest
  checkpoint, not completed player acceptance; review feedback before new features.
  It reports processing/ready/failed status and labels preparation time and older
  story revisions; it must not present a prepared view as live game state.
- The reliability batch replaces the heavy queue payload with small
  files under `lorekeeper-views`. Python prepares timeline pages and model input;
  the window must never parse history logs or construct model payloads.
  The user verified responsive opening/refresh, story completion, and N/P
  timeline pagination on 2026-09-06. Older completed stories remain readable
  with their preparation time and explicit revision labeling.
- On-demand memoire profiles are separate bounded `.profile.json` files
  referenced by small view requests. Never add this capture to the periodic
  collector. Capture is capped per section (64 entries, 128 emotions), with a
  128 KiB file limit; unsupported/truncated data must be reported. R does not
  recapture; reopening does. Compact semantic profile content participates in
  schema-v23 story caching, excluding capture/recall time and emotional strength.
  Full profiles remain separate from the compact model input. The user verified initial profile
  capture and all 33 then-current Lua tests; see memoire audit notes.
- Resolve Death/UnexpectedDeath references as historical figures only; do not
  treat witnessed-death/body references as figure IDs. The user verified Minkot's
  reference 7068 resolves to Momuz Lilumuzol and her link is
  `histfig_hf_link_spousest`. Do not generalize this to her other death thoughts.
- Object references use the shared typed resolver, never untyped ID guessing.
  WitnessDeath/SawDeadBody resolve through incidents and their victims. Live
  incident 141 identifies victim unit 8421 / HF 12569, `Dattle Brown` Obokkudust,
  not Momuz. Resolve verified kinds only; preserve unsupported, missing, invalid,
  error, and budget-exhausted status. Cache only within one capture so mutable
  names and save/world changes cannot reuse stale objects. Limit 160 references
  and link depth 2. Profile schema 9 / story schema 23 use typed references
  and unique full-name accent restoration; never guess among ambiguous matches.
- WatchPerform references are performance incidents, not historical events directly.
  Only Performance / STORYTELLING_EVENT with a valid reference_id and no written
  content reference resolves a story subject. Poem/music/dance IDs must never be
  treated as historical events. `storytelling.lua` enriches at most 8 incidents
  on demand, within the shared 160-reference budget; no periodic enrichment.
- Keep `heard_stories` separate from personal historical episodes. Preserve listening
  date, narrated-event date, reaction, typed participants, and resolved office/entity
  names. Hearing about an election does not make the listener a participant or
  supporter. Current office assignments do not establish historical event location.
  A subject ledger prevents re-tellings from repeatedly triggering memoire
  generation (legacy 256 IDs; monthly book limit 2,000). See
  `docs/notes/heard-stories.md`; the user approved the current result for playtesting.
- Include resolved performance participants as storytellers, never as the people
  whose historical deeds they recount. Enrich organizations with their current
  entity type and race; unknown fields remain unknown. Names such as The Letter
  of Safety can name civilizations, not documents. A story told locally does not
  prove the organization visited. See `docs/notes/cultural-chronicles.md`.
- On-demand profiles include directional friends from `hf.info.relationships.hf_visual`
  using documented `core.love` thresholds (50 friend, 75 close friend, 100 kindred
  spirit). Examine at most 128 contacts, retain at most 32 friends, and report
  truncation. Do not equate acquaintances with friends or claim mutual friendship.
  Historical-figure references retain verified born/died year and tick fields.
  Python derives at most 24 life events from these references and death incidents,
  including child births and deaths of linked family/friends. Dates are event
  dates, not memory recall dates; current bonds do not prove historical bonds or
  awareness/grief. Do not infer marriages, other parents, or friendship formation.
  Choose a supported narrative focus, with a portrait fallback for sparse data.
  Never add this profile work to the periodic collector or synchronously scan world history.
  See `docs/notes/life-events-and-friends.md` for evidence and remaining review.
- `lorekeeper/event_index` incrementally indexes supported world-history event
  types in a separate session-local task, started by autostart or first capture.
  Each batch visits at most 128 records with a 2 ms CPU-time target, yielding
  between batches even while paused. It retains at most 50,000 participant links,
  32 events per figure, and 32 members per participant group. Profile capture copies
  at most 8 matching events with 8 named participants each; it never scans the log.
  Unload, time reversal, or vector shrink resets the index. New records are polled.
  No persistent index/config changes are required; current names resolve on demand.
  Supported events: explicit battle groups, site attackers, deaths, wounds,
  artifact creation/naming, abduction/release/enslavement/ransom, reunions,
  travel, profession/whereabouts changes, personal/organizational link changes,
  moods, and masterwork items. A fixed-size link ring evicts old links when full
  rather than refusing newer evidence. Per-figure retention favors milestones
  over routine travel; selection favors kind diversity within the same 8-event cap.
  Coverage remains partial. Do not infer immigration from travel, appointment
  from membership, or divorce/death from removed links. Unresolved position IDs
  remain unnamed; a current profession is not evidence of the historical title.
  Never infer participation from fortress residence,
  victory from group membership, murder intent from slayer attribution, or
  a strange mood from artifact creation. Retain event IDs, roles, and coverage.
  Profiles captured during indexing stay partial until Update/reopen; disclose
  this outside the prose. See `docs/notes/historical-event-index.md`.
- Keep writing-process commentary out of the narrator's prose, including claims
  about what is not invented. Show a blank line between memoire and timeline.
  Seeing a body is not witnessing its death, and ANYTHING supplies no specific
  emotion. Missing cups/wells do not establish poor drink quality. Preserve these
  distinctions explicitly when evaluating faster memoire models.
- Legacy full memoires are not limited to two paragraphs. Target 4–6 developed paragraphs
  (about 350–550 words) for substantial evidence, 1–3 shorter paragraphs for sparse
  histories. Current monthly chapters override this: one paragraph per month,
  with 1–3 short introductory paragraphs. Required factual anchors for resolvable selected historical deaths,
  wounds, captivity/release, and artifact creation outrank brevity/thematic choice.
  The worker checks these sentences before publishing or reusing a story, records
  checked event IDs, and visibly fails while preserving old prose on omission.
  Coverage failures do not auto-retry. This is a bounded omission guard, not a
  proof of all prose claims or completeness of the game history. Never infer
  murder, intent, remorse, or a victim's age from slayer attribution alone.
  See `docs/notes/biography-event-coverage.md`.
- In this installation, name lookup uses `dfhack.translation.translateName`,
  not `dfhack.TranslateName`. Inline multiword Lua commands need the `:lua` form.
- Split story paragraph breaks before UTF-8-to-DF conversion; preserve blank
  lines and convert each display line once. The user verified the formatting
  fix and all 30 DFHack tests on 2026-09-06.
- Display-safe punctuation replacements must preserve accented names and leave
  cached Unicode untouched. On 2026-09-06 the user verified the v7 historian
  narrative, its separate interpretation notice, and all 31 DFHack tests.
- History story requests use a versioned compact payload with exact thought
  additions/removals, profession transitions, and personality facet changes.
  Change the request/schema version when the payload contract changes so stale
  cached stories are not reused.
- Story caching is separate from exact timeline revision caching. Preserve named
  references, relationships, values, preferences, personality changes, and counted
  thought additions/removals. Quantize stress and need focus as floor(value/1000)
  for compact story input; these bands are not diagnostic categories. Keep exact
  values and timestamps in the raw history/profile. Publish all discovered
  timelines in a save before sequential model work, prioritizing newest requests.
  Do not regenerate dormant completed requests merely on schema deployment;
  reopening requests an updated version. Save queue/preparation/model-queue/
  generation/total timings and payload size for diagnosis. See
  `docs/notes/biography-responsiveness.md` for measured results and limitations.
- The Python history view preserves append order. A backward (year, tick)
  transition starts a `timeline_reset` segment with a fresh snapshot baseline;
  never infer normal changes across that boundary or sort the records to hide it.
  History-view schema changes invalidate older prepared stories. A reset indicates
  recorded time reversal, not proof of a save reload. On 2026-09-06 the user
  verified Minkot's regenerated two-segment story and the final page's explicit
  reset/fresh-baseline label in-game.
- The local `helper/watch_queue.py` watcher is the hands-off development
  workflow: it monitors the active save queue, invokes Codex outside DFHack,
  and updates the cache while the player remains in-game. A future installer
  or launcher should start the save-directory watcher automatically. Prefer
  `helper/watch_save_directory.py` for startup because it follows all regions
  beneath the Dwarf Fortress save directory.
- `helper/start_watcher.sh` is the portable startup wrapper. It resolves the
  repository path and launches the save-directory watcher; Windows Task
  Scheduler registration remains an explicit user setup step.
- `helper/install_watcher_task.ps1` provides that explicit Windows Task
  Scheduler registration. It must be run by the user and accepts project/save
  path overrides; never register tasks automatically from repository actions.
- `dfhack/scripts/lorekeeper/autostart.lua` provides the explicit DFHack-side
  collector startup hook. It is enabled by adding `lorekeeper/autostart` to
  `dfhack.init`; repository actions must never edit the user's DFHack config.
- User preference: when the product is ready for broader use, prefer starting
  the translation watcher with DFHack/Dwarf Fortress startup rather than
  requiring a separate Windows login task. Keep model execution outside DFHack
  so the game loop and credentials remain isolated.
- Verified current Steam setup: the DFHack startup file is
  `C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\dfhack-config\init\dfhack.init`.
  Documentation must include the `init` subdirectory when instructing users
  to enable `lorekeeper/autostart`.

## Coding and review standard

### Annual fortress chronicles

- Request schema 2 includes a saved narrator; schema 1 remains readable. The Lua
  narrator selector visits at most 32 active units per frame with a 2 ms target,
  captures only 23 voice facets and up to 32 explicit values for the chosen dwarf,
  and never invokes full memoire profiles or scans world history. Weight is
  1 + min(unique retained local-year events, 8). Saved voice files are capped at
  32 KiB. No eligible citizen uses an explicitly labeled external chronicler;
  invalid saved choices fail rather than silently selecting someone else.
  Published story attribution is separate from a requested narrator, so failed
  updates do not misattribute old prose. Completed annual chapters stay immutable.
  See `docs/decisions/0007-dwarf-narrators.md` and `docs/notes/dwarf-narrators.md`.
- Event narratives include supported causes/methods beside the event. The
  on-demand `event_method.lua` resolves one exact indexed historical event and
  at most two recorded weapon descriptions; never scan combat reports, units,
  or world history for a method. Preserve projectile versus launcher roles.
  Resolve wound injury type/body part/loss when supported. Generic STRUCK_DOWN,
  MURDER, absent or unknown codes do not imply a weapon, attack or motive.
  Method details participate in model input and coverage; personal knowledge
  filtering still removes hidden incident details from Memoires. See
  `docs/notes/event-methods.md` for verified fields and limits.
- Annual prose mentions its year at most once near the opening. Deterministic
  local-event examples use month names from valid event ticks (33,600 per month);
  unknown months stay unspecified. Keep earlier years in a tale's historical
  subject distinct from the local performance month. Shared calendar code supplies
  both monthly memoires and annual labels; never ask the model to guess dates.
  Establish a month once for nearby events instead of repeating it at each
  sentence/paragraph opening; a later reflective mention is fine. Explain supplied
  organization/subject context at first mention, not in a detached list later.
  Annual coverage uses bounded ordered factual clauses within one sentence;
  connective language and shared month context are flexible, but roles, tellers,
  subjects and topic years remain checked. This is a structural omission guard,
  not a semantic truth proof. Memoire coverage keeps its existing contract.
  Do not add a second model call or rewrite pass for style. Completed chronicles
  remain immutable; D requests a new current-year draft. See
  `docs/notes/chronicle-prose.md`.
  Preserve the latest coverage-rejected candidate separately as
  `<chapter-key>.rejected.json`, with missing IDs, requirements, request/prompt
  digests and generation settings. Never publish that candidate or replace the
  last good story with it. Keep one diagnostic file per chapter, no automatic
  coverage retries, and use the Chronicle label for annual validation errors.
  A coverage mismatch does not prove a fact was omitted: inspect rejected prose
  before changing requirements. Tests must reject wrong roles, dates and negation
  while allowing supported appointment wording and small spelled-out years.
- `lorekeeper/chronicle` is the bounded annual monitor, started by the existing
  `lorekeeper/autostart` hook. `lorekeeper/chronicles` is its separate reader and
  the fortress overlay button opens it without requiring a selected dwarf.
- Queue a finished year only after observing calendar rollover. Generate through
  the external save watcher, never from the game thread. Current-year drafts are
  explicitly requested with D; N/P browse, R retries failures. Published finished
  chapters are immutable; draft updates cannot overwrite them.
- Annual evidence uses explicit site associations in the historical-event index,
  with bounded current/previous-year buckets (256 each), selecting at most 16
  events. Resolve one event per frame, up to 256 reference lookups and 128 KiB
  request files. This is supported, selected evidence, not exhaustive fort history.
- Annual cultural evidence has a separate `culture_index` over performance incidents:
  128 records / 2 ms target per monitor batch, current/previous-year site buckets
  capped at 256 each, latest 4 tellings exported separately from 16 history events.
  Resolve at most one selected event per frame within the existing shared resolver
  and 128 KiB request limits. Deduplicate incident IDs, not listener or historical
  subject IDs. Preserve storyteller, local site/date and narrated subject separately.
  Namespaced required anchors verify selected resolvable tellings before publication.
  Truncation/errors mark incomplete coverage. Old completed annual chapters remain
  immutable; use Year so far for a new draft with enriched evidence.
- Every fortress load and observed backward-time transition starts a new recording
  branch. Preserve earlier files; do not merge incompatible histories or turn gaps
  into fictional events. Coverage warnings and branch labels belong outside prose.
- Files live under the save's `lorekeeper-chronicles/`; the reader reads bounded
  prepared files, never logs. The catalog shows the newest 100 chapters, retaining
  older files on disk. See `docs/notes/annual-chronicles.md` for validation limits.
- 2026-09-06 playtest handoff: the user verified the five separate footer controls
  and overlay placement x=6, y=10, approved publication, and will play normally to
  collect bugs/improvements. Natural year-end generation remains unverified live
  despite automated rollover tests. Review playtest feedback before new features;
  preserve this caveat until an actual year transition has been observed.

Apply Bob Martin's Clean Code principles whenever writing or reviewing code, while using judgment appropriate to this project's Lua and game-integration constraints:

- Prefer clear, intention-revealing names over comments that explain vague code.
- Keep functions and modules small, focused, and responsible for one coherent thing.
- Separate collection, normalization, translation, caching, persistence, and UI concerns.
- Minimize side effects and make dependencies explicit, especially around DFHack state and network calls.
- Avoid duplication, speculative abstractions, clever code, and unnecessary framework complexity.
- Keep interfaces small and stable; hide implementation details behind focused modules.
- Handle errors explicitly and preserve useful diagnostic context.
- Write code that is easy to test; use fixtures for captured DFHack data and tests for translation rules and cache behavior.
- Test changes before committing or pushing them. For in-game behavior, wait for in-game verification when a local automated test cannot reproduce the behavior.
- Before committing or pushing, update the durable knowledge base when the
  implementation, workflow, or verified environment has changed: update
  `AGENTS.md` for lasting agent instructions and add a dated note or ADR for
  evidence and technical decisions. Do not rely on the conversation as the
  only record.
- Test the real integration path before publishing it. A mocked unit test is
  not enough for a CLI, network, DFHack, or game integration: run one bounded
  end-to-end check when credentials and the local environment permit it, and
  document any untested boundary explicitly.
- When handing off a game-facing change, explicitly tell the user whether Dwarf Fortress must be restarted. A restart is required after changing DFHack script-path configuration; otherwise, first try rerunning the command, and recommend a restart if DFHack does not reload a changed or newly added module.
- Refactor toward clarity when touching nearby code, but do not make unrelated rewrites.
- During review, prioritize correctness, readability, maintainability, and regression risk over personal stylistic preference.

## Project memory and documentation

- Treat version-controlled project documentation as the durable source of project memory; do not rely on conversational memory.
- Keep stable user goals, constraints, and working assumptions here in `AGENTS.md`.
- Record significant technical choices in `docs/decisions/` as short Architecture Decision Records (ADRs), including the decision, context, alternatives, and consequences.
- Record verified environment discoveries, compatibility findings, and test procedures in `docs/notes/`.
- Update documentation when a decision changes; do not accumulate contradictory instructions.
- Prefer concise, dated, evidence-based notes. Link to the relevant code, command output, save fixture, or official documentation when practical.
- Do not store secrets, API keys, private save data, or large generated dumps in the repository.

## Recommended first architecture

1. **DFHack collector (Lua):** read selected dwarf data and detect changes on a modest interval or relevant state changes. Start with thoughts, personality facets, current stress/needs, relationships, profession, and location.
2. **Stable data contract:** write newline-delimited JSON or another append-only format with a schema version. Use records such as `dwarf_snapshot`, `thought`, `personality_change`, and `event`; include world/site identity, dwarf ID, in-game time, collection time, and source/version metadata.
3. **Translation layer:** use a local deterministic glossary for known DF/DFHack enums and thought tokens. Use a low-cost, fast model only for unknown or context-sensitive cases, through a local helper service. Cache by raw text/tokens, relevant context, language, prompt/schema version, and model; always preserve the raw value alongside the translation.
4. **History storage:** begin with JSONL files for easy inspection and portability; move to SQLite when querying by dwarf, date, event type, or relationships becomes important.
5. **In-game summary view:** use DFHack GUI/view-screen facilities to detect the currently viewed or selected dwarf and open a dedicated, scrollable summary window. Group translated thoughts by category and severity, then show personality facets, stress/needs, relationships, and a concise overall interpretation. Preserve raw values and an “explain details” view for debugging and unknown translations. Keep the window independent of vanilla screen layout where possible.
6. **History UI:** build a read-only desktop/web viewer for longer-term review. Useful views are a timeline, dwarf detail page, thought/personality breakdown, and filters by severity, category, and date.

## Verified workflow discoveries

- The optional Codex translation backend is a batch worker, not a synchronous
  DFHack dependency. `helper/codex_batch.py` deduplicates requests and sends
  up to 50 items through one `codex exec --ephemeral --sandbox read-only`
  invocation with JSON Schema output.
- On 2026-09-06, `codex login status` reported `Logged in using ChatGPT`, and
  a real two-item batch returned validated structured results. This verifies
  the local Codex CLI path.
- On 2026-09-06, the full selected-dwarf path was verified in-game: a selected
  dwarf was queued with `lorekeeper/translate`, processed with
  `python3 helper/process_queue.py <queue.jsonl>`, and displayed by
  `lorekeeper/show` after refresh. `show` currently presents a current-state
  summary, not a historical story.
- DFHack UI text uses a CP437-oriented display path while Codex returns Unicode.
  Translation caches preserve Unicode using JSON escapes, and the UI converts
  Unicode once to DF display encoding. Do not transliterate names;
  the authoritative snapshot and the Identity section retain the original
  dwarf name and raw values.
- Codex CLI may reuse ChatGPT-managed authentication for local workflows.
  Platform API keys are a separate usage-billed path. Never copy Codex auth
  files or API keys into the repository, DFHack scripts, queue data, or logs.
- Before claiming a Codex backend is game-ready, add and run a DFHack-facing
  queue command and verify that `lorekeeper/show` remains responsive while a
  batch is pending. Report restart requirements explicitly.

## Suggested milestone order

- Verify the installed DFHack version and locate its script path.
- Build a read-only `dump` command for one selected dwarf; validate the raw fields against the game UI.
- Build the smallest in-game summary window for the currently viewed dwarf, starting with translated thoughts and a close/refresh hotkey.
- Add a small polling collector and JSONL export, with fixtures from a real save for repeatable tests.
- Implement glossary-based translation and confidence/unknown handling for fields that are not understood yet.
- Add the local model helper only after the glossary path works; use the backend-specific defaults above and return a temporary fallback while uncached text is being translated.
- Add SQLite indexing and the first timeline/detail UI.
- Add incremental collection, deduplication, privacy/retention controls, and only then consider an in-game overlay.

## Technical references

- DFHack Lua API: https://docs.dfhack.org/en/stable/docs/dev/Lua%20API.html
- DFHack overlay development: https://docs.dfhack.org/en/stable/docs/dev/overlay-dev-guide.html
