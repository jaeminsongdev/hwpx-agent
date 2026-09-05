# P16 MAIN integration source qualification

This qualification composes MAIN parent `9cc1db3` and P16 parent `62542b0` without rewriting the
immutable PostgreSQL or P15 source-qualification contracts. The merge changes the PostgreSQL
runtime-source set only at `Cargo.lock`: P05 diagnostics add the already locked `serde` and
`serde_json` development dependencies for `hwpx-package`. The corresponding package manifest and
the two qualification validators/tests are also bound as explicit predecessor/current hash pairs.

The successor revalidates both predecessor contract bytes, both actual PostgreSQL receipts, all
unchanged runtime hashes, each P15 predecessor contract, every historical context source and every
guard source. A replacement is accepted only when its P16-parent SHA-256 and current SHA-256 match
the new immutable contract exactly. Missing evidence, extra paths, changed history, claim promotion
or partial qualification fails closed.

This is source qualification only. It does not claim that the merged source has rerun actual
PostgreSQL acceptance, that P15/P16 is complete, that a registered host or real Hangul was used, or
that the product is production-ready. The integrated PostgreSQL harness and full current/independent
regressions remain required. Next reasoning: `max`.
