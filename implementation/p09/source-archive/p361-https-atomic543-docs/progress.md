# P09-10 REF-053 product API verification note

## Scope

This is a supplemental work-in-progress note. It does not replace or promote the pinned
`P09-10_REFERENCE_AUXILIARY_REPORT.md`; REF-048 through REF-053 retain their existing unit-only and
native/target `NOT_RUN` classification.

## HTTPS SQL policy publication and revocation

The source-bound server registration API validates finite HTTPS-only policy data, generates the immutable binding/version,
then consumes the preparation for real Evidence ingest/ACL/AEAD readback and SQL generation CAS. Failed registration retains encrypted Evidence;
lost acknowledgement or mismatched replies remain OutcomeUnknown, never a retry/no-effect permit. No public issuer transport was opened.
Dedicated exact25 job/metadata connectors preserve all original23/24 checks and refusal of future schemas. New guards verify current editor role,
source head/latest/unrevoked policy and both ACLs, registration management rights, SQL body/privilege/RLS/immutable boundaries.
HTTPS policy authority is not borrowed from form/formula data. Artifact roles cannot execute the dedicated policy/job/lookup APIs.

[541](evidence/p09-361-https-policy-sql541.v1.json) verifies actual SQL registration/selection/revocation/replacement, stale-candidate rejection,
retained Evidence after failed generation CAS, principal/head/reader/manage/ACL denials and excessive-role/helper/RLS/body-tamper admission denials.
Fixture rights/functions/RLS are restored and readmitted before the actual HTTPS job. The original guarded coordinator then completes claim/lease,
registered intent/precommit, one CAS and completion; public registered effect recovery before/after DB restart does not reexecute the product.
Four local paths are absent during recovery and restored byte-exact. Policy rows remain versions2/revocations1/latest2; artifact9/jobs2/attempts2/intents1/revisions2/seals2/head2,
including bootstrap1+HTTPS1 and the failed publication's retained Evidence. Ciphertext is unchanged; both owned postmasters stop normally.

885fresh/final885, actual example dep-info44 dependencies predeclared, binary/dep-info2final, no diagnostics, cleanupTrue.
409.391s total/Cargo4.141s/SQL worker243.437s including full paced runtime hashes; system CPU max23.05 percent/free RAM min36.567 percent.
One-core/6.25 percent CPU cap and RAM/commit protections remain; peak compiler772.0MiB/SQL86.41MiB and empty owned trees verified.
538 stopped on a Debug warning before SQL;539/540 stopped on seed CHECK23514 before product execution. Failures and missing final closure remain preserved.
The fixture now uses reader and preserves the last-manager invariant via a temporary backup manager, removed after owner restoration; no product or DB guard was relaxed.
Previous accepted tests/consumed roots/SQL520/003/Native were not replayed. Operating deployment, external issuer/worker attestation, atomic execution-policy binding,
long-term key custody and Native/P09 qualification remain unproven. The next policy dependency is atomic binding to the actual CAS transaction.

## HTTPS SQL lifecycle and public registered effect recovery

`PreparedHttpsTargetLookup::recover_registered` delegates to the unchanged common current-scope lookup/archive/ACL/AEAD recovery and second observation.
It reads an existing effect; it grants no new policy approval, claim, execution or retry. Missing/uncertain/conflicting observations never fall back to preparation.

[537](evidence/p09-361-https-target-sql537.v1.json) uses one fresh owned PostgreSQL schema24 root, not SQL520's retained database.
The actual captured HWPX passes the strict HTTPS request, mandatory guarded original coordinator, real SQL claim/lease/barriers,
registered intent/precommit, one CAS and completion. Artifact metadata is SQL-backed and disk AES/readback preserves the original source.
Cold public-request recovery before/after server restart succeeds with four original local handle/state/policy/request paths absent, then restored byte-exact.
Changed requests conflict, missing requests remain NotObserved, and wrong AES keys fail. Recovery does not claim/execute/CAS or retry the product.
Before/after counts remain artifacts7/jobs2/attempts2/intents1/revisions2/seals2/head2; jobs include bootstrap1 and HTTPS1. Ciphertext is unchanged and both owned postmasters stop normally.

850fresh/final850; actual example dep-info42 dependencies predeclared; binary/dep-info2final; no diagnostics; cleanupTrue.
410.875s total, Cargo13.812s, worker241.329s including full paced runtime hashes; system CPU max32.83 percent/free RAM min35.194 percent.
No protection stop; owned one-core/6.25 percent cap, peak compiler1085.79MiB/SQL77.41MiB and empty owned trees verified.
Policy selector/routes/scanner remain isolated fixtures, and keys are ephemeral. This is SQL storage/recovery evidence, not operating policy issuer,
attested worker/admission, durable key custody or Native/P09 qualification. Old tests/536's eight cases/SQL520/003/prior Native were not replayed.

## Mandatory HTTPS job guards and preserved registry admission

`with_verified_guarded_job_preparation` obtains fresh server routing/time, prepares the original common job and automatically
attaches current source/policy/route restrictions before claim and both mutation boundaries. A caller cannot replace that guard;
missing routing stops before storage/job callbacks. The original coordinator owns registration, lease, barriers, single CAS and completion.
No retry loop or alternate execution engine was added. This trusted storage primitive is not a product admission permit.

The pinned-registry HTTPS entry authenticates the preserved actual P02 snapshot and retains its routing-disabled release policy.
Strict request parsing precedes admission, and routing denial precedes source/policy preparation. Signature verification does not
upgrade old claims, activate a route or mutate public trust material; no private signing key is read.

[536](evidence/p09-361-https-target-job536.v1.json) runs8 new cases; unchanged storage8/request22 were retained without replay.
The real pinned signature/early denial and original coordinator's guard/register/CAS/completion/replay/uncertain response paths passed.
Memory lifecycle models show actual AES/readback, archived receipts and one CAS, preserved head on revocation/uncertain validation,
preserved committed effects on lost completion acknowledgement, and retained receipts with no CAS on failed/uncertain registration.
They do not qualify real SQL registration/worker/issuer/durable jobs or Native/P09. Source/runtime bodies of the common coordinator remain unchanged.
Current838fresh/final838·actual dep-info1final·no diagnostics·cleanupTrue;131.984s total/Cargo24.235s/body7.95s.
CPU max44.32 percent/free RAM min35.797 percent, no protection stop; owned one-core/6.25 percent cap, peak private1085.75MiB,
empty owned tree verified. See the [stored HTTPS contract](../../protocol/migrations/p09-stored-https-target-candidates-v1.md).

## HTTPS manifests and shared storage preparation

The HTTPS product now moves into source/policy-bound manifest data through the unchanged common router/manifest body.
Target/registry/health/time and whole route-set are rechecked at reuse. Its sole current source/output callback feeds the
same storage preparation, one-shot staged import validator, request job identity, commit binding and job primitives as search.
The shared factory adds source/output/manifest/plan/base-head/request binding checks; original search hashing/job/CAS guards remain.
Current source/policy/route restrictions are refreshed at both ingest and final-CAS boundaries; the first guard failure latches.
Neither a manifest nor a prepared job permits registration, durable claim, backend execution or product route qualification.

[535](evidence/p09-361-https-target-storage535.v1.json) runs HTTPS6 plus affected existing literal document/paragraph-scope2:8 cases.
The unchanged prior request22 were retained, not replayed. Actual captured HWPX output passed original workspace engine,
one-shot validator, real AES/readback and in-memory revision CAS. Revocation between ingest and CAS preserved the original head
and retained ingested output. Corruption/reused validator, route drift and guard latching also passed; product route denial remains.
Routes/scanner/policy repository and stores are fixtures, not operating SQL/issuer/attested registry/durable-job/Native evidence.
Current833fresh/final833·actual dep-info1final·no diagnostics·cleanupTrue;124.813s total/Cargo18.578s/body1.86s.
System CPU max69.73 percent/free RAM min44.335 percent, no protection stop; owned one-core/6.25 percent Job cap,
peak private1085.46MiB and empty owned tree verified. Historic peak attribution and PC-freeze cause remain unresolved.
See the [stored HTTPS contract](../../protocol/migrations/p09-stored-https-target-candidates-v1.md).

## Strict HTTPS product requests and common scoped observation

`StoredProductRequest` now accepts a strict dedicated HTTPS request only through methods receiving the trusted policy repository.
The2MiB/4096-item schema requires object shapes at every envelope/operation/change/target level and rejects duplicate/unknown fields,
duplicate reference IDs, invalid hashes/head and non-HTTPS targets before source reads. Source/head/ACL/policy still receive fresh service checks.
The original borrowed/owned transfer pattern returns a self-contained source/candidate/compiler without graph or output cloning.
Raw/canonical/scoped request hashes are distinct and bound to authenticated provider scope and the compiled receipt; no key is claimed.

The observe-first entry reuses the common scoped lookup. Existing and lookup failures never fall back to source/head/policy/compiler work.
Only NotObserved enters preparation, and it is not an absence lease or execution permit. Original prepare_json explicitly returns
PolicyRepositoryRequired; search-only preparation cannot bypass that boundary. Old Form/Formula/search parsing and routes are unchanged.

[534](evidence/p09-361-https-target-request534.v1.json) closes corrected1 plus unchanged533 body17 and retained early-denial4:22 distinct,
not a22-case run. New request8+ownership-affected10 were selected;17 were not replayed after fixing one reserved-zero digest fixture.
53317pass/1fail/warnings2/absent final closure remain intact. The shared zero-source lookup guard was not relaxed; runtime bodies are unchanged.
Current834fresh/final834·actual dep-info1final·no diagnostics·cleanupTrue,122.390s total/Cargo15.750s/body0.01s.
CPU max23.05 percent, available RAM min34.322 percent, owned peak private1082.65MiB, one-core/6.25 percent cap and empty owned tree verified.
Operating policy issuer/repository, attested registry/manifest, durable claim/job/CAS and Native/Gate remain open.
See the [stored HTTPS contract](../../protocol/migrations/p09-stored-https-target-candidates-v1.md).

## HTTPS candidates through the common plan compiler

The stored candidate now moves into `PreparedCompiledHttpsTargetCandidate` through the original `OperationPlanCompiler`.
It retains selected source begin anchors without a second whole graph clone/field import, shares the unchanged actual-owner
resolver with search compilation, and emits REF-034 `ref.hyperlink_edit` plan data. Source graph/revision, source/output,
stored receipt, current policy identity/digest and exact source field/meaning/target hashes are bound without URI arguments.
An actual ctrl owner is not redirected to a guessed paragraph. Compilation is bounded and current policy/source checks run before
and after; later verification/delivery never repeats compilation or lowering. The local catalog is not an attested registry or route.

[532](evidence/p09-361-https-target-compiler532.v1.json) closes one corrected test plus nine unchanged531 body results and
four original early-denial cases:14 distinct, not a14-case execution. New compiler5 plus affected stored preparation5 were selected;
the unrelated early-denial4 and official249 were not replayed.531's9pass/1fail and absent final closure remain preserved.
The correction replaces a test-only graph-position assumption with independent original XML range containment; product owner code is unchanged.
Current closure is831fresh/final831, actual dep-info1final, no diagnostics, cleanupTrue;108.641s total/Cargo2.531s/body0.07s.
System CPU max22.57 percent, available RAM min35.898 percent; owned one-core/6.25 percent Job cap and empty owned tree verified.
Public request/idempotency, operating policy repository/issuer, attested registry/manifest/job/CAS and Native/Gate remain open.
See the [stored candidate contract](../../protocol/migrations/p09-stored-https-target-candidates-v1.md).

## Stored source HTTPS target candidates

`StoredImportedDocumentForms::prepare_https_target_candidate` now connects authenticated source ACL/AEAD/head checks
and repository-selected immutable HTTPS policy artifacts to the original whole-batch lowerer. Public callers cannot supply
policy bytes or policy artifact selectors. Delivery rechecks write scope, both artifact ACLs, source/head, current policy/revocation
and policy AEAD, with final policy/head checks inside writer integrity. It never repeats lowering/writing or publishes output.
The repository interface requires current project write authorization; its operating SQL/issuer implementation remains open.

[530](evidence/p09-361-stored-https-target530.v1.json) records one corrected head case plus eight unchanged body results retained
from528, not a nine-case replay. Current closure is831fresh/final831, actual dep-info1final, no diagnostics, cleanupTrue.
527 compile-only failure and528/529 invalid future-revision fixture failures remain intact; storage/domain rules were not relaxed.
Final wall time110.203s, Cargo3.688s, body0.05s, system CPU max41.9 percent, available RAM min35.804 percent, no protection stop.
Original Job one-core/6.25 percent cap and empty owned process tree were verified. Historic freeze attribution remains unresolved.
The530 receipt has no operating policy issuer, atomic lease, common execution/job/CAS, Native or Gate qualification;
`require_current_product_route` still denies. See the [stored candidate contract](../../protocol/migrations/p09-stored-https-target-candidates-v1.md).

## Source HTTPS target edit candidates

The typed product API `prepare_package_https_target_changes` now joins actual source meaning selections
to policy-bound HTTPS target candidates. The original six-parameter reader/formatter supplies only existing
Command/Path leaves to one preserving transaction. Full output import compares new selected targets,
unselected meanings, original field IDs/positions and bytes outside selected content. Cached display text
is preserved, not updated or declared fresh. No source file, external URL, Native session or stored revision is mutated.

An immutable borrowed policy view validates sorted approvals once and performs exact kind/digest binary
lookups. The unchanged shared Unicode lock/tracking guard feeds one prefix index per selected part.
The original structure parser still rejects unsupported lock placements; it was not relaxed for the test.

[526](evidence/p09-361-source-https-target526.v1.json) closes current14 plus unchanged retained policy3
as17 distinct cases, not one17-case execution. Current inputs are836fresh/final836, actual dep-info3final,
diagnostics empty and cleanupTrue.524 source7/1fail and525 preflight-only failure remain preserved.
Source7 was rerun because the actual policy/guard path changed; unchanged policy3 was not replayed.
Runtime was258.5 seconds. System CPU peaked81.42 percent and available RAM bottomed29.777 percent;
owned one-core/6.25 percent Job limits were verified and no protection stop occurred. Historic peak
attribution remains unresolved, not a PC-freeze fix. Current service/issuer/route/storage/Native update
and save/reopen qualifications remain open. See the [candidate contract](../../protocol/migrations/p09-source-https-target-changes-v1.md).

## Source field meaning API and borrowed index

The separate `assess_package_field_semantics` product API reads actual package bytes through the existing
Form/field-range and HTTPS/table-formula readers. `SourceFieldMeaningIndex` borrows the original ranges
without an additional complete document graph clone. Selection output contains source-derived IDs,
fingerprints, meaning hashes and kinds, not URI, Command, formula/cache or body text. Supported malformed
parameters fail; unsupported kinds remain explicit. Existing source v13, unresolved4, no report and exit3
are unchanged. No destination is opened and no external approval or complete flow is inferred.

[523](evidence/p09-361-source-field-semantics523.v1.json) closes new9+affected6=15 cases with849fresh/final849,
two actual dep-info hashes and cleanupTrue. It reads the preserved HTTPS package and16 hash-pinned P06
formula packages, retaining unverified formula caches and original bytes. Runtime was186.015 seconds;
system CPU peaked45.31 percent and available RAM bottomed31.925 percent under the original protections.
522's three token-window equivalence/work tests returned success but missed two cfg(test) fixture inputs
and have no final fresh closure. Their original observations are retained, not replayed or promoted to a
current complete unit qualification. The15 cases in523 exclude those three.

The token window optimization retains the original owner/token-kind predicates and parser-owned empty/end
boundaries. It removes whole-token-vector scans for each HTTPS parameter. Full reference edges, target/cache
semantics, auxiliary state, page/document flow, actual update/save-reopen and Native/Gate remain open.
See [source field meaning contract](../../protocol/migrations/p09-source-field-meaning-assessment-v1.md).

## Source API v13 direct outline targets

The actual source API and CLI now explicitly use reference-source-assessment/v13. An optional
heading_target_import receipt joins direct OUTLINE targets to the existing target inventory using the same
immutable Form structure, without a second ZIP/XML/Form import. No observed HH heading model yields null,
not a fabricated empty inventory; an explicit valid NONE model yields a real zero-target receipt. Any observed
HH heading invokes the strict importer and never converts Binding, Coverage or Limit to null.

The current closed-input verification424 passes new core7, new API13, affected API57 and stored3:80 distinct
product cases,878fresh/final878, no diagnostics and cleanupTrue. The compiler dependency closure declares
all87 current test input paths for the three binaries and is checked before and after compilation. Cases cover
actual CLI/API agreement, document/source binding, unchanged originals, existing bookmark joins, explicit
NONE versus unavailable headers, invalid/opaque/header declarations, two-part IDs, exact limits and redaction.
The previous standalone core24, official249 and Native runs are not replayed.

421 observed core7/API70 passes but could not publish its final row because the original256KiB cap was exceeded;
the missing final proof is not reconstructed as original acceptance.422 preserves stored3pass followed by one
shared fixture dead_code warning,806fresh/final806,cleanupTrue.423 preserves a pre-execution lookup KeyError
for a fixture absent from the earlier manifest,809fresh/final809,tests0,cleanupTrue.424 closes the actual87-input
test graph, not an assumed historical fixture result. Only that shared function's unused annotation was added;
no production algorithm, fixture function body or test assertion changed to remove the warning.

Lossless inline sample columns preserve every resource observation with the same256KiB cap. The six layout
roundtrip/rejection/limit cases passed in422 and remain unchanged. Decode the new receipts with
tools/p09/resource_sample_table.py:unpack to restore resource_samples. Verification424 retains251 samples,
126.281 seconds total and10.531/0.250/2.141 command seconds. Job CPU9.109/0.172/1.734 seconds,
peak private1066.17MiB, maximum system CPU22.73%, minimum available RAM40.0186%; all Jobs active0,
empty and handle closed. Original one-core/BelowNormal,CPU6.25%,private8%/stop7%,RAM/commit95% stay intact.

V13 remains incomplete with all four unresolved stages, no validation report and exit3. Heading receipt flags
for effective style cascade, Native number/navigation and complete reference state remain false. Raw heading
parameter observations are not added to the API. Full OtherTargetFamilies, CROSSREF semantics and Native
acceptance are still open. Queue158/249,91 remaining,next165,P09/A12/A13 OPEN,P10 not started,goal ACTIVE,
CROSSREF8 NOT_RUN,Native011 unapproved and character-style6 choice pending remain unchanged.
See [source outline contract](../../protocol/migrations/p09-source-direct-outline-targets-v1.md) and
[424 evidence](evidence/p09-361-reference-source-heading-api-closed-inputs424.v1.json).

## Standalone direct source outline stage history

The new standalone source importer binds explicit header OUTLINE declarations to represented original paragraphs.
It reuses immutable XML/graph/anchors, indexes declarations once, and rejects missing whole-source coverage in
header/nonspine/opaque XML. NUMBER/BULLET/NONE are not headings; absent direct declarations do not imply a
named-style cascade. Raw idRef/level observations do not resolve Native numbers, level ranges, pages or navigation.

418 stopped before Cargo because this integration test root was absent from the preceding catalog source manifest.
The historical test result was not reused.419 executed new22 and original target2:22pass/2fail. The two tests let
the existing Paragraph rejection escape before the intended assertion. Production code and passed bodies stayed
unchanged;420 ran only those failed2 and passed, retaining22. Current distinct24,789fresh/final789,cleanupTrue.
The original418/419 failures remain. Actual application/COM/Native, official249 and other successful suites were not replayed.

At420 this was not yet wired into the actual source API. V12 and its four unresolved stages, incomplete status, absent
report and exit3 were unchanged. The subsequent versioned API/CLI integration above does not clear
OtherTargetFamilies or claiming P09 acceptance. See [source outline contract](../../protocol/migrations/p09-source-direct-outline-targets-v1.md)
and [420 evidence](evidence/p09-361-source-heading-targets-test-recovery420.v1.json).

## Source API v10 caption joins for stored requests

The actual reference-source response now explicitly uses v10 and exposes
caption_source_state_import, caption_owner_links and caption_source_events with
typed accessors. All reuse the one existing original caption-state assembly.
No second package/XML/Form/caption-state import is added. The joined receipt
binds the existing constituent models; links and events index their exact rows.

