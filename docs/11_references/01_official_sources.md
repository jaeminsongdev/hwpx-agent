# 공식 자료 기준 목록

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Hancom

- HWP Automation 개발 가이드: `https://developer.hancom.com/hwpautomation`
  - ActionTable, HwpAutomation, ParameterSetTable, Event Handler, 보안 승인 모듈.
  - 비상업적 개인 이용과 상업적 이용 라이선스 조건을 release gate에서 재확인.
- WebHWP 개발 가이드: `https://developer.hancom.com/webhwp/devguide`
- HWPX 포맷 소개: `https://tech.hancom.com/hwpxformat/`
- 한/글 2024 도움말: `https://help.hancom.com/hoffice130/ko-KR/Hwp/index.htm`
- 한글 문서 포맷 공식 자료: Hancom download center의 HWP/OWPML 자료.

## OpenAI

- Plugin architecture: `https://developers.openai.com/plugins/concepts/plugins`
- Package plugins: `https://developers.openai.com/plugins/build/plugins`
- Build MCP server: `https://developers.openai.com/plugins/build/mcp-server`
- Add MCP UI: `https://developers.openai.com/plugins/build/chatgpt-ui`
- Define tools: `https://developers.openai.com/plugins/plan/tools`
- Connect/test: `https://developers.openai.com/plugins/test-connect`
- Submission/guidelines/security pages는 P16/P19에서 최신 상태 재수집.

## source lock 정책

각 외부 자료는 `source-lock.json`에 URL, fetched_at, version/build, SHA-256, parser version, license note를 기록한다. 링크만 저장하지 않는다. PDF/ZIP/XSD 원본은 라이선스가 허용하는 내부 저장소에 immutable 보관한다.

## 우선순위

공식 Hancom schema/manual/help/runtime와 공식 OpenAI docs가 1차 source다. 커뮤니티 라이브러리는 구현 참고이며 기능 지원의 권위가 아니다.
