# P16-05 project continuity visual QA

## Result and method

`PASS_SCOPED_LOCAL_RENDER`. The 1536x1024 generated concept and all seven final captures were
inspected at original resolution. Captures use Google Chrome `152.0.7977.76`, isolated headless
profiles, the generated local `continuity-preview.html`, no development server and no network
resource. Desktop is 1200x720; narrow is 500x760 below the 720 px breakpoint.

This is local browser/component evidence, not actual ChatGPT/Codex host, Developer mode, registered
plugin, remote MCP, Hangul/COM or production evidence.

## Evidence

| State | Viewport | Bytes | SHA-256 |
|---|---:|---:|---|
| desktop confirm | 1200x720 | 42,150 | `b8b96630cc3dc21e99522b3846fc11de2dd04dd9e67bf990f273c3e08e71de28` |
| desktop conflict | 1200x720 | 41,210 | `0a1a15279aae69d2c6779c23de1f48f0207741cb6e94ba5dbc38b56d17335b2b` |
| desktop dark saved | 1200x720 | 39,063 | `4f84531b2dffac491568ce9825e3a2836ed6402cb671e49a0725f1740fb93d36` |
| desktop ready | 1200x720 | 36,750 | `ce3be74593fed26c574b6092f17b3a9478bef2aa8c8dc89bb449af26311cd8c9` |
| narrow confirm | 500x760 | 38,439 | `60945372f3a6fc30f4d88fd10d481193c7f5e449775e8f3e60190ba251006650` |
| narrow conflict | 500x760 | 37,529 | `859d77937e7d3a4e9b534f7e88653ec0674707ab9041e6d5b746625238690a1f` |
| narrow ready | 500x760 | 32,838 | `ad12c8dff9bfcd761c0f458ecc46c96eb512ff428df10c6346afd87091760405` |

## Review findings

1. The implementation retains the concept's project-history identity, vertical revision graph,
   emphasized head, conflict banner and checkpoint action while reducing the board to a portable
   inline card.
2. Desktop gives metadata and timeline separate columns. Narrow stacks them, keeps dates and opaque
   IDs readable and moves actions to full-width native buttons without nested scrolling.
3. Ready exposes exactly two actions. Conflict exposes only Refresh. Confirmation exposes exactly
   Cancel and Confirm and create; the first checkpoint click alone causes no write.
4. Dark saved state preserves geometry and adds only a bounded completion message. No state reveals
   a full identifier, filename, path, document text, revision note or raw error.
5. The initial capture revealed that a transparent preview body became black below a short light
   card. Only the preview harness was corrected to paint the expected canvas; the production
   resource remains host-transparent.
6. The local design uses a simpler timeline than the concept detail pane because inline widgets
   must avoid deep navigation, nested scrolling and more than two actions.

## Accessibility review

- Native buttons, one `h1`, section headings, definition-list metadata, ordered revision history,
  visible focus, `aria-live`, alert/status roles and 44 px targets are present.
- Small status colors are `#117a4b`, `#8a4b00` and `#b42318` on white; dark equivalents are
  `#5bd19a`, `#f0ad4e` and `#ff8a80` on `#171f2c`. The contract verifies each pair at 4.5:1 or above.
- Full keyboard, screen-reader and actual-host container acceptance remains P16-09 and is not claimed.
