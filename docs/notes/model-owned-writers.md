# Model-owned writers — 2026-09-07

Strategies belong to an explicitly registered model. The router resolves that
model's allowed strategies before preparing prompts or selecting a transport.
Unknown models and cross-model strategies fail before any model call. Adding a
model requires an intentional policy registration and its own strategy tests;
changing a model string does not inherit Qwen's policy.

Supported profiles in `helper/writer_settings.py`:

| Profile | Model | Memoire | Chronicle |
| --- | --- | --- | --- |
| `qwen-fast` (default) | `qwen3:8b` | personal brief | assembled facts with optional reflections |
| `qwen-compact` | `qwen3:8b` | personal brief | compact whole-passage generation |
| `luna-literary` | `gpt-5.6-luna` | full-context passage | full-context passage |

Qwen's anchored annual route falls back to its compact route when there are no
mandatory anchors. Provenance records that actual fallback. `qwen-compact` is an
evaluation option, not a verified improvement over the default.

Luna's preparation lives in `helper/luna_writing.py`: original full context and
translation envelope, no personal-brief compiler or Python annual assembly.
Luna cannot select either Qwen route. Its low reasoning setting stays independent
of interactive Codex. `luna-fast` and `qwen-literary` are unsupported.

Transport adapters accept prepared prompts and schemas. They share process/network
handling, not writing policy. Knowledge filtering, factual coverage and persistence
remain common safeguards. Canonical generation settings include model and strategy
versions and tuning; completed prose records prompt/schema digests and available
model timing metrics. Failed revisions preserve the prior story and its provenance.
Completed annual chapters remain immutable. Dormant books are not bulk rewritten.

Select `LOREKEEPER_WRITER_PROFILE` before starting the worker. Clear conflicting
legacy `LOREKEEPER_PROVIDER`, `LOREKEEPER_MODEL`, and strategy overrides when
switching profiles; mismatches are errors. `LOREKEEPER_WRITER_CONFIG` accepts the
JSON format in `helper/writer_profiles.example.json` for separately tuned profiles
of registered models. Model options and strategy options are validated separately.

Evaluate a captured item with `helper/evaluate_writing.py --profile PROFILE
--output .lorekeeper/NEW-REPORT.json INPUT`. Repeat `--profile` to compare each
model using its own policy. Reports retain private evidence/prose; never commit
them. This evaluator does not publish into game saves. Coverage success does not
prove every narrative claim. Native Windows Luna execution requires an installed,
authenticated Codex CLI; this machine currently has the CLI only in WSL.

Both Linux and Windows suites: 211 tests, 204 passed, seven optional live tests
skipped. Tests cover cross-model rejection, separate prompts/envelopes, tuning,
fallback provenance, and preservation of an existing revision on failure.
Python routing changes require a watcher restart, but no Dwarf Fortress restart.

Bounded live checks using isolated captured items passed: Windows Ollama Qwen
annual 3.30s with all seven required anchors; quiet monthly 2.98s. WSL Codex Luna
full-context monthly 13.04s. The quiet monthly sample has no mandatory anchors;
these are transport/routing checks and single warm timings, not literary acceptance
or a model quality ranking. Diagnostic reports remain under `.lorekeeper/router-*-owned-*`.
