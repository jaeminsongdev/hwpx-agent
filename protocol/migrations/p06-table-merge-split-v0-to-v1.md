# P06 table merge/split v0 to v1

P06-03 introduces the private `hwpx-agent.table-merge-split/v1` contract over the immutable
`TableGrid` and P06-02 table-operations prerequisites. There was no accepted v0 wire format.

Callers must construct an exact grid-bound `TableContentState` and choose an explicit
`ContentPreservationPolicy`. Legacy or ad-hoc merge behavior without a complete rectangular slot
set, exact content ownership and policy is not migrated automatically and must fail closed.

Merge retains the top-left master identity. `concatenate` and one-destination `distribute` preserve
all content in canonical order; `reject_if_multiple` blocks ambiguous multiple nonempty sources;
`first` is explicitly lossy and receipts every discarded content-block ID.

Split operates only inside an evenly divisible existing span, retains the source identity at the
top left and requires exact caller IDs for remaining parts. `distribute` uses contiguous balanced
chunks. Other policies keep all blocks in the first result and split never discards content.

No compatibility alias, default policy, silent rectangularization, implicit grid expansion,
partial-span fallback, backend identifier, HWPX XML or desktop action is accepted. Later changes
require a new version, migration and negative tests.
