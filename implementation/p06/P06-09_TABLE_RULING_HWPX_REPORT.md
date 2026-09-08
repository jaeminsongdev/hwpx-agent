# P06-09 TABLE-002/003 table ruling HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-ruling-hwpx.hancom-2020/1`
- Model profile: `hwpx-agent.table-ruling/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-002 and TABLE-003 now have preserving direct-HWPX integration evidence for the full domain
operation family. The adapter reads a complete physical grid and edge lattice, preserves exact
cell payload/property/formula/cache state, and lowers full/local draw strokes, both diagonals,
structural shared-edge erasure, transparent nonstructural erasure and separately bound outer-table
creation.

Outer creation replaces only a digest-bound empty top-level paragraph using a validated native 1x1
wrapper. Existing operations relift source state immediately before mutation. Both paths verify
domain plan state/grid/document-flow receipts and return coordinated header/section bytes only after
exact semantic readback.

## Verification

| Check | Result |
|---|---:|
| Dedicated table-ruling HWPX tests | 15/15 PASS |
| Complete reader: physical boundaries, grid, edges, payloads, properties | PASS |
| Outer rectangle with exact insertion/template/native-ID binding | PASS |
| Full row then column strokes and local split | exact static readback PASS |
| Slash diagonal and line-identity resolution | exact static readback PASS |
| Structural merge and row-major payload preservation | exact static readback PASS |
| Nonstructural transparent erasure and borderFill deduplication | PASS |
| Source state/grid, flow, insertion and missing-style drift | fail closed |
| Nonuniform native side and shared-edge disagreement | fail closed |
| Line-only formula AST/cache preservation | PASS |
| Structural formula topology mutation | explicit fail closed |
| Closed package graph, sibling formula/cache and pagination | preserved |
| Non-header/section parts, unselected table and source bytes | exact preservation PASS |
| Determinism and Debug redaction | PASS |
| Focused package Clippy with `-D warnings` | PASS |
| Private contract validator and tamper tests | 4/4 PASS |
| P06 Python suite | 154/154 PASS |
| Workspace all-target/all-feature locked offline tests | PASS; existing isolated P17 PostgreSQL qualification test 1 ignored |
| Workspace Clippy with `-D warnings` | PASS |
| `cargo fmt --all -- --check` and `git diff --check` | PASS |
| Strict matrix/ledger/nonclaim audit | PASS; 61 rows, green 0/61, 120-line ledger |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved
real HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 36 to 34
- direct `integration_passed`: 10 to 12
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

The two rows gain static `semantic_reopen`, `formula_readback` and `page_split` evidence. They still
lack render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence.

## Preserved boundaries

General structural-formula native lowering remains unsupported and is rejected atomically. No
synthetic result is promoted to licensed Hangul 2020 or renderer evidence. Automation projection
remains unverified for all 61 rows and all differential states remain `not_run`. P06-09, P06,
production and the product remain in progress.

The next exact step is another bounded unit-only semantic group or a licensed current-target oracle
for an integration-only row. Recommended reasoning remains `max`.
