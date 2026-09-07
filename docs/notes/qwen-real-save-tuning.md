# Real-save Qwen tuning — 2026-09-07

The player reported "Writing monthly chapters in the background" without updates.
The native worker subsequently failed Minkot's request with incomplete output,
and Tun's with an incorrect result count. A read-only DFHack RPC inspection
confirmed the open reader had received its matching failed request and displayed
the failure; its polling was working. Previous saved prose remained intact.

Ollama logs showed real prompts of 16,551–23,970 tokens truncated to 8,194.
The installed Ollama 0.33.3 implementation defaults to truncation and uses half
the context as its prompt limit while context shifting is enabled. The model
therefore lost the beginning of the request, including instructions and IDs.
Sources: [runner implementation](https://raw.githubusercontent.com/ollama/ollama/v0.33.3/llm/llama_server.go),
[generate API](https://raw.githubusercontent.com/ollama/ollama/v0.33.3/api/types.go),
[route defaults](https://raw.githubusercontent.com/ollama/ollama/v0.33.3/server/routes.go).

Preset `qwen3-nonthinking-v4` now:

- Presents instructions directly and packs repeated JSON objects into tables.
  Uniform rows share column names; mixed shapes reference a field schema by
  zero-based index. All values, ordering, Unicode, missing fields and nulls remain.
  Raw saved profiles and semantic cache inputs are unchanged. Both captured
  real inputs passed an exact decode roundtrip; regression tests cover both forms.
- Sets `truncate:false` and `shift:false`. Oversized input fails explicitly;
  incomplete output also fails while retaining old prose. A real 18,087-token
  request at 16K verified the input rejection before context was increased.
- Constrains the JSON results array to the exact requested length and its IDs
  to supplied IDs. Existing post-validation still checks order and required fields.
- Uses 20,480 context and 2,048 output tokens, non-thinking mode, unchanged
  Qwen non-thinking sampling. Generation version participates in cache identity.

20K with q8_0 cache offloaded only 35/37 layers. Windows user settings now use
`OLLAMA_FLASH_ATTENTION=1` and `OLLAMA_KV_CACHE_TYPE=q4_0`; the clean server
verified 37/37 layers, 100% GPU and 5.9 GB while DF was running. Quantized KV cache
can reduce quality; this is a memory tradeoff, not a change to Q4_K_M model weights.
See [Ollama's cache guidance](https://docs.ollama.com/faq). These settings persist
and affect the Ollama server's other models. The current explicitly launched
server writes ignored `.lorekeeper/ollama-20k.*.log`; no LAN exposure was added.

Final compact real introductions measured 13,730 tokens for Minkot and 17,282
for Tun. Tun returned a valid batch in 28.26s. In a separate local directory,
Minkot's full monthly pipeline reached ready with no pending chapters. Introduction
and newest month took 21.04s and 19.98s; older chapters approximately 17–22s.
One failed attempt was not retained and is not counted as a diagnosed wording
failure. Subsequent captures retained exact request/result pairs. Malachite's
retained response said "I have heard" instead of "I heard", preserving all
remaining required words. The bounded tense alternative now passes that candidate
without regeneration; tests still reject negation and changed teller/year/reaction.
Final runner logs reported `truncated = 0`.

Windows Python 3.13 and WSL regression suites each ran 184 tests: 177 passed,
seven opt-in live tests skipped. The real-save checks above were separate live
Windows/Ollama runs, with output stored only under ignored `.lorekeeper/`.
No diagnostic story was copied into game saves and no raw game record was changed.
The old worker was paused during tuning to prevent outdated truncated requests.
The tuned native worker was restarted (checkpoint PID 30224, launcher 12712),
with an advancing save-root heartbeat and empty `.lorekeeper/watcher-tuned.err.log`.
Failed requests need U in Memoire to request fresh preparation.
No Dwarf Fortress restart is needed.

Limits: this is evidence for these captured requests, not all possible profile
sizes or model responses. The generated prose still sometimes invents occupation
routines or unsupported setting details. Mandatory event checks do not establish
the truth of every sentence. Player-facing completion and narrative quality remain
to be verified in the live reader. No new startup task or commit was created.
