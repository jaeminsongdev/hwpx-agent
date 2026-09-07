# P06-05 exact table-layout target fixture

Date: 2026-09-07

## Prepared evidence

The current-PC target builder is bound to the synthetic Hangul 2020 source SHA-256
`814c481da946e760b2bc3b90b996863786652001e49f8b2b422e13c3d3e477a4` and installed-font receipt
SHA-256 `c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab` for 10 pt
`함초롬바탕` TTF metrics. No user document is opened or scanned.

The four exact target strings are hashed individually. The verified plan uses a 70,000 micrometer
table width, columns `52990,17010`, estimated row heights `13758,4586`, zero body/target overflow,
zero target underfill and no content deficits. Exact HWPX readback is table `19843 x 5200` HWPUNIT,
columns `15021,4822`, rows `3900,1300`, and inherited inner margins `510,510,141,141` HWPUNIT.

Three independent create-new writes (`target.hwpx`, `target-repeat.hwpx`,
`target-current.hwpx`) are byte-identical with SHA-256
`a678588188593c250b33205f1660fef6c301280cd5ae30deb4b6a03f185055bc`. A wrong input digest is
rejected without output. An existing target path is rejected and remains unchanged. Source and font
receipt hashes are rechecked after the build. `Preview/PrvText.txt` contains the target strings.

## Evidence boundary

The preserved source `Preview/PrvImage.png` is stale by design and is not visual evidence. Actual
Hangul 2020 save/reopen, exact text readback, geometry/wrapping inspection and signed PDF visual
comparison are **NOT RUN**. P06-05 is not complete, and this fixture does not claim another PC or
version, arbitrary documents, P06 completion, production, or product completion.
