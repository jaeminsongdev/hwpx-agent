# P09-109 저장된 완전한 호출자 댓글 본문과 기존 compiler 연결

## 기존 제품 경로

원래 StoredFormProvider의 source/full_document_ir sealed revision 선택·actor scope·head·
독립 result/IR ACL·AEAD·scanner/kind/media/digest·canonical graph 검사를 그대로 사용한다.
원래 stored_state/context와 P108 CommentRichContext/RichCommentOperationPreparation을
연결한다. 공개 source/IR artifact selector나 기존 body override를 새로 받지 않는다.
입력은 원래 StoredCommentInputs와 삽입할 때만 제공하는 새 CommentRichBody다.
state 및 기존 본문 전체는 실제 다운로드한 revision-selected IR metadata에서 읽는다.

현재 검증은 실제 서비스 API/AES-GCM과 in-memory repository/scanner/fixture actor 및
명시적인 synthetic complete caller IR을 사용한다. source fixture bytes는 native HWPX가
아니다. authenticated storage evidence는 native source metadata/import 또는 SQL durability
증거가 아니다. 한글/COM/접근허용이나 실제 운영 DB를 사용하지 않는다.

## 정확한 JSON과 전체 본문 검증

canonical outer graph만으로 그 안의 body JSON 문자열까지 신뢰하지 않는다.
private deny_unknown_fields DTO로 typed Flow를 읽고 P108 bodies_json과 exact byte equality를
확인한다. missing/unknown/duplicate/lexical aliases 및 incomplete body view를 거부한다.
public body/receipt/prepared operation에 Deserialize 또는 mutable authority accessor를
추가하지 않는다. 원래 body order/review ID/body digest/style/resource/ID/table/nested caller
protection/whole document partial/protection admission이 source 및 final target에서 적용된다.

inner body input8MiB 제한과 원래 graph string/total/depth/byte limits를 모두 유지한다.
기존 graph string ceiling이 더 먼저 거부하면 그 검사를 우회하거나 넓히지 않는다.
삽입 actual body와 final compiler hash는 P108의 bounded preparation을 그대로 사용한다.
main document Flow를 review body로 덮거나 body를 plain cache로 대체하지 않는다.

## 재검증과 실행 경계

immutable preparation verify는 source/result 및 IR을 다시 독립적으로 다운로드한다.
scope/head/artifact/binding/whole graph/state/body/final compiler/receipt 전부를 재구성해
비교한다. fresh 권한·암호문·quarantine·head 실패는 RouteUnqualified보다 먼저 반환한다.
반복 읽기는 atomic lease/CAS가 아니다. getter는 memory candidate만 반환하며 publication
또는 지속 저장 권한이 아니다. actual ingest/head commit/output publication은 하지 않는다.

native_metadata_verified/hwpx_lowered/execution_authority_verified는 계속 false이며 route는
fresh 검증 후 항상 기존 RouteUnqualified다. 실제 원본 author/time/state/native coordinate
mapping, native lowering/save-reopen/render/oracle, durable SQL 제품 통합, trusted issuer/
보호/atomic publication, field/Date/external/document 의미 및 actual P84 SQL 검증은 미완료다.

기존 P95 보고서의 locked actual capture는 metadata positive가 아니다. 보관된 공식
fieldBegin의 generic parameters/metaTag 지원만으로 author/time/state 의미를 발명하지 않는다.
P09~P20 전체 목표를 유지하고 최소6 큰 잔여 묶음을 이번 부분 구현만으로 차감하지 않는다.
P09/A12/A13 OPEN; native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED;
P26 failed_semantic_non_green; P62/P84_SQL UNRESOLVED; green0/no P10/product false/goal active.
사용자 dirty/private/native/실패 증거, HEAD 및 PLANS 삭제 상태를 보존한다.
