# 전체 시스템 아키텍처

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


```text
ChatGPT Web ───────┐
                   │  Universal plugin: skills + registered remote MCP app
Codex remote ──────┤
                   ▼
             HTTPS /mcp Gateway
                   │
        AuthN/AuthZ · Rate limit · Audit
                   │
          Rust Document Control Plane
  ┌────────────────┼─────────────────────────────┐
  │ Intent compiler│ Capability planner/router   │
  │ DocumentGraph  │ Operation transaction       │
  │ Project state  │ Validation/evidence         │
  └───────────────┬┴─────────────────────────────┘
                  │ Job DAG
       ┌──────────┼───────────┬─────────────┐
       ▼          ▼           ▼             ▼
 Direct HWPX   Windows      WebHWP       Oracle/Render
 Rust engine   Hancom pool  adapter      workers
       └──────────┴───────────┴─────────────┘
                  │
        Object Storage + PostgreSQL
                  │
          Revision DAG + Evidence

Codex local companion
  ├─ same remote MCP
  └─ optional local .mcp.json → local bridge → installed Hancom
```

## 계층 책임

### Plugin/Skill

사용자 intent를 유도하고 올바른 도구 순서, 확인 질문, 결과 표현을 정의한다. 파일 포맷과 action binding을 모른다.

### MCP Gateway

표준 tool contract, auth, schema validation, request id, idempotency, streaming job 상태를 제공한다.

### Control Plane

DocumentGraph IR, OperationPlan, capability resolution, transaction, policy, project/revision, evidence를 소유한다.

### Backend

실제 HWPX 패키지 또는 한/글 응용 프로그램을 조작한다. 모든 backend는 같은 `BackendExecutionRequest/Receipt` 계약을 구현한다.

### Storage

artifact는 SHA-256 content address로 immutable 저장한다. project head와 labels만 가변 포인터다.

## 동기/비동기 경계

작은 inspect/plan은 동기 응답한다. 한/글 실행, render, PDF 변환, 대형 문서 편집은 job으로 승격하며 `job_id`를 반환한다. UI와 모델은 `job_get`으로 진행 상태와 결과 artifact를 읽는다.

## 서버와 Windows 분리

공개 MCP와 state service는 Linux/Rust로 운영 가능하나, 실제 한/글 오토메이션은 라이선스가 확보된 격리 Windows worker에서만 실행한다. 워커는 tenant별 임시 작업 디렉터리, 제한된 서비스 계정, 네트워크 기본 차단, 프로세스 시간 제한, 자동 재부팅/recycle 정책을 사용한다.
