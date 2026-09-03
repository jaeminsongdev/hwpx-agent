# Page setup v0 to v1

`hwpx-agent.page-setup/1` introduces the first typed page-setup boundary; no prior wire version is
accepted or silently upgraded.

## Additive model

- positive unrotated HWPUNIT width and height;
- typed portrait/landscape orientation;
- typed single/facing/top-bottom gutter placement;
- explicit left/right/top/bottom/header/footer/gutter values;
- checked effective-page and printable-body metrics; and
- deterministic lower/section-patch receipts with bounded SHA-256 identities.

## Rejection behavior

Unknown fields, raw XML, floating-point HWPUNIT, implicit orientation swaps, negative values,
impossible printable regions, unsupported namespaces, multiple `pagePr` records, and over-limit
inputs are rejected. Callers must submit a new version-1 request after resolving the typed error;
there is no lossy v0 fallback.
