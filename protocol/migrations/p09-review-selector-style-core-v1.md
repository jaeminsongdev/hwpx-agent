# P09 Review Selector Style Core

SourceReviewScopeIndex.find_style combines document, section, selection and node set windows with explicit
hidden explanation/MEMO body policy and declared-reference or typed-definition style predicates. This
profile qualifies the source core. Its separate current stored/strict JSON/cursor connection is qualified
in [the v7 product profile](p09-review-selector-style-product-v7.md). Legacy request meanings are unchanged.

The separate [character-property replacement source profile](p09-source-character-style-replacement-v1.md)
uses the same matcher with an operation-local target declaration. Existing no-target search results,
hashes and predicates remain unchanged; v7 search does not become a style-mutation product route.

## Selection and style predicates

The original scope resolver validates the whole admitted source index and actual supplemental review
node IDs. The same windows are then filtered by explicit body policy before the matcher applies style
predicates. Scope, body-policy and style exclusions precede accepted-match limits. Regex sees the clipped
window, and original NFC/source positions remain global. A selected-out first match cannot consume the
limit or widen the selection into its whole paragraph.

SourceReviewStyleFilter is Declared or Definition with an explicit filter object. Declared compares the
original p/run/t reference axes independently. Definition uses the original typed header catalogs and
explicit run/text/named-character or direct/named-paragraph axes. Missing references remain absent, not
zero or a fallback. Every original scalar contributing to an NFC match must satisfy the predicate; mixed
run styles across a composed Hangul character therefore reject that character. Zero-width matches have
no source contributors and are not style matches. Empty/unused/missing filter axes are rejected.

Definition admission resolves all present indexed references, including policy-excluded regions. Dangling
IDs and invalid header counts/links fail rather than returning an apparently complete empty subset.
Declared ID matching does not claim that a referenced definition is valid or that an implicit formatting
cascade has been evaluated. Actual hidden visibility, rendering and effective formatting remain unqualified.

## Shared source work and bound result

The declared and definition all-contributor predicates are extracted from their original closures without
changing their logic. Review window/policy resolution and result assembly are extracted once for both
plain and style paths. Removing those helpers reconstructs all three original files exactly, including
query hashes, exclusions, result limits, original plain/review searches and their flags.

One operation builds the original inspection metadata from already imported source XML. Only Definition
builds its original typed-definition lookup, once for the entire query rather than per match. No second
source package/XML/Form import is added per match. Existing regex/source/point/catalog/output bounds remain.

The result profile is hwpx-agent.source-review-selector-style-search/v1. It binds filter, inspection and
optional definition receipt, source index/scope/query/policy and selected matches. The contained search
uses this new profile, not the legacy plain-search profile. Its original inspection receipt stays a
declared-inventory receipt; the separate definition receipt proves the explicit definition join.

The entire response, including filter/definition/window/region metadata, must fit the original result
byte cap without truncation. Pure core navigation binds the full style result and preserves source pieces
and regions without another search. The caller-supplied core context and receipts are not service access,
revision, editing, Native or execution/publication authority. No raw body/author text is included.

## Verification and resource observations

Components103 passes8 new and27 unchanged affected cases:9 declared/control,10 definition and8 review
selector cases,35 total with552 fresh/final552 and cleanup true. Coverage includes both predicate families
with all four scopes, an actual MEMO node, partial regex/zero-width semantics, policy/predicate exclusions
before limits, mixed NFC contributors, missing and explicit source axes, dangling excluded references,
invalid headers/filters, filter/policy/cursor binding, exact response cap and one-byte shortage, source
preservation and non-disclosure. Prior33 navigation, other completed suites and official249 cases are not
replayed. The reused fixture's unused package/with_body helpers produce two warnings; they are not suppressed.

Overall149.640 seconds, command77.047 seconds, test body2.33 seconds, owned Job CPU28.031 seconds.
Maximum sampled system CPU20.83%, minimum available RAM35.5548%, peak Job private5.0859% of physical RAM.
The Job ends active0/empty/handle closed. One CPU affinity1, BelowNormal, CPU cap6.25%, private cap8%/stop7%,
RAM/commit95%, command300s, guard600s and before/after input checks remain. These are run observations, not
a benchmark, process attribution or PC-freeze resolution. Evidence:
implementation/p09/evidence/p09-361-selector-styles-components103.v1.json.

## Remaining product boundary

Current stored access, strict JSON and cursor binding are qualified separately in the v7 product profile,
retaining whole source proof and current write/scope/head/ACL/quarantine/AEAD/final-consumer checks.
This core profile alone does not confer service authority.

The separate [direct-formatting resolution profile](p09-source-resolved-formatting-v1.md) uses the same
selected review windows to reject unresolved required source axes before searching. It preserves this
explicit declared/definition filter contract and does not infer Native cascade or display visibility.

Control scope needs actual control_anchor position and exact selection-boundary projection. Some controls
have no indexed text scalar; selecting their paragraph alone would admit controls outside the requested
window. This implementation does not substitute that paragraph fallback or claim control-scope completion.
Effective cascade/visibility, full source coverage/Native flow, full SearchScopeSelector, replacement/
conversion, complete protection, match_set/semantic_diff/reopen, transaction/dispatcher/DB/CAS/execution/
publication and Native/Gate evidence remain open.

Source API v12 stays incomplete with four unresolved stages, null report and CLI exit3. Official acceptance
is158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011 is unapproved/unexecuted.
P09/A12/A13 stay OPEN, P10 is unstarted and the full P09 through P20 goal stays ACTIVE.
