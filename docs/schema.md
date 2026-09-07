# Lorekeeper data contract

## Current protocol map

Audited 2026-09-07 against implementation checkpoint `8dd7a66`. These are
independent contracts, not one global schema version.

| Contract | Version | Purpose |
| --- | --- | --- |
| Persisted dwarf snapshot | 1 | Raw append-only history record below |
| On-demand profile | 9 | Bounded context and typed references; 128 KiB file cap |
| Prepared history view | 26 | Python-prepared reader status, timeline and story caching |
| Monthly request protocol / book | 1 / 2 | Introduction and significant monthly Memoires |
| Annual request | 2 | Year evidence plus saved narrator; version 1 remains readable |
| Environment observation | 1 | Bounded observed calendar/weather/geography context |

Profiles are captured on demand, not for every periodic citizen scan. Small
reader requests reference those files. The in-game reader consumes bounded
prepared results, never the full history/model payload. Cache identity includes
semantic evidence and generation settings; capture time alone is not new evidence.
Older incompatible book data is retained separately rather than silently used as
current personal knowledge. Model prose is interpretation, never new evidence.

History indices are derived accelerators; preserve the underlying history log.
Back up generated books and revisions too if their prose matters. Token/glossary
queues and the optional HTTP prototype are separate older contracts; see
[translation](translation.md) and [worker utilities](../helper/README.md).

## Snapshot example

The current persisted record type is `dwarf_snapshot`. Records are written as
one compact JSON object per line to `lorekeeper-history.jsonl` in the active
save directory.

```json
{
  "schema_version": 1,
  "record_type": "dwarf_snapshot",
  "captured_at": "2026-09-06T16:40:19Z",
  "ingame_time": {
    "year": 102,
    "year_tick": 47611
  },
  "snapshot": {
    "schema_version": 1,
    "source": {
      "df_version": "v0.53.16 win64 STEAM",
      "dfhack_version": "53.16-r1.1"
    },
    "context": {
      "site_id": 123,
      "save_id": "region3"
    },
    "identity": {
      "id": 9001,
      "name": "Test Dwarf",
      "race": "DWARF",
      "caste": "MALE",
      "profession": "Miner",
      "citizen": true
    },
    "soul_present": true,
    "mental_state": {
      "stress": 1000
    },
    "thoughts": [
      {
        "thought_id": 165,
        "thought_name": "Talked",
        "emotion_id": 66,
        "emotion_name": "FONDNESS",
        "severity": 0,
        "relative_strength": 0,
        "subthought": 17
      }
    ],
    "personality_facets": [
      {
        "facet_id": "CONFIDENCE",
        "facet_name": "CONFIDENCE",
        "value": 50
      }
    ]
  }
}
```

Raw IDs and values remain authoritative. Readable names are convenience
labels, and later glossary or model translations must not replace the raw
fields.

The collector's change signature intentionally ignores `subthought`, treats
thoughts as an order-independent counted set, and groups stress into 500-point
bands. The full snapshot is still preserved when a record is emitted.
