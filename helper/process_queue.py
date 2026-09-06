#!/usr/bin/env python3
"""Process Lorekeeper JSONL translation jobs through one Codex batch."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from codex_batch import normalize_items, run_batch


def display_safe_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    normalized = unicodedata.normalize('NFKD', value)
    return normalized.encode('ascii', errors='ignore').decode('ascii')


def display_safe_results(results: dict[str, Any]) -> dict[str, Any]:
    safe_results = {}
    for result_id, result in results.items():
        if not isinstance(result, dict):
            safe_results[result_id] = result
            continue
        safe_result = dict(result)
        for field in ('text', 'explanation', 'category'):
            if field in safe_result:
                safe_result[field] = display_safe_text(safe_result[field])
        safe_results[result_id] = safe_result
    return safe_results


def load_queue(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw_queue = path.read_bytes()
    try:
        queue_text = raw_queue.decode('utf-8')
    except UnicodeDecodeError:
        # DFHack may persist CP437 strings from Dwarf Fortress in JSON text.
        queue_text = raw_queue.decode('cp437')

    items = []
    for line_number, line in enumerate(queue_text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'invalid queue JSON on line {line_number}') from exc
        items.append(item)
    return items


def load_results(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw_results = path.read_bytes()
    try:
        results_text = raw_results.decode('utf-8')
    except UnicodeDecodeError:
        results_text = raw_results.decode('cp437')
    data = json.loads(results_text)
    if not isinstance(data, dict):
        raise ValueError('translation cache must be a JSON object')
    return data


def write_results(path: Path, results: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded_results = (json.dumps(display_safe_results(results), ensure_ascii=True, indent=2,
                                  sort_keys=True) + '\n').encode('cp437', errors='replace')
    with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, delete=False) as output:
        output.write(encoded_results)
        temporary_path = Path(output.name)
    os.replace(temporary_path, path)


def process_queue(queue_path: Path, result_path: Path) -> int:
    queued_items = normalize_items(load_queue(queue_path))
    cached_results = load_results(result_path)
    pending_items = [item for item in queued_items if item['id'] not in cached_results]
    if not pending_items:
        if cached_results:
            write_results(result_path, cached_results)
        return 0

    batch = run_batch(pending_items)
    for result in batch['results']:
        cached_results[result['id']] = result
    write_results(result_path, cached_results)
    return len(batch['results'])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('queue', type=Path)
    parser.add_argument(
        'results', type=Path, nargs='?',
        help='JSON cache path; defaults to lorekeeper-translation-cache.json beside the queue',
    )
    args = parser.parse_args()
    result_path = args.results or args.queue.with_name('lorekeeper-translation-cache.json')
    count = process_queue(args.queue, result_path)
    print(f'Lorekeeper: processed {count} translation job(s).')


if __name__ == '__main__':
    main()
