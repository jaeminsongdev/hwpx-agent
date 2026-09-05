---
name: insert-native-equations
description: Insert or revise native editable HWPX equations from LaTeX, MathML, EqEdit, or a math AST with semantic round-trip and requested visual validation.
---

# Insert Native Equations

Use this skill when mathematical or scientific notation must remain editable as native equations.

## Primary tool sequence

1. `project_open`: load the canonical source revision and target profile.
2. `document_inspect`: resolve the equation or insertion selector without exposing raw internals.
3. `capability_check`: verify the source notation, equation tier and target oracle.
4. `document_plan`: compile exactly one source representation and fail on ambiguous syntax.
5. `document_edit`: first set dry run true and best effort false; execute only the accepted native-equation operation.
6. `job_get`: poll the edit job to a terminal state.
7. `document_validate`: compare normalized math semantics after reopen.
8. `document_render`: render required pages for clipping or baseline evidence.

## Guardrails

No silent text or image substitute is allowed. Compiler success alone is not validation. Preserve an
unproven legacy equation in surgical mode and leave the requested edit unverified.
