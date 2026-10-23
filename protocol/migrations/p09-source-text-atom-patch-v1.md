# Source text atom scalar range patch

## Purpose and admission

ReplaceTextAtomScalarRanges edits existing Text atoms in original HWPX TextSpan elements while
preserving tab and lineBreak elements as original bytes. It is an additive patch prerequisite for
mixed-body literal replacement, not a change to the existing v1 replacement compiler or product JSON.

The target is an immutable XmlElementSelector for a non-root hp:t in the Hancom 2011 paragraph
namespace. A crate-private bridge calls the original read_text_span, including its original attribute,
tab parameter, empty-control, plain-text and opaque/comment checks. The bridge bounds the selected
element's outer bytes and element count and uses the existing finite TextFlow limits. It does not
replace whole-package or standalone paragraph envelope validation.

Supported controls are the original qualified hp:tab and hp:lineBreak. Unknown elements, comments,
invalid controls and unsupported attributes fail closed. The existing writer ID profile remains
independent: in particular, this addition does not qualify charStyleIDRef for hwpml_2011_shape_v6.

## Coordinates and preservation

TextAtomRangeReplacement::new(source_atom,start_scalar,end_scalar,replacement) uses a half-open
range inside one original Text atom. Adjacent Text/Whitespace/Reference tokens are one Text atom;
each tab/lineBreak contributes an atom index but cannot be selected for editing. Coordinates refer
to decoded original Unicode scalars, not NFC positions, UTF-8 offsets or XML bytes.

Text before and after a control belongs to separate atoms. Leading or adjacent controls do not
create phantom empty Text atoms. An empty/control-only source has no editable Text atom. Deletion
can remove all text from an existing atom; original controls, including whitespace inside paired
control tags, remain byte-exact. Insertions address existing Text atom boundaries only.

The original reader decodes the element once. A parallel lexical inventory skips complete control
token spans and matches the reader's Text/control atom order. For each selected Text atom, the shared
scalar boundary helper scans original text/reference tokens once and records only requested
endpoints. All requested ranges for that atom share the scan. The helper retains the original
entity spans and XML scalar normalization semantics; TextAtom values retain the stricter HWPX
plain-text policy and reject control/noncharacter replacement strings.

Only selected scalar bytes change. Control XML, unselected entity spelling, element/run attributes,
unselected section bytes and other package parts are preserved by the tested patch/writer path.
There is no raw XML or caller byte-offset input. The original ID, preservation and writer checks
are retained; this primitive itself is not field-cache or document-protection authorization.

## Limits and compatibility

Ranges are ordered by original atom then scalar range. Reversed/out-of-bounds/control ranges,
overlap and ambiguous touching insertions are rejected. One element may appear only once across
ReplaceTextAtomScalarRanges and ReplaceLeafScalarRanges, using package collision key plus element
identity. This prevents path aliases or split intent families from duplicating the same scan.

When an atom intent is present, both range-intent families share aggregate range-count and escaped
replacement-byte limits as well as per-value limits. Existing PatchLimits apply before endpoint
or escaped-output allocation. No per-match package/Form import or repeated whole-atom scan is added.

ReplaceLeafScalarRanges retains its original child rejection, self-closing leaf behavior and generic
XML CR/CRLF support. Its endpoint decoder is extracted into a shared internal function, with exact
inverse checks and all nine current scalar cases passing. Existing text reader/writer/value policy,
other intent bodies and public exports are inverse-checked outside additive declarations.

## Verification

Components072 records eight passes and two new fixture failures, with cleanup confirmed. One
fixture expected a charStyleIDRef unsupported by the original ID profile; the other used D, which
also matched the unchanged sentinel text. Recovery073 retains the original ID rejection as a
negative case, tests namespace declaration preservation and uses a unique search character.
The only production repair is an unused import removal, not a reader/ID/policy change.

Recovery073 executes only those two repaired cases and nine not-yet-run affected scalar cases:
11 current passes plus eight preserved passes, 19 distinct validated cases,481 fresh/final481,
no diagnostics and both Jobs terminal/empty/closed. Exact inverse checks preserve the other eight
test bodies, shared fixtures, original reader/value policy and scalar decoder/edit implementation.
The failed Components072 result remains immutable.

The tests exercise actual source-search piece coordinates, multiple original atoms, non-BMP/entity
scalars, exact control and unrelated-part bytes, leading/adjacent/trailing controls, insertion/deletion,
malformed/opaque/control values, cross-family budgets, duplicate/overlapping/stale selections and
redacted values. They do not integrate the mixed-body search replacement compiler or service.

Overall recovery is144.047 seconds, repaired command78.109/test0.50 and scalar command1.672/test0.10.
Maximum system CPU is26.89%, minimum available RAM26.6786%, peak Job private5.0086% of physical RAM.
One core, BelowNormal, CPU cap6.25%, private cap8%/stop7%, RAM/commit95% and input checks remain.
These observations are not a performance benchmark or proof that PC freezes are fixed.

## Remaining implementation

The separate [v2 candidate and stored-service profile](p09-source-literal-text-atom-output-v2.md)
now qualifies source-bound literal lowering, TextSpan/control readback and current stored access.
Existing compiler/stored/product v1 still rejects mixed leaves. Source ownership handoff and strict
v2 product JSON preparation are qualified in the separate
[v2 request profile](p09-literal-replacement-product-request-v2.md), not by this primitive profile alone.
Full search scope, hidden/MEMO/field/newline replacement, full protection and target match_set/
semantic_diff/reopen, dispatcher/DB/CAS/execution/publication and Native remain unqualified.

The official queue stays158/249 with91 remaining and case165 next. Source API v12 is incomplete,
four unresolved/null report/exit3. Fixed CROSSREF8 remains NOT_RUN, Native011 unapproved/unexecuted,
P09/A12/A13 OPEN, P10 not started and the full P09–P20 goal ACTIVE.
