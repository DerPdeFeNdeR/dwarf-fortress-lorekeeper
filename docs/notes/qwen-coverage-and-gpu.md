# Qwen wording and GPU validation — 2026-09-07

The user explicitly authorized relaxing checks for Qwen and moving all model
layers to GPU. The retained synthetic candidate at ignored local path
`.lorekeeper/before-tuning/` failed only on two storytelling lead-ins:
"Urist followed with a tale of" and "Doren, too, recounted the story of".
These preserved teller, subject, office, organization and topic year. Updated
coverage accepts those forms, additional ordinary telling verbs, and a bounded
set of parenthetical transitions directly after the verified teller. It does
not strip arbitrary words or join facts across unrelated sentences. The exact
retained draft now passes all three required events without a model call.

Regression tests still reject changed tellers, years, negation and role reversal.
Live-test checks for nearby organization descriptions and repeated month openings
are now editorial review notes, not assertions. Production prompting still asks
for that context. This is not an exemption for invented events or relationships.

Research:
- https://docs.ollama.com/faq — Flash Attention and q8_0 KV cache, GPU placement.
- https://qwen.readthedocs.io/en/latest/getting_started/quickstart.html — Qwen3
  non-thinking temperature 0.7, top-p 0.8, top-k 20, min-p 0.

Changed Qwen sampling from temperature zero to the recommended non-thinking
values; retain `think:false`. `ollama_preset=qwen3-nonthinking-v3` makes this
generation setting participate in cache identity. Context remains 16,384, output
cap 2,048. No full context-size guarantee for maximal real-save inputs is implied.

Installed Ollama 0.33.3 is using Windows user settings
`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`. Both were originally unset.
q4_0 was briefly tried and reverted. Restarting Ollama left orphaned model-runner
children that retained GPU memory; exact verified children were stopped. The
clean q8_0 server reports **100% GPU**, 6.3 GB, 16K context, **37/37 layers**
offloaded. DF remained running. No LAN listener or firewall change was needed.
The server is currently an explicitly launched hidden `ollama.exe serve`, with
logs under ignored `.lorekeeper/ollama-clean.*.log`. User settings persist across
future app launches; remove them and restart to restore defaults.

Windows and Linux coverage regression batch: 180 run, 173 passed, 7 skipped.
Final prompt adds one regression (181 total). The first full-GPU monthly check
hit its 2,048-token limit. Retained diagnostics showed repetition in explanation,
not thinking tokens. The final Ollama prompt presents instructions directly,
preserves request metadata and evidence, and requests a one-sentence explanation.
Full-GPU retained monthly test then passed (including cached reopen): intro 9.71s,
month 10.25s. Final retained Chronicle published ready with all three factual
checks in 7.04s. No correction was needed. Earlier mixed-device Chronicle: 69.45s.

Quality limitation: the sparse introduction still invented length of service
and a personality from occupation despite the instruction against doing so.
The monthly tests check format, first-person voice and cache behavior, not every
assertion. The final Chronicle is accurate but plain and lacks organization
descriptions; these now remain explicit editorial review notes. Do not present
passing automated checks as factual or literary player acceptance. The existing
WSL worker has not been replaced during this tuning task.
No production story was changed by these isolated checks.
