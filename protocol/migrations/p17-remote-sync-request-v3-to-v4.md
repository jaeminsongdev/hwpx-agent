# P17 remote sync pull request v3 to v4

The private remote-sync request advances only the `pull` operation from
`hwpx-agent.remote-sync-request/v3` to `hwpx-agent.remote-sync-request/v4`. A v4 pull adds the
required `observed_snapshot_sha256` beside `observed_head`; the digest is the client's exact
snapshot at that observed revision and generation. This closes the ambiguity where one revision
identity could otherwise be paired with stale or substituted document state.

The migration is breaking for pull. The durable v4 pull host accepts only canonical v4 bytes and
rejects v3 pull requests, missing or malformed digests, and any head/snapshot mismatch before a
database mutation. The response remains `hwpx-agent.remote-sync-response/v1`, with its
`request_sha256` bound to the exact v4 request bytes.

`push` and `checkpoint` remain on request v3 and retain their existing contracts. This operation-
scoped version split is deliberate; it does not silently reinterpret a v3 push or checkpoint as
v4. Persistent credential custody, remote network transport, registered-host lifecycle,
production authentication, P17-06 completion and product completion remain outside this migration.
