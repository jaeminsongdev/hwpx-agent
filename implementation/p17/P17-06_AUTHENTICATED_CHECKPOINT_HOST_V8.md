# P17-06 authenticated checkpoint host v8

Date: 2026-09-06
Scope: current-PC injected server-host component for private checkpoint
Decision: **authenticated host boundary implemented; actual transport and concrete P15 dispatch remain open**

The new `remote-sync-host` crate owns the server-side order for one checkpoint exchange. It first
bounds the request and validates host correlation fields, then authenticates and consumes a
single-use internal service bearer with the `mirror.sync` scope. It decodes only the exact canonical
private v3 checkpoint bytes, parses exact public project/branch/mirror/revision IDs, binds the
authenticated tenant and subject to retention-mirror admission, and invokes an injected checkpoint
dispatcher only after every prerequisite succeeds.

A stale expected head returns the current registered head in a request-SHA-bound conflict without
dispatch. A cross-mirror alias, missing role, non-idle mirror or definitive dispatcher denial returns
a bound rejection. Repository failure, uncertain service outcome, invalid checkpoint ID or a
returned revision different from the exact expected revision are unavailable rather than success,
because a mutation may already have occurred. The same private idempotency mapping can therefore be
retried later with a fresh one-time service credential.

The dispatcher receives the exact P15 `project_checkpoint` arguments, authenticated tenant and
subject, service-intent SHA-256 and exact argument SHA-256. Debug output redacts authentication,
dispatcher, tenant, subject, document labels, notes, IDs and digests. The crate has no listener and
never logs or persists a bearer. Its six tests cover success and replay, stale head without
dispatch, cross-mirror and service rejection, canonical-body failure after token consumption,
uncertain and invalid receipts, invalid authentication and debug redaction. Formatting and
all-target/all-feature Clippy with warnings denied pass.

The machine contract is `protocol/private/p17-checkpoint-authenticated-host-v1.json`; first-version
and future version rules are in
`protocol/migrations/p17-checkpoint-authenticated-host-v1.md`.

This remains injected component evidence. The local HMAC verifier is explicitly a reference
adapter, and there is no network listener, qualified credential provider, asymmetric JWKS/IdP,
concrete P15 checkpoint backend, cross-boundary durable transaction or actual remote transition.
P17-06 is therefore still in progress. The next increment is a concrete service adapter compatible
with P15 idempotency and note semantics, followed by an in-process client/host compatibility test;
actual transport qualification comes only after those pass.
