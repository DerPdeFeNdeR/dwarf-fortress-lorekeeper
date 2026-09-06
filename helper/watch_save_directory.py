#!/usr/bin/env python3
"""Watch all Dwarf Fortress save queues for new Lorekeeper jobs."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Callable

from process_queue import process_queue
from watch_queue import process_if_changed


QUEUE_NAME = "lorekeeper-translation-queue.jsonl"


def process_directory_once(
    save_directory: Path,
    states: dict[Path, tuple[int, int] | None],
    processor: Callable[[Path, Path], int] = process_queue,
) -> tuple[int, dict[Path, tuple[int, int] | None], list[Exception]]:
    total = 0
    errors = []
    current_queues = set(save_directory.glob(f"*/{QUEUE_NAME}"))
    for queue_path in sorted(current_queues):
        result_path = queue_path.with_name("lorekeeper-translation-cache.json")
        count, state, error = process_if_changed(
            queue_path, result_path, states.get(queue_path), processor
        )
        total += count
        if error:
            errors.append(error)
        states[queue_path] = state
    for queue_path in set(states) - current_queues:
        del states[queue_path]
    return total, states, errors


def watch_directory(
    save_directory: Path,
    interval: float,
    processor: Callable[[Path, Path], int] = process_queue,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    states: dict[Path, tuple[int, int] | None] = {}
    while True:
        count, states, errors = process_directory_once(save_directory, states, processor)
        if count:
            print(f"Lorekeeper: processed {count} translation job(s).", flush=True)
        for error in errors:
            print(f"Lorekeeper: queue processing failed; will retry: {error}", flush=True)
        sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save_directory", type=Path)
    parser.add_argument("--interval", type=float, default=5.0,
                        help="seconds between queue checks (default: 5)")
    parser.add_argument("--once", action="store_true",
                        help="process discovered queues once and exit")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")

    if args.once:
        count, _, errors = process_directory_once(args.save_directory, {})
        for error in errors:
            print(f"Lorekeeper: queue processing failed: {error}")
        print(f"Lorekeeper: processed {count} translation job(s).")
        return

    print(f"Lorekeeper: watching save directory {args.save_directory} every {args.interval:g}s.",
          flush=True)
    try:
        watch_directory(args.save_directory, args.interval)
    except KeyboardInterrupt:
        print("Lorekeeper: save-directory watcher stopped.")


if __name__ == "__main__":
    main()
