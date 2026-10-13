# P09-86 저장된 원본 정책의 제품 준비 경로 연결

## 범위와 권위

기존 원본 importer/정책 바인더/strict product envelope/ArtifactService/폼 inventory compiler를 연결한다. 등록된 최신 정책에서 원본 component map과 complete typed 정책을 얻고 기존 출력 생성기에 전달한다. 공개 요청에 map/policy/artifact/source path/approval 선택을 추가하지 않는다.

전체 목표는 P09~P20이며 이번 연결은 P09 폼 경로의 한 단계다. 부분 importer를 full DocumentGraph로 승격하거나 기존 full-document guard를 우회하지 않는다. 외부 인증 issuer, signed execution/publication, actual Hangul acceptance, P09 Gate는 이 변경의 완료 범위가 아니다. 삭제된 루트 PLANS.md는 재생성하지 않는다.

## 원본 native binding 보존

기존 PolicyBoundDocumentForms::bind에서 actual_map과 native readback, 원본 관측 비교, 정책 merge/domain 검사에 실제 사용한 map/native policies를 immutable private-field BoundNativeFormPolicies에 이동해 보관한다. caller constructor/Deserialize가 없고 Debug는 redacted다. 별도 importer/merge 구현이나 새 기본값을 만들지 않는다. 원본 바인더의 whole source 재검증 및 저장 소비자의 whole state/graph/receipt 비교에 이 보관 binding의 전체 동등성 검사만 추가한다.

IDs는 기존 source-local component reservations이며 실제 XML stable/native identities라는 주장이 아니다. getter는 memory binding을 반환할 뿐 현재 ACL/latest-policy/실행 권한을 증명하지 않는다.

## 제품 요청과 재검증

StoredSourceFormPolicies::prepare_product_json은 기존 전체 원본/정책 재검증 뒤 원본 StoredProductFormRequest::prepare_json을 호출한다. map/policies는 내부에서만 선택한다. access는 기존 trusted server 입력이며 공개 JSON approval/route grant가 아니다. 기존 request limits/unknown·duplicate 거부/source/head scope/AEAD/parser/domain/output/compiler를 그대로 사용한다.

PreparedStoredPolicyProduct는 원본 prepared product와 정책 version/source receipt를 함께 보관한다. verify는 최신 정책과 원본을 앞뒤로 재읽고 원래 compiler/candidate 전체를 검증한다. 동일한 값의 새 policy generation도 이전 cache를 거부해야 한다. 철회·ACL·AEAD·head/provider/access 변경도 거부한다. 반복 read는 observation interval을 제한하지만 atomic source/policy execution lease가 아니다.

require_current_product_route는 fresh 전체 검사 뒤 변경하지 않은 원본 route guard를 호출한다. 현재 form scope는 계속 거부돼야 한다. 준비·검증은 감사 이벤트를 생성할 수 있지만 candidate ingest, document head commit, idempotency claim/publication을 하지 않는다. P09-85의 정책 등록 자체는 실제 Evidence 쓰기이며 이번 연결과 구분한다.

## v1/v2 상태 경계

원본 native package v1 state와 managed-value v2 state는 opaque payload 지문 정의가 다르다. v1은 원래 bind_policies 결과 및 독립 v1 state SHA로 비교한다. v2 출력은 기존 제품 처리기 전체 bytes/receipt와 비교한다. 서로 다른 버전의 state를 같게 만들거나 원본 receipt/hash를 덮어쓰지 않는다.

## 검증과 보존

수정한 parent3개의 raw whole preimages 및 변경 제거 inverse를 확인한다. 기존 source/private/native/실패 기록은 보존한다. 새 Rust4개/runner1개는 독립 파일이며 기존 migrations/guard/compiler/full-import admission/의존성/설정은 변경하지 않는다.

검증은 기존 pinned source/output10 paths, 기존 값 입력·기본값 초기화·selection clear 사례, 실제 ArtifactService AEAD, 기존 strict product/compiler 회귀와 owned disposable PostgreSQL을 사용한다. actor/scanner/worker metadata 및 정책 선택은 fixture다. 원래 SQL metadata 검사를 줄이지 않는다. SQL 제품10 cases는 case identity를 확인하는 독립 프로세스로 모두 수행하며 각 프로세스의 180초 상한을 유지한다. 한 batch의 제한 시간 실패는 별도 보존한다.

정리는 이 검사에서 생성한 owner-verified disposable container/ciphertext directory에 한정한다. 운영 DB, trust/runtime DB, 원본·검증 증거를 정리하지 않는다. 비밀 값이나 전체 로그를 출력하지 않는다.

P09 Gate/A12/A13 OPEN, P10 새 구현 없음. 기존 P26 failed_semantic_non_green/P62 UNRESOLVED/native INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN, matrix_drift 및 과거 SQL intermittence 미확정은 유지한다.
