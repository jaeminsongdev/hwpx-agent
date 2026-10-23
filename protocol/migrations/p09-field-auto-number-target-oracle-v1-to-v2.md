# P09 field auto-number target oracle v1 to v2

v1 `state=pass` proved only four ordered native auto-number shapes with canonical numeric values.
It did not compare the values to the expected fixture projection. Legacy output MUST NOT be
reinterpreted as a semantic target PASS, object-number qualification or product evidence.

v2 adds separate `structural_state`, `semantic_state`, `expected_projection`, native object counts
and caption-ancestor observations. Without expected values, its overall state is `structural_only`.
With an exact typed expectation it returns `pass` or `fail`; differing values report
`semantic_projection_mismatch`. Every output keeps product, render and automation claims inactive.

To migrate, retain the original fixture/trace/output bytes and re-inspect them under their SHA-256
locks. Use the P09-17 qualifier to bind the closed fixture v1 manifest and lifecycle trace, and write
a new exclusive-create qualification receipt. The independent qualification schema remains v1;
the oracle schema becomes `hwpx-agent.p09-17-field-auto-number-target-oracle/v2`.

Do not normalize mismatching values to zero, rewrite failed artifacts, treat PDF metadata as render
proof, enable fallback routing, or promote the static P09 matrix from this migration alone.
