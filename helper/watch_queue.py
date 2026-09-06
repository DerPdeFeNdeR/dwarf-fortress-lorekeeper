#!/usr/bin/env python3
"""Watch a Lorekeeper queue and process new jobs through Codex."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Callable

from process_queue import process_queue


def queue_state(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return stat.st_mtime_ns, stat.st_size


def process_if_changed(queue_path: Path, result_path: Path,
                       previous_state: tuple[int, int] | None,
                       processor: Callable[[Path, Path], int] = process_queue
                       ) -> tuple[int, tuple[int, int] | None, Exception | None]:
    current_state = queue_state(queue_path)
    if current_state is None or current_state == previous_state:
        return 0, previous_state, None
    try:
        count = processor(queue_path, result_path)
    except Exception as error:  # noqa: BLE001 - retry while the watcher remains alive
        return 0, previous_state, error
    return count, current_state, None


def watch(queue_path: Path, result_path: Path, interval: float,
          processor: Callable[[Path, Path], int] = process_queue,
          sleep: Callable[[float], None] = time.sleep) -> None:
    previous_state = None
    while True:
        count, previous_state, error = process_if_changed(
            queue_path, result_path, previous_state, processor)
        if count:
            print(f"Lorekeeper: processed {count} translation job(s).", flush=True)
        if error:
            print(f"Lorekeeper: queue processing failed; will retry: {error}", flush=True)
        sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queue", type=Path)
    parser.add_argument("results", type=Path, nargs="?",
                        help="JSON cache path; defaults beside the queue")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="seconds between queue checks (default: 5)")
    parser.add_argument("--once", action="store_true",
                        help="process the queue once and exit")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")

    result_path = args.results or args.queue.with_name("lorekeeper-translation-cache.json")
    if args.once:
        count = process_queue(args.queue, result_path)
        print(f"Lorekeeper: processed {count} translation job(s).")
        return

    print(f"Lorekeeper: watching {args.queue} every {args.interval:g}s.", flush=True)
    try:
        watch(args.queue, result_path, args.interval)
    except KeyboardInterrupt:
        print("Lorekeeper: queue watcher stopped.")


if __name__ == "__main__":
    main()
