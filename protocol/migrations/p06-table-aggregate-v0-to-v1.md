# P06 table aggregate planner v0 to v1

Date: 2026-09-08

`v0` had a general locale-neutral `FormulaAst`, but no typed operation bound block, horizontal or
vertical table selections to the nine aggregate capability identifiers. Callers could assemble an
AST manually without proving that the source range was ordered, outside the destination and on the
declared axis.

`hwpx-agent.table-aggregate/v1` is additive. It binds exact table dimensions, source range,
destination, axis and function, then returns a bounded `FormulaCell` plan with absent cache and
general format. Horizontal ranges must be strictly left and vertical ranges strictly above; invalid
or self-referencing requests are not coerced and return no plan.

This migration may not promote HWPX syntax compatibility, calculated cache correctness, licensed
Hangul 2020 behavior, automation, differential, release, production or product claims.
