# Lorekeeper background worker

For Windows installation, use the [root README](../README.md#windows-developer-installation).
All commands here run in **WSL from the repository root**, unless stated otherwise.
The active worker uses Python's standard library and a local Ollama server by default.
The worker supports Windows Python as well as WSL. Native Windows uses byte-range
file locks; WSL uses POSIX locks. Do not run both workers on the same save root:
cross-platform lock interoperability is not assumed.

### Native Windows startup (Ollama)

Install Python 3.13 for your Windows user. From PowerShell in the checkout:

```powershell
.\helper\start_watcher.ps1 -Python "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -Check
.\helper\start_watcher.ps1 -Python "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
```

Stop the existing WSL worker before the second command. The launcher runs in the
foreground; Ctrl+C stops it. It accepts `-SaveDirectory` for another installation.
`-Check` only validates imports/arguments, with no save processing. The existing
scheduled-task installer still launches WSL; do not use it for native startup.
Ollama on Windows is reachable at Windows localhost without exposing it to the LAN.
This change needs a worker restart, not a Dwarf Fortress restart.

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
| `LOREKEEPER_PROVIDER` | `ollama` | `ollama` or `codex-cli` |
| `LOREKEEPER_MODEL` | `qwen3:8b` | Local Ollama model, or model accessible to Codex |
| `LOREKEEPER_REASONING_EFFORT` | `low` | Effort accepted by that model |
| `LOREKEEPER_OLLAMA_URL` | `http://127.0.0.1:11434/api/generate` | Local Ollama endpoint |
| `TMPDIR` | `/dev/shm` through wrapper | Temporary structured model output |
| `XDG_STATE_HOME` | `~/.local/state` | Wrapper log parent |

The current model is verified on the development account; availability differs.
To try another account-supported model, set its actual identifier in the WSL
shell before starting the foreground worker. These exports affect that shell's
children, not an already-running task:

```bash
ollama pull qwen3:8b
export LOREKEEPER_PROVIDER='ollama'
export LOREKEEPER_MODEL='qwen3:8b'
export LOREKEEPER_REASONING_EFFORT='low'
```

Ollama must be running on Windows before the WSL watcher starts. The worker
uses JSON-schema output, disables Qwen thinking for latency, and keeps the model
loaded for 30 minutes. To use the previous hosted path, set
`LOREKEEPER_PROVIDER=codex-cli`, choose a Codex model, and verify `codex login
status`.

Ollama uses a 20,480-token context and a 2,048-token output cap. Oversized inputs
and incomplete outputs fail rather than replace a story; prompt truncation and
context shifting are disabled. Repeated evidence records use lossless compact
tables. Two real-save introductions measured 13,730 and 17,282 input tokens;
this does not guarantee that every future request will fit.

Qwen3 non-thinking sampling uses temperature 0.7, top-p 0.8, top-k 20 and min-p 0,
following Qwen's recommendations. The saved `ollama_preset` identifies this
generation version for caching. The Codex effort setting does not enable thinking
in Ollama; Ollama always receives `think: false`.

Preset `qwen3-personal-v7` uses compiled personal facts, relevant chapter context,
and dedicated prose output. Quiet months target 60–100 words, busier months
100–180, introductions 80–140; mandatory facts override length targets. See
[personal brief evidence](../docs/notes/qwen-personal-briefs.md).
The annual strategy introduced in v6 uses dedicated prose
output. Annual requests with mandatory facts assemble those sentences in Python;
Qwen adds optional short reflections in one call. This favors reliable coverage
over fully free literary narration; optional-event/atmosphere prose is currently
limited. See [rewrite evidence and limits](../docs/notes/qwen-writing-rewrite.md).
`evaluate_writing.py` supports explicit, isolated comparisons of captured requests;
store its private reports under ignored `.lorekeeper/`, never in the game save.

On the verified RTX 4070 Laptop setup, `OLLAMA_FLASH_ATTENTION=1` and
`OLLAMA_KV_CACHE_TYPE=q4_0` (Windows user environment, then Ollama restart) permit
100% GPU at 20K context, measured at 5.9 GB. The lower-precision cache trades some
quality for memory; model weights remain Q4_K_M. See
[real-save tuning](../docs/notes/qwen-real-save-tuning.md).
These are Ollama-server settings, not worker settings.
They affect other models served by that Ollama installation as well. Use
`ollama ps` to verify placement; device memory varies with other applications.
When restarting, unload models with `ollama stop qwen3:8b` before closing the
server. Orphaned `llama-server.exe` children can retain GPU allocations; inspect
their exact paths and command lines before stopping any leftover runner.
To restore defaults, remove these two environment variables and restart Ollama.

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

## Model-specific writer profiles

The worker defaults to `qwen-fast`. Set `LOREKEEPER_WRITER_PROFILE=luna-literary`
to select Luna's separate full-context writing policy, or `qwen-compact` to
evaluate Qwen's compact annual alternative. Restart the worker after switching.
Clear conflicting legacy provider/model/strategy environment overrides first.
Luna cannot use Qwen's strategies. See [model-owned writers](../docs/notes/model-owned-writers.md)
and [example tuning profiles](writer_profiles.example.json). Windows Luna needs
an installed, authenticated Windows Codex CLI; the WSL installation is separate.