An actual API-to-stored integration case constructs typed caption creation and
deletion requests from that response without a caller-side caption-state import.
It checks the output through the actual source API and rejects foreign-document
and altered joined digests. Existing current access/source/proof/writer/final-head
checks are unchanged. Receipt hashes do not authorize access; XML event order
does not establish Native counters or rendered flow.

New API5, stored integration1 and all41 affected source cases pass:47 total,
278 fresh/final278 inputs and confirmed cleanup. Existing source41 bodies are
preserved except one include and eight explicit v9-to-v10 schema expectations.
Production source import/coverage/limits/errors/unresolved logic is unchanged
outside the declared response additions. Existing stored test bodies and service
production code remain unchanged; core49, patch13 and stored30 are neither
replayed nor promoted to this feature graph.

Coverage includes actual CLI v10 and exit3, exact API/CLI agreement, source-byte
preservation, two-part local-ID separation, complete owner/control links, empty
and caption-less owners, whole-source/document binding, exact response limits
and non-disclosure of private text/styles/affixes. Components001 takes81.735
seconds overall and40.235 owned seconds,13.938 Job CPU seconds,765.94 MiB peak
private memory,51.37 percent maximum system CPU and25.1971 percent minimum
available RAM. The Job is empty, active0 and closed. Original resource bounds,
64 arguments/8536 UTF-16 bytes and32 KiB capture remain; the CLI compiles once.
Only the existing unused-import warning remains. Evidence:
`p09-361-source-caption-join-components001.v1.json`.

Next is source CROSSREF parameter/target binding against official definitions
and captured originals for reference-edge import. V10 still reports incomplete,
four unresolved stages and no validation report, with exit3 and denied execution/
publication. Native counter/rendering, full state/flow/protection, CAS and Native
qualification remain open. Queue158/249,91 remaining, next165, P09/A12/A13 OPEN,
P10 not started, goal ACTIVE and separate Native011 approval are unchanged.

## Fresh stored access for whole caption structure candidates

`prepare_caption_structure_candidate` binds typed caption creation, deletion
and explicit replacement to the existing current scope/head/ACL/quarantine/AEAD
source, whole Form proof, joined state, writer integrity and final-head callback
boundary. A private Captions variant shares that boundary without exposing inner
content or an alternate byte accessor. No production path ingests or commits.

Creation receipts follow original owner order rather than caller order. One
owner index matches source object IDs, hashed local IDs and paragraph allocation
counts; deletion IDs/fingerprints, the complete request digest, joined state and
output inventories are bound. Saved receipts/proofs never authorize later reads.
Every verification and delivery rechecks current source access.

New structure6 and existing content6/sequence6/number-topology6/program6 cover30
distinct cases. Components001 retains29 passes and one failed protection-visit
expectation. Three separate two-pass maps make6N visits for the mixed case, not4N.
Only that test expectation changed, verified by exact inverse bytes/hash, and
recovery002 runs only that case and passes. Its subsequent tuple/list metadata
comparison failure remains intact. Metadata003 verifies the complete successful
case list,274 fresh/final274 inputs and terminal cleanup without another test run.

Cases cover reversed creation order, mixed create/delete/replace and retained
text/layout/three styles, request digests, revoked ACL, quarantine/AEAD tamper,
foreign scope, final callback head movement and invalid/protected/limited input.
Existing common access code is unchanged outside imports/variants/dispatch;
previous service test bodies are unchanged outside one include. Normal access
leaves read audits only; source/head and denied execution/publication stay intact.
Core49 and patch13 are neither replayed nor promoted to the current feature graph.

Recovery002 takes90.703 seconds overall,68.078 owned seconds and4.484 Job CPU
seconds, with723.91 MiB peak private memory,52.51 percent maximum system CPU
and26.2935 percent minimum available RAM. Both Jobs from001/002 are empty,
active0 and closed. Existing resource, argument and output bounds are unchanged;
only the existing CLI unused-import warning remains. Evidence:
`p09-361-stored-caption-structure-components001.v1.json`,
`p09-361-stored-caption-structure-recovery002.v1.json` and
`p09-361-stored-caption-structure-metadata003.v1.json`.

Next is implementing missing source observations/policy for caption/number
binding in the actual API's CompleteAuxiliaryState and ReferenceEdgeSemantics
stages. Native counter/render behavior, full state/flow/protection and
CAS/execution/publication remain open. Source API v9 stays incomplete with four
unresolved stages, no report and exit3. Queue158/249,91 remaining, next165,
P09/A12/A13 OPEN, P10 not started, goal ACTIVE and separate Native011 approval
remain unchanged.

## Whole caption creation deletion and replacement candidates

Typed `lower_caption_structure_candidate` and its whole Form proof variant
bind explicit owner/caption fingerprints, complete paragraph/run/text/number
bodies, declared character/paragraph/named styles and layout to the original
joined state. Replacing an existing caption requires an explicit matching
deletion. Even no-op content requests aimed at deleted captions are rejected.
No caller XML, inferred style or Native defaults are accepted.

New paragraph IDs start after each original part maximum; removed IDs are not
reused. One ID scan per changed spine part and shared protection indexes serve
the batch. Retained text/layout/style bindings use rebased source byte positions.
Complete output owner/caption/control inventories and exact outside-edit bytes
are checked after one writer and reimport.

A separate static caption-owner/v8 ID profile adds arc/connectLine id/instid
from the official Hancom model inheritance at commit
`1453388472c703a4b299a0834f425cdac16644b9`. Existing shape/v6 and chart/v7
remain unchanged. Only the new caption structure mode selects v8. Duplicate
shape/instance IDs, unknown ID-like references and namespaced IDs on HWPX
elements fail. Foreign namespace elements remain opaque, preserved and never
registered as HWPX IDs. Charts and connector endpoint references are not added.

Core49 comprises48 passes in components003 plus the corrected failed case in
recovery005. Exact source checks preserve those48 without replay. Only the
failed test's foreign-namespace expectation changed, with an inverse-byte/hash
check; product code and other tests were unchanged. Original failures001/002
and003/004 remain intact. New structure6 plus affected core43 cover ten owner
kinds, two parts,64 creations/deletions, replacement, retained bindings and
rejections. Regressions006 separately passes all37 affected stored24 and patch13,
with267 fresh/final267 inputs and confirmed cleanup. These86 distinct
components do not promote results between feature graphs or accept queue cases.

Regressions006 takes69.797 seconds overall and30.609 owned seconds, with
28.734 Job CPU seconds,1514.32 MiB peak private memory,19.32 percent maximum
system CPU and27.1792 percent minimum available RAM. Recovery005 takes42.516
seconds overall and3.594 owned seconds with266 fresh/final266 inputs. Both
Jobs are empty, active0 and closed. Existing resource and argument/output bounds
remain unchanged; the CLI's prior unused-import warning remains the only warning.
Evidence: `p09-361-caption-structure-recovery005.v1.json` and
`p09-361-caption-structure-regressions006.v1.json`.

Next is fresh stored-service binding for the new whole-caption topology request
and receipt. Existing stored24 regression passes do not qualify that new binding.
Native counter/render behavior, complete auxiliary state/flow/protection,
CAS/execution/publication and Native qualification remain open. Source API v9
stays incomplete with four unresolved items, no report and exit3. The official
queue remains158/249 with91 remaining and case165 next; P09/A12/A13 stay OPEN,
P10 is not started, the goal stays ACTIVE and Native011 needs separate approval.

## Fresh stored binding for caption programs and generated labels

`prepare_caption_program_candidate` connects explicit caption arithmetic to the
existing current scope/head/ACL/quarantine/AEAD source checks, whole original/
Form proof, one joined state, writer integrity and final-head callback boundary.
Private closed request/output variants share that boundary; the inner content
and any alternate byte accessor remain private.

Generated label+separator requests are added to the ordinary text request
bindings, including no-ops. Digests and UTF-8 lengths are computed once per
sequence. Definition/member indexes match exact caption/object/text/control
identities and caller order against the output metadata, then reuse the existing
text/content validator. Full program and lowered-number digests are bound but
never treated as access authority. ACL revocation, quarantine, AEAD tamper,
foreign scope and final writer-head movement prevent consumer calls.
Preparation/exposure neither ingests nor commits a source, and the execution/
publication route stays denied.

`p09-361-stored-caption-program-components001.v1.json` records 24 passes: six
new stored-program and six each of existing content, sequence and topology
cases. All 253 inputs passed fresh/final checks; cleanup is confirmed. Exact
inverse edits preserve 71 prior service test bodies and common service code
outside new declarations, dispatch and generated-label binding. The earlier
30 core-program cases were not rerun or promoted to this CLI feature graph.

Total time was 89.313 s; owned execution 52.000 s; job CPU 49.172 s; peak private
memory 1868.71 MiB; system CPU at most 21.78%; available RAM at least 25.6073%.
The owned job ended empty with its handle closed. One-core, BelowNormal,
CPU cap 6.25%, RAM/commit 95%, 39 arguments/12154 UTF-16 bytes, 32 KiB capture
and complete input pre/post checks remain unchanged. Only the pre-existing
test glob warning remains.

This path edits existing captions. Creating/removing original captions, native
counter recalculation/rendering, complete auxiliary state/flow/protection, CAS,
execution/publication and Native qualification remain open. Actual source API
v9 stays incomplete with four unresolved stages, no report and exit 3.
Queue 158/249, remaining 91, next case165, P09/A12/A13 OPEN, P10 not started,
goal ACTIVE and separate Native011 authorization remain. Next: inspect existing
plain-static caption insertion and ID allocation, then implement source-bound
caption creation/deletion with preservation and output readback.

## Source bound typed caption sequence output

`lower_caption_program_candidate` and its whole Form proof entry bind existing
typed sequence definitions to every original caption. The caller explicitly
selects each object/sequence, whole plain label hp:t, autoNum and document_order.
Continuous/per-section arithmetic and seven formats feed the existing atomic
text/layout/style/complete-number-snapshot compiler. Unselected controls,
document/section starts including zero, original affixes/userChar and unknown
properties remain intact.

This output profile binds number_style_sha256 to the selected run's unique
declared character-style subtree, including an explicitly requested replacement
declaration from the original header. It does not infer inherited formatting,
label/body text splits, native defaults or native/render order. Missing,
duplicate, foreign, wrong-kind/style/order, protected, oversized and overflowing
requests fail closed. Sequence locks/opaque metadata without a native mapping
are rejected, not silently dropped. No fabricated complete auxiliary/v1 state
is used to bridge partial source data.

The original full-state validator and new arithmetic share one counter kernel,
retaining the original last-item overflow rule.
`p09-361-caption-program-components002.v1.json` records 26 passes: six new domain,
six new source-output and 14 existing domain cases, with 247 fresh/final inputs.
`p09-361-caption-program-oracles003.v1.json` adds only four unchanged original
counter regressions, with 248 fresh/final inputs. The distinct scope is 30 cases,
including the 1555-variant, 512-protection-mask, overflow/error and 8192-record
comparisons. The 26 passing cases were not rerun.
The preserved first-run compile failure executed no tests; its only production
repair replaces a test-only hex reference with the existing hex_digest helper.
No dependency, test body or resource guard changed for that repair.

Successful run 002 observed system CPU at most 27.65%, available RAM at least
26.2074% and peak owned private memory 1479.08 MiB. Run 003 observed 20.83%,
27.3802% and 1538.28 MiB. The initial compile failure observed 61.70%, 24.1313%
and 1858.65 MiB. All three owned jobs ended empty with closed handles. One-core,
BelowNormal, CPU cap 6.25%, RAM/commit 95%, finite argument/capture limits and
whole input pre/post checks remain.

Native counter recalculation/rendering, stored program binding, complete
auxiliary state/flow/protection, CAS, execution/publication and Native
qualification remain open. Actual source API v9 remains incomplete with four
unresolved stages, no report and exit 3. Queue 158/249, remaining 91, next
case165, P09/A12/A13 OPEN, P10 not started, goal ACTIVE and separate Native011
authorization remain. Next: bind generated label requests and the program to
the stored service's existing fresh scope/head/ACL/quarantine/AEAD and final
writer-head boundary.

## Fresh stored access for number control structural edits

`prepare_caption_topology_candidate` binds insertion/deletion candidates to the
existing current scope/head/ACL/quarantine/AEAD source checks, whole original/
Form proof and one joined state. Private closed request/output enums share
existing content/sequence verification, writer integrity and the final-head
callback boundary. The new wrapper keeps its inner content private; no caller
output implementation, saved access flag or alternate byte getter is added.

The bounded request digest binds the joined state, deletion identities/
fingerprints/order and wrapper-removal choice, and insertion anchors/
fingerprints/positions/local IDs/control order/values/formats. It is compared
with the core output receipt, never used as access or execution permission.
Every verification/exposure rechecks current source access. ACL revocation,
quarantine, AEAD tamper, foreign scope and final writer-head movement block the
consumer. Successful preparation/exposure neither ingests nor commits a source;
the execution/publication route remains denied.

`p09-361-stored-number-topology-components001.v1.json` records 18 passes:
six new stored-topology cases and six existing content plus six existing
sequence cases. All 240 inputs passed fresh/final checks, with cleanup
confirmed. Exact inverse edits preserve all 65 prior service test bodies and
the common service code outside the new declarations/dispatch. Previously
qualified core topology cases were not rerun.

Total time was 45.375 s; owned execution 9.422 s; job CPU 8.031 s; peak private
memory 698.41 MiB; system CPU at most 17.19%; available RAM at least 30.3688%.
The owned job ended empty with its handle closed. One-core, BelowNormal,
CPU cap 6.25%, RAM/commit 95%, 33 arguments/9136 UTF-16 bytes and 32 KiB capture
remain unchanged.

Calculated counters, complete auxiliary state, label/separator interpretation,
effective style/whole-flow protection, CAS, execution/publication and Native
qualification remain open. The actual source API stays v9, incomplete with
four unresolved stages, no validation report and exit 3. Queue 158/249,
remaining 91, next case165, P09/A12/A13 OPEN, P10 not started, goal ACTIVE and
separate Native011 authorization remain. Next: bind the existing typed
caption-sequence requests to exact source number/object/caption state and
actual output, without inventing Native defaults or text splits.

## Number control insertion and deletion

The source-state compiler now accepts typed insertion/deletion requests bound to
the original joined state and exact source anchors. It builds auto/restart
controls with explicit formats, section starts and document starts in the same
transaction as caption text, layout and declared style references. It reads back
the complete retained/deleted/inserted control inventory. A sorted source-byte
edit map rebinds surviving text and caption elements after structural edits;
changed output ordinals are not treated as original identities.

Protection maps are shared per part. Sorted insertion-position and deletion-
boundary indexes avoid a request-by-request scan of all operations. Unknown
wrapper attributes, comments and other children remain intact; an empty ctrl is
removed only when every selected child explicitly permits removal. Existing
overlap, ID, source preservation, writer and readback checks remain active.

The first run completed all 42 selected tests and closed its owned processes,
then stopped on system CPU 91.73% during the final input audit. Its FAILED
receipt is preserved in `p09-361-number-topology-components001.v1.json`.
The follow-up retained the exact production source and already-passed test
bodies, executed only seven new boundary cases plus 13 affected patch cases,
and completed 236 fresh/final input checks with cleanup confirmed:
`p09-361-number-topology-boundaries002.v1.json`.
The distinct scope is 62 component cases: topology 7, splice 6, core 30, stored
sequence 6 and legacy patch 13. The 42 completed cases were not rerun.

The follow-up observed system CPU at most 26.70%, available RAM at least
26.2837%, and owned private memory at most 1468.02 MiB. Both owned jobs ended
empty with closed handles. The post-execution pressure spike is not attributed
to Defender or another process, and no freeze fix is claimed. One-core,
BelowNormal, CPU cap 6.25%, RAM/commit 95% and all original finite limits remain.

This qualifies a file-candidate compiler path, not a stored topology service
route, calculated counters, whole-flow protection, CAS, execution, publication
or Native behavior. The existing stored content/sequence paths and source API
v9 remain unchanged. Queue 158/249, remaining 91, next case165, P09/A12/A13 OPEN,
P10 not started, goal ACTIVE and separate Native011 authorization remain.
Next: bind the topology candidate to the stored service's existing fresh
scope/head/ACL/quarantine/AEAD, whole original/Form proof and final writer-head
boundary.

## Fresh stored service binding for the complete number request

`prepare_caption_sequence_candidate` binds all four request families to current
service scope/head/ACL/quarantine/AEAD, whole original/Form proof and one joined
state. A private closed Content/Sequence output enum shares the existing fresh
verification, writer integrity and final-head callback boundary. There is no
caller-provided output implementation, trusted flag, raw byte getter or alternate
authorization path. The legacy content API/receipt shape remains unchanged.

The bounded `NativeNumberSequenceReplacement::canonical_sha256` binds joined-state,
document-start presence/ID/fingerprint/all six values, and every ordered event's
ID/fingerprint/kind/values/category/section starts/format Preserve or Replace choice.
Format type, user character, affixes and superscript are included; plaintext is
hashed before serialization. Output-v2 adds caller_request_sha256 while retaining
the node/value complete_request_sha256. Stored candidates independently compare
the actual caller request hash. Pure request identity is not source, access or
execution authority; historical v1 receipts are not promoted to v2.

Evidence: `p09-361-stored-number-stream-components002.v1.json`, new6 plus affected
core6/legacy stored content6, all18pass,227fresh/final227,cleanupTrue. Two complete
target groups are6/12, with37 arguments/8290 bytes within original budgets. Tests
cover all four families/output readback, independent digest changes for all request
fields/no-ops, ACL revocation, quarantine, ciphertext tamper, foreign scope,
actual shared head movement at the final writer read, invalid/partial requests,
protection and finite limits. Normal effects are read audits only; source/head
and execution/publication denial remain intact.

001 is preserved as an import-delimiter compile failure with zero tests executed.
002 reverses exactly that one-character fix and checks all other current inputs
before the first execution of the18 cases. All107 old core and59 old service test
bodies/fixtures are preserved. There are no new warnings; the existing unrelated
CLI import warning remains. Resource timings/extrema are in CURRENT_STATE.md;
elapsed build time does not establish compiler phase or external-load attribution.

Native counter interpretation/recalculation, control/format creation/deletion,
complete effective styles/flow/protection, CAS, execution, publication and Native
remain unqualified. Next is typed insertion/deletion to remove the fixed original
control-topology limitation. Source API v9, general routes, Native dispatch and
resource limits remain unchanged. Official158/249,next165,P09/A12/A13 OPEN,goal ACTIVE
and separate Native011 approval/current-input qualification remain.

## Complete original number control stream output

`NativeNumberSequenceReplacement` binds the exact joined-state fingerprint,
original document-start presence/identity and every auto/restart/section-start
control in actual spine/XML order. Omission, duplicate, reorder, kind, foreign or
stale substitutions reject. The source-state and whole Form proof entry points
compile this stream together with text/layout/style edits using one transaction,
writer and complete output import/readback. Zero, stored19 and signed values are
stored native integers, not resolved/recalculated counters.

All22 existing NumberFormat variants and existing user/prefix/suffix/superscript
attributes are supported; Preserve retains the original format. Numeric/boolean
no-ops keep lexical spellings. Unknown properties and expanded bytes outside the
selected edits remain exact. Receipts bind every requested node/value by hash
without leaking affix plaintext. Shared style/number protection maps give4N visits
for128number+64style+64text requests in one part.

