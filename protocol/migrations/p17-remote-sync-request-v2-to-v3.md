# P17 remote sync request v2 to v3

The private remote-sync request advances from `hwpx-agent.remote-sync-request/v2` to v3. All
operations retain the exact `(project_id, branch_id, mirror_id)` binding introduced by v2.
`checkpoint` additionally requires `label` and may include `note`; an absent note is omitted rather
than encoded as `null`. The response remains `hwpx-agent.remote-sync-response/v1`.

This is a breaking private request migration. A v3 host must reject v2 requests. For checkpoint
requests it must enforce the public P15 length bounds, the P14 label constraints, exact expected
head, and idempotency binding before mutation. The response `request_sha256` covers the exact v3
bytes, including label and note when present.

The local client persists only the idempotency key and exact v3 request SHA-256. It does not persist
the label or note text. Retrying an uncertain checkpoint with the same key but changed identity,
head, label or note is rejected before credential acquisition or remote I/O.

