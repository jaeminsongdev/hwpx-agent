---
name: insert-native-equations
description: Insert or edit truly native, editable Hancom equations from LaTeX, MathML, EqEdit, or Math AST with semantic round-trip validation.
---

# Insert Native Equations

## Use this when

The document includes mathematical or scientific notation that must remain editable in Hancom.

## Workflow

1. Accept exactly one source representation: LaTeX, MathML, EqEdit, or Math AST.
2. Parse and normalize to MathAst; stop on unsupported or ambiguous syntax.
3. Compile to the target EqEdit dialect and insert a native equation object through the selected backend.
4. Save/reopen, read the equation script, parse it again, and compare normalized AST.
5. For final output, run editor smoke and render/baseline checks required by the tier.

## Guardrails

- No silent text or image substitute.
- Never treat compiler success alone as validation.
- Preserve legacy scripts in surgical mode when semantic editing is not proven safe.
