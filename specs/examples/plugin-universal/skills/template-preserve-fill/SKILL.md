---
name: template-preserve-fill
description: Analyze and fill an existing Korean institutional/school/company HWPX template while preserving unknown XML, layout, styles, headers, assets, fields, and protected regions.
---

# Preserve and Fill Hancom Template

## Use this when

The user supplies an existing form or asks to keep a school/company format unchanged.

## Workflow

1. Run `template_analyze`; inventory slots, fields, tables, repeated rows, headers/footers, protected regions, unknown controls, OLE/scripts, and style/page assumptions.
2. Produce a TemplateContract. Do not edit until required slots and preservation levels are resolved.
3. Use `surgical_preserve`; target named slots/fields/bookmarks/stable IDs.
4. Dry-run with touched part list, semantic diff, and unknown-content impact.
5. Execute to a new revision; verify untouched parts by byte/token policy and affected content semantically.
6. Run target Hancom save/reopen and visual diff for production output.

## Guardrails

Do not normalize the entire document merely to fill a few fields. Never execute embedded scripts or OLE content.
