# P07-04 EqEdit parser/compiler policy

## Decision

Status: `component_only / unit_passed`.

P07-04 establishes `hwpx-agent.eqedit-adapter/v1` and the finite
`hwpx-agent.eqedit-profile/hangul-2020-canonical-v1` profile in `equation-engine`. It parses one
profile-qualified EqEdit script to the P07-01 `MathAst`, compiles an admitted `MathAst` to a fully
grouped canonical script, and accepts compiler output only after parsing it back to the same
semantic AST. It does not create or modify an HWPX equation object.

## Exact current-target source qualification

The profile is tied only to this PC's licensed Hangul 2020 `11.0.0.9136` x86 ko-KR target. The
installed `Hwp.chm`, EqEditor command/data XML and `EqEditor.dll` were read without modifying the
installation. Help pages were decompiled into a disposable temporary directory for inspection;
that directory is not a committed or required validator input. Artifact sizes and SHA-256 values,
the extraction method and the public Hancom format/help references are frozen in
`evidence/p07-04-eqedit-source-qualification.current-2020.v1.json`.

The installed help identifies grouping, quoted text, row/column separators, current command
families and the fact that legacy `FROM`, `TO`, `SCALE` and `PHANTOM` are unused. The current P06-07
fixture/report independently supplies one exact EqEdit script that survived a licensed Hangul 2020
save/reopen lifecycle. P07-04 admits that script, but this predecessor fact is only source-profile
evidence: the new parser/compiler has not itself been executed through Hangul.

## Finite parser profile

- Numbers, at-most-nine-character identifiers, nonempty quoted text and braces are typed without
  retaining raw source in the result. Explicit arithmetic, relation, set and logic commands use a
  fixed precedence table. Relation chains are rejected.
- `OVER`, `_`, `^`, `SUP`, square/nth roots, fixed functions, Greek/fixed symbols, accents,
  overline/underline, `SUM`, `PROD`, `lim`, and all six one/two/three-dimensional ordinary/contour
  integral tokens map to distinct AST semantics.
- `MATRIX`, `PMATRIX`, `BMATRIX`, `DMATRIX`, `CASES`, `PILE`, `BINOM`/`CHOOSE`, and matched
  `LEFT`/`RIGHT` delimiters are supported. Grids must be nonempty and rectangular. `VERT` is
  admitted only as the set-builder separator inside the exact `LEFT { ... RIGHT }` form.
- Adjacent primaries are retained as an ordered `MathAst::Row`; they are never guessed to mean
  multiplication or function application. Callers requiring multiplication use `TIMES`.
- Bare vertical-bar pairs are lexically ambiguous and fail closed; canonical bars use
  `LEFT | ... RIGHT |` or `LEFT || ... RIGHT ||`. Backslash changes native font style, while `~`
  and backtick insert visual space, so these unmodeled characters fail closed instead of being
  discarded. The four removed legacy commands also fail closed.
- A derivative is recognized only from the compiler's versioned grouped quotient pattern, with an
  exact positive order sum. Other quotient typography remains an ordinary fraction.

This is an exact finite profile for the qualified build, not a claim to accept every EqEdit string
that the editor may display or preserve.

## Compiler and preservation boundary

The compiler emits a deterministic, fully grouped form and checks
`MathAst -> EqEdit -> MathAst` semantic equality internally. Fractions and division remain
distinct, `Script` power and `Apply(Power)` remain distinct (`^` versus `SUP`), integral
multiplicity/contour state is preserved, and matrix/case/aligned/set/derivative structure is never
lowered to text or an image.

Only profile-safe ASCII identifiers and text requiring no undocumented escape are emitted. Typed
styles, named functions, double-bar matrices, permutations, annotations with payload, unsupported
operators and unrepresentable values fail closed. No partial script, substitution, raw XML or image
fallback is returned.

Source/script byte size, token count, individual token bytes, parse depth, compile depth and result
serialization have finite defaults and hard ceilings. Parse receipts bind versions, source SHA-256,
byte/token counts and the complete AST. Compile receipts bind versions, semantic/script SHA-256,
byte/token counts and the complete emitted script. Debug and typed errors redact source, script,
values, spans, hashes and AST payloads.

## Gate boundary

This component does not claim full EqEdit coverage, arbitrary legacy-script preservation,
EquationNode integration, direct HWPX writing, package mutation/preservation, native equation
creation/readback, execution of this engine in Hangul 2020, save/reopen, editor smoke, page layout,
rendering, automation, differential, another Hangul version, P07 completion, production readiness
or product completion. Those states remain `false` / `not_run`.

Reasoning level: `max`. P07-05 native equation lowering and every target/runtime Gate remain at
`max`.
