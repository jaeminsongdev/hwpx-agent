# P07 equation layout v0 to v1

There is no stored v0 qualification or estimate to migrate. Version 1 starts fail-closed.

Existing P07-05 extents remain `provisional` with no evidence digest and
`render_required=true`. They MUST NOT be relabeled as target readback or a verified estimator.

A v1 qualification must be rebuilt from the exact target build, font-metric evidence, a bounded
semantic corpus, native readback and inspected render ink boxes. It must contain at least four
inline and four display samples, object-extent error no greater than 150 HWPUNIT, baseline error no
greater than 50 HWPUNIT, zero clipping, overflow, overlap and silent fallback, and complete page inspection. The exact qualification bytes
must be pinned by a trusted SHA before use.

An exact measured case may produce `target_readback`; a non-exact case may produce
`verified_estimator` only inside the qualified structural envelope. Every other case remains
provisional and requires render. Raw JSON cannot forge a verified HWPX extent: the lowerer requires
the opaque estimator result and rechecks semantic, layout, base-unit, baseline, extent, source and
evidence bindings.
