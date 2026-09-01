# 패키징·연결·제출

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 개발 연결

1. staging MCP `/mcp`를 HTTPS로 노출.
2. ChatGPT Developer Mode에서 remote MCP app 등록.
3. 발급된 registered app technical ID를 `.app.json`에 매핑.
4. `.codex-plugin/plugin.json`의 `apps`를 `./.app.json`에 연결.
5. plugin 변경 시 연결을 새로고침하고 새 chat에서 테스트.
6. Codex local companion은 별도 `.mcp.json`과 approval policy로 검증.

## 제출 전 체크

- stable tool names/schemas/annotations.
- OAuth redirect and account deletion.
- privacy policy, terms, support, domain ownership.
- UI CSP/domain and accessible screenshots.
- harmful file/security behavior review.
- rate limit, retry, error UX.
- test tenant와 production tenant 분리.
- Hancom 상업 automation license evidence.
- 지원 한/글 버전과 제한 공개.

## compatibility drift

OpenAI plugin/app manifest와 UI API는 변할 수 있으므로 P16/P19마다 공식 문서를 다시 fetch하고 `manifest-contract` 테스트를 갱신한다. 이 문서의 example은 기준 설계이며 release 시점 공식 schema가 최종 권위다.
