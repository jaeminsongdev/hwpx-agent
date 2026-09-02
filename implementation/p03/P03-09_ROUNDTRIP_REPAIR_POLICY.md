# P03-09 Round-trip and repair policy

- State: implemented for current-PC core; exact 한글 2020 oracle required for Gate closure
- Contract: `hwpx-agent.roundtrip-repair/v1`
- Source capabilities: P03-01 through P03-08
- Product boundary: deterministic round-trip verification and non-mutating repair diagnosis
- Current runtime target: licensed 한글 2020 exact build `11.0.0.9136`, x86 STA

## 1. Round-trip admission

`RoundTripVerifier` accepts only an explicit reader and finite `RoundTripLimits`. It applies the bounded ZIP reader, closed package graph, preservation report, current 한글 2020 typed ID/reference profile and a no-op preserving patch transaction before building both writer modes. Failure at any layer returns a typed error and no partial evidence.

Success evidence contains counts, writer SHA-256 values, same-mode determinism booleans and the untouched-policy violation count. It never exposes document bytes, XML values, paths or raw text. Evidence is returned only when:

- both artifacts pass their internal integrity checks;
- repeated preserving output has the same SHA-256;
- repeated normalized output has the same SHA-256;
- preserving metadata states only the source properties actually available;
- normalized metadata is explicitly marked normalized;
- every untouched part keeps the source expanded-byte SHA-256;
- writer reports and the patch artifact have identical part cardinality;
- graph/preservation/typed-ID counts agree across validation layers.

Preserving and normalized modes remain separate. A successful normalized result is never represented as source-byte preservation.

## 2. Repair diagnosis boundary

P03-09 repair is diagnosis, not document mutation. `RepairDiagnostic` maps a stable error code to:

- one layer: archive, package graph, preservation, ID/reference, patch, publication or internal evidence;
- one repairability class: safe retry, regenerate from validated source or not automatically repairable;
- one recommended action: use a new destination, review finite limits, retry from validated source, inspect a published artifact, replace/restore the source or stop and report.

Diagnostics contain no source value, archive path, XML text, document text or exception message. The verifier does not rewrite malformed input, delete a published artifact, overwrite a destination, loosen limits automatically or continue after evidence disagreement. Full repair planning and controlled mutation belong to P04 and later phases.

## 3. Deterministic corpus and fuzz baseline

The committed deterministic corpus contains 128 valid synthetic packages with varied entry order, compression, comments and semantic attributes. Every package must produce zero untouched violations and repeatable preserving/normalized hashes. A platform-independent semantic corpus digest and a separate aggregate of all preserving/normalized writer hashes detect silent corpus or writer drift. The writer aggregate must be identical on Windows and Linux; ZIP creator system and regular-file permissions are pinned rather than inherited from the host.

A second bounded corpus replays 128 one-byte mutations and 128 truncations twice. Identical bytes must produce identical success evidence or identical error code and diagnostic. No mutation or truncation may return partial evidence or panic.

The `cargo-fuzz` target admits at most 1 MiB per input and calls the production verifier and diagnostic mapping. Corpus and crash artifacts stay outside Git. A fuzz smoke is evidence only for the executed run count and configuration; it does not prove absence of all parser or writer defects.

## 4. Exact 한글 2020 oracle

The runtime oracle receives one explicit disposable workspace and opens exactly these fixed files:

- `fixture-0/preserving.hwpx`
- `fixture-0/normalized.hwpx`
- `fixture-1/preserving.hwpx`
- `fixture-1/normalized.hwpx`

It performs no recursive search and never opens a user document. The parent pins a manifest of file sizes and SHA-256 values, resolves the 32-bit COM server through `Registry32`, requires executable version `11.0.0.9136` and executable SHA-256 `7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce`, and refuses a pre-existing `Hwp.exe` process.

Each file is opened in a fresh x86 PowerShell STA child. The child verifies the file hash again, opens without saving, extracts `UNICODE` text, canonicalizes NUL/newline/NFC representation and records only its SHA-256 and UTF-8 length. Preserving and normalized text evidence must match per fixture. Each child closes without saving and calls `Quit`; timeout or unowned/residual processes fail closed.

The private receipt is created once inside the disposable workspace and contains no absolute private path or raw document text. Computer Use may be used only to inspect screenshots. File-access consent clicks are performed by the user; any repair, recovery or format-conversion prompt blocks the Gate rather than being silently accepted.

## 5. Non-claims and future boundary

This contract does not claim visual/render equivalence, exact raw compressed-stream identity, repair mutation, save fidelity after a Hancom edit, arbitrary user-document completeness, OS/hardware power-loss durability, or 한글 2022/2024 compatibility. Those require later phase work or exact testing on a PC where the target version is installed.

The P03 phase Gate requires all P03-01 through P03-09 regression suites, the current exact 한글 2020 oracle, Linux core validation, a clean-clone bootstrap, security/dependency checks and a strict code review. Missing actual-runtime evidence is `NOT_RUN`, not a synthetic pass.
