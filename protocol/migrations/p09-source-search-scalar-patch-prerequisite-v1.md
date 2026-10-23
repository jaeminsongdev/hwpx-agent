# P09 original scalar range patch prerequisite

`PatchIntent::ReplaceLeafScalarRanges` supplies the original-coordinate editing primitive needed
for SEARCH-006. It preserves original lexical bytes outside selected scalar ranges. It does not
yet connect search results, complete protection policy, authenticated product requests or revision commit.
There is no service JSON schema, database migration or capability registration change.

## Typed source coordinates

The intent takes an original XmlElementSelector and LeafTextRangeReplacement values. Each value
contains a half-open decoded Unicode scalar range and validated XML 1.0 semantic replacement text.
There are no caller byte offsets, raw XML fragments or unchecked deserialized proof objects.
The source selector retains its existing whole XML digest/name/element binding.

Ranges must be ordered and disjoint in original coordinates. Adjacent nonempty ranges are allowed;
ambiguous insertions touching another range, overlapping/unsorted/empty batches and duplicate element
requests fail. Duplicate checks use the package collision key, including case-folded/NFC path identity.
Multiple ranges on one leaf belong in one intent and share one source scan.

The leaf has no child elements or comments. Root edits and stale source selections fail. An insertion
at zero can expand a self-closing leaf while retaining its original name/attributes. Existing
nonempty leaves support insertion/deletion/replacement at valid scalar boundaries. This is not
permission to erase controls inside mixed content.

## Exact bytes and finite work

Text/reference tokens map decoded scalar boundaries back to original bytes. Literal CR and CRLF
follow XML newline normalization; a character reference to CR remains its own scalar. References
retain their entire source span. Only requested boundaries are stored, with endpoints collected
linearly after ordering validation. Replacement text is escaped once and semantic CR uses &#13;.
Unselected entities, literal newlines, tags/attributes/siblings and other package parts stay exact.

Preflight bounds aggregate range count across all new intents, per-value bytes and aggregate escaped
bytes before allocation. Existing PatchLimits defaults apply:4096 aggregate scalar ranges,1 MiB per
semantic replacement and128 MiB escaped replacement bytes. Existing transaction conflict, growth,
ID, preservation and writer validation remain. These are configurable validated limits, not a
performance benchmark or full protection assessment.

## Verification and preserved failures

Components061 fails compilation on missing Eq/PartialEq for the new range type; no tests execute.
Recovery062 adds only those derives and passes eight new scalar tests plus three existing whole-leaf
and two targeted original atomic-patch tests:13 pass,466 fresh/final466, no diagnostics and closed Jobs.

Subsequent review switches duplicate detection to the existing package collision key and removes
redundant endpoint sorting. Alias063 stops on system CPU96.35%; the owned Job records CPU0.172s,
private34.71 MiB, one-core/6.25% limits and terminal/empty/closed cleanup. The triggering process
is not causally identified. No resource policy, Defender/OS settings or unrelated process is changed.

Linear064 fails compiling a new test's direct private collision_key call. The production code/API
stays unchanged; the ASCII fixture compares public path spellings instead, and the engine's actual
Conflict error verifies alias rejection. Linear065 runs all nine affected scalar tests:9 pass,
468 fresh/final468, no diagnostics and terminal/empty/closed Jobs. Five unchanged legacy patch
passes remain preserved without replay, for14 distinct validated cases. All failed/stopped originals
remain unchanged. Previous search/product tests and the official queue are not reexecuted.

Coverage includes exact expanded part bytes/other parts, multibyte/entity selections, literal versus
reference newlines, insert/delete/adjacent/disjoint ranges, partial-batch rejection, stale selections,
aggregate count/value/escaped limits, case aliases, deterministic output and redacted Debug.

## Required search and product joins

The [actual literal candidate and stored boundary](p09-source-literal-replacement-output-v1.md) now
connect mapped plain-leaf matches, explicit run policy, observed guards and output readback. The
generic primitive's XML CR support does not qualify HWPX plain-text control-character insertion.
Full mixed/control/field semantics and the product/commit work below remain separate requirements.

The full search/product path must bind actual search matches to original pieces, prove NFC source selection
and contiguity, reject overlapping original selections, and define multi-run formatting and mixed
atom handling without inventing native defaults. It must apply field/table/other observed protection,
scope and replacement-count limits, build one candidate transaction and independently read back
the output semantics and exact preservation. Current source/ACL/head and final consumer boundaries,
strict product requests and actual CAS/execution/publication remain separate work.

Source API v12 remains incomplete/four unresolved/null report/exit3. Queue158/249, remaining91,
next165, P09/A12/A13 OPEN, fixed CROSSREF eight NOT_RUN, Native011 unapproved/unexecuted,
P10 not started and goal ACTIVE remain unchanged. The scalar primitive does not close SEARCH-006
or the P09 Gate and does not prove the PC freeze cause resolved.
