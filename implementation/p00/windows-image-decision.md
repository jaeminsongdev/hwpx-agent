# P00-02 Windows Image Decision

- Decision state: `current_pc_development_baseline_accepted`
- Current-PC Gate state: `pass_scoped`
- Portable/production worker state: `deferred_disabled`
- Decision date: 2026-09-01

## Decision

By direct user instruction, active implementation and debugging use this current physical PC and its exact Hangul 2020 installation only. A separate clean image is not required for the current local development Gate. The current host is instead pinned by a privacy-preserving machine binding, OS build/UBR, exact product executable and Registry32 binding, font, PDF printer, oracle receipt, source locks, and evidence hashes.

The original clean immutable worker-image contract is retained only for a future portable worker, another PC, production, or distribution scope. It is not claimed as complete. Hangul 2022/2024 qualification starts later on the PCs where those versions are installed, with independent target evidence so their shared ProgID cannot mix receipts.

## Current host observation

- OS caption: Windows 11 Pro.
- Display version: `25H2`.
- Build: `26200.8875`.
- OS architecture: x64.
- Locale/UI culture: `ko-KR`.
- Current session: interactive session ID 1.
- Current host baseline digest: `7fbf6559fc3372b9da6c0b0ca53d9f4eb78b76a79df248c37ff009c13376adc0`.
- Baseline classification: mutable current development PC; `clean_image_claimed=false`.
- Clean-image install/run smoke: not run and outside the current-PC scope.

The current host has a valid no-document 2020 diagnostic probe and generated-document smoke. Run `98798b1801314a5e9bebf0f2505bc763` created a synthetic document, saved HWPX, closed, reopened, matched the exact normalized text, exported a one-page PDF through Hancom PDF, invoked `Quit()`, and left zero `Hwp.exe` processes. The HCR Batang fixture had zero substitution. The current-host manifest and independent verifier bind those results to the live environment without launching Hangul again.

## Current-PC baseline policy

- Execution still requires the current interactive desktop; Session 0 and unattended service UI automation remain unsupported.
- The verifier fails closed if Windows build/UBR, machine binding, exact `Hwp.exe`, Registry32 registration, HCR Batang, Hancom PDF binding, accepted evidence, or scope claims drift.
- The baseline does not store computer name, user name, raw MachineGuid, license key, or a user document.
- Product or Windows updates require regenerating and reviewing the baseline before further oracle use.
- Network, production providers, server/VM, CI, customer, and distribution paths remain disabled.
- Evidence from this host cannot qualify another host or another Hangul release.

## Deferred portable-worker work

If the user later opens a portable worker, production, or distribution scope, provision and seal an independently qualified environment and repeat target identity, bounded automation, document save/reopen/readback/PDF, font substitution, and cleanup evidence. That future work is not a blocker for P01 development on the current PC.

Next exact action after the scoped P00 audit: start the P01 repository/security scaffold on this current PC at reasoning effort `xhigh`.
