# 제품 정의

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 한 문장

자연어 지시를 버전이 고정된 의미 연산으로 컴파일하고, HWPX 직접 편집과 실제 한/글 자동화를 안전하게 조합하여 Web ChatGPT와 Codex에서 동일한 한/글 문서를 생성·편집·검증하는 문서 제작 플랫폼.

## 사용자 가치

- “A3 가로, 여백 12mm, 2단, 표 6×8, 수식은 편집 가능하게”와 같은 요구를 재현 가능한 문서로 변환한다.
- 학교·기관의 복잡한 기존 양식을 훼손하지 않고 필요한 부분만 고친다.
- 작성 결과가 실제 한/글에서 열리고 편집되는지 근거와 함께 확인한다.
- ChatGPT Web에서 시작한 작업을 Codex 로컬 환경에서 이어서 자동화·테스트하고 다시 Web에서 검토한다.
- 지원하지 않는 기능은 이유와 대안을 명확히 표시한다.

## 제품 구성

### 1. Universal Plugin

`skills/`와 등록 원격 MCP 연결을 묶어 ChatGPT와 Codex에 동일한 사용자 기능을 제공한다.

### 2. Remote Document Control Plane

인증, semantic tools, capability planning, job orchestration, project state, artifact storage, audit를 제공한다.

### 3. Direct HWPX Engine

HWPX package parse/write/preserve, schema lowering, deterministic IDs, binary relationship 관리, semantic diff를 담당한다.

### 4. Windows Hancom Worker Pool

한/글 오토메이션, HWP 변환, GUI/desktop 전용 기능, 실제 렌더·저장 oracle을 담당한다.

### 5. Optional WebHWP Adapter

웹한글 기안기 환경이 있는 기관에서 브라우저 기반 편집·API 연계를 제공한다.

### 6. Preview/Diff Widget

페이지 미리보기, 기능 지원 경고, 문서 diff, revision 선택, 작업 상태를 보여 준다. widget은 편집 데이터의 source of truth가 아니다.
