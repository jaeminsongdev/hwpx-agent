# P09 note HWPX v0 to v1 migration

There is no accepted v0 direct-HWPX note insertion profile. Earlier note-engine evidence is a typed
component and digest manifest only; it must not be reinterpreted as section or package evidence.

Migration to v1 requires rebuilding a domain insertion plan against the current complete note state
and document-flow digest, supplying the complete top-level paragraph logical-ID map, and supplying
one self-contained body payload that passes the closed `subList/p/run/t` validator. The adapter then
seals the exact section, source wrappers, map, payload SHA/length and domain plan before one byte
insertion and complete target readback.

Unknown versions, rich objects, fields, tables, change tracking, line caches, incomplete payloads,
non-BMP marker characters, opaque/locked notes, stale state/flow/section/map/payload or altered plans
fail closed. There is no partial output, inferred conversion, compatibility fallback or automatic
promotion to actual HWPX, Hangul, render, automation, differential, production or product PASS.
