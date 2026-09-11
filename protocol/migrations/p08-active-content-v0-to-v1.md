# P08 active-content inventory v0 to v1

There is no accepted v0 active-content inventory. A caller must not reinterpret a drawing-canvas
resource list, preservation map, filename scan, or automation flag as
hwpx-agent.active-content-inventory/v1.

Admission requires rebuilding the bounded HWPX package graph, scanning every XML part with the
preserving parser, resolving each reviewed OLE/video reference through the OPF manifest, and
integrity-reading every inventoried payload. Unknown fields, namespace lookalikes, dangling
references, media/signature conflicts, over-limit values, and graph drift fail closed.

The normal product tier has no migration switch that enables OLE, multimedia, executable,
script/macro, form-command, or external-link activation. Any future execution tier requires a new
schema/profile and separate security review; it cannot be represented by changing a v1 boolean.

