# P09-17 Field auto-number target policy

Status: `HISTORICAL LIFECYCLE PASS / THREE OBJECT-NUMBER SEMANTIC FAILURES / NON-GREEN`.

## Scope and immutable inputs

This qualification consumes only the named disposable P09-17 fixture and its existing two-session
target attempt. It performs no COM call, opens no user document, invokes no network, and does not
change the private attempt. A successor public record is written with exclusive-create semantics.

The target is licensed Hancom Hangul 2020 `11.0.0.9136`, x86, `ko-KR`, on this PC only. The fixture
manifest and lifecycle trace require caller-supplied SHA-256 locks. Input, saved, reopened and PDF
files must match their declared hashes and byte lengths. The saved/reopened packages are inspected
independently from the trace; a trace marked `pass` cannot authorize semantic promotion.

## Structural and semantic separation

`inspect_field_auto_number_target.py` v2 reports `structural_only` when no expected projection is
supplied. With expectations, it compares ordered PAGE/PICTURE/TABLE/EQUATION numeric values and
reports `semantic_projection_mismatch` when any differ. Package hash verification and ZIP inspection
consume one bounded byte snapshot. Links, invalid member identities, excess ZIP expansion, active
XML constructs, comments, stray format text, unknown attributes and noncanonical numbers fail closed.

`qualify_field_auto_number_target.py` binds the exact fixture v1 expectations `9/2/3/4`, the five
operation identities and their state/section hash chain, the final input projection, target identity,
security preflight, independent save/reopen process identities and output hashes. Changed expected
values, duplicate JSON keys, stale artifacts and boundary escapes are rejected.

The qualifier records the PAGE insertion, three object-number insertions and numeric PAGE update as
separate cases. A preserved PAGE cached value proves only preservation of that value. It does not
prove application-owned reference recalculation, a page-count algorithm, rendering or automation.
Native object counts and caption ancestry are observations, not proof of a valid object binding.

## Gate and source boundary

All cases remain `non_green`. Even matching cached values yield only `partial_non_green` until the
required product evidence exists. A lifecycle pass with mismatching values yields
`failed_semantic_non_green`. PDF signature/hash validation never qualifies rendered content.

The P09-11 matrix remains the conservative static-section inventory: 46 P09-owned rows, 7 P11-owned
deferred rows, 35 unit rows, 11 integration rows and zero oracle/green rows. This failed, bounded
target experiment must not be used to replace the matrix's row-level evidence requirements.

Current P08 source validation is independently held by a stale whole-file `lib.rs` digest. Keep the
historical P08 receipts and this failure; do not refresh old evidence or claim that the live P08
aggregate passed. Do not start P10 before the authoritative P09 Gate closes.

## Next execution boundary

Reuse the field-domain/section adapter and the existing object adapters to implement source-qualified
object/caption association and application-owned numbering expectations. Collect a new fixture and
a new attempt only after preflight and source identity qualification. Stop and pause the goal before
any new validation that needs the user to press Hangul's access-allow button, as requested.
