# P09 retained search navigation v1

`hwpx-agent.product-source-search-next-request/v1` continues a retained authenticated search
preparation. It selects one original occurrence forward/backward without rerunning its query or
building a new source index. It is a partial SEARCH-005 path, not full capability registration.
The same next schema now supports v5/v6 selector Find through
[the selector navigation profile](p09-selector-result-navigation-v1.md), while Inventory remains denied.

## Request and movement

Call `PreparedStoredSourceSearchProduct::navigation_receipt_sha256` for preparation identity,
then `with_next_verified_json` on that same retained preparation and the current provider.
The strict request contains only schema_version, search_receipt_sha256 and navigation:

```json
{
  "schema_version": "hwpx-agent.product-source-search-next-request/v1",
  "search_receipt_sha256": "<lowercase preparation receipt SHA256>",
  "navigation": { "direction": "forward", "wrap": false, "cursor": null }
}
```

Direction is forward or backward; wrap is required. Missing/null cursor means start at the first
or last retained occurrence. A returned cursor resumes strictly after/before its occurrence.
At an end with wrap=false, selection/match_index are null, exhausted=true and the existing cursor
is preserved for reversing direction. Wrap=true alone enables cycling and marks wrapped=true.
An empty set always has no selection/cursor and wrapped=false. Zero-width matches advance by
ordinal, so they cannot repeat forever without explicit wrap.

The16 KiB request rejects duplicates/unknown fields, non-object envelopes/navigation/cursors,
wrong types/enums and malformed receipt SHA before source access. A null cursor is allowed.
Missing direction/wrap fails. The previous v1~v4 search preparation request shapes stay unchanged.
No new query, caller source/graph, output path or approval bit is accepted in this continuation.

## Cursor identity and response

The cursor binds the full immutable original result and a context derived from the full product
preparation receipt. Original source/document/index/query/options/scope/style/control/review policy
therefore remain bound, as do the product key/plan/provider scope and raw preparation-request digest.
Even a different raw JSON encoding of a preparation starts a different cursor context.
Index bounds, cursor profile and per-occurrence fingerprint are checked. Stale/foreign/edited
cursors fail with SOURCE_SEARCH_CURSOR_STALE_OR_INVALID through the existing stored error boundary.

Cursors are unsigned selection coordinates, not credentials, signed execution receipts or durable
idempotency claims. A valid cursor never bypasses current source or service authorization.
Pure component callers provide their own context digest; only the product adapter derives trusted
product context from its immutable receipt.

Responses use hwpx-agent.source-search-navigation/v1 and include total_matches, optional match_index,
selection, region, cursor, wrapped/exhausted and a navigation request digest. Selection is one text
match with unchanged original pieces, or one control match with its original anchors. Review text
retains body_and_notes/hidden_explanation/memo_body. No raw text/query is included.
The whole selected response remains subject to the original result byte limit without truncation.

All existing scoped literal/regex, declared style, typed definition style, control and review text
result variants are supported. Their retained order is used; this is not a native page/layout order.
Selecting an occurrence is constant-time after identity validation. Current-result identity is a
bounded streaming hash and current stored validation still serializes/checks that result, so total
navigation cost is not constant-time. Only the selected match is cloned, not the whole match vector.

## Current access and completion boundary

Each product call retains the original document.write, provider scope/head/ACL/quarantine/AEAD,
fresh original source and result checks. Temporary full-result validation bytes are dropped before
the selected response is built. The final head check immediately precedes the consumer. No unchecked
retained selection getter, source overwrite, ingest/commit/CAS, key claim, CLI/server execution or
publication is added. The pre-existing full-product route continues to reject qualification.

Components058 passes nine core cases and fails one new size assertion. That assertion wrongly
expected a single selected response to exceed the full source result. Product code and finite limits
are unchanged; only the test changes to exact-bound preservation and one-byte-too-small rejection
of the full original result. Recovery059 runs that one case and seven previously unexecuted product
cases: eight pass with461 fresh/final461 and terminal/empty/closed Jobs. Nine unchanged core passes
are preserved without replay, for17 distinct validated cases. The original failure remains failed.
One unused package helper warning remains in the reusable product fixture; it is not suppressed.
Unrelated312 stored cases, previous search tests and the official queue are not replayed.

Full SearchScopeSelector, actual app selection/page movement, target match_set/semantic_diff/reopen,
operation dispatcher/CAS/execution/publication, Native and the P09 Gate remain unqualified.
Source API v12 remains incomplete/four unresolved/null report/exit3. Queue158/249, remaining91,
next165, P09/A12/A13 OPEN, fixed CROSSREF eight NOT_RUN, Native011 unapproved/unexecuted,
P10 not started and goal ACTIVE remain unchanged.
