# ChatGPT·Codex 공용 플러그인 패키지

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 목표 형태

```text
hwpx-agent-plugin/
 ├─ .codex-plugin/plugin.json
 ├─ .app.json                  # registered remote MCP mapping
 ├─ skills/
 │   ├─ create-hancom-document/SKILL.md
 │   ├─ edit-hancom-document/SKILL.md
 │   ├─ compose-math-exam/SKILL.md
 │   ├─ validate-hancom-document/SKILL.md
 │   └─ resume-hancom-project/SKILL.md
 └─ assets/
```

OpenAI의 현재 플러그인 패키징에 맞춰 required entry는 `.codex-plugin/plugin.json`이며, 공개 공용 패키지는 등록된 원격 MCP를 `.app.json`으로 연결한다. 로컬 MCP가 필요한 Codex 개발판은 별도 companion 패키지로 분리한다.

## 권장 archetype

`interactive-decoupled`를 기본으로 한다.

- 문서 생성·편집·검증 자체는 UI 없이도 완결되는 MCP 도구.
- preview, 페이지 이동, revision 비교, 기능 경고 확인은 React widget.
- data operation과 render operation을 분리해 widget이 매 tool call마다 재생성되지 않게 한다.

## manifest 원칙

- name/version/description을 안정적으로 유지.
- `skills: "./skills/"`.
- `apps: "./.app.json"`.
- 공개 배포 전 author, repository, license, privacy, terms, support, icon, screenshots를 채움.
- 모든 경로는 plugin root 기준 `./` 상대경로.
- 정확한 schema는 P16에서 최신 공식 문서와 `@plugin-creator` 출력으로 재검증.

## surface-specific 기능

같은 listing을 사용하되:

- ChatGPT Web: 원격 MCP, file upload/download, widget 중심.
- Codex remote: 원격 MCP + repo 문서/스킬 워크플로.
- Codex local: 별도 local companion에서 설치된 한/글·로컬 fixture·Git integration.

surface 차이는 capability response에 노출하고, 사용자가 불가능한 기능을 호출했을 때 명확한 대안을 제시한다.
