# P09-28 public source revision r02: strict documentation lint repair

The first source capsule remains immutable at
`evidence/p09-28-native-form-public-export-source.current-2020.v3.json`,
SHA `41a9f4d1fc27d6d1cf3257d7584582c5e022511258ecaa8081a43755575b2280`.
Its 18 public Rust cases and source/legacy-validator checks passed, but the full
workspace strict Clippy run subsequently failed on the new test's documentation:
`item in documentation is missing backticks`. This is a real failed quality check,
not a source/native/product PASS claim.

Before repairing, preserve the exact first public test in
`source-archive/p09-28-public-attempt01/native_form_hwpx_public.rs` and require
its raw SHA to equal the first capsule's test source pin. r02 changes only that
header comment, adding Markdown backticks around `hwpx_package`; no test body,
production module, public exports, source checker, policy, native corpus,
old authority or assertion is changed. New source hashes require a separate
append-only r02 capsule, not an overwrite or hidden refresh of the first.

Rerun public tests, strict workspace Clippy, full workspace/P09 regressions,
format/diff checks and exact r02 receipt reproduction. The first capsule cannot
be reported as a byte-reproduced current-source receipt after this change.
Both attempts remain non-Gate; no new native session or permission action occurs.
