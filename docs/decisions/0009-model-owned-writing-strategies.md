# ADR-009: Keep writing strategies owned by their model

**Status:** accepted  
**Date:** 2026-09-07

## Context

Lorekeeper now supports a local Qwen3/Ollama writer alongside the authenticated
Codex/Luna writer. The two models need different prompts, context preparation,
output shapes, and tuning. Treating a strategy as interchangeable across
providers made it too easy for a Qwen optimization to silently change Luna's
behavior, or for a new model to inherit an unsuitable policy.

## Decision

Register each supported model with an explicit writing policy. The router resolves
the model and its permitted Memoire and Chronicle strategies before preparing a
prompt or selecting a transport. Unknown models and cross-model strategy choices
fail before model work.

Qwen3:8b owns the personal-brief and anchored/compact Chronicle strategies.
gpt-5.6-luna owns the full-context literary strategy. Luna preparation remains in
its own module and does not use Qwen's personal-fact compiler or Python annual
assembly. Transport adapters remain shared and accept only an already-prepared
prompt and schema. Model tuning and strategy tuning are separate validated parts
of the generation identity.

## Alternatives considered

We considered one provider-independent strategy registry with any strategy usable
by any model. That made comparisons convenient, but it blurred model-specific
assumptions and allowed accidental cross-model behavior. We also considered
duplicating the entire worker for each model, which would duplicate persistence,
coverage, locking, and error handling. Explicit model policies with shared
transports preserve the useful common safeguards without sharing writing policy.

## Consequences

Adding a model requires an explicit registration, a strategy implementation, and
routing tests. A model switch can invalidate cached prose because model and
strategy versions are part of generation provenance. Profiles are easy to select,
but arbitrary model strings are rejected until deliberately supported. Qwen can be
tuned for speed without changing Luna; Luna retains its existing full-context
behavior. Existing stories remain readable and failed replacements preserve their
last successful provenance.

See [model-owned writer notes](../notes/model-owned-writers.md) for profiles,
live checks, and player/developer setup.
