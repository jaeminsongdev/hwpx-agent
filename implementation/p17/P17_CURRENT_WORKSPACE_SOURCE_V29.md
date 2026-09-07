# P17 current workspace source qualification v29

Date: 2026-09-07

Scope: P06-05 current-PC installed-font metric receipt and solver binding successor only

Decision: **qualified source and named installed-font measurement boundary only; no actual Hangul
renderer, P06-04/P06-05 card, phase, production or product PASS**

The v1-v28 qualification contracts remain byte-for-byte unchanged. This v29 layer composes exact
v28 contract SHA-256 `55fb75ca03e7331b246d3cc309df84455fa0a32b087a23b73bc7b24ad011091e`
and advances the source view to clean commit
`42aba1cb2539cd5b798c783ac81fb23796d3980e`.

The source-check guard itself is an explicit implementation source in this layer. Therefore v29
does not re-evaluate the v1 guard identity against successor bytes; it validates the immutable v28
contract by exact SHA-256, then validates the new guard, commit blobs and current acceptance receipt
independently. Historical qualification files remain untouched.

Current-host source acceptance run `99fd2af086e14d3e9d97daa2f01b6408` passed all 11 checks. Its
canonical receipt SHA-256 is
`41a03372ef614af2c4691dfb7a70005e7237dbed4983c694fb3de7f4fbcbdfa9`. The twenty-six cumulative
successors are exact, and the locked/offline 25-member Cargo projection SHA-256 is
`14159fe60a20ba6ee8a4402f1c4c6928a3b2298f44a06c4c8c603c14fff4334f`.

This layer binds fifteen exact files: the product dependency/export, strict Rust receipt adapter,
six tests, bounded actual-receipt consumer, PowerShell generator and static tests, independent
Python verifier, policy, private contract, migration, validator and the updated source-check
guard. `serde` and `serde_json` are now exact product dependencies and are absent from the dev-only
section.

The current source produced one ignored Windows PowerShell 5.1 run and one ignored PowerShell 7
run. Both independently resolved the exact installed `HANBatang.ttf`, produced the same fixed
four-cell measurement-set SHA-256, passed 16/16 checks, passed the Python verifier and were consumed
by the Rust product adapter. Raw fixture text and paths are absent, no user document was opened, no
font was copied, no UI/network/registry action ran, and measurement created no Hwp process.

The dedicated Rust receipt tests passed 6/6, all `hwpx-package` targets passed, all P06 Python tests
passed 33/33, the full Rust workspace passed with only the pre-existing isolated-PostgreSQL test
explicitly ignored, and workspace formatting and warning-denied Clippy passed.

This is verified GDI+ typographic input for the deterministic solver, not evidence that Hangul 2020
renders, wraps or paginates identically. P06-04 still waits on its already running licensed Hangul
2020 source-generation approval. Named-fixture HWPX lowering, Hangul save/reopen semantic readback,
PDF comparison, P06-04/P06-05 completion, another PC/version, production and product completion
remain open.
