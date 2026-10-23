# P09 stored comment preparation v0 → v1

기존 DocumentGraph/comment request/revision/artifact schema 또는 serialized original receipt를
변경하지 않는 additive Rust preparation API다. 기존 StoredFormProvider에
prepare_comment_json(StoredCommentInputs, now)을 추가하고 immutable PreparedStoredComment 및
hwpx-agent.product-stored-comment-preparation/v1 receipt를 제공한다.

입력은 head/plan/request/logical insertion이며 source/IR artifact ID와 complete comment state를
public request로 받지 않는다. 원래 sealed revision binding과 canonical IR 속성에서만 읽는다.
재검증은 원래 source/IR reader와 원래 CommentBuilder/compiler 전체 replay를 사용한다.
기존 form API/guard는 바뀌지 않고 부모 module 내부 visibility만 확장한다.

unknown/duplicate/oversized/missing state, kind/media/digest/canonical drift, 문서/actor/scope,
독립 ACL/state/AEAD, stale 및 download 중 변경된 head의 negative 검사와 기존 source/form/comment
회귀를 추가했다. synthetic IR/storage fixture PASS는 실제 HWPX/source-native 의미 증거가 아니다.
current route는 항상 거부하며 SQL/native/issuer/atomic execution/publication/Gate를 승격하지 않는다.
