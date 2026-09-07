"""Lossless compact presentation of repeated records for local model prompts."""
import json


def compact(value):
    if isinstance(value, dict):
        return {key: compact(item) for key, item in value.items()}
    if not isinstance(value, list):
        return value
    rows = [compact(item) for item in value]
    if len(rows) < 2 or not all(isinstance(row, dict) for row in rows):
        return rows
    columns = list(rows[0])
    if not columns:
        return rows
    if any(set(row) != set(columns) for row in rows):
        schemas, packed = [], []
        for row in rows:
            keys = sorted(row)
            if keys not in schemas:
                schemas.append(keys)
            packed.append([schemas.index(keys)] + [row[key] for key in keys])
        table = {'record_schemas': schemas, 'record_rows': packed}
    else:
        table = {'record_columns': columns,
                 'record_rows': [[row[key] for key in columns] for row in rows]}
    return table if len(encode(table)) < len(encode(rows)) else rows


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def compact_raw(raw):
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return raw
    return encode(compact(value))
