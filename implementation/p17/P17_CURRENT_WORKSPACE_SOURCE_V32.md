# P17 current workspace source qualification v32

Date: 2026-09-07

Scope: bounded P06-06 Hangul 2020 formula source-capture tooling successor only

Decision: **qualified source tooling only; the capture has not run and HWPX formula shape, formula
semantics, cache, lowering, Hangul 2020 oracle, P06-06/P06 phase, production and product PASS remain
false**

The v1-v31 contracts remain byte-for-byte unchanged. This v32 layer composes exact v31 contract
SHA-256 `dcda4b3ea4a8c8d5ce858ef1cb7054c1f3730a8b4be49fd322841a754f75dec7`
and binds clean implementation commit
`e28220e7f50b0556fc028a1e45d9addfd70619a7`.

Current-host source acceptance run `f043ce35eb9a4d68bf1da27ee1c3ef3a` passed all 11 checks. Its
canonical receipt SHA-256 is
`cbc408de730fc415574179c7161b944e5e380ca5a42270c76c781f85aad6ab2e`. The twenty-six cumulative
successors, locked/offline 25-member Cargo projection and all runtime/production false claims remain
exactly preserved.

The four bound files add an exact-build x86 formula source worker, a 30-to-900-second watchdog,
privacy-safe progress and terminal receipts, static/preflight tests and a diagnostic policy. The
worker uses the documented parameter-set-free `TableFormulaSumHor` action on a new fixed 1-by-3
table instead of inventing target formula commands or field identifiers. Timeout cleanup is limited
to a same-session automation process created by the run with the expected executable digest.

Windows PowerShell 5.1 checks pass 21/21, the P06 Python contract suite passes 37/37 and
PSScriptAnalyzer reports zero warning or error findings. No dependency was added.

The worker was not executed because P06-04 attempt04 still owns the live Hangul automation process.
Prepared code, official action documentation and static tests do not prove a generated HWPX formula
field, recalculation or render behavior. A fresh bounded licensed Hangul 2020 run and strict offline
field inspection are required before target adapter implementation or any P06-06 completion claim.
