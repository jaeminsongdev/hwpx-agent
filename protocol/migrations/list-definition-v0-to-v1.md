# List definition v0 to v1

## Contract

`hwpx-agent.list-definition/1` is the first public typed list-definition and sequence boundary. There
is no compatible v0 payload. Callers must construct typed definitions, paragraph bindings and sequence
operations; raw XML or backend action identifiers are never migrated.

## Required changes

- Use dense one-based numbering and bullet IDs. Keep zero-based paragraph heading levels distinct from
  one-based XML paraHead levels.
- Resolve OUTLINE idRef 0 through an explicit section outline numbering ID. Resolve NUMBER/BULLET only
  through their typed one-based domains.
- Preserve numbering definition start, ten ordered level starts/styles/templates and the exact
  UINT32_MAX no-character-style sentinel.
- Express character bullets with useImage=false, one Unicode scalar mark, optional checked mark and one
  typed paragraph-head style. Image bullets remain unavailable until P08 binary closure.
- Supply a nonzero sequence ID for every evaluated item. Continuity, nesting and restart are explicit
  engine inputs; visual definition reuse never implies shared counters.
- After semantic deduplication, apply complete one-based maps only through the typed paragraph-heading
  and section-outline rewrite APIs.

## Rejection behavior

Unknown elements/attributes/enums, sparse IDs or levels, missing/extra level records, malformed
templates, image bullets, unresolved character styles, malformed maps, dangling paragraph or outline
references, invalid sequence transitions/restarts, overflow and finite-limit violations reject with
stable `list_definition_*` codes before publication.

## Deferred compatibility

Rendered marker shape, image bullets, arbitrary packages, other PCs and Hangul 2022/2024 require their
own later implementation or exact-build evidence. They cannot be inferred from this contract.
