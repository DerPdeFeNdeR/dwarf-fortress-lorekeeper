# Collection, generation, and presentation boundary

Current pipeline: Windows DFHack writes bounded profiles/requests beside saves;
`helper/watch_save_directory.py` in WSL prepares timelines and model inputs, invokes
the authenticated Codex CLI, validates output and writes caches. Readers poll those
prepared files without network calls or history parsing in the game thread.

## Current story workflow

- `lorekeeper/memoire` (alias `read`) opens a selected-dwarf monthly book. Opening/U
  captures once. Introduction first, significant months newest-first; unchanged
  evidence reuses prose, and updates revise chapters rather than append filler.
- `lorekeeper/chronicles` displays annual chapters; D requests a current-year draft,
  and the monitor queues a finished year after observing rollover.
- `lorekeeper/story` creates a small `lorekeeper-views` request. It does **not** write
  the old `dwarf-history-v3` JSONL job. `history/show` is the prepared debug reader.
- Current view schema is 26, profile schema 9, monthly request protocol 1/book 2,
  annual request schema 2. See [contracts](schema.md) for storage and provenance.

The worker explicitly selects `gpt-5.6-luna` / low reasoning by default. Account
access must be verified; model/effort can be configured without changing personal
Codex defaults. Credentials stay outside Lua and saves. Structured game data is
sent to the model provider; this is not a fully offline workflow. See
[worker documentation](../helper/README.md).

## Evidence and cache safeguards

Memoires use first-person personal-knowledge-filtered inputs; annual chronicles
have broader local history and one saved narrator per year. Imagined motives are
interpretation, not new evidence. Generated prior prose is not a factual source.
Unknown references remain unknown. Current relationship links do not prove old
relationships or awareness of another person's events.

Required anchors check selected consequential events and tellings, not all possible
claims. Failed replacements preserve good prose. Annual coverage failures permit
one insertion-only sentence-index correction; it must pass all anchors, and its
attempt is persisted before invocation to survive crashes without loops. Personal
Memoire failures do not use this annual correction path.

Cache identity includes relevant evidence and writer/model/effort/schema context.
Optional atmosphere is attached after significance selection, not a reason to
generate a new chapter. Shared observed weather is excluded from personal Memoire
inputs; annual context can include it. Completed annual chapters stay immutable.
Prepared views describe captured revisions, not continuously live game state.

JSON writers preserve Unicode, escaping it where needed for DFHack. Display
conversion happens once per line after splitting paragraph breaks. Known legacy
mojibake is repaired conservatively; raw/source text remains available for audit.

## Deterministic glossary and legacy utilities

Known tokens are labeled locally (`known: true`, `source: glossary`); unknowns
preserve the raw token and explicitly report unknown status. These labels never
replace raw history data.

`lorekeeper/translate` still queues an old selected-unit explanation to
`lorekeeper-translation-queue.jsonl`; the save watcher processes it for
`lorekeeper/show`. `process_queue.py` and `watch_queue.py` handle this legacy queue,
not current Memoires/Chronicles. They are developer utilities, not required player
steps. `helper/server.py` is a separate localhost Platform API prototype and is not
wired to the current readers.

Startup remains two-part: DFHack autostart for collection and an optional Windows
logon task for the WSL worker. Launching the worker with DFHack itself is a future
product goal, not implemented behavior.
