# DEV-01 validation throughput report

## Result

The local feedback bottleneck is materially reduced without weakening a product
Gate. DEV-01 is a development-infrastructure PASS only. P17 full closure and
P18 production performance remain open.

## Measured evidence on 2026-09-11

| Check | Result | Meaning |
|---|---:|---|
| Direct Git vs batch, 4 paths x 25 | 11.475119 s vs 0.104134 s | identical 2,590,000 bytes; 110.195x for this repeat-read workload |
| Batch process/cache accounting | 1 start, 4 queries, 4 entries, 96 hits | replaces 200 legacy `cat-file` processes in this benchmark |
| P17 development profile | 101 tests / 4.461 s | 22 admitted files passed; 72 closure/replay files explicitly deferred |
| Developer-tool tests | 12 passed | byte parity, bounds, redaction, journal, cache and tier tests |
| Live smoke | 1.483 s | stdout/stderr, 1 s heartbeat, redacted secret and terminal summary observed |
| Patch conflict regression | 3 passed / 0.01 s | 8,000 exhaustive three-range combinations plus 50,000 insertions |
| `sccache` clean-target probes | 4.51 / 4.32 / 4.39 s | 0 cache hits; therefore opt-in, not the default |

The earlier P17 complete suite baseline was 381 tests in 3,164.282 seconds. The
new 397-test run was manually interrupted after about 39 minutes while still
passing, so no 397/397 result is claimed. The fast profile does not replace it.

Two exploratory fast-profile runs also remain non-passing development history:
the first exposed a direct-script import-path defect; the next two were stopped
after 135 and 210 seconds when profiling showed additional qualification/source
replay in the admitted set. The final plan makes these exclusions explicit and
completed in 4.9 seconds including runner overhead.

## Implemented

- `tools/dev/run.py`: no-shell live runner, heartbeat, bounded redacted JSONL,
  atomic truthful summary, failure exit propagation and optional `sccache`.
- `tools/dev/validate.py`: fixed component/development/closure profiles with
  authority labels and fail-fast stages.
- `tools/dev/p17_fast.py`: deterministic 94-file classification; 22 current
  checks/contracts admitted and 72 expensive closure/replay files deferred.
- `tools/dev/git_batch.py`: one-process bounded immutable Git blob reader with a
  4,096-entry/64 MiB cache and repository-environment hardening.
- `benchmark_git_batch.py` and 12 tests cover parity, tampering boundaries,
  redaction, limits, tier separation and measurements.
- `hwpx-package::patch::validate_conflicts` is now sort plus linear sweep instead
  of the prior worst-case quadratic insertion scan.

## Evidence boundary and follow-up

DEV-01 does not stage or modify P17 frozen-lineage source; separate uncommitted
v48 closure work remains outside this checkpoint. The batch reader is not
retroactively treated as historical authority; it is available for the next
independently source-locked successor. No actual HWPX, licensed Hangul, render,
automation, differential, production workload, capacity or P18 SLO claim is made.

Workspace Rust FULL, Clippy with `-D warnings`, format/diff and strict self-audit
passed after the implementation. The local checkpoint records this result, after
which development returns to the next product implementation using the fast
profile during iteration and the complete profile at evidence closure.
