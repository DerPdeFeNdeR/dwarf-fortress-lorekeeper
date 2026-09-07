# Windows player setup

This is the simplest supported setup. It runs the Lorekeeper watcher with
Windows Python and keeps model work outside Dwarf Fortress. Back up your saves
before testing an early playtest build.

## Install the game integration

Install Steam Dwarf Fortress and a matching DFHack release. Download this
repository into a stable folder, for example `C:\Users\YOUR_NAME\Lorekeeper`.
Install Python 3.13 for Windows if the `python` command is unavailable.

In the Dwarf Fortress installation directory, edit `dfhack-config\script-paths.txt`
and add the full Windows path to the checkout's `dfhack\scripts` directory:

```text
+C:\Users\YOUR_NAME\Lorekeeper\dfhack\scripts
```

Then add `lorekeeper/autostart` to `dfhack-config\init\dfhack.init`. Restart
Dwarf Fortress after changing these files.

## Qwen and Ollama (recommended)

Install [Ollama for Windows](https://ollama.com/download/windows), start it, and
download Qwen3:

```powershell
ollama pull qwen3:8b
```

From PowerShell in the Lorekeeper checkout, start the native worker:

```powershell
.\helper\start_watcher.ps1 -Python python
```

Keep this window open while playing. The worker should report
`writer ollama / qwen3:8b`. Run only one worker for a save directory.

## Luna and Codex (optional)

Install the Windows Codex CLI using the [official Codex CLI instructions](https://learn.chatgpt.com/docs/codex/cli),
then authenticate it in PowerShell:

```powershell
codex --version
codex login
codex login status
```

In the same PowerShell window, select Luna and start the worker:

```powershell
$env:LOREKEEPER_WRITER_PROFILE = 'luna-literary'
$env:LOREKEEPER_PROVIDER = 'codex-cli'
$env:LOREKEEPER_MODEL = 'gpt-5.6-luna'
$env:LOREKEEPER_REASONING_EFFORT = 'low'
.\helper\start_watcher.ps1 -Python python
```

Windows and WSL Codex installations have separate login state. Luna's writing
strategy is separate from Qwen's strategy.

## Play

Select a dwarf and press **Ctrl+L**, or click **Read Memoire**. Press **U** to
request an update. Run `lorekeeper/chronicles` from the DFHack launcher and press
**D** for a year-so-far Chronicle. The game remains playable while the worker
generates text. Close the worker with Ctrl+C when finished.

