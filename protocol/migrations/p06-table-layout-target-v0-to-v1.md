# P06 table-layout product target v0 to v1

This contract introduces `hwpx-agent.p06-05-table-layout-target-contract/v1` for builder output
`hwpx-agent.p06-05-table-layout-target/v2`. The earlier uncontracted `/v1` builder target is kept as
immutable diagnostic evidence, not upgraded in place.

The `/v1` target changed the four table-cell texts and table geometry while preserving Hangul's
source `hp:linesegarray` values. Those values are derived layout caches. After the text changes they
contained stale and internally impossible text positions. Exact licensed Hangul 2020 build
`11.0.0.9136` returned `Open=false` for target SHA-256
`a678588188593c250b33205f1660fef6c301280cd5ae30deb4b6a03f185055bc`; no text, save/reopen,
geometry, wrapping, or PDF semantic evidence was produced.

The `/v2` builder fails closed unless every edited source cell paragraph has exactly one direct
`hp:linesegarray`, replaces only the selected text content, deletes the exact outer byte span of
each stale cache, and requires zero such caches on target readback. It never guesses cache values;
Hangul must regenerate them when it opens and saves the document. Missing or duplicate caches,
unexpected paragraph shape, edit overlap, wrong input identity, and an existing destination all
fail before publication or without overwrite.

There is no automatic migration and no historical result is promoted. The new deterministic target
still requires a fresh Hangul 2020 open, exact text readback, save/reopen, geometry and wrapping
inspection, and PDF visual review. P06-05, P06, production, arbitrary documents, other PCs, and
other Hangul versions remain unclaimed.
