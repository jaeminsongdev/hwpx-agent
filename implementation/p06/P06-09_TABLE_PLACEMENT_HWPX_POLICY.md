# P06-09 table placement HWPX adapter policy v1

Status: direct HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope

This profile maps the complete `hwpx-agent.table-placement/v1` state for four capabilities into
the reviewed current-Hangul-2020 table XML shape:

- `TABLE-034` / `table.position`
- `TABLE-036` / `table.inline_floating`
- `TABLE-037` / `table.wrap`
- `TABLE-038` / `table.outer_margin`

The admitted native surface is the selected `hp:tbl` root's `textWrap` and `textFlow`, its single
direct `hp:pos`, and its single direct `hp:outMargin`. The strict table-layout reader first admits
the entire grid/cell shape and produces a content digest. Unsupported, missing, duplicate,
noncanonical or over-limit native values fail closed.

## Exact current-profile mapping

The adapter maps all four horizontal reference frames, all three vertical reference frames, all
five horizontal and vertical alignments, signed offsets, `flowWithText`, `allowOverlap`,
`holdAnchorAndSO`, `treatAsChar`, `affectLSpacing`, the four table wrapping styles, the four side
flow modes and four nonnegative outside margins. Boolean values are canonical `0` or `1`; numeric
values are canonical decimal HWPUNIT with finite bounds.

Inline lowering owns only `treatAsChar`, `affectLSpacing`, wrap/flow and margins, preserving the
inactive floating-position attributes byte-for-byte. Floating lowering owns the complete floating
payload but preserves inactive `affectLSpacing`. This makes attachment transitions explicit and
prevents an adapter from inventing discarded inactive values.

The mapping is bounded to table UI semantics documented by Hancom. General shape-object
`Tight`/`Through` wrapping is not admitted as a table capability. Reviewed official sources are
the Hancom HWPML revision 1.2 specification and the Hancom table-properties help page:

- <https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D3.0_HWPML_revision1.2.pdf>
- <https://help.hancom.com/hoffice/webhelp/9.0/en_us/hwp/table/tableattribute/table(general).htm>

## State drift, lowering and preservation

Source and target states are independently serialized, reopened and hashed before parsing. Their
logical table IDs must match. Native source readback must equal the complete active source state;
otherwise no bytes are returned. Only differing owned attribute value spans are edited. The output
is strictly reparsed and must equal the quantized target state while retaining the source content
digest.

The closed synthetic package fixture covers all five domain operations, including both attachment
directions. It reopens the package graph and requires exact formula AST/cache and pagination
readback, exact expanded-byte SHA-256 for every non-section part, a preserved merged-cell sibling,
deterministic package bytes and immutable source bytes. The receipt binds source/output bytes,
source/target states and table content hashes; Debug omits those hashes and document values.

## Evidence promotion rule

Passing the seven adapter tests and private tamper suite promotes only these four rows from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with `schema`, static
`semantic_reopen`, `formula_readback` and `page_split`. It does not prove renderer identity,
licensed Hangul 2020 save/reopen, target-build, automation runtime, differential exact match,
rollback/retry, release-enabled status, arbitrary user-document compatibility, another PC/version,
P06-09/P06 PASS, production or product completion.
