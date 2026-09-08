# P06 table properties v0 to v1

hwpx-agent.table-properties/v1 is a new private semantic contract for TABLE-007, TABLE-008 and
TABLE-009.

There is no compatible v0 wire representation. Existing documents and operation records are not
rewritten or interpreted as v1. A caller must construct a complete v1 state and an exact state-bound
request from a validated TableGrid.

The migration boundary is fail closed:

- arbitrary property maps, raw XML and desktop parameter identifiers are not imported;
- partial, duplicate or coordinate-mismatched master-cell lists are not upgraded;
- unordered slot input is canonicalized; duplicate, out-of-grid and partially merged selections are
  rejected, while the unified operation additionally rejects non-rectangular selections;
- preserve, clear and set remain distinct and missing intent is not invented;
- per-cell and unified-selection edge topology is never inferred from a legacy boolean;
- no partial plan or receipt is published after any validation failure.

HWPX lowering and current-target execution require separately versioned adapters and evidence.
