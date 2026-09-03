# P05 actual Hangul readback diagnostics

## Current scope

This harness is limited to the current PC's licensed Hangul 2020 build `11.0.0.9136`, x86 COM
registration and executable SHA-256 fixed in the scripts. It opens only a caller-named disposable
fixture whose expected digest is supplied. It never scans user documents, registers a security
module, changes Registry/system settings, uses the network, or automates UI click/type. The user may
manually approve Hangul's access prompt.

Hangul 2022 and 2024 are not covered by this evidence. When their PCs become available, each release
gets a separate exact profile, executable identity, wrapper schema and run directory. A successful
2020 run must not be reused as cross-version proof.

## Evidence set

Every future P05 actual run is correlated by three files inside the disposable fixture directory:

- the no-overwrite HWPX output;
- one terminal JSON trace with input/output digests, text digests, phase states and privacy markers;
- one append-only `*.progress.jsonl` journal with schema
  `hwpx-agent.p05-hancom-readback-progress/v1`.

Progress events contain only sequence, UTC time, worker/Hwp process IDs, phase, state and a constant
`raw_document_text_present=false`. They contain no document path, text, raw XML, COM parameter value,
secret or user identity. The important boundary events are `open_input:running/pass`,
`save_as_hwpx:running/pass`, `reopen_output:running/pass` and `terminal`. A missing terminal trace can
therefore still be diagnosed from the last durable progress event without guessing where COM hung.

The section/column and header/footer wrappers additionally accept an optional new `.pdf` path in the
same disposable fixture directory. When requested, the reopened output is exported with the
already-qualified `IXHwpDocument.SaveAs/PDF` path. The worker rejects an existing, linked, empty,
non-PDF-signature or larger-than-32-MiB result; the watchdog independently correlates its SHA-256,
length, boolean state and export method. A timeout or partial file never becomes render PASS.

`verify_p05_hancom_pdf.py` performs the next independent layer. It binds the PDF and exact
`pdftoppm` executable by SHA-256, rejects encryption and out-of-bound inputs, checks page count,
rotation, MediaBox dimensions and fixture-only required/forbidden text, then renders every page at
144 DPI. Each complete PNG is decoded with Pillow, checked against the physical page dimensions and
recorded by size and SHA-256. The expectation, trace and new render directory must be direct children
of the named disposable PDF directory. The terminal JSON contains hashes and measurements but no
document text or path. The input PDF and renderer are rehashed after rendering to close mid-run
mutation, and the PNG directory must contain exactly the expected pages. Automated PASS still
requires a human/agent visual review of every generated PNG before a layout Gate can close.

On the current PC this verifier uses the Codex bundled Python runtime reported by
`load_workspace_dependencies`, with `pypdf 6.10.0`, `Pillow 12.3.0` and that bundle's exact
`pdftoppm.exe`. The CLI requires the expected renderer SHA-256, and its trace also records the
Python executable, verifier source, expectation and renderer SHA-256 values plus both Python package
versions. These packages are diagnostic-only dependencies, not HWPX Agent product-runtime
dependencies. Validate changes explicitly with the bundled Python executable:

```powershell
& $BundledPython -m unittest implementation.p05.tests.test_verify_p05_hancom_pdf
& $BundledPython -m py_compile implementation\p05\tools\verify_p05_hancom_pdf.py
```

## Bounded execution and cleanup

`invoke-hancom-2020-bounded-readback.ps1` runs the x86 STA engine in a separate hidden PowerShell
process. The default timeout is 300 seconds and the accepted range is 30–900 seconds so a manual
access prompt has time to be handled but cannot wait forever.

After exit or timeout, cleanup is allowed only for an `Hwp.exe` that:

1. is in the same interactive Windows session;
2. was created after this run began;
3. has the exact expected executable SHA-256; and
4. has the COM server command line `-Automation -Embedding`.

Any non-matching process is refused rather than killed, and the result becomes `unverified` if an Hwp
process remains. Timeout, output-drain failure, missing/invalid inner trace, child failure and cleanup
uncertainty have separate stable task-prefixed error codes. The input hash is checked again and no
existing output, trace or progress file is overwritten.

## Remote-PC diagnostic workflow

For a later 2022/2024 machine, first run the P00 offline discovery/probe bundle and bind the returned
exact version, architecture, ProgID and executable digest into a new target profile. Copy only a
named disposable fixture plus its expected digests and the version-specific signed/hashed diagnostic
bundle. Return the terminal trace, progress journal, output digest and product semantic-inspection
result. Do not return user documents or raw document text.

If the last progress event is `open_input:running`, the operator handles only the visible Hangul access
prompt and reruns in a new empty run directory after the watchdog has cleaned the owned process. If a
trace exists, its exact error code controls the next action; evidence files are preserved and never
rewritten to manufacture a pass.
