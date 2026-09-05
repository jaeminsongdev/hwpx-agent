# P16-06 visual QA

## Current response-evidence status (2026-09-06)

The earlier baseline and safety audit remain preserved below. Thirteen current
desktop/narrow/minimum-width screenshots were copied only after source and destination SHA-256
verification into `implementation/p16/visual-qa/response-v3/`. The policy binds all thirteen
digests and sizes to preview HTML SHA-256
`71572ab4a01a98c4431e128f30b018fb3c000b45bdf9c8e5cc577d3c65f27a58`.
The source UI and build script are byte-identical to commit
`477d4023d6e29c944d08fb81b9193d0fe3010276`, and the rebuilt preview, widget and E2E-host digests
match the isolated `run-03` capture receipt. That receipt SHA-256 is
`aff360cdf4227f28b07398980e13a0bbcd0c6dc13be0fe4c23cdd08ba871810e`.

All thirteen images were inspected again with `view_image` at original resolution. No capture has
overlap, horizontal clipping, framework/browser error output, document contents, a filesystem path,
account data or a full opaque identifier. See `P16-06_RESPONSE_EVIDENCE_REFRESH.md` for exact scope
and preserved non-claims.

## Current capture coverage

The authoritative per-image hashes and byte sizes are in `p16-plan-review-policy-v1.json`,
`visual_qa.captures`. Each source was verified before copying to the new archive directory.

| Viewport | Captured states | Direct inspection |
|---|---|---|
| 1200x760 | ready, confirm, blocked, dark-submitted, unconfirmed, committed-unverified | clear risk/route/diff; pre-ack execute disabled; submitted actions disabled; unknown and unverified outcomes use amber copy |
| 500x1200 | ready, confirm, blocked, unconfirmed, committed-unverified | one column, visible actions, no horizontal clipping or overlap |
| 320x1600 | ready, committed-unverified | minimum-width content, warning and actions fit; not short-phone viewport proof |

All thirteen current images were inspected with `view_image` at original resolution. The isolated
browser also checked the disabled controls, alert/status roles, contrast tokens, no unexpected
horizontal overflow and no page/console errors. The separate bridge flow made exactly five calls.
These are local component observations with synthetic route/plan responses, not registered-host,
server execution, accessibility assistive-technology or actual-Hangul proof.

## Historical baseline

- Browser: Google Chrome `152.0.7977.76`, isolated headless file preview with networking disabled.
- Concept source: 1536×1024, 1,182,885 bytes, SHA-256
  `06b8750663041d690c02804da7c1d5bc628290aef5012c756c96cc1e1aa8aa41`.
- The concept is not shipped by the widget. All final surfaces are React/CSS.

## Inspected captures

| Capture                             |                Size | SHA-256                                                            | Inspection                                                             |
| ----------------------------------- | ------------------: | ------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| `p16-06-desktop-ready.png`          | 1200×760 / 65,078 B | `995b05c677a7fbf847678d9d449c98f474d28e23ed1d79ddcc944bba005af1d0` | route, totals, warnings and two actions visible                        |
| `p16-06-desktop-confirm.png`        | 1200×760 / 69,292 B | `6a6efb7f7718f9799cf2c7fa6323b94ea42d20b2a9eca164358d5f3ea10d1617` | separate acknowledgement and disabled execute visible                  |
| `p16-06-desktop-blocked.png`        | 1200×760 / 60,846 B | `d3e97198e5f37688b6ef8361c65888c48477101821cc1f62daca35fe26f1c9eb` | unverified route, blocking warning and disabled review visible         |
| `p16-06-desktop-dark-submitted.png` | 1200×760 / 66,726 B | `781f5e7f63d08195db4cc41c96262e84a4eb7a437f406274f537049283cf8273` | dark tokens and submission status remain readable                      |
| `p16-06-narrow-ready.png`           | 500×1200 / 57,996 B | `e974d3e655577e7fc987edf5b8a469ccbbea53a70f81a15540ff24c16b985f70` | one-column content and full actions visible                            |
| `p16-06-narrow-confirm.png`         | 500×1200 / 62,266 B | `6fc0ab775fb931a077d8918d3cba5eddd8f92c84d2225d4efa0627309ae18320` | acknowledgement and two confirmation actions visible                   |
| `p16-06-narrow-blocked.png`         | 500×1200 / 53,880 B | `9d6e4d98dec7f259bb1aa4542feedb36db5963c44c17b9bd546561c31c365cfe` | blocked reason and disabled action visible without horizontal clipping |

Every image was inspected at original resolution. No capture contains a path, document content,
full opaque identifier, raw server warning, XML/action string, external image or account data. The
500 px captures require no horizontal scrolling and keep the decision area visible in one viewport.
