# P16-04 Widget shell report

- Generated: 2026-09-05
- Audited implementation commits: `745d76af279de842b210682675dc0de7631f9512` and
  P15 evidence-chain repair `19d1cf775e5702e1150e35624bf616f1dbf9a34c`
- Reasoning effort: `high`; bridge/result/CSP/security and closure review: `max`
- Decision: `pass_scoped_local_widget_shell_component`

P16-04 implements a standards-first React/MCP Apps widget shell as a deterministic self-contained
resource. It proves the current-PC local component, lifecycle, resource, responsive-render and
security boundary. It does not claim actual ChatGPT host rendering, registered-plugin behavior,
Developer mode, hosted MCP execution, Hangul/COM execution, file transfer or production readiness.

## Implemented boundary

- Immutable resource `ui://hwpx-agent/document-work/v1.html` uses
  `text/html;profile=mcp-app`, inline display and a closed CSP with no connect, resource or frame
  domain.
- The official MCP Apps `App` runs strict with unsafe eval disabled and automatic resize. Input,
  result, cancellation, host-context and teardown handlers are registered before connect.
- Missing approved input is an expected `approval_pending` state. Model-originated input cannot make
  the shell ready; a schema-valid server result must follow and match the approved surface/project.
- Continue calls only the exact read-only `project_open` tool. The server must re-authenticate and
  re-authorize every call.
- Host theme and locale are sanitized. Optional host extensions are detected by method presence and
  never by hostname. No network API, browser storage, cookie, arbitrary URL or local path is used.
- Responsive Korean/English HTML uses native semantics, visible focus, 44 px controls, reduced-motion
  handling, AA color pairs and opaque six-character identifier prefixes.
- The eighteen P15 tools remain UI-independent. UI metadata exists only on the dedicated render tool.

## Exact identity

- Contract: `implementation/p16/p16-widget-shell-contract-v1.json`
- Decision: `pass_scoped_local_widget_shell_component`
- Bundle: `web/plugin-widget/dist/widget-v1.html`, 643,174 bytes, SHA-256
  `7298d67619fa5afb3c9e870f59dce1412a2de77741474e8b522006d4f469db78`
- Preview: 203,381 bytes, SHA-256
  `bcf8db422a876efdbb93acef0b09c5e313eac32c95b5d92e15aea38dcad2300d`
- Source locks: 45; dependency versions: MCP Apps 1.7.5, React/React DOM 19.2.8,
  esbuild 0.28.2.
- Visual evidence: two immutable concept sources and seven inspected Chrome captures; minimum CSS
  width 320 px. See `implementation/p16/P16-04_VISUAL_QA.md`.

## Validation

| Check | Result |
|---|---|
| P16-04 target | pass; TypeScript 21/21, Python 14/14, deterministic bundle |
| P16 cumulative | pass, 64/64 |
| Current exact-repair-commit full CI | pass, 5/5: Linux 13.170s, Windows 67.939s, Widget 5.576s, Docs 1,726.357s, Security 20.919s |
| Independent exact-repair-commit full CI | pass, 5/5: Linux 14.329s, Windows 74.306s, Widget 6.531s, Docs 1,156.732s, Security 14.885s |
| Independent P14/P15 regression | pass, P14 132/132 and P15 84/84 |
| Offline Linux P16 | pass; pinned image, network disabled, source/root read-only, capabilities dropped, 64/64 |
| Independent checkout tracked changes / residual checkout | pass, 0 / removed |

The current exact-commit security run `f937f312841f40e4b94f47f49a68f3f5` is retained in the
Git-ignored evidence tree. Its 1,295-byte report SHA-256 is
`c3efc03710299d034107999d0b96b590d127544ce12ece8550efcddd78816ce5`; its 1,055,074-byte,
1,015-component SBOM SHA-256 is
`a27787db8bfecb9bda313ad2ddf14c853e9be4277d284e994c719c27d7c01c57`. Every check passed and the
secret scan found zero findings across 1,104 files.

The final independent security run `e6e72c1b12ab435990a24b692f7d4cfb` was copied byte-for-byte to
the main ignored evidence tree before checkout removal. Its 1,294-byte report SHA-256 is
`18833b408622a320c19477b9ca6e88927b7cfe6db7121e350fc9de4cd1b78c01`; its 869,782-byte,
782-component SBOM SHA-256 is
`40b1a690894598e5c34f67268dc9ab4010aa1de1328c48a141815688ffb4259c`. Every security check passed
on the first audit attempt. Component-count differences reflect checkout-local ignored build state.

Offline Linux used local pinned image
`python@sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f` with networking
disabled, a read-only root/source, all capabilities dropped, `no-new-privileges` and bounded
resources.

## Failure, repair and independent-audit record

- The first full CI on `745d76a` correctly failed in the docs lane because three dependency files
  changed after the P15 closure. The failure was not promoted. Repair `19d1cf7` permits exactly five
  successor paths only when the full P16-04 contract passes and every historical P15 byte still
  matches audited commit `7ea2f84c244fe5bbd7926ba3f176dc5acafcf624`.
- The first independent full-CI attempt stopped because four Git-ignored, digest-pinned P10
  current-PC diagnostic records were absent. Only those four exact JSON records were copied; no
  HWPX, PDF, user document, credential or design source was transferred.
- The second independent attempt was externally terminated with `0x40010004` when Windows rebooted
  at 2026-09-05 14:45:59. Event logs showed OS/driver/service restart activity and another OEM
  process failure; no repository assertion had failed. This attempt was not promoted.
- The unchanged third attempt completed all five lanes. Its security report and SBOM were retained
  before the exact detached worktree was removed.
- No Hangul process, COM call, UI input, external account, public endpoint or system setting was
  opened or changed by this card.

P16-04 may be checked. Continue P16-05 at reasoning effort `high`; use `max` for checkpoint write,
component `_meta`, response identity, host reauthorization and the actual-host evidence boundary.
P16-02 registration remains independently pending.
