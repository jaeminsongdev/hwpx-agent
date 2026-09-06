# P05 Text, Style and Page Layout Gate Report

- Generated: 2026-09-07
- Implementation base commit: `cacbc936e4d225e1a4424efb806aa96f86965ec5`
- Source qualification commit: `23b2a534cb65d1e2f99e594eca89861cffae36bb`
- Audited FULL commit: `cf5475379422899ac25fecb78968802d53442b3c`
- Audit mode: `STRICT`; reasoning recommendation: `high`
- Overall state: `pass_scoped_current_pc_hangul_2020_local_layout`
- P06 authorization: `authorized_current_pc_local_only`

P05-01~09를 현재 PC의 정품 한글 2020 `11.0.0.9136` x86, 개인·비상업·로컬 개발
범위에서 구현하고 재현했다. Bounded text flow, character/paragraph style, tabs,
lists/numbering, page setup, sections/columns, header/footer/master page와 VS-1 layout을 typed
contract와 fail-closed reader/writer 경계로 연결했다. 실제 desktop 증거는 이 보고서에 명시한
disposable fixture에만 적용하며 사용자 문서, 임의 HWPX, 다른 PC/버전 또는 production
호환성으로 확대하지 않는다.

## Gate criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| P05-01 Text flow | `pass` | Unicode/run-boundary 128 corpus, typed run/tab/line-break/field handling | Arbitrary package lifting is not claimed |
| P05-02 Character style | `pass` | font-slot/style dedup and 128 variation corpus | Installed-font substitution outside the fixed target is unverified |
| P05-03 Paragraph style | `pass` | typed paragraph layout, reference rewrite and 128 negative/variation cases | Full rendered fidelity for arbitrary documents is unverified |
| P05-04 Tabs | `pass` | default/custom/leader/decimal model and exact-2020 save/reopen semantic readback | Visual tab fidelity beyond the fixture is unverified |
| P05-05 Lists and numbering | `pass` | bounded nesting/restart/continuation model and exact-2020 readback | Arbitrary legacy numbering imports are unverified |
| P05-06 Page setup | `pass` | checked paper/orientation/margins/gutter and impossible-layout negatives | Printer-dependent output is unverified |
| P05-07 Sections and columns | `pass` | sparse attempt23 plus dense attempt02 actual save/reopen/PDF/visual evidence | Earlier timeouts and failed expectations remain failures |
| P05-08 Header/footer/page number | `pass` | v12 actual 4-page/4-definition/8-field/1-master strict readback and PDF review | Fixed fixture and current target only |
| P05-09 VS-1 layout | `pass` | v2 actual two-column explicit-break semantic, coordinate and visual verification | Equation/table/graphics verticals are P06+ |
| Common phase constraints | `pass` | migrations/negative tests present; unexecuted claims stay unverified; in-place source writes 0; failed fixtures and exact P06 handoff recorded | Other PCs/versions/production remain deferred |

## Current-target actual evidence

- P05-07 sparse attempt23 passed landscape section identity, save/reopen and PDF verification. Dense
  attempt02 passed 31-paragraph zero-explicit-break automatic flow, two-page coordinate/balance and
  original-resolution visual review. Failed predecessors are retained and were not relabeled.
- P05-08 v12 evidence is under
  `fixtures/target-build/p05-08-current-2020-20260907-v12/`. Input
  `226122eaac21031270316819c89c43e029f48417aae742d69edbde9e0b230475` produced saved HWPX
  `2fd7af9efb54132160b617b7b28399804596115fb2758bf193e5b0cd830838ac` and PDF
  `649452bdc3f755def558fbe70a6be5ad8a75e6d6e2dc9059e6fee96e82a7838a`. Strict readback found
  4 pages, 4 definitions, 8 fields, 1 master and first-page hiding. The 128-case digest is
  `67ed13c27ab4c7197dfec1c1853554a19fd21b93b0bb4fb4bc282f0b61f45bc9`.
- P05-09 v2 evidence is under `fixtures/target-build/p05-09-current-2020-20260907-v2/`. Input
  `7274a592905e15a0b4a2d58a38a827e45cc4f7e5717e1c8c6c986a9597e91666` produced saved HWPX
  `35169882bd81981fc516a86de8c2082e596b5448fc64f4a0de5fe3095d5a4ea2` and PDF
  `f2df223831be330e81103f0db3d338a6aae3f45b8160b9f808aafaa6af03484d`. Strict readback found
  11 package parts, 5 paragraphs, 1 explicit break, 2 columns and gap 1700. PDF verification found
  24 left-column fragments, 17 right-column fragments, one page-edge callback and 10.145 mm bottom
  delta. Visible-text digest is
  `2d93a6073c0703bdc54ccb4a6f12671604a7cac5207fd20744d264a5f93df33f`.
