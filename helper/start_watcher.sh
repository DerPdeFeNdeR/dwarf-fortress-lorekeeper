#!/usr/bin/env bash
# Start the Lorekeeper watcher for use from WSL login or Windows Task Scheduler.

set -euo pipefail

project_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
save_directory="${1:-/mnt/c/Program Files (x86)/Steam/steamapps/common/Dwarf Fortress/save}"

cd "$project_directory"
log_directory="${XDG_STATE_HOME:-$HOME/.local/state}/lorekeeper"
mkdir -p "$log_directory"
exec >>"$log_directory/watcher.log" 2>&1
printf 'Lorekeeper watcher starting: %s\n' "$(date -Is)"
exec env TMPDIR="${TMPDIR:-/dev/shm}" python3 helper/watch_save_directory.py "$save_directory"
