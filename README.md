# HWPX Agent Product Design v2 — ChatGPT Web·Codex 공용 한컴 문서 제작 플러그인

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


> 본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.

이 문서 세트는 Web ChatGPT와 Codex에서 동일한 프로젝트를 이어 가며 **한/글 문서를 생성·편집·검증·변환**하는 제품을 구현하기 위한 기준 설계다. 업로드된 v1 설계의 장점은 유지하되, “표·문서 크기·수식뿐 아니라 한/글의 전체 기능을 능숙하게 사용”한다는 목표에 맞춰 제품의 범위와 아키텍처를 전면 확장했다.

## 최종 결론

단일 HWPX 라이브러리만으로는 완전한 기능 대응과 실제 한/글 렌더링 충실도를 동시에 보장할 수 없다. v2는 다음의 **기능 기반 다중 백엔드**를 사용한다.

1. `DirectHWPXBackend` — Rust 기반 HWPX 패키지 파서·보존 편집기·작성기.
2. `HancomDesktopAutomationBackend` — 격리된 Windows 워커에서 한/글 오토메이션을 실행하는 완전 기능 경로.
3. `WebHWPBackend` — 웹한글 기안기 라이선스와 배포 환경이 있을 때 사용하는 선택 백엔드.
4. `HancomOracleBackend` — 실제 한/글 열기·저장·렌더·인쇄·내보내기 검증 경로.
5. `CapabilityRouter` — 기능, 문서 상태, 대상 한/글 버전, 보존 수준, 보안 정책에 따라 백엔드를 선택한다.

HWPX는 canonical artifact로 유지하지만, 내부 source of truth는 `DocumentGraph IR + OperationPlan + immutable revision`이다. `.hwp`는 직접 바이너리 생성보다 공식/자동화 변환 경로를 우선한다.

## “모든 기능”의 정의

“모든 기능”은 막연한 표현으로 두지 않는다. 지원 대상 한/글 버전별로 기능 목록을 고정하고, 각 기능을 `DIRECT_FULL`, `AUTOMATION_FULL`, `HYBRID`, `READ_ONLY`, `PRESERVE_ONLY`, `OPTIONAL_EXTERNAL`, `DISABLED_BY_POLICY`, `UNSUPPORTED` 중 하나로 분류한다. GA 시점에는 대상 버전의 모든 기능이 `FEATURE_COVERAGE_MATRIX.csv`에 한 번 이상 등장하고, 구현 경로·테스트·제약·근거가 비어 있지 않아야 한다.

## 반드시 먼저 읽을 순서

1. `00_START_HERE.md`
2. `EXECUTIVE_REVIEW_AND_DELTA.md`
3. `docs/00_review/01_executive_review.md`
4. `docs/02_architecture/01_system_architecture.md`
5. `docs/02_architecture/02_capability_routing.md`
6. `docs/03_document_model/01_document_graph_ir.md`
7. `docs/03_document_model/11_operation_plan.md`
8. `FEATURE_COVERAGE_MATRIX.md`
9. `docs/09_roadmap/00_master_roadmap.md`
10. `IMPLEMENTATION_PLAYBOOK.md`

## 설계의 절대 원칙

- LLM이 HWPX XML 또는 오토메이션 action 이름을 임의로 생성하지 않는다.
- 공개 MCP 계약에는 메뉴명·COM 세부 이름 대신 안정된 semantic operation을 노출한다.
- 모든 mutation은 dry-run, capability plan, expected revision, idempotency key, atomic commit을 갖는다.
- 원본 템플릿과 입력 문서는 immutable이다. 결과는 새 revision으로 저장한다.
- 지원하지 않는 기능을 이미지·텍스트·근삿값으로 조용히 대체하지 않는다.
- 실제 한/글 검증을 수행하지 못한 결과는 `verified`로 표시하지 않는다.
- 오토메이션 상업 이용·서버 배포는 한컴 라이선스 승인을 확인하기 전 production gate를 통과할 수 없다.
- 문서에 포함된 스크립트·OLE·외부 링크는 기본적으로 실행하지 않고 보존 또는 격리한다.
- ChatGPT Web과 Codex의 영속 상태는 서버가 소유하며 widget/local cache는 source of truth가 아니다.

## 산출물 구성

- `FEATURE_COVERAGE_MATRIX.csv`: 기능별 구현·검증·로드맵 매핑 원본.
- `WORK_BREAKDOWN_STRUCTURE.csv`: P00~P20의 190개 실행 작업.
- `FEATURE_COVERAGE_MATRIX.md`: 사람이 읽기 쉬운 요약.
- `IMPLEMENTATION_PLAYBOOK.md`: 구현자가 따라갈 통합 절차.
- `docs/`: 제품·아키텍처·IR·백엔드·MCP·앱·테스트·운영 상세.
- `specs/`: 구현 계약용 JSON Schema와 609개 generated capability contract.
- `decisions/`: 변경 불가능한 핵심 설계 결정.
- `skills/`: ChatGPT/Codex 플러그인 워크플로 초안.
- `templates/`: ADR, 핸드오프, 테스트 기록, 기능 바인딩 기록 템플릿.
