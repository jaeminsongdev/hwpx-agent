# P17-06 authorized mirror admission v7

Date: 2026-09-06
Scope: current-PC retention mirror registry checkpoint admission
Decision: **exact mirror/head admission implemented; authenticated host and dispatch remain open**

`retention-sync-service` now parses the exact lowercase `mir_` public identifier and provides a
read-only checkpoint admission operation. The operation uses its request context as the tenant and
subject authority, requires at least the editor role, and finds the mirror only inside that tenant.
The stored mirror must belong to the exact project and branch supplied by the request. An alias or
unknown identity returns the existing non-disclosing not-found result.

The requested expected head must be structurally valid and equal both the current registered branch
head and the mirror's observed head. A stale head returns the current head as a typed conflict and
does not mutate the registry. Dispatch is admitted only while the mirror is clean, has no pending
operation plan and has no active push lease. This keeps local unpushed work and an in-flight push
from being mislabeled as an already remote checkpoint.

The machine contract is `protocol/private/p17-checkpoint-host-admission-v1.json`; first-version and
future version rules are recorded in
`protocol/migrations/p17-checkpoint-host-admission-v1.md`. The target suite passes 18 tests, including
canonical-ID negatives, exact project/branch/mirror binding, missing-role rejection, non-idle
rejection, stale-head reporting and no-mutation. Formatting and all-target/all-feature Clippy with
warnings denied pass.

This increment still does not authenticate a bearer credential, bind an `AuthContext` to the
registry request context, open network transport, dispatch the mapped P15 arguments, or capture an
actual remote transition. It is component evidence only and does not prove P17-06 PASS. The next
increment is a bounded server host that performs one-time `mirror.sync` service-token
authentication, canonical request decoding, this admission check and injected checkpoint dispatch
in that order.
