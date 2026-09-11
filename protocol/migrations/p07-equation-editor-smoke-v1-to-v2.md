# P07 equation editor smoke v1 to v2 migration

Licensed Hangul 2020 observations showed that native-editor serialization is not a stable
pre-edit boundary. One run exposed `x+1` after opening the editor, while a later screenshot still
showed the stored compiler form `{x} + {1}` immediately before the operator changed the digit. Both
runs saved the semantically requested result as `x+2`. The persisted source, canonical planned
edit and exact saved native script therefore MUST NOT be collapsed or ordered as a deterministic
three-step raw-script transition.

V2 binds the canonical compiler before and after scripts generated from the two round-tripping
`MathAst` values. Exactly one canonical token fingerprint must differ between those planned
scripts. It separately binds the raw `saved_after_script` and digest observed for the exact target;
that raw script must parse to the planned after semantic state but need not equal the canonical
compiler spelling. The complete source artifact/graph/flow/anchor/object/semantic/script state
remains independently bound and immutable.

V1 plans and evidence do not migrate. Missing v2 fields fail JSON admission, and relabeling a v2
shape as v1 fails the version check. Attempts 06 through 09 remain failed or discovery evidence:
06 overwrote its disposable input, 07 exposed saved-script canonicalization, 08 exposed the
non-deterministic pre-edit serialization boundary, and 09 lacked the mandatory four screenshots.
A v2 PASS requires one new hash-pinned plan, complete manual screenshot/attestation set and
automated save/reopen evidence. No predecessor receipt, screenshot or verbal permission is
promoted.
