# P05-09 VS-1 layout policy

## Scope

P05-09 closes only the **layout portion** of VS-1 defined by the P05 roadmap: one deterministic
current-PC Hangul 2020 document combining a custom 230 x 310 mm landscape page, a balanced two-column
section, and typed title/body character and paragraph styles. The broader product VS-1 still requires
the P06 table, P07 native equation, P10 Windows worker, and their own target evidence.

## Public boundary

`Hancom2020Vs1LayoutDocument` accepts only bounded single-line text. It requires one title and between
2 and 32 body paragraphs, normalizes them to NFC, rejects controls and XML noncharacters, and caps the
combined UTF-8 text at 32 KiB. The caller cannot supply raw XML, action strings, package paths, style
IDs, or automation commands.

`Hancom2020Vs1LayoutBuilder` applies the fixed typed profile through the already validated P05
character-style, paragraph-style, page-setup, section-column, and text-flow modules. It rebuilds a
VS-0 package deterministically and releases bytes only through `with_verified_bytes` after:

- bounded ZIP admission and full package-graph coverage;
- current Hangul 2020 ID-index validation;
- exact custom page and two-column semantic readback;
- title/body style signature and reference validation;
- exact paragraph count, one explicit column break, and NFC visible-text digest validation.

## Failure and preservation rules

- Missing or non-unique template anchors fail closed; no heuristic mutation is used.
- Source packages and user documents are never modified in place.
- Output publication in the target fixture uses `create_new`; an existing path is not overwritten.
- Debug output contains only counts, sizes, digests, profile IDs, and stable error codes, not document
  text.
- P05-09 remains `unverified` until the generated target is saved, reopened, and rendered by the exact
  licensed Hangul 2020 build on the current PC, with source immutability and semantic readback proven.

## Required evidence

1. Rust unit/integration tests, formatting, Clippy, package regressions, and clean-checkout FULL pass.
2. Deterministic target build and product-side semantic inspection pass.
3. Exact Hangul 2020 save/reopen succeeds with unchanged canonical visible-text digest.
4. PDF export passes bounded PDF structure and nonblank render verification.
5. A separate strict P05 Gate audits P05-01 through P05-09 without promoting synthetic evidence to
   actual target evidence.
