# P09 formula result output v0 -> v1

기존 read-only source evaluator/receipt/API 의미와 native cache Unverified 상태는 바꾸지 않는다.
새 lower_results와 authenticated prepare_results/verify/with_verified_bytes는 별도 candidate 출력 API다.
기존 typed source import를 새 full-document/native/route evidence로 업그레이드하지 않는다.

Rust PatchIntent에 ReplaceLeafText { target: XmlElementSelector, value: PatchText }가 additive로 들어간다.
exhaustive Rust consumer는 이 semantic leaf-only edit을 명시적으로 다뤄야 한다. raw XML/byte offsets가 아니며
root/children/comment 대상 거부, original selector/budget/conflict/preservation/writer 검사는 동일하다.
SQL/request schema/dependency/target/native dispatcher/registry/trust/기존 private 원장은 변경하지 않는다.

새 FormulaResultOutputReceipt의 outside_result_leaf_edits_exact는 self-closing tail expansion을 포함한
declared edit 바깥 bytes 보존이다. formula_ast_and_numeric_inputs_preserved는 re-import/component 범위다.
native_recalculation_verified=false; execution_publication_authority=unqualified이며 route는 계속 거부한다.
serialized receipt는 provenance 보고용이지 caller authority 또는 prepared object deserialize 경로가 아니다.

negative 검사는 source drift, unknown/absent targets, no-op, observed protection, tiny writer, unsafe/mixed leaf,
cached actor/scope/head/ACL/AEAD/quarantine 및 callback denial을 포함한다. 실제 SQL/한글/렌더 acceptance는 별도다.
이전 부모6개의 whole preimage와 모든 이전 raw pin/실패를 보존하며 PLANS.md를 복원하지 않는다.

