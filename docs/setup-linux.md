# Linux player setup

Linux is supported by the same Python worker and DFHack scripts. This guide uses
native Linux paths and does not require Windows or WSL. Back up your saves before
testing an early playtest build.

## Install the game integration

Install Steam Dwarf Fortress, a matching Linux DFHack release, Python 3, and
Git. Download this repository into a stable folder such as `~/Lorekeeper`.

Find the Dwarf Fortress installation directory through Steam. Add the checkout's
`dfhack/scripts` directory to DFHack's Linux script path, then add
`lorekeeper/autostart` to `dfhack.init`. Restart Dwarf Fortress after changing
DFHack configuration. The exact configuration location can vary by installation;
use the path reported by your DFHack package if it differs from the usual game
directory.

## Qwen and Ollama (recommended)

Install [Ollama for Linux](https://ollama.com/download/linux), start its service,
and download Qwen3:

```bash
ollama pull qwen3:8b
```

From the repository root, start the watcher with your Linux save directory:

```bash
bash helper/start_watcher.sh "/path/to/Dwarf Fortress/save"
```

Ollama must be reachable at `http://127.0.0.1:11434` unless configured otherwise.
The worker should report the `qwen-fast` profile and `qwen3:8b`.

## Luna and Codex (optional)

Install and authenticate the Linux Codex CLI using the [official instructions](https://learn.chatgpt.com/docs/codex/cli):

```bash
codex --version
codex login
codex login status
```

Select Luna for this worker process:

```bash
export LOREKEEPER_WRITER_PROFILE='luna-literary'
export LOREKEEPER_PROVIDER='codex-cli'
export LOREKEEPER_MODEL='gpt-5.6-luna'
export LOREKEEPER_REASONING_EFFORT='low'
bash helper/start_watcher.sh "/path/to/Dwarf Fortress/save"
```

Qwen and Luna have model-specific writing strategies. The transport and file
pipeline are shared, but Luna cannot select Qwen's writing strategies.

## Play

Select a dwarf and press **Ctrl+L**, or click **Read Memoire**. Press **U** to
request an update. Run `lorekeeper/chronicles` from the DFHack launcher and press
**D** for a year-so-far Chronicle. Keep the watcher running while you play and
stop it with Ctrl+C when finished. Run only one worker for a save directory.

