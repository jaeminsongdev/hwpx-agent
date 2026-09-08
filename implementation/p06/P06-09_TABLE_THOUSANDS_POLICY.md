# P06-09 table thousands-format planner policy v1

Status: pure bounded component implemented; no HWPX or Hangul 2020 oracle claim

## Scope

This policy covers the locale-neutral grouping-flag boundary for two table capabilities:

- `TABLE-032` / `table.thousands_add`
- `TABLE-033` / `table.thousands_remove`

The operation applies only to an exact, nonempty selection of validated formula cells whose current
format is `Number`. It does not parse or rewrite visible cell text and does not infer a numeric
format from `General`, `Percent` or `Scientific`.

## Semantics

Every request binds exact nonzero table dimensions, one mode and a finite set of zero-based cell
coordinates. Selection order is canonicalized, while duplicate or out-of-bounds coordinates fail
closed. The supplied formula cells must match that selection exactly: missing, extra and duplicate
owners are rejected before a plan is returned.

`add` sets only `use_grouping=true`; `remove` sets only `use_grouping=false`. Existing decimal
places, owner coordinate, formula AST and cache state/value remain exact. Applying the same mode
again is idempotent.

## Safety and determinism

- Request JSON is exact `hwpx-agent.table-thousands/v1`; unknown and duplicate keys fail closed.
- Dimensions, coordinates, selection cardinality and serialization are bounded by caller-supplied
  `FormulaLimits`.
- Every reconstructed formula cell is revalidated against the request's exact dimensions.
- Mixed unsupported formats or selection mismatch return no partial plan.
- Canonical plan JSON and SHA-256 are deterministic; Debug output redacts formatted cells.

## Evidence promotion rule

Passing Rust and contract/tamper tests promotes only TABLE-032 and TABLE-033 to
`component_only / unit_passed` with `schema` evidence. It cannot promote direct HWPX integration,
formula or cache readback from an artifact, page split, render diff, licensed Hangul 2020
target-build, automation, differential exact match, release-enabled, P06-09/P06 PASS, production
or product completion.

The next boundary is a preserving HWPX number-format adapter based on exact native source evidence
from the current licensed Hangul 2020 target. Recommended reasoning remains `max`.
