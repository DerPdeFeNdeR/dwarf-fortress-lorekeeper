# Story-first biography reader — 2026-09-06

## Implementation

`lorekeeper/read` opens a dedicated modal DFHack window with name/profession,
paragraph-preserving white prose, a secondary interpretation notice, and simple
Update / Details / Close controls. No timeline, ticks, raw stress, trait values,
or record counts appear in the story body. The existing debug UI is unchanged.

Opening or U captures the selected subject on demand and submits the existing
small request protocol. The protocol now additionally returns its request token
so the reader can distinguish a previously ready result from the newly requested
update. Existing callers retain their original first two return values.

The reader checks bounded status once per wall-clock second while open, including
while paused. It retains old prose through processing, failure, and watcher
unavailability. Status changes rebuild the display while preserving selection;
window resizing rewraps prose. D only toggles the prepared timeline; N/P only read
its pages. No UI path parses history logs, starts a model directly, or changes the
collector. The existing watcher and generation cache remain unchanged.

## Verification

- 49 DFHack regression tests passed (seven new reader presentation/state tests).
- 43 Python regression tests passed; `git diff --check` passed.
- Opened the reader through the real DFHack client on selected unit 4525.
- Exercised D, N, and D again via screen input: details page 2 worked and request
  nonce stayed unchanged; the story remained free of timeline rows.
- U produced a newer request token. The saved story stayed readable.
- Verified accented name with DF-to-UTF-8 round trip. An initial inline test with
  a literal accent failed due to the Windows command transport; the ASCII-byte
  assertion passed, confirming this was not a reader rendering regression.
- Forced refresh retained selected row 5. Escape dismissed the reader.

The user reviewed the reader in-game and said "looks good", then approved
committing/pushing this checkpoint. This is overall visual acceptance, not a
claim of exhaustive mouse/resizing coverage at every game UI scale. Final checks
again passed 49 live DFHack tests and 43 Python tests. The vanilla-screen entry
button remains a separate, not-yet-implemented milestone.

## User test

No game or watcher restart is required. If DFHack retains an older module, retry
the command first; restart only if it still fails to reload.

1. Select a dwarf with a known biography and run `lorekeeper/read`.
2. Check prose readability, accents, paragraph spacing, and the small notice.
3. Scroll using arrow keys, Page Up/Down, or the mouse wheel; try resizing.
4. Press D: the technical timeline should appear. Try N/P, then D to return.
5. Press U: existing prose should remain readable while it updates automatically.
   A cache hit may finish quickly and need not change the words.
6. Press Escape, select another dwarf, and run `lorekeeper/read` again.

The collector need not be started manually to test existing stories. Let the
fortress run with its collector active only when testing genuinely newer history.
The selected-dwarf-screen entry button and in-window dwarf switching are not
part of this checkpoint.
