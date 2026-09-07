# P06 current font metric receipt v0 to v1

P06-05 introduces private receipt profile
`hwpx-agent.p06-05-current-font-metric-receipt/v1`. There was no accepted v0 font-metric receipt,
so no earlier measurement or arbitrary font input is migrated automatically.

The v1 boundary is deliberately narrow: the current licensed Hangul 2020 build `11.0.0.9136` x86,
the exact installed private `HANBatang.ttf` identity, 10 pt at 96 dpi, GDI+ typographic measurement,
and four named synthetic cells. Two independent passes must agree. The compact canonical cell array
must hash to the receipt digest and to the separately qualified measurement-set digest. Merely
recomputing a digest after changing a metric does not admit the receipt.

The exact font-file hash remains the identity authority. PowerShell 7 may expose its family as the
canonical Hangul name while Windows PowerShell 5.1 exposes the same file as `HCR Batang`; these two
names alone are admitted and the receipt always emits the canonical Hangul name. The final fixed
measurement-set digest must still agree, so a runtime-dependent metric drift fails closed.

Only after complete admission may the adapter produce `FontMetricStatus::Verified`, bound to the
SHA-256 of the exact receipt bytes. Raw text, arbitrary file paths, copied font bytes, user
documents, UI input, network calls, registry changes, actual Hangul rendering, another PC or
another version are outside v1.

No compatibility alias, fallback measurement, renderer-equivalence claim or silent normalization
is migrated. Any additional font, point size, DPI, target build, fixture text, provider or operating
system requires a new contract version, migration and independent negative and actual evidence.
