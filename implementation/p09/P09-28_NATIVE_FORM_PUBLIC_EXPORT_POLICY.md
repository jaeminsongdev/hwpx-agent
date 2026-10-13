# P09-28 native-form public export and source successor policy

Date: 2026-10-02. This advances implementation, not the P09 Gate.

## Allowed delta

Preserve raw P09-23/v2 shared lib, P09-23 bridge tests, P09-27 observation
tests and P09-22 target tests in `source-archive/p09-28-pre-public-export/`
before changing live files. Exact SHA-256 equality is mandatory. Add only
the `native_form_hwpx` module declaration and its explicit public type exports.
The P09-27 production file and pending-export Rust tests remain byte exact.

The public integration successor executes all 18 preceding cases through the
public library imports, without importing/compiling the production file itself.
The new source bridge subtracts both literal export spans and requires equality
with the archived v2 library before checking the v2/v1/P08 projection chain.
Non-export edits, duplicated/missing spans, source/map/receipt tampering fail.
No digest monkeypatch, token normalization, refreshed predecessor capsule,
or source/target/Gate verdict substitution is allowed.

## Historical authorities and live tests

The immutable P09-23/v2, P09-27 pending-export and both P09-22 native receipts
keep their original source pins and meanings. The new verifier validates each
original receipt and every original source: only the four explicitly archived
paths may resolve to byte-exact predecessor files. This is an archived source
check, not a current full predecessor verifier PASS or renewed native evidence.

The old v1/v2 source verifiers and pending-export qualifier must actually reject
the changed current shared lib. Live bridge tests assert the new v3 source chain
and these genuine predecessor failures. Live observation tests preserve their
non-Gate tests and assert the explicit export transition; they cannot claim the
pending-export receipt reproduces against the new live library.

P09-22 mutation tests explicitly use the archived v2 lib and original archived
test file in their disposable historical fixture roots. Every original native,
manifest, source and rejection test remains; this does not qualify new current
exports or alter/refresh native receipts. New source-chain checks cover the live
export separately. All other P08/P09/P17 source/evidence/user changes survive.

## Evidence and next boundary

Run public Rust tests with locked/offline dependencies; require exactly all 18
named tests PASS, zero failed/ignored. Pin before and after execution. Run all
25 actual legacy source validators with raw non-lib locks: the original nine
full-lib failures must remain failures; the other validators must genuinely pass.
Publish a new append-only, deterministic public capsule and reproduce its bytes.
Check workspace tests, Clippy warnings, formatting and diff whitespace.

Only public component linkage/source qualification is claimed. Full package part
bindings, production routing, complete native targets, render, product comparator,
green rows, P09 Gate and P09-P20 completion remain false/NOT_RUN. P10 cannot start.
Prepare all dependency-ready native cases together before dispatch; only the user
handles permission dialogs. No new native session is required for this source step.
