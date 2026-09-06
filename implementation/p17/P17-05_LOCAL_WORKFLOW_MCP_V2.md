# P17-05 local workflow daemon and MCP v2

Date: 2026-09-06
Scope: current PC, path-free local workflow integration
Decision: **PASS for current-PC local file/Git-plan workflow**

The private daemon now preserves the qualified v1 health and path-authorization protocol while
adding a versioned v2 boundary for materialize, identity-only diff, create-new publish and
digest/current-HEAD-bound Git-plan preparation. Version crossing fails closed: v1 cannot call v2
workflow methods, and v2 cannot call the legacy path method.

The MCP bridge is version `0.2.0` and exposes the existing health tool plus four workflow tools.
Public inputs contain only bounded workspace, operation, fixture and output identifiers, lowercase
SHA-256 values, a fixed slot and a bounded commit message. No public input accepts a path. The
daemon alone derives `input/{fixture_id}.hwpx` and `output/{output_id}.hwpx` inside a qualified
workspace.

Materialize and publish are create-new operations. Publish is marked destructive because it
creates the public output and removes the private candidate after verified copy; it never replaces
an existing output. Diff returns only digest, size and equality. The Git helper is read-only and
returns `executed=false`; it does not spawn Git or change the index. Actual commit execution remains
reserved for the denied-by-default P17-08 approval policy.

Clean implementation commit `e1e3edaa7e830cc05086bc1af2847bdbf00c8506` produced actual MCP
stdio run `bf248400ce1c4985bb2353aa9209ec02`. All 16 checks passed. The run initialized
MCP `2025-11-25`, discovered the exact five-tool catalog, called the real Node bridge and Rust
daemon through materialize, diff, publish and Git-plan preparation, and rejected traversal,
oversized input and unknown fields without a partial workflow file. The disposable workspace was
removed and residual daemon/Hangul process counts were both zero.

The canonical 990-byte receipt is Git-ignored at
`artifacts/p17/local-workflow-runs/bf248400ce1c4985bb2353aa9209ec02/receipt.json`; its SHA-256 is
`36641be1a6bf7d37c3a796c624cfcb885b6c650acffac14e3d4d8fe1b55fe721`. Component validation also
passed 9 local-workflow tests, 13 daemon tests, Rust Clippy with warnings denied, TypeScript
typecheck/build, eight bridge tests and four acceptance-harness tests.

This PASS satisfies the P17-05 path traversal/large-file acceptance for the local workflow helper.
It does not claim a Codex client call, personal-plugin reinstall, real Git commit or approval-policy
execution. Those remain P17-08 work. No Hangul process, access prompt, user document or network
request is part of this evidence.
