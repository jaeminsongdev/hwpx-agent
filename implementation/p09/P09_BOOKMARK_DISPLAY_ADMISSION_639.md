# 보통 책갈피의 제품 표시 옵션 admission — 639

## 실제 제품 변경

[638의 발견](P09_PREPARED_BOOKMARK_RENDER_637_638.md)을 제품 코드에 반영했다. 현재 source-bound 책갈피 인터페이스는 **point/보통 책갈피**를 수용하며, 블록 범위를 자격 검증한 인터페이스가 아니다. 이 경계에서 page/bookmark_name/relative_position은 유지하고 Content는 블록 책갈피가 필요하다는 typed 오류로 거부한다. 요청한 Content를 몰래 BookmarkName으로 바꾸지 않으며, caller의 `block=true` 같은 주장으로 우회하는 입력은 추가하지 않았다.

적용한 실제 준비 경계4개는 다음과 같다.

1. `ReferenceValidationProductOperation::prepare_source_bookmark_reference_insertion`
2. `StoredImportedDocumentForms::into_bookmark_insertion_candidate`
3. `ReferenceValidationProductOperation::prepare_source_bookmark_command_changes`
4. `StoredImportedDocumentForms::prepare_bookmark_command_candidate`

새 공통 `PointBookmarkAuthoringDisplay`는 명시적인3가지 선택만 표현한다. 삽입 오류는 `SOURCE_BOOKMARK_INSERT_CONTENT_REQUIRES_BLOCK_BOOKMARK`, 편집 오류는 `SOURCE_BOOKMARK_UPDATE_CONTENT_REQUIRES_BLOCK_BOOKMARK`다. stored 경계는 기존 typed Output 원인으로 전달한다. 이는 HTTP/MCP 전체 오류 매핑이나 실제 게시/운영 route 자격까지 검증했다는 뜻은 아니다.

기존 권한·현재 source/SHA·head 검증 뒤, writer/owned 출력 후보 생성 전의 판정이다. 편집 요청 수는 기존 aggregate 상한 안에서 먼저 제한한다. 추가 ZIP/XML import·전체 graph clone·전체 원본 재검증을 추가하지 않았고 표시 enum 비교만 삽입했다. 유효한 요청은 기존 보호/target/selection/writer/preservation 경로를 그대로 통과한다.

읽기/진단, source-bound inert SDK discovery, 비공개 포렌식 및 과거 `?` 캡처는 삭제하거나 거부하지 않았다. 이들 불활성 후보는 원래 Native/currentness/게시 권한을 주지 않으며, 일반 양성 authoring 경로와 구분한다. Block-bookmark Content 지원을 완료하거나 P09 범위에서 제거한 것이 아니다.

## 검증 결과

[audit003](evidence/p09-361-bookmark-display-admission639-audit003.v1.json)은 변경된 조건10개와 직접 영향받은 AEAD 조건1개를 합쳐11조건의 수용 근거를 닫았다. 최초 실행002의10통과/1실패를 모두 반복하지 않았다. 제품/보조 함수/통과 시험 본문이 바뀌지 않았음을 확인하고, 원 시험 실행 파일·dep-info를 private에 byte-exact 보존한 뒤 수정한 실패 fixture1개만 실행했다. 모든 현재 입력은 마지막 fresh hash로 다시 닫았다.

| 항목 | 결과 |
| --- | --- |
| 새 조건 / 영향받은 기존 AEAD 조건 | 10 / 1 |
| audit003 재실행 | 실패 fixture1개만 PASS |
| 통과10조건 | 원 결과·불변 본문·제품 source·실행 파일을 보존, 재실행 안 함 |
| 현재 실제 원본의 유효6조합 | 기존627 예상 output SHA와 일치 |
| 현재 실제 원본의 Content2조합 | typed 거부, 대체 출력 생성 안 함 |
| 직접/저장소 삽입·편집 | 4경계의 거부와 유효 경로 확인 |
| 권한·원본 SHA 선행 | Content 진단보다 먼저 거부됨을 확인 |
| source fresh/final | 913/913 |
| 새 시험 실행 파일·dep-info fresh/final | 2/2 |
| audit003 경과 / CPU 최고 / 가용 RAM 최저 | 158.032초 /10.42% /49.1056% |
| 전체 실행 중 관측 CPU 최고 | audit002의19.74% |
| 보호 중단 / 새 Native / 전체249 재실행 | 0 / 0 / 0 |

audit003은74,088bytes / SHA256 `52c198d30f92cbf91aa6c409549bb70eaf52b048d7876f71e3b50eba3299d40c`, cleanup=true다. 새 compiled test는8,842,240bytes / SHA256 `1124ea09a592dd65b35710faf1ffbb9379d32ff95de6c3db594de7c9688d0b0f`다. 새로운 실제 SQL/issuer/Native/실행 권한/등록/CAS/게시나 production-default end-to-end route 자격으로 승격하지 않는다.

### 실패·기존 fixture 보존

- [audit001](evidence/p09-361-bookmark-display-admission639-audit001.v1.json): 사전검사에서 마지막 기존 시험 뒤 보조 함수까지 시험 본문으로 잡은 비교기 오류. 빌드 전 실패했다. 당시 검증기를 보존하고 column-zero 함수 종료 범위로 고쳤다.
- [audit002](evidence/p09-361-bookmark-display-admission639-audit002.v1.json):10조건 통과, 권한 선행 fixture1개 실패. 기존 필드로 감싼 유일한 plain run을 재삽입 selector로 찾으려 한 fixture 문제였다. 삽입용 원본과 편집용 원본을 분리했고, 이 함수 본문 외 나머지 새 시험/보조 함수와 제품 source는 byte-identical이다. 원 실패 전체를 PASS로 변경하지 않았다.
- AEAD 시험은 의미와 무관한 잘못된 Content 입력 대신 유효한 BookmarkName을 사용하도록1곳만 바꾸고 해당 시험을 실행해 보존했다. 나머지 기존7시험의 본문은 바꾸지 않았고 실행하지 않았다.
- 기존628의 고정8개 private 출력 생성 함수는 Content가 들어 있는 legacy manifest를 출력 디렉터리 생성 **전**에 거부하도록 소스에서 퇴역시켰다. 새로운6종 batch로 몰래 바꾸지 않았으며 기존8개 파일/소비된 실행 파일은 보존한다. 이 legacy batch를 실행해 새 자료를 만들지는 않았다.

## 다음 직접 작업과 범위

다음은 실제 한글이 저장한 **블록 책갈피 범위 원본**과 fieldBegin/fieldEnd/name/내용 결속 근거를 확보해 block-content 양성 지원을 구현하는 일이다. 기존 P09-13은 명시적으로 point marker의 스키마/정적 시험이며 actual HWPX/한글/저장재열기/render 자격이 아니므로 블록 원본으로 대체하지 않는다. 범위를 나타내는 XML·인수를 추측하거나 caller flag로 권한을 대신하지 않는다.

허용된6개 point 표시 경로를 소비하는 현재 로컬 계획/권한/head/backend/새 출력 마감, 이동/이름 변경·없음/중복/깨짐 및 다른 필수 대상도 계속 진행한다. 필요한 새 실물 캡처는 현재 세션 자격과 묶음 경계를 먼저 준비하며, 소비된 point8종/Native 시험을 재실행하지 않는다.

P09-F11/전체 P09/A12/A13 OPEN·31미마감묶음/65기능·공식249의158수용/91대기/다음165를 유지한다. 새 P10은 시작하지 않았다. 현재 새 사용자 명령이나 접근 허용은 필요 없고 목표는 ACTIVE다.
