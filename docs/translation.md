# Translation boundary

The deterministic glossary is the first translation layer. It converts a raw
DF token into a small structured result without changing the captured
snapshot:

```json
{
  "schema_version": 1,
  "kind": "thought",
  "known": true,
  "raw": "Talked",
  "text": "Had a conversation",
  "source": "glossary",
  "confidence": "high"
}
```

Unknown tokens use `known: false`, preserve the raw token, set
`source: "unknown"` and `confidence: "none"`, and display an explicit
unknown message. They are never silently guessed.

The glossary result is presentation data, not history data. History retains
the raw IDs and values from the snapshot so labels can be corrected or
retranslated later. A future local model helper should accept only bounded,
explicit inputs, return this same shape plus model metadata, and remain
optional and asynchronous.

## User-facing queue workflow

The DFHack `lorekeeper/translate` and `lorekeeper/story` commands write JSONL
jobs to the active save directory. Running `helper/process_queue.py` manually
is currently a development bridge, not the intended user workflow.

The finished product should run a background local watcher that notices queued
jobs and updates the cache without requiring the player to leave Dwarf
Fortress. The in-game UI should show pending, ready, and failure states while
the helper remains outside DFHack for credentials and model execution.

History story jobs use the `dwarf-history-v2` request namespace and include
grouped events plus exact thought and personality changes. The cache key is
versioned so changes to that payload contract force a fresh model result.

The helper cache writer preserves Unicode by using JSON Unicode escapes. This
keeps the cache ASCII-safe for DFHack while allowing names and model prose to
round-trip with their original characters.
