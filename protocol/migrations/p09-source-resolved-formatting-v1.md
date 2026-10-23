# Selected source formatting resolution

`hwpx-agent.source-resolved-direct-formatting/v1` adds required-axis coverage before searching selected
source formatting. It distinguishes unresolved formatting from a valid empty match set. This is a
direct-source predicate and resolution core, not complete Native effective-style/cascade/visibility,
general product execution or P09 completion. Its separate
[current stored/v9 product binding](p09-resolved-style-product-v9.md) preserves the resolution errors,
current-access boundary and retained-result navigation.

## Source meaning and unresolved axes

[Hancom's HWPX parsing explanation](https://tech.hancom.com/python-hwpx-parsing-2/) connects paragraph
paraPrIDRef and run charPrIDRef to the definitions in header.xml. The original typed readers provide
those actual direct values. The pinned official
[text model](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/t.h)
also exposes charStyleIDRef; its storage declaration is not a precedence rule.

SourceResolvedStyleFilter requires a nonempty combination of bold, italic, height_hwpunit, text_rgb
and alignment. It has no caller-selected source axis or approval/default switch. False is a real
predicate. Unknown fields and invalid value shapes reject typed deserialization.

The optional [character-detail extension](p09-character-detail-search-v1.md) adds24 predicate families on
the same original typed character declaration. Omitting it preserves the original canonical filter bytes.
It keeps the required-axis rules below and does not qualify font substitution, cascade or visibility.

The optional [paragraph-detail extension](p09-paragraph-detail-search-v1.md) adds27 predicates on the original
typed paragraph declaration. Explicit measurement units and compatibility branches are compared independently,
not rendered or resolved into a Native branch. Requesting these details requires the direct paragraph axis;
omitting them leaves prior canonical bytes and required-character-axis behavior unchanged.

The requested character axis resolves from an existing run reference only when no text-style reference
is present on t or in an enclosing paragraph-namespace ctrl. A missing run reference or such a present text-style reference keeps that character segment
unresolved, including ID0 or a coincidentally equal value. The requested paragraph axis requires its
direct paragraph reference. An unrequested axis need not be resolved. This does not infer missing
references as0, named-style defaults, nextStyle inheritance or a text/run priority from attribute names.

The [control-context correction](p09-control-style-context-v1.md) computes one parent-context map per
selected source part, without reparsing XML or walking ancestors per match. Context does not leak to
siblings/excluded regions or empty windows; duplicate t/control uncertainty counts once per segment.
This is not an inferred Native inheritance rule. Styled MEMO wrappers rejected by original admission
remain rejected, not admitted through the new coverage check.

Each unresolved required selected axis produces SourceResolvedStyleSearchError::Unresolved with a
bounded coverage receipt before query matching, even when the query would find nothing. It cannot
silently omit unknown-format text and return a successful empty result. Existing malformed/dangling
references and header admission still reject the entire original typed catalog; policy exclusion is
not permission to admit an invalid source.

## Exact scope and shared work

The existing four source selectors resolve once. Hidden-explanation/MEMO policy exclusion happens
before coverage and result limits. Outside-scope or policy-excluded unresolved segments do not affect
the selected coverage. File-body labels remain distinct from Native application visibility.

One inspection and one typed-definition import serve coverage and matching. Selected NFC units
contribute every original scalar/segment; a deduplicated segment set is assessed once, not per match.
An empty scalar window selects0 contributing segments and produces no style matches, including a
zero-width regex result. The original all-contributor direct-definition predicates run over exactly
the resolved windows. No extra package/XML/header import or normalization algorithm is introduced.

SourceResolvedStyleCoverage contains the original definition receipt, selected/resolved/missing/text
uncertainty counts, segment visits and requested-axis completion. Native effective/visibility/execution
authority and inferred-default/named-fallback flags stay false. The result binds source/index/header,
scope, body policy, query, filter and coverage into its request fingerprint and retained navigation.
The entire JSON response, including coverage, obeys the existing bound; exhaustion is not truncation.
No query/body/author strings are emitted. There is no source edit, ingest, commit or durable key claim.

## Qualification

Components148 passes18 new tests with635 fresh/final635 inputs, no diagnostics/warnings and confirmed
cleanup. Only two module declarations are added to existing definition/selector roots; their complete
prior bodies match the preceding paragraph-product baseline after removal. All other production,
fixture, product and prior test inputs remain exact. Previous suites and the official249 queue are
not rerun or promoted to this new scope.

Coverage includes independent original typed-reader values, false and conjunctive predicates,
missing axes before absent queries, text-style0/1 ambiguity, requested-axis separation, four scopes and
clipped/outside windows, hidden/MEMO exclusion before resolution and caps, every NFC contributor,
regex/case/word/zero-width behavior, original dangling/header rejection, closed filters, invalid scopes
and stale source, retained-cursor identities, exact output bounds, query/match/pattern limits,
128 segments/128 matches with one assessment per segment, source preservation and non-disclosure.

Overall108.484 seconds; command27.094 seconds, libtest2.19 seconds and owned Job CPU25.422 seconds.
Peak private memory1684.28 MiB or5.2864% of physical RAM. Maximum sampled system CPU69.14%; minimum
available RAM23.8824%. Whole-system samples are not process attribution. Logical CPU2/mask4,
BelowNormal, CPU cap6.25%, private8%/stop7%, RAM/commit95%, command300s/guard600s remain, with final
active0/empty/handle closed. These observations are not a benchmark or proof of a PC-freeze fix.
Other processes, OS and Defender settings are unchanged.

Evidence: implementation/p09/evidence/p09-361-resolved-style-components148.v1.json.

## Remaining product and phase work

Current stored/strict v9 product binding qualifies20 new cases with639 fresh/final639 inputs through
the linked profile. Next is authoritative qualification of text-style precedence, missing-axis
behavior and Native visibility. None is inferred from the new
direct-source predicate. Complete cascade, full selector/filter/protection, match_set/semantic_diff/
reopen, dispatcher/storage/CAS/idempotent execution/publication and required Native evidence remain.
Source API v12 stays incomplete/four unresolved stages/null report/CLI exit3. Acceptance stays158/249
with91 pending, next case165; fixed CROSSREF8 NOT_RUN and Native011 unapproved/unexecuted.
P09/A12/A13 remain OPEN, P10 is unstarted and the full P09 through P20 goal remains ACTIVE.
