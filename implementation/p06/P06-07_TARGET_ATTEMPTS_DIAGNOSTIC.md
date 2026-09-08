# P06-07 current-PC target attempts diagnostic

Date: 2026-09-08

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
