# Product note file preparation request v1

`hwpx-agent.product-note-file-request/v1` connects a strict public JSON request to the existing
source-bound HWPX note-file candidate. It is an additive preparation API, not a CLI/server command,
executed capability, idempotency claim, stored revision or publication route. The older domain
`DigestManifestV1`/`PrepareExport`, source assessment v12 and product request v1/v2 dispatchers are
unchanged. REF-025 still requires its full semantic/Native validators before supported execution.

## Required input

`form_product_request::stored_note_file::StoredNoteFileProductRequest::prepare_json` accepts at
most 16,384 UTF-8 bytes. Both the outer request and its operation must be objects. The required
outer keys are schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id and operation. The operation
has exactly kind `export_note_file` and selection `footnotes`, `endnotes` or `both`.

All keys are mandatory and duplicate keys are rejected, including escaped equivalents. Unknown
keys, nested operation arrays, trailing JSON, unknown schema/kind/family and null/missing values
reject before artifact reads. Existing typed ID validators apply; document ID is at most 1,024 bytes,
generation is positive and source SHA is exactly 64 lowercase hexadecimal characters. Limits are
trusted host arguments, not user JSON. No path, caller source artifact/graph, approval or validator
verdict may be supplied. Family selection is explicit rather than inferred from missing data.

## Current source and access

The authenticated StoredFormProvider owns tenant, subject, project, branch, document, services
and permissions. It must have document.read and document.write, while the original artifact ACL,
quarantine/AEAD/digest and sealed revision checks still apply. The public request cannot construct
these permissions; host/issuer authentication itself is not implemented by this preparation API.

The provider selects its sealed current Result at the requested revision/head. Its imported source
SHA must equal the expected SHA. Callers may obtain that SHA from source assessment v12 JSON
without a separate caller-side Form import. The imported source then moves into the stored
candidate, not a clone or self-referential structure. The candidate reuses the original call-local
whole Form proof, source/output writer ID/security/preservation checks and final head discipline.

Every verify or output callback rechecks provider write scope and the original stored read/source/
head/output integrity. Retained receipt/proof clones never grant access. The final head is checked
inside the verified callback before consuming bytes; these reads neither lock the head nor perform
atomic CAS. The callback remains deliberately requested derived-file consumption, not publication.
Metadata/unused resources may retain source information, so output is not privacy redaction.

## Request identity and receipt

The preparation receipt records raw request SHA, canonical typed request SHA and a separate
request digest scoped to the provider's tenant/subject/project/branch/document. Canonical bytes
contain the schema, key, project, document, revision, generation, source SHA, plan and operation.
Whitespace changes only the raw digest; changing key/plan/selection changes canonical and scoped
identity. A family change can produce the same output bytes but must still have a different request
digest. The stored receipt binds source SHA, selection/count, request digest and output SHA.

The profile is `hwpx-agent.product-note-file-preparation/v1`, capability `ref.note_export`.
`idempotency_key_claimed` and `issuer_native_cas_execution_publication_authority` remain false.
The key is bound request data, not an execution claim. Repeating preparation does not promise
exactly-once execution. The candidate has no unguarded raw-byte getter and redacts its Debug.
`require_current_product_route` performs fresh verification and always denies execution.

## Verification and remaining work

`implementation/p09/evidence/p09-361-note-file-request-components032.v1.json` records all 8 new
request and 8 affected stored tests passing with 447 fresh/final447 inputs. It excludes 268 unrelated
tests and does not rerun the 11 core exports, existing source API or official 249-case queue. Coverage
includes source API JSON to actual new file/reopen, family/canonical/source binding, strict parsing,
16 KiB boundaries, write scope, foreign providers, stale head/source, ACL/regrant, quarantine/AEAD,
three final-head race boundaries, protection/limits and the historical six exports/three ID rejections.
Native failures and original source bytes are preserved.

The empty entrypoint type initially lacked Debug. Only its derive was added; debug-check033
proves the full source inverse and unchanged remaining input/test bodies, then compiles the library
with no diagnostics and no test rerun (449 fresh/final449). Both owned jobs closed empty. Their
system CPU peaks were 55.44% and 31.35%, available RAM minima 21.3877% and 19.9714%, and Job
private peaks 899.48 MiB/2.8231% and 1483.74 MiB/4.6569% under unchanged resource safeguards.

The [source XML context rules](p09-note-export-xml-context.md) preserve inherited language/space in
guarded product output and reject removed intermediate bases. Two new product tests pass while
retaining all 52 core/reader/mapper passes; no request schema, write/access or route guard changes.
Body-container/subList layout and XML Base URI binding need further qualification. Native
numbering/layout/save/reopen/reference update/render, full protection, issuer/durable DB/atomic
CAS/exactly-once execution/publication and the P09 Gate remain open. Preparing a file is not
completion of those requirements or a registry support upgrade.
