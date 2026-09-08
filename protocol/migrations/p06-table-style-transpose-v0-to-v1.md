# P06 table style and transpose v0 to v1

hwpx-agent.table-style-definition/v1, hwpx-agent.table-style/v1, and
hwpx-agent.table-transpose/v1 are new separately versioned private semantic contracts.

There is no compatible v0 wire representation. Existing documents and prior operation records are
not rewritten or interpreted as v1. A caller must explicitly construct a v1 style definition and
complete v1 request from a validated TableGrid.

The migration boundary is fail closed:

- unversioned style IDs or region maps are not imported;
- partial cell lists are not upgraded;
- implicit merged-cell or band precedence is not invented;
- formula strings are not copied without typed FormulaAst transposition and explicit cache policy;
- no partial plan or receipt is published after any validation failure.

HWPX lowering and current-target execution require separately versioned adapters and evidence.
