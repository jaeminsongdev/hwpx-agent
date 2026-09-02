# P03-03 Safe XML reader report

- Generated: 2026-09-02
- Audited source commit: `69d75340ee50b650028421ccace30565ada8ad3a`
- State: `pass_current_pc_local_core`
- Reasoning/review mode: `max / untrusted XML boundary`

`hwpx-package`에 재사용 가능한 bounded XML 1.0 reader를 구현하고 P03-02 `PackageGraph`가 같은 계층을 사용하도록 교체했다. 이 계층은 namespace URI 기준 element/attribute identity와 구조 event만 내부에 유지하며 raw XML, resolver, filesystem 또는 network capability를 public API에 노출하지 않는다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Reusable safe XML layer | `pass` | `crates/hwpx-package/src/safe_xml.rs`; `PackageGraph` parser가 동일 layer를 소비 |
| XML 1.0 / UTF-8 envelope | `pass` | declaration 위치·버전·encoding·standalone 순서/값, exactly-one-root, root 밖 whitespace-only 검사 |
| Namespace-aware identity | `pass` | `NsReader` URI resolution, unknown prefix 거부, expanded `(namespace URI, local)` attribute 중복 거부 |
| Entity and resolver policy | `pass` | predefined 5종과 valid numeric scalar만 허용; DTD/custom entity/network/filesystem resolution 불가 |
| Forbidden constructs | `pass` | processing instruction, CDATA, XML 1.1, legacy encoding fail closed |
| Finite resource contract | `pass` | input/event/node/depth/text/total text/attribute/attribute bytes/active namespace binding limits |
| Stable non-sensitive error | `pass` | public `SafeXmlError::code()`; untrusted XML text를 error에 포함하지 않음 |
| Synthetic safety corpus | `pass` | Windows/Linux safe XML `5/5`; bomb/entity/depth/text/attribute/namespace/malformed cases 포함 |
| Regression | `pass` | PackageGraph `8/8`, malicious ZIP `8/8` |
| Versioned contract | `pass` | `implementation/p03/P03-03_SAFE_XML_POLICY.md`, `protocol/migrations/safe-xml-reader-v0-to-v1.md` |

## Dependency boundary

- `quick-xml = 0.42.0` exact pin과 기존 minimal feature set을 그대로 사용했다.
- 새 dependency 또는 async/serialize/arbitrary-encoding/network/resolver feature는 추가하지 않았다.
- parser limit은 reader가 소유하고 construction 시 zero, overflow, 상호 모순을 거부한다.
- public surface는 stable error type만 노출하며 parsed raw text/event model은 crate-internal이다.

## Validation evidence

- Current Windows repository FULL bootstrap: final implementation state에서 `5/5` lanes passed.
- Safe XML corpus: Windows `5/5`; PackageGraph `8/8`; malicious ZIP `8/8`; locked workspace Clippy `-D warnings` passed.
- Official Linux image: `rust@sha256:31ee7fc65186be7e0e0ccb3f2ca305f14e4739e7642a1ae65753aa5d7b874523`; `rustc 1.96.0`, read-only source mount와 tmpfs target에서 safe XML `5/5`, PackageGraph `8/8`, Clippy passed.
- Clean clone: audited commit `69d75340ee50b650028421ccace30565ada8ad3a`, FULL bootstrap `5/5`, exit code 0, post-run tracked changes 0.
- Security: secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 159.
- `unsafe`, filesystem write/extraction, external XML resolution, 사용자 문서 접근, 한글 runtime 실행: 0.

`cargo deny`의 `hashbrown`/`syn` duplicate-version message는 기존 warn policy 안의 dependency graph 경고이며 advisories/licenses/sources/bans 결과는 pass다.

## Strict self-review

- Change risk: `high` (untrusted XML structural boundary).
- Initial finding: P03-02의 narrow XML reader가 graph module에 중복돼 있었고 XML declaration version/order와 expanded attribute identity를 충분히 고정하지 않았다.
- Remediation: 공통 safe reader로 추출하고 XML 1.0 declaration contract, namespace URI resolution, expanded-name duplicate 검사와 active namespace ceiling을 추가했다.
- Compatibility finding: 모든 reference를 일괄 차단하면 정상 metadata의 `&amp;`와 numeric reference까지 깨진다. predefined 5종과 valid XML scalar numeric reference를 allowlist하고 custom named entity는 계속 거부했다.
- Final blocker/major/minor findings: `0/0/0`.

## Scope and remaining boundary

이 task는 synthetic XML/HWPX와 core parser만 검증했다. 실제 사용자 문서, 실제 한글 2020 저장 corpus, byte-span token preservation, writer 또는 한글 round trip은 검증했다고 주장하지 않는다. XML comment는 안전하게 소비하지만 P03-04 전까지 preservation token으로 공개하거나 재작성하지 않는다.

## Next exact task

`P03-04 Preserving tokenizer`를 시작한다. accepted XML 원본의 immutable bytes와 checked byte span, namespace-resolved lightweight token/tree index를 결합하고 untouched serialization이 byte-for-byte 동일함을 Windows/Linux에서 검증한다. 추론수준은 `max`다.
