# P03-05 Part preservation map report

- Generated: 2026-09-02
- Audited source commit: `61dc97865b38c653efabe509077fead2ac254a3f`
- State: `pass_current_pc_local_core`
- Reasoning/review mode: `max / untrusted package evidence and preservation classification boundary`

`hwpx-package`에 closed `PackageGraph`의 모든 non-directory part를 bounded reader로 다시 읽고, 권위 그래프·크기·SHA-256 identity를 검증한 뒤 근거 있는 보존 등급만 부여하는 `PreservationReport`를 구현했다. 보고서는 canonical package path 순서로 결정적이며 raw part/XML 내용은 공개하지 않는다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Complete deterministic map | `pass` | 모든 non-directory part를 exactly once 포함, portable collision key 중복/누락/초과 거부, canonical path 정렬 |
| Authoritative trust boundary | `pass` | 동일 bounded reader에서 `PackageGraph` 재구축, supplied public graph의 document/relationship/spine/path/media/role/size 재검증 |
| Raw identity readback | `pass` | 각 part 재읽기 후 expanded size와 SHA-256 일치 필수, drift는 partial report 없이 hard failure |
| Evidence-ranked classes | `pass` | `ByteExact`, `TokenStable`, `Opaque`, `Rejected`만 v1 근거로 자동 부여; `Semantic`/`Regenerated` 자동 승격 0 |
| XML/media fail closed | `pass` | path/media 불일치, XML smuggling, DTD/entity 및 supported binary signature mismatch를 `Rejected`로 유지 |
| Preservation evidence | `pass` | source ZIP index/compression/size/CRC32, part SHA-256, class/reason, 비민감 token/element count와 untouched verification |
| Readiness boundary | `pass` | `Rejected > 0`이면 `direct_preserve_ready=false`; writer 존재나 round trip 완료로 해석하지 않음 |
| Non-disclosure | `pass` | part bytes, XML text, attribute/comment/entity value, filesystem path, resolver capability 미노출 |
| Synthetic corpus | `pass` | preservation map `5/5`; preserving XML `7/7`; safe XML `5/5`; PackageGraph `8/8`; malicious ZIP `8/8` |
| Versioned contract | `pass` | `implementation/p03/P03-05_PRESERVATION_MAP_POLICY.md`, `protocol/migrations/preservation-report-v0-to-v1.md` |

## Public and private boundary

- Public: `PreservationReport`, deterministic part records/counts, stable classes/reason codes, package identity metadata, hashes and non-sensitive token evidence.
- Private: re-read part buffers, original XML bytes and values, signature inspection bytes, token model source buffer.
- Unknown non-XML media is `Opaque` only: future byte-copy inventory이며 semantic validity나 writer support를 뜻하지 않는다.
- Unsafe XML is a complete `Rejected` record so 다른 part evidence를 숨기지 않지만 direct-preserve readiness는 차단한다.
- Supplied graph order는 신뢰하지 않으며, public graph 필드 변조도 권위 재구축 또는 raw readback 비교에서 실패한다.

## Validation evidence

- Current Windows exact commit: FULL bootstrap `5/5`; Rust workspace tests/Clippy/doc tests/generated drift, Windows worker, widget, docs and security passed.
- Core corpus: preservation map `5/5`, preserving XML `7/7`, safe XML `5/5`, PackageGraph `8/8`, malicious ZIP `8/8`; whole `hwpx-package` `33/33`.
- Linux exact toolchain: image `rust@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc`, `rustc 1.96.0`; source/Cargo registry read-only, Cargo offline, target tmpfs; `hwpx-package` `33/33` and Clippy `-D warnings` passed. Clippy component installation은 disposable container 내부에 한정했다.
- Clean clone: `D:\개발데이터\Temp\hwpx-agent-p03-05-clean-61dc978`, exact audited commit, FULL bootstrap `5/5`, exit code 0, post-run tracked changes 0.
- Security: scanned files 480, secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 159.
- `unsafe`, filesystem write/extraction, external XML resolution, 사용자 문서 접근, 한글 runtime 실행: 0.

`cargo deny`의 기존 duplicate-version warning은 advisory/license/source/ban failure가 아니다.

## Strict self-review

- Change risk: `high` (untrusted package evidence and future writer policy input).
- Caller-controlled `PackageGraph`를 권위 입력으로 오인하지 않도록 동일 reader에서 재구축하고 semantic snapshot을 대조한다.
- `Opaque` unknown media를 `Semantic`으로 승격하지 않는 negative fixture와 XML/media/signature contradiction rejection을 고정했다.
- source order/compression evidence를 잃지 않도록 canonical report order와 별개로 source entry index/compression/CRC32를 기록한다.
- Derived diagnostics가 raw malicious XML을 포함하지 않는지 DTD fixture의 secret marker로 검사했다.
- Final blocker/major/minor findings: `0/0/0`.

## Scope and remaining boundary

이 task는 synthetic HWPX package와 core classification만 검증했다. 실제 사용자 HWPX의 등급 맵, ID/reference semantics, patch, modified XML serialization, ZIP write, 한글 2020 round trip 또는 다른 한글 버전 동작은 검증했다고 주장하지 않는다.

## Next exact task

`P03-06 ID/reference index`를 시작한다. token-stable XML part의 part-scoped ID namespace와 명시적으로 지원하는 cross-part reference 규칙만 typed index로 만들고, duplicate/dangling/wrong-type를 deterministic fail-closed diagnostics로 검출한다. 기존 ID는 재번호화하지 않으며 아직 ID allocation이나 patch를 구현했다고 주장하지 않는다. 추론수준은 `max`다.
