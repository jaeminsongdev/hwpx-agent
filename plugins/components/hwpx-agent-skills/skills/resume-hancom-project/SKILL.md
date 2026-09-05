---
name: resume-hancom-project
description: Resume a prior HWPX Agent project across ChatGPT or Codex from canonical revision history, active jobs, checkpoints, warnings, and explicit conflict handling.
---

# Resume Hancom Project

Use this skill when the user asks to continue an earlier HWPX Agent project or revision.

## Primary tool sequence

1. `project_open`: load canonical project state; never reconstruct it from conversation history.
2. `project_history`: inspect bounded revision and checkpoint history when needed.
3. `job_get`: inspect active or recently terminal work before starting another operation.
4. `project_checkpoint`: checkpoint a selected completed revision after a meaningful accepted change.

## Optional cancellation

Use `job_cancel` only after a fresh explicit cancellation request and host confirmation. It is the
only destructive public tool and requires the expected revision, idempotency key, job ID and reason.

## Guardrails

Summarize the head, target profile, latest checkpoint, warnings and next operation. On conflict,
preserve both revisions and offer an explicit branch, rebase or manual merge path. A local state file
is only a cache; it never overrides the canonical project service.
