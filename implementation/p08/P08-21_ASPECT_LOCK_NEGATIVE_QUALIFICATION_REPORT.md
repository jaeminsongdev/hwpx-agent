# P08-21 aspect-lock negative qualification report

## Result

Result: `CAPABILITY_UNAVAILABLE_FOR_TARGET` for `OBJ-044` on the exact current target.

The pinned Hancom OWPML model exposes object identity, wrapping, locking and `sz` width/height
fields including `protect`, but no persistent aspect-ratio-lock field. Four pinned official
automation PDFs contain no exact `AspectLock`, `KeepRatio`, `AspectRatio`, or `LockAspect` binding.
Their `ProtectSize` references are not admitted as an equivalent.

The installed Hangul 2020 object-property UI XML contains exactly one fixed-size control and no
aspect/ratio/proportion control token. This installed surface matches the official model and
automation negative result. The target executable and UI XML identities are bound by SHA-256.

## Claim boundary

This is exact official-source and installed-surface negative evidence. It is not an executed HWP
runtime test: no HWP process was launched, no action ran, and no document was opened, created, or
mutated. `OBJ-044` therefore remains unit-level and non-green, with direct lowering fail-closed and
automation unavailable with reason.

`actual_target_runtime=false`, `direct_hwpx_mapping=false`,
`automation_runtime_binding=false`, `differential=false`, `row_green=false`,
`p08_complete=false`, `production_ready=false`, and `product_complete=false`.

## Next work

Treat the `OBJ-044` mapping investigation as closed for this exact build. Continue P08 automation
binding/runtime and differential work only for capabilities with an independently qualified exact
target surface. Do not substitute size protection for aspect locking.
