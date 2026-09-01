# Codex local companion package blueprint

Universal remote package의 skill semantics를 유지하면서 `.mcp.json`으로 workspace-confined local daemon을 추가한다. local cache는 remote project state의 mirror이며 push 전 revision conflict를 확인한다. 실제 배포 시 universal package의 assets/interface metadata를 함께 복사한다.
