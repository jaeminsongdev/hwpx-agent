# P09-102 source-selected review paragraph report

Source/product-component progress only. P09/A12/A13 OPEN; native34 NOT_RUN/green0; no actual SQL or native execution.

## Product change

Previously, editing a review body or table cell required replacing its full paragraph list. A plain paragraph next to a rich paragraph containing a table/opaque XML could not be selected independently. The new lower_paragraph and stored prepare_paragraph path replace one actual source paragraph while retaining every outside byte and every other expanded part. Whole-body and whole-cell output still use the original path.

Selection is immutable source identity, not a native numeric ID. Complete target TextFlow supports original runs, text, tabs, line breaks and paragraph properties. Replacement is complete within the selected paragraph; it does not promise preservation of old rich content inside that paragraph. New table/rich-object insertion and full native CommentState remain incomplete.

## Validation

The scoped Rust regression has 305 tests: package 138 and product 167. New feature tests are six package and three stored tests, included in that total rather than additional product tasks. The final raw regression receipt identifies terminal sessions/chunks, exact commands and tested source pins. Tests cover direct MEMO/hidden output, whole outside-part equality, table/opaque sibling preservation, original reimport, stale/foreign/main/non-paragraph selections, no-op/opaque/dangling-style/finite-output rejection, nested-cell protection, original unsupported nested-review rejection and immutable original capture.

Stored tests exercise equality with the direct package result, deterministic fresh replay, no ingest/head change, mandatory callback denial on actual fixture AEAD corruption, ACL revocation and advanced head, scope5 substitutions and continued product-route denial. These are in-memory repository/encrypted fixture checks, not PostgreSQL acceptance.

Eight Python tests verify live prior raw inheritance/whole parent transforms and mock coverage/qualification rejection. Strict package and product lint, targeted formatting, whitespace checks and current-source component conformance are recorded separately. The original default conformance remains FAIL:matrix_drift; component conformance retains fifteen validators, green0 and Gate OPEN. All historical/native qualification was not rerun.

## Failed attempts and recovery

Initial tests attempted private XML/reader access and failed E0624. Tests now use the original public bounded ZIP/source interfaces and explicit synthetic no-op values; no original visibility or parser guard was relaxed. A first main-paragraph negative accidentally selected a legitimate table-cell paragraph with repeated numeric ID0; it now selects the actual root-child paragraph anchor. The nested-review positive attempted a shape the unchanged original reader forbids; the final negative asserts the exact original text_flow_invalid_field rejection instead of inventing nested support. The failed 4-pass/2-fail executable remains in the initial target directory, not overwritten by corrected package builds.

The first formatter invocation recursively reformatted three original fixture files. Their altered bytes were retained, and all three were restored to exact prior hashes before final regression. The raw verifier caught the drift. Strict product lint detected duplicate fixture-module loading, then an obsolete assembly import; both failed new-test source preimages remain. The original fixture is now loaded once and reused, with no lint allow/skip. A six-parent inventory update was initially incomplete; the failing audit/unit output is retained, and the final audit covers the complete declared inventory.

## Remaining full objective

This makes selective rich-body editing more complete but closes none of the minimum six coarse work groups. Still required: new rich Flow/table/comment insertion/show/resolve; native author/time/state/coordinates; original full compiler/protection integration; durable real integration; remaining fields/Date/external/document semantics; trusted issuer/atomic execution/publication; actual P84 SQL cause/regression and authorized native acceptance. Native input remains INPUT_CHANGED_RE_ADMISSION_REQUIRED, P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED. P10 was not started. Goal remains active.

Evidence: `evidence/p09-102-review-paragraph.source-regression.v1.json`, `preservation.v1.json`, `initial-failures.v1.json`, `source-progress.v1.json` and `final-audit.v1.json` under the same prefix. No original source document/evidence was deleted, moved or overwritten.
