# P06-06 current-PC Hangul 2020 formula source and adapter report

Date: 2026-09-07

Decision: **PASS for the actual source capture and exact adapter component; P06-06 remains in
progress**.

## Actual source capture

The bounded worker created a new synthetic one-row, three-column table in the licensed x86 Hangul
2020 build `11.0.0.9136`, wrote operands `17` and `25`, inserted the sum formula using Hangul, saved
HWPX, reopened it, verified stable visible text, exported PDF, closed the document, and quit.
The user approved only Hangul's file-access prompts. No user document was opened, no network or
system setting was touched, and no Hwp process remained.

The source HWPX SHA-256 is
`d968cae419a3754b1dc65eb845f9d1d6bf8bbb486736359cd9b838a78e47d38f`; the PDF SHA-256 is
`adbd88f65b0a31ab769c0a277d340a1ffcb8165a93b263c557eaff4d1baeab26`; the trace SHA-256 is
`2bb67d3d53611dcbfb70ab014e5f3499bcc44885b7ce5ed024798e8abd10a1d7`. The pre-save and reopened
visible-text SHA-256 is
`b3cc193c31f1bd7402576b13822eb4025dc49893dd7f4de84a8b21de8e074265`.

## Exact adapter

The source inspection found one formula field in C1. The native directional left-sum is lifted to
the locale-neutral pure AST `SUM(A1:B1)`, with decimal result `42` retained only as an
`unverified` cache. The source section SHA-256 is
`5d106d507b899dbbff1f0b790e975889d88cc9974f89d4c4163b8f6f6afa0de8`; canonical formula-cell
SHA-256 is `49453797e05490cd92a1dd9a9a58bb4156b346c06726977e86c5e1454089f3f8`.

The lowerer accepts only a complete relative left-prefix `SUM` range for the same owner and exact
grid. It owns the bounded formula/cache/display text slots, edits only the three slots required for
cache publication, reparses its output, exact-compares the typed formula cell, and verifies a digest
over every unowned byte. Unknown syntax, parameter drift, ID mismatch, duplicate or missing cells,
non-unit spans, non-left-prefix ASTs, unsupported formats and unverified-cache shape drift reject.
Native command strings are not exposed by the public API or Debug output.

Eight integration tests pass, including exact lift, deterministic lower, unowned-byte preservation,
negative decimal rendering, identity mismatch, namespace/grid drift, unsupported formula/cache and
finite limits. The read-only actual-source adapter check also passes and its identity lowering is
byte-exact.

## Gate boundary

Contract `hwpx-agent.p06-06-table-formula-hwpx-contract/v1` records actual source-capture PASS and
adapter-component PASS only. The cache is not oracle verified. Row/column structural differential,
an altered product target, and licensed Hangul 2020 target save/reopen remain `NOT_RUN`; therefore
P06-06 and P06 are not complete. No arbitrary document, another PC, Hangul 2022/2024, production or
whole-product claim is made.
