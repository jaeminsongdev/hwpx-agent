# P02-04 OWPML Extractor Report

- Completed: 2026-09-02
- Audited source commit: `dbad3a71ad2b3b756cbea34a2911610cea51fac1`
- Task state: `pass_current_pc_local`
- Review: `STRICT / xhigh`, blocker/major/minor `0/0/0`

## Source readiness decision

- The locked official machine-readable KS X 6101 reform 03 response is the authoritative input: source ID `ks-x-6101-machine-content-20260901`, SHA-256 `c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4`, 521 paired title/content sections and operation date 2024-10-30.
- Appendices B-H each contain one complete XML declaration and `xs:schema` document. The seven target namespaces are distinct and all use the OWPML `2024` namespace version.
- Section 8.2 contains the authoritative example ZIP container part table. It yields 22 file parts, including five bracket-marked optional parts.
- No standalone XSD ZIP/archive is claimed. The official response's embedded schema documents are parsed as exact locked source material; descriptive prose is not substituted for missing schema markup.
- The source is restricted to personal non-commercial local reference. Original JSON, reconstructed XML and extracted SourceRecords are not committed or redistributed.

## Delivered

- Read-only, source-lock/SHA-bound machine-standard decoder with strict UTF-8, NUL and replacement-character rejection.
- Deterministic recovery of the official viewer representation: 37 glossary-definition widgets reduce to their displayed term and display-only `<br/>` tags reduce to XML line breaks. Any residual HTML, ambiguous schema boundary, `DOCTYPE`, `ENTITY`, foreign element, duplicate namespace or unsupported namespace fails closed.
- Bounded XML parsing with per-schema byte, node, attribute and depth limits. The parser performs no network fetch and never follows `schemaLocation`.
- Schema, import, named element/attribute/type/group declarations and Section 8.2 package parts become deterministic `SourceRecordV1` records with source-bound `xsd_component` locators.
- Anonymous inline types are represented by their owning element/attribute declaration; the extractor does not invent source names for them.
- Raw XML is never emitted. Every record remains `documentation_only` with empty executable parameters.
- Restricted outputs are confined to Git-ignored `implementation/p02/evidence`, using atomic no-overwrite publication.
- Independent verifier recomputes source counts and namespace/package coverage without using the extractor's XML tree, then verifies schema/semantic validity, source identity, contiguous ordinals, unique locators and raw-XML absence.

## Actual locked extraction

| Record kind | Count |
|---|---:|
| package part | 22 |
| schema | 7 |
| import | 5 |
| element | 359 |
| attribute | 648 |
| named complexType | 82 |
| named simpleType | 14 |
| attributeGroup | 7 |
| **Total** | **1,144** |

- Namespaces: `version`, `head`, `section`, `paragraph`, `core`, `master-page` and `history`, all under `http://www.owpml.org/owpml/2024/`.
- Deterministic output: two emissions were byte-identical at 1,321,462 bytes, SHA-256 `c32f323a8fd22f228cc0a116c81881f9ae6c846525c19209142cfe7adcef6ea1`.
- Independent verifier: 1,144 records, namespace coverage 7/7, package part coverage 22/22, errors 0, raw XML published `false`.
- The source SHA-256 before and after extraction remained `c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4`.

The authoritative records remain local at [private OWPML records](evidence/owpml/owpml.records.v1.json). They are not reproduced or committed.

## Validation

- Windows P02 suite: 23/23 passed; compileall and independent actual-output verification passed.
- Official Python 3.13.13 Linux image `sha256:aa938a849bcb82dce8f49480f056ab82bf5c1c3ebc294f0430f37b6820e7f286`, read-only repository mount: 23/23 passed.
- Current repository FULL bootstrap: 5/5 lanes passed; secret findings, vulnerabilities and forbidden licenses 0; CycloneDX components 147.
- Clean clone at `dbad3a7`: FULL bootstrap passed and post-run Git status changes 0.
- Negative coverage: missing appendix, duplicate namespace, `DOCTYPE`/`ENTITY`, residual viewer markup, depth/resource limit, package traversal, source tamper, wrong source kind, restricted-output escape, output traversal and overwrite.

## Preserved boundaries

- The official machine-readable JSON, source archive, installed Hancom files and user documents were not modified or committed.
- 한글/COM/UI was not opened or automated for this task.
- OWPML 2024 namespace metadata does not qualify installed 한글 2020 runtime behavior. Runtime binding remains unverified until P02-06/P02-08.
- 2022/2024, other PCs, production/provider use and redistribution remain outside this current-PC local task.

## Failed checks retained

- Direct XML parsing initially failed for six appendices because the official viewer injected glossary-definition HTML inside schema text. Restricted coordinate inspection identified the exact widget structure; 37 replacements and zero residual HTML are now explicit invariants.
- The first FULL command used a nonexistent `-Mode` parameter and did not start validation. The documented parameterless `tools/bootstrap.ps1` command was then run from the beginning and passed all lanes.

## Next exact task

Implement `P02-05 normalization and duplicate candidates`: consume only source-valid P02 records, normalize label/input/output/scope deterministically, preserve every provenance edge and emit review candidates without automatic merging. Recommended reasoning effort: `xhigh`; P02-06 semantic review and the P02 final Gate: `max`. No user local operation is required at task start.
