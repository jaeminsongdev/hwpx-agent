---
name: compose-math-exam
description: Compose Korean math exams, worksheets, answer sheets, or question banks that need exact page layout, native editable equations, tables, figures, scoring, and question split rules.
---

# Compose Math Exam

Use this skill when the requested document is primarily a mathematics assessment or worksheet.

## Primary tool sequence

1. `project_create`: create a revisioned project when no project exists.
2. `capability_check`: verify page, table, native-equation, object and reference capabilities.
3. `document_plan`: compile sections, questions, scores, answers, exact dimensions and keep rules.
4. `document_create`: submit the accepted plan in normalized authoring mode or the approved template mode.
5. `job_get`: poll the creation job to a terminal state.
6. `document_validate`: verify score totals, numbering, native equation semantics and split rules.
7. `document_render`: render every required page and check clipping and major bounds.
8. `artifact_get`: request bounded preview or attachment delivery after authorization.

## Guardrails

Do not guess ambiguous paper names; resolve exact millimetres. Keep equations native and editable.
Do not silently split a question, alter a score, or promote missing Hangul evidence to pass.
