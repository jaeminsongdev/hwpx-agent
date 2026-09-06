# P17 checkpoint host admission v1

This is the first retention-mirror checkpoint admission contract, so there is no predecessor state
to migrate. Hosts must parse the exact lowercase public project, branch, mirror and revision IDs and
must not infer an identifier from a label, path or display name.

The check is deliberately read-only. A stale expected head returns the current registered head as a
conflict without mutating either branch or mirror state. A cross-tenant, cross-project,
cross-branch or cross-mirror alias is indistinguishable from absence. Non-idle mirrors are rejected
before checkpoint dispatch.

Future versions may add a durable transactional reservation around service dispatch. They must not
weaken exact identity, tenant/subject authorization, clean-mirror or stale-head checks. Version 1 is
only a component prerequisite: it does not authorize claims of bearer authentication, network
transport, P15 dispatch, an actual remote transition or P17-06 completion.
