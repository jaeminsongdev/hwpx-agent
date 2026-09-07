# P06-05 current-PC font-metric receipt policy

Date: 2026-09-07

Scope: exact installed-font measurement and verified solver-input component for one named synthetic
table fixture on the current PC. It narrows a previously open P06-05 prerequisite. It is not actual
Hangul layout or PDF-render evidence and does not close P06-04, P06-05 or P06.

## Measurement boundary

`measure-hancom-2020-layout-font.ps1` admits only the current licensed Hangul 2020 executable build
`11.0.0.9136` x86 and exact SHA-256, plus the exact installed private font file `HANBatang.ttf`
(28,412,796 bytes, fixed SHA-256). The font is loaded directly into a GDI+
`PrivateFontCollection`; it is never copied, embedded, changed or published.

The same exact font file reports the canonical Hangul family name under PowerShell 7 but the
localized name `HCR Batang` under Windows PowerShell 5.1. Those two names alone are accepted under
the fixed font-file SHA-256, and the receipt always emits the canonical name. Runtime-dependent
dimension drift remains rejected by the fixed measurement-set digest.

The receipt JSON escapes non-ASCII code units as standard `\uXXXX`. This preserves the canonical
family value while keeping the file safely parseable by Windows PowerShell 5.1, whose default
`Get-Content` decoding otherwise misreads UTF-8 without a BOM.

The profile measures four named synthetic cell texts at 10 pt and 96 dpi with
`GenericTypographic`. It converts pixels to integer micrometers with explicit away-from-zero
rounding. Two independent passes must be byte-identical per cell before a new run directory and
receipt are atomically created under the ignored `artifacts/p06/font-metric-runs` root. The receipt
contains cell IDs, text digests and dimensions but no raw text or absolute path.

## Admission and solver binding

The Python verifier independently checks the artifact boundary, duplicate JSON keys, exact local
Hwp/font identities, fixed profile, four ordered cell identities, canonical cell digest, finite
positive dimensions and every false privacy/completion claim.

`CurrentFontMetricReceipt` repeats the strict bounded parsing in the Rust product path. It requires
the canonical cell digest to equal both the receipt field and the separately qualified fixed
measurement-set SHA-256. This prevents a modified measurement plus recomputed self-digest from
being promoted. Only a fully admitted receipt yields `FontMetricStatus::Verified`, exact profile ID
and the SHA-256 of the entire admitted receipt as solver evidence. Callers may add only bounded,
nonnegative margins; missing cells and checked outer-width overflow fail closed.

The current source produced exact ignored run `4b9b0cac589946918140abc4a12c1be1` under Windows
PowerShell 5.1 (receipt SHA-256
`c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab`) and run
`cb76a3477e2c4bcdac78b6647e187acf` under PowerShell 7 (receipt SHA-256
`329d424445c463bae9c84215cc627a1e9b1b1e3287de6f8d1eb01439ccdde6f3`). Both independently yielded
measurement-set SHA-256 `96e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9`.
Each runtime's suite passed 16/16, the independent Python verifier passed, and the bounded Rust
product example consumed both exact ignored receipts successfully. No Hwp process was created by
measurement.

## Privacy and side effects

No user document is opened. The generator and verifiers perform no UI click or typing, no external
network request, no registry or system-setting write, and no font redistribution. Publication uses
create-new semantics and rejects a reused run ID. Debug formatting redacts cells and text.

## Not claimed yet

GDI+ typographic measurements are verified inputs for the deterministic table solver; they are not
proof that Hangul 2020 lays out or paginates the same text identically. Actual named-fixture HWPX
lowering, Hangul save/reopen semantic readback and signed PDF visual comparison remain required.
Arbitrary text, fonts, sizes, DPI, user documents, another PC or version, production, P06-04,
P06-05, P06 and product completion remain unclaimed.
