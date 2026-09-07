# Windows Ollama migration — 2026-09-07

The user authorized Qwen3 integration and proceeding with the Windows worker.
Ollama has qwen3:8b, Q4_K_M, digest
500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41.
Windows localhost works; WSL localhost fails even outside the command sandbox.
Windows listener is 127.0.0.1:11434. A real tiny JSON test took 2.86 seconds,
including 2.52 seconds loading. This is not a story benchmark.

Python 3.13 was installed per-user using winget with approval. The native
PowerShell launcher uses the existing Python pipeline and Windows byte-range
locks. WSL keeps flock. Cross-platform exclusion is not assumed; stop the old
worker before migration. Scheduled-task registration remains user-managed.
No DFHack configuration changes are needed. Only the worker needs restarting.

Initial Windows and Linux suites: 178 tests run, 171 passed, 7 opt-in tests skipped.
Final Windows suite after truncated-output regression: 179 run, 172 passed,
7 skipped. Native launcher `-Check` passed against the Steam save root.

Real Windows/Qwen monthly test passed: introduction 25.33 seconds, month 21.14
seconds, cached reopening verified. Real grouped-month annual test failed with
`Chronicle coverage check could not verify: incident:2, incident:3`. Total two-test
runtime was 149.46 seconds. The check failure is not proof of factual omission;
inspect a retained rejected candidate before changing the coverage contract.
The fixture temporary directory was cleaned up by the test, so its rejected
candidate is not available for this run. A diagnostic rerun must retain it.

During generation `ollama ps` reported 7.8 GB, 20%/80% CPU/GPU, 16,384 context.
Local generation is not currently faster than the earlier ~11-second Luna sample.
No live worker cutover was performed because annual validation failed. The WSL
task remained untouched. Game acceptance remains pending.

Follow-up: `qwen-coverage-and-gpu.md` records resolution of the false coverage
rejections, full GPU placement, the direct Qwen prompt, and final passing live
checks. Literary/factual quality on sparse inputs still needs review.

## Live cutover

At the user's explicit request, stopped the WSL task and verified its Python
process exited. Disabling the task required Windows administrator approval; it
is now Disabled. No replacement task was registered. Started native Python
3.13.15 using `helper/start_watcher.ps1`, explicit Ollama/Qwen3 settings and
Windows localhost. Python PID 2520 matches the live save-root heartbeat. Startup
log confirms the Steam save root; error log is empty. Logs are at ignored
`.lorekeeper/watcher-windows.out.log` and `.err.log`. Native startup is manual
after reboot until the user installs a native startup mechanism. No DF restart
needed. Player in-game completion and quality checks remain pending.
Keep previous stories on failures; never claim coverage checks establish every
prose assertion. Original annual immutability and personal-knowledge rules apply.

Ollama defaults to Qwen3 8B, thinking disabled, schema JSON, temperature zero,
16K context, 2K output cap, 30-minute keep-alive. Large real inputs and GPU memory
under play still need validation. Codex is an explicit alternative provider, not
an automatic fallback. Existing WSL startup task must not race the native worker.
