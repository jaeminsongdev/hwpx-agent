---
name: build-hancom-tables
description: Create or revise structured tables in a revisioned HWPX project when the request centers on rows, columns, merges, formulas, repeated headers, borders, or page splitting.
---

# Build Hancom Tables

Use this skill when a table or structured form is the main requested feature.

## Primary tool sequence

1. `project_open`: load the canonical source revision and target profile.
2. `capability_check`: verify the requested table and target-profile capabilities.
3. `document_plan`: compile the logical grid, spans, sizes, formula rules and page policy.
4. `document_edit`: first set dry run true and best effort false; execute only after the grid diff and merge-content policy are accepted.
5. `job_get`: poll an accepted asynchronous operation to a terminal state.
6. `document_inspect`: read the new revision's bounded table snapshot.
7. `document_validate`: check grid semantics, formulas, merges, repeat headers and page splits.
8. `document_render`: render boundary pages when visual evidence is required.

## Guardrails

Use stable table and cell identifiers. If a merge contains multiple nonempty cells, require an
explicit concatenate, first, distribute or reject policy. Never overwrite the source revision or
claim target-Hangul fidelity when its oracle is unverified.
