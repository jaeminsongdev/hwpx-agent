---
name: resume-hancom-project
description: Resume the same Hancom document project across ChatGPT Web, Codex remote, and Codex local using remote revision state, checkpoints, conflicts, and artifact history.
---

# Resume Hancom Project

## Use this when

The user says to continue, resume, modify the prior document, or move work between ChatGPT and Codex.

## Workflow

1. Call `project_open`; do not reconstruct state from chat history.
2. Summarize head revision, latest checkpoint, target profile, unresolved warnings, active jobs, and recommended next operation.
3. Use the current head as `expected_revision` unless the user explicitly selects another revision/branch.
4. After a meaningful change, create a checkpoint with a concise note and evidence summary.
5. On conflict, preserve both revisions and offer rebase/branch/manual merge; never overwrite remote head.

## Local Codex rule

`.hancom/project-state.json` is a cache/mirror. The remote project service remains canonical and must be reconciled before push.
