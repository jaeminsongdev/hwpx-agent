# P06-07 current-PC target attempts diagnostic

Date: 2026-09-09

This file records failed or superseded renderer attempts. An attempt here is not P06-07 PASS.

## Attempt 01: access timeout

The first strict run reached visible `open_input` but received no approval within the finite
600-second watchdog. The runner terminated only its exact automation process and reported zero
remaining `Hwp.exe` processes. No output HWPX or PDF was published.

## Attempt 02: structural save/reopen PASS, renderer layout FAIL

The first generated target had SHA-256
`2f20e831ef8b23df9470762f6d8f70a0859a20cde38e262fba6b2add1ea3848d`. Licensed Hangul 2020
build `11.0.0.9136` completed open, input text read, HWPX save, close, reopen, output text read,
PDF export, close, and quit. Input and output semantic-text SHA-256 both equalled
`919f5fb04a1a6b4cbcb4964a79870504084ee981e794421e12ea2eafa830399d`. The saved HWPX strict
oracle passed all six table profiles and observed 140 renderer-produced line caches.

The nine-page A4 PDF is diagnostic-only. Visual inspection found that the `CELL` long-cell case
rendered visible items 001 through 022 on page 1, produced a blank page 2, and omitted visible
items 023 through 064. The three 38/39/40-line avoid-table boundary candidates all moved to the
following page, so they did not establish before/exact/after separation. The avoid-row table,
nested table, equation, and bottom caption rendered, but the table did not cross a page boundary.

Root cause is target construction, not promoted product behavior: the long cell carried an
artificial 95,000-HWPUNIT stored height and the avoid-row table was too short. The attempt remains
failed even though the save/reopen lifecycle passed.

## Successor target

The successor removes the artificial long-cell height, extends the avoid-row table with 30
ordinary rows so it must cross a page, and changes boundary fillers to 34/35/36 lines. It uses a
new create-only evidence directory; the failed predecessor and its evidence remain immutable.

The first successor calibration launch reached visible `open_input` but was not approved within
the 600-second watchdog. It produced no HWPX or PDF and left zero `Hwp.exe` processes. This is an
access-timeout diagnostic only; the successor renderer state remains `NOT_RUN`.

## Successor attempt 02: text identity calibration only

The next bounded launch was intentionally supplied a non-matching all-zero expected text digest so
that the exact successor document text identity could be measured without publishing an output.
The user approved the visible input-access prompt. Licensed Hangul 2020 build `11.0.0.9136`
opened the exact successor target and observed canonical input-text SHA-256
`19e2e32f32ce5238e72ffafdca368a7ebba92bb60b9ed514a40719305b5a8855`. The runner then failed
closed with `TABLE_PAGINATION_READBACK_INPUT_TEXT_MISMATCH`, as designed, before save or PDF
export. The input remained unchanged, no output was published, and zero `Hwp.exe` processes
remained. This calibrates only the expected text identity; it is not renderer PASS evidence.

## Successor attempt 03: full readback access timeout

The full save/reopen/PDF launch used the calibrated exact text digest and a 900-second watchdog.
It reached visible `open_input`, but the new access prompt was not approved within the watchdog.
The runner recorded `TABLE_PAGINATION_READBACK_TIMEOUT`, published no output HWPX or PDF, verified
the input remained unchanged, terminated only its exact automation-owned process, and reported
zero remaining `Hwp.exe` processes. The successor renderer state therefore remains `NOT_RUN`.

## Successor attempt 04: lifecycle PASS, renderer layout FAIL

The same successor target was copied byte-exact into a new create-only evidence directory and
completed the licensed Hangul 2020 lifecycle. The saved HWPX SHA-256 was
`3b46ba1b4f4484cc77190276cef9d6724f1982b3a8206b9960e3f585eab5b9f5`; the eight-page PDF
SHA-256 was `b38fbb2489a3d15f7033e676b032ed285a3d97a64c831b15707211b7df2114f1`.

Visual and PDF text-geometry inspection failed the renderer Gate. The `CELL` long cell still laid
all 64 items into page 1's content stream while only items 001-022 were inside the visible page;
page 2 was blank. The `TABLE` case similarly extended past page 4 instead of continuing, so its
equation and bottom caption were outside the visible page. Save/reopen and text identity passed,
but page splitting and repeated-header rendering did not. This attempt is permanently diagnostic
and is not promoted.

The newly isolated root cause was `treatAsChar="1"` on every generated table. Inline tables do not
participate in automatic multi-page table layout. The previous height-only correction therefore
could not make either table paginate.

## Corrected create-only target (contract v2)

The next create-only target sets `treatAsChar="0"` on all five top-level tables and retains
`treatAsChar="1"` only on the nested table. Its exact SHA-256 is
`44cfcd14d867e6b53f4a015061666fe3b9ac990d3b3c321faae863d172fe8316`. Its successful lifecycle
and ten-page visual oracle are recorded separately in `P06-07_TARGET_READBACK_REPORT.md`; that
success does not modify or erase any attempt in this diagnostic.
