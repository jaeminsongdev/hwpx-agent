# P06 table layout v0 to v1

There is no persisted v0 table-layout payload to migrate. `hwpx-agent.table-layout/v1` is a new
private component boundary composed over the immutable `hwpx-agent.table-grid/v1` identity and the
checked micrometer/ratio unit model.

An importer may construct v1 only after validating the exact grid, resolving absolute/percent/
fit-content/fit-page width semantics, supplying exactly one column constraint and one master-cell
measurement, and attaching structurally valid font-metric evidence. Unknown versions, fields,
width modes, negative or unbounded dimensions, fixed-below-minimum columns, preferred-below-minimum
measurements, duplicate/missing cells, invalid metric provenance and arithmetic/allocation/output
limits fail closed.

The migration must not reinterpret an old renderer width as verified font evidence. Missing fonts
remain explicit and make the plan unverified. Hard minimums are never reduced. Body overflow, target
overflow, fixed-span content deficit and exact-target underfill remain explicit receipt data and
must not be converted into a successful fit.

A new contract version is required before changing width-mode rounding, minimum distribution,
preferred allocation, canonical order, metric-evidence binding, row-height estimation, limit
ceilings, canonical serialization or verified-fit conditions. This v1 component does not migrate or
claim HWPX lowering, Hancom renderer fidelity, row-height operations, pagination or public API
support.
