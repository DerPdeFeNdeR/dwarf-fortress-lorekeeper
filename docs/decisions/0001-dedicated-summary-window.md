# ADR-001: Use a dedicated in-game summary window

**Status:** accepted  
**Date:** 2026-09-06

## Context

The tool needs to explain a selected dwarf's thoughts, personality, and
related mental state. Replacing vanilla text in place would be tightly coupled
to DF screen layouts and more likely to break across game or DFHack updates.

## Decision

The first user-facing feature will be a separate, read-only DFHack summary
window opened for the currently selected dwarf. The vanilla Dwarf Fortress UI
will remain unchanged. In-place text replacement can be considered later if
there is a strong usability reason.

## Alternatives considered

- Replace vanilla thought text directly: more seamless, but fragile and harder
  to debug.
- External history UI first: easier to build, but does not satisfy the
  immediate in-game inspection workflow.
- Permanent overlay beside every dwarf screen: available as a fallback, but
  less focused than an explicitly opened summary window.

## Consequences

- The first implementation can use DFHack's normal GUI APIs and remain
  independent of vanilla screen coordinates.
- The window needs clear refresh, close, loading, and unavailable-data states.
- The translation model can be added asynchronously without blocking the game.

