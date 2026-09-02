# P02-08 Exact-2020 Runtime Probe Report

- Completed: 2026-09-02
- Audited source commit: `7c1c214f619b3e3e51b13d7fc61fc2b66f23da6b`
- Task state: `pass_current_pc_local`
- Review: `STRICT / max`, blocker/major/minor `0/0/0`

## Delivered

- Draft 2020-12 request, trace and receipt schemas plus a deterministic Python planner and independent verifier.
- A Windows PowerShell 5.1 parent and x86/STA child harness pinned to the exact current-PC Hancom Hangul 2020 identity before COM activation.
- A disposable synthetic fixture with default-ParameterSet observation, safe undo/redo canaries, pre/post hashes, HWPX save/reopen semantic readback and bounded process cleanup.
- Fail-closed request correlation, locked-input hashes, private no-overwrite output, path/reparse protection, timeout handling and exact-process cleanup rules.
- A policy that executes only the two safe canaries, attempts one non-mutating default read, blocks modal/clipboard/security/external/high-risk candidates and leaves all other candidates not run.
- Restricted evidence that excludes raw Action/ParameterSet/default values, absolute private paths, user-document contents and UI input events.

## Exact current-PC run

- Request ID: `d43ff4a2f90c4b5493f2dd052c404fd9`.
- Product/build/locale/architecture/apartment: Hancom Hangul 2020 / `11.0.0.9136` / `ko-KR` / x86 / STA.
- Executable, target profile, registry and capability-contract identities all matched their pinned SHA-256 values before execution.
- Request: 21,155 bytes, SHA-256 `87972311e87a0087117f1b8bc493458d3eeb584122beeffefb6481b7cb650633`.
- Trace: 40,502 bytes, SHA-256 `7cea2ff287df3de356462df73048b59ec02695521943d23ba0ab73baa9689246`.
- Receipt: 2,329 bytes, SHA-256 `45ae7f63744119e4a67c4ca08c6fb7ee35443024fc5529807a841ca0e09672aa`.
- Disposable output HWPX: 17,940 bytes, SHA-256 `9674ebcb61b01c8733f94e1d54425a400c2cf34dd5a4786dd9b713c69ee2a251`.
- Runtime state `pass`; child exit `0`; timeout false; unexpected window false; remaining Hwp processes `0`.
- Every required phase passed: COM create, version check, document add, fixture insert, default read observation, undo, redo, save, close, reopen, semantic readback, close and quit.
- Undo changed the semantic snapshot, redo restored the original snapshot, and save/reopen was an exact semantic match.

The authoritative request, trace, receipt and disposable HWPX remain local under the Git-ignored [private runtime-probe evidence](evidence/runtime-probes/d43ff4a2f90c4b5493f2dd052c404fd9).

## Candidate dispositions

| Disposition | Count | Meaning |
|---|---:|---|
| `verified` | 2 | Safe disposable undo/redo effects observed and restored |
| `failed` | 1 | Non-mutating default read produced typed, hashed failure evidence |
| `blocked_by_risk` | 17 | Clipboard, modal, workstation, security, external or high-risk scope was not executed |
| `not_run` | 12 | Outside the bounded canary allowlist |
| total candidates | 32 | Complete one-to-one disposition |

The single `failed` disposition is the public `edit.go_to` default-read observation. Its action was not executed. The trace retains only exception type, HRESULT and message hash; the raw automation identifier and error text are not published. This is accepted probe evidence, not a supported-binding claim. The source registry remains unchanged, routing-disabled and unverified until P02-09 applies signed promotion rules.

## Validation

- Independent actual-output verifier: `state=pass`, errors `0`, candidate coverage `32/32`, raw identifier leaks `0`.
- Windows combined P02 Python suite: `47/47` passed.
- Windows PowerShell 5.1 runtime-harness static suite: `31/31` passed and left Hwp process count `0`.
- Python compileall and `pip check` passed.
- The verifier re-read every locked input and evidence file after validation and detected no mutation.

## Preserved boundaries

- No user document, original design ZIP or unrelated local file was opened or modified.
- No network, clipboard, print, password/security, macro or external-service candidate was executed.
- No registry or system setting was changed. The user handled Hancom's local file-access consent; Computer Use performed no click or text input.
- A `verified` probe result is target-build evidence only. It does not by itself enable public routing, production/provider use, another PC or another Hancom version.
- 한글 2022/2024 remain deferred until their installed PCs are available for independent qualification.

## Failed checks retained

No Gate validation failed. The default-read attempt for `edit.go_to` failed on this exact build and is deliberately retained as a typed, hashed negative runtime observation rather than converted into a PASS or hidden.

## Next exact task

Implement `P02-09 Registry signing and drift`: consume the locked source registry plus independently verified P02-08 evidence, apply fail-closed target-scoped promotion without enabling routing, create a deterministic signed manifest and build-to-build drift report, and prove tamper/drift rejection. Recommended reasoning effort: `max`; the P02 phase final Gate also requires `max`.
