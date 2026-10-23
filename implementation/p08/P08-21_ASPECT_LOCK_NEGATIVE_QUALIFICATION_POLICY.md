# P08-21 aspect-lock negative qualification policy

## Scope

This task qualifies whether `OBJ-044` (`obj.aspect_lock`) has an exact persistent HWPX field or
an exact automation binding on licensed Hancom Hangul 2020 `11.0.0.9136` x86, `ko-KR`, on the
current PC. It does not infer support from a similarly named or visually adjacent control.

## Admission rule

An implementation may be admitted only when the pinned official OWPML model contains a persistent
aspect-ratio-lock field or the pinned official automation archive contains an exact binding whose
semantics can be independently read back. The `sz.protect` field and installed `ProtectSize`
surface mean fixed width and height; they are not an aspect-ratio lock for a later resize. Rectangle
corner `ratio` is also unrelated and is rejected as an equivalent.

When neither route exists, the exact-target result is
`CAPABILITY_UNAVAILABLE_FOR_TARGET`. Direct lowering must remain fail-closed, automation routing
must remain disabled, and the catalog contract remains visible rather than being silently removed.

## Evidence boundary

The public qualification binds the exact target executable, installed object-property UI XML,
pinned Hancom OWPML files, and pinned automation PDFs by SHA-256. The validator rechecks the live
installed executable and UI XML on this PC and rejects target drift. It also rejects any promotion
to actual runtime, direct mapping, automation binding, differential, green row, P08 completion,
production readiness, or product completion.

No HWP process, document, action, registry setting, or system setting is touched by this negative
qualification. Official repositories are used as read-only sources. User documents are outside
scope.
