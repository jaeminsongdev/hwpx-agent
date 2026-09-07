# P06 table cell style v1 to v2

P06-04 v2 adds explicit `hwpx-agent.table-cell-style.hancom-2020/2` exact-build rules on top of
immutable `hwpx-agent.table-cell-style.hancom-2020/1` for the bounded synthetic HWPX emitted by this
PC's licensed Hangul 2020 `11.0.0.9136` x86 installation. The immutable v1 contract and default
APIs keep their original rules; there is no automatic profile detection or silent v1 widening.

The actual source capture established four serialization facts that v1 did not admit:

- `hp:tc` children occur as `subList`, `cellAddr`, `cellSpan`, `cellSz`, `cellMargin`;
- `hasMargin="0"` can retain nonzero inherited/default `cellMargin` numbers, which are inactive;
- table and sub-list IDs plus border-fill and zero-sentinel link references require table ID rules;
- exact `Preview/PrvText.txt` with media type `text/plain` can begin with visible angle-bracket cell
  markers without being XML.

Callers migrate only by explicitly selecting all matching v2 profiles. The v2 style reader treats
inactive stored margin numbers as `None`; when lowering `None`, it changes `hasMargin` as needed but
preserves the four inactive numeric value spans. A present margin still rewrites all four bounded
values. The same selected profile is required for post-lowering readback and is recorded in the
receipt.

The preservation exception is exact-path and exact-media only. Core v1 and every other path still
reject XML-looking non-XML bytes. The table ID profile adds only observed `hp:tbl`, `hp:tc` and
`hp:subList` declarations/references, accepts zero only for the observed link sentinels, and keeps
unknown, malformed, duplicate, dangling and wrong-type IDs fail closed.

Hangul 2022, Hangul 2024, other builds, arbitrary documents, auto-repair and generalized preview
classification are not migrated. They require independent profiles and actual runtime evidence.
