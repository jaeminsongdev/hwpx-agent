# P17-08 approved Git effect host v4

Date: 2026-09-06
Scope: current-PC local executor, disposable Git repositories only
Decision: **semantic Git effect executor implemented; P17-08 remains in progress**

The new `git-effect-host` crate is the first executor behind the P17-08 approval boundary. It accepts
only a typed Git commit effect; there is no shell or argument string supplied by a public caller. The
host prepares the exact target/plan request used by the confirmation authority, then consumes an
uncloneable `AuthorizedEffect` and checks effect, scope, receipt schema, operation, workspace target,
plan and execution-age bindings again immediately before Git mutation.

Execution uses one explicit absolute regular Git executable with a cleared environment, interaction
disabled, replace objects disabled and an empty hooks directory. It snapshots and SHA-256 checks the
approved output, bypasses clean filters, builds a tree in a temporary index rooted at the approved
HEAD, creates a commit with exactly that parent, and updates only the approved branch or detached
HEAD through an old-OID compare-and-swap reference transaction. A staged change to the target is
rejected. Unrelated staged entries never enter the temporary tree and remain staged afterward. The
real index is synchronized only for the approved path after the ref transaction. All Git output is
bounded to 256 bytes and errors expose no command, path, content, token or key.

Seven tests execute the current PC's real Git in disposable repositories. They verify exact committed
bytes/parent/branch, unrelated-stage preservation, default deny, stale/output/plan drift rejection,
target-stage preservation, symbolic and detached HEAD behavior, hook suppression and debug/error
redaction. The crate passes all-target Clippy with warnings denied. The implementation follows Git's
documented `update-ref --stdin` transaction and old-object verification semantics:
<https://git-scm.com/docs/git-update-ref>.

This is component evidence only. It did not commit the HWPX Agent repository through the effect host
or touch a user document. P17-08 remains open until the private daemon owns this executor, consumes a
durable trusted-host confirmation through a versioned method, and the MCP layer exposes only the
confirmation-required semantic action. Automation, external provider, printing and security-change
executors remain disabled.
