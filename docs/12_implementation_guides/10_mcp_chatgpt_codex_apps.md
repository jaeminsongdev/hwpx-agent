# MCP 서비스·ChatGPT Web·Codex 플러그인 구현

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 앱 형태

primary archetype은 **interactive-decoupled**다. 문서 작업은 장시간 job과 preview/버전 선택이 필요하므로 data tool과 render widget을 분리한다. public tool은 사용자 목적 단위이며 609개 capability를 tool 609개로 노출하지 않는다.

## public tool 규칙

- schema는 enum/range/required를 명확히 한다.
- mutation은 `expected_revision`, `idempotency_key`가 필수다.
- annotations의 read-only/destructive/idempotent/open-world 의미를 정확히 지정한다.
- `structuredContent`에는 요약/IDs만, 대형 또는 민감 payload는 artifact와 widget-only metadata로 전달한다.
- tool description은 “Use this when …” 형태의 선택 기준을 포함한다.

## server handler 순서

```text
authenticate -> resolve tenant/project
-> parse JSON Schema
-> authorize capability/risk
-> compile or enqueue job
-> return structuredContent + concise narration + UI resource metadata
```

MCP handler 안에서 COM/ZIP 작업을 직접 수행하지 않는다. job orchestration을 호출한다.

## widget

주 화면:

- project/revision selector.
- capability/dry-run summary.
- page thumbnails and validation badges.
- semantic diff and warning/degradation.
- job progress/cancel/retry.
- output download/export.

MCP Apps bridge를 기본으로 사용한다. tool result notification을 받아 `structuredContent`로 렌더하고, widget 동작은 `tools/call`로 서버 도구를 호출한다. `window.openai`는 file upload, display mode, host theme/locale 같은 ChatGPT 확장에만 feature detection으로 사용한다.

## UI resource 보안

- exact CSP `connectDomains`/`resourceDomains`.
- versioned immutable resource URI.
- HTML에 artifact signed URL을 장기 저장하지 않는다.
- document content를 localStorage에 보관하지 않는다.
- UI에서 임의 capability/action을 만들지 않고 server가 제공한 plan/registry를 선택한다.

## 패키지

```text
.codex-plugin/plugin.json
.app.json                 # registered remote app mapping
skills/*/SKILL.md
assets/*
```

Codex local companion은 별도 패키지로 `.mcp.json` local bridge와 hooks/AGENTS instructions를 둘 수 있다. universal Web package에 local-only file paths나 secrets를 포함하지 않는다.

## 로컬/스테이징 검증

1. schema/static contract test.
2. MCP Inspector에서 tool/resource 목록과 annotations 확인.
3. staging HTTPS `/mcp`에 연결.
4. ChatGPT developer mode에서 create→dry-run→execute→preview→download.
5. Codex remote에서 같은 project open/edit/checkpoint.
6. Codex local에서 local fixture를 처리한 뒤 remote checkpoint sync.
7. retry, stale revision, permission denied, worker unavailable, unverified oracle UI 확인.

## 제출 준비

privacy, terms, support, data handling, destructive action confirmation, app metadata, icons/screenshots, domain verification, test account/runbook을 release artifact로 관리한다. 제출 시점에 최신 공식 OpenAI 문서로 manifest/tool/UI 요구사항을 다시 검증한다.
