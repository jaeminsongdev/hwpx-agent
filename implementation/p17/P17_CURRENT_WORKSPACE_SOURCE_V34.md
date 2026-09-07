# P17 current workspace source qualification v34

Date: 2026-09-07

Scope: exact P06-05 current-PC table-layout v2 source successor only

Decision: **qualified source only; P06-05 actual target Hangul readback/PDF, P06 phase,
production and product PASS remain false**

The v1-v33 qualification contracts remain byte-for-byte unchanged. This v34 layer composes exact
v33 contract SHA-256 `329c111bdce1a401e4b221341d5295e4b730c6bb3b917ebd6fb6a201affab297`
and binds clean implementation commit
`84437dd3df2a1679eda2eed7f4ca8125d5ad2e26`.

Current-host source acceptance run `8b080b651ade4e5d85701bd47bd9e6b6` passed all 11 checks. Its
canonical receipt SHA-256 is
`8ad2a58f77347e7fde94259b36a59beeb35bc7de9e309b4c31800d55fa8a8977`. The twenty-six cumulative
successors, locked/offline 25-member Cargo projection and all runtime/production false claims remain
exactly preserved.

The fifteen bound files introduce the explicit table-layout HWPX v2 successor, typed bounded
inherited `hp:inMargin` readback, exact source/installed-font receipt binding, deterministic
create-new target publication, preview-text refresh, bounded Hangul 2020 runtime wrapper, contract
tamper tests and evidence-bound reports. Immutable v1 remains hash-bound and there is no automatic
profile widening.

The complete `hwpx-package` test suite, targeted Clippy with `-D warnings`, formatting, P06 Python
45/45, table-layout v1/v2 validators, v1/v2 contract tests 8/8 and runtime-wrapper static tests
15/15 pass. The exact target was independently regenerated at SHA-256
`a678588188593c250b33205f1660fef6c301280cd5ae30deb4b6a03f185055bc` with exact table size,
cell sizes and inner margins. No dependency was added.

The P06-04 completion report is source-bound but its ignored local HWPX/PDF artifacts are not
reverified by this source-only qualification. Likewise, the P06-05 target fixture and report do not
prove actual Hangul geometry, wrapping, save/reopen or PDF rendering. Those claims remain false
until a fresh bounded user-approved target readback and visual review pass.
