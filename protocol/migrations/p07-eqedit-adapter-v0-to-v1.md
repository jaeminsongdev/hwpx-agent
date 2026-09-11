# P07 EqEdit adapter v0 to v1 migration

There is no stored v0 EqEdit adapter request, parse result or compiled script to reinterpret or
upgrade in place.

Version 1 introduces `hwpx-agent.eqedit-adapter/v1` and
`hwpx-agent.eqedit-profile/hangul-2020-canonical-v1`. A parse caller must submit both versions and
one bounded script. A compiler caller supplies an already admitted P07-01 `MathAst`; the compiler
returns only a canonical script that reparses to the same semantic AST.

Legacy or previously tolerated strings are not grandfathered. Unsupported/ambiguous syntax,
relation chains, bare vertical bars, unmodeled visual spacing/style controls, removed
`FROM`/`TO`/`SCALE`/`PHANTOM` commands, ragged grids and unrepresentable AST forms MUST fail closed.
A caller MUST NOT rewrite, escape, infer multiplication, strip style controls or substitute text or
an image on the adapter's behalf.

The v1 source qualification is exact to the recorded Hangul 2020 build but proves only a finite
dialect component. It MUST NOT be migrated into a native HWPX, Hangul execution, save/reopen,
readback, editor, render, automation, production or P07 PASS; those are separate P07 Gates.