- All reviewed P05-07/08/09 pages had no visible overlap or clipping. Inputs were unchanged, visible
  text contracts were preserved and residual `Hwp.exe` processes were 0.

## Source and repository validation

- Source successor v20 qualification `p17.current-workspace-source.v20.20260907` passed 11/11 at
  run `7f1b1756db794407a6256398170b7bf8`. Receipt SHA-256 is
  `f5eafd5b3d1fef9d46c9fb7b2eb5179e9d2e1998387025470cc93484aee4c2c3`; contract SHA-256 is
  `adca1fbccedad8b4c6dfb7dbd223f86b02a7ba5f9357c21220340b3796969d22`.
- Exact audited commit `cf5475379422899ac25fecb78968802d53442b3c` passed the current workspace FULL
  pipeline `5/5`: linux-core, windows-worker, widget, docs and security. Security run
  `401faa204de34bd1aca467ac4491efc4` reported failed checks, vulnerabilities and forbidden licenses
  0; report SHA-256 is
  `6a431fa491980d9de107cbcb563a670eefa7dc18a0574586a5ada9d8c969cac6`.
- A clean independent worktree detached at the same exact commit passed FULL `5/5`. Security run
  `5c87496e8ba3491ba93edc577e2d5e61` reported the same zero findings; report SHA-256 is
  `dc76ef74b4d9905c940b5db680e87f2765a560f249560740ab3502c605343397`.
- Offline Linux used Rust 1.96.0 with network disabled, read-only source and Cargo registry,
  dropped capabilities, no-new-privileges, bounded CPU/memory/PIDs and disposable tmpfs. The P05
  package test set passed 210/210 and Clippy `-D warnings` passed. Image digest:
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
- The first offline Linux attempt failed before compilation because rustup attempted to write beneath
  the read-only toolchain path. It is retained as a diagnostic failure; the retry pinned the already
  installed toolchain explicitly and did not weaken network or filesystem isolation.

## Strict review and remediation

- Change risk: `high`; page/section identities, preservation behavior and actual Hangul rendering
  are consumed by later table, equation, graphics and public-operation phases.
- Verdict: `approve_scoped_current_pc_hangul_2020_local_layout`.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- The first FULL run exposed that the design validator traversed ignored local evidence beneath
  `fixtures/target-build`. Commit `cf5475379422899ac25fecb78968802d53442b3c` excludes local
  evidence roots from the design source tree and adds a regression test. Both current and independent
  FULL runs then passed at that exact commit.
- Changed production P05 files introduced no `unwrap`, `expect`, `panic`, `unsafe`, `TODO` or
  `FIXME` sites. One `unreachable!()` in `header_footer.rs` predates this P05 closure and is behind a
  closed-name filter.
- Synthetic, unit, source and component evidence was not promoted to actual Hangul proof. Actual
  fixture proof was not promoted to arbitrary-document, other-version, production or native-equation
  proof.

## Failure fixtures and residual boundaries

- P05-07 timeout/identity/one-page-expectation failures, P05-08 early master/control failures and
  v11 marker overlap, and the first P05-09 page-edge callback failure remain preserved.
- The exact current-PC PASS does not qualify Hangul 2022/2024. Each will require its own PC, exact
  build/profile, source binding, save/reopen/readback/PDF evidence and differential report later.
- User documents were not opened or modified. Production, provider, server/VM, customer distribution,
  printing, arbitrary HWPX compatibility and commercial deployment remain unqualified.

## Phase decision

P05 is complete for the explicitly current-PC, licensed Hangul 2020 personal local-development
scope. P06 may start in the same scope. No broader runtime or release authorization is implied.

## Next exact task

Start `P06-01 Grid/span invariant` at reasoning effort `high`. Lock a bounded `TableGrid` model with
slot-to-master-cell mapping and rectangular spans, define finite row/column/cell limits and typed
invalid/nonrectangular/overlap failures, then prove canonical serialization and deterministic
property tests before implementing create/insert/delete operations.
