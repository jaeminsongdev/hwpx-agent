# P17 durable Git mirror pull qualification v17

## Decision

`p17.durable-git-mirror-pull.v1.20260911` is PASS for the exact current-PC scope: PostgreSQL
18.4 in a digest-pinned loopback container, an explicitly local disposable bare Git repository,
and authenticated loopback request/response framing. The qualification binds implementation
commit `dbbdab7b7dae62790a96bbfa81b3ce3af33a21f6` to run
`4162580f49da402983be6a8527e9721e` and its 20 exact checks.

## Earned evidence

The run verified migration 17, observed-snapshot backfill, a clean fast-forward observation,
exact replay without a second observation, an ahead-state conflict that preserved pending local
state, immutable observations, Git/database drift rejection, least-privilege drift rejection,
and owned-resource cleanup. The receipt and every runtime source are SHA-256 bound to the source
commit; guard sources are separately bound by the generated qualification contract.

## Boundary

This is current-PC component/runtime qualification only. It does not exercise a remote Git
network or service, persistent credential custody, registered-host lifecycle, production
authentication, HWPX, Hangul, rendering, or another PC/version. `P17-06`, production, and product
completion remain false.
