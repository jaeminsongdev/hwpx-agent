# P06-06 Hangul 2020 formula source capture

- State: prepared, not executed
- Target: licensed Hangul 2020 `11.0.0.9136` x86 on the current PC
- Worker: `tools/create-hancom-2020-formula-source.ps1`
- Watchdog: `tools/run-hancom-2020-formula-source.ps1`
- Static tests: `tests/Test-Hancom2020FormulaSource.ps1`

## Source boundary

The locked P02 automation record identifies `TableFormulaSumHor` as the parameter-set-free
horizontal-sum action. The private worker creates only a new 1-by-3 table, writes the fixed operands
`17` and `25`, and asks Hangul to author the third-cell formula. It does not invent a
`FieldCtrl.Command`, packed command syntax, field IDs, cache, or number-format code.

The worker is pinned to the exact local build and executable digest, activates its newly created
document, checks ordered visible operands/result before save and after reopen, and emits only hashes
and booleans. It never scans or opens a user document.

## Diagnostic and cleanup boundary

The wrapper launches the worker in 32-bit STA PowerShell with a configurable 30-to-900-second
watchdog. A bounded append-only progress journal records only phase, state, process IDs and privacy
flags. A success receipt must prove the two operands, Hangul-authored action, pre-save and reopen
visible result, equal semantic text digests, bounded HWPX/PDF artifacts and a valid PDF signature.

On timeout, cleanup may stop only an `-Automation -Embedding` Hwp process created after this run
started, in the same Windows session, with the exact expected executable SHA-256. A refused cleanup,
identity mismatch or residual Hwp process leaves the receipt failed or unverified. The scripts do
not perform UI input, network access, module registration or registry/system-setting writes.

## Evidence state

Windows PowerShell 5.1 static/preflight checks pass 21/21 and PSScriptAnalyzer reports zero warning
or error findings. The worker has not been run because P06-04 attempt04 still owns the live Hangul
automation process. Prepared code and static checks are not actual formula evidence. HWPX field
shape, command grammar, cached value, number format, recalculation and P06-06 completion all remain
unverified until a fresh bounded run and offline structural inspection pass.
