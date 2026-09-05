---
name: create-hancom-document
description: Create a new editable HWPX document for reports, worksheets, forms, letters, or general Korean documents with explicit layout, content, validation, and output requirements.
---

# Create Hancom Document

Use this skill for a new general-purpose HWPX document; route math assessments and supplied templates
to their specialized skills.

## Primary tool sequence

1. `project_create`: establish a revisioned project and target profile.
2. `capability_check`: verify every nontrivial requested capability and oracle level.
3. `document_plan`: compile the intent before execution and surface ambiguity or unsupported work.
4. `document_create`: submit the accepted plan with the expected revision and idempotency key.
5. `job_get`: poll an accepted asynchronous creation to a terminal state.
6. `document_validate`: run the requested structural, semantic and target checks.
7. `document_render`: create bounded preview evidence when requested.
8. `artifact_get`: deliver authorized metadata, preview or attachment without exposing local paths.

## Guardrails

Never emit raw document XML, private automation identifiers or arbitrary paths. Inputs are immutable.
Do not replace native equations with images or claim that a preview equals Hangul without its oracle.
