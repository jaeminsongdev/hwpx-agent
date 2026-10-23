# P09 caller full-IR comment preparation v0 to v1

Adds product-library preparation only. Existing domain comment model/request/plan schema and original
DocumentGraph schema remain unchanged. New private caller-IR properties are p09_complete_comment_state_json,
p09_complete_comment_entry_json, p09_complete_comment_style_json and p09_complete_comment_section_json.
Complete canonical domain JSON and every matching actual section/style/review view are required; missing
properties are rejected, not initialized with defaults. Root state binds ordered component inventories;
Graph review catalog remains canonical by logical ID. Caller insertion anchors bind real section/node
identities but do not qualify native run/inline coordinates.

Existing actual import/partial/security admission remains denied. Unknown native author/time/state is
never migrated into a complete CommentDocumentState. No runtime/native authority or route migration is
performed. All five original P09 operations use CommentBuilder and OperationPlanCompiler and no P11
delete operation exists. HWPX lowering, authenticated provider, issuer/execution/publication and native
save/reopen/render are still unavailable/unverified. Prepared product route remains unqualified.
