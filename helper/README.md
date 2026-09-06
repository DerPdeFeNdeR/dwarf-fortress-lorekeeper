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
