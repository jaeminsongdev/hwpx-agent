# P09-18 object-caption composition, source successor v2

The v1 predecessor is preserved, including original implementation/tests/validator
bytes in the hash-bound `p09-18-object-caption-source.20261002-r01.snapshot.json`.
This policy and the new v2 contract/qualification are the current source authority.

All v1 typed-state, selector, source/object/caption/plan hashes, bounded allocation,
preserving splice and no-fallback rules still apply. An existing caption is required.
P09-16's numeric adapter and the public Rust profile/wire plan remain unchanged.

## Exact namespace admission

An ancestor namespace declaration is allowed only when its declaration name and
semantic URI exactly equal the declaration already present on the original root.
Such redundant declarations remain byte-exact in the original object. A new prefix,
different URI, namespace shadowing or unresolved caption view fails closed. This
fix admits the redundant `hp`/`hc` declarations found in complete P08 object packages
without flattening namespaces or changing source bytes.

`numberingType` must already equal the selected kind and `lock` must equal `0`.
P09-19's fixture-only caption copying and NONE-to-PICTURE preparation are not product
caption-creation or automatic object-category update claims.

The new focused tests still use synthetic object shells. Separate P09-19 complete
packages exercise this adapter with real source object payloads; package/static
evidence does not establish application-owned sequence semantics or native validity.

`actual_hangul=false`, `semantic_save_reopen=false`, `render=false`, `green_rows=0`,
`p09_complete=false`, `product_complete=false`. Preserve P09-17 failures and all
historical P08/P17 authorities. Do not start a new COM/access-allow validation without
crossing the user-requested pause boundary explicitly.
