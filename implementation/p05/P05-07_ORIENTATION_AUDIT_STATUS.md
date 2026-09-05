# P05 orientation/spine audit status and continuation

- Date: 2026-09-05; implementation checkpoint `9f493a5fef097e6b1a232ea8e2b16408e6a2ed51`.
- Goal/card status: active/in progress, not complete or blocked.
- This file records audit progress after the checkpoint report; do not infer completion from launch.
- Only documentation may change while these audits run; keep implementation bytes at this checkpoint.

## Verified results

Windows package all-target tests: 193 passed, zero ignored; all-target/all-feature Clippy passed.
The same package's actual Linux all-target tests: 193 passed; Clippy with warnings denied passed.
Linux session 57646 is terminal exit 0. The named temporary container is absent after automatic
removal. It used the pre-existing pinned Rust 1.96.0 image
`sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`, network none, read-only
root/source/Cargo registry, dropped capabilities, no-new-privileges, 4 GiB memory and 3 GiB temporary
build filesystem (1.8 GiB used). No toolchain update, installation or test suppression occurred.

| Main checkout log under artifacts/p05-orientation-repair | SHA-256 |
|---|---|
| package-final.log | 5f9a260cfc16f391f1c4720b262399a507aed992c1507aa2d0aad813686bfdc9 |
| orientation-before.log | 62321c054e4801feba0a2527fc9efec9beacbe60a2ae84401d194b0dffc79d95 |
| spine-before.log | 9f19ac066827965270fa9ec3d5bf82a13316afa0479e274f0bd5d968424f0c80 |
| linux-offline-9f493a5.log | 39c795b17c45ca19266a1765959ba3473d00325a2d4b340cdeccb525f24222ea |

## FULL audits: live handles, not terminal results

1. Current checkout `D:\개발\hwpx-agent`, session **84430**, still live on last tool observation.
   `artifacts/p05-orientation-repair/full-current-9f493a5.log`: Rust, Windows worker and widget
   lanes passed into the docs lane; latest output advanced through all P14 contract validators
   to `python -m unittest discover -s tools/p14/tests -p test_*.py`. Security/overall result pending.
2. Exact clean detached checkout `D:\개발\hwpx-agent-audit-p05-orientation-9f493a5`, retry session
   **81116**, still live on last observation. `full-independent-retry02-9f493a5.log` in the same
   artifact subdirectory. It also reached the P14 unittest suite in docs. Four exact digest-pinned
   diagnostic JSON records were copied to ignored paths; no user documents or keys were copied.
3. First independent session **71568** is terminal exit 1. Do not poll/restart that handle.
   `full-independent-9f493a5.log` SHA-256:
   `b19688f4e72002c2dc16e4cd664358af5021820f4238e75b9d9b9ef805bf9676`.

Recheck 84430 and 81116 with their existing handles. An observation timeout is not termination.
Do not start another FULL run merely because the docs lane is slow. Both implementation trees
were clean at the last source check, before this audit-status documentation update in main.

## First independent failure: retained, not explained away

The existing C# smoke `HardCommandTimeoutRecyclesAndReplaysUnknownAsync` failed its compound
assertion at Program.cs:1029: `hard timeout left its actual owned process tree running`.
That assertion requires both a non-null asynchronously published process-ID receipt and absence
of the two recorded processes. Its message does not distinguish a missing receipt from live
processes. The executor reads that receipt asynchronously while its one-second command timeout
can initiate cancellation/recycling. A publication/timing race is plausible, not proven.

Post-failure process inspection found no matching test process or Hwp process. The unchanged
compiled C# smoke was then executed three times sequentially: all three passed 32/32. Session
42848 is terminal exit 0; `worker-smoke-recheck-1.log` through `-3.log` remain in the independent
checkout. No timeout, assertion, production code or test was changed. The failed run remains
failed; these retries do not retroactively establish its cause or eliminate the reproducibility risk.
The new FULL retry started only after the failed run and all three probes were confirmed terminal.

## Remaining next work

- Finish the two live FULL audits before a closure decision. Record terminal results and hashes.
- If the worker assertion repeats, separate the missing-receipt and live-process diagnostics and
  repair the actual readiness/termination race with deterministic coverage; do not increase a
  timeout or drop an assertion simply to get a pass. Track uncertainty even if the retry passes.
- Resolve P05-07 column-ID normalization offline. Locked KS X 6101 section 10.7.1.1 identifies
  `colPr/@id` as a column-settings identifier. The product ID index explicitly indexes nonempty
  column IDs and only treats empty current-profile IDs as absence. Thus globally ignoring IDs
  would weaken preservation; do not do so. Actual attempt21 shows both synthetic IDs became empty.
- Read `P05-07_COLUMN_ID_ADMISSION_PLAN.md` for the checked existing identity/normalization contracts
  and the next bounded diagnostic implementation. This design note is not an implemented remap.
- Fresh actual landscape output remains unverified. No automatic Hangul relaunch or UI input.
- Preserve the separate dirty P16 PostgreSQL adapter work. Its failed empty rollback remains the
  next durable-source integration issue; this P05 audit does not qualify that code.
- Recommended reasoning: max for preservation, process ownership, normalization and final Gates.
