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

## Play

Select a dwarf and press **Ctrl+L**, or click **Read Memoire**. Press **U** to
request an update. Run `lorekeeper/chronicles` from the DFHack launcher and press
**D** for a year-so-far Chronicle. The game remains playable while the worker
generates text. Close the worker with Ctrl+C when finished.
