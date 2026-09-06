#!/usr/bin/env python3
"""Process Lorekeeper JSONL translation jobs through one Codex batch."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from codex_batch import normalize_items, run_batch


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
    # JSON unicode escapes keep the file ASCII-safe for DFHack while preserving
    # the original characters when its JSON decoder reads the cache.
    encoded_results = (json.dumps(results, ensure_ascii=True, indent=2,
                                  sort_keys=True) + '\n').encode('cp437', errors='replace')
    with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, delete=False) as output:
        output.write(encoded_results)
        temporary_path = Path(output.name)
    os.replace(temporary_path, path)


def repair_story_names(items: list[dict[str, Any]], results: list[dict[str, Any]]) -> None:
    """Replace CP437-mojibake names in model prose with the source name."""
    items_by_id = {item.get('id'): item for item in items}
    for result in results:
        item = items_by_id.get(result.get('id'))
        if not item or item.get('kind') != 'dwarf_history':
            continue
        try:
            story_input = json.loads(item['raw'])
            full_name = story_input['identity']['name']
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
        if not isinstance(full_name, str) or not isinstance(result.get('text'), str):
            continue
        personal_name = full_name.split(',', 1)[0]
        for source_name in (full_name, personal_name):
            mojibake_name = source_name.encode('utf-8').decode('cp437')
            result['text'] = result['text'].replace(mojibake_name, source_name)


def process_queue(queue_path: Path, result_path: Path) -> int:
    queued_items = normalize_items(load_queue(queue_path))
    cached_results = load_results(result_path)
    pending_items = [item for item in queued_items if item['id'] not in cached_results]
    if not pending_items:
        if cached_results:
            write_results(result_path, cached_results)
        return 0

    batch = run_batch(pending_items)
    repair_story_names(pending_items, batch['results'])
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
