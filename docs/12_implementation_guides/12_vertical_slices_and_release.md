# 수직 슬라이스·완료 순서·릴리스 운영

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 개발 원칙

영역별 엔진을 끝까지 따로 만든 뒤 마지막에 합치지 않는다. 각 마일스톤에서 **ChatGPT/Codex request → OperationPlan → backend → HWPX → oracle → revision → preview/download**의 얇은 수직 슬라이스를 완성한다.

## VS-0 Hello HWPX

- 빈 A4 문서, 한 문단, 한 스타일.
- direct package writer, reopen, checksum, revision.
- MCP `document_create`, artifact download.
- 실제 한/글 open evidence.

## VS-1 자유 문서 크기·기본 표·수식

- custom mm/여백/orientation/2단.
- 3×4 표, 병합, border/fill, row split.
- LaTeX 분수/근호/적분을 native equation으로 삽입.
- ChatGPT widget preview와 Codex 재개.

이 슬라이스가 사용자의 필수 요구인 표·문서 크기·수식의 첫 end-to-end gate다.

## VS-2 기존 양식 surgical edit

- 학교 템플릿 분석, fillable slot, unknown XML/asset 보존.
- 제목/문항/표/수식만 수정.
- untouched part byte/token preservation report.
- Hancom save/reopen와 visual diff.

## VS-3 시험지 30문항

- A3/B4/custom profile, 1/2단 혼합.
- 문항 keep, 표/그림/수식, 배점, 정답지 분리.
- page split report와 expected page count.
- 수정 요청 후 같은 project revision 이어가기.

## VS-4 desktop-only 기능

- HWP import/export, 변경 추적, 차트, 필드 갱신, PDF export.
- target binding, worker crash/modal/retry.
- no partial commit와 loss report.

## VS-5 전 기능 catalog/GA

- target build official/runtime item 100% disposition.
- core capability green threshold 및 non-core explicit classifications.
- security/fuzz/performance/DR.
- Web/Codex packaging/submission.

## Definition of Done

기능 하나는 다음이 있을 때만 완료다.

- semantic contract와 generated types.
- permission/risk/fallback/degradation.
- direct 또는 target-bound automation implementation.
- normal/boundary/negative/preservation/security fixture.
- semantic readback.
- 요구된 Hancom/render/export evidence.
- docs, registry, release report 갱신.

## release train

- target build profile별 독립 channel.
- canary tenant와 synthetic corpus 우선.
- binding/compiler/schema 변경은 관련 evidence invalidation.
- rollback은 service version뿐 아니라 capability registry, Windows image, binding bundle, widget resource URI를 함께 되돌린다.
- deprecated capability는 최소 한 release의 warning/migration을 제공하되 보안상 즉시 disable은 예외다.
