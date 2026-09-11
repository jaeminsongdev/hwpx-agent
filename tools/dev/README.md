# Development throughput tools

These tools shorten the feedback loop without changing a product or evidence
Gate. Logs are written under ignored `tmp/dev-runs/` and are never promoted to
P06/P17/P18 evidence.

## Live command runner

```powershell
python tools/dev/run.py --name p07-math-ast -- `
  cargo test -p domain-ir --test math_ast --locked --offline
```

The runner streams both output channels, emits a periodic elapsed-time
heartbeat, and writes a bounded JSONL journal plus summary. The summary starts
as `running`, so even an ungraceful console/process termination does not look
like a PASS; a graceful exit atomically replaces it with the terminal state.
Persisted text redacts common credential forms and the workspace path. Command arguments
are not persisted; only their count is recorded. Cargo keeps its ordinary
incremental mode by default. `--sccache` opts into the installed cache and sets
`CARGO_INCREMENTAL=0`; this is not the default because the 2026-09-11 clean-target
probe produced zero hits on this PC.

## Fixed validation profiles

```powershell
python tools/dev/validate.py --list
python tools/dev/validate.py --profile dev-tools
python tools/dev/validate.py --profile p17-fast
```

`p17-fast` runs current checks/contracts while excluding qualification, frozen
authority and source-successor replay. It is explicitly development feedback only.
`p17-full` remains the closure test;
passing the fast profile must never be reported as a full P17 PASS.

## Batched immutable Git reads

`GitBatchReader` preserves exact revision/path validation, repository-selection
environment removal, no-prompt/no-lazy-fetch behavior, blob type/size checks and
exact bytes while reusing one `git cat-file --batch` process and an in-memory
per-reader cache bounded to 4,096 entries and 64 MiB. It does not modify the
frozen P17 v39-v48 implementation.

```powershell
$revision = git rev-parse HEAD
python tools/dev/benchmark_git_batch.py --revision $revision --repeats 25
```

Timing output is a developer benchmark, not production performance evidence.
