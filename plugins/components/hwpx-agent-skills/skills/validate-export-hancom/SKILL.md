---
name: validate-export-hancom
description: Validate, render, preview, or export an HWPX revision with honest evidence states, target-Hangul checks when available, bounded artifact delivery, and explicit loss reporting.
---

# Validate and Export Hancom Document

Use this skill when the user requests correctness evidence, a preview, or an export such as PDF,
DOCX, HWP, image, or text.

## Primary tool sequence

1. `document_inspect`: resolve the exact revision and bounded features under review.
2. `document_validate`: run the required package, semantic, target, accessibility or security levels and fail on unverified when requested.
3. `job_get`: poll an accepted validation or export job to a terminal state.
4. `document_render`: render affected or all pages and report substitutions or layout differences.
5. `document_export`: export with an explicit format, profile, expected revision, loss policy and loss report.
6. `artifact_get`: deliver authorized metadata, preview or attachment with bounded lifetime.

## Guardrails

Report only pass, fail, unverified or skipped by policy. Missing workers never become pass. No public
direct-print tool exists: do not claim printer execution; explain that only validation, render and
export are available. Never expose local paths or overwrite the source revision.
