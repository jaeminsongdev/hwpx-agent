# P06 table pagination v0 to v1

Date: 2026-09-08

`v0` had no typed table-pagination model and allowed callers to treat renderer-specific page
breaks as unstructured values. `hwpx-agent.table-pagination/v1` introduces an additive, strict
boundary for `allow`, `avoid_row`, `avoid_table`, and `required_keep`; a contiguous repeat-header
prefix; exact row heights and split eligibility; vertical caption/keep metadata; and a separate
`hwpx-agent.table-pagination-observation/v1` renderer observation.

Migration is explicit. A caller must resolve one validated `TableGrid`, provide every row exactly
once in ascending order, classify nested/unbreakable rows without guessing, and obtain available
page heights and fragments from an identified renderer. Unknown values, absent measurements, or a
legacy boolean page-split flag are not coerced. HWPX and automation adapters must use their own
version-pinned mappings and may not promote this pure validation into target-renderer evidence.

