---
name: template-preserve-fill
description: Analyze and fill a supplied Korean school, institutional, or company HWPX template while preserving unknown content, layout, styles, assets, fields, and protected regions.
---

# Preserve and Fill Hancom Template

Use this skill when the user supplies an existing form or requires its format to remain unchanged.

## Primary tool sequence

1. `project_open`: load the canonical template revision and target profile.
2. `template_analyze`: inventory slots, fields, repeated rows, protected regions and unknown content.
3. `document_plan`: compile stable targets in surgical preservation mode.
4. `document_edit`: first set dry run true and best effort false; show touched parts and unknown-content impact before execution.
5. `job_get`: poll the accepted fill job to a terminal state.
6. `document_validate`: verify affected content semantically and untouched content by the declared preservation policy.
7. `document_render`: compare affected pages when visual evidence is required.

## Guardrails

Do not normalize a whole template to fill a few fields. Never execute embedded scripts or OLE
content, edit a protected region without authorization, or overwrite the supplied source revision.
