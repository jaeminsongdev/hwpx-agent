# P03-04 Preserving XML tokenizer report

- Generated: 2026-09-02
- Audited source commit: `631bba14c13a4de456a81f67bea8a8d305d317cd`
- State: `pass_current_pc_local_core`
- Reasoning/review mode: `max / byte-preservation and untrusted XML boundary`

`hwpx-package`에 P03-03 safe XML 결과를 소비하는 exact-source token/span model과 namespace-aware lightweight element index를 구현했다. 원본은 validation 이후 private immutable buffer에만 보관되고 public API에는 checked span, 구조 token, namespace identity, tree index, 길이와 SHA-256만 노출된다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Checked source coordinates | `pass` | half-open UTF-8-boundary spans, ordered/non-overlap/gap-free token coverage, invalid/order/overflow rejection |
| Exact lexical preservation | `pass` | BOM, declaration, start/end/empty, text, XML whitespace, reference spelling, comment, attribute order/quote/value spans |
| Namespace-aware names | `pass` | original QName/prefix/local plus resolved URI; default/unprefixed attribute rules, reserved `xml`, `xmlns`, descendant rebinding |
| Lightweight tree/index | `pass` | matching start/end, outer/content spans, parent, first/last child, previous/next sibling, empty identity |
| Untouched equality | `pass` | internal token-slice reconstruction, byte-for-byte and SHA-256 equality; normalization/re-encoding 0 |
| Raw-data boundary | `pass` | source/text/attribute/comment bytes private; public untouched verifier returns no bytes; custom summary-only `Debug` |
| Safe parser inheritance | `pass` | P03-03 DTD/entity/PI/CDATA/encoding/namespace/limit rejection and stable codes preserved |
| Synthetic corpus | `pass` | P03-04 `7/7`; P03-03 `5/5`; PackageGraph `8/8`; malicious ZIP `8/8` |
| Versioned contract | `pass` | `implementation/p03/P03-04_PRESERVING_XML_POLICY.md`, `protocol/migrations/preserving-xml-token-v0-to-v1.md` |

## Public and private boundary

- Public: `PreservingXmlDocument`, safe structural token/name/span/tree metadata, source length/SHA-256, `verify_untouched_round_trip()`, stable `PreservingXmlError::code()`.
- Private: source bytes, text/reference/comment content, attribute values, token serializer, safe reader limits/events, arbitrary rewrite operations.
- No raw XML returning method, resolver, filesystem, network, process, writer or patch capability was introduced.
- Safe events gained parallel source spans and ordered attribute-name metadata so P03-04 does not perform a second semantic XML parse. Existing PackageGraph v1 failure mapping remains unchanged.

## Validation evidence

- Current Windows exact commit: FULL bootstrap `5/5`; Rust workspace tests/Clippy/doc tests/generated drift, Windows worker, widget, docs and security passed.
- Core corpus: preserving XML `7/7`, safe XML `5/5`, PackageGraph `8/8`, malicious ZIP `8/8`; failures 0.
- Linux exact toolchain: image `rust@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc`, `rustc 1.96.0`; source and Cargo registry read-only, Cargo offline, target tmpfs; whole `hwpx-package` `28/28` and Clippy `-D warnings` passed. Clippy component was installed only inside the disposable container.
- Clean clone: audited commit `631bba14c13a4de456a81f67bea8a8d305d317cd`, FULL bootstrap `5/5`, exit code 0, post-run tracked changes 0.
- Security: scanned files 475, secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 159.
- `unsafe`, filesystem write/extraction, external XML resolution, 사용자 문서 접근, 한글 runtime 실행: 0.

`cargo deny`의 기존 duplicate-version warning은 advisory/license/source/ban failure가 아니다. 초기 Linux preflight의 mount quoting, slim-image toolchain/cache/component 문제는 product code 실행 전 환경 설정 실패였으며, exact 1.96.0 image의 최종 lane으로 대체했다.

## Strict self-review

- Change risk: `high` (untrusted input coordinates and lossless reconstruction).
- Finding 1: `quick-xml`은 UTF-8 BOM을 소비한 뒤 offset을 BOM 이후 좌표로 보고했다. 모든 safe span을 원본 좌표로 3바이트 보정하고 BOM을 별도 token으로 고정했다.
- Finding 2: derived `Debug`는 private source bytes를 출력할 수 있었다. length/digest/count/root만 표시하는 custom `Debug`로 교체하고 raw content non-disclosure test를 추가했다.
- Finding 3: root 밖 text가 Rust의 넓은 Unicode whitespace 판정을 사용했다. XML 공백 4종만 허용하도록 교정하고 NBSP negative case를 추가했다.
- Finding 4: parser/build 함수가 길어 감사성이 낮았다. safe output과 preserving build state로 분리하고 Clippy 예외 확대 없이 통과시켰다.
- Final blocker/major/minor findings: `0/0/0`.

## Scope and remaining boundary

이 task는 synthetic XML과 core token model만 검증했다. 실제 HWPX 전체 part classification, patch, modified XML serialization, ZIP write, 사용자 문서 또는 한글 2020 round trip은 검증했다고 주장하지 않는다.

## Next exact task

`P03-05 Part preservation map`을 시작한다. closed `PackageGraph`의 모든 part를 raw identity와 media policy에 결합해 `ByteExact/TokenStable/Semantic/Regenerated/Opaque/Rejected` 중 근거 있는 등급만 결정하고, unknown/unsafe part가 silently downgraded되지 않는 known-fixture expected map을 검증한다. 추론수준은 `max`다.
