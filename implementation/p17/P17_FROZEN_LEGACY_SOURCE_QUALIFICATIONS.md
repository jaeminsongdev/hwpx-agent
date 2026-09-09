# P17 frozen legacy source qualifications

Date: 2026-09-10

Decision: **PASS for immutable verification of the migrated historical source qualifications**

## Closed defect

The P17 Python suite initially ran 178 tests with 31 errors. Historical qualification tests were
re-executing generators and successor-admission helpers against legitimately changed worktree
sources. Typical failures were `contract.exact`, `implementation.bytes`, `current.sources` and a
missing replacement key. None showed that the committed historical qualification bytes had changed.

The migration keeps all original qualification JSON, ignored receipts, generators, reports and
failed evidence unchanged. Historical tests now use three fail-closed readers:

- `frozen_current_source_history_v1.py` follows the exact v39-to-v20 predecessor chain. Each
  contract/current pair is read at the immutable snapshot selected by its successor's `base_commit`;
  implementation, successor and guard blobs plus the seven v20 predecessors are checked there.
- `frozen_local_qualifications_v1.py` checks five exact local daemon, MCP/plugin, main-bound,
  PostgreSQL-checkpoint and widget-preparation contract/current pairs. It validates 86 runtime and
  18 guard blobs at the commits where every recorded lock coexisted.
- `frozen_source_successor_pairs_v1.py` verifies the v12 121-source map at its base commit and ten
  P15 contexts. Historical successor hashes are located only in bounded ancestry of the fixed v39
  anchor, with exact predecessor ancestry and blob digest checks.

All Git operations inherit the frozen-v39 protections: full commit IDs, canonical relative paths,
4 MB bounds, no replace refs, no lazy fetch, no interactive prompt, no optional locks and no
repository-selection environment overrides. Error output is a bounded code, not candidate bytes or
paths.

## Verification result and boundary

The expanded P17 Python suite passes 199/199. Focused tamper tests reject contract, current,
implementation, successor, guard, source-map, context, path and version drift. Black, Flake8 and
Pyright pass for every changed Python file.

This is source-history evidence only. Ignored receipt bytes are not newly verified. No actual
Hangul, registered host, production, remote pull/push, P17 phase or full-product claim is promoted.
The original mutable modules remain historical generation/current-admission tools, not authority for
revalidating old qualification state.
