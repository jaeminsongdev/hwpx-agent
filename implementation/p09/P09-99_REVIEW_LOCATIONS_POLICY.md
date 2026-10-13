# P09-99 원래 XML/IR 메모 위치 연결 정책

## 목표와 의미

P09-04의 실제 문서 메모 처리를 위해 original source의 marker 위치를 original IR의
문단·control ref에 결속한다. 임의 작성자·시간·상태로 완전한 CommentState를 만들지 않는다.
이것은 원본 XML 항목 위치이며 한글 caret/character offset/화면 좌표가 아니다.
full native metadata/state/protection/compiler/실행 및 P09 Gate는 미완료다.

## 원래 경로와 자료

ImportedDocumentReviewBodies::locate(fresh)는 original whole Source→Forms→Fields→Review 검증을
전후로 수행한다. 원래 실제 marker/end anchor를 source resolver로 해석하며 caller XML,
숫자 ID, 위치, source profile 또는 authored metadata를 받지 않는다. graph/source는 수정하지 않는다.

source의 실제 marker 또는 singleton ctrl 항목, run, paragraph와 source part를 결속한다.
paragraph 위치는 같은 container의 hp:p sibling ordinal, run 위치는 같은 paragraph의 hp:run
sibling ordinal, item 위치는 같은 run의 XML child-element ordinal이다. 공백·문자 수·픽셀·
document-global numeric p/id나 본문/메모 body 안의 p 개수를 그대로 좌표로 대체하지 않는다.

start/end는 원래 paired field의 같은 paragraph/container/part여야 한다. hiddenComment는
동일한 실제 item point이며 별도 range를 만들어내지 않는다. 모든 original source anchors,
root부터 paragraph container까지 전체 XML ancestry와 original paragraph node ID를 보존한다.
original IR paragraph의 source anchor와 actual review target control ref도 일치해야 한다.

## 중첩과 단순 모델 경계

원래 schema는 CommentAnchor(section_id/start/end)의 단순 ordinal 표현이다. paragraph가
직접 section root child일 때에만 direct_section_item_anchor를 제공한다. 이것도 원본 XML item
ordinal과의 결속이며 한글 native 커서 의미의 검증은 아니다. table cell·drawing/note 등의
중첩 scope는 전체 XML path를 남기고 simple anchor는 None이다. 중첩 paragraph를 전역 문단처럼
펼치거나 범위를 fabricated point로 채우지 않는다. 기존 comment schema/compiler는 변경하지 않는다.

## 한계와 비용

원래 source/XML/graph/field/review 한계와 재검증을 유지한다. 원래 paragraph/control refs를
한번 index하고 source XML 각 parent의 child 순서를 한번 순회해 sibling ordinal table을 만든다.
각 marker마다 앞선 XML siblings 전체를 다시 훑지 않는다. section lookup도 ordered set이다.
완전한 location 목록은 원래8MiB DigestBudget에 추가하기 전에 집계하고 receipt의 bounded
canonical SHA-256에 결속한다. 알려지지 않은 source/anchor/flow/order/byte budget은 거부한다.
256개 반복 numeric ID sibling 예제를 완전한 목록/순서/replay로 테스트했다. native 성능 또는
전체 실제 corpus 좌표 검증으로 확대 주장하지 않는다.

## 원래 저장소 연결

StoredImportedReviewBodies::locate(provider, now)는 원래 scope/ACL/quarantine/AEAD/head/
전체 source 검증으로 original package location을 조회한다. 캐시 getter는 memory일 뿐이다.
verify와 with_verified_locations는 fresh original access/source/whole location replay 전후
검사를 수행한다. provider scope 재결속·권한 철회·ciphertext 변조·head 변경은 callback 전에 거부한다.
반복 검사는 원자적 실행 lease가 아니다. require_current_product_route는 검증 후에도
RouteUnqualified로 거부한다. ingest/revision/publication/한글 실행은 없다.

## 증거와 보존

새 positive 위치는 original bounded synthetic fixture 및 원래 IR 코드의 실행 결과다.
잠긴 historical captured source는 review가 없어 zero-location negative로 사용한다.
원래 AES-GCM/revision/service의 stored tests는 in-memory이며 실제 SQL이 아니다.
native_caret_or_visual_coordinates_verified/native_author_time_state_verified와 실행 권위는 false다.

P09-98 whole snapshot10,168 bytes/0ee405068fb4f98368b416dc131d0edf043d01175296ba036decf566629539ab를
고정한다. 변경 부모3개의 whole preimage 및 current에서 module 선언만 제거한 exact inverse를
먼저 확인한다. 수정하지 않은 P98 검사에 정확한 부모3개만 whole preimage로 읽게 하는
read-only previous view를 제공한다. 다른 source/capture/official/receipt/executable은 현재 파일을
그대로 읽는다. 이전 검사를 바꾸거나 current acceptance 증거처럼 과거 view를 해석하지 않는다.
view는 실제 파일 변경·복사·쓰기 없이 prior bytes만 검사하고 검사가 끝나면 read roots를 복원한다.

이전 선언 raw pins1,310개 및 prior current source840(837 exact/부모3 whole preimage)을
확인한다. 이전 실행 파일100개는 보존하며 재실행으로 주장하지 않는다. 최초 baseline 전체
감사나 모든 historical qualification 재실행을 뜻하지 않는다. 최초 compile failure와 관련
새 source 전체를 별도로 보존한다. 수정 빌드가 이번 실패 binary를 대체하므로 모든 실패
binary 보존은 주장하지 않는다.

원래 registry/P11 comment-delete 계약/한글 target qualification/failed evidence는 변경하지 않는다.
P09/A12/A13 OPEN, native34 NOT_RUN/green0, SQL unresolved, P10 미시작과 삭제된 root PLANS를 유지한다.
