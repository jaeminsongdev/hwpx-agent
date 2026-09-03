# P05-03 paragraph-style reader/writer report

- Generated: 2026-09-03
- Implementation and audited source commit: ec76232756d355c2a71f0322a3982746c94cbfee
- State: pass_current_pc_local_paragraph_styles
- Reasoning/review mode: max / namespace, layout, compatibility, reference and fail-closed audit

hwpx-package now exposes the executable hwpx-agent.paragraph-style/1 model. It lifts the exact
current-2020 paraProperties and referenced borderFills through the P03 preserving XML tree, types the
paragraph layout and compatibility branches, validates external tab/list reference domains and lowers
deterministic escaped XML. Every output is reparsed for exact typed equality and reference closure and
is bound to a digest/count receipt.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Source/profile lock | pass | locked KS X 6101 reform-03 Appendix C/F structural source plus exact current generated 2011 head namespace |
| Exact current header | pass | 20 dense paraPr IDs, tab domain 0..2, numbering domain 1, no bullet domain and borderFill IDs 1..2 |
| Typed paragraph layout | pass | alignment, break/condense/grid/font-line-height, signed margins/indent, spacing, line spacing and auto spacing |
| Pagination semantics | pass | widow/orphan, keep-with-next, keep-lines and page-break-before flags plus the exact HwpUnitChar current/fallback switch |
| Heading compatibility | pass | current/fallback heading branches, NONE/OUTLINE/NUMBER/BULLET reference rules and levels |
| Border/fill semantics | pass | side lines, offsets, connect/ignore-margin, diagonal center line, winBrush and typed colors/widths |
| ID/reference integrity | pass | count, dense ID and tab/numbering/bullet/border closure; P05-02 character-border references can be checked |
| Semantic dedup | pass | ID-excluding first-occurrence identity including both compatibility branches and checked dense allocation |
| Typed rewrite | pass | complete-map validation before mutation; only typed P05-01 paragraph-property references change |
| Deterministic lower | pass | bounded escaped fragment, exact lower-to-re-lift equality and stable SHA/count receipt |

## Validation evidence

- Windows Rust 1.96.0: paragraph-style 12/12, complete hwpx-package 86/86, workspace tests, format and
  Clippy with warnings denied passed.
- Exact current generated header lifted all twenty paragraph records and both border/fill records with
  complete external tab/numbering/bullet domains. P05-02 character-style border references resolved
  against the same catalog.
- Alignment, signed margin/indent, spacing, all supported line-spacing units, break/keep variations,
  both compatibility branches, border/fill shapes, dedup, typed reference rewrite and malformed/count/
  ID/reference/range/enum/namespace/limit cases passed.
- The fixed 128-case paragraph-layout lower corpus is byte deterministic with aggregate SHA-256
  ae926c9940e0989eb49f977bcacf1266b12f2a62309896cb7c112b87220ed339.
- Exact commit ec76232 passed offline Linux Rust 1.96.0 workspace Clippy/tests with network disabled,
  repository and Cargo registry read-only, and only a disposable build directory writable. Pinned
  validation image digest:
  sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f.
- Current checkout and exact-commit clean clone each passed all 5/5 bootstrap lanes; both Git states
  remained clean. Security scanned 589 files in each checkout with secrets/vulnerabilities/forbidden
  licenses 0; current/clean-clone SBOM components were 273/231.
- The locked machine-readable source remained SHA-256
  c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4.
- Hangul UI/runtime executed by this task: false. User documents opened or modified: 0.

The first isolated Linux invocations used a login shell that hid the pinned toolchain and then an
empty container registry. Both stopped before compilation. The successful run used direct pinned
toolchain binaries and the host Cargo registry as a read-only mount while retaining network denial.
The clean clone and all disposable Linux build data were deleted after validation.

## Strict self-review

- Change risk: high; tab/list/page/section lowering and later layout validation will trust these IDs,
  units, compatibility branches and paragraph semantic identities.
- Review found that the public deduplication mapping could otherwise be malformed by a caller before
  reference rewrite. Complete map-domain, target-range and source-reference validation now occurs
  before any mutation.
- Exact 2020 winBrush faceColor="none" is preserved as an observed profile fact despite the narrower
  later RGB schema. Unsupported gradation/image fills fail closed instead of being guessed.
- External tab/list definitions remain explicitly owned by P05-04/P05-05 and are supplied as typed
  reference domains for standalone fragment readback; the paragraph writer never overwrites them.
- No raw XML fragment, arbitrary path, COM/HAction string or platform fallback is accepted.
- Final blocker/major/minor findings after remediation: 0/0/0.

## Scope and remaining boundary

P05-03 does not prove arbitrary-document editing, full tab/list definition semantics, page/section
pagination, visual layout, gradation/image fills, real Hangul save/render behavior, another PC, or
Hangul 2022/2024 compatibility. It is a bounded package/IR contract over the exact generated current-
2020 profile. Runtime/render claims remain later exact target-oracle evidence.

## Next exact task

Start P05-04 Tabs at reasoning effort max. Lock the exact current-2020 tabProperties records and the
official Appendix C/F tab-stop enums and units. Implement bounded typed default/automatic and custom
left/right/center/decimal stops, leaders, ordering, semantic dedup, paragraph-reference rewrite and
deterministic lower/readback fixtures. No Hangul UI is required for the first package/IR slice; an
actual Hangul 2020 target readback will be requested only when its disposable fixture is ready.
