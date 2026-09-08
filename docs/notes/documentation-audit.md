# Documentation audit — 2026-09-07

Scope: documentation against published implementation `8dd7a66`; no runtime
changes, task registration, game configuration edits or model regeneration.

## Changes

- Root README now describes Memoires/Chronicles and Windows developer setup,
  with separate PowerShell, WSL and DFHack commands, first foreground-worker
  test, optional logon task, updates, privacy and troubleshooting.
- Corrected helper/DFHack guides and model-boundary documentation: current
  prepared-file readers are not the old JSONL queue or optional HTTP prototype.
- Explicitly separated DFHack collection startup from Windows-logon worker
  startup. Registration does not start a task; Ready does not mean Running.
- Updated roadmap, schema map and handoff to the published checkpoint. Older
  notes/architecture sketches remain historical evidence, not current setup steps.
- Worker installation guidance was checked against current provider
documentation and local code. Current model/effort comes from runtime code;
account access is not guaranteed for every environment.

## Verification and limits

The PowerShell installer's `-WhatIf` check passed on the existing Windows/WSL
setup, converting project/save paths and constructing the action without task
registration. This does not validate a fresh user's permissions, login or model
access. Watcher `--help` and wrapper shell syntax checks passed without starting
another worker. Local Markdown links and referenced headings resolved across
50 Markdown files; `git diff --check` passed. Published test evidence remains
169 Python passes / seven opt-in
skips, and 115 actual DFHack passes; documentation work does not claim a new
gameplay regression run.

A clean-machine installation, natural annual rollover and extended gameplay
limits remain unverified. The audit did not run dependency installers, change
credentials, restart the task, or interrupt the player's fortress. No DF restart
is required for these documentation changes. Publication requires separate approval.

[current setup](../../README.md),
[Microsoft WSL installation](https://learn.microsoft.com/en-us/windows/wsl/install),
[DFHack configuration](https://docs.dfhack.org/en/stable/docs/Core.html#configuration-files).
