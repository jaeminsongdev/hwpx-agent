# Tab definition v0 to v1

## Contract

`hwpx-agent.tab-definition/1` is the first public typed tab-definition boundary. There is no compatible
v0 payload. Callers must construct typed definitions and stops; raw XML or backend action identifiers
are never migrated.

## Required changes

- Use dense zero-based definition IDs and keep autoTabLeft and autoTabRight explicit in output.
- Express custom stops as Direct or HwpUnitChar typed variants.
- Use LEFT, RIGHT, CENTER or DECIMAL alignment and the shared twelve-value LineType2 leader enum.
- Preserve an optional CHAR/HWPUNIT direct unit. For HwpUnitChar, preserve both current and fallback
  items and their exact scale pair; do not normalize one branch away.
- Keep stop positions non-negative, use one effective unit per definition and order them strictly by
  effective fallback/direct position.
- After semantic deduplication, apply the complete old-to-new map only through the typed paragraph
  tab-reference rewrite API.

## Rejection behavior

Unknown elements/attributes/enums, VERTBAR without exact current-target admission, negative or unordered
positions, inconsistent compatibility pairs, bad counts/IDs, malformed maps, dangling paragraph
references and finite-limit overflow reject with stable tab_definition_* codes before publication.

## Deferred compatibility

Target canonicalization and actual layout remain current-PC Hangul 2020 readback evidence. Other PCs and
Hangul 2022/2024 require their own future profiles and cannot be inferred from this contract.
