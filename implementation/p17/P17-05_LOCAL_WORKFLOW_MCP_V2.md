# P17-05 local workflow daemon and MCP v2

Date: 2026-09-06
Scope: current PC, path-free local workflow integration
Decision: **implemented; clean-commit MCP acceptance pending**

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

The current implementation passed the Rust daemon tests and Clippy as well as MCP TypeScript
typecheck, build and eight unit tests. These component results are not the clean-commit MCP
acceptance. `tools/p17/run_local_workflow_checks.py` must still run from a clean implementation
commit and prove discovery and real Node-to-Rust calls in a disposable workspace before this
increment can be qualified.

No Hangul process, access prompt, user document, network request, personal-plugin reinstall or real
Git commit is part of this increment.
