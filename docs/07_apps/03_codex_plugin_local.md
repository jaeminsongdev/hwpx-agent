# Codex 플러그인과 로컬 Companion

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 두 경로

### Remote path

공용 plugin의 `.app.json`을 통해 ChatGPT Web과 같은 MCP·project state를 사용한다. 문서 기능과 revision 의미가 동일하다.

### Local companion

별도 패키지 또는 repo-local 설정으로 `.mcp.json`을 제공한다.

```text
Codex → stdio/local MCP bridge → local Rust daemon
      → installed Hancom automation adapter (선택)
      → local workspace/object cache
      ↔ remote project sync
```

## 로컬 전용 기능

- fixture directory batch import.
- golden update proposal.
- schema/action catalog generation.
- target Windows workstation runtime probe.
- local Hancom oracle smoke.
- Git diff/handoff/ADR 자동 갱신.
- 민감 문서의 remote upload 금지 모드.

## sync

`.hancom/project-state.json`은 cache/mirror이며 canonical은 remote revision graph다. offline revision은 local branch로 생성하고 reconnect 시 3-way semantic merge 또는 explicit fork를 수행한다.

## 보안

- Codex shell 명령과 automation worker 권한을 분리.
- 임의 HAction 실행용 generic tool을 노출하지 않음.
- local path는 workspace root/allowlist 밖으로 벗어나지 못함.
- generated document를 자동 commit하지 않고 diff와 test receipt를 먼저 제시.
