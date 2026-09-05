# P16-06 visual QA

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
