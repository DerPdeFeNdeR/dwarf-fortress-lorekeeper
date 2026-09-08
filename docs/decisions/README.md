# Architecture decisions

This directory contains short, version-controlled Architecture Decision
Records (ADRs). Add an ADR when a choice affects the project structure,
integration boundary, data format, model behavior, or user experience.

## Decision index

- [001: Dedicated summary window](0001-dedicated-summary-window.md)
- [002: Citizen collector policy](0002-citizen-collector-policy.md)
- [003: HTTP prototype](0003-local-translation-helper.md) — historical; not the active reader backend
- [004: Collector autostart](0004-collector-autostart.md)
- [006: Annual Chronicles](0006-annual-fortress-chronicles.md)
- [007: Dwarf narrators](0007-dwarf-narrators.md)
- [008: Observed atmosphere](0008-observed-atmosphere.md)

Decisions preserve their original context. Use the [current setup guide](../../README.md)
and [contracts](../schema.md) for operational instructions and schema versions.

## Template

Use this format:

```markdown
# ADR-NNN: Decision title

**Status:** proposed | accepted | superseded
**Date:** YYYY-MM-DD

## Context

What problem or constraint led to this decision?

## Decision

What are we choosing?

## Alternatives considered

What else was considered, and why was it not chosen?

## Consequences

What becomes easier, harder, or constrained by this decision?
```
