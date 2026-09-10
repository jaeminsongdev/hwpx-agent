# P06-09 TABLE-002/003 exact table-ruling target readback report

Date: 2026-09-10

Decision: **PASS for TABLE-002/003 on the exact current-PC Hangul 2020 target**.

## Exact target and lifecycle

The successful create-only attempt is `20260910-08` over deterministic manifest SHA-256
`8296cf4057c1cb6b27c800c15694866008c31cfa290cd6863321179c1efda543`. The five immutable
inputs cover all nine admitted table-ruling actions: outer rectangle, full row and column strokes,
local cell split, existing-boundary style replacement, both directional diagonals, shared-edge
structural merge, and nonstructural transparent erasure.

The exact `HWPFrame.HwpObject.2`, 32-bit registry view, x86 STA client, Hangul 2020 file version
`11.0.0.9136`, locale `ko-KR`, and executable SHA-256
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce` completed all five cases
and 85 bounded progress events through `terminal/pass`. Every input was opened and read, saved to a
new HWPX, closed, reopened and read, exported to a signed PDF, and closed before the next case.
Canonical visible-text SHA-256 stayed exact for every case. No input changed, no raw document text
was retained, and zero HWP processes remained.

## Independent typed readback

The independent Rust oracle rejects unknown package, binding, topology, payload, formula or
selected-table-exterior drift. It first relifts the full selected table through the strict native
adapter and requires the manifest-bound state/grid, cell/payload/property/formula counts and ruling
semantics. It then removes only validated renderer `linesegarray` caches and compares the exact
section exterior after replacing the selected table span with a marker.

Hangul performs two reviewed empty-scaffold normalizations: it can serialize an empty
`<hp:run><hp:t/></hp:run>` as `<hp:run/>`, and it adds
`pageBreak="0" columnBreak="0" merged="0"` to the exact outer-case anchor paragraph. The reader
now recognizes only the self-closing empty-run form as empty; any nested control or text remains
payload. The oracle normalizes the three default attributes only at that one bound anchor and
continues to reject all other exterior drift. Hangul may also remap a selected cell's
`borderFillIDRef`; this is accepted only after full typed table equivalence, never by ignoring the
selected table.

All five exact outputs passed:

| Case | Output HWPX SHA-256 | State/grid result | Renderer caches |
|---|---|---:|---:|
| draw outer | `aee474cc...f7eb7` | 1x1, 1 master, exact | 11 |
| draw topology | `db6512e8...b644ce` | 3x6, 16 masters, exact | 18 |
| draw diagonals/formula | `8e324789...dc080` | 2x4, 8 masters, formula exact | 10 |
| eraser structural merge | `46506cc0...dc6e9` | 2x4, 6 masters, payload order exact | 10 |
| eraser transparent/formula | `a61f86e5...e4e77` | 2x4, 8 masters, formula exact | 10 |

The complete digests, counts and cache digests are bound in
`p06-table-ruling.current-2020.attempt08.v2.json`.

## PDF render oracle

Hangul produced five unencrypted, JavaScript-free, one-page A4 PDFs through
`IXHwpDocument.SaveAs/PDF`; producer is `Hancom PDF 1.3.0.550`. Each PDF was rendered with
`pdftoppm 26.07.0` at 144 DPI to 1190x1682 RGB pixels and inspected at original detail. There were
no blank pages, clipping, overlap or black boxes.

- The outer case shows the original 2x4 table and a separate empty outer rectangle.
- The topology case shows the 3x6 lattice, full row/column strokes, local split and boundary style.
- The diagonal case shows both diagonal directions in the formula cell.
- The structural eraser case shows both row-wise merges and preserved payload order.
- The transparent eraser case keeps topology while the formula cell's bottom/right outer lines are
  absent.

The five PDF and ephemeral rendered-PNG digests are recorded in the evidence receipt. PNGs are QA
intermediates, not product inputs; the exact retained PDF digests are the renderer artifacts.

## Retry and historical failure boundary

Attempts 01-07 remain immutable failed or interrupted evidence and are not promoted. Attempt 08
reused the same exact manifest and immutable inputs, used new create-only outputs, completed after
the prior bounded timeouts, and left no owned process behind. This proves the admitted retry path;
it does not relabel any earlier partial trace as successful evidence.

## Gate boundary

Contract `hwpx-agent.p06-09-table-ruling-target-contract/v2` promotes only TABLE-002 and TABLE-003
to `direct_hwpx / oracle_verified` on this exact target, adding `target_build`, `render_diff` and
`rollback_or_retry` evidence. Automation runtime and direct/automation differential remain
`not_run`. General structural-formula native lowering, arbitrary user documents, another PC,
Hangul 2022/2024, P06-09/P06 completion, production and product completion are not claimed.
