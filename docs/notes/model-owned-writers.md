# Model-owned writers — cleanup profile set

This branch keeps a single active writing configuration for cleanup testing:

- Active profile: `qwen-thread` in `helper/writer_settings.py`
- Active model: `qwen3:8b` (Ollama provider)
- Strategy map: Memoire → `personal-thread`, Chronicle → `anchored-stream`

Router behavior is strict: model + strategy combinations are validated before any
model call. Unsupported combinations now fail during settings resolution.

## Legacy profiles

Legacy experimental profiles are removed from runtime registration.
Only `qwen-thread` is active in this branch.

## Worker and diagnostics

Profile and tuning selection comes from `LOREKEEPER_WRITER_PROFILE` and
`LOREKEEPER_MODEL_OPTIONS` (plus strategy options), with optional tuning via
`helper/writer_profiles.example.json`. Invalid mixed-provider or cross-model
settings fail before invocation.

`helper/evaluate_writing.py` still supports explicit comparison runs, but only
with the active `qwen-thread` route in this cleanup mode.
