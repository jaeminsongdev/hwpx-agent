# P15-07 rate limit and quota policy

Date: 2026-09-05
Scope: current development PC, licensed Hancom Hangul 2020, local MCP control-plane reference
Status: implementation candidate until the P15-07 report closes the card

## Admission boundary

Quota admission runs only after public-user authentication, duplicate-key-free JSON parsing, frozen
input-schema validation and tenant/project authorization. It runs before the single gateway dispatch.
Malformed, unauthenticated or unauthorized calls cannot create quota identities or learn tenant quota
state. A quota rejection performs zero gateway dispatches.

The digest-pinned `protocol/mcp/p15-quota-policy-v1.json` defines a 60-second refill window. Every
admitted call atomically consumes one token from its tenant, authenticated user and capability
bucket. A validated `capability_id` gets its own SHA-256-keyed bucket; other calls use the public tool
kind as their capability key. The six durable async submission tools also consume one tenant-scoped
job-class token:

- `standard`: `document_create`, `document_edit`, `document_transform`, `document_validate`;
- `render`: `document_export`, `document_render`.

The product burst capacities/refill rates per window are tenant `120/120`, user `60/60`, capability
`30/30`, standard job `8/8` and render job `2/2`. Integer refill accounting carries fractional
remainders and never uses floating point. A clock regression for an applicable bucket fails closed.

## Atomicity, fairness and replay

All applicable buckets are inspected under one bounded mutex. Tokens are deducted only when every
bucket can admit the call. If any bucket is exhausted, no bucket is charged and the largest exact
wait across exhausted dimensions becomes the bounded client-only `hwpx/retryAfterSeconds` value.
Tenant, user, capability and job-class keys are independent, so one noisy tenant or user cannot
consume another identity's bucket.

The in-memory reference retains at most 65,536 bucket records and 65,536 replay records. Capacity,
poisoned state, invalid policy and arithmetic/clock invariants fail closed as quota unavailability.
Production distributed persistence, cross-replica atomicity and administrative quota mutation are
not claimed by this card.

Only the six durable async submission tools use the 900-second quota replay cache. The key binds
tenant, authenticated subject digest, tool and idempotency key; its fingerprint binds the validated
arguments after removing only `request_id`. An exact replay is admitted without a second charge.
Reusing the key with different arguments returns a request conflict. Non-async calls are charged per
admission and preserve their existing P15-03 through P15-05 behavior.

## Public failure and privacy

The immutable P15-06 v1 error catalog remains present with its original digest. The additive
`p15-public-error-catalog-v2.json` preserves all prior codes and adds:

- `QUOTA_EXCEEDED`: retryable storage-category failure at the `quota` stage;
- `QUOTA_UNAVAILABLE`: retryable backend-category failure at the `quota` stage.

`REQUEST_CONFLICT` additionally permits the `quota` stage for idempotency-payload conflicts. Public
structured details remain empty. Retry seconds are a bounded integer in client-only metadata; bucket
keys, tenant IDs, subject digests, token counts, payload fingerprints and internal errors are never
returned. Every success and error result includes the quota-policy digest for correlation.

## Deferred claims

No Hangul process, COM call, HWPX/PDF/user document or network service is used by this card.
Distributed rate limiting, Redis/PostgreSQL persistence, active-job concurrency release, plan/billing
entitlements, production HTTP `Retry-After`, cross-region fairness and abuse/cost controls remain
P15-09/P18/P19 work. Hancom 2022/2024 remain deferred to their own PCs.
