# P06-09 TABLE-006 render-diff policy

- Scope: `exact-target calibration / non-gating`
- Target: licensed Hangul 2020 `11.0.0.9136` x86 ko-KR on this PC
- Contract: `hwpx-agent.table-chart-render-diff-contract/v1`
- Direct stage: `integration_passed`

## Frozen comparison

The native-reference and direct-product charts are exported by the same exact Hangul build. The
comparison requires identical one-page A4 PDF identity, the exact eight table words and their
positions, equal full-page ink bounds, and equal saved-HWPX table/chart type, series, cache and
anchor semantics. Pages are rendered at 150 DPI. Pixel changes are permitted only inside the frozen
default-title rectangle because both chart packages omit explicit title text and Hangul supplies
the visual placeholder. The ratio, mean channel delta and ink-count delta remain tightly bounded;
one changed pixel outside that rectangle fails.

The validator is read-only for its four evidence inputs. It renders into a temporary directory,
emits bounded JSON without paths or document payload, and rejects missing, oversized, malformed or
semantically drifting inputs. User screenshots and photo evidence are not required.

## Anti-overfitting boundary

Calibration attempt 01 is used only to freeze the profile. It may demonstrate that the validator
matches the observed native/product pair, but it cannot satisfy `required_render_diff`. A fresh
independent native/product export created after the profile checkpoint must pass without changing
any threshold. That later run must also pass a fresh retry before TABLE-006 can advance to
`oracle_verified`.

## Gate boundary

This policy does not claim the required render differential, rollback/retry, product automation
runtime, release differential, P06-09/P06 completion, arbitrary documents, another PC/version,
production readiness or product completion. TABLE-006 remains `integration_passed`.