Attribute tab/LF/CR now use character references so that [XML 1.0 attribute
normalization](https://www.w3.org/TR/xml/#AVNormalize) preserves their intended
semantic characters. The original SafeXml normalization/security parser is
unchanged. Tests independently reimport both quote styles, specials and whitespace.

Evidence: `p09-361-number-stream-content-components001.v1.json`, new6 plus affected37,
all43pass(core30/source1/stored12),221fresh/final221. The previous101 core test bodies
are unchanged. The exact multi-package invocation uses64 arguments/14974 bytes
within original budgets. `p09-361-number-stream-attribute-regressions001.v1.json`
adds the separately scoped unchanged patch13 regressions,222fresh/final222.
`p09-361-number-stream-warning-compile002.v1.json` removes only a new unused import,
checks the exact inverse and compiles without executing tests,223fresh/final223.
All jobs terminate empty and closed under the original resource guards. The
88.734-second compile-only observation is not a speedup or phase/cause attribution.

This preserves original control topology, not general caption-state creation/
deletion, missing-format synthesis, native counter interpretation or recalculation.
At the original compiler stage, source API v9, stored wrappers and general routes
were unchanged; subsequent fresh stored binding is described above. Full effective styles,
flow/protection, CAS, execution, publication and Native remain unqualified.
Official158/249,next165,P09/A12/A13 OPEN,goal ACTIVE and separate Native011
approval/current-input qualification remain.

## Fresh stored service access for caption content

`prepare_caption_content_candidate` binds text/layout/style requests to one fresh
authenticated source, whole Form proof and joined state. Character/paragraph/named
style requests include original caption/node IDs, family, exact declaration ID and
fingerprint, and changed/no-op status. The original text/layout request checker is
shared without changing legacy receipt shapes. No per-request source/state import,
cached service authorization, source overwrite, ingest or revision commit is added.

Every prepare/verify/byte exposure keeps current scope/head/ACL/quarantine/AEAD and
complete original reconstruction checks. The final head read is inside the writer
callback before invoking the consumer. A test-only repository advances the real
shared in-memory head at this last read; no consumer callback occurs. Fresh access
is not atomic CAS or authority to retain plaintext access, and execution/publication
routes remain denied. Normal service effects are metadata/download read audits.

`p09-361-stored-caption-content-components001.v1.json`: new6 plus affected existing
mixed6, all12pass,212fresh/final212,cleanupTrue. Coverage includes all three request
families and no-ops, complete output, ACL revocation, quarantine, ciphertext tamper,
head movement, foreign scope/original/state/proof/bytes, invalid selectors, protection
and finite limits. The53 previous test bodies are preserved by exact include removal.
002 removes only a new unused import and recompiles without executing tests:
213fresh/final213,cleanupTrue. The original unrelated warning remains.

The previous62 distinct cases include6 affected stored mixed cases, which were
requalified, not blindly retained. The other56 retain their original scope/input
evidence; adding the6 new cases gives68 scoped component cases, not queue credit.
The001 field `retained_core_and_style_scope62_without_reexecution` does not distinguish
this overlap. `p09-361-stored-caption-content-closure003.v1.json` corrects its scope
against exact case-name sets and fresh current source pins without altering001.

The P09 roadmap still requires reproducible real outputs, preserved originals and
qualified targets. Actual source API v9 and general typed routes remain unchanged.
Full sequence/recalculation, effective styling, flow/protection, CAS, execution,
publication and Native remain unqualified. The subsequent original number-stream
request/output work is described above; its stored-service binding remains next.
Official158/249,next165,P09/A12/A13 OPEN,goal ACTIVE and separate Native011
approval/current-input qualification remain.

## Atomic caption content and declared style references

The joined source state now compiles text, layout and character/paragraph/named
style references in one original-bound transaction and complete output readback.
Targets must be exact original caption run/paragraph selectors and uniquely located
original header declarations with matching subtree fingerprints. The retained
declaration index avoids per-request header/ZIP/XML re-import. Effective/inherited
styling is not inferred. Existing text/layout APIs and receipt shapes remain intact;
a separate content receipt binds the joined input and all style changes.

Missing unqualified numeric attributes use one sorted grouped insertion per node,
without relaxing overlap checks. Invalid names, namespace declarations, overwrites,
empty groups, source drift, duplicate/wrong-family/wrong-owner selectors, ambiguous
declarations, limits and observed ancestor/descendant protection reject atomically.
No-op lexical spelling, unchanged header/number controls including stored19, and
all expanded bytes outside the selected edits remain exact. A96-request case
checks4N protection visits for one part, not a full scan for each request.

Evidence: `p09-361-caption-style-content-components003.v1.json` retains41 passes
from001 and executes only the two corrected failing fixtures, with206fresh/final206.
Unknown namespaced ID-like attributes and unsupported nested caption owners still
reject under the original ID-index/coverage conditions. The corrected test file
round-trips exactly to001; production and the41 passed test bodies are unchanged.
The failed001 and reader-boundary-only002(steps0) remain immutable. The original43
used the two-package feature-union graph; the retry2 used core-only scope. These
are scoped results, not one new43-case run in the same graph.

`p09-361-caption-style-content-regressions001.v1.json` adds unchanged patch13/frame6
regressions:19pass,209fresh/final209,cleanupTrue. Thus62 distinct component cases
are covered across the retained and current scopes, with no replay of the41 passed
cases. Existing target restrictions in the Cargo helper remain unchanged. The
separate four-target core regression invocation explicitly bound all19 names and
complete harness groups under the same owned resource guards.

The actual source API remains v9 and execution/publication routes are unchanged.
The stored-service content candidate now uses fresh access/source/head checks above.
Effective style, full sequence/recalculation, flow/protection, CAS, execution,
publication and Native remain unqualified. Official158/249,next165,P09/A12/A13 OPEN,
goal ACTIVE and separate Native011 approval/current-input qualification remain.

## One Cargo graph for exact component case sets

`component_cargo_batch_v1` builds an explicit two-package/three-integration-target
invocation and exact case IDs. It has no launcher or authority cache; the original
owned launcher, source pre/post reads, one-core/BelowNormal/RAM/commit safeguards,
single test thread and32768-byte complete capture remain mandatory. Original
64-argument/24000-byte UTF-16 budgets are retained. The output validator requires
all declared target case sets, counts and successful complete summaries; missing,
extra, duplicate, partial, ignored, failed or fabricated-summary output rejects.

[Multiple package selections unify dependency features](https://doc.rust-lang.org/cargo/reference/resolver.html#features),
so this is a separately qualified build scope, not promotion of an older PASS.
Evidence: `p09-361-component-cargo-batch-qualification001.v1.json`, pure15 plus the
same actual37 cases(core24/source1/stored12),201fresh/final201,cleanupTrue. Rust code
and test bodies are unchanged. The real case execution used one Cargo invocation,
58 arguments/12166 bytes. Subsequent same-graph no-run preparation emitted no
compile announcement and executed no tests. Existing warning/entry points and
Native dispatch remain unchanged. Resource details are in CURRENT_STATE.md and
the receipt. Package-level compile announcements and the1.734-second warm check
are not rustc-unit counts or a general cold-build speedup benchmark.

This helper is now the opt-in path for the qualified component scope with the
existing guards; changed source/scope and failed/partial results require current
qualification. Other core71/source CLI40/services/249 cases, heavy binary and
Hangul/COM/Native were not executed. General sequence/state, numbering recalculation,
full protection/flow, CAS/execution/publication and Native remain. Official158/249,
next165,P09/A12/A13 OPEN,goal ACTIVE and separate Native011 approval/current-input
qualification remain.

## Joined source state as the caption output compiler input

`ImportedCaptionSourceState::lower_edit_batch_candidate` reuses its exact admitted
numbering/frames after whole fresh-source verification. The whole Form proof entry
also requires the same original object, assembled state, proof and fresh bytes.
Both tighter and looser admission limits reject reuse. A private candidate binds
the full joined source receipt to the actual output receipt. Full output import/
readback and original protection/error/outside-edit preservation remain. The large
lowering body is non-generic rather than duplicated per source-proof callback.
This is immutable input-model reuse, not cached service/ACL/head authorization.

Evidence: `p09-361-caption-source-state-compiler-components002.v1.json`, new6 plus
affected core18/stored mixed6/text6/actual source API1=37pass,198fresh/final198,
cleanupTrue. Exact inverses preserve original models, compiler body and89 core
cases.001 stopped before any command because its inverse reader could not locate
the trailing blank-line boundary. The new six test bodies moved unchanged into
support/caption_source_state_output.rs; a short include declaration replaced the
brittle boundary search. Original001 and the existing unused-import warning remain.

Tests cover same-byte/document-ID foreign objects, foreign state/proof/bytes,
different budgets, exact old output/receipt equality, original rejection cases,
multiple parts and192-request reverse-order output equality. Other core71/source
CLI40/services/249 cases, heavy binary and Hangul/COM/Native were not rerun. Resource
details are in CURRENT_STATE.md and the receipt. Build preparation still dominates;
no wall-time speedup or Windows-freeze-cause conclusion is claimed.

General sequence/state requests and numbering recalculation, full flow/protection,
CAS/execution/publication and Native remain. Actual assessment v9 remains incomplete
with four unresolved stages, null report and exit3. Official158/249,next165,
P09/A12/A13 OPEN,goal ACTIVE and separate Native011 approval/current-input
qualification remain.

## Exact source caption state assembly in the actual assessment

`ImportedCaptionSourceState` consumes one original numbering/caption model and
joins context, frames and non-caption body projections. It checks exact owner/
caption/envelope/frame/body indices and all section/spine/XML control positions,
rejecting incomplete, duplicate or inconsistent links. Indexed joins and sorting
replace per-owner collection searches; no extra ZIP/XML/graph import or copies of
existing model vectors are added. Actual assessment uses this assembly while its
v9 response, receipts, incomplete/four unresolved/null report/exit3 stay unchanged.

Evidence: `p09-361-caption-source-state-assembly-components001.v1.json`, new6 plus
affected API/actual CLI41=47pass,194fresh/final194,cleanupTrue. Original models and
core83/CLI41 tests are unchanged; scoped inverses preserve root/API code. Tests
cover ten owner families, uncaptioned owners, missing versus NONE, zero starts,
stored19, ZIP reverse versus actual spine order, duplicate native IDs, complex
frames, mid-caption restarts, caption-only source drift and128 owners/64 captions/
192 events. Prior compiler/stored components, other core83/249 cases, heavy binary
and Hangul/COM/Native were not rerun. Resource details are in CURRENT_STATE.md and
the receipt; no wall-time speedup or freeze-cause conclusion is claimed.

This is lossless source-input assembly, not conversion into a purported complete
typed v1 sequence. It does not infer labels, effective styles, zero continuation
rules or native recalculated numbers. The pinned [official model](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/AutoNumNewNumType.cpp)
serializes integers; the [section help](https://help.hancom.com/hoffice120/ko-KR/Hwp/format/section/section.htm)
distinguishes section starts from arbitrary in-section restarts. Complete sequence/
state request and output compilation, full protection, CAS/execution/publication
and Native remain. Official158/249,next165,P09/A12/A13 OPEN,goal ACTIVE and separate
Native011 approval/current-input qualification remain.

## Stored source caption text and layout batch authorization

`prepare_caption_edit_batch_candidate` reuses one current service source and whole
Form proof for both edit families in the shared compiler. All changed/no-op texts
bind source caption/text IDs, SHA-256 and UTF-8 length; layouts bind source caption
ID, the five requested values and change status. Each verify/exposure rechecks
scope/head/ACL/quarantine/AEAD and whole original, with a final head check inside
the writer-integrity callback. Normal paths produce read audits only, preserve
original/head and exclude request plaintext from receipt/Debug. Execution and
publication routes remain denied; these reads do not implement atomic service CAS.

Evidence: `p09-361-stored-caption-edit-batch-output-components001.v1.json`, new6pass,
old47filtered,192fresh/final192,cleanupTrue. Tests cover both request families,
changed/no-op bindings, full output readback, repeated fresh access, revoked ACL,
quarantine/tamper, moved head, foreign scope/original/proof/bytes and whole rejection
of invalid mixed requests. Exact inverses preserve prior provider and47 tests.
Compiler19/core83/source CLI41/other services/249 cases, heavy binary and
Hangul/COM/Native were not rerun. The original unused-import warning remains.
Resource details are in CURRENT_STATE.md and the receipt.

This is isolated memory repositories, fixture scanner and synthetic-key component
coverage, not live issuer/scanner qualification. Complete caption state/sequence,
full protection, CAS/execution/publication and Native remain. Actual assessment v9
stays incomplete/four unresolved/null report/exit3. Official158/249,next165,
P09/A12/A13 OPEN,goal ACTIVE and separate Native011 approval/current-input
qualification remain.

## Atomic caption text and layout output compilation

`lower_caption_edit_batch_candidate` combines plain caption text leaves and the
five native layout attributes in one source verification, numbering/frame model,
patch/writer and full output import. It does not chain intermediate packages.
The existing text batch API and receipt delegate to the shared compiler unchanged.
Invalid, duplicate, foreign, protected or over-limit requests reject the whole
candidate; semantic no-ops retain lexical bytes. All bytes/parts outside selected
edits and stored19 remain unchanged. Input is never overwritten. This is an atomic
memory candidate, not service CAS, complete sequencing or execution authority.

Evidence: `p09-361-caption-edit-batch-output-components003.v1.json`, retained002
executions of new6+affected text6+stored6+actual source API1=19pass,190fresh/final190,
cleanupTrue,zero tests rerun.001 stopped before any command on a test inverse-reader
newline error.002 commands all exited0 with19pass; only the final collector's
tuple/list equality failed.003 independently verifies exact current source/input,
retained outcomes and all three terminal/empty/closed Jobs. Original001/002 and all
lossless samples remain. The stored test's existing unused-import warning remains.

Original single text/layout code is unchanged; scoped inverse checks preserve the
root, original text engine and77 tests. Differential cases cover64 original layout
guard combinations, protected descendant tables/cells/size, multiple parts, exact
Form proof, no-op aliases and independent single output lowerers.192 requests
(text128/layout64) share four element passes on one part, with equal expanded output
under reverse request order. This is a work-bound check, not wall-time or freeze
causation evidence. Other core71/source CLI40/services/249 product cases, heavy
binary and Hangul/COM/Native were not rerun. Resource details are in CURRENT_STATE.md
and original002.

Stored service binding followed in the component above. Complete caption
state/sequence, full protection, CAS/execution/publication and Native remain. Actual assessment v9 stays
incomplete/four unresolved/null report/exit3. Official158/249,next165,P09/A12/A13 OPEN,
goal ACTIVE and separate Native011 approval/current-input qualification remain.

## Source caption frames in the actual API and CLI

The actual source assessment v9 returns `caption_frame_import` and `caption_frames`
from the existing original numbering/caption model, without another ZIP/XML/graph
import. Frames bind paragraph/run/style/text observations to the same original
caption/object/control IDs. An API-returned selector drives the real plain-text
batch candidate; reassessment checks the requested hash/UTF-8 length, unchanged
stored19 and mutation-stable non-caption body. No label/separator, effective style
or recalculated sequence is invented. JSON and Debug exclude plaintext.

Evidence: `p09-361-source-caption-frames-cli-components001.v1.json`, affected38 plus
new3=41pass,186fresh/final186,cleanupTrue. Exact inverse checks preserve v8 source
and38 tests apart from seven schema expectations. Actual CLI/API equality, five
style reference states, invalid-ID rejection without partial output, original
preservation and exact final JSON limits passed. Prior lower frame/batch/stored
components,249 product cases, heavy binary and Hangul/COM/Native were not rerun.
Resource details are in CURRENT_STATE.md and the receipt.

Assessment remains incomplete with four unresolved stages, null validation report,
exit3 and false qualification/authority flags. Complete caption state/sequence/
compiler, full protection, service CAS/execution/publication and Native remain.
Official158/249,next165,P09/A12/A13 OPEN,goal ACTIVE; separate Native011
authorization and current-input qualification are unchanged.

## Stored source caption text batch authorization

`prepare_caption_text_batch_candidate` performs one fresh service source read and
whole Form reconstruction for the batch, reusing the exact original proof in the
pure lowerer. Changed and no-op requests bind source caption/text IDs, requested
SHA-256, UTF-8 length and change status. Every verify/exposure rechecks current
scope/head/ACL/quarantine/AEAD and the whole source; the final head check is inside
the writer-integrity callback. Request plaintext is absent from receipts/Debug.
Candidate generation is atomic in memory, not service CAS; no ingest, revision
commit, publication or original overwrite occurs. Executable routes remain denied.

Evidence: `p09-361-stored-caption-text-batch-output-components001.v1.json`, new6pass,
old41filtered,185fresh/final185,cleanupTrue. Tests cover changed/no-op binding,
repeated fresh exposure, original/head preservation and read-only audits, revoked
ACL, quarantine, ciphertext tamper, moved head, foreign scope/proof/bytes and whole
batch rejection without partial exposure. Exact inverse checks preserve the prior
service source and41 tests. Previously passed pure6/single9/stored6/sourceCLI38/
core71/product41/249 cases and Hangul/COM/Native were not rerun. Resource details
are in CURRENT_STATE.md and the receipt.

These are isolated memory repositories, fixture scanner and synthetic-key
components, not live issuer/scanner qualification. Complete caption state/sequence/
compiler, full protection, service CAS, CLI/execution integration and Native remain.
Official158/249,next165,P09/A12/A13 OPEN,goal ACTIVE; Native011 still needs its
separate authorization and current-input qualification.

## Batched plain caption text output

`lower_caption_text_batch_candidate` verifies one input and reuses one numbering/
frame model, patch/writer and full output import for the entire request. Exact
source anchor-index/fingerprint lookup replaces per-leaf XML search. Two element
passes build observed protection once per changed part;128 leaf edits reuse one
part guard. One invalid/protected/duplicate request rejects the whole candidate,
while semantic no-ops retain original lexical bytes. Candidate construction is
atomic in memory, not service CAS/publication, and never overwrites input.

Evidence: `p09-361-caption-text-batch-output-components006.v1.json`, five retained
passes from001 plus only one corrected case rerun in006, 183fresh/final183,
cleanupTrue.128 protection combinations match the original single path; tests cover
single-output equivalence, empty/entity/namespace/CR/Unicode/no-op cases, multiple
sections, exact Form proof reuse,128-leaf work bounds, order-independent outputs,
whole-batch failure and byte preservation. Original code inverse/core71 prefix
were checked. Production code and five passing cases were unchanged during fixture
repairs. Original001/002 fixture admission failures,003 reader-only newline failure
(steps0),004/diagnostic005 extra table-lock admission expectation failures remain.
Resource details are in CURRENT_STATE.md and receipts, not a wall-time or PC-freeze
causation benchmark.

Prior single-output9/stored6/sourceCLI38/core71/product41/249 cases, heavy binary
and Hangul/COM/Native were not rerun. Stored batch binding followed in the section
above. Batch execution/CLI mutation integration, complete caption state/sequence/
compiler, whole protection and Native acceptance remain open.
Official158/249, remaining91, next165, P09/A12/A13 OPEN, P10 not started, goal ACTIVE
and separate Native011 approval/current-input qualification remain unchanged.

## Stored source caption text candidate binding

Stored caption text preparation/verification/every byte exposure rechecks current
scope/head/ACL/quarantine/AEAD and the complete original form reconstruction.
Preparation reuses that exact original-bound proof without another input import.
Output exposure requires writer integrity and a final head check inside its callback;
this is not atomic CAS or retained authorization. Source caption/text IDs and request
SHA/UTF-8 length bind the private output. Request plaintext is not stored in receipts.
Only normal source metadata/download read audits occur; no ingest, revision commit,
source overwrite, execution or publication is added.

New6 only: 6pass/35filtered, 176fresh/final176, cleanupTrue. Evidence:
`p09-361-stored-caption-text-output-components001.v1.json`. Existing source/provider/
layout/caption models and all previous tests were checked by exact inverse. Revoked,
quarantined, tampered, advanced-head and foreign scope/proof/byte paths block callbacks;
original selector/protection/value/no-op/limit rejections remain. Prior pure-output9,
sourceCLI38, original35, 249 cases, heavy binary and Hangul/COM/Native were not rerun.
Resource details are in CURRENT_STATE.md and the receipt.

These tests use isolated memory repositories, a fixture scanner and synthetic keys,
not live issuer/scanner/deployment or Native acceptance. Complete caption state/
sequence/compiler and whole protection remain open. Executable routes are denied
after fresh verification. Official158/249, remaining91, next165, P09/A12/A13 OPEN,
P10 not started, goal ACTIVE and separate Native011 approval/current-input qualification remain.

## Source bound caption plain text output candidates

`lower_caption_text_candidate` changes one exact imported plain hp:t leaf using
its caption/text source ID pair, never caller offsets, numeric native IDs or guessed
label spans. Original ReplaceLeafText, shape v6 ID, preservation, patch and writer
checks remain. Full output source/number/frame import verifies requested semantic
text and exact expanded bytes outside the selected leaf edit. Self-closing leaves
retain their original QName/attributes. Semantic no-ops are rejected without lexical
rewriting. Candidate creation never overwrites the input file.

Only the semantic leaf path now emits CR as a character reference; generic
text/attribute escaping is unchanged. Existing leaf2 plus new CR1 and caption-output6
passed: 9pass, 174fresh/final174, cleanupTrue. Evidence:
`p09-361-caption-text-output-components001.v1.json`. Original structure/output/leaf
code inverse and entire original core65 test prefix were checked. Cases cover
empty/entity/namespace/Unicode/escaped text, other content/parts/styles/numbers,
drift/foreign/cross-caption/opaque/number selectors, observed locks/table protection,
duplicate IDs and finite input/writer bounds. An exact original-bound Form
reconstruction avoids another input ZIP/XML/graph import and rejects foreign
proofs or fresh bytes. The captured rectangle memory candidate preserves stored19
and leaves the original file unchanged.

Total61.531s, owned33.687/2.906s, tests0.10/0.50s, Job CPU18.578/2.469s,
peaks1398.11/547.86MiB, system CPU maximum24.67%, available RAM minimum25.9173%.
Original one-core, BelowNormal, CPU cap6.25%, RAM/commit95%, lossless samples and
both terminal empty/closed Job checks remain. This is not complete caption
state/sequence/output compilation, whole protection, service execution/publication
or Native/save/render acceptance. CLI v8/core65/sourceCLI38/249 product cases,
heavy binary and Hangul/COM/Native were not rerun. Official158/249, remaining91,
next165, P09/A12/A13 OPEN, P10 not started, goal ACTIVE and separate Native011
authorization/current-input qualification remain unchanged.

## Source caption text style and number control frames

`ImportedCaptionNumbering::import_frames` binds original caption/subList/p/run
frames and existing number controls without another ZIP/XML/graph import or
per-caption full-token/style parse. Plain direct-run hp:t leaves retain text order
and spaces; no label/separator split or default style/counter is inferred. Lexical
CRLF/CR normalization precedes character-reference expansion, so `&#13;` remains
CR, following [XML 1.0 end-of-line handling](https://www.w3.org/TR/xml/#sec-line-ends).
Rich/comment/mixed/foreign content and multiple paragraphs or number controls
remain explicit, not concatenated into a qualified simple caption.

Character/paragraph/named style references match exact source header declarations
and retain missing-reference, missing-declaration, ambiguous and unverified-location
states. A unique declaration is not inherited/effective font or Native qualification.
Plain text is available only through an explicit original-snapshot getter; serialized
observations and Debug are hash-only/redacted and are not fresh service authorization.

Only six new tests ran: 6pass/59filtered, 171fresh/final171, cleanupTrue.
Evidence: `p09-361-caption-source-frames-components001.v1.json`.
Original code inverse and entire59-test prefix were checked. Tests cover exact
text/number/style binding, complex content, table/note nesting, declared spine order,
duplicate native IDs, non-caption controls, bounds/fresh drift and the immutable
captured rectangle's stored19. Total89.844s, owned65.735s, tests0.19s, Job CPU21.203s,
peak1396.21MiB, system CPU maximum39.18%, available RAM minimum26.2586%.
Original one-core, BelowNormal, CPU cap6.25%, RAM/commit95%, lossless samples and
terminal empty/closed Job guards remain.

This is a library source-assembly input, not complete typed state/sequence,
counter evaluation, output compilation, flow/protection or Native acceptance.
The actual CLI remains v8; prior sourceCLI38/context/projection/index/layout/stored,
249 product cases, heavy binary and Hangul/COM/Native were not rerun. Official158/249,
remaining91, next165, P09/A12/A13 OPEN, P10 not started, goal ACTIVE and separate
Native011 authorization/current-input qualification remain unchanged.

## Source context and object state in the actual product API and CLI

The actual package assessment API/CLI now emits v8 with document starts, all
known owners including uncaptioned owners, declared spine/XML control order and
separate non-caption object projections. It reuses one original numbering/caption
model and immutable source graph without another ZIP/XML/graph import or caller
state assertions. Missing numbering types, zero and stored19 retain their source
values, not inferred defaults or resolved numbers. Legacy target/caption/numbering/
SDK receipts and field/security coverage remain unchanged.

New3 plus affected original35 API/actual-CLI tests: 38pass, 169fresh/final169,
cleanupTrue. Evidence: `p09-361-source-caption-context-cli-components001.v1.json`.
The entire original v7 implementation and original test prefix were compared by
exact inverse apart from six schema expectations. The changed entrypoint/response
required these35 cases; underlying core/context/projection, direct-product35,
index54, layout/stored, 249 product cases, heavy binary and Hangul/COM/Native were
not rerun. Malformed/duplicate/hidden document starts and unsupported numbered
owners produce no partial CLI output. Input files remain unchanged and exact
final JSON bounds and private-value non-disclosure were checked.

Total91.625s, owned66.094s, tests3.22s, Job CPU25.750s, peak1399.24MiB;
system CPU maximum21.09%, available RAM minimum26.4718%. Original one-core,
BelowNormal, CPU cap6.25%, RAM/commit95%, lossless samples and terminal empty/closed
Job guards remain. Normal output is still incomplete, four unresolved stages,
validation_report=null and exit3. Complete typed state, counter semantics,
flow/protection, the general compiler and Native acceptance remain open.
Official158/249, remaining91, next165, P09/A12/A13 OPEN, P10 not started, goal ACTIVE
and separate Native011 authorization/current-input qualification remain unchanged.
Next is assembly of source caption content/style and controls into typed sequence/state.

## Non caption object state projections

`ImportedNumberingContext::project_object_states` produces a separate object-body
digest with each admitted existing caption subtree replaced by a fixed marker.
Full caption envelopes remain independently fingerprinted. Other raw bytes,
resolved namespaces, caption presence and position remain bound. Whole-source
verification still rejects changes inside masked captions. Child digests are
computed once per XML element and reused for nested owners; no graph/ZIP/XML
reimport, per-owner subtree copy or overlapping raw subtree hashing is added.
Depth4/6/8 work checks visited exactly the XML element count and hashed no more
raw bytes than that XML's size. Original source import fingerprint work is unchanged.

Six distinct tests passed: four retained from components002 plus only the two
failed fixture cases rerun in components003. Evidence:
`p09-361-caption-object-state-projection-components003.v1.json`.
The original components001 private-function test compile error and components002
forbidden-PI/over-depth fixture failures are preserved. Only those fixtures changed;
original admission limits, production code and four passing cases are unchanged.
Components003: 168fresh/final168, cleanupTrue, total25.953s, owned1.954s,
tests0.05s, Job CPU1.828s, peak544.24MiB, system CPU maximum72.66%, available RAM
minimum29.0199%. Original resource/cleanup guards and lossless samples remain.

This is an existing-caption-edit-stable body projection, not insertion/deletion,
complete typed state, counter interpretation, flow/protection, the general compiler
or Native qualification. CLI v7 and false qualification flags remain unchanged.
Official158/249, remaining91, next165, P09/A12/A13 OPEN, goal ACTIVE and separate
Native011 authorization/current-input qualification remain. Prior core53,
sourceCLI35, index54, 249 product cases, heavy binary and Hangul/COM/Native were not rerun.

## Document starts and complete known owner observations

`ImportedCaptionNumbering::import_context` binds six explicit document `beginNum`
values, all ten known owner families including uncaptioned owners, and numbering
controls to the original graph. Missing `numberingType` stays unknown and differs
from explicit `NONE`. Owner/control positions follow the actual spine and source
XML, not ZIP order or a qualified native counter/render order. Zero is preserved,
not interpreted as an implicit default or continuation rule. Existing imports and
anchor fingerprints are reused without another ZIP/XML import or per-caption parse.
Invalid header placement, unsupported numbered owners, limits and source drift fail
closed. Original implementation inverse and existing test prefix were checked.

Only the six new context tests ran: 6pass/47filtered, 164fresh/final164, cleanupTrue.
Evidence: `p09-361-numbering-document-owner-context-components001.v1.json`.
Total107.500s, owned84.235s, tests0.12s, Job CPU44.562s, peak1855.35MiB;
system CPU maximum31.82%, available RAM minimum26.4467%. Original one-core,
BelowNormal, CPU cap6.25%, RAM/commit95%, lossless samples and terminal empty/closed
Job checks remain. Prior core47/sourceCLI35/index54/249 product cases, the heavy
form_stored_provider binary and Hangul/COM/Native were not rerun.

Whole-owner subtree fingerprints include mutable captions; they are not a stable
typed object-state projection. Complete sequence/state interpretation, mutable
projections, flow/protection, the general compiler and Native acceptance remain
open. Source CLI v7 and false qualification flags are unchanged. Official158/249,
remaining91, next165, P09/A12/A13 OPEN, P10 not started, goal ACTIVE and separate
Native011 authorization/current-input qualification remain unchanged.

## Borrowed indexes for caption state validation

Caption validation and expected-number calculation now share call-local borrowed
section/object/sequence indexes instead of repeatedly scanning complete vectors.
Lock preservation uses find-first target sequence/caption maps, unchanged
last-entry object maps and a changed-section set. Counter keys borrow sequence
IDs instead of cloning them for each lookup. No state/flow/plan/projection check,
lock, limit, error or existing overflow rule is removed and no authorization or
cross-call validation cache is introduced.

The original validation/counter/lock algorithms remain cfg(test) oracles. An exact
whole-source inverse preserves existing schema, serialization and all old tests.
Differential tests cover1555 small inputs and reversed orders,512 lock masks with
eight target variants, missing/ambiguous selectors, stale caches and input JSON.
The8192-record private counter case has16388 index-record/caption visits. This is
not linear wall time, public full-state acceptance or Native evidence; tree/sort
cost remains logarithmic and the slow legacy oracle was not run at that scale.

Evidence: `evidence/p09-361-caption-index-optimization-components001.v1.json`.
Four new cases plus the original sealed-plan case,14 domain cases and35 direct
product API cases passed:54 total,159 fresh/final hashes and confirmed cleanup.
Total time was349.656 seconds; owned commands84.422/24.453/215.204 seconds,
tests1.23/0.09/0.56 seconds and Job CPU18.484/23.141/52.578 seconds. Peak private
memory was1536.72/1855.00/1869.82 MiB, system CPU maximum80.66 percent and minimum
available RAM25.6854 percent. Original resource protections and lossless sampling
remain. Neither build-wait attribution nor Windows-freeze causation is established.
Source CLI/numbering/layout/service suites, serialization/cycle-specific cases,
the249-product queue, heavy form_stored_provider binary and Hancom/COM/Native were
not replayed. Source sequence/state/compiler binding remains next; acceptance
stays158/249,91 pending, next case165; P09 OPEN, P10 not started, goal ACTIVE.

## Native numbering source import and actual CLI

ImportedCaptionNumbering binds every admitted native autoNum/newNum/startNum to
its actual section and represented paragraph or exact caption/subList/p/run/ctrl
ancestry. Header/nonspine/opaque/unrepresented controls, missing or invalid native
values, duplicate formats/starts and finite limits fail closed. Seven categories,
22 official format names and only seven existing typed-format vocabulary matches
are recorded. Other formats have no guessed typed mapping. Affix/user strings are
hash-only and existing source fingerprints are reused without per-caption parsing.
Stored signed INT numbers and u32 section starts, including zero, are observations,
not resolved sequence numbers or evidence of native recalculation.

Section starts and mid-section number restarts must remain distinct. The
[official section help](https://help.hancom.com/hoffice120/ko-KR/Hwp/format/section/section.htm)
describes both mechanisms. Pinned official model source files bind native
attribute/enum vocabulary only, not complete sequence behavior. The original
complete rectangle package's stored19 remains19, not a fabricated recalculated1.

reference-source v7 adds numbering_import, numbering_controls and
numbering_section_starts, reusing the number importer's retained original caption
model instead of importing captions twice. Original legacy target/caption/SDK
receipts, whole field/security coverage, incomplete status, four unresolved stages
and null validation_report remain. Sequence interpretation, native recalculation
and complete auxiliary state qualification stay false.

Evidence: `evidence/p09-361-source-caption-numbering-section-limit-components004.v1.json`,
with original core001, actual-CLI002 and zero-test preflight003 preserved. Six core
cases and35 affected API/actual-CLI cases cover41 distinct scopes across runs.
After adding standalone section-count enforcement, only its changed core case ran;
the other five core and35 CLI results were retained. Exact v6-source/test inverses
preserve all prior cases except five schema expectations. Final freshness was
158/158 with confirmed cleanup, not a simultaneous41-case rerun.

Core/CLI/boundary totals were41.140/48.016/57.859 seconds; owned commands
19.110/26.047/35.234 seconds and tests0.11/2.02/0.01 seconds. Job CPU was
17.641/23.453/18.594 seconds, peak private memory1371.65/1383.20/1373.27 MiB.
System CPU maximum across the runs was62.30 percent and minimum available RAM
29.8439 percent. All original resource/cleanup protections remain. New component
resource tables use lossless_columns_v1 with exact value/order roundtrip; sampling
and Native policies are unchanged. Typed sequence/state/compiler binding and
Native acceptance remain pending. Official acceptance stays158/249,91 pending,
next case165; P09 OPEN, P10 not started, goal ACTIVE.

## Stored source caption layout candidate binding

PreparedStoredCaptionLayoutCandidate binds layout output to the original stored
form model and current service source access. Preparation reuses an original-bound
VerifiedFormReconstruction rather than importing the source ZIP/XML/graph again.
The original pure lowerer still runs its whole verify_source through the same
private path. Its layout, protection, ID, patch/writer and complete output-readback
logic was checked by exact inverse; existing service/test bytes are preserved.

Every verify and byte exposure freshly reads and reconstructs the original source
through the unchanged scope/head/ACL/quarantine/AEAD checks. Immutable receipts
and writer integrity precede the final head check inside the byte callback. No
cached proof grants access, no caller graph/verification flag is accepted, and no
production ingest/commit/publication is added beyond normal read audits. The
executable route remains denied; repeated head reads do not establish atomic CAS.

Evidence: `evidence/p09-361-stored-caption-layout-output-components001.v1.json`.
Only the six new stored-layout cases ran: six passed,148 fresh/final hashes and
cleanup confirmed. Prior source-layout6/source38/auxiliary41/stored-caption6,
the249-product queue, large form_stored_provider binary and Native were not rerun.
Total time was282.891 seconds, owned command260.063 seconds and test0.12 seconds.
Job CPU was24.266 seconds, peak private memory1369.26 MiB, system CPU maximum
30.98 percent and minimum available RAM36.3097 percent. The elapsed/CPU-time gap
is observed; specific build-lock/IO or other wait attribution remains unverified.
One core, BelowNormal,6.25 percent Job CPU cap and original RAM/commit95 percent
and Job protections were preserved, with terminal empty/closed cleanup.

These are isolated repository/fixture-scanner/synthetic-key component results,
not live issuer/scanner, complete caption sequence/state/protection, general
auxiliary compiler, execution/publication or Native/save/reopen/render acceptance.
Original numbering semantics and typed state/compiler binding remain next.
Official acceptance remains158/249 with91 pending and next case165; P09 is OPEN,
P10 not started and goal ACTIVE. Native011 still needs separate authority/current inputs.

## Source preserving caption layout output

CaptionLayoutOutputCandidate changes only the selected caption's five native
layout attributes. Selection uses source anchors, not numeric object IDs. Only
semantically different values are patched; quotes/order, equivalent lexical
spellings, namespaces, unknown attributes, numbering, subList/content and other
expanded package parts remain exact. Complete output import and a streaming
comparison outside the bounded value spans validate preservation without a full
expected-section buffer. The original patch/writer/ID/protection code is unchanged;
the candidate uses the existing shape v6 ID profile and observed protection checks.

Six distinct cases combine one protection pass from001, one original complete
rectangle-package pass from003, two passes from004 and only the final two fixture
cases from005. Positive synthetic fixtures needed actual style/border declarations,
the first stored mimetype entry and unique object/paragraph IDs. Dangling-reference
and duplicate-ID negatives remain. Failed001/diagnostic002/003/004 are preserved,
including the new adapter's initial incorrect field-v3 ID profile. The original
7886-byte rectangle package remains SHA-256
fe58ad76019828a0df0051fc54b97f98f04de82a8c46e7fc1d8b68ad5f2fbc91.

Evidence: `evidence/p09-361-source-caption-layout-output-components005.v1.json`.
It confirms147 fresh/final hashes and cleanup, not a simultaneous six-case rerun.
Total time was71.922 seconds, owned command48.516 seconds, test0.25 seconds,
Job CPU1.875 seconds and peak private memory540.06 MiB. System CPU maximum was
18.52 percent and minimum available RAM35.8384 percent. This does not establish
the cause of the wall-time/CPU-time difference. One core, BelowNormal,6.25 percent
Job CPU cap and original RAM/commit/Job protections remain unchanged.

This is a writer-verified memory candidate, not complete caption sequencing,
typed auxiliary state/document protection, stored service execution/publication,
Native or save/reopen/render acceptance. Stored-service binding is recorded separately.
Official acceptance remains158/249 with91 pending and next case165; P09 is OPEN,
P10 not started, goal ACTIVE. Native011 needs separate authority/current inputs.

## Stored source caption service binding

StoredImportedReferenceCaptions reuses the original sealed Result provider and
fresh scope/head/ACL/quarantine/AEAD/whole-source verification on every access.
The operation-local VerifiedFormReconstruction is bound to the original model;
caption receipt, target and envelope inventories are reconstructed and compared
without another package parse. Each callback follows a final head check, not an
atomic CAS. Production adds normal read audits only, not ingest, commit or
publication, and the product route remains denied after fresh verification.

Six distinct component cases cover read-only/privacy/route, revoked ACL,
quarantine/AEAD tamper, advanced head with the same artifact, foreign scope/proof,
and finite limits/malformed envelopes. components003 retained five passes;
components004 ran only the corrected input/output-limit fixture case and passed.
The exact original three-file inverse and 141 fresh/final hashes were checked.
The isolated repositories, fixture scanner and synthetic keys do not qualify live
issuer/scanner access, numbering, complete state, atomic CAS or Native execution.

Evidence: `evidence/p09-361-stored-reference-caption-service-components004.v1.json`.
Its 22.094 seconds include 2.125 owned command seconds and 0.02 test seconds;
Job CPU was 1.938 seconds, peak private memory 642.19 MiB, system CPU maximum
25.29 percent and minimum available RAM 38.1353 percent. Cleanup was confirmed.
Original components001 CPU-stop, compile002 private-module import failure and
components003 invalid test-limit failure are preserved. The CPU-stop's verified
6.25 percent Job cap does not identify the cause of the 92.77 percent system
sample. Prior passed suites, 249-product queue, large form_stored_provider test
binary and Hancom/COM/Native were not replayed. Official acceptance remains
158/249, 91 pending, next case165; P09 remains OPEN and the goal ACTIVE.

## Source caption envelope import

ImportedReferenceCaptions binds original native caption parents to actual graph
object/table nodes, not numeric native IDs or caller object maps. It covers the
eight picture/shape tags, equation and table, including table/note descendants.
It reads required side/fullSz/width/gap/lastWidth without defaults and reuses the
original subList and whole-caption fingerprints. All admitted XML parts are
checked: header/nonspine/opaque/unsupported owners, duplicate captions/subLists,
malformed attributes and finite item/extent/output bounds fail closed. Source
fresh verification delegates to the original complete source/graph reconstruction.
There is no per-caption ZIP/XML reparse or subtree serialization; original table
grid, whole field coverage and security checks remain intact.

The actual reference-source CLI returns schema v6 with caption_import,
caption_envelopes and distinct Caption targets. Original bookmark/note/table v3
and object v1 receipts and the SDK are unchanged. Envelopes contain structural
attributes and hashes, not raw text or labels. This is not full native caption
schema or numbering qualification: UnverifiedSubListNumbering and false
sub_list_numbering_qualified/complete_auxiliary_state_qualified remain. The
response stays incomplete with four unresolved stages and a null report.
Original picture-caption/Native failures are not relabelled.

`evidence/p09-361-source-caption-envelopes-components001.v1.json` records six new
core and 32 changed source API/actual CLI tests passing, 136 fresh/final inputs
and cleanup. The core's 29 previous tests are filtered. The source's original
29 tests change only four schema expectations, then run with three new tests
because the entry/response changed. Exact original target/object/SDK/core-test
prefixes and whole source-v5 inverse comparison are preserved. Earlier
auxiliary41/cycle701/literal9, the heavy form_stored_provider binary, product249
and Native are not run.

Overall time was 85.844 seconds; owned commands took 42.500/22.578 seconds and
libtest work 0.12/1.21 seconds. Job CPU was 40.250/20.969 seconds and peak private
memory 1854.46/1367.26 MiB. Both jobs ended empty and closed. System CPU peaked at
19.92 percent and minimum available RAM was about 33.7862 percent. Original
one-core, BelowNormal, machine CPU cap 6.25 percent and memory guards remain.
Official acceptance is still 158/249, with 91 remaining, P09 OPEN and the goal
ACTIVE. Native011 still needs explicit authority and current input qualification.

## Borrowed state serialization and bounded JSON hashing

State Serialize now borrows all 31 original Draft fields in exact order instead
of cloning the whole state through serde into conversion. Original strict
Deserialize/TryFrom and legitimate state-transition clones remain. State, report,
caption, date, plan and edge-inventory digests stream the same JSON bytes into a
bounded hash sink without a discarded complete JSON buffer. Explicit canonical
JSON uses a byte sink that checks each chunk before appending. Both sinks latch
failure. Original validation, graph, locks, cache checks, schemas, error variants
and finite limits remain.

`evidence/p09-361-auxiliary-borrowed-stream-serialization-components001.v1.json`
preserves a pre-command field-name collector failure: its expression omitted
digits in sha256. No Rust tests were executed. After the collector correction,
`evidence/p09-361-auxiliary-borrowed-stream-serialization-components002.v1.json`
records private4/domain14/direct-product23 passing, 133 fresh/final inputs and
cleanup confirmed. The three new tests compare original Draft serialization,
Unicode escaping, SHA and Deserialize, exact/one-byte-short budgets, original
serialization errors and latched early refusal. Exact whole-source inverse
comparison preserves every original check and test outside these serialization
changes. The dedicated cycle701/16384 tests, source35, heavy form_stored_provider
binary, product249 and Native are not run.

Overall time was 159.594 seconds; owned commands took 15.265/71.828/51.516 seconds
and libtest work 0.02/0.10/1.08 seconds. Job CPU was 14.219/27.094/45.281 seconds,
with peak private memory 1528.67/1850.87/1867.08 MiB. All jobs ended empty and
closed. System CPU peaked at 33.52 percent and minimum available RAM was about
31.8891 percent. Original one-core, BelowNormal, machine CPU cap 6.25 percent and
memory guards remain. This proves removal of code-path copies/buffers and exact
results, not a wall-clock/heap reduction ratio or the cause of past PC freezes.
Official acceptance remains 158/249, with 91 remaining and P09 OPEN.

## Official help and unresolved filename and date semantics

Checked on 2026-10-18, Hancom's [file name help](https://help.hancom.com/hoffice120/ko-KR/Hwp/insert/date/date%28filename%29.htm)
describes a code that changes with the document name/path. That is not evidence
for frozen text semantics or a no-extension projection. Its [date format help](https://help.hancom.com/hoffice/multi/ko_kr/hwp/insert/date/date%28format%29.htm)
describes country and display-format selection, not the DATE/DOC_DATE HWPX
parameter-key mapping. These general help pages do not qualify the exact
installed Hancom2020 target. Projection refusal and unverified Native date
semantics therefore remain; no guessed mapping is implemented.

## Stored result descriptor file name binding

The existing StoredFormProvider now binds a filename candidate to the committed
result descriptor's exact full leaf name and UTF-8 digest. It retains the original
sealed head/node, tenant/scope, ACL, quarantine, AEAD, size and content checks, then
rechecks the descriptor and head. There is no caller artifact/name selector.
Document/revision/package binding, strict Request/Plan/Build and the original
preserving candidate lowerer are reused. Preparation adds normal read audits, not
result ingest, revision commit or publication.

Candidate verification and every byte callback freshly read the current source
and descriptor and compare provider scope, head, artifact, digest, complete bytes
and filename. The head is checked again immediately before callback invocation.
Revocation, quarantine, AEAD tamper and head advance block the callback. Route
qualification still fails after fresh checks. The new provider-scoped filename
flag proves only that stored result descriptor binding; it is not issuer identity
or a filesystem filename attestation. Original pure preparation/candidate flags
are unchanged. No-extension projection is explicitly unqualified rather than
guessing a stem rule. Complete caller state/style/flow, atomic CAS, issuer, the
actual service execution route and Native remain unqualified.

`evidence/p09-361-stored-file-literal-service-components001.v1.json` preserves a
test fixture ArtifactId namespace compile failure with zero tests. After that
fixture correction, `evidence/p09-361-stored-file-literal-service-components002.v1.json`
records six new tests passing, 17 filtered, 131 fresh/final inputs and cleanup.
The tests use isolated in-memory repositories, fixture scanner and synthetic
encryption material, not a live production issuer/scanner qualification. They
cover descriptor mismatch, strict JSON, unavailable projection, read-only service
effects, fresh ACL/quarantine/AEAD/head/scope refusal, callback non-invocation and
redaction. Original provider/tests remain exact prefixes; original services,
encryption, ACL and source lowerer are unchanged.

The current run took 22.704 seconds overall, 3.938 seconds owned and 0.14 seconds
in libtest. Job CPU was 3.094 seconds and peak private memory 662.82 MiB; the job
ended empty and closed. System CPU peaked at 12.69 percent and minimum available
RAM was approximately 38.6142 percent. Original one-core, BelowNormal, machine CPU
cap 6.25 percent and memory guards remain. Previous literal9/cycle32/source35,
the heavy form_stored_provider test binary, the 249 product queue and Native are
not run. Official acceptance remains 158/249, with 91 remaining, P09 OPEN and the
goal ACTIVE.

## File name literal preserving HWPX candidates

The actual source structure now creates an in-memory preserving HWPX candidate for
frozen leaf-name text at a native section/paragraph/run child boundary. Empty and
self-closing runs and all existing child boundaries are handled. Original namespace
context is carried into the run fragment; the original patch, ID, preservation and
writer profiles remain unchanged. Complete package/structure readback compares the
exact selected run, bytes outside that run, original run/paragraph attributes and
unchanged other parts. No source file is overwritten and no dynamic PATH field is
created. Original field-pair import rejects insertion inside a dynamic field cache;
observed table/cell protection, source drift, unsupported selection and limits remain
fail-closed.

The prepared product connection first re-verifies the original strict Request,
Plan and Build, then binds document, package and revision. It lowers only a collapsed
point payload; ranges, locked and opaque target semantics are explicitly rejected.
Caller style digests, authenticated source filename metadata, complete auxiliary
state/target flow, issuer/service authority and Native remain unqualified. Existing
preparation flags, including hwpx_lowered, remain false and the product route still
denies execution. The candidate is not acceptance of the complete original capability.

`evidence/p09-361-file-literal-output-candidates-components001.v1.json` preserves a
compiler failure with zero tests. Components002 records four passes and two source
admission failures; diagnostic003 executes only those two failures. The positive
fixtures contained attributes/comments rejected by the original source reader.
Those inputs remain negative cases.
`evidence/p09-361-file-literal-output-candidates-components004.v1.json` verifies exact unchanged inputs
for the four retained passes and an exact inverse of only the two failed fixture
corrections, then executes the corrected two and three new product tests.
Retained 4 plus corrected 2 plus new 3 are not a simultaneous nine-test run.
Closing checks are 102/102 with cleanup confirmed. One original captured package is
read for a memory-only candidate; no Native acceptance is inferred.

The current run took 78.297 seconds overall; owned commands took 7.562/54.547 seconds
and libtest work 1.26/0.04 seconds. Job CPU was 1.812/23.266 seconds and peak private
memory 537.49/1369.87 MiB. Jobs ended empty and closed. System CPU peaked at 22.39
percent and minimum available RAM was approximately 33.7829 percent. One-core,
BelowNormal, machine CPU cap 6.25 percent and existing memory guards remain intact.
Original source/API/tests are exact prefixes. Earlier cycle32/source35/auxiliary14,
the 249 product queue and Hancom/Native are not rerun. Official acceptance remains
158/249, with 91 remaining, P09 OPEN and the goal ACTIVE.

## Reference cycle traversal optimization

The original cycle detector restarted the same successor path from every source,
requiring O(V squared log V) work on a long chain. Completed paths are now memoized
only inside the current invocation, reducing traversal to O(V log V). Only actual
cycle members are reported; a tail reaching a cycle is not itself cyclic. This is
not a historical document-result cache or a skipped fresh verification. Public
schemas, report bytes/hashes, errors, locks, limits and the remaining domain code
and original tests are preserved by exact whole-source inverse comparison.

An independent copy of the old algorithm matches all 701 functional graphs with
up to four sources and their reversed input order. A 16,384-source chain takes
16,384 walk steps; a full cycle and a long tail reaching a 64-source cycle take
16,385. The private step hook provides a deterministic test bound, not a new
product work limit or weakened acceptance condition. The expensive old algorithm
is not executed on those large graphs.

`evidence/p09-361-reference-cycle-memoization-components001.v1.json` preserves four
passing Rust unit tests and a subsequent result-collector namespace mismatch
(tests versus private_tests). That failed overall record is not promoted.
Components002 rechecks every original execution input and runs only the pending
14 domain and 14 direct product tests. Retained 4 plus newly executed 28 are two
runs, not a simultaneous 32-test run. The current closing audit is 91/91 with
cleanup confirmed. Earlier source35, the 249 product queue and Native are not run.

Overall times were 24.671/121.078 seconds; actual libtest times were 0.19 and
0.08/0.21 seconds. Job CPU was 15.094 and 26.797/44.078 seconds, with peak private
memory 1520.32 and 1854.16/1866.63 MiB. All jobs ended empty and closed. System CPU
peaked at 21.21/30.10 percent and available RAM stayed above 30.9850/30.3109 percent.
Existing one-core, BelowNormal, machine CPU cap 6.25 percent and memory guards
remain in force. This removes quadratic verifier work; it does not establish the
cause of past PC freezes or Defender load, or a wall-clock speedup benchmark.
Filename output/source-style binding, full auxiliary import and Native remain
unfinished. Official acceptance stays 158/249, with 91 remaining and P09 OPEN.

## Actual source object and equation targets

The reference-source CLI now returns schema v5, adding source object and equation
targets with a separate object_target_import receipt. The original bookmark,
note and table import and the source-bound SDK keep their v3 receipt unchanged.
The new importer uses original graph node identities and immutable source anchors,
not numeric native IDs. It reuses subtree fingerprints without serializing or
reparsing object subtrees. Its nine native names match the original caption
classifier: pic, rect, ellipse, line, arc, polygon, curve, connectLine and equation.

Whole-source XML coverage rejects supported objects hidden outside represented
structure, including header/nonspine and opaque wrappers. Expanded namespaces,
per-family counts, aggregate inventory output and original fresh reconstruction
remain bounded. A target is active only in the sense that its exact source element
exists; native geometry, equation semantics, navigation and complete auxiliary
state remain unqualified. The response retains incomplete status, all four
unresolved stages and a null validation_report.

`evidence/p09-361-source-object-equation-targets-components001.v1.json` records
6 new importer tests and 29 changed source API/actual CLI tests passing, with
87 fresh/final inputs and cleanup confirmed. The core's 17 earlier tests were
filtered; the product's original 25 were checked with 4 new tests because the
source entry and response schema changed. Original core source/tests remain exact
prefixes. Exact inverse comparison preserves original product source/tests except
the new import/receipt merge and three v4-to-v5 schema assertions. Previous typed
preparation tests, the 249 product queue and Hancom/Native were not executed.

The run took 125.562 seconds overall; owned commands took 88.468 and 22.610 seconds,
with libtest work at 0.05 and 1.00 seconds. Job CPU was 19.500/21.047 seconds and
peak private memory was 1345.64/1358.73 MiB. Both jobs ended empty and closed.
System CPU peaked at 30.08 percent and available RAM stayed at or above 31.9967
percent. Existing one-core, BelowNormal, machine CPU cap 6.25 percent and memory
guards remained in force. Official acceptance is still 158/249, with 91 remaining;
P09 stays OPEN and Native011 is not executed.

## Six typed auxiliary product preparations

ReferenceAuxiliaryProductPreparation connects all six original operations:
caption state, date format, filename literal, correction mark, data link and
read-only validation. It reuses the original strict Request/Plan/Build with
caller-supplied typed state and document/revision/package/flow pins. Context,
fixed limits, original request and sealed plan are digest-bound without a
whole output buffer. Private request/plan/target/receipt storage has no mutable
or deserialization route. Fresh verify reconstructs the original operation.
The complete original read-only API and four tests remain exact byte prefixes.

Read-only preparation also rejects a declared state/flow mutation. Other target
flow pins are declarations, not observed graph flow. Source completeness, target
flow, HWPX lowering, execution authority and external-data access flags all remain
false. require_current_product_route always denies after fresh verification.
No file mutation, CLI/MCP/raw action, external source access or Native route is added.

Initial001 passes13 tests (old4/new9), no filters,31 first/final witnesses and
cleanupTrue. Coverage includes parity with all six original targets/receipts,
fresh identity/state/flow/limit drift, strict JSON, locks, caption/cache/report
checks, date-cache staleness and unrelated preservation, privacy/output bounds,
all19 correction kinds and eight data-link model combinations. After adding the
read-only flow guard and independent request/plan SHA oracles,002 runs only the
common six-operation parity test and new refusal test:2pass/12filtered,
32 first/final witnesses and cleanupTrue. The test-name union is14 with one
overlap, not a simultaneous current14-test execution. Exact inverse bytes/hash
preserve the original inputs outside these additions;001 remains its own scope.

001/002 take13.297/13.500seconds total, owned7.219/7.485 (libtest0.15/0.05),
Job CPU5.531/5.391seconds and peaks661.78/661.66MiB. Both owned trees end empty
with closed handles. System CPU maxima21.21/12.11percent and available RAM
minima28.5156/28.5739percent retain one core, BelowNormal,6.25percent CPU cap
and original RAM/commit/Job protection. Evidence:
`evidence/p09-361-typed-auxiliary-product-preparation-components001.v1.json` and
`evidence/p09-361-typed-auxiliary-product-preparation-guard002.v1.json`.

Caller-typed preparation is not complete actual-source import, graph/compiler
or HWPX lowering, licensed save/render, Native or authenticated service/issuer
qualification. Incomplete source-v4 is not converted to complete state. Prior
entry465 and unrelated earlier tests are not current qualification. No36 source
or249 queue replay, Hancom/COM or Native execution occurred. Native011 authority
and current inputs remain separate. Official158/249, remaining91, P09 OPEN,
no P10 and ACTIVE remain.

## Streamed active inventory serialization

The active scanner now validates its original canonical JSON through a Count
writer instead of allocating and discarding that complete buffer. ActiveState
uses the same sorted control projection and Serialize representation, streamed
directly to SHA-256 rather than another complete JSON allocation. The borrowed
projection vector needed for original ordering remains. Only explicit canonical_json
requests use a Bytes writer, checking the original limit before each append.
State projection is no larger than the full inventory, so its same output cap
only rejects already over-limit inventory earlier. Public bytes, state hashes,
schema v4, error codes and graph/namespace/signature/activation checks remain.

Exact whole-module reverse bytes/hash show only the serialization paths and
writer changed. Removing three added tests reproduces the original ten-test
file. Current coverage is13 core tests without filters, two source-summary tests
with five filtered, and two actual CLI tests with23 filtered:17 exact passes.
Independent legacy serde JSON/state-projection SHA,256 controls, exact limits,
one-byte excess, tiny limits and unrelated XML-ordinal shifts are covered.
Historical36 inputs and the complete CLI25/security32/249 product queue are not
replayed or added to current coverage.

Receipt001 records37 first/final witnesses and cleanupTrue in105.985seconds.
Owned stages take18.453/1.781/78.719seconds (libtest0.07/0.02/0.13), Job CPU
16.891/1.469/23.984seconds and peaks1345.87/534.49/1354.66MiB. All owned trees
are empty with closed handles. System CPU maximum30.35percent and available
RAM minimum24.6841percent remain under original protection; one core, BelowNormal,
6.25percent CPU cap and RAM/commit/Job limits are unchanged. Overall elapsed time
includes compilation/linking/preparation and is not a controlled runtime or
memory-reduction benchmark. Evidence:
`evidence/p09-361-active-inventory-streamed-serialization-components001.v1.json`.

These17 tests qualify the changed serialization scope, not the current full
source/Native product. Prior32/44 records and entry465 are not rebased. Complete
state/flow, native security/external access and Native011 authority/current inputs
remain open. No Hancom/COM/Native execution occurred. Official158/249, remaining91,
P09 OPEN, no P10 and ACTIVE remain.

## Passive source security in the actual CLI

Current reference-source v4 adds active_security from SourceActiveSecurityAssessment.
The immutable source and existing catalog-security importer share the original
scanner construction, authoritative graph comparison, admission checks, errors
and legacy defaults. The summary needs no additional catalog/meaning graph and
accepts no caller inventory/graph. It returns source binding, original inventory
graph/state fingerprints and classifications, never raw paths, commands or URIs.
Reference-item/JSON limits can tighten but not enlarge the original limits.

Activation remains false. Native security stays not_assessed_by_active_content_inventory;
native-form security and external-data access remain unqualified. Original
scanner counts do not imply coverage of every native form or an unlocked/safe
document. Page/lock nulls, incomplete flow, null report and all four unresolved
stages remain. No complete auxiliary/security state is fabricated.

The original five security tests plus two new tests and25 actual source-CLI tests
pass32 without skips or filters. The36 historical inputs are passive original
file reads, not Native/product reexecution. Summary fingerprints/counts equal
the original scanner; minimal headers remain ineligible for the full catalog
path. Namespace spoofing, original budgets, CLI command privacy and no partial
success are covered. Exact reverse bytes/hash preserve the complete old security
importer and both old test files, apart from five added tests, two explicit
v3-to-v4 schema expectations and one corresponding test-name migration.

Receipt002 records79 first/final witnesses and cleanupTrue in70.062seconds.
Owned35.532/22.437seconds (libtest17.02/1.03), Job CPU33.109/21.125seconds and
peaks1344.89/1361.54MiB end with empty owned trees and closed handles. System
CPU maximum80.04percent occurs in exactly one of138 samples at or above75percent;
none reach90percent. That sample's parent CPU is0percent. The verified6.25percent
Job cap, one-core affinity and BelowNormal remain, but these observations do not
identify the cause process. Available RAM minimum25.8953percent and original
RAM/commit/Job protection remain; no protection abort occurred.

Receipt001 preserves a pre-execution CRLF inverse-audit rejection, zero test
steps, cleanupTrue and incomplete closing.002 corrects only that audit boundary,
without weakening exact source equality or reclassifying001. Prior44 tests and
the fixed probe are not rerun or combined as current coverage. No249 product,
Hancom/COM or Native run occurred. Complete state/flow, document protection,
signature, external-data access and Native011 authority/current inputs remain
open. Official158/249, remaining91, P09 OPEN, no P10 and ACTIVE remain. Evidence:
`evidence/p09-361-passive-source-security-components001.v1.json` and
`evidence/p09-361-passive-source-security-components002.v1.json`.

## Source section topology in the actual CLI

The v3 reference-source result introduced section_flows, retained by current v4, with
ImportedSectionFlowObservation from the original body import: native paragraph,
run and inline counts, framed run/inline topology hashes and the original part
fingerprint. Existing XML paragraph indexes are reused with no extra ZIP/XML
parse, subtree serialization or per-candidate reconstruction. Expanded names
make namespace aliases equivalent; the original transparent-bookmark wrapper
rule preserves topology while the separate part fingerprint binds exact source.
Opaque native paragraphs, tables and notes remain in source order. Fresh
structure/forms comparisons now include the derived section observations.

Page assignment and locked are null, complete_document_flow_qualified is false,
and the result remains incomplete with a null report and all four unresolved
stages. The native-form non-form-content digest is not substituted for reference
topology. No empty hashes, unlocked defaults or complete auxiliary state are
fabricated. Original section and aggregate output budgets apply to v3, including
an exact-size serialization pass and rejection at one byte below that size.

Importer22 plus actual source-CLI22 pass44 exact tests without skips or filters.
Removing seven added tests and reversing only the explicit v2-to-v3 schema
expectation reproduces both complete original test-file preimages. Tests cover
bookmark transparency, run boundaries, inline kinds, namespace aliases, opaque
paragraphs, multiple sections, nested table/note bodies, fresh comparison,
historical original preservation, unknown page/lock state and both budgets.
The rebuilt fixed probe also matches its original eight-candidate packet and
the full historical response in exact1836 stdout bytes/SHA. It does not replay44.

Receipt001 records38 first/final witnesses, cleanupTrue and47.422seconds total:
owned18.532/21.937seconds (libtest0.22/0.89), Job CPU17.078/20.750seconds and peaks
1344.72/1362.28MiB. System CPU maximum is20.45percent and available RAM minimum
27.0955percent. Probe002 records44 first/final witnesses, cleanupTrue and10.125
seconds total, build1.563/baseline0.828seconds, Job CPU1.125/0.219seconds, peaks
633.94/19.62MiB and system CPU maximum9.57percent. All owned trees end empty with
closed handles. One core, BelowNormal,6.25percent CPU cap and existing RAM/commit/
Job limits remain. Evidence:
`evidence/p09-361-source-section-topology-components001.v1.json` and
`evidence/p09-361-source-section-topology-fixed-probe002.v1.json`.

Complete auxiliary state/flow, resolved edge meanings, page/protection semantics
and Native qualification remain open. Prior v1/v2 records and entry465 are not
current v3/full-product/Native qualification. No249 queue, Hancom/COM or Native
run occurred. Official158/249, remaining91, P09 OPEN, no P10 and ACTIVE remain.

## Source section and paragraph order

ImportedBookmarkSectionLocation now binds the original section identity and XML
paragraph ordinal/count to each source bookmark and its SDK discovery candidate.
One bounded sorted vector is built per section, with binary search per bookmark;
there is no per-candidate ZIP/XML/body reconstruction or paragraph-tree allocation.
It follows the existing bookmark lowerer's native XML-element paragraph order,
not attached-table/detached-note graph traversal. Native paragraphs inside opaque
subtrees still count without becoming typed coverage. The new location is private,
redacted and serde-skipped; original observation JSON, target fingerprints and
candidate receipts/commands remain unchanged.

Removing only the six added tests reproduces the exact three original test-file
preimages. Importer18 and SDK8 pass with no filters/skips; the product preparation
target runs only the new test with four old tests filtered. These27 exact outcomes
cover table/note/note-table/opaque ordering, section reset, duplicate native IDs,
fresh paragraph insertion drift, preserved six-key JSON/privacy and all eight
prepared candidates. A separately rebuilt fixed read-only probe verifies its
original eight-candidate packet and the complete historical baseline response,
including exact1836 stdout bytes/SHA. The27 tests are not repeated for that check.

Receipt001 records37 first/final witnesses and cleanupTrue in72.422seconds.
Owned stages take19.360/46.094seconds (libtest0.25/0.03/0.03); Job CPU17.812/21.781
seconds, peak private1342.78/1357.41MiB, system CPU maximum25.78percent and available
RAM minimum26.0128percent. Fixed-probe002 records43 first/final witnesses and
cleanupTrue in11.688seconds: build2.969 and actual baseline1.047seconds, Job CPU
1.547/0.219seconds, peaks633.08/19.95MiB and system CPU maximum17.42percent.
All owned trees are empty with closed handles. One core, BelowNormal,6.25percent
CPU cap and original RAM/commit/Job protection remain.

Source XML locations do not supply complete auxiliary sections, typed LinkAnchor
qualification, page assignment, protection, resolved edges or Native authority.
Targets keep anchorNone and the overall source assessment remains incomplete with
all four unresolved stages and a null report. Prior source-CLI19 results are not
rebased onto changed Rust, nor is entry qualification465 current binary/input
qualification. No249 product, Hancom/COM or Native run occurred. Official158/249,
remaining91, P09 OPEN, no P10 and the ACTIVE goal remain. Evidence:
`evidence/p09-361-bookmark-source-section-location-components001.v1.json` and
`evidence/p09-361-bookmark-source-section-location-fixed-probe002.v1.json`.

## Actual source field inventory

The v2 reference-source CLI introduced form_import and field_range_import.
Current v4 retains these original receipts from one immutable package and borrows its body
for the original target import. The result binds source, body, form and range
graphs without accepting a caller-provided field inventory or reimporting the
ZIP/XML/structure for targets. Both native field-start and field-end counts in
all XML parts must match the represented original ranges. Hidden header,
nonspine or opaque markers fail coverage, including end-only markers. Original
pair/header/parameter/nesting/body admission and finite reference-item limits
remain. The output writer checks the aggregate limit before extending its
buffer, rather than allocating an entire over-limit JSON result first.

The unchanged whole prefix of thirteen original tests is preimage verified.
Six additional tests cover exact original receipts and graph binding, nesting
and repeated paragraph-local IDs, hidden begin/end/pairs, broken-pair CLI failure,
note/table fields and budgets, and the actual historical saved input through
the CLI. All nineteen pass without skipped or filtered tests. The historical
original and synthetic file inputs retain their bytes. The prior sixteen
crossref component outcomes and249 product cases were not replayed.

Receipt002 has39 first/final source witnesses, cleanupTrue and11.453seconds
total. The owned compile/test stage takes4.500seconds (libtest0.78), Job CPU
3.281seconds, peak private660.42MiB/2.0728percent and zero active children with
an empty owned tree and closed handle. System CPU maximum is11.17percent and
available RAM minimum30.0495percent. One core, BelowNormal,6.25percent CPU cap
and existing RAM/commit/Job protection remain. Receipt001 preserves a test-only
boxed-versus-typed error comparison compile failure, zero executed tests and
cleanupTrue;002 corrects the test to call the original typed API directly.

The current result stays incomplete with a null validation report and all four
unresolved stages. Source field ranges do not supply resolved validation edges,
complete auxiliary state/flow, cache evaluation, native target resolution or
execution authority. Historical v1 results and prior entry qualification465
are not current v2/full-product/Native qualification. Official158/249, remaining91,
P09 OPEN, no P10 and the ACTIVE goal remain. Evidence:
`evidence/p09-361-reference-source-field-inventory-components001.v1.json` and
`evidence/p09-361-reference-source-field-inventory-components002.v1.json`.

## Combined observations from one output snapshot

The fixed private worker probe now consumes this joint observation instead of
importing its output twice. Exact whole-file reverse bytes/hash verify that the
response, admission, paths and original pre/post source rereads are unchanged.
Its four existing consumer tests pass, and the freshly built read-only baseline
response equals historical011 in its full JSON and exact1836 stdout bytes/SHA.
The prior16 component outcomes and249 product cases were not replayed.
Receipt005 has40 first/final witnesses and cleanupTrue:102.750seconds total,
owned test45.922 (libtest3.64), build44.062 and baseline4.110seconds. Job CPU is
1.781/1.234/0.141seconds, peak private634.38/633.05/20.04MiB, system CPU maximum
26.54percent and available RAM minimum28.5645percent. All owned trees are empty
with closed handles. Historical baseline elapsed0.988seconds, so this establishes
duplicate-import removal and response parity, not measured elapsed-time speedup
or Native/full-reference qualification. Evidence:
`evidence/p09-361-combined-crossref-probe-integration005.v1.json`.

`SourceCrossReferencePreparation.observe_output_for_discovery` imports an output
package/form/field once and borrows its original body for bookmark target observations.
The immutable result joins the two original observations from that same snapshot,
not caller-supplied reports. Original separate APIs, SHA/coverage/pair/ambiguity
checks and native-false classifications remain. One bounded writer/count enforces
the combined output budget; two individually permitted reports can still be rejected.

The first001 batch keeps its8 passes and1 failed budget fixture, without running
the remaining7 target tests or completing its source closing. The fixture incorrectly
kept default input1MiB above its small output cap. Only its input cap was corrected.
Receipt002 executes that one corrected test (8 filtered) and the pending7 tests.
Exact whole-file reverse bytes/hash and unchanged dependency pins support retaining
the8 original results:16 combined outcomes, not a simultaneous16-test replay.
Its34 first/final witnesses are a separate source review, not retroactive original
guard closing or Native byte credit. Native/complete reference validation remain false.

Parity with both original reports, missing/duplicate targets despite matching commands,
SHA/pair failures and aggregate limits are covered. The historical saved HYPERLINK
also remains CROSSREF0/not-observed in the combined path without source mutation.
Original001 takes253.219seconds including250.078seconds compile/test, peak1904.73MiB;
002 takes8.922seconds, owned stages1.672/0.406seconds and peaks633.64/53.71MiB.
All owned trees end empty with closed Job handles and cleanupTrue. One core,
BelowNormal,6.25percent CPU cap and existing RAM/commit/Job limits stay unchanged.
No Hancom/COM/Native product ran. Official158/249 and P09 OPEN remain.

The separate source/document review004 passes39 first/final witnesses with no
component replay. Original review003 rejected source-order versus libtest's
name-sorted execution order; that failure and cleanupTrue/zero execution steps
remain preserved.004 checks exact names/statuses independently of order, retaining
duplicate/missing checks, the8+8 split, dependency preimages and original001's
failed/incomplete closing classification. This is not retroactive guard closing.

## Source local bookmark point retention

The source importer now retains the original bookmark projection's XML run ordinal
and non-bookmark child boundary in `ImportedBookmarkSourcePoint`. The source-bound
SDK candidate carries that point with its actual paragraph identity, including
nested table/note paragraphs. This is not the imported ControlRef/BookmarkAnchor
index or a flattened LinkPoint, LinkAnchor, page assignment or Native cursor.
No extra whole-source traversal is introduced. Existing observation JSON and
target fingerprints exclude this derived point; receipt/Debug privacy remains.

The bookmark import14 and SDK7 component tests pass21 with no failures, skips or
filters. Adjacent bookmarks, separate runs, nested paragraphs, preserved JSON and
candidate binding are covered. Receipt `p09-361-reference-bookmark-source-point-components002.v1.json`
records28 named first/final witnesses, not a complete Cargo/Native source closure.
The original shim rejection001 remains unchanged, including cleanupFalse. The
successful owned compile/test takes142.765seconds (libtest0.17/0.03seconds), uses
one core/BelowNormal/6.25percent CPU cap, peaks at1891.54MiB private memory and
ends with no active process and a closed Job handle. Existing protection stays.

No Hancom/COM/Native product or existing249 queue case ran. Complete reference
state/flow, native target mapping and product/Gate qualification remain incomplete.
Rust source changes require current build/input-generation qualification before
any separately authorized Native011 attempt; prior entry qualification465 is not
new Rust binary/corpus credit. Official158/249, P09 OPEN and P10 not started remain.

## Canonical runtime and linked raw evidence

The separate canonical route uses original fixed-eight/core steps but requires a trusted,
qualified session factory instead of generic COM creation. It retains original IO/cleanup
and raw CIM trace, writing canonical observations only to a fixed exclusive/fsynced sidecar
bound to the raw trace's exact bytes/hash/path. Completion/writer are one-shot and preserve
separate original/sidecar errors. Actual Native writing is unrun; no default/public Native
entry is enabled or replaced.

Record comparison preserves raw bytes, checks exact compatibility identity, and temporarily
projects only seven checked identity fields for the original strict producer verifier.
Whole-eight case checks run once per case. Paced reads and final freshness remain; tightened
parse limits restore on error. This does not qualify physical producer or native success.

Receipt068 passes four readonly runtime/sidecar contracts plus eight memory-only comparator
contracts. Actual eight-case planning stops at first prepare_slot with factory0/COM0/output0.
Forty-three first/final reads, tests6.813/0.390seconds, total25.406seconds, Jobs74.28/34.90MiB,
CPU sample peak17.12%, cleanup True. Prior suites are unreplayed. Actual factory/protection,
Native writes/admission/independent producer and full-eight product qualification remain.
Fixed eight NOT_RUN; official158/249 and P09 OPEN. New queue execution authority is pending,
not inferred from consumed Native010 authority or readonly results.

## Dual owner representation adapter

The new observer retains one query-only process handle before and after the unchanged
original P58 fresh CIM/window check. It preserves original CIM identity/trace and constructs
canonical birth from the kernel only. Its admission helper sends a borrowed-window proxy
through original HostMessage; no clock tolerance or original verifier change is introduced.
The decoder validates exact kernel UTC/filetime and rejects self-inspection as a Native
candidate. Neither record nor ACK is Native qualification/authority.

Receipt066 passes seven Python contracts including two PS models, not nine peer tests.
An actual x86 self-inspector is independently checked by its parent while still alive;
canonical birth matches exactly, raw CIM remains separate, fixed ACK leads to exit0 and
joined IO/closed handles. Twenty first/final reads, tests2.625seconds, total6.266seconds,
Job84.9MiB, CPU sample peak11.52%, cleanup True. Existing source/suites remain unchanged/unreplayed.

Default fixed-eight admission and producer v1 still need canonical evidence linkage without
overwriting raw CIM traces. Actual Hancom/COM and new Native work remain unrun; root062
failure/missing boundaries stay preserved. Native/producer qualification remains false,
fixed eight NOT_RUN, official158/249 and P09 OPEN.

## Root failure and birth representation

Receipt062's five component tests report passes, but the fixed suspended readonly child
remains Job-bound after the permitted request. Root proof fails before assignment/Native
work. Its readonly body exits65 for graceful cleanup; handles/empty Job close without kill,
policy change, alternate launcher/parent or replay. Missing062 final fresh/runtime hashes
stay missing. Receipt063 reviews this failure/current sources with thirteen first/final
reads; not retroactive completion or whole-run reuse of the five reported passes.

The separate x86 inspection of its own live process finds CIM birth six100ns units below
stable before/after .NET Process birth. Original P58 uses CIM, exposing a representation
risk at exact kernel-time comparisons, not an actual Hancom measurement. Preserve CIM
compatibility data and canonical held-handle birth separately; tolerance/checks are unchanged.
Observation1.219seconds, total3.781seconds, its Job62.95MiB, cleanup True. Root/Native and
producer qualification remain false, no acceptance added, fixed eight NOT_RUN.

## Native startup backend and inherited lifecycle

The new private backend restricts startup to pinned Hwp.exe -Automation, validates readonly
installed registration, preassigns original native limits at creation and checks the exact
suspended handle/PID/birth/session/image. Resume and same-process/window binding are single
attempts. Existing P58/native/host/readonly sources and prior test suites remain unchanged.
No COM fallback, generic argv, registry write or force termination is installed, and the
native controller/running-object provider remains unwired.

Receipt058 contains ten initial contracts with creation/resume/bind success in models only.
Actual registration, two installed-image byte reads, process inventory and empty native
Job parent-denial are verified. Snapshot059 preserves source before tightening the parent
predicate: immediate-Job limits cannot prove every ancestor safe. Only a jobless caller
is now admitted. Receipt060 runs two affected parent contracts and reuses eight unaffected
components after exact inverse/nine-test-body checks; not a current full-ten run or Native
execution. All actual Hancom/COM creation remains zero, with native_startup_qualified false.

The coordinator itself inherits flags0x2800, so its native route is denied pending an owned,
protected jobless execution boundary. No parent policy changed; at061 breakaway inspection
was unrun, and later062 failed without root qualification. Running-object binding, complete native admission and independent
producer/cleanup still require qualification. Official acceptance stays158/249, P09 OPEN.

## Initial thread resource containment

The fixed readonly child now supports Job assignment during CreateProcess via the Job-list
attribute. It remains suspended until exact handle/membership/limits and zero user CPU
are verified; after one resume the child checks its own immediate Job/effective limits
and exits zero. Live-child/tree handles are retained, not force-closed. No generic command,
Hwp/COM launcher, restart or native authority is added; existing source/tests stay unchanged.

Receipt056 passes five new contracts only: seven first/final source reads plus a separate
external runtime first/final pin, tests0.531seconds, total2.391seconds, outer Job37.83MiB,
child7.54MiB, CPU sample peak8.44%, cleanup True. This qualifies the closed readonly
mechanism, not original COM startup, running-object binding or Native admission/producer.

## Closed runtime host connection

The third fixed readonly role connects the actual one-percent host, fixed-eight controller,
protocol and parent-observation wrapper. A worker-side canonical negative-first-reply gate
blocks both the intended denial and an erroneous positive ACK before any slot/session is
created. Finish delivery after failure is not evidence of native cleanup.

Snapshot053 preserves prechange host/tests; exact inverse comparison keeps original limits,
lifecycle and old test bodies unchanged. Receipt054 passes five new contracts only, including
two actual x86 STA connections. Each has one failed parent record, zero owner admissions,
zero artifacts and eight NOT_RUN paths. Tests18.781seconds, total23.547seconds, outer Job
peak104.3MiB, CPU sample peak19.51%, cleanup True. Prior suites are not replayed. Actual
Native runtime wiring, startup limits, independent producer and admission remain unqualified.

## Fixed eight controller and producer observations

The new batch function calls the existing host-bound case in fixed eight-case order and
stops on first failure/uncertain cleanup. It preserves partial results, projects only closed
summary fields and refuses subset/retry/existing-record overwrite. No native entry is enabled.

The parent-observation wrapper and separate comparator align child traces, parent owner
observations and file pins, including fresh reopen birth, stage/probe identity, uncertain
SDK/indirect IO and cleanup. Whole comparison requires all eight cases and nonreused producer
lifetimes. Consistent records still do not prove physical native execution/provenance or
causal/product success, so native_provenance_qualified remains false.

Receipt051 passes six batch plus nine record contracts, with positive fixtures in memory
only. Actual native directories remain eight NOT_RUN; a fixed-denial concrete batch stops
before creating the first slot/session. Tests11.532/2.015seconds, total18.547seconds, owned Job
peaks74.81/28.63MiB, cleanup True. Prior host/resource suites remain unreplayed. Closed readonly
runtime wiring is qualified in054; native runtime wiring, physical producer, COM startup
limits and full native admission remain unqualified.

## Readonly pre COM prefix

The host now has a second fixed readonly role for installed binary/registration checks
and frozen window-type loading before COM. Four binary pins are paced at1MiB/s with
deny-write/delete read sharing. The original harness main and actual native window method
are not executed; no session, document, output directory or acceptance is created.

Exact prechange source/inverse comparison preserves CPU/memory/lifecycle and all prior
tests. Only the three new prefix049 contracts run: actual x86 STA, four installed pins,
readonly registration, type signature/import checks, Hwp inventory0/0 and eight absent
output directories. Tests7.437seconds, whole11.5seconds, test Job peak99.08MiB, cleanup True.
Type loading is local to this inspector process. External COM activation/inheritance,
physical producer, runtime activation of the eight-case dispatcher and actual native guard/admission remain
unqualified; existing acceptance and native-entry denial are unchanged.

## Owned readonly host process

The new host process uses a one-percent Job for the waiting bootstrap and two fixed readonly
targets, with limits/membership readback before its one-time signal. Live workers
or descendants prevent close; no force-kill/native route is implemented. The coordinator
is outside that worker Job and retains the original separate guard.

Immediate-parent CPU readback avoids multiplying an already bounded quota. Full parent
budget is used only with a verified hard cap no greater than the original one-core limit,
matching affinity/BelowNormal and no breakaway; unknown/weaker parents retain the original
child quota. A configured100% parent share is not PC100%, and later parent drift stops work.
The proof is limited to descendants created by this fixed host, not external COM activation.

Partition043 passes eight contracts. After exact prechange preservation/inverse comparison,
CPU045 reuses five unaffected contracts and runs three affected actual OS roles plus two
new CPU contracts. Actual empty Job, pre-signal EOF and fixed readonly target all close
cleanly. The selected five-test run takes14.937seconds with peak101.88MiB; it is not a
same-scope speed benchmark against the prior eight-test run. Full native startup/guard,
current-batch admission, independent producer and whole eight-case dispatcher remain pending.

## Ordered case host connection

The private host channel now connects ordered case checkpoints, owner resource admission
and finally finish. Messages have a fixed4KiB schema and sequence; failures latch without
blocking the single cleanup finish. The resource adapter uses the existing native backend
and rejects preparation-only guards. Neither ACK nor callback return grants native authority.

Channel036 covers ten contracts, including actual x86 readonly pipes, first-checkpoint
core/ports denial and one finish without a native directory/session. The actual product
case wrapper is separately tested using fixed in-memory denial, never external approval.
Wrapper038's test-only split-count failure and diagnostic039/split040 remain preserved.
Corrected041 changes only the test split line, reuses the unchanged prior ten contracts and
executes the wrapper contract alone. This is ten-plus-one component coverage, not eleven
current tests. Native host-budget integration, COM startup/inherited Jobs, actual native guard/current-batch
admission, independent producer qualification and the full eight-case dispatcher remain.

## Native resource admission backend

The private `crossref_native_host_limits.py` binds a resource Job to an exact owned target
handle using PID, lossless UTC birth, image, session, live window and fresh fixed executable
pin checks. It reads limits back after assignment and retains the original host sampler.
Pre-assignment private memory is included conservatively with subsequent Job peak memory;
it is not silently excluded by relying on Job accounting alone. Native close never force
kills an access-prompt session and rejects nonempty cleanup.

Ten source/model/OS contracts in native-host-limits031 include two actual empty-Job
readbacks and an actual non-Hancom rejection, not target assignment. After exact source
preservation and inverse comparison, native-preexisting-memory033 reuses nine unaffected
contracts and runs only the affected prior memory test plus two new tests. No product,
COM or access prompt is executed. Host one-percent partition installation, native case-port
integration, COM creation/inherited Jobs and whole native guard/admission qualification
remain pending. This backend does not change acceptance or the native entry denial.

## Concrete native case ports

The internal `crossref-native-case-ports.ps1` now connects the sixteen-step case core
to original owned sessions and document IO, SDK insertion and the fixed source probe.
It retains raw operation and producer observations without promoting them to product
acceptance. A denied host checkpoint latches failure before output/session creation.
Completion preserves cleanup and trace-write failures separately; its one-attempt latch
prevents a subsequent call from erasing those failures or retrying an uncertain write.

Source/denial receipt `p09-361-crossref-native-ports-contracts027.v1.json` covers eight
contracts. After preserving exact prechange source in snapshot028, completion029 proves
the small latch-only source delta and runs only two new contracts, reusing the prior eight
without replay. Neither run activates native sessions or creates native case outputs.
This does not constitute a current ten-test run, source-to-native producer qualification,
complete reference validation, or actual save/reopen acceptance. Qualified native host
protection, current batch admission, independent producer/cleanup evidence and the full
eight-case dispatcher remain pending; the native preparation entry stays denied.

## Case callback core and stage probe runner

The new case core fixes sixteen callback steps spanning slot/source/binding/opened probe,
SDK/saved probe, independent reopen, reopened probe, cleanup and source closing. Tests
exercise eight model cases and all sixteen failure positions; callback completion is not
native-operation evidence. Primary and cleanup failures remain separate, retries are not
performed, and the core never promotes callback return to native/cleanup acceptance.

The readonly stage runner holds the exact probe binary open after one hash, preventing
write/delete sharing and avoiding repeated binary hashes inside a future batch. Its code
comes from an exact SHA-bound template snapshot; original bounded capture/deadline/cleanup
suffix is reused. The fixed case/stage/SHA interface grants no native or producer authority.

Original5-pass/lease-failure022, source snapshots/diagnostic023 and pre-child verifier
failure024 are preserved. The digest-instance correction changes no prior case core/test
bodies.025 runs4 remaining contracts with5 filtered, giving5+4 component coverage, not9
in one current run. Actual missing-case1 readback exits2 with child cleanup and no artifact;
real held-binary write-open denial and closed-lease rejection pass.30fresh/final30,
whole27.824756seconds, tests8.550939seconds, Job peak71.59MiB, CPU sample maximum52.34%,
cleanup True. Receipt: `evidence/p09-361-crossref-case-flow-probe-corrected025.v1.json`.

The concrete StepExecutor is now connected internally as described above. Independent
producer/session-cleanup qualification and original native resource/current-admission
integration remain pending. No actual COM case or new authority was enabled.
Existing SDK/IO/product source and completed tests remain preserved; acceptance stays158/249.

## Save and fresh reopen source integration

The function-only `crossref-save-reopen.ps1` adds opened baseline save, post-insert saved
save, saved open in a later owned session and reopened save. Original P58 IO source/live
function definitions remain exact; its saved/reopened helpers are reused. Opened alone uses
a new fixed HWPX SaveAs. Case/stage paths and active-document/SHA observations are bounded.
Native SaveAs create-new atomicity and actual document-path behavior remain unqualified.

Fresh identity compares UTC birth, login session, EXE and window binding rather than PID
alone. Failed pre-handoff reopen releases its document, leaving session cleanup to the
concrete case ports above. Records preserve operation intent and unknown effects without retries.
Indirect helper entry is not a confirmed native call: invocation remains null until normal
helper return. The source/model correction is separate from actual producer attestation.

Six initial contracts passed,17fresh/final17,14.288704seconds, Job peak69.48MiB. Exact
prechange source019 and original6 results018 remain preserved. Only two added record
contracts ran after correction, with6 filtered,19fresh/final19,9.724859seconds and Job
peak65.68MiB, cleanup True. Receipt: `evidence/p09-361-crossref-save-reopen-records020.v1.json`.
This is6+2 component evidence, not one current eight-test run or an actual native open/save.
Existing SDK/artifact/ownership/product code and completed tests were not replayed.

Next are actual stage-probe invocation and case/batch/producer/cleanup coordination with
original native protection/current admission. The native entry still denies execution;
REF-053/P09 completion and the158/249 acceptance ledger remain unchanged.

## SDK adapter and artifact stage binding

The new function-only adapter `crossref-sdk-insertion.ps1` consumes the fixed eight-case
packet and the selected opened-stage source-probe observation. Installed declarations
distinguish HAction's two-argument BOOL GetDefault/Execute from individual Action methods.
The HActionCrossRef/HSet/Command path is checked against the actual installed signatures.
It rechecks owned active-document binding before execute and records execute intent and
unknown effects in a caller-owned record; it does not grant authority, retry, or prove
insertion/preservation. The existing preparation entry still denies native execution.

`crossref-owned-artifact.ps1` adds fixed case/stage path+SHA binding for original-session
opened input and saved/reopened artifacts, using the prior IUnknown/owner observation
helpers without changing the original-source bridge. Clean points require VT_I4 zero;
post-insert observations do not turn a modified value into acceptance. This source bridge
has not been exercised on real COM or a captured new native artifact.

Eight source/model/rejection contracts passed, including the32-selector matrix, bad probe
rejection, non-COM runtime rejection and exact source call ordering. Whole10.499380seconds,
14fresh/final14, test2.219670seconds, Job peak71.71MiB, system CPU sample maximum22.49%,
cleanup True. Receipts: `evidence/p09-361-crossref-action-call-declarations014.v1.json`,
`evidence/p09-361-crossref-action-hub-declarations015.v1.json`, and
`evidence/p09-361-crossref-sdk-artifact-contracts016.v1.json`.

Next are actual save/fresh-reopen case/batch wiring, stage-probe/producer binding and the
original native resource protection/current admission before separate execution authority.
The existing13 binding contracts, Rust product library and accepted queue remain unchanged.

## Fixed worker source probe and preparation composition

The new internal example `p09_crossref_discovery_probe` calls both source observation APIs
and rebinds the exact eight-candidate packet to current preparation receipts. It accepts
baseline or fixed case/stage/SHA selectors, never arbitrary paths or commands. Initial and
final source/manifest/packet hashes are fresh; Windows source handles deny write/delete
sharing while read. Reads use bounded buffers and2MiB/s pacing. Redacted output is capped
at16KiB and cannot attest native execution, producer lineage or causal preservation.

Four new contracts passed in8.377116seconds,29fresh/final29. The actual binary baseline
reported all eight exact-name targets and CROSSREF0 in0.987596seconds, Job peak20.30MiB;
the separate build/audit took17.990212seconds,31fresh/final31. The existing product library
and its prior seven tests were unchanged; completed tests were not replayed. Receipts:
`evidence/p09-361-crossref-worker-probe-tests010.v1.json` and
`evidence/p09-361-crossref-worker-probe-baseline011.v1.json`.

The actual x86 preparation composition imports the source-binding functions, verifies the
original owner function, and invokes the existing whole-eight installation prefix once and
the source probe once. New PS4 contracts, actual early native denial and actual two-child
completion/cleanup passed.45fresh/final45, whole51.698768seconds, actual preparation
23.891316seconds, Job peak141.73MiB, system CPU sample maximum75.52%, cleanup True.
Receipt: `evidence/p09-361-crossref-worker-composition012.v1.json`.

This is preparation integration, not an implemented native dispatcher. SDK action/save/
fresh-reopen execution, stage-specific active-document/producer binding and original native
resource protection remain before separate authority and actual qualification. The probe
can describe a fixed saved path without proving who produced it. Native readiness and
REF-053/P09 completion remain false; frozen P58 and the158/249 queue are unchanged.

## Source target observations across snapshots

`SourceCrossReferencePreparation::observe_bookmark_targets_in_output` now imports one actual
output package/structure and target-name index for an entire prepared batch. It derives
expected bookmark names from the preparation's immutable source and each opaque original
target digest. It accepts no caller-supplied target-name/state mapping. Exact decoded names
produce unique/missing/ambiguous observations; no first match, trimming, normalization or
cross-snapshot logical-ID equality is assumed. Source/graph/target and candidate-receipt
digests bind the result. Serialization uses a bounded writer; an over-limit complete JSON
buffer is not allocated. Native, causal preservation and complete-validation flags remain false.

Seven new tests passed: shifted source-local IDs across snapshots, missing/duplicate names,
exact Unicode/entity handling, SHA/work/text/output limits, nonspine coverage rejection,
the actual generated discovery input, and a historical saved HYPERLINK without a bookmark
target. Test runtime0.18seconds, build/test51.792906seconds, whole56.012538seconds,
26fresh/final26, Job peak1,353.55MiB, system CPU sample maximum57.52%, cleanup True.
Receipt: `evidence/p09-361-crossref-product-target-readback-tests007.v1.json`.
The prior SDK/preparation bodies match after removing only the new read-only opaque getter
and module export. Prior passed preparation/queue tests were not repeated.

The separate owned-active-source observation bridge is implemented but not exercised on
real COM. Installed getter inspection and visual review of the official automation manual
pages46/47/51 confirm declaration scope; `Modified` is LONG rather than BOOL. Its initial
expectation and AST-extent failures remain preserved. Source/model evidence is13 components
through7+5 then10 reused+3 selective tests, not all13 in one current run. Owned-process,
IUnknown, active-document and fixed source checks return observations, not native authority
or proof that the bookmark survived opening. No execution route or document write was added.

Next are actual worker/current-preflight integration and, with separate authority, real
save/reopen/target and preservation observations. REF-053 and P09/A12/A13 remain incomplete.

## Fixed private discovery input and batch preparation

The fixed private preparer now exercises `prepare_source_crossref_discovery` on a generated
bookmark-bearing input, deriving the logical target from the actual imported source. It
prepares page/name/content/relative-position displays with both hyperlink choices in one
eight-candidate packet. The original saved HWPX remains unchanged; the fixture adds one
paragraph, checks all other expanded parts, and is not an installed-Hangul-qualified input
or a public bookmark-insertion implementation.

`crates/product-cli/examples/p09_crossref_discovery_prepare.rs` accepts no arguments and
reads only the fixed manifest/input SHA pins. It writes the private packet once with
exclusive creation and fsync, verifies the source at the batch boundary, and records the
input CROSSREF0/not_observed observation. It does not execute commands or add a CLI/MCP
action route. The42,762byte packet is explicitly not native-ready and remains outside P58.

The three Rust preparer tests passed. The Python fixture tool's declared five-test suite
exited0; its receipt retains stderr size/hash but the capture helper did not parse the
individual unittest summary, so this is not an audited runtime count. Actual fixture
generation took2.007213seconds. Build and packet creation completed in16.243408seconds,
including0.356991seconds for the packet program; peak owned-job private memory632.55MiB,
system CPU sample maximum32.10%, cleanup True. Completed prior source/product tests were
not repeated. Receipts: `evidence/p09-361-crossref-discovery-fixture-tests001.v1.json`,
`evidence/p09-361-crossref-discovery-input001.v1.json`,
`evidence/p09-361-crossref-discovery-preparer-tests001.v1.json`, and
`evidence/p09-361-crossref-discovery-prepared-batch002.v1.json`.

The fixed whole-eight no-COM preflight also passed in an actual x86/STA process. It checks
packet order and source/command/target bindings, then the installed2020 binary/typelib and
security module registration with no writes. Ten pins receive a fresh final check once per
batch; the preserved owned-session library is hashed but not imported or run. Eight new
pure/source contracts pass; before/after Hwp counts are0. Overall19.867716seconds,
owned-job peak88.93MiB, system CPU sample maximum17.39%, cleanup True. Receipt:
`evidence/p09-361-crossref-discovery-preflight003.v1.json`. There is no execution switch,
new native attempt, or raw command route in this preflight.

Next are qualified owned-worker runtime and active-document/target binding, fresh preflight
at any future execution boundary, separate native authority, and actual save/reopen/preservation observations. This does not
change source assessment `incomplete`, REF-053 completion, or P09/A12/A13 OPEN.

## Implemented library surface

- Added `crates/product-cli/src/reference_validation_product.rs` and exported its library module.
- The operation accepts only the typed `ref.reference_validate` request, delegates strict bounded
  request parsing and plan/build to `ReferenceAuxiliaryBuilder`, recomputes the report digest, and
  checks the domain receipt plus unchanged source/target state and document-flow pins.
- It performs no filesystem/package read or write, native action, reference repair, field update, or
  external data-source access. This typed operation remains a library API. The separate source
  assessment CLI described below does not execute it or claim complete reference validation.
- Added four integration tests for a missing-target report, rejection of mutation capabilities,
  malformed capability-envelope classification, and duplicate-key rejection through the domain
  parser. The product response carries the fixed qualification
  `caller_supplied_typed_state_only_source_completeness_unverified` so callers cannot mistake the
  API result for a fully imported document report.

## Verification boundary

- After adding the qualification field, `CARGO_BUILD_JOBS=1 cargo test -p hwpx-agent-cli --test
  reference_validation_product --locked --offline`: `4 passed, 0 failed`.
- `rustfmt --edition 2024 --check` on the new API and test files: `PASS`.
- This incremental one-target build began at CPU `38%`, available RAM `6,013 MiB`; after completion
  the sample was CPU `80%`, available RAM `5,869 MiB` of `31,861 MiB`. No full suite was started.
- Actual HWPX write/readback, Hangul open/save, render, external source handling, P09 queue
  acceptance, and Gate closure remain `NOT_RUN`/unverified. P09 remains 104/249, next111, Gate
  `OPEN`; P10 implementation remains unstarted.

## Next boundary

The next implementation needs a qualified product-side reader that derives the complete reference
state and flow pins from the actual HWPX package. The current product API accepts already-typed state
and does not provide that reader, CLI dispatch, or package output. Do not promote REF-053 beyond the
tested library contract until that path is implemented and verified. Do not infer target or Gate
acceptance from these unit tests.

## Source-reader audit (2026-10-10)

- `hwpx-package`/`product-cli` search found no `ReferenceAuxiliary` HWPX reader or reference-validation
  CLI dispatch.
- The existing `ImportedDocumentStructure` exposes bookmark observations. The existing field-semantic
  import recognizes only `HYPERLINK` and `FORMULA` in its closed scope; it does not produce the complete
  cross-reference edge inventory required by `ref.reference_validate`.
- Therefore the tested library operation still depends on caller-supplied typed state. Deriving a
  full-document report from these partial observations would overstate coverage; no such projection
  was added. HWPX source binding remains `NOT_RUN`.

## Source backed bookmark targets added 2026 10 17

`hwpx-package::document_import::reference_targets::ImportedReferenceTargets` now derives
domain `ValidationTarget` values from the immutable `ImportedDocumentStructure`. It does not
accept a deserialized target list. Each target keeps the original bookmark reference ID and a
digest of the complete source observation; its receipt binds the source package, provenance,
structure graph and typed target inventory.

The source-name index preserves exact decoded Unicode and distinguishes missing from ambiguous
names. It does not normalize names, pick the first duplicate, or claim native navigation. Source
anchors are not converted into invented `LinkAnchor` coordinates: the optional domain anchor stays
absent. An active target means the exact marker exists, not that the document is authorized or
editable. Every imported XML part is checked for uncovered paragraph-namespace bookmarks; a marker
outside the supported structure fails with `Coverage`. Native field presence remains explicit, and
`complete_reference_state_qualified` remains false.

Canonical target hashing streams through a bounded digest writer rather than allocating a second
whole-inventory JSON buffer. Caller item, name and serialization limits remain enforced. Fresh
source verification delegates to the unchanged full package and structure reconstruction, not a
hash-only replay. No package or original evidence is rewritten.

### Focused verification and compiler memory

- The first compiler Job stopped at its existing 7 percent private-memory budget, with a recorded
  peak of 2,254.63 MiB and confirmed empty owned process tree. This was not the system RAM 95 percent
  boundary. The initial tool-launch refusal also correctly rejected Rustup symlinks before creating
  a Job; verified installed toolchain executables were used without weakening that check.
- The compiler-only profile disables incremental compilation and debug information and uses 16
  codegen units. CPU affinity, BelowNormal priority, one Cargo job, one test thread, assertions,
  overflow checks, system RAM/commit checks and the original Job memory limits remain enabled.
  The new profile is not the current stored-product runtime build profile.
- Metadata/type checking passed in 121.114962 seconds overall, with a 1,508.5 MiB Job peak and
  confirmed cleanup. This alone is not a test run.
- The integration target built and ran under that profile: eight tests passed and one fixture failed.
  The entire run took 113.414311 seconds, with a 1,855.68 MiB Job peak and confirmed cleanup. The
  failing fixture had compressed the HWPX `mimetype` using ZIP defaults, so original package graph
  validation rejected it before the new coverage check.
- Only that synthetic ZIP creation statement was corrected to `Stored`. The failed test then passed
  alone in 4.317823 seconds overall, with eight tests filtered out and a 534.23 MiB Job peak. Its
  first handoff audit incorrectly represented newline escapes and therefore kept that receipt
  failed despite the test passing. The failure was not overwritten or reclassified.
- A separate read-only audit verified the exact old test preimage, one corrected fixture statement
  plus line-ending normalization, and unchanged declared product/dependency pins. It combined the
  original eight passing tests with the corrected single passing test: 14 fresh/final 14 inputs,
  cleanup true, zero test replays for the audit. This is composite coverage of nine tests, not a
  claim that the post-fix binary ran all nine together.

Records: `evidence/p09-361-reference-target-compile-pressure001.v1.json`,
`evidence/p09-361-reference-target-low-memory-check002.v1.json`,
`evidence/p09-361-reference-target-low-memory-tests003.v1.json`,
`evidence/p09-361-reference-target-fixture-correction004.v1.json`, and
`evidence/p09-361-reference-target-composite-review005.v1.json`.

### Remaining product boundary

The complete `ReferenceAuxiliaryDocumentState`, document-flow pins, other target families, reference
edge meanings and completed-validator CLI result still need source-derived implementation and qualification.
The caller-supplied-state product API has not been promoted to a complete source validator. Native
name lookup, updates, target/render/automation qualification and P09 closure remain unverified.

The Rust source changed for this stage. Earlier source-generation binaries are preserved as history,
not presented as current-source runtime evidence. Queue acceptance remains 158/249, next165, with
91 trials pending; no Native010 replay or Native011/Hangul/COM run occurred. P09/A12/A13 stay OPEN,
P10 remains unstarted, and the full P09–P20 goal remains active.

## Actual source assessment CLI added 2026 10 17

The product now has an actual source entry, not just a caller-supplied typed-state interface:

```text
hwpx-agent-cli reference-source DOCUMENT_ID SHA256 ABSOLUTE_LOCAL_FILE
```

`ReferenceValidationProductOperation::assess_package_source` imports the exact expected package
bytes, reconstructs the original source-backed structure, and derives typed bookmark targets.
The response binds the source/package/provenance, structure and target inventory. Raw names, body
text, native parameter values, paths and external URIs are not response fields. The entry performs
no field update, repair, native application call or source write.

The original schema was `hwpx-agent.product.reference-source-assessment/v1`; the current
v2 adds the source-derived form and field-range receipts described above. The status is
`incomplete`; `validation_report` is explicitly null, not a zero-reference success. Other target
families, reference-edge meanings, complete auxiliary state and document-flow qualification remain
unresolved. No synthetic empty state or inferred native `CROSSREF` parameter mapping is passed to
the existing typed validator. The pinned P09-06 policy still classifies those native parameter
meanings as unverified.

- Exit 3 returns an available but incomplete source assessment.
- Exit 2 rejects invalid arguments, file/profile bounds, source drift or import failure.
- The new command does not return exit 0 as a successful complete reference validation.

The file entry is bounded to 32 MiB and requires an absolute local disk path. It rejects lexical
nonlocal/device/parent paths, non-files and symlinks; ancestors are checked from the root before
descendant metadata so existing Windows junctions/reparse points are rejected as well. This is a
direct-path preflight, not a race-proof filesystem sandbox or service ACL/head/route authorization.
Source identities describe the imported snapshot, not an attestation of the latest service revision.

### Product and real file verification

The exact new source and test target passed metadata checking in 101.590181 seconds overall, with
a 1,518.61 MiB Job peak. The initial nine integration tests passed in one run: build/run overall
82.430596 seconds, libtest runtime 0.55 seconds, Job peak 1,866.35 MiB, 15 fresh/final 15 declared
inputs, cleanup confirmed. They include real CLI subprocesses, incomplete exit 3, no source mutation,
closed errors, wrong digest/document binding, finite limits, unknown `CROSSREF` parameters, duplicate
names and legacy/unknown command error routing. Existing CPU/RAM/Job guards, one CPU, one Cargo job,
one test thread, assertions and overflow checks stayed enabled.

After ancestor preflight was added, only affected CLI cases were run: four passed and one failed
while creating its synthetic junction, before the product check. A single-test diagnostic confirmed
the fixture setup failure, not an assertion failure. Switching only that fixture's creation to the
Windows PowerShell `New-Item -ItemType Junction` command made the single test pass; ten tests were
filtered out. The temporary junction was removed non-recursively and its underlying synthetic
source bytes remained unchanged. No administrator approval or system setting change was used.

The component reuse audit cryptographically restored the previous source by reversing only the
private file-ancestor preflight, verified the original nine test bodies as an unchanged prefix,
and reversed only the failed junction creation fixture against its earlier exact pin. All other
declared dependency pins matched. Current coverage is six unchanged core/legacy tests reused from
the original run, four CLI guard passes, and the corrected junction pass: eleven component tests,
not a claim that all eleven ran together after the fix. The review read 21 fresh/final 21 inputs
and ran no tests again.

The final executable also read the unchanged historical Hangul-saved HWPX input whose SHA-256 is
`feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480`. It observed 11 parts, 8 XML
parts, 736 elements and one native field, with zero fabricated bookmark targets. The returned report
remained `incomplete` with null validation report and exit 3. The actual owned command stage took
about 0.273 seconds; the whole source/binary pre/post audit took 13.640359 seconds with a 17.34 MiB
Job peak, 17 fresh/final 17 inputs and confirmed cleanup. This reuses a historical saved input; it
is not a new Hangul/COM/save-reopen/render or native field-semantic qualification.

Records are in `evidence/p09-361-reference-source-product-check001.v1.json`,
`reference-source-product-tests002`, `reference-source-captured-cli003`,
`reference-source-parent-guard-tests004`, `reference-source-junction-diagnostic005`,
`reference-source-junction-correction006`, `reference-source-captured-cli007`, and
`reference-source-component-review008`, each with the same `p09-361-` prefix and `.v1.json` suffix.
The earlier failed records are preserved unchanged.

Complete source reference validation, native parameter qualification, full state/flow construction,
target/render/automation/differential evidence and the final P09 Gate remain incomplete. The new
source-assessment CLI is not promoted to REF-053 complete validation or P09 acceptance. Official
queue acceptance stays 158/249 with 91 pending, P09/A12/A13 OPEN, P10 unstarted and the goal active.

## Source note targets added 2026 10 17

The actual target importer now admits source-backed footnotes and endnotes as well as point
bookmarks. Its receipt profile is `hwpx-agent.document-import-reference-targets/bookmarks-notes-v2`
and reports separate `bookmark_targets` and `note_targets` counts. Notes use the immutable structure
importer's source-derived `note_id`, not native `instId` or displayed numbering as a global identity.
Each marker and body anchor resolves against the original source. Notes do not enter the exact
bookmark-name index, and their optional typed flow anchor remains absent.

The coverage scan compares all imported XML parts against admitted bookmark, footnote and endnote
observations. An otherwise ignored note outside the supported structure is a closed Coverage error,
not a zero-note success. Per-kind limits and bounded streaming target digests remain enforced.
The digest binds the source observation, including its package and body anchor; source body changes
cannot reuse the earlier target inventory. The CLI exposes no note text or native parameter values.

All 13 target-import tests and 12 product tests passed in one serial build/run sequence, including
the actual CLI with mixed bookmark/note targets. Nine historical packages cover three generated,
three saved and three reopened note inputs; their original `failed_semantic_non_green` and zero
green status stay unchanged. Verification took 56.769728 seconds overall, with a 1,344.39 MiB peak
owned Job, 32 fresh/final 32 inputs, sampled system CPU at most 50.59 percent and confirmed cleanup.
The target and product stages took 26.157441 and 25.387879 seconds respectively. One CPU, BelowNormal,
single Cargo/test execution and the existing CPU/RAM/commit/Job protections remained active.

A later diagnostic-only change corrects the Debug scope label to include notes and adds one
assertion. Exact inverse hashing restored the original tested source and test file; other declared
inputs matched. Only that affected test was rerun: one pass, twelve filtered, 24.525717 seconds
overall and 1,331.73 MiB Job peak. The earlier full-suite and product executable results retain their
original source generation; they are not relabelled as executions of the later binary.

A separate bounded read-only census inspected 248 HWPX files in the declared P09-prefixed fixture
and private-evidence directories. It parsed 125 unique byte identities and reused their inspection
for the remaining duplicates. There were no rejected/excluded archives or CROSSREF candidates in
this declared set, with 250 fresh/final 250 inputs and 43.328682 seconds overall. This is neither an
all-repository/user-document search nor native parameter qualification. Unverified CROSSREF keys,
target mappings and cached display meanings remain unimplemented, not inferred from field names.

Records: `evidence/p09-361-reference-note-target-product-tests001.v1.json`,
`evidence/p09-361-reference-note-target-debug-correction002.v1.json` and
`evidence/p09-361-native-crossref-corpus-census001.v1.json`.
Other target families, complete auxiliary state/flow, reference-edge semantics and final validation
remain incomplete. The response stays `incomplete`, null validation report and exit 3. No new
Hangul/COM/Native010 replay/Native011 or access dialog occurred. Official acceptance remains 158/249;
P09/A12/A13 stay OPEN and the goal stays active without starting P10.

## Actual table targets added 2026 10 17

The current receipt profile is `hwpx-agent.document-import-reference-targets/bookmarks-notes-tables-v3`.
The existing source-backed structure importer has already validated native table grid, cell spans,
placement and bodies. The reference target importer now walks its borrowed section and note flows,
including nested cell bodies, and preserves each actual table node ID and source anchor as a Table
target. No native numeric ID, displayed numbering, bookmark name or fabricated flow anchor is used.
The receipt adds `table_targets` alongside the bookmark and note counts.

The walk visits each flow once and uses the original table subtree fingerprint with its actual ID,
rows and columns for the target-state digest. It does not serialize every nested subtree again or
clone the document graph. The source importer's existing fingerprint budget remains authoritative.
All imported XML parts are checked for uncovered native tables, in addition to bookmarks and notes.
Duplicate anchors, missed tables and per-kind exhaustion reject the whole target import. Unmapped
equation/drawing/object semantics are not promoted from local-name observations to supported targets.

Seventeen target-import tests and thirteen product tests passed with 50 fresh/final 50 inputs,
47.188584 seconds overall and a 1,346.10 MiB owned Job peak. Target and product stages took 19.222944
and 21.522609 seconds, with test runtimes 1.11 and 0.76 seconds respectively. The suite covers nested
tables and note tables, source node identities despite repeated native IDs, body-change digests,
per-kind limits, off-structure rejection, foreign namespaces and the real CLI. Sixteen historical
generated/saved table packages and nine note packages were read; their original native results are
preserved, not counted as new native acceptance. Existing resource protections stayed enabled; sampled
system CPU peaked at 32.20 percent and all owned process trees were cleaned up.

The first preflight compared a whole historical manifest row, including text/unchanged metadata,
against a three-field file pin. It stopped before compilation/test execution after formatting. The
failed receipt remains unchanged. The correction selects exactly path, byte size and SHA-256 while
still verifying the locked manifest digest; it does not drop any archive byte-integrity check.

The resulting current executable also read the historical Hangul-saved table package with SHA-256
`91735b23a3b3ef528df1f6c411cb1cc1e7aaa895cb2f8de75be1f9eed331dadc` and size 14,384 bytes. The actual
CLI returned one table target and one observed native field, with no invented reference meaning.
Its result stayed incomplete, null validation report and exit 3. The owned command took 0.572579
seconds; the whole source/binary pre/post audit took 14.513174 seconds, with a 17.00 MiB Job peak,
20 fresh/final 20 inputs and confirmed cleanup. This is a real file/product read, not a new
Hangul/save-reopen, field recalculation, render or differential run.

Records: `evidence/p09-361-reference-table-target-product-tests001.v1.json` (pre-test failure),
`evidence/p09-361-reference-table-target-product-tests002.v1.json` and
`evidence/p09-361-reference-table-captured-cli003.v1.json`.
Complete source reference state/flow, other target families, reference-edge/native parameter
semantics and the final validator/Gate remain incomplete. Queue acceptance remains 158/249 with
91 pending; no Native010 replay, Native011, Hangul, COM or access dialog occurred. P09/A12/A13 stay
OPEN, P10 is unstarted and the full goal remains active.

## SDK cross reference command candidate added 2026 10 17

The pinned SDK manuals provide a concrete discovery route that the generic OWPML field model does
not: `InsertCrossReference` and `ModifyCrossReference` use `ActionCrossRef.Command`. ActionTable
pages 16 and 23, and ParameterSetTable pages 1, 175 and 176, were visually checked after a bounded
keyword search of 52 and 179 pages. These are the fixed 2025 manuals; their documented command
semantics are not automatically qualified for the installed 2020 application or HWPX serialization.

The actual installed registered type library was read without COM server activation or registration.
`HActionCrossRef.Command` is member 28703: a VT_BSTR getter and a setter with one input VT_BSTR
argument. The original inspector, exact target EXE/DLL identity, REGKIND_NONE and process-set checks
remain unchanged. A new wrapper verifies the original source SHA, makes only three fixed declaration
and schema transformations, and filters output to the three related types. The static inspection
took 4.569544 seconds with 6 fresh/final 6 inputs and a 93.12 MiB peak owned Job.

`cross_reference_sdk.rs` now builds inert same-document candidates from typed object/note/bookmark
targets and display choices. It does not accept raw commands, serialize public request JSON, expose
a CLI/MCP route or invoke the SDK. Current syntax covers table, picture, equation, footnote, endnote,
outline and bookmark; page/number/name/content/relative selection is checked for each kind. Note
source-order indices have a separate type from native object identity. They do not bind the current
source ordering or prove a zero/one-based origin. External-document support and unknown escaping
remain unqualified rather than silently inferred from the hyperlink implementation.

Six tests cover three same-document manual examples, all 52 valid kind/display/hyperlink combinations,
invalid combinations, positive identities, delimiter/control/path rejection, exact Unicode
preservation, privacy and the 4096-byte output boundary. These are six tests with a 52-combination
matrix, not 52 native product trials. They passed in 68.048637 seconds overall; the build/test stage
took 59.680991 seconds, with a 1,343.52 MiB Job peak, 18 fresh/final 18 inputs and confirmed cleanup.
The actual native application, save/reopen and HWPX field lowering remain NOT_RUN for this candidate.

The source-flow inspection also confirmed that imported control_inline_position includes synthesized
BookmarkAnchor entries, while the closed bookmark lowerer counts non-bookmark native run children.
Nested table/note paragraphs lack a qualified general mapping to its top-level LinkPoint coordinates.
Those indices are not substituted for one another, and no fake complete flow/state is constructed.
Existing source-assessment behavior stays incomplete; REF-053 completion is not claimed.

Records: `evidence/p09-361-reference-installed-declarations001.v1.json`,
`evidence/p09-361-reference-official-manual-search001.v1.json`,
`evidence/p09-361-reference-official-manual-pages002.v1.json` and
`evidence/p09-361-crossref-sdk-candidate-tests001.v1.json`. Five rendered source pages remain in
`target/p09-149-conservative/reference-manual-review-20261017-01` and are hash-bound in those records.
Earlier binaries retain their own source-generation evidence; the new module is not a requalification
of the queue or old product executable. Native010 is not replayed and Native011 is not executed.
Official acceptance remains 158/249 with 91 pending, P09/A12/A13 OPEN and P10 unstarted. The full goal
remains active. Next qualification must bind actual targets and native command readback before
promoting the SDK candidate to a real operation or interpreting HWPX field parameters.

## Actual source bound SDK preparation added 2026 10 17

The discovery candidate now has a real source-binding entry. `SourceCrossReferenceContext` imports
the immutable actual structure/targets and builds logical-ID and exact-name indexes once. It selects
an actual observed bookmark by source-local logical target ID, not a caller-supplied native name,
instId, note index, graph or command. Duplicate source names reject either bookmark ID. Missing,
cross-document and changed-package IDs cannot rebind the source. Unicode names remain exact, with
no implicit normalization. Unknown delimiter encoding still rejects the candidate.

The source/package/provenance/graph/target inventory, selected-target state and command digest are
bound in a private-constructor receipt. Neither receipt JSON nor Debug exposes a raw name, command
or document content. The receipt still requires native target qualification: actual application
name resolution/normalization, active-document identity, current service head and execution authority
are not established by a source snapshot. Nested table/note bookmarks do not receive invented flat
flow coordinates. HWPX table ids are not assumed to be HML InstIds; note instId/number is not assumed
to be the SDK source-order INDEX. Those kind mappings remain explicitly unqualified.

The product API `prepare_source_crossref_discovery` imports one package/structure/context for a whole
batch, retains its immutable source and prepares all selections or none. Empty, duplicate, missing
and partially invalid selections reject. Aggregate receipt-plus-private-command byte accounting is
checked before retaining each candidate; an allowed one-candidate budget is tested to reject two
candidates. Fresh verification reconstructs the original whole source/graph once per batch boundary,
not once per display variant. JSON status is `native_execution_not_run` and includes only binding
receipts. No raw command CLI/MCP route, SDK invocation, document write/update or execution permit
has been introduced. The existing source-assessment schema and incomplete result are unchanged.

Six source-context and four product-preparation tests passed: actual imported names and identities,
duplicates, forged/cross-document/version targets, nested contexts, exact Unicode, unsupported native
kind/encoding/display rejection, eight variants for one bookmark, fresh-source drift, aggregate limits,
privacy and original byte preservation. The inputs are generated actual HWPX packages, not new
native-Hancom samples. The run used 22 fresh/final 22 inputs and took 108.913698 seconds overall;
source and product stages took 41.684282 and 62.384451 seconds, with 0.03-second test runtimes each.
Peak owned Job memory was 1,349.89 MiB; sampled system CPU peaked at 41.99 percent. Original one-CPU,
BelowNormal, single Cargo/test thread and CPU/RAM/commit/Job protections stayed enabled, and all owned
process trees were cleaned up. Record: `evidence/p09-361-source-bound-crossref-tests001.v1.json`.

Earlier SDK syntax, target-import and CLI suites were not replayed. Their original source-generation
receipts are preserved; they are not promoted to executions of the current binary. Next qualification
still requires native target/command readback and source mappings for other target kinds, followed by
actual action/save-reopen/HWPX serialization and full state/flow/Gate evidence. Official acceptance
remains 158/249 with 91 pending; Native010 is not replayed, Native011 is not executed, no new Hangul
or access dialog is started, P09/A12/A13 remain OPEN, P10 is unstarted and the full goal remains active.

## Source cross reference command observations added 2026 10 17

`CrossReferenceCommandObservations` observes prepared command strings in actual output HWPX fields.
It borrows the original immutable form/field-range import, resolves its exact parameter anchors and
decodes each admitted direct plain hp:stringParam leaf once. A single expected-command index serves
all candidates; the XML is not rescanned per candidate. Parameter names are not interpreted as
Command keys. XML text references are decoded without trimming, case folding or Unicode normalization.
Non-string, structured and comment payloads are counted as opaque. NotObserved is scoped to those
admitted leaves, not an assertion about opaque payload content.

Multiple matching leaves or fields reject a unique interpretation; two candidate strings inside one
field are also marked shared/ambiguous. No first match is selected. Every imported XML part is checked
for uncovered native CROSSREF starts, including non-spine headers. Original source/form/range admission,
expected output SHA, distinct candidate commands and finite aggregate text/work/output limits remain
required. No HWPX field parameter key, cache meaning, target resolution or field update is inferred.

`SourceCrossReferencePreparation::observe_crossref_output` imports the output package/forms/fields
once for the whole candidate set. The report status is source_observation_only. Parameter-key semantics,
native execution attestation, causal insertion or preservation and complete reference validation all
remain false. A preexisting matching field is explicitly tested to retain those false claims. The
report therefore cannot attest that a native action occurred, that the output descends from the input,
that a target survived, or that a display cache is valid. No CLI/MCP/raw-action route or source write
has been added.

Eight observation and three product tests passed on generated HWPX packages. They cover arbitrary key
names, entities, missing/foreign-kind values, duplicate leaves/fields, shared fields, opaque comments/
non-string values, absent parameters, exact whitespace, duplicate candidates, budgets, off-spine
coverage, an eight-candidate batch, preexisting matches, wrong SHA and malformed pairs. The run took
100.164491 seconds overall with 28 fresh/final 28 inputs and a 1,354.52 MiB peak owned Job. Source and
product stages took 70.425573 and 23.129070 seconds, with libtest runtimes of 0.09 and 0.04 seconds.
Sampled system CPU peaked at 72.97 percent; existing one-CPU, BelowNormal, Cargo/test serialization,
CPU/RAM/commit/Job protections remained active and cleanup was confirmed. This does not establish
that the historic PC-freeze cause has been resolved.

A later single new test read the historical Hancom-saved HYPERLINK package, size 15,097 bytes and SHA
feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480. It returned zero CROSSREF observations
and NotObserved instead of relabelling a hyperlink as a cross-reference. Source bytes were preserved.
Exact inverse-prefix hashing restored the prior three-test file and all other declared inputs matched;
only the new test ran, with three filtered out. This later verification used 30 fresh/final 30 inputs,
30.013898 seconds overall, a 23.267780-second build/test stage, 0.50-second libtest runtime and a
633.11 MiB Job peak. Current evidence is eight source tests plus three product tests reused plus one
new captured-file negative test, not a single current-generation twelve-test run or a new native run.

Records: `evidence/p09-361-crossref-source-observation-tests001.v1.json` and
`evidence/p09-361-crossref-source-observation-captured002.v1.json`.
Actual native command capture/readback, target/identity mappings for other kinds, SDK action and
save/reopen behavior, HWPX parameter semantics, full state/flow, preservation/differential and the
P09 Gate remain unqualified. No Native010 replay, Native011 or Hancom/access-dialog activation occurred.
Acceptance remains 158/249 with 91 pending, P09/A12/A13 OPEN, P10 unstarted and the full goal active.
