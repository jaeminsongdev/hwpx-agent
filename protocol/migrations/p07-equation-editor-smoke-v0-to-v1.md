# P07 equation editor smoke v0 to v1 migration

There is no stored v0 protocol. P07-06 action-based edit traces, screenshots, manually edited HWPX
files and free-form operator notes are inputs only and MUST NOT be relabeled as
`hwpx-agent.equation-editor-smoke-evidence/v1`.

A v1 run begins with a complete native-equation source snapshot and two normalized `MathAst`
programs. The planner must prove exactly one canonical EqEdit token changes and pin the harness,
oracle, source state and plan. Private plan JSON is reloaded only with its exact file SHA and every
binding recomputed.

Manual screenshots and attestation are combined with automated exact-target preflight,
native readback and close/reopen evidence. Both are mandatory. Existing automation-only edits do
not migrate to editor smoke, and manual screenshots alone do not migrate to native save/reopen.
Failed or effect-unknown runs remain failed history. Target PASS is a new immutable evidence file,
never an in-place promotion of source qualification.
