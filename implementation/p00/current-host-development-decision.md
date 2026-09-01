# P00 Current-PC Development Scope Decision

- Decision date: 2026-09-01
- Authority: direct user instruction
- State: `accepted_current_pc_only`
- Target: Hancom Hangul 2020 `11.0.0.9136` x86

## Decision

The active implementation and debugging scope is this current physical PC and its installed genuine Hangul 2020 only. Hangul 2022 and 2024 work resumes later on PCs where those exact products are installed. A separate clean Windows image or another PC is not a prerequisite for current development.

This decision distinguishes two gates:

1. **Current-PC local development Gate** — may pass with an exact, privacy-preserving host baseline plus the already accepted runtime/document/font/PDF evidence.
2. **Portable worker, another PC, another version, production, or distribution Gate** — remains disabled and receives its own target-specific evidence later.

The original design package's clean-image requirement remains a product-hardening input. It is not reported as completed and is not silently weakened into a clean-image claim. It is explicitly outside the user-authorized current-PC development scope.

## Accepted current-PC evidence

- Exact `Hwp.exe` file version and SHA-256 match `11.0.0.9136` x86.
- Registry32 `HWPFrame.HwpObject.2` points to the accepted executable.
- The bounded runtime probe passed in STA and exited with zero remaining `Hwp.exe`.
- Synthetic run `98798b1801314a5e9bebf0f2505bc763` passed HWPX save, close, reopen, exact normalized readback, PDF export, `Quit()`, and cleanup.
- HCR Batang substitution is zero for the fixture and the PDF embeds the font.
- Hancom PDF is present with the pinned driver/profile evidence.
- Source lock passes in PowerShell 7 and Windows PowerShell 5.1.
- The current host baseline digest is `7fbf6559fc3372b9da6c0b0ca53d9f4eb78b76a79df248c37ff009c13376adc0`.

The baseline stores no computer name, user name, raw MachineGuid, license key, or user document. The stable machine binding is a one-way SHA-256 value, and the manifest explicitly records `clean_image_claimed=false`.

## Authorization boundary

Passing this scoped Gate authorizes only repository/scaffold and subsequent local product development on this PC. It does not authorize or claim:

- Hangul 2022, Hangul 2024, or any later release support;
- behavior on another PC;
- clean or immutable Windows image qualification;
- commercial, organization-internal, hosted, server, VM, CI, customer, or distribution use;
- external provider activation.

Any target or scope change reopens the applicable qualification and license decisions. Evidence from this PC cannot be promoted to another version or host.

## Revalidation

Run both commands from the project root with Hangul closed:

```powershell
.\implementation\p00\tools\New-CurrentHostBaseline.ps1
.\implementation\p00\tools\Test-CurrentHostBaseline.ps1
```

The verifier fails closed on baseline digest change, evidence tampering/path traversal, Windows build drift, Hangul executable drift, font drift, PDF printer binding drift, another Windows installation, scope overclaim, or a running `Hwp.exe` process.
