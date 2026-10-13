# P09-18 namespace source successor report

Date: 2026-10-02. Public Rust profile remains
`hwpx-agent.field-object-caption-hwpx.hwpml-2011-digit/v1`; private source contract
and qualification advance to v2. The v1 contract, qualification and report remain
historical evidence, not a current-source PASS. Their source/test/validator bytes
are retained in the exact hash-bound r01 snapshot.

## Evidence-driven correction

P09-19 complete-object preparation first failed before publication. The original
rectangle uses `numberingType=NONE`, not PICTURE, so it correctly failed kind checks.
After fixture-only category preparation, the reader still rejected the root-equal
`hp`/`hc` redeclarations on the source object. No HWPX was published in these failures.

The product adapter now admits only declarations identical to those inherited from
the section root, preserving them verbatim. Conflicting/new ancestor bindings stay
rejected. Added an exact-insert-reversal test for redundant declarations and retained
the negative shadowing test with a genuinely conflicting namespace.

Focused public tests: **9/9 PASS**. Package all-target/all-feature locked offline
Clippy with `-D warnings`: **PASS**. The private plan tamper test is unchanged.
Public tests use **synthetic object shells**. Four separately prepared P09-19 packages
also exercise complete source payloads through this adapter with byte-deterministic
retry, source-drift rejection, field reversal and package graph validation.

The original numeric adapter/domain engine hashes and shared export shape remain
unchanged. P08's live shared-`lib.rs` source hold remains separate and unresolved.

`green_rows=0`, `actual_hangul=false`, `semantic_save_reopen=false`, `render=false`,
`p09_complete=false`, `product_complete=false`. No historical failed receipt was
relabelled and no new COM/UI run occurred.
