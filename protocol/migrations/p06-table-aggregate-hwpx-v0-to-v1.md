# P06 table aggregate HWPX v0 to v1

Before this profile, TABLE-022/023/024/026/027/028/029/030 had only the pure bounded aggregate
planner. It produced locale-neutral formula ASTs but did not create or reopen a native HWPX field and
therefore could not supply direct-HWPX integration evidence.

`hwpx-agent.table-aggregate-hwpx.hancom-2020-wrapper/1` adds one preserving adapter for all block,
horizontal and vertical `SUM`, `AVG` and `PRODUCT` combinations. It binds exact source parts,
complete ruling state/grid and before/after document flow, requires a formula-free unmerged source
and exact empty destination, inserts one explicit A1 range field with an unverified decimal cache,
and publishes only after full formula, ruling and pagination semantic reopen. TABLE-025 uses the
same adapter only as a compatibility regression and keeps its stronger independent oracle evidence.

The migration is additive. Existing documents are not rewritten in place, the public legacy formula
profile remains restricted to `SUM(LEFT)`, and sources with merged cells, existing formulas or
nonempty destinations fail closed. Static synthetic XML/package success may not promote the rows to
saved-real-HWPX, licensed Hangul 2020, evaluator, renderer, target-build, rollback/retry, automation,
differential, release, production or product PASS.
