# P09 actual literal replacement candidate v1

`ImportedDocumentForms::lower_literal_search_candidate` and its exact VerifiedFormReconstruction
entry lower actual mapped literal matches into one preserving package candidate. The authenticated
stored adapter prepares and exposes that candidate under current source authorization. There is
no revision commit, key claim or full SEARCH-006 qualification. The additive strict
[product request](p09-literal-replacement-product-request-v1.md) now binds this same candidate path.

## Original selection and explicit run policy

The API requires a literal SourceSearchQuery, explicit SourceSearchScope, replacement text and
FirstOriginalRunRetainAllRuns policy. Existing NFC/simple-casefold/whole-word matching and bounded
complete match-set behavior apply. Query max_results is the complete replacement-selection bound;
overflow rejects the operation instead of truncating it. Scope validation precedes zero-match results.

Every occurrence must select all contributing original scalars exactly and contiguously. Partial
normalization expansions, noncontiguous canonical-reordering selections and overlapping original
selections fail. Reordering is supported when the whole original selection is contiguous. Matching
across source runs retains exact source points. Replacement goes into the first original text leaf;
selected ranges in later leaves are removed, retaining all run/leaf elements and their attributes.
This preserves declared source structure, not an inferred effective formatting or native layout.

Only mapped body/table/drawing/footnote/endnote plain text leaves are admitted. Mixed-atom leaves,
control/opaque/paragraph boundary crossings and hidden/MEMO-only body regions are not silently
flattened or treated as complete corpus coverage. No matches and no semantic change are explicit
errors. No-op scalar ranges retain their original lexical bytes; matched-occurrence counts and
actually changed range/leaf counts remain distinct.

## Protection and bounded lowering

The original field collector validates all represented fields. Cached field content is unqualified
for generic literal mutation, even when native editable=true. Field intervals are merged per part
and queried without rescanning every field per match. The existing table/cell/size/ancestor lock
scanner is reused once per changed part; its body is unchanged behind a crate-private bridge.
Missing flags are not full protection authorization. Full protection/native state stays unqualified.

The original TextFlow validate_text policy is reused through a crate-private bridge. XML-valid
control characters or Unicode noncharacters that the HWPX plain-text reader rejects fail early.
CR/LF/tab insertion requires separately qualified typed control handling; the generic XML scalar
patch's CR support does not override this HWPX contract. Regex mode is explicitly rejected here.

One original Form reconstruction supplies the operation-local proof; there is no per-match package
import or writer invocation. Source index and field collection use that original model. Segment
edits are grouped once, with4096 aggregate scalar ranges,1 MiB replacement limit, existing index
limits and bounded changed-leaf text/receipt bytes. Patch/ID/preservation/writer limits remain.
The compiler calls the original scalar-range backend in one transaction.

## Independent output checks and stored access

The complete output package is imported as Form/fields once. Expected leaf values are constructed
from decoded original text and source ranges, then checked against the imported output and digests.
Original/new XML outside selected leaf content spans is compared, including element counts, tags
and attributes. Other package parts cannot change. The scalar backend separately retains lexical
bytes outside selected ranges. The receipt's outside_selected_leaf_contents_exact deliberately names
the compiler's independent comparison scope, not an invented full semantic/Native verification.

The receipt binds source/index/scope/query/replacement/run policy, matched occurrences, changed
range/leaf digests, output SHA/size and observed guard counts. It contains no query/replacement
plaintext. field_cached_content_edit_qualified=false and
full_protection_native_or_execution_authority=false remain mandatory.

StoredImportedDocumentForms::prepare_literal_search_candidate requires current document.write,
provider scope/head/ACL/quarantine/AEAD and complete source reconstruction. Retained verify/bytes
reauthorize original source and writer integrity without rerunning the query or rebuilding the candidate.
The final head check is inside the writer callback before the consumer. No unchecked stored byte
getter, source overwrite, ingest/commit/CAS, durable key claim or execution/publication route is added.

## Verification and completion boundary

Components067 records nine core passes and one failure: a new literal-CRLF fixture is rejected by
the original typed reader during Form import. Reader/policy bodies stay unchanged. The new compiler
adds early reuse of that policy; the failing test becomes admitted multi-match replacement/deletion
plus explicit CR/LF/tab/noncharacter rejection. All other nine test bodies and compiler behavior
after the added precondition are retained exactly.

Recovery068 runs the corrected one core case and six previously unexecuted stored cases:7 pass,
472 fresh/final472, terminal/empty/closed Jobs. The previous nine unchanged core passes remain
preserved without replay, for16 distinct validated cases. An existing reusable fixture package helper
warning is disclosed. The original failed receipt remains failed; unrelated319 stored cases,
prior search/patch suites and the official queue are not rerun.

The linked product profile adds strict JSON/key/plan binding. Full SearchScopeSelector, hidden/MEMO replacement, field and
mixed/control/newline semantics, complete protection, target match_set/semantic_diff/reopen,
dispatcher/DB/CAS/execution/publication and Native remain. Source API v12 stays incomplete/four
unresolved/null report/exit3. Queue158/249, remaining91, next165, P09/A12/A13 OPEN,
fixed CROSSREF eight NOT_RUN, Native011 unapproved/unexecuted, P10 not started and goal ACTIVE
are unchanged. This candidate/stored path does not close SEARCH-006 or the P09 Gate.
