# Chronicle rejection diagnostics — 2026-09-06

The year-102 draft failed coverage for incident 667. The original generated text
was discarded, so it is unknown whether it omitted the fact or used unsupported
wording. Do not retrospectively claim one cause without evidence.

Annual coverage errors now say "Chronicle coverage check could not verify".
The latest rejected prose is saved in `<chapter-key>.rejected.json` alongside
missing IDs, the requirements, request identity/digest, prompt digest and model
settings. The prose already passed the 16,000-byte display limit; one diagnostic
file per chapter is replaced on the next rejection, not accumulated per retry.
It is never placed in the chapter catalog or shown as accepted prose. The last
good draft and its narrator attribution remain intact. Diagnostic write failure
does not publish a rejected story. There is no automatic model retry.

Cultural requirements accept additional telling verbs, taking/took office or
becoming/became the supplied office, inline subject descriptions, and written-out
small years. Each event still binds teller, subject, office, organization and
subject year within one sentence. Wrong offices, unrelated tellers, year 11 in
place of year 1, scattered names and negation in connective gaps are rejected.
This conservative structural check is not a general semantic verifier.

Unit tests exercise failure persistence, preservation of the previous story and
narrator, bounded replacement of diagnostics, no unsolicited retry, successful
publication of supported natural wording, and incorrect/negated fact rejection.
No game-thread or collection work was added. Restart the existing watcher for
Python changes; no game restart is required. Completed chapters remain immutable.

The explicit in-game retry passed incident 667 but rejected a victim-first death
sentence using "death came to [victim] at [site] when [slayer] killed him".
The preserved prose proved this was a wording mismatch. Added narrowly scoped
passive/victim-first alternatives that retain both names and local role binding;
arbitrary pronouns across sentences are still not resolved.

`chronicles.recheck_rejected(save, key)` is an explicit operator recovery tool,
not an automatic retry. It verifies the failed state, chapter/request identity,
request digest and candidate size, then reruns all coverage checks before
publication. It rejects ready chapters or changed requests. Recovery retains
original generation settings and narrator identity and marks the provenance.

Verification: 155 Python tests (150 passed, 5 opt-in skipped), including rejection
persistence, natural appointment/date wording, locally bound victim pronouns,
wrong/negated facts, no automatic retry, explicit no-model recovery, and stale
request rejection. The actual year-102 candidate passed all seven requirements
(three deaths and four tellings, including incident 667) and was recovered to
ready without another model call. The latest watcher restart loads these rules.
The old discarded candidate remains unavailable; its precise failure cause is
still unknown. No commit or push; player review of the recovered draft is next.
