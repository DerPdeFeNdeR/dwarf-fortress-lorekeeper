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
