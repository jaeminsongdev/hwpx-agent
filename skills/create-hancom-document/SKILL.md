---
name: create-hancom-document
description: Create a new editable Hancom HWPX document from content, page/layout requirements, styles, tables, equations, images, and output constraints. Use for reports, worksheets, exams, forms, and general Korean documents.
---

# Create Hancom Document

## Use this when

The user wants a new `.hwpx`/Hancom document, including custom paper size, margins, columns, tables, native equations, images, headers/footers, page numbering, or a reusable template.

## Required workflow

1. Resolve exact output format, target profile, document size in mm/preset, orientation, margins, sections, columns, fonts, and validation requirement from the request. Do not guess ambiguous physical sizes.
2. Call `capability_check` for every nontrivial capability group and required oracle level.
3. Call `document_plan` with `compile_only=true`. Surface unresolved ambiguities and high-risk/external operations.
4. For a plain new document use `normalized_authoring`; for a supplied template use `surgical_preserve` and `template_analyze` first.
5. Call `document_create` with expected revision/idempotency data.
6. Poll `job_get` until terminal, then call `document_validate` for the requested gates and `document_render` for page preview.
7. Return the created artifact, revision, validation state, exact page dimensions, warnings, and any unverified evidence.

## Guardrails

- Never emit raw HWPX XML or raw HAction names.
- Native equations only; no image fallback unless the user explicitly requests an export-only approximation.
- Input/source artifacts are immutable.
- Do not claim a preview is identical to Hancom unless target Hancom oracle evidence passed.
