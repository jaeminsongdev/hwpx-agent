# P05-08 header/footer actual attempts 01-02 diagnostic

- Date: 2026-09-06.
- Scope: fixed synthetic P05-08 fixture on the current licensed Hangul 2020
  `11.0.0.9136` x86 installation only.
- Source implementation commit: `398ebd07e6c1d192fe15d3b0cde0bfc612aa254a`.
- Result: actual Hangul 2020 Gate remains `UNVERIFIED`.
- Reasoning/review risk: MAX / HIGH-STRICT.

## Preserved failed attempts

Attempts 01 and 02 each passed bounded preflight and COM creation, displayed the Hangul window for
user access, and entered `open_input`. Each later received `false` from Hangul's `Open` call. The
runner then failed closed with `HEADER_FOOTER_READBACK_INPUT_OPEN_RETURNED_FALSE`, skipped every
read/save/reopen/PDF phase, quit the exact owned Hwp process, and found zero remaining Hwp
processes. The fixed input digest remained unchanged.

There is no positive receipt recording that the user completed the displayed access request in
either attempt. Consequently these failures do not prove that Hangul rejected the HWPX structure,
and they do not prove a successful authorized open. A new attempt must not be promoted unless the
user explicitly confirms the access clicks and the lifecycle trace passes.

| Artifact | SHA-256 |
|---|---|
| input HWPX | `fda9547afe1326a5f2d9ebcea951a2dcf5345ef554eba846bb1e78e80a7bfe11` |
| render expectation | `43b18547bc2c440200c0a65b30002a865c17465c0ca28d6615e7272002bb175f` |
| attempt01 trace | `f0969ce7c9dfe15c60aa6d56b4874653a1e033ca1f05604ccf4d2ac0be8fa5b9` |
| attempt01 progress | `8c74beb3abf16ec299e6d840244f8ac9d640ae0060b2077c8663abcf0f798e91` |
| attempt02 trace | `348346e6fcce864dc24424f6230d0a24c2903941144137f1b5683bd8cf9dddad` |
| attempt02 progress | `ab73e531af26ceb6ffea0854ee254c75be2c27c09bd760d9468cca6e02161769` |

Ignored evidence is preserved under
`fixtures/target-build/p05-08-current-2020-20260906-v1/`. No user document was opened or scanned.

## Independent official-model diagnostic

The official Apache-2.0 Hancom `hwpx-owpml-model` repository was fetched into an ignored source
cache at the exact policy-locked commit `1453388472c703a4b299a0834f425cdac16644b9` without modifying
its source. Its Win32 Release libraries and sample reader were built with the installed Visual
Studio 2022 Build Tools while explicitly retaining the source project's legacy non-strict string
mode. The x64 configuration's inconsistent precompiled-header setup and the initial strict-string
sample build failures are diagnostic only and are not hidden or called PASS.

The successfully built official `OWPMLTest.exe` has SHA-256
`ca6099590ddd654204f3cec9cc28ef1a91d9466289533b9f7f65b61d97ec55f4`. It opened the exact P05-08
input and emitted a 188-byte synthetic-only text extraction with SHA-256
`3240b3558cd678b80eb212edce3ab6a09774da101eadbf415cf65c1f2ed2d248`. The extraction contains all
four main page markers and the even/odd header/footer markers. This is independent evidence that
the official model can parse the package and section controls; it is not evidence that installed
Hangul 2020 opened, saved, laid out, or rendered the document.

## Next acceptance

Run one fresh bounded attempt only when the user is present to confirm every `접근 허용` prompt.
Then require, in order: lifecycle PASS, input/saved canonical text equality, strict product
header/footer/master-page semantic inspection, four-page PDF verification, original-resolution
visual review, zero owned-process residue, and a redacted tracked qualification receipt. Any
failure remains preserved and cannot be replaced by the official-model diagnostic.

