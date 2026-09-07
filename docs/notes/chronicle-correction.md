# Bounded chronicle corrections — 2026-09-06

The live draft omitted incident 667's topic year (1) and shortened incident 680's
teller to Urist rather than Urist Udiboltar. Coverage was not relaxed.

After an annual generation fails coverage, preserve the original candidate and
make at most ONE correction call per request. Persist `correction_attempted`
before that call; failures, restarts and later watcher polls cannot retry it.
One chapter per watcher cycle now permits two model calls: initial generation
plus correction. No correction for model/network failures during initial writing.
More than four flagged events fails closed without a correction model call.

The model receives numbered sentences and missing factual anchors; returns up to
four `{event_id,sentence_id,new}` replacements encoded in the existing batch text
field. Validate indices, one complete sentence per edit, size, uniqueness,
non-overlap, each flagged fact, and finally ALL coverage. Unchanged text is
preserved byte-for-byte. Every original word must remain in order: corrections
only insert missing information, never delete classifications or other wording.
An interrupted processing state with a persisted attempt marker fails closed
without restarting generation or resetting the budget.
Unsupported sentence punctuation may conservatively fail;
never guess a replacement location. Prior good prose remains visible on failure.

The first live exact-source-copy protocol failed to reproduce a source sentence;
it published nothing. Sentence indices remove that copy requirement. Responses
are now retained before validation (16 KiB limit), alongside original prose and
outcome. The original failed attempt remains in the audit record. A separate
explicit operator validation of the revised protocol does not reset the automatic
attempt budget. `recheck_rejected(..., edits=...)` can publish externally validated
edits without another model call, after matching original request provenance and
checking coverage again. `repair=True` consumes the ordinary single attempt.

Tests cover missing dates, abbreviated names, unrelated/overlapping/bad edits,
preserved prose, unchanged full coverage, offline failure, durable attempt limits,
successful generation/correction/cache behavior. The existing low-effort Luna
model and authentication path are unchanged. Prompt design follows explicit
success criteria and empirical validation from [OpenAI prompting guidance](https://developers.openai.com/api/docs/guides/prompt-engineering).

Final verification: synthetic live indexed/insertion-only correction passed in
9.73 seconds. The real draft was recovered without further model calls using the
two verified insertions, preserving the organization classification. All six
required checks passed, including incidents 667 and 680. The checker accepts
the narrow `later told a story about` form without arbitrary pronoun inference.
Original rejected prose and development diagnostics remain on disk.
Player: reopen `lorekeeper/chronicles`, year 102. No retry/new draft is needed to
see this recovery. No DF restart, commit, or push.
