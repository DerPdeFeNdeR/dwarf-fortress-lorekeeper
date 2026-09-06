#!/usr/bin/env bash
# Start the Lorekeeper watcher for use from WSL login or Windows Task Scheduler.

set -euo pipefail

project_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
save_directory="${1:-/mnt/c/Program Files (x86)/Steam/steamapps/common/Dwarf Fortress/save}"

cd "$project_directory"
exec env TMPDIR="${TMPDIR:-/dev/shm}" python3 helper/watch_save_directory.py "$save_directory"
