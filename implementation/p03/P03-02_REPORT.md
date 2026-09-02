# P03-02 PackageGraph report

- Generated: 2026-09-02
- Audited source commit: `504f05cd2e0a915ebc480ae0f0bab87d2f15387d`
- State: `pass_current_pc_local_core`
- Reasoning/review mode: `max / untrusted package metadata boundary`

`hwpx-package`에 exact HWPX infrastructure 검사, namespace-resolved OCF container/OPF parser, source-relative relationship resolution, closed part graph와 stable typed error contract를 구현했다. 모든 non-directory part는 P03-01 integrity read를 통과한 뒤 SHA-256을 기록하며, 관계 closure와 orphan 검사가 끝나기 전에는 graph를 반환하지 않는다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Typed public graph/error/limit contract | `pass` | `PackageGraph`, `PartRecord`, `Relationship`, `MediaType`, roles/kinds, validated limits, `GraphError::code()` |
| HWPX infrastructure | `pass` | exact first/stored `application/hwp+zip`, required `version.xml`/container, one declared existing rootfile |
| Container and OPF parse | `pass` | OCF/OPF namespace-resolved container, manifest, spine with all quick-xml reader checks enabled |
| Internal relationship resolution | `pass` | UTF-8 percent decoding, source-relative normalization, portable collision key, package-root containment |
| Closed part graph | `pass` | unique manifest ID/normalized target, existing non-directory target, spine closure, unlisted/orphan rejection |
| External/entity/network policy | `pass` | external scheme/network path blocked; DTD/custom entity/PI/CDATA blocked; no resolver or I/O API |
| Bounded metadata | `pass` | byte/event/depth/attribute/attribute-byte/namespace-binding/relationship/media-type ceilings |
| Raw part integrity identity | `pass` | every part reuses P03-01 streamed size/CRC/nesting validation and stores SHA-256 only after success |
| Synthetic positive/negative corpus | `pass` | Windows/Linux 8/8 groups including missing/duplicate/dangling/orphan/external/escape/namespace/entity/limit cases |
| Initial contract migration | `pass` | `protocol/migrations/package-graph-v0-to-v1.md` |

Detailed acceptance and future compatibility rules are authoritative in `implementation/p03/P03-02_PACKAGE_GRAPH_POLICY.md`.

## Dependency boundary

- `quick-xml = 0.42.0` exact pin, default features disabled.
- No serialize, arbitrary encoding, async, network or external entity resolver feature is enabled.
- Namespace resolution uses `NsReader` with all checks and an explicit active-binding ceiling.
- Existing `sha2 = 0.11.0` supplies part identity only; graph construction does not publish or persist raw bytes.

## Validation evidence

- Current Windows repository FULL bootstrap: `5/5` lanes passed after the final code state.
- Rust workspace: format, locked workspace Clippy `-D warnings`, tests, doc tests and generated-artifact drift passed.
- P03-02 synthetic graph corpus: Windows `8/8`, failures 0; P03-01 malicious ZIP regression `8/8`, failures 0.
- Official Linux image: `rust@sha256:31ee7fc65186be7e0e0ccb3f2ca305f14e4739e7642a1ae65753aa5d7b874523`; `rustc 1.96.0`, source read-only mount, tmpfs target, graph `8/8` and Clippy passed.
- Clean clone: audited commit `504f05cd2e0a915ebc480ae0f0bab87d2f15387d`, FULL bootstrap `5/5`, post-run Git status changes 0.
- Security: secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 159.
- `unsafe`, filesystem extraction/write, external XML resolution, user document access and 한글 runtime execution: 0.

`cargo deny`의 `hashbrown`/`syn` duplicate-version messages는 기존 warn policy 안의 dependency graph 경고이며 advisories/licenses/sources/bans 결과는 pass다.

## Strict self-review

- Change risk: `high` (untrusted package/XML relationship boundary).
- Initial findings: caller가 ZIP과 다른 path limit을 중복 전달할 수 있었고, container rootfile media type이 graph에서 소실됐으며, literal prefix 비교는 descendant namespace rebinding을 안전하게 판별하지 못했다.
- Remediation: reader-owned validated limits만 재사용하고 declared rootfile media type을 보존했으며, bounded `NsReader` URI resolution과 prefix-rebinding negative test로 교체했다.
- Compatibility finding: 모든 general reference 거부는 정상 OPF metadata의 `&amp;`/numeric reference도 막았다. XML predefined 5종과 valid numeric scalar만 allowlist하고 custom entity는 계속 거부했다.
- Final blocker/major/minor findings: `0/0/0`.

## Scope and remaining boundary

이 task는 locked standard contract와 synthetic HWPX package만 검증했다. 실제 사용자 문서, 실제 한글 2020 저장 HWPX corpus, generic XML token preservation, writer 또는 한글 round trip은 검증했다고 주장하지 않는다. P03-01의 embedded archive/HWPX rejection도 그대로 유지된다.

## Next exact task

`P03-03 XML safety parser`를 시작한다. P03-02의 narrow parser 안전 규칙을 reusable internal safe XML layer로 추출하고 DTD/custom entity/network off, namespace URI resolution, depth/event/text/attribute limit과 XML bomb/invalid namespace corpus를 Windows/Linux에서 검증한다. 추론수준은 `max`다.
