# P06 table partition v1 to exact-target v2 admission

This is an additive evidence admission. It does not rewrite existing documents or weaken the
`hwpx-agent.table-partition/v1`, split HWPX v1 or join HWPX v1 contracts.

Consumers must validate all three predecessor contracts before accepting
`hwpx-agent.p06-09-table-partition-target-contract/v2`. The v2 contract adds only the exact
current-PC Hangul 2020 save/reopen, typed oracle, renderer and retry evidence for TABLE-010 and
TABLE-011.

The target probe identified Hangul's canonical native wrapper forms. The split lowerer now emits a
trailing empty `hp:t` after each table and a self-closing empty separator run. The join reader
admits that native empty run as exactly one paragraph break. Non-whitespace content, missing
paragraph boundaries, objects, comments and hidden content still fail closed.

There is no automatic migration. Formula-bearing, repeat-header or caption-bearing whole-table
partitioning remains outside this admission. Implementations may not promote automation runtime,
differential equivalence, arbitrary documents, P06 completion, production or product completion
from this exact-target evidence.
