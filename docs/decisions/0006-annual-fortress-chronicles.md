# 0006: Background annual fortress chronicles

Date: 2026-09-06

## Context

The player wants a fortress history written at the end of each game year, readable
without leaving DF. Existing memoire generation and history scans must not be
reintroduced into the render loop. Reloads can reverse recorded time.

## Decision

Observe year transitions in a small DFHack monitor using the existing autostart
hook. Reuse the incremental event index, retaining explicit active-site events for
the current and previous year. Export a bounded selection with resolved references
over multiple frames. The external watcher writes a prepared chapter and catalog.

Finished chapters are immutable. Current-year drafts are separate, refreshable
outputs. Both initially used the established historian persona and factual coverage checks.
The narrator choice is superseded by [ADR 0007](0007-dwarf-narrators.md);
annual persistence, evidence boundaries, and immutability remain unchanged.
Failed requests require explicit retry, avoiding repeated model calls.

Use a separate recording branch on every map load or observed time reversal.
Earlier chapters remain archived and browsable. This conservative isolation avoids
claiming save-lineage knowledge the integration does not have.

## Alternatives and consequences

- Generating synchronously at rollover would freeze the game; rejected.
- Combining every citizen memoire would duplicate events and incorrectly include
  off-site lives. Use explicitly site-associated historical events instead.
- Merging across reloads requires reliable save lineage; defer rather than blend
  incompatible histories. A normal reload also creates a new branch for now.
- A complete annual ledger is future work. This implementation selects 16 events
  from bounded buckets and discloses partial coverage, including truncated input.
- A year transition not observed while the monitor is active cannot be promised a
  chapter. Bounded catch-up handles up to eight years, with missing evidence labeled.

Implementation and verification: [annual chronicles](../notes/annual-chronicles.md).
