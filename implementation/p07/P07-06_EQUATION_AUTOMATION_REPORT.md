# P07-06 equation automation report

## Result

Result: exact-current-PC `pass` / direct stage `oracle_verified`.

`equation-engine` now produces deterministic typed insert/edit/readback plans from complete bound
state and verifies effect receipts with operation-specific mutation rules. A private source-derived
harness executed those operations against licensed Hangul 2020, and `hwpx-package` independently
reopened both saved outputs through a strict automation-native equation profile.

## Component evidence

- Equation automation Rust tests: 8/8 PASS. Coverage includes insert/edit/readback happy paths,
  request/build state and selection drift, mutation/nonmutation receipts, failed/effect-unknown
  handling, wrong object/semantic state, strict JSON, limits and redacted Debug.
- Native equation HWPX tests: 12/12 PASS. The added test proves direct and automation profiles are
  distinct, exact automation normalization reopens semantically, and style/comment/script tampering
  fails closed.
- Private probe-builder tests: 5/5 PASS. They cover deterministic redacted output, exact source
  identity/shape/type checks, script/semantic digests, private-boundary enforcement, duplicate JSON
  and no-overwrite publication.
- P07 Python contracts: 30/30 PASS. Final workspace Rust FULL passed with only the pre-existing
  explicitly ignored environment qualifications; workspace Clippy with `-D warnings`, PowerShell
  parser checks for both harness files, `cargo fmt --check` and `git diff --check` all passed.

## Licensed Hangul 2020 target evidence

- Exact target: `HWPFrame.HwpObject.2`, Registry32, x86 STA, ko-KR, build `11.0.0.9136`, executable
  SHA-256 `7f009613...72bce`.
- Source records SHA `03db035d...317b5` yielded one opaque binding-set SHA
  `3d8bbc9b...35cfb`, with three action and eight typed item bindings. Neither the public receipt nor
  committed evidence contains the raw identifiers or private paths.
- Attempt 03 passed all 16 lifecycle/action phases, exact in-session readback before and after edit,
  save/reopen and quit. It timed out nowhere, exited 0 and left no target process.
- Inserted HWPX SHA `4c908413...ca61` is 13,024 bytes; the product oracle found one display equation,
  object ID `1192022476`, initial semantic/script SHA equality, base unit 1000, baseline 86 and
  extent 2230x975.
- Edited HWPX SHA `ec935ef2...9f2b` is 13,073 bytes; the same object ID remained selected and the
  distinct edited semantic/script SHAs matched, with base unit 1000, baseline 89 and extent
  2665x1163. Both packages contain 11 parts, 74 ID declarations and 172 references.
- Attempts 01/02 and the initial attempt-03 oracle remain failed diagnostic history. The oracle fix
  was rerun over the same immutable successful HWPX files; none of the failed results was promoted.
- Authority: `implementation/p07/evidence/target/p07-06-equation-automation.current-2020.attempt03.v1.json`.

## Registry and product boundary

The frozen P02 current registry still represents `eq.insert_native`, `eq.edit_native` and
`eq.roundtrip_readback` as unavailable for lack of a reviewed mapping, with routing disabled and
runtime support unverified. P07-06 neither edits nor promotes that registry. Production routing
must wait for the dedicated P10 security/executor Gates.

No PDF/render claim is made for P07-06; P07-05 already has a separate direct-lowerer render result.
Editor double-click smoke, layout estimator visuals, differential parity, production execution,
other versions, P07 completion and product completion remain `false` / `not_run`.

## Next exact task

Implement P07-07 layout estimation at `max`, with baseline/ink-box visual tests on the exact current
target and explicit `render_required` behavior when the estimator cannot prove a bounded extent.
