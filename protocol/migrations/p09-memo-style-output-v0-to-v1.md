# P09 existing source memoPr style output

Status: explicit readonly in-memory package derivation; NOT native semantic/product execution admission.

ImportedDocumentCatalog::lower_memo_style takes the fresh original package, actual source memo
definition anchor, seven explicit typed native style values and validated writer limits. It does not
accept XML, byte offsets, author/time/state maps or new native IDs. No external operation wire,
CommentDocumentState schema, REF ownership or SQL schema is changed.

MemoStyleOutput is immutable and non-deserializable. The receipt binds whole source/output digests,
output size, changed attribute/part counts and the explicit unqualified boundary. Output bytes are
available only through original verified PackageArtifact callbacks. Stored callers must use the
original fresh source/catalog checks plus complete lowering replay before their output callback.
The product execution/publication route remains denied.

Original source IDs now recognize hh:memoPr/id as the same MemoShape declaration family as the
retained historical hh:memoShape/id. Duplicate IDs across both spellings, foreign namespace and
missing references remain errors. Source preservation and strict FormulaV3 ID checks are applied
before and after output; no reference validator or native protection policy is bypassed.

P09-96_MEMO_STYLE_OUTPUT_POLICY.md documents the closed scope. Existing native style output is
one required branch, not complete comment insertion/show-hide/resolve/body lowering, a complete
source-native typed comment state, native semantic verification or a P09 Gate pass.
