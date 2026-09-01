---
name: edit-hancom-document
description: Safely edit an existing HWPX/HWP project by stable selectors, semantic operations, dry-run diff, preservation policy, atomic revision, and validation.
---

# Edit Hancom Document

## Use this when

The user wants to change text, styles, paragraphs, page setup, tables, equations, images, references, review data, or metadata in an existing Hancom document.

## Required workflow

1. Open the project/revision with `project_open` or inspect the artifact with `document_inspect`.
2. Prefer logical IDs, template slots, fields, bookmarks, table/equation/object IDs. Text-context targeting is a fallback and must include a fingerprint.
3. Run `document_plan` and `document_edit` with `dry_run=true`; present affected nodes/pages, semantic diff, selected backend, preservation impact, and warnings.
4. Execute only against the expected revision with an idempotency key.
5. Validate semantic reopen and all feature-required oracle levels. For template edits, include untouched-part preservation evidence.
6. Return the new revision; never overwrite or delete the source revision.

## Conflict handling

A stale revision must produce branch/rebase/manual-merge choices. Never silently retarget the current head or apply an edit to the first matching string.
