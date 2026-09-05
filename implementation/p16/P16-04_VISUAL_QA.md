# P16-04 visual QA

## Result

`PASS_SCOPED_LOCAL_RENDER`. The generated concept boards and every final screenshot were inspected
at original resolution. The production shell preserves the concepts' product/surface header,
state-first hierarchy, semantic status color, three metadata rows, restrained hairlines and one
primary action. It renders only one current state, as required by the bridge contract.

This is local browser/component evidence. It is not evidence of ChatGPT host rendering, Developer
mode, registered-plugin behavior, remote MCP connectivity, file transfer or Hangul execution.

## Capture method

- Browser: Google Chrome `152.0.7977.65` in isolated headless profiles.
- Source: generated `web/plugin-widget/dist/preview.html`; no development server or network request.
- Viewports: `1200x720` desktop and `500x720` narrow, both at device scale 1. The narrow capture is
  below the 720 px single-column breakpoint. CSS separately enforces a 320 px minimum.
- Interaction: no Computer Use click or keyboard input. Query-locked local states were captured,
  then concepts and final screenshots were inspected with `view_image` at `original` detail.
- An initial 390 px Chrome CLI attempt was not admitted because Chrome retained a wider layout
  viewport while cropping the bitmap. Those files were overwritten by the isolated 500 px captures.

## Evidence

| State              | Viewport |  Bytes | SHA-256                                                            |
| ------------------ | -------: | -----: | ------------------------------------------------------------------ |
| desktop approval   | 1200x720 | 21,047 | `fb83b66541a3cd642381ea3fe3a89860a05d9ef9bffc32b113c5d91292e700f6` |
| desktop dark ready | 1200x720 | 26,275 | `fe55b0f067732bf45ecf86a4688d3c8aac14a0c0cf178d037fcac1fe951631a6` |
| desktop error      | 1200x720 | 19,743 | `48189381753a4cbe46bb72b148d89598f5d44991b4f0dda89ec2d389a3bfc355` |
| desktop ready      | 1200x720 | 21,710 | `1262ac4520db011b194c4312e7bf86c6daa2062571a8be61b6700a288bba303e` |
| narrow approval    |  500x720 | 17,229 | `71f852c6bf2c7aa247564105a8c3cbed8fa0c47a4bd14701e2dac20be219f48f` |
| narrow error       |  500x720 | 16,725 | `7e2578d8e921c4613d3592b79466fbb8de49e34c50056edbfb4a89f694847d38` |
| narrow ready       |  500x720 | 18,593 | `ce8b473c4ab0d734642c751d9e32ca418038028e7720aba09a554f0d0d4c6fcf` |

## Concept comparison

1. Header identity and surface label match the desktop concept; the narrow implementation keeps
   both visible without the concept's non-functional overflow and collapse controls.
2. Ready, approval and recoverable-error states retain green, amber and red semantics. Code-native
   document-check, clock and alert SVGs replace illustrative placeholders.
3. The desktop concept's side-by-side review board is intentionally normalized to one state per
   production widget. At 1200 px, status and metadata remain a clear two-column composition.
4. Below 720 px the widget becomes one column, keeps every label/value visible, removes horizontal
   scrolling and expands the primary action to the available width.
5. The concept's large document illustration, nested cards, chevrons and fake detail navigation are
   absent. P16-04 is a portable inline shell, not a document browser.
6. Opaque project and revision identifiers show six characters plus an ellipsis. Missing values use
   an em dash; filenames, paths, document content and raw server errors never appear.
7. Dark rendering uses the host-selected theme and stays within the same geometry. The background,
   text, hairlines, status color and primary button all switch without a hostname branch.

## Copy and accessibility review

- Concept copy was shortened to local, bounded lifecycle messages. Approval says it is waiting for
  approved host input; recoverable failure never exposes transport text.
- The first render correctly revealed insufficient small-text contrast for the light success and
  approval colors. Final colors were changed to `#117a4b` and `#9a5800`, producing contrast ratios
  `5.372:1` and `5.570:1` on white. Error is `5.505:1`.
- Dark success, approval and error are `8.695:1`, `8.506:1` and `6.598:1` on `#171f2c`. Dark button
  ink on the light-blue primary surface is `7.863:1`.
- Definition-list semantics, one `h1`, `aria-live`, a 44 px control, focus-visible styling and
  reduced-motion handling are implemented. Full keyboard, assistive-technology and host-container
  accessibility acceptance remains P16-09 work and is not claimed here.
