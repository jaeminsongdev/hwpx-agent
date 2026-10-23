# Source/stored bookmark CROSSREF command candidates v1

This additive API edits an existing source CROSSREF command. It does not insert a
new CROSSREF, recalculate its displayed result, or authorize storage/execution.
The main Source assessment v15, field-meaning v2 and partial meaning graph v3 are
unchanged. Existing incomplete-source/full-context rejection remains mandatory.

## Source input and preserving output

`SourceBookmarkCommandChange` selects an actual imported field by reference ID,
exact source-field fingerprint and meaning SHA. The target is an actual
source-local bookmark logical ID. Display is a typed four-way SDK enum and the
hyperlink option is a boolean; no caller-provided command, target name or map is
accepted. The lowerer obtains those values from the same whole source snapshot.

Preparation requires the original fresh reconstruction proof, full XML field
coverage, original document protection checks and finite writer/work budgets.
An empty/duplicate/stale/unsupported/no-op request or missing/ambiguous target
rejects the whole batch. Lock/review/table protection is not bypassed to edit a
command. An invalid source may fail import before the change-specific guard.

Only the selected command contents may change. Original writer/shape checks,
outside-edit byte equality, complete range readback, supported meaning readback
and unselected-field preservation are required. The existing cached field
contents are preserved, NOT refreshed or declared current. A bound source-local
target is not evidence of Native navigation or correct pagination/display.

Receipt profile: `hwpx-agent.source-bookmark-command-update/v1`. It binds the
source/output package hashes, request hash, selected field/meaning fingerprints,
output command hash and selected target ID/state hashes. Raw commands, bookmark
names and displayed contents are not receipt or diagnostic fields.

## Authenticated stored-source candidate

`StoredImportedDocumentForms::prepare_bookmark_command_candidate` reuses current
provider scope/head/node/Result descriptor, actual artifact ACL, quarantine/scan,
AEAD, whole bytes and imported-form reconstruction checks. It additionally
requires the current token's `DocumentWrite` scope. Token scope alone is NOT
proof of atomic project write membership or a service mutation grant.

The lowerer runs once and the output is privately owned. Each byte delivery uses
the original fresh source proof and writer integrity boundary. Inside the writer
callback it checks current scope, fresh ACL/AEAD/raw bytes and final head again
before the consumer. Any observed delivery denial permanently poisons that
candidate, including after ACL regrant or ciphertext restoration. These reads
are not an atomic lease or a guarantee against every external race.

Receipt profile: `hwpx-agent.stored-source-bookmark-command-candidate/v1`.
Execution/publication authority remains false; `require_current_product_route`
retains `RouteUnqualified`. No result artifact is ingested, source overwritten,
revision committed or publication performed by these preparation/access APIs.

## Original operation compiler connection

The candidate retains only selected field anchors from its existing field import.
It is moved into `PreparedCompiledBookmarkCommandCandidate`, without graph or
output cloning, field/meaning re-import, command lowering or writer replay.
The original common source-owner resolver selects actual structural owners.
Original `SelectorSnapshot`, `CapabilityCatalog` and `OperationPlanCompiler`
validate the plan against the sealed source revision and actual source graph.
Current source authorization is checked before AND after compilation.

Local capability `ref.crossref_command_edit` deliberately differs from REF-035's
`ref.crossref_insert`: editing an existing command is not insertion support.
This local compiler definition is not a new advertised catalog/registry entry,
Native qualification or executable route. The canonical 609-feature registry is
not rewritten and this compiler result does not make REF-035 or P09 green.

Each operation binds source/output/stored-receipt hashes, exact field anchor and
reference ID, source-field/meaning hashes, output-command hash, selected target
ID/state hashes, request hash and explicit owner-binding profile. Command text,
target names and cached values are never operation argument values.

Receipt profile: `hwpx-agent.stored-source-bookmark-command-compiler/v1`.
It additionally binds plan ID, source revision/head generation/artifact/graph,
selected anchors and the complete compiled-plan hash. Cached values are still
preserved-not-refreshed; execution/publication authority is false. Immutable
receipt/plan integrity plus original current-source delivery checks are reused
without compiling the plan again. Current route qualification is still denied.

## Evidence and outstanding boundaries

Source changes: `implementation/p09/evidence/p09-361-bookmark-command-updates621-audit006.v1.json`.
Stored access: `implementation/p09/evidence/p09-361-stored-bookmark-commands622-audit002.v1.json`.
Compiler verification and original failure records are reported separately in
`implementation/p09/P09_BOOKMARK_COMMAND_COMPILER_623.md`; a source file or this
contract alone is not a compiler verification receipt.

Stored tests use the real ACL/AEAD services with isolated memory repositories,
scanner and keys. They are not operating SQL, scanner/issuer/key-custody or atomic
storage/CAS evidence. Common request/owned dispatch, registered execution,
artifact validation/ingest/revision CAS/publication, durable recovery and actual
Native update/navigation/save-reopen remain separate completion requirements.
Historical Native failures/claims and original documents must be preserved.
