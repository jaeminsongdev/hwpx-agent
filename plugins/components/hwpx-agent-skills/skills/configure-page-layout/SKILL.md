---
name: configure-page-layout
description: Set or change HWPX paper dimensions, orientation, margins, gutter, sections, columns, headers, footers, master pages, or page numbering.
---

# Configure Page Layout

Use this skill when physical page geometry or section layout is the main request.

## Primary tool sequence

1. `project_open`: load the canonical head and target profile.
2. `document_inspect`: inspect section geometry and affected anchored objects.
3. `capability_check`: verify every requested page and section operation.
4. `document_plan`: compile exact dimensions, selectors and overflow checks.
5. `document_edit`: first set dry run true and best effort false; execute against the expected revision only after review.
6. `job_get`: poll the layout job to a terminal state.
7. `document_validate`: verify semantic reopen, page count and requested oracle levels.
8. `document_render`: compare affected pages and major bounds.

## Guardrails

Present exact width and height for region-dependent paper names. Reject impossible geometry. Do not
silently shrink content, change margins, retarget another section or overwrite the source revision.
