# P17 checkpoint service mapping v1 admission

This is the first private-to-service checkpoint mapping contract and therefore has no predecessor
payload to migrate. It accepts only `hwpx-agent.remote-sync-request/v3` checkpoint semantics and
produces the unchanged P15 `project_checkpoint` input v1 shape. Pull, push, v1/v2 checkpoint
requests and unknown mapping versions are not admitted by this mapper.

The public idempotency UUID is derived deterministically from the exact private
`(project_id, branch_id, mirror_id, idempotency_key)` identity. Host correlation fields do not alter
that key or the service-intent digest. A future mapping version must use a new schema version and
must not reinterpret an existing v1 key derivation.

This mapping does not migrate or authenticate a mirror. The host must verify the retained private
project/branch/mirror/head binding before dispatching the mapped P15 service request.
