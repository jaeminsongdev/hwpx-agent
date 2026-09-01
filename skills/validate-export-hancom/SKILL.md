---
name: validate-export-hancom
description: Validate, render, print, or export Hancom documents with honest evidence states, target Hancom reopen checks, visual comparison, accessibility/security checks, and loss reports.
---

# Validate and Export Hancom Document

## Use this when

The user asks whether a document is correct, wants a preview, PDF/DOCX/HWP/image/text export, or needs print/accessibility/security assurance.

## Workflow

1. Inspect the revision and determine required validation levels for the requested use.
2. Run package/schema/relationship/semantic checks first.
3. When target Hancom is required, run clean-process open and save/reopen.
4. Render affected/all pages and report font substitution and visual/layout differences.
5. For export, call `document_export` with a loss policy; reopen the exported artifact and attach the loss report.
6. For print/external side effects, show destination/settings and require explicit confirmation.

## Evidence language

Use only `pass`, `fail`, `unverified`, or `skipped_by_policy`. Missing a worker or renderer never becomes a pass.
