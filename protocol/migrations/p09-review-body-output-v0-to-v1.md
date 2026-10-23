# Existing observed review paragraph-body output

Status: pure source-preserving in-memory derivation, not full comment product/native admission.

ImportedDocumentReviewBodies::lower_body accepts the exact fresh original package, an actual
observed MEMO/hiddenComment marker anchor, complete typed TextFlow paragraphs and writer limits.
It does not accept caller XML, offsets, native author/time/state defaults or raw execution actions.
Missing bodies, zero target paragraphs and semantic no-op are rejected. The selected content is
explicitly replaced; original wrapper tags/attributes and every byte outside its content stay exact.
Generated paragraphs use the original TextFlowWriter and independent complete namespace bindings.

The original generic patch enum adds ReplaceElementContent with a bound XmlElementSelector and
bounded independently ValidatedXmlFragment children. Existing selector/overlap/ID/preservation
checks remain in force. Both each fragment and the aggregate content size are checked; self-closing
targets without a content span are rejected. No raw unchecked writer or parser alternative is added.

ReviewBodyOutput and PreparedStoredReviewBody are immutable and non-deserializable. Receipts bind
whole source/output package hashes, whole review observation hashes, size/kind/counts and explicit
unqualified metadata/execution status. Stored callbacks require original fresh authorization and
whole deterministic lowering replay. No new artifact ingest, revision commit or publication occurs.

No CommentDocumentState/CommentRequest/SQL/REF ownership schema changes are made. Original full
typed caller-IR compiler admission and partial/protection guards are not bypassed. Full native
metadata/state/coordinates, rich table/drawing output, insertion/show/resolve/delete lowering,
complete compiler/protection/issuer/durable/atomic publication integration and actual native
save/reopen/render/differential qualification remain incomplete. P09 Gate stays OPEN.
