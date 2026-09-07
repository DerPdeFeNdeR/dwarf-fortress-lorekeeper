# Natural chronicle context — 2026-09-06

The user reported repeated "In Hematite" openings and detached lists explaining
several organizations after their stories. Exact required sentences forced both:
each contained a month prefix and disallowed inline context.

Annual generation now accepts ordered factual clause groups instead of full
verbatim sentences. Historical action clauses retain named participant roles.
Cultural clauses retain teller/action, office subject and historical subject year,
with four supported telling-verb choices and bounded space for inline explanations.
All groups for a fact must occur in order within one sentence, separated by at
most 240 characters. Names in unrelated sentences do not satisfy coverage.
Memoire sentences retain their existing validation contract.

The prompt establishes shared month context, varies transitions, and explains
supplied race/organization type at first mention. Current classification does
not prove historical classification. Topic dates still date the historical
subject rather than the local telling. The checker is an omission/role guard,
not a general semantic verifier: chronology, interpretation and literary quality
still require review. No extra model call, render-loop work or retry loop is added.

Used the OpenAI Docs skill and [official prompting guidance](https://developers.openai.com/api/docs/guides/prompt-engineering)
to remove conflicting instructions and validate the revised prompt. Model and
reasoning settings remain unchanged.

Tests cover shared month context, inline classification, supported phrasing,
missing/wrong tellers, subjects and dates, reversed killing roles, and scattered
mentions. Initial live fixtures accidentally used non-Hematite timestamps;
they now derive the date from the shared calendar and assert it before calling
the model. A subsequent live sample passed factual coverage and inline context
but exposed an overly strict style assertion. The user explicitly agreed that a
closing reflective mention of Hematite is fine: check repeated introductions,
not every occurrence of the month name.

Completed chapters are not rewritten. Request a new year-so-far draft with D in
`lorekeeper/chronicles`. Restart the existing watcher to load Python changes;
no Dwarf Fortress restart is needed. Player review precedes commit/push.

Final verification: Python discovery ran 140 tests (136 passed, 4 opt-in
skipped). The grouped-month live test passed separately in 9.38 seconds, with
all three telling facts, one Hematite introduction and inline human-government
context for each named league. Cached reopening made no additional model call.
`git diff --check` passed. The existing watcher was restarted and reported
Running. Actual player review of the regenerated year-102 draft remains pending.
