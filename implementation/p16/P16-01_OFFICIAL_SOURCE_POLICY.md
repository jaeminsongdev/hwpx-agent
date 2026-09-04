# P16-01 Official Source Policy

## Decision

P16 UI와 플러그인 패키징은 2026-09-04 UTC에 다시 확인한 OpenAI Plugin 문서와 stable MCP Apps
표준을 기준으로 구현한다. 이 카드의 범위는 **공식 소스와 구현 의무의 잠금**까지다. 플러그인 번들,
위젯, ChatGPT Developer mode 연결, 공개 HTTPS, 제출, 한글/COM 실행은 구현하거나 검증한 것으로
간주하지 않는다.

기계 판독 가능한 정본은 `protocol/apps/p16-official-source-lock-v1.json`이다. 각 변경 가능한 웹
문서는 조회 시각, 응답 바이트 길이, SHA-256을 기록하며, 공식 examples와 MCP Apps 릴리스는 Git
commit/tag로 고정한다. `tools/p16/validate_official_source_contract.py --check-online`은 출시 시점에
공식 문서가 동일한지 다시 확인하고, 변경이 있으면 실패시켜 재검토를 요구한다.

## Architecture lock

- 공통 UI 기반은 MCP Apps다. tool은 `_meta.ui.resourceUri`로 versioned `ui://` resource를 참조하고,
  resource는 `text/html;profile=mcp-app`을 반환한다.
- iframe과 host의 기본 통신은 `postMessage` 위의 MCP Apps `ui/*` JSON-RPC lifecycle이다.
- `window.openai`는 shared MCP Apps에 대응 기능이 없는 ChatGPT 전용 확장을 capability detection으로만
  사용한다. host 이름이나 제품 이름으로 분기하지 않는다.
- P15의 18개 public data/action tool은 UI 없이도 완결돼야 한다. P16에서 추가하는 dedicated render
  tool만 UI resource를 선언하며, 새 tool/schema는 versioned migration과 negative test 없이 공개하지
  않는다.
- 승인 대상 tool의 초기 input이 비어 있는 상태는 오류가 아니다. 승인 이후
  `ui/notifications/tool-input`으로 전달되는 lifecycle을 처리한다.

## Manifest lock

- entry point는 plugin root의 `.codex-plugin/plugin.json`이다.
- 모든 manifest path는 `./`로 시작하고 plugin root 안에서만 해석된다.
- registered remote MCP connection은 root의 `.app.json`에 두고 manifest의 compatibility `apps`가 이를
  가리킨다. 실제 `plugin_asdk_app...` 값은 Developer mode 등록 결과만 허용하며 가짜 값을 만들지
  않는다.
- bundled local MCP server가 필요할 때만 `.mcp.json`과 `mcpServers`를 사용한다. registered remote
  mapping과 혼동하지 않는다.
- P16-03은 9개 workflow skill을 실제 versioned public tool names에 맞추고 positive/negative trigger
  evaluation을 남긴다.

## UI, data, and file boundary

- model-visible `structuredContent`는 schema-valid한 opaque ID와 bounded summary만 포함한다.
- document bytes, raw HWPX XML, HAction/COM identifiers, arbitrary local paths, credentials, unbounded
  document content는 public/model-visible contract에 넣지 않는다.
- component-only hydration은 result `_meta`에 둘 수 있지만 secret을 넣지 않고, server는 매 호출마다
  tenant, subject, scope, project, revision, artifact ACL을 재검증한다.
- `uploadFile`, `selectFiles`, `getFileDownloadUrl`은 모두 ChatGPT 전용 capability로 feature-detect한다.
  upload는 server-side media type/size/digest/tenant/ACL 검사를 거치며, download는 `artifact_get` 또는
  host file reference와 bounded expiry/fresh authorization을 사용한다.

## CSP and accessibility lock

- standard resource policy는 returned content item의 `_meta.ui.csp`에 둔다.
- `connectDomains`, `resourceDomains`, 필요한 경우의 `frameDomains`는 wildcard 없는 exact HTTPS origin만
  허용한다. nested frame은 기본 금지한다.
- legacy `openai/widgetCSP`는 compatibility 또는 `openExternal`의 reviewed `redirect_domains`에만 쓴다.
- 제출용 unique `_meta.ui.domain`은 실제 hosting이 정해지기 전까지 `unverified`다.
- inline-first, 최소 display mode, inline card 최대 2개 action, no deep navigation/no nested scrolling을
  적용한다. keyboard, focus, semantic label, contrast, responsive size, theme, locale, reduced motion은
  P16-09 acceptance 항목이다.

## Security and validation lock

- 최소 권한, 명시적 동의, destructive/write 확인, server-side validation을 적용한다.
- prompt injection과 악성 파일을 정상적인 hostile input으로 간주한다.
- 로그는 PII/secret/raw prompt/raw document를 남기지 않고 bounded correlation ID만 보존한다.
- MCP Inspector에서 discovery, representative/edge/missing/empty, auth, annotation, confirmation,
  model-readable result를 검증한다.
- ChatGPT Developer mode 최종 E2E는 사용자가 직접 UI를 조작하는 별도 세션에서 positive, indirect,
  follow-up, write-confirmation, unsupported, boundary prompt와 console/state restore를 확인한다.

## Current scope

현재 범위는 이 PC의 정품 한글 2020을 대상으로 하는 local development뿐이다. P16-01은 한글을 켜지
않고 COM을 호출하지 않는다. 한글 2022/2024와 다른 PC, production hosting, workspace/public publish,
submission은 해당 환경과 권한이 준비된 뒤 별도 증거로 검증한다.
