# Universal ChatGPT Web/Codex package blueprint

1. `.app.json`의 registered app ID를 실제 값으로 교체한다.
2. `.codex-plugin/plugin.json`의 조직·URL·라이선스·asset을 교체한다.
3. `skills/`의 tool names를 production MCP descriptors와 동기화한다.
4. public package에는 local `.mcp.json`, API key, Windows path를 포함하지 않는다.
5. release 시점의 공식 OpenAI plugin/Apps SDK 문서로 manifest와 UI metadata를 재검증한다.
