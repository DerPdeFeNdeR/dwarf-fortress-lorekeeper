# Codex game integration verification — 2026-09-06

Environment: DF 0.53.16 win64 STEAM, DFHack 53.16-r1.1.

## Verified path

1. Select dwarf Eral èrithbomrek (unit 4068).
2. Run `lorekeeper/translate` in DFHack.
3. Process the queue from WSL:

   ```text
   python3 helper/process_queue.py "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dwarf Fortress/save/region3/lorekeeper-translation-queue.jsonl"
   ```

4. Refresh `lorekeeper/show`.

The command processed one Codex job and the window displayed a model
interpretation alongside the current identity, thoughts, stress, and
personality facets. The game-facing command did not wait for Codex.

## Compatibility note

DFHack writes some Dwarf Fortress strings as CP437 bytes, while Codex returns
Unicode. The queue reader accepts UTF-8 or CP437. The result cache uses
ASCII-safe display text so DFHack's JSON decoder and UI do not misread UTF-8
bytes as CP437. Raw snapshots and the Identity section remain authoritative.

## Scope note

`lorekeeper/show` is currently a current-state summary. It does not yet
assemble a timeline or generate a historical story. Historical narrative
requires querying recorded snapshots and adding event/change context.
