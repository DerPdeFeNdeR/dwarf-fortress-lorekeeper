# Lorekeeper data contract

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
