# P09 comment model v0 to v1 migration

There is no accepted v0 comment-model schema and no migration switch.

`hwpx-agent.comment-model/v1` must be created from a freshly inspected complete ordered section,
author, memo-style, hidden-explanation and comment inventory. Legacy maps, raw XML fragments,
untyped comment bodies, inferred author/time/show/resolved fields, missing field pairs, incomplete
style or opaque state, and P11 comment-delete claims fail closed. Existing identity, anchors,
timestamps, payload/style/reference/protection state and document-flow bindings must be supplied
explicitly.

Only the pinned official `hiddenComment`, `fieldBegin`/`fieldEnd` `MEMO`, `memoProperties/memoPr`
and `memoShapeIDRef` structures are source-qualified. Native author/time, visibility and resolution
remain `UnverifiedMemoParameters`; migration must not reinterpret component state as exact HWPX,
installed-Hangul or target-readback evidence.
