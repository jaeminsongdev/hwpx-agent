---
name: edit-hancom-document
description: Safely revise an existing HWPX project using stable selectors, a dry-run semantic diff, preservation policy, expected revisions, atomic publication, and validation.
---

# Edit Hancom Document

Use this skill for changes to an existing document when no more specialized workflow is dominant.

## Primary tool sequence

1. `project_open`: load the canonical project head rather than reconstructing state from chat.
2. `document_inspect`: resolve stable logical IDs, fields, bookmarks or fingerprinted context.
3. `document_plan`: compile the requested semantic operations and preservation impact.
4. `document_edit`: first set dry run true and best effort false; after review, execute with the same plan against the expected revision.
5. `job_get`: poll the edit job to a terminal state.
6. `document_validate`: verify the new revision and preservation requirements.
7. `document_render`: render affected pages when visual evidence is required.

## Guardrails

Never edit the first matching string without a stable selector. A stale revision produces an explicit
conflict path; never silently retarget the head, overwrite the source revision or delete history.
