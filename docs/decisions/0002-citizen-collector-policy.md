# ADR-002: Use a throttled all-citizen snapshot collector

**Status:** accepted  
**Date:** 2026-09-06

## Context

The project needs a fuller history than manual inspection can provide, but
thought lists and stress values change frequently. Capturing every raw change
would create excessive JSONL volume and unnecessary file I/O.

## Decision

The first automatic collector tracks living fortress citizens returned by
`dfhack.units.getCitizens()`. It scans in batches of 12 units, schedules a
new sweep every 100 game ticks, keeps signatures in memory, and emits at most
one snapshot per dwarf per 1,200 game ticks (one in-game day).

Signatures ignore subthought-only changes, compare thought/emotion/severity
combinations as an order-independent counted set, and use 500-point stress
bands. The full raw snapshot is written only when the policy emits a record.
The collector is opt-in, has start/stop/status commands, and stops when the
world unloads.

## Alternatives considered

- Manual recording only: simpler, but misses changes the player does not see.
- Selected-dwarf polling: lightweight, but produces incomplete fortress history.
- Unthrottled all-citizen polling: complete in theory, but too noisy and
  expensive for thought-list churn.
- Event-only collection: efficient where available, but does not cover all
  mental-state changes reliably across DFHack versions.

## Consequences

- History is broader and less dependent on player behavior.
- The history file remains local to the save and append-only.
- Very rapid changes may be represented by the next eligible snapshot rather
  than every intermediate state.
- The collector's pure policy is testable without writing save data.
- Future high-priority event records can bypass the regular snapshot cooldown.
