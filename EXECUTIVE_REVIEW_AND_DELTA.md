# v1 검토 결과와 v2 수정 요약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 판정

v1은 **HWPX 중심 문서 생성기**를 만드는 설계로는 방향이 좋았지만, 사용자가 요구한 **한/글 기능 전반을 능숙하게 사용하는 제품**을 구현하기에는 범위와 추상화가 부족했다. 특히 문서 IR이 문단·표·그림·수식 정도에 머물렀고, 실제 한/글 오토메이션·버전별 기능 바인딩·Windows 운영·라이선스·검토/보안/필드/양식/차트/인쇄·내보내기·외부 서비스·편집기 UI 기능이 빠져 있었다.

## 유지한 결정

- Rust-first 원칙
- HWPX canonical artifact
- native 한컴 수식
- semantic MCP tool surface
- immutable revision과 Web↔Codex 연속성
- preserve-unknown과 실제 한/글 reopen 검증

## 폐기 또는 수정한 결정

| v1 결정 | v2 수정 |
|---|---|
| Python backend MVP를 사실상 주 authoring 경로로 시작 | Rust 패키지 파서·보존 엔진과 capability registry를 먼저 구축하고 Python 라이브러리는 교체 가능한 adapter로만 사용 |
| HWPX backend 두 종류(Python/Rust) | Direct HWPX + Desktop Automation + WebHWP + Oracle의 다중 백엔드 |
| 14개 이하 MCP 도구 | 인위적 개수 제한 폐기. 사용자 목적별 18개 semantic tool과 비공개 internal operations로 분리 |
| 제한된 Document IR | 문서 그래프, 리소스, 스타일, 구역, 컨트롤, 검토, 보안, 접근성까지 표현하는 v2 IR |
| unknown XML 보존 원칙만 제시 | 원본 part byte map, semantic patch, relationship closure, ID allocator, canonical/opaque bag을 포함한 알고리즘으로 구체화 |
| real Hancom 테스트가 후반 | Windows automation/oracle을 중반 핵심 phase로 이동 |
| “모든 기능”의 정의 없음 | 대상 버전별 capability registry 100% disposition을 GA 기준으로 명시 |

## 반드시 수정된 핵심 위험

1. **기능 누락 위험** — 메뉴·오토메이션·HWPX 스키마를 결합한 자동 생성 capability catalog로 통제한다.
2. **렌더링 불일치** — 실제 한/글 worker의 open/save/render/export 결과를 oracle evidence로 기록한다.
3. **오토메이션 불안정성** — 버전별 action binding, timeout, process recycle, desktop session isolation, modal detector를 둔다.
4. **상업 라이선스** — 라이선스 승인을 P00과 production gate에 강제한다.
5. **보안** — 문서 스크립트/OLE/외부 링크/암호 문서는 별도 정책과 격리 경로를 사용한다.
6. **ChatGPT UI 종속성** — MCP Apps 표준을 먼저 사용하고 `window.openai`는 기능 탐지형 확장으로만 사용한다.

## 제품 완료 정의

다음이 모두 충족돼야 “한/글 기능을 능숙하게 사용한다”고 표현할 수 있다.

- 대상 한/글 버전의 메뉴·문서 객체·자동화 기능이 모두 capability registry에 등록됨.
- 모든 capability에 지원 수준, 백엔드, 권한, 위험, 입력 스키마, 테스트, 검증 근거가 있음.
- 문서 크기·여백·구역·다단·머리말/꼬리말·표·수식·그림·도형·차트·필드·주석·참조·검토·보안·인쇄·내보내기 등의 핵심 기능은 실제 한/글에서 성공 검증됨.
- 외부 서비스 또는 GUI 전용 기능은 명시적으로 `OPTIONAL_EXTERNAL` 또는 `AUTOMATION_FULL`로 분류되며, 조용한 대체가 없음.
- Web ChatGPT와 Codex에서 같은 프로젝트 revision을 열고 수정·검증·다운로드할 수 있음.
