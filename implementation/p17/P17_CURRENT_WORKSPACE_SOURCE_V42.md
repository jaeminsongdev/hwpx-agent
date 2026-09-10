# P17 current workspace source qualification v42

## Decision

`p17.current-workspace-source.v42.20260911` is PASS for the exact durable Git mirror pull
implementation commit `dbbdab7b7dae62790a96bbfa81b3ce3af33a21f6` and its current-PC runtime
qualification. It preserves the immutable frozen v41 predecessor and binds 29 implementation
sources, six runtime-qualification sources, three guard sources, and the 28 existing workspace
source successors.

## Evidence

Current-source run `75c0595bbf5842d2b417927b96c319f8` passed 11 checks and is bound by receipt
SHA-256 `92fa78d9974df9159d3d4212d04e44688148a9ccb9cd32ad57f59620e4daa71c`.
The nested runtime qualification binds the exact 20-check PostgreSQL 18.4, local bare-Git, and
authenticated-loopback pull receipt. Implementation source bytes must equal Git blobs from the
base commit; mutable guard and qualification files are separately hashed.

## Boundary

This source successor earns only the current-PC durable pull claims. Remote-network Git,
persistent credential custody, registered-host lifecycle, production, Hangul, other PC/version,
`P17-06`, and product completion remain false.
