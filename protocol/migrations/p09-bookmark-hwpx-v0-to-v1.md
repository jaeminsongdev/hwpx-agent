# P09 bookmark HWPX v0 to v1 migration

There is no accepted v0 wire contract and no implicit migration.

Only `hwpx-agent.bookmark-hwpx.hwpml-2011-point-marker/v1` is accepted. Unknown profiles or fields,
ranged/locked/opaque bookmarks, unsupported native tags, malformed wrapper or marker shapes,
ambiguous transitions, stale state/flow/section/wrapper bindings, and unsealed plans fail closed
with no partial output. Producers must reconstruct and validate a fresh v1 typed state and plan;
no older, partial, or discovery payload is upgraded in place.
