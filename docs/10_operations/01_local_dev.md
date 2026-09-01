# 로컬 개발 환경

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 권장 monorepo

```text
crates/             Rust domain/package/backend/control-plane
services/           mcp-gateway, state, jobs, artifact
windows/            automation-worker, oracle-agent, image scripts
web/                MCP Apps widget
plugins/            universal and codex-local packages
schemas/            canonical source schemas
fixtures/           manifests; large binaries external/LFS
catalog/            source locks/generated capability bindings
tests/              conformance/e2e/security
ops/                containers/terraform/runbooks
```

## bootstrap

- pinned Rust toolchain and lockfile.
- Node package manager lock.
- .NET SDK/runtime pinned for Windows worker.
- local PostgreSQL/object store; Redis optional.
- `just`/`cargo xtask` 단일 entry commands.
- secrets는 `.env` template만 제공하고 실제 값 commit 금지.

## 명령 계약

```text
just bootstrap
just generate-schemas
just generate-capabilities
just test-unit
just test-fixtures
just mcp-dev
just widget-dev
just windows-probe TARGET=...
just validate-release
```

새 개발자는 START_HERE만으로 mock backend 기반 core tests를 실행할 수 있어야 한다. 실제 한/글 테스트는 라이선스와 Windows image가 있는 lane에서 별도로 실행한다.
