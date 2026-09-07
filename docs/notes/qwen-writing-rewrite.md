# Qwen writing pipeline rewrite — 2026-09-07

The user authorized a rewrite focused on Qwen after the live annual request
returned one sentence and omitted six required events. Work remains uncommitted.

## Design and comparison

`writing_brief.py` compiles dedicated monthly/annual writing instructions from
already filtered inputs. Monthly events remain scoped to chapter evidence;
introductions retain undated profile memories. Monthly context excludes other
months' emotion lists and all old generated prose. Original requests, knowledge
filtering, monthly storage and mandatory coverage remain unchanged. Repeated
records retain lossless table presentation. Personality/mental delivery cues and
explicit value direction are prepared in Python; they do not establish facts.
The small voice guide covers five delivery facets and the four mental attributes,
not every personality dimension. More nuanced voice remains future tuning.

Writing output uses id/text only. The compatibility envelope is supplied in code
with narrative category and low confidence, not model self-certification. Codex
and legacy translation/correction contracts retain their previous behavior.

The ignored captured real Chronicle was compared without publishing candidates:

| Strategy | Calls | Seconds | Input tokens | Coverage |
| --- | ---: | ---: | --- | --- |
| Compact free prose, v5 | 1 | 31.77 | 4,035 | all seven anchors unverified |
| Seasonal free prose, v5 | 3 | 37.99 | 1,516 / 2,246 / 2,028 | all seven unverified |
| Facts plus reflections, v6 | 1 | 4.16 | 772 | seven passed |

The free-prose candidates also invented motives, fortress-wide moods, visits and
other details. Smaller sections did not fix those problems. Section generation
therefore remains an opt-in experiment in `helper/evaluate_writing.py`; there is
no production section cache, extra style pass, or automatic regeneration loop.

`anchored_chronicle.py` instead groups required factual sentences by known month
and assembles them in code. Qwen supplies at most 45 words of optional reflection
per paragraph, in one request. Unknown months remain unspecified. Narrator choice
is unchanged. The original coverage validator still runs after assembly. An
annual request with no mandatory anchors uses the compact prose path.

This is a deliberately narrower annual account: required events are preserved,
but optional selected events and shared atmosphere do not currently get additional
free prose in the anchored path. First-mention organization descriptions and
varied month transitions remain limited. The output can read as a factual sequence
with reflections rather than a fully integrated literary chapter. Do not describe
this as equivalent literary quality to the previous hosted writer.

Review found a generated reflection confusing a killer with a victim despite a
correct fixed factual sentence. The optional-reflection guard now omits explicit
named references and a bounded vocabulary of death-experience descriptions,
recording omitted paragraph IDs in `writing_diagnostics`. It never removes the
factual sentences. This guard can omit harmless reflections and cannot establish
the truth or appropriateness of arbitrary remaining prose. Invalid reflection
shape/length fails the request rather than publishing a partial result.

Generation preset is `qwen3-anchored-v6`; explicit reopening requests a new version.
Finished annual chapters remain immutable. Error diagnostics now hash the actual
compiled Ollama prompt. Context remains 20,480 with q4_0 KV cache/Flash Attention;
verified 5.9 GB and 100% GPU. Input truncation and context shifting stay disabled.

## Reader and validation

D selects the current branch/year draft and tracks its specific request filename
through evidence preparation and worker completion. Retry uses the same tracking.
Older chapter status cannot overwrite the pending request message. Manual chapter
navigation exits that tracking. No model calls or history scans enter the reader.
Live reload testing exposed a cached old monitor callback that could export the
draft without updating the new request handle, leaving the status on Preparing.
Module reload now cancels/rebinds that timer while preserving runtime branch,
narrator, pending jobs and any active capture coroutine. A reader opened before
the fix must be reopened; completed data must not be mistaken for a progress pass.
The final post-rebind live request completed in 3.46s with seven checks passed;
DFHack inspection confirmed Saved chapter, pending cleared, and the same branch.

Actual DFHack activation showed `Preparing the requested draft`, selected the
current branch, and subsequently showed `Saved chapter` with pending cleared.
The native watcher produced that real draft in 3.92 seconds with seven coverage
checks passed. This was a current-year draft update, not a finished chapter edit.
The reflection issue above was found during its prose review and fixed afterward.
Focused pure DFHack progress tests passed. A full Lua suite was not run during play.

Linux regression: 195 run, 188 passed, seven opt-in live tests skipped.
Windows also ran 195 tests: 188 passed and seven optional live tests skipped.
Final post-guard live draft reached ready in 3.61s with seven checks passed and
no reflections omitted. Reader completion cleared pending automatically. An
isolated full monthly preparation pass took 13.72s for the intro, with five months
still pending in that diagnostic book. These do not establish full-book quality.
Final reflections still include awkward/unverified imagery, including a desert
metaphor beside dehydration. This remains a playtest limitation, not proof of a
desert setting or acceptance of every prose claim.
An isolated real Minkot introduction measured 10,462 input tokens and 18.83s,
but still invented occupation routines and species stereotypes; Memoire literary
and factual quality is not accepted merely because required anchors passed.
Raw save records and prior finished books were not modified by evaluation scripts.

Use `helper/evaluate_writing.py CAPTURED_ITEM --output .lorekeeper/NEW_REPORT.json`
for one explicit live comparison. `--sections` partitions an annual input without
losing its assigned events or required facts. Reports contain private prose and
stay ignored. The tool does not publish into save directories; never point its
output at production chapter paths.

The native worker must restart to load Python changes. Close/reopen Chronicles
to load the reader changes; no script-path change or DF restart is required.
No new startup task was registered and no personal Codex settings were changed.
