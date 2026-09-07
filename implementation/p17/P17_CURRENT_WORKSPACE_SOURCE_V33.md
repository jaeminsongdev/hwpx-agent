# P17 current workspace source qualification v33

Date: 2026-09-07

Scope: exact current-PC Hangul 2020 observed table-shape v2 source successor only

Decision: **qualified source only; actual product-target Hangul readback/PDF, P06-04/P06 phase,
production and product PASS remain false**

The v1-v32 contracts remain byte-for-byte unchanged. This v33 layer composes exact v32 contract
SHA-256 `e386ea8ab4e390c14356c875529765064900d405ca7737bb8f6f2ff509f0e16f`
and binds clean implementation commit
`5adba7d2b1c98f7e2fa87671f321ff6d599dde48`.

Current-host source acceptance run `7783a21d553e45eaab55497fea2b3f1c` passed all 11 checks. Its
canonical receipt SHA-256 is
`2239e1722f4a7df6c4c1f79cb3fc95a318ae6bdbfa5d5e3368d8e4e65ae773e2`. The twenty-six cumulative
successors, locked/offline 25-member Cargo projection and all runtime/production false claims remain
exactly preserved.

The fourteen bound files introduce explicit, non-auto-detected v2 profiles for the exact
`Preview/PrvText.txt` text/plain behavior, table/sub-list ID domains, actual `subList`-first cell
order and inactive stored margin values observed in the bounded Hangul 2020 source. Immutable v1
entry points retain the original rejection and canonical-zero behavior. The target builder selects
all three v2 profiles explicitly, preserves the source, publishes only to a create-new path and
reparses semantic/content identity before returning.

The complete `hwpx-package` test suite passed, targeted Clippy with `-D warnings` passed, both v1
and v2 Python contract suites passed 8/8, and direct inspection accepted both the exact source and
product-generated target under the bound v2 profiles. No dependency was added.

The source capture and product target remain local ignored evidence and therefore are not promoted
by this source qualification. Two product-target Hangul readback attempts timed out at the
user-controlled `open_input` access prompt; both preserved the input, created no output and cleaned
all owned Hangul processes. A fresh user-approved run must prove save/reopen/text/PDF behavior before
P06-04 can close.
