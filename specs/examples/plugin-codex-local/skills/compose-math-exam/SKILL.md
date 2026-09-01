---
name: compose-math-exam
description: Compose and revise Korean math exam papers with precise paper size, one/two-column layout, question keep rules, editable Hancom equations, tables, figures, scoring, and separate answer sheets.
---

# Compose Math Exam

## Use this when

The user asks for a mathematics test, worksheet, answer sheet, or question bank in Hancom format.

## Workflow

1. Parse the exam spec into sections, questions, scores, choices, solutions/answers, asset references, and layout constraints.
2. Resolve paper preset or exact mm, margins, column model, question numbering, header/footer, school metadata, and whether the answer key is separate.
3. Check `page.*`, `table.*`, `eq.*`, `obj.*`, and `ref.*` capabilities for the target profile.
4. Build an OperationPlan that uses native equations and question-level `keep_together`/split policies. A question may split only under the explicit long-question policy.
5. Create or fill a template; render all pages; run question-split, table-page-split, equation semantic round-trip, and target Hancom open/save validation.
6. Produce HWPX, preview, split report, score total check, and optional answer/solution artifact.

## Non-negotiable checks

- Score total and question number uniqueness.
- Native equation editor round-trip for required tiers.
- No clipped tables, figures, equations, headers, or footers.
- Page size receipt contains exact millimetres, not only a colloquial paper name.
