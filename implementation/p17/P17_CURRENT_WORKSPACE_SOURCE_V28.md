# P17 current workspace source qualification v28

Date: 2026-09-07

Scope: P06-05 current-Hangul-2020 HWPX table-layout adapter component successor only

Decision: **qualified source boundary only; no P06-04/P06-05 card, phase, runtime or product PASS**

The v1-v27 qualification contracts remain byte-for-byte unchanged. This v28 layer composes exact
v27 contract SHA-256 `eb2ca5b661ed303ba9522e401b732606621c2b63c32eaf5f2dfb8ddf6563a222`
and advances the source view to clean commit
`2a9f7e992dc49aea54b02a784e01e0d45cbed4b3`.

Current-host source acceptance run `52e6bb043715461aac1b22ebc213dbb2` passed all 11 checks. Its
canonical receipt SHA-256 is
`58072df41cdbfd3c71ab207a99d4f917fb18f90edb3e034c517e14aaa7857851`. The twenty-six cumulative
successors and locked/offline 25-member Cargo projection remain exact.

This layer binds ten exact files: the package dependency and lock update, public export, bounded
HWPX layout reader/lowerer, twelve-test suite, scoped policy, private contract, migration, contract
validator and four negative validator tests. It admits only a verified grid-bound layout plan and a
narrow absolute-size, zero-spacing current-2020 table shape. It quantizes the logical column/row
vectors once, makes table and merged-cell dimensions exact sums, changes only existing size value
spans, reparses the result and proves content-token digest identity.

The dedicated Rust tests passed 12/12, all `hwpx-package` targets passed, all P06 Python tests passed
29/29, the full Rust workspace passed with only the pre-existing isolated-PostgreSQL test explicitly
ignored, and workspace formatting and warning-denied Clippy passed.

This proves source bytes and component checks only. P06-04 still waits for actual licensed Hangul
2020 file-access approval and runtime evidence. Installed-font extraction, renderer equality, row
constraints/equalization, P06-04 or P06-05 completion, another PC/version, production and product
completion are not claimed.
