# P16-06 composed source and clean-room audit

- Date: 2026-09-06; review STRICT / risk HIGH; recommended reasoning `max`.
- Audited code commits: `cd9437f0c9972eeea125228476aba77a7e7d1f1b` and clean-room repair
  `0b484bf`.
- Decision: composed P14/P15 source qualification and isolated P16 plan-review component PASS;
  P16 phase completion, registered host, real service execution and actual Hangul remain open.

## Source qualification

The immutable predecessor contracts were not rewritten. The P16 successor admits only declared
predecessor/current SHA-256 pairs after verifying fixed historical Git blobs, eleven predecessor
contracts, the PostgreSQL successor contract and its two actual-runtime receipts. It exposes ten
context-specific replacement maps and retains `phase_complete: false`.

The source qualification checks passed in both the implementation checkout and a detached clean
checkout at `0b484bf`. Mutation coverage includes predecessor/guard/runtime drift, history mismatch,
extra paths, claim promotion, missing contexts, no-overwrite publication and foreign Python module
cache isolation.

The underlying actual PostgreSQL P14 harness remains bound to runtime-source commit `eb5674e`:

| Evidence | Receipt SHA-256 | Log SHA-256 |
|---|---|---|
| current checkout | `1c070cae73afc22aa46e7d7e9a0746aebbd7a973888933350e3f34ae11db1c5b` | `7b2d975f2afb46bf3ee19e3de05367a5d358ff6c618c3494f699945f2a58d583` |
| independent checkout | `c2b7f1d4cbfd1ae8863c3790667775d879a96c3ed9e3be3a45e60e0f488e3e34` | `cacdbbbf021752146ccdf8cd5741435ec46168f7a86e22e581b3774f1b62b0df` |

Both receipts report migration, reapply, smoke, rollback and security PASS; their disposable
containers were removed. Later P16 commits do not change any of the 21 bound runtime-source bytes.

## Current and independent validation

| Check | Implementation checkout | Detached clean checkout |
|---|---:|---:|
| P14 Python regression | 132/132 PASS | 132/132 PASS |
| P15 Python regression | 84/84 PASS | 84/84 PASS |
| P16 Python regression | 129/129 PASS | 129/129 PASS |
| plan-review widget | 126/126 PASS | 126/126 PASS |
| plan-review policy tests | 16/16 PASS | 16/16 PASS |
| local AppBridge call order | 5/5 PASS | 5/5 PASS |
| source/plan contract checks | PASS | PASS |

The implementation checkout also passed relevant Rust tests 110/110, workspace format, Clippy with
warnings denied, and all five repository CI lanes. The security lane reported zero failed checks,
zero forbidden licenses, 813 SBOM components and no secret findings; the final direct scan covered
1,065 files with zero findings. All thirteen current response screenshots were inspected at original
resolution and are digest/size locked by the plan-review policy.

## Failed evidence preserved

The first detached run at `cd9437f` failed with `predecessor.validation:bundle.read`: the plan-review
runner built its own bundle but relied on an already-existing continuity predecessor bundle. The
runner now builds that predecessor first, and a regression requires this order. A brand-new detached
checkout at `0b484bf` then passed the same plan-review runner from dependency restore onward.

An attempted parallel P14/P15/P16 run in one checkout was discarded. All three processes shared the
same mutable ignored `web/plugin-widget/dist/` tree; failures observed while that tree was absent are
not treated as product or Gate evidence. Sequential clean-room reruns preserved 125 generated files
across P15 and produced the PASS counts above. Future independent validation must serialize suites
that share generated output or allocate separate checkouts per suite.

## Remaining boundaries

This audit does not qualify authenticated stored-plan projection, a registered ChatGPT/Codex host,
remote MCP, durable production authorization/idempotency, real document mutation, Hangul/COM,
assistive technology, another PC, or Hangul 2022/2024. The exact next implementation work is P16-06
authenticated stored-plan projection and registered-host integration. Actual Hangul 2020 should be
launched only when that later acceptance explicitly reaches the desktop worker boundary.
