# P09-98 기존 메모·숨은 설명의 원본 결속 삭제 정책

## 요구사항과 단계 경계

원래 P09-04에는 insert/style/show/resolve/delete 및 author/time/readback이 요구된다.
이번 변경은 실제 읽은 MEMO/hiddenComment의 삭제 출력 경로를 구현한다. 전체 요구사항을
문단 본문 변경이나 구조 검사만으로 완료 처리하지 않는다.

원래 generated contract의 `review.comment_delete`/`review.comment_delete_all`은 P11이며
review.accept, change_readback/save_reopen/visual_diff가 필요하다. 해당 계약·등록부·단계와
지원 표기는 변경하지 않는다. P09 내부 삭제 출력은 P11 공개 기능 승인이나 전체 메모
compiler 연결을 뜻하지 않는다. 새 공개 capability/action/raw XML 경로는 만들지 않는다.

## 원본 선택과 출력

- 원래 Source→Forms→Fields→Review importer의 완전한 원본 재검증을 먼저 수행한다.
- 요청은 실제 생성된 immutable marker SourceAnchorHandle과 원래 WriterLimits뿐이다.
  caller XML/offset/작성자/시간/상태/증거 주장으로 대상을 만들지 않는다.
- MEMO는 원래 paired-field collector가 결속한 begin/end의 ctrl subtree를 함께 삭제한다.
  표식 사이의 선택 본문, run, paragraph는 삭제하지 않는다. body 없는 기존 MEMO도 처리한다.
- hiddenComment는 원래 direct run child 또는 singleton ctrl envelope를 삭제한다.
- ctrl envelope가 단일 원래 child가 아니거나 begin/end가 다른 part/겹친 범위이면 거부한다.
  다른 review를 삭제 payload 안에서 발견하면 거부한다. 원래 importer의 nested payload
  금지를 유지하며 lowering에도 별도 방어 조건을 둔다.
- 원래 PreservingPatchEngine의 DeleteSubtree, FormulaV3 ID 검사, Hangul2020PreviewTextV2,
  원래 PreservingWriter 및 모든 원래 source/package/patch/writer 한계를 그대로 사용한다.
  reader/validator/ID 규칙/기본 한계/기존 실패 검사는 수정하지 않는다.
- 출력은 별도의 immutable PackageArtifact다. 원본 파일 덮어쓰기·삭제·이동은 하지 않는다.

## 출력 재검증

전체 새 package를 원래 importer로 다시 읽는다. section 전체에서 선언한 1~2개 subtree만
없어진 것인지 나머지 연속 byte 구간을 그대로 비교한다. XML을 재직렬화하거나 visible text만
비교하는 방식이 아니다. changed part는 정확히1, added part0, 다른 모든 part의 expanded raw
hash는 같다. 원래 paired fields 및 review를 다시 읽어 정확한 종류별 감소를 확인한다.

삭제 대상에 포함된 body/parameters/metaTag 자체는 의도된 삭제 범위다. 다른 메모·숨은 설명·
header/style catalog/resource 및 선택 본문을 같은 삭제 범위로 확대하지 않는다. 암호화·보호·
작성자·시간·상태 권위는 별도로 미완료이며 이 처리가 그것들을 해석·해제·승인하지 않는다.

## 원래 저장소 연결

StoredImportedReviewBodies::prepare_delete는 원래 서비스의 scope/ACL/quarantine/AEAD/head/
전체 source 검증 전후로 동일한 삭제 출력을 준비한다. verify 및 bytes callback은 같은 fresh
검사와 전체 삭제 replay/receipt/artifact integrity를 다시 수행한다. 철회·변조·head drift 때
callback은 실행되지 않는다. 새로운 ingest/revision commit/publication은 없다.

반복 fresh 검사만으로 원자적 실행 lease가 생기지 않는다. require_current_product_route는
검증 후 RouteUnqualified로 거부하며, protection_execution_publication_authority=false다.

## 검증 증거의 한계

새 package positive는 원래 bounded synthetic fixture이며 실제 한글 삭제/저장·재열기/render
증거가 아니다. 원래 잠긴 captured package는 메모가 없어 잘못된 대상의 negative로만 사용한다.
저장소 테스트는 원래 AES-GCM 및 서비스 코드의 in-memory fixture다. 실제 SQL 운영 검증이 아니다.
caller-owned complete CommentState/원래5개 compiler 연산을 source-bound native state로
승격하지 않는다. native author/time/visibility/resolution 및 전체 보호 정책은 unverified다.

## 보존 및 migration

P09-97 checkpoint 전체를 고정하고 P95~P97 선언 raw pin1,269개를 현재 바이트 또는 정확한
기존 whole archive로 검증한다. 원래 current source828 중825는 같고, 변경 부모3개는 전체
preimage를 보관한다. 이번 module 선언만 제거한 전체 inverse가 원래 부모 사본과 같아야 한다.
이전 실행 파일85개는 보존하며 재실행으로 주장하지 않는다. 새로운 실패 source/run 기록도
유지한다. 이번 실패 binary는 수정 빌드로 교체되어 전부 보존했다고 주장하지 않는다.

원래 P97 validator와 snapshot은 수정하지 않는다. 새 P98 receipt/profile은 별도다. 전체
과거 qualification 재실행이나 최초 baseline 전수 감사를 뜻하지 않는다. migration은
protocol/migrations/p09-review-delete-v0-to-v1.md, 현재 증거는 evidence/p09-98-review-delete.*다.

P09/A12/A13 OPEN, native34 NOT_RUN/green0, SQL unresolved, P10 미시작을 유지한다.
root PLANS.md는 삭제 상태를 유지한다.
