# P17 remote sync request v1 to v2

The private remote-sync request advances from `hwpx-agent.remote-sync-request/v1` to v2. Every
`pull`, `push`, and `checkpoint` request now requires the opaque `mirror_id` already stored by the
local mirror. The response remains `hwpx-agent.remote-sync-response/v1`.

This is a breaking private request migration. A v2 host must reject v1 requests and must resolve the
triple `(project_id, branch_id, mirror_id)` under the authenticated tenant before reading or
mutating state. It must reject a mirror that belongs to another project or branch. The exact v2
request bytes, including `mirror_id`, remain covered by `request_sha256` in the response.

The field is not public or model-visible. Debug output continues to redact project, branch, mirror,
digest, credential, and idempotency values. No compatibility fallback may invent or infer a mirror
identity from only a project and branch.
