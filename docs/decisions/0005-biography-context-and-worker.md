# ADR-005: Bounded biography context and asynchronous Luna worker

Date: 2026-09-06
Status: Accepted for the current development checkpoint

## Context

Generic thought summaries lacked named people and meaningful personal context.
Full history/model work must not block the game. The user verified richer
biographies, Unicode names, automatic refresh, and accepted Luna's current quality
and approximately 11-second generation samples before moving to a friendly reader.

## Decision

Capture bounded profiles on demand, never in the periodic citizen collector.
Resolve supported references through a typed, per-capture lookup cache with
explicit unsupported/missing states. Keep raw profiles separate from small view
requests. Python prepares timeline pages and compact story input outside DFHack.

Use explicit `gpt-5.6-luna` / low reasoning in the existing authenticated Codex
worker, independently of interactive coding settings. Biography cache identity
includes semantic input, schema, model, effort, and historian prompt. Keep prior
stories readable while new work is pending; poll bounded status once per second
in the open window, including while paused. Preserve full diagnostic timelines.

## Alternatives and consequences

Inheriting the personal Codex default caused unpredictable model choice and
latency. Synchronous model calls remain unacceptable. Continuous pre-generation
for all dwarves adds usage and backlog and is deferred. Further model/reasoning
comparisons are also deferred at the user's request.

Fresh stories still take seconds, and sequential worker requests may queue.
Resolved identities improve specificity but do not establish relationships at
past event times. Prompt rules reduce errors, not guarantee factual correctness.
The next milestone is a separate story-first reader; this checkpoint does not
implement that reader or a vanilla-screen button.

Evidence and tests: [reference resolution](../notes/typed-reference-resolution.md),
[responsiveness](../notes/biography-responsiveness.md), and
[Luna validation and acceptance](../notes/luna-biography-validation.md).
