# P17-08 local MCP confirmed Git effect v6

Date: 2026-09-06
Scope: current-PC local stdio MCP, disposable Git repository evidence
Decision: **MCP effect boundary implemented; P17-08 remains in progress**

The local companion MCP successor is version `0.3.0` and exposes seven tools. The five v2 tools are
preserved. `local_companion_prepare_git_commit_approval` is read-only and returns the exact target
and plan digests required by a trusted confirmation surface. `local_companion_execute_git_commit` is
destructive and non-idempotent. It accepts one signed, single-use confirmation token and forwards
only the fixed semantic Git-commit request to private daemon protocol v4. The MCP server has no
confirmation authority, signing key access through a tool, token-minting tool or arbitrary command
surface.

Health, ordinary workflow and approval-preparation daemon children retain the minimal environment.
Only the confirmed effect child receives the explicit absolute Git executable, approval-state root
and canonical base64url secret. `TEMP` and `TMP` are set to the same bounded approval-state root so
the effect host can create its owned temporary Git index after the rest of the host environment and
`PATH` have been removed. Responses are exact-schema checked and reject any token, secret, private
path or document-content reflection.

Clean source commit `a725c1cc83dbcbdd0c35659fa0925755afacb5b6` produced acceptance run
`d239faf9cabc41eb9386d5d6aa514ec3`, recorded under
`artifacts/p17/mcp-approval-effect-runs/`. All 18 checks passed through the actual MCP `2025-11-25`
stdio transport, Node bridge, Rust daemon and current PC Git executable. The run initialized the
exact seven-tool catalog, prepared target/plan digests, used a test-only authority outside the MCP
server to model a trusted confirmation host, committed exact synthetic HWPX bytes to a disposable
repository, verified the parent and branch, preserved one unrelated staged entry and rejected the
same confirmation on a second process invocation through the durable replay ledger. All temporary
workspaces were removed and no network or Hangul process was used.

The first acceptance attempt correctly rejected an incomplete fixture that lacked the required
`input/` directory. After fixing that fixture, the effect daemon correctly failed closed because the
minimal environment lacked a temporary-directory root. The final change derives both temporary
variables from the approved state root; it does not restore general environment inheritance. Failed
attempts are not promoted to evidence and the final receipt is the only PASS cited above.

This is actual local MCP and disposable Git evidence, but it is not an actual Codex-client,
installed-personal-plugin or trusted user-confirmation UI run. The test authority is not a production
confirmation surface and must not be shipped as one. P17-08 therefore remains open until the trusted
host/UI supplies confirmation without granting the model a minting capability, followed by a fresh
installed-plugin Codex qualification. It also does not qualify Hangul, user repositories, remote
providers, automation, printing or security-change effects.
