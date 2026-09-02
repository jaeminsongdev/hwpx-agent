# P04-01 DocumentGraph v2 types report

- Generated: 2026-09-02
- Audited source commit: `0408d8f19592641e8737544ea35377265f444a1b`
- State: `pass_current_pc_local_pure_model`
- Reasoning/review mode: `max / untrusted graph identity, canonical bytes and finite admission`

`domain-ir`에 backend-neutral `DocumentGraph` v2 draft/validated type 경계를 구현했다. 문서,
source profile, metadata/settings/security/accessibility, resource/style catalogs, sections/flow,
notes/references/review, source anchor와 opaque preservation을 typed field로 표현한다. ZIP, XML,
COM, HAction, 한글 runtime 또는 사용자 문서는 이 task에서 사용하지 않았다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Pure typed boundary | `pass` | `#![forbid(unsafe_code)]`; filesystem/network/process/backend dependency 0 |
| Required graph coverage | `pass` | 9 node kinds, inline/review/reference/note, resource/style, security/accessibility, opaque handle |
| Validated publication | `pass` | mutable `DocumentGraphDraft` -> finite fail-closed validation -> immutable serializable `DocumentGraph` |
| Identity and closure | `pass` | global logical/source-anchor uniqueness; typed node/resource/style/reference/review/opaque closure |
| Table shape | `pass` | checked dimensions/capacity/spans, exact grid coverage and overlap rejection |
| Finite bounds | `pass` | top-level preflight, serialized bytes, node/inline/edge/property/cell counts, string bytes and depth ceiling |
| Deterministic bytes | `pass` | canonical catalog order, `BTreeMap`, compact JSON, round-trip byte equality |
| Cross-platform golden | `pass` | Windows/Linux digest `2ab9ffef0263e14609afa148e412ba2915820e54e365c9a420c734f908a6f3c6` |
| Privacy | `pass` | Debug/error body/path/formula/ID/opaque redaction negative test |
| Version/migration | `pass` | `P04-01_DOCUMENT_GRAPH_POLICY.md`, `document-graph-v1-to-v2.md`, wrong-version fail closed |

The design schema remains a vocabulary input, not a permissive runtime validator. Canonical JSON
uses the design top-level names `resource_catalog`, `style_catalog` and `artifact_ref`; the Rust
validator is the current executable authority. A future public generated wire schema requires its
own Gate and cannot weaken this contract.

## Validation evidence

- Windows Rust 1.96.0: `domain-ir` `9/9`, doc tests, Clippy `-D warnings` passed.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`,
  network off, source/registry read-only, Cargo offline, executable tmpfs; `9/9` and Clippy passed.
- Current checkout FULL bootstrap: `5/5` lanes passed.
- Exact implementation commit clean clone FULL bootstrap: `5/5` lanes passed; post-run Git changes 0.
- Current security: 516 files scanned, secrets/vulnerabilities/forbidden licenses 0, SBOM 271 components.
- Clean-clone security: secrets/vulnerabilities/forbidden licenses 0, SBOM 229 components.
- Generated artifact drift, design validation, C# worker and TypeScript widget regressions all passed.

The first read-only Linux command failed before compilation because `rustup` attempted to write its
own read-only temporary directory. The authoritative rerun mounted only that toolchain temp path as
`tmpfs` while preserving network-off and read-only source/registry conditions.

## Strict self-review and remediations

- Change risk: `high` because future planner/transaction layers will trust graph identity and bytes.
- Top-level design wire names initially differed from Rust field names; explicit serde names and
  golden assertions fixed the drift.
- Table validation initially checked only cell anchors, not merged-span overlap/full coverage;
  expanded-grid validation and a negative fixture fixed it.
- Programmatic drafts initially reached catalog sort/reference collection before serialized-size
  admission; top-level/count preflight and non-retaining bounded serialization now run first.
- Nested properties, inline count, edge count, source-anchor uniqueness and native opaque closure
  received explicit finite/negative coverage.
- Derived identifier deserialization initially bypassed smart constructors; custom validated
  `Deserialize` implementations and invalid-JSON ID tests closed the bypass.
- Final blocker/major/minor findings after remediation: `0/0/0`.

The single Clippy suppression is limited to one comprehensive synthetic fixture builder
(`too_many_lines`); product code has no lint suppression.

## Scope and remaining boundary

P04-01 proves a pure synthetic graph contract, not HWPX lowering/lifting, source-ID stability across
real save cycles, public API schema compatibility, large real-document performance, visual fidelity
or a Hancom runtime operation. No user source was opened or modified. 2022/2024 and other PCs remain
deferred and are not blockers for the current-PC P04 sequence.

## Next exact task

Start `P04-02 Unit and ID model` with reasoning effort `high`. Implement checked mm/pt/HWPUNIT
conversion, explicit rounding, coordinate spaces, logical/source/revision identity and deterministic
property tests before selector compilation. P04 final Gate remains `max`. No user local operation is
required for P04-02.
