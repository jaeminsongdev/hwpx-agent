# Preview·Diff·Capability Widget

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 화면 구성

1. **Project header**: project, branch, head revision, target Hancom build.
2. **Page preview**: thumbnail rail, zoom, page dimensions, render provenance.
3. **Outline/object tree**: section, paragraph, table, equation, object handles.
4. **Change panel**: semantic diff, affected pages, source preservation.
5. **Validation panel**: pass/fail/unverified evidence.
6. **Capability panel**: backend route, unavailable reason, warning.
7. **Revision picker**: checkpoints, compare, publish.

## 통신

MCP Apps 표준을 먼저 사용한다.

- UI resource: `_meta.ui.resourceUri`.
- 초기화/결과: `ui/initialize`, `ui/notifications/tool-result`.
- component tool call: `tools/call`.
- follow-up: `ui/message`.
- ChatGPT 전용 `window.openai`는 file picker, modal, display mode 등 shared spec 밖의 기능만 feature-detect해 사용.

## state

widget state에는 선택 페이지/노드/zoom/filter만 저장한다. project head, document graph, job, artifact는 서버 source of truth다.

## CSP

`connectDomains`와 `resourceDomains`는 exact allowlist. preview image/object URL은 동일 app domain 또는 signed CDN domain만 허용한다. 문서 안 외부 URL을 widget이 직접 fetch하지 않는다.

## 접근성

키보드 navigation, focus order, zoom, reduced motion, 고대비, validation 상태의 text equivalent, 페이지 preview alt summary를 제공한다. visual diff는 색만으로 상태를 표현하지 않는다.
