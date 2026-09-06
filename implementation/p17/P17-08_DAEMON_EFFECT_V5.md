# P17-08 private daemon Git effect v5

Date: 2026-09-06
Scope: current-PC private daemon, disposable Git repository evidence
Decision: **daemon execution boundary implemented; P17-08 remains in progress**

Private daemon protocol v4 now owns the P17-08 Git executor. The capability is default-off. It is
created only when the private host supplies all three environment values: an explicit absolute Git
executable, an absolute approval-state root and a canonical base64url secret. Absence of all three
keeps the daemon read/prepare-only; partial or malformed configuration stops startup. The secret is
decoded into zeroizing storage and is passed only to the approval evaluator. The daemon exposes no
confirmation-authority or token-minting method.

`execute_git_commit` accepts path-free workspace/output identifiers and one signed confirmation. It
rebuilds the exact effect request from the current output, Git HEAD/reference, operation, actor,
tenant and message, consumes the durable replay ledger under the fixed workstation-control scope,
then passes the uncloneable authorization into the semantic Git effect host. The response contains
only bounded identifiers, object/digest evidence, approval time and index status. It does not return
the token, secret, path, message or document bytes. Protocol v1–v3 behavior remains available, while
every older protocol rejects the v4 execution method and v4 rejects older mutation methods.

The daemon now passes eighteen tests: one main reader test, fifteen sandbox/contract tests and two
real binary tests. The new binary test launches the built daemon, uses the current PC's real Git and
a disposable repository, executes one correctly confirmed HWPX commit, verifies exact output bytes,
then rejects reuse of the same request. The default-off/version-crossing test verifies that an
unconfigured daemon cannot execute. Daemon, approval policy and Git effect host all pass all-target
Clippy with warnings denied.

This is private daemon evidence, not a public MCP or Codex-client run. No user repository/document,
Hangul process, UI access prompt or network endpoint was used. P17-08 remains open until an MCP
successor exposes the confirmation-required action and a trusted host/UI supplies the signed
confirmation. The MCP/LLM must never receive a minting capability.
