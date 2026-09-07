# Qwen stream and personal-thread writers — 2026-09-07

Qwen3:8b now has separate model-owned strategies for the two player-facing
narratives. `anchored-stream` writes an annual Chronicle as one continuous
response with globally ordered verified anchors. It preserves model paragraph
breaks, shapes a single-block response into readable paragraphs, removes repeated
connective or factual sentences, and repairs omitted anchors by inserting the
exact verified sentence. Same-day observed weather is optional context, never a
required event.

`personal-thread` writes Memoire chapters with a bounded continuity seed from
prior prose. The prompt asks for a primary personal thread plus one or two
meaningful supporting moments when a month contains several consequential facts.
Supplied dwarf thoughts establish the dwarf's own awareness and reactions; they
do not establish eyewitness attendance. Missing required Memoire facts receive
one deterministic insertion repair for this strategy before normal coverage
validation. Routine observations may be grouped or omitted.

The active profile is `qwen-thread`: Memoire `personal-thread`, Chronicle
`anchored-stream`, Ollama `qwen3:8b`. Luna remains behind its independent
`luna-literary` strategy. The full Python suite passed 215 tests on this date
(seven optional tests skipped). New drafts require a reader Update/D request;
existing completed chapters are not rewritten automatically.
