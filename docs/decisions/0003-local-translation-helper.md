# ADR-003: Isolate model translation in a localhost helper

**Status:** accepted  
**Date:** 2026-09-06

## Decision

The OpenAI integration runs in a separate local Python process. DFHack Lua
does not contain an API key and does not call the network. The helper uses the
Responses API with `gpt-5-mini`, structured JSON output, `store: false`, a
20-second request timeout, bounded input, and a persistent local cache.

Cache keys include the raw token, context, language, model, prompt version,
and output schema version. Cache misses may call the model; cache hits do not.
The helper binds to `127.0.0.1` by default and returns an explicit offline
error when no key is configured.

## Consequences

- The game remains usable when Python, the network, or OpenAI is unavailable.
- Model explanations are versioned and can be regenerated when the prompt or
  schema changes.
- The first implementation requires a separately launched local process.
- Model output is advisory; raw DF values and deterministic glossary labels
  remain authoritative.
- The DFHack bridge is file-based: `lorekeeper/translate` queues a selected
  snapshot, and `helper/process_queue.py` writes a cache that `lorekeeper/show`
  reads on refresh. This keeps the game independent of the Codex process.
