# Lorekeeper local translation helper

This optional service keeps the OpenAI API key outside DFHack Lua. It binds to
localhost, translates one bounded token request at a time, and persists only
successful structured results in a local cache.

## Run

From this directory:

```bash
export OPENAI_API_KEY='your-key'
python3 server.py
```

The default endpoint is `http://127.0.0.1:8765`.

```bash
curl http://127.0.0.1:8765/health
curl -X POST http://127.0.0.1:8765/translate \
  -H 'Content-Type: application/json' \
  -d '{"kind":"thought","raw":"SatisfiedAtWork","context":"emotion=SATISFACTION"}'
```

Configuration:

- `OPENAI_API_KEY`: required for cache misses; never placed in DFHack files.
- `LOREKEEPER_MODEL`: defaults to `gpt-5-mini`.
- `LOREKEEPER_CACHE_PATH`: defaults to `~/.lorekeeper/translation-cache.json`.
- `LOREKEEPER_HOST` and `LOREKEEPER_PORT`: default to `127.0.0.1:8765`.

Run the offline tests with:

```bash
python3 -m unittest discover -s . -p 'test_*.py'
```

The helper is not yet called by the in-game window. That integration remains
separate so the DFHack render loop never waits on a network request.

## Codex CLI batch backend

If Codex CLI is already authenticated with ChatGPT, queued translations can
be processed without an API key. Put a JSON array of pending items in a file:

```json
[
  {"id":"thought:SatisfiedAtWork","kind":"thought","raw":"SatisfiedAtWork"},
  {"id":"emotion:SATISFACTION","kind":"emotion","raw":"SATISFACTION"}
]
```

Then run one bounded batch:

```bash
python3 helper/codex_batch.py pending.json results.json
```

The command deduplicates equivalent requests, sends at most 50 items through
one `codex exec --ephemeral --sandbox read-only` invocation, validates the
structured response, and writes `results.json`. It does not edit the
repository or send dwarf names/IDs unless they are explicitly included in a
request item.

For the DFHack queue, process the game-generated JSONL file and write the
cache that `lorekeeper/show` reads:

```bash
python3 helper/process_queue.py \
  /path/to/save/region3/lorekeeper-translation-queue.jsonl
```

Repeat the command whenever new jobs are queued. It skips IDs already present
in the result cache and writes that cache beside the queue. An explicit second
path is still supported when needed.

For the hands-off workflow, run the background watcher instead:

```bash
python3 helper/watch_queue.py \
  "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dwarf Fortress/save/region3/lorekeeper-translation-queue.jsonl"
```

It checks for new jobs every five seconds, retries processing failures, and
writes results beside the queue. Use `--once` for a bounded test run.
