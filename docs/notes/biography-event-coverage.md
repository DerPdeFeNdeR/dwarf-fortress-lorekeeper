# Biography length and consequential-event coverage — 2026-09-06

The user noticed that Feb's biography omitted his attributed killing of Tirist
despite including an animal death and an artifact. Inspection confirmed the death
event was present in the selected model input. It was a writing omission, not a
collection failure. The old prompt asked for 2–4 short paragraphs, while the
generic batch wrapper independently asked for concise text.

## Changes

- Target 4–6 developed paragraphs / 350–550 words when supported; 1–3 shorter
  paragraphs for sparse history. No minimum padding and the existing 8,000-byte
  display limit remains. The batch wrapper defers to the item's length contract.
- Prioritize deaths, wounds, captivity/release and artifacts above routine links
  and travel in the bounded index. Index version 4 rebuilds session data.
- `story_coverage.py` constructs neutral required sentences for resolvable
  consequential events in the selected (maximum eight) historical episodes.
  The historian must integrate them unchanged into normal prose, not a list or
  quotation. Surrounding prose remains flexible. No child age, intent, criminal
  culpability, remorse, rescue mechanism, or emotional consequence is invented.
- Check actual returned prose after name normalization, not model self-reported
  coverage. Normalize Unicode composition and whitespace, then require the
  factual sentences. Missing coverage prevents publication and preserves old
  prose with a failed status. It does not launch automatic retries. The player
  can explicitly request another update. Cache reuse is checked too.
- Store checked event IDs/method with successful prose; story schema 16 invalidates
  older cached results on new requests, not dormant biographies. No additional
  network call or game-side validation is introduced.

This intentionally trades paraphrase freedom on a few important facts for a
deterministic omission guard. It is not a semantic contradiction detector or
an audit of every surrounding claim. Unknown names and index/input caps still
limit coverage; it must not be presented as a complete biography of all events.
The OpenAI Docs skill guided task-specific regression checks and human review,
consistent with [official evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices).

## Validation / handoff

67 Python tests and 69 in-game tests passed, including omission rejection,
names-only rejection, responsibility without invented intent, Unicode/linebreak
normalization, both killing and achievement coverage, sparse input, successful
publication evidence, and preservation/no automatic retry after a failed check.
No game restart is required. The existing watcher was restarted and the index
rebuilt. Use Read biography, then U; the longer story updates automatically.
The user authorized committing/pushing this batch on 2026-09-06 after the
coverage and length handoff. This approval does not replace the remaining
rare-event and narrative-quality coverage limits documented below.

Live schema-16 validation produced five paragraphs, with both the attributed
killing and artifact creation passing the sentence gate (events 73864, 75042).
Generation took 17.33 s; preparation 0.56 s; total 20.93 s. Longer prose increases
latency; no second model validation call or automatic repair call was added.
The generated reference to horror was checked separately: the profile's
WitnessDeath/HORROR entry resolves through incident 181 to the same victim HF
11527, not an unrelated death. This supports the association, not remorse or
intent. Remaining stylistic issues include duplicated artifact description and
technical caveat prose; the gate is not a claim of complete narrative quality.
