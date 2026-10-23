# P08-22 object automation binding overlay policy

## Scope

This task builds a P08-only restricted derivative from the pinned P02 official automation records
and candidate graph. It covers all 42 P08-owned `OBJ` rows. P11-owned chart/media rows remain owned
by P11 even though their existing source candidates remain visible in the aggregate projection.

## Admission

A source candidate requires one exact official record and one exact candidate-graph node with
matching source identity. Shared Actions are allowed only as feature-specific parameter or context
candidates and require separate runtime probes. A source candidate does not prove that the Action
is enabled, nonmodal, executable, semantically correct, or safe for routing.

Known-modal routes are excluded from an unattended batch until they pass isolated probes. Routes
marked `must_probe` are also excluded from mutation until a surface inventory proves the exact
context and nonmodal execution path. No raw Action or ParameterSet identifiers appear in the public
contract or aggregate projection.

`OBJ-044` remains unavailable by P08-21. `OBJ-046` is unavailable because the official ShapeObject
automation surface has no exact per-object printable field; global print-image/drawing options are
not equivalents.

## Claim boundary

The overlay advances only source mapping. Runtime support stays unverified, routing stays disabled,
differentials remain not run, and no row becomes green. No HWP process or document is touched by
this task.
