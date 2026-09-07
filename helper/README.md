# Lorekeeper background worker

For Windows installation, use the [root README](../README.md#windows-developer-installation).
All commands here run in **WSL from the repository root**, unless stated otherwise.
The active worker uses Python's standard library plus an authenticated Linux Codex CLI.
POSIX `fcntl` locking and process groups mean native Windows Python is not supported.

## Active workflow

```bash
python3 helper/watch_save_directory.py "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dwarf Fortress/save"
```

Adjust the save root. This watches direct child region folders, prepares small
`lorekeeper-views` requests and annual `lorekeeper-chronicles` requests, and also
processes legacy token queues. It maintains a heartbeat and exclusive save-root
lock. One worker per root; Ctrl+C stops a foreground worker. No game-loop network
calls or manual queue processing are needed for Memoires/Chronicles.

`--interval 5` is the default delay between work cycles, not a guaranteed completion
time. `--once` is a development processing pass that **can invoke the model and
write results**; it is not a read-only health check and does not acquire the normal
continuous worker lock. Stop the normal watcher before using it.

The startup wrapper resolves its checkout and redirects output into a WSL log:

```bash
bash helper/start_watcher.sh "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dwarf Fortress/save"
```

Default log: `~/.local/state/lorekeeper/watcher.log`, or
`$XDG_STATE_HOME/lorekeeper/watcher.log` when set. The wrapper defaults temporary
model output to `/dev/shm` unless `TMPDIR` is already set. It does not register or
start a Windows scheduled task itself. See the root README for installation,
`-WhatIf`, access-denied troubleshooting, and explicit first start.

## Configuration

The Codex worker explicitly passes these settings instead of inheriting your
interactive Codex model configuration:

| Variable | Default | Meaning |
| --- | --- | --- |
| `LOREKEEPER_MODEL` | `gpt-5.6-luna` | Model accessible to your Codex account |
| `LOREKEEPER_REASONING_EFFORT` | `low` | Effort accepted by that model |
| `TMPDIR` | `/dev/shm` through wrapper | Temporary structured model output |
| `XDG_STATE_HOME` | `~/.local/state` | Wrapper log parent |

The current model is verified on the development account; availability differs.
To try another account-supported model, set its actual identifier in the WSL
shell before starting the foreground worker. These exports affect that shell's
children, not an already-running task:

```bash
export LOREKEEPER_MODEL='YOUR_SUPPORTED_MODEL'
export LOREKEEPER_REASONING_EFFORT='low'
```

For scheduled startup, put non-secret exports in the WSL login-shell startup
file your distribution reads (commonly `~/.profile` or `~/.bash_profile`). Verify
with `wsl.exe -- bash -lc 'command -v codex; codex login status'` in PowerShell,
then restart the task. A setting only in an interactive `.bashrc` section may not
reach a noninteractive login shell. Do not change personal Codex config for this
project, or copy credentials into the checkout/save files.

Model calls have a 180-second timeout. Current monthly Memoire processing writes
at most one chapter per pass; unchanged/insignificant evidence avoids generation.
Annual processing handles one chapter per pass, with at most one additional
bounded coverage correction. Failed requests retain previous good prose; polling
must not silently regenerate or repeatedly repair them. Explicit U/reopen (Memoire)
or R/D (Chronicles) controls subsequent requests. Legacy token-queue processing
has a separate retry-on-error policy.

## Testing

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm python3 -m unittest discover -s helper -p 'test_*.py'
```

At published checkpoint `8dd7a66`: 176 tests, 169 passed and seven opt-in live tests
skipped; 115 additional tests run in-game via `lorekeeper/test`.
Live tests use your authenticated model account and create temporary fixtures.
Run only the relevant bounded check, from **`helper/`**:

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm LOREKEEPER_LIVE_CORRECTION_TEST=1 python3 -m unittest test_chronicle_correction.CorrectionTests.test_live_indexed_correction
```

Other opt-in examples and provenance are in the [test notes](../docs/notes/README.md).
Mock tests do not prove a new game's field layout, account access or visual behavior.

## Legacy developer tools—not the Memoire installation path

- `python3 helper/codex_batch.py INPUT.json OUTPUT.json`: up to 50 deduplicated
  items in one schema-constrained Codex invocation. Inputs contain `id`, `kind`,
  `raw` and optional context. Uses the same model/auth settings as the worker.
- `python3 helper/process_queue.py /path/to/region/lorekeeper-translation-queue.jsonl`:
  process the old token/selected-unit explanation queue; cache defaults beside it.
- `python3 helper/watch_queue.py /path/to/region/lorekeeper-translation-queue.jsonl`:
  watch only that legacy queue. **Does not prepare current Memoires or Chronicles**
  and does not provide the save-directory worker heartbeat.

Do not run these concurrently against files owned by the normal watcher.
`lorekeeper/story` now writes a small view request; it no longer queues a JSONL
history job for `process_queue.py`.

## Optional HTTP API prototype

`helper/server.py` is separate and **not connected to the current in-game readers**.
It binds to `127.0.0.1:8765`, uses a separately provided `OPENAI_API_KEY`, defaults
to `gpt-5-mini`, and exposes `/health` and `/translate`. It uses the Platform API
rather than the Codex sign-in path. No API server/key is needed for the setup above.

For deliberate prototype development only, provide the API key privately in the
process environment and run `python3 helper/server.py`. Other settings are
`LOREKEEPER_HOST`, `LOREKEEPER_PORT`, `LOREKEEPER_MODEL` and `LOREKEEPER_CACHE_PATH`
(default `~/.lorekeeper/translation-cache.json`). Never place keys in documentation,
Lua, save data or Git. Do not expose this prototype beyond localhost.
