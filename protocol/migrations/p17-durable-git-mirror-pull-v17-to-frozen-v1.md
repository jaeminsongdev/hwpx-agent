# P17 durable Git mirror pull v17 to frozen v1

The current-PC durable-pull qualification is retired as a mutable-worktree authority and replaced
by `hwpx-agent.p17-frozen-durable-git-mirror-pull-v17/v1`. The frozen verifier accepts only the
exact implementation commit `dbbdab7b7dae62790a96bbfa81b3ce3af33a21f6`, qualification commit
`f79ad78a1e984622582c620eb2f4f030fb6beeff`, bounded committed Git blobs, and their pinned digests.

No evidence field is promoted by this migration. Remote Git networking, persistent credentials,
registered-host operation, production, Hangul, `P17-06`, and product completion remain false.
