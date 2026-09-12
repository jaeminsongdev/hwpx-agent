# P09 TOC/index v0 to v1

- There is no accepted v0 wire representation.
- Producers must emit `hwpx-agent.toc-index/v1` with complete ordered section, TOC-source,
  TOC-mark, index-mark, generated-body, and occupied non-TOC/index native-ID/name inventories.
- Raw XML, HAction names, filesystem paths, clear-text headings/index keys, inferred anchors,
  implicit collation, and implicit native parameters are not migratable inputs.
- TOC sources migrate only with stable identity, exact anchor and level, text/numbering/style/page
  projection digests, opaque state/properties, and protection.
- TOC marks migrate only with a live containing source and explicit native `ignore` state. Index
  marks migrate only with fresh logical/control identity, paired primary/secondary key and sort-key
  digests, page assignment, native payload, opaque state, and protection.
- Generated bodies migrate only with complete settings, exact generated-content digest, exact
  complete-source projection, and consistent `current` or `stale` classification.
- `TABLEOFCONTENTS` parameters and index generated-range semantics remain unverified; v1 does not
  imply direct HWPX lowering, REF-040 update automation, or installed-Hangul support.
- Missing, duplicate, dangling, outside, colliding, stale-on-create, malformed, unbounded, or locked
  state fails closed. No level, style, leader, collation, page, or layout defaults are synthesized.
