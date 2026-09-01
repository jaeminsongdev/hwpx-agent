# START HERE — 새 ChatGPT/Codex/개발 세션 진입점

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 세션 시작 순서

1. `CURRENT_STATE.md`와 `ROADMAP_STATUS.yaml`을 읽는다.
2. `IMPLEMENTATION_PLAYBOOK.md`와 현재 phase 문서, 직전 handoff를 읽는다.
3. `WORK_BREAKDOWN_STRUCTURE.csv`에서 현재 task를 확인한다.
4. `FEATURE_COVERAGE_MATRIX.csv`에서 해당 기능의 `support_level`, `preferred_backend`, `phase`, `validation`을 확인한다.
5. 관련 JSON Schema를 확인하고 테스트부터 추가한다.
6. 구현 전에 `CapabilityPlan`을 만든다. action 이름이나 XML 태그를 코드에 바로 박지 않는다.
7. 구현·테스트·문서·capability registry를 같은 커밋에서 갱신한다.
8. 세션 종료 시 `templates/HANDOFF.md` 형식으로 기록하고 `CURRENT_STATE.md`를 갱신한다.

## 고정 결정

- Rust control plane + Rust direct HWPX engine.
- Windows 한/글 오토메이션 워커를 정식 백엔드로 포함.
- HWPX canonical, `.hwp`는 변환/자동화 경로.
- native 한컴 수식 필수.
- semantic MCP tools + 상세 `OperationPlan`.
- remote project state canonical.
- 버전별 capability registry와 실제 한/글 oracle suite 필수.
- 공개 Web/Codex 플러그인은 등록된 원격 MCP 연결을 사용하고, Codex 로컬 패키지는 선택적으로 `.mcp.json` local bridge를 추가.

## 금지 사항

- 채팅 기록만 보고 이전 상태를 추정하지 않는다.
- 임의 COM action 문자열을 LLM 출력에서 직접 실행하지 않는다.
- 사용자 파일을 in-place로 수정하지 않는다.
- 서명·암호·배포용 문서·개인정보 보호를 우회하지 않는다.
- 문서 스크립트나 OLE를 자동 실행하지 않는다.
- 검증되지 않은 렌더를 “한/글과 동일”이라고 보고하지 않는다.
- HWPX에 저장되지 않는 편집기 보기 설정을 문서 기능이라고 혼동하지 않는다.

## 한 줄 재개 규칙

`CURRENT_STATE.md → ROADMAP_STATUS.yaml → 직전 handoff → 현재 phase 문서 → 관련 capability rows → 테스트` 순서로 재개한다.
