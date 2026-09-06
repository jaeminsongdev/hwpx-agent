# P05-08 Hangul 2020 master-page and control-placement repair

- Date: 2026-09-07.
- Scope: current licensed Hangul 2020 `11.0.0.9136` x86 and disposable P05-08 fixtures only.
- Decision: **fixed v12 current-PC Hangul 2020 fixture Gate PASS**.
- Reasoning/review: MAX / STRICT, change risk HIGH.

## Actual source-of-truth reference

The bounded x86 STA diagnostic `tools/create-hancom-2020-master-reference.ps1` created a new
document, used Hangul's own `MasterPage` action, inserted the marker
`P05-08-MASTER-REFERENCE`, and saved a disposable HWPX. The source artifact is 14,077 bytes at
SHA-256 `2f093f002a0a4dda894775724145b797b88d94ed2333aa3029e1c11cd846467f`.
It was then opened, saved, reopened and exported to PDF by the same bounded lifecycle used for the
target. Its roundtrip HWPX is 14,098 bytes at SHA-256
`792949ef292062097355c696ffd6b529d33e197339f0bbbb2af57a5561daf62f`, its PDF is 11,191 bytes at
SHA-256 `f90253879d1cce1f7e60a08ce0f7d378cdd8abb0eb7e682e2d0b5e96d65959f5`, and no owned Hwp
process remained.

The actual package established the current-profile form:

- `Contents/masterpage0.xml` uses an XML declaration and an unqualified `masterPage` root;
- manifest item `masterpage0` precedes the section item and the master resource is not in OPF
  spine;
- section `masterPageCnt="1"` and `hp:masterPage idRef="masterpage0"` link the part;
- the master `subList` has empty body ID, `TOP` vertical alignment, width `42520`, height `65762`,
  numeric paragraph ID `0`, and no synthetic text character-style reference;
- Hangul-generated header/footer controls reside in the second body run after the section-property
  run, and their sublist paragraphs contain line-segment cache data.

The reference lifecycle preserved the master part, proving that the bounded runner did not delete
it. The earlier target failures therefore remained package/control-shape defects until repaired.

## Product repairs

The master lowerer now emits the actual standalone root form and required namespace envelope. The
reader accepts that form while retaining the legacy namespaced form for already-produced internal
artifacts. Target publication binds the manifest/root/section identity as `masterpage0`, omits the
master from spine, and emits it before the referring section. Header/footer/page-number controls are
placed in the body run rather than the `secPr` run. Header/footer/master paragraphs now receive a
bounded deterministic `hp:linesegarray` cache.

The first strict read of the successful Hangul output exposed a separate panic: Hangul writes an
empty `<hp:t/>` after some page fields, whose preserving-XML end token equals its start token. The
reader now treats a validated empty text element as zero semantic inlines instead of slicing an
invalid token range. A dedicated regression covers that exact shape; malformed or nested shapes
continue to fail closed.

## Preserved diagnostic progression

The earlier v4-v9 target variants all reached the lifecycle but lost their master part on save, so
none is relabeled as PASS. They isolated, in order, master identity, spine membership, standalone
root, canonical master body, header spine linearity and archive order. A master-only v10 attempt
timed out before authorized open and is not runtime evidence.

The corrected v11 input is 8,495 bytes at SHA-256
`c812d29894a14f272d387a8b4ad1240fedb877cd4f722eb7040b33aebcff9783`. Its authorized actual
lifecycle passed every phase and preserved the input. The saved HWPX is 14,638 bytes at SHA-256
`760b893cad728000c5912cabd4c345b7ff287557462e9cd8f03ae7d3921b851d`; strict readback reports
4 pages, 4 header/footer definitions, 8 page fields, 1 master page, first-page suppression and the
locked body-text SHA-256 `aa45c23687c9a6e94d33c40e13578c0b73905b48eb4bd1237bfe6893c6a08d15`.
The 18,528-byte PDF at SHA-256
`54e2f6211110af40f34a3ea072f229b54cf15f095bdfe54598b15e4b8dd31c6f` passed the four-page
text/forbidden-text/geometry verifier. Its trace also records zero timeout, zero cleanup error and
zero remaining Hwp processes.

Original-resolution review then found the body and master markers intentionally generated at the
same top-left position on pages 2-4. Because this prevents an unambiguous clipping/overlap review,
v11 is retained as structural and render-presence evidence but not promoted to final visual PASS.
The v12 fixture shifts only the disposable master marker with a typed tab; its input is 8,516 bytes
at SHA-256 `226122eaac21031270316819c89c43e029f48417aae742d69edbde9e0b230475`. Attempt01 timed out
at `open_input` without an access click, produced no output/PDF, preserved the input, cleaned its one
owned Hwp process and left zero residue. It is not a rejection and not a PASS.

User-authorized attempt02 then passed all ten lifecycle phases. The 14,661-byte saved HWPX at
SHA-256 `2fd7af9efb54132160b617b7b28399804596115fb2758bf193e5b0cd830838ac` passed strict readback
with 4 pages, 4 definitions, 8 page fields, 1 master, first-page suppression and the unchanged body
text digest. The 18,561-byte PDF at SHA-256
`649452bdc3f755def558fbe70a6be5ad8a75e6d6e2dc9059e6fee96e82a7838a` passed the locked
four-page expectation. Its verification trace SHA-256 is
`39bacc81579547ad7a9d90324231c27ce52281d56c347c1ee3d2542508d507fc`.

All four 144-DPI page rasters were inspected at original resolution. Page 1 contains only the body
marker as required by first-page suppression. Pages 2 and 4 contain the even header/footer, body,
right-side master marker and bottom-center page number; page 3 contains the odd equivalents. No
marker overlaps, clips, disappears or crosses to the wrong page variant. The lifecycle left zero
Hwp processes and did not modify the input.

## Validation and remaining Gate

The complete `hwpx-package` all-target/all-feature suite passes 217/217, warnings-denied Clippy
passes, the PDF verifier tests pass 21/21, the new PowerShell diagnostic parses cleanly and formatting
is clean. The locked 128-case digest is now
`67ed13c27ab4c7197dfec1c1853554a19fd21b93b0bb4fb4bc282f0b61f45bc9`.
The fixed v12 current-PC Hangul 2020 P05-08 Gate is closed. No evidence here qualifies Hangul
2022/2024, another PC, arbitrary documents, P05-09, the P05 phase Gate or the whole product.
