# P09 field engine v0 to v1

There is no accepted v0 field-engine state. A caller must not reinterpret a raw field code,
display-only string, cursor-only insertion, unordered field list, single native ID, ambient clock,
ambient filename, current page guess, or unverified automation action as v1.

V1 requires the complete ordered inventory; logical and native begin/end identities; exact anchors;
typed definitions and cached results; update/cache/lock state; evaluation, style, payload, opaque,
and unrelated document bindings. Date, filename, page, section and object results are explicit
observations. No migration switch computes them from workstation state.

Unknown or duplicate fields, invalid limits, malformed identities/names/text/locale/timezone or
digests, result-kind mismatch, collisions, missing targets, locked/frozen updates, no-ops, state or
flow drift and plan tampering fail closed. There is no migration switch that weakens these rules or
promotes component evidence to HWPX, Hangul, field-readback, render, automation, differential,
production, P09, or product evidence.
