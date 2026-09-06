# P17-08 default-deny approval core v1

Date: 2026-09-06
Scope: pure local reference approval policy
Decision: **first bounded increment implemented; P17-08 remains in progress**

The `approval-policy` crate models only five predefined side-effect classes: Git commit,
allowlisted automation execution, external invocation, printing and security modification. There
is no arbitrary shell-command string in the model. Each effect maps to a separate capability scope.
An empty allowlist is the default policy and denies even a correctly signed confirmation.

Authorization requires every layer to pass: tenant policy allowlist, user/role scope, a fresh
explicit confirmation, HMAC integrity, exact actor/tenant/effect/operation/target/plan binding,
bounded issue/expiry times and single-use consumption. The local reference token lifetime and
request age are capped at five minutes. Tokens, signing keys, identifiers and digests are redacted
from Debug output. The approval receipt records only bounded effect/scope metadata and digests; it
does not contain the raw operation ID, confirmation token, key, command or document body.

Nine tests cover default deny, missing scope/confirmation, exact authorization, replay, binding
drift, signature tamper, expiry/future issuance, absent confirmation, lifetime/request-age bounds,
capacity/pruning and debug/error redaction. All-target Clippy passes with warnings denied.

The replay registry is process-local in this increment. Restarting the process would forget a
consumed confirmation, so no side-effect executor is wired and no actual Git, automation, network,
print or security action is authorized by this result. A create-new durable replay ledger and
daemon/MCP integration are required before P17-08 can become PASS. Production must also replace the
local HMAC signer with the trusted host confirmation service.
