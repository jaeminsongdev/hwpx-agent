# P03-06 ID/reference index report

- Generated: 2026-09-02
- Audited source commit: `c70479c62f4ac87e8527b6b12b0c18b7975808d6`
- State: `pass_current_pc_local_core_and_disposable_2020`
- Reasoning/review mode: `max / typed reference integrity and private document-value boundary`

`hwpx-package`에 P03-05 `TokenStable` XML만 재검증해 part-scoped typed declaration/reference를 결정적으로 색인하는 `IdIndex`를 구현했다. v1 규칙은 현재 PC의 정품 한글 2020 HWPML 2011 core QName에 한정되며, ID 값·XML·문서 경로는 public record나 진단 출력에 노출하지 않는다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Trust chain | `pass` | bounded reader에서 `PreservationReport`를 재구축하고 `TokenStable` part SHA-256 일치 후에만 색인; rejected/opaque/non-token-stable part 해석 금지 |
| Typed identity | `pass` | identity를 `(part collision key, IdKind, normalized private value)`로 고정; 같은 값의 다른 part/type 공존 허용 |
| Versioned rule profile | `pass` | `hancom-2020-hwpml-2011-core/v1`; OPF 및 현재 2020 header/paragraph declaration·reference QName allowlist |
| Complete resolution | `pass` | duplicate declaration, dangling reference, wrong-type target, malformed/unknown ID-like shape를 stable code로 분리하고 partial-valid index를 반환하지 않음 |
| Field semantics | `pass` | 현재 2020의 empty optional metadata, paragraph unassigned zero, no-target zero/u32-max sentinel을 정확한 field별로만 적용 |
| Cross-part target | `pass` | v1 HWPML resource reference는 고정 canonical `Contents/header.xml`; missing/non-token-stable target fail closed |
| Finite limits | `pass` | part/declaration/reference/issue/value 길이의 nonzero checked ceiling과 allocation failure 경로 |
| Non-disclosure | `pass` | semantic value는 private; custom `Debug`는 길이만 노출; diagnostic은 fixture ordinal/profile/aggregate/stable code만 출력 |
| Synthetic corpus | `pass` | ID index `5/5`; preserving XML `12/12` unit; PackageGraph `8/8`; preservation map `5/5`; malicious ZIP `8/8`; package 전체 `38/38` |
| Current 2020 disposable evidence | `pass` | 승인된 기존 fixture 2개가 각각 `8 parts / 73 declarations / 184 references / 0 issues` |
| Versioned contract | `pass` | `implementation/p03/P03-06_ID_REFERENCE_POLICY.md`, `protocol/migrations/id-reference-index-v0-to-v1.md` |

## Current-2020 compatibility repairs

현재 PC의 이미 승인된 disposable 한글 2020 산출물을 read-only 진단하면서 다음 차이를 발견해 synthetic regression으로 고정했다.

- OPF namespace의 표준 URI와 현재 2020 trailing-slash URI만 정확히 허용하고 유사 URI는 거부한다.
- `container.xml`의 여러 rootfile 중 정확히 하나의 HWPX package root를 선택하고 ancillary root target도 검증한다.
- manifest href가 package-root-relative 또는 OPF-source-relative인 현재 2020 변형을 actual entry closure로 판정하며, 둘 다 서로 다른 entry에 맞으면 ambiguous로 거부한다.
- 고정 preview infrastructure `Preview/PrvImage.png`와 current media type은 허용하되 임의 orphan part는 계속 거부한다.
- font ID는 한글/라틴/한자/일본어/기타/기호/사용자 7개 언어 domain을 분리한다.
- 현재 2020의 field별 zero/u32-max sentinel과 empty optional metadata를 일반 규칙으로 확대하지 않고 정확한 QName 규칙으로만 처리한다.

## Validation evidence

- Current Windows exact commit: FULL bootstrap `5/5`; Rust workspace tests/Clippy/doc tests/generated drift, Windows worker, widget, docs and security passed.
- Actual disposable diagnostic: 명시한 기존 current-2020 fixture 2개 read-only, 각 `8/73/184`, issue 0; 한글/COM/UI를 이 task에서 실행하지 않았다.
- Linux exact toolchain: image `rust:1.96.0-bookworm@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc`, `rustc 1.96.0`; source/Cargo registry read-only, Cargo offline, target tmpfs; `hwpx-package` `38/38`와 Clippy `-D warnings` passed.
- Clean clone: `D:\개발데이터\Temp\hwpx-agent-p03-06-clean-c70479c`, exact audited commit, FULL bootstrap `5/5`, exit code 0, post-run tracked changes 0.
- Security: scanned files 486, secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 159.
- Library filesystem/network/process/`unsafe`, 사용자 문서 접근·수정, 한글 runtime 실행: 0. Diagnostic example만 명시 입력 파일을 read-only로 읽는다.

`cargo deny`의 기존 duplicate-version warning은 advisory/license/source/ban failure가 아니다.

## Strict self-review

- Change risk: `high` (typed references become an input to future mutation and allocation).
- 실제 2020 evidence가 드러낸 container/OPF/manifest/preview/font/sentinel 차이를 allow-all로 풀지 않고 exact allowlist, actual-entry closure, ambiguity rejection, field-specific 규칙으로 고정했다.
- 공개 record와 `Debug`가 raw document-derived ID를 노출하지 않는지 secret marker fixture로 검증했다.
- invalid input에서는 issues가 있더라도 valid `IdIndex`를 반환하지 않아 downstream patch가 불완전 색인을 신뢰할 수 없다.
- Final blocker/major/minor findings: `0/0/0`.

## Scope and remaining boundary

이 task는 현재 PC의 exact 한글 2020 core profile과 이미 승인된 disposable fixture만 검증했다. 사용자 문서 전체, 모든 HWPML ID 문법, ID allocation, XML patch/serialization, ZIP write, 한글 round trip 또는 2022/2024 동작은 검증했다고 주장하지 않는다.

## Next exact task

`P03-07 preserving patch engine`을 시작한다. 제한된 `PatchIntent`를 checked source span과 typed ID index 위에서 transaction으로 계획하고, overlap/nesting/ambiguous dependency는 자동 순서 추정 없이 conflict로 실패시킨다. untouched byte equality, rollback, deterministic property/random patch corpus를 검증하며 아직 ZIP publication을 주장하지 않는다. 추론수준은 `max`다.
