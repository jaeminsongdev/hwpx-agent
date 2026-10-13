# P09-83 저장 정책 파일의 실제 읽기·해석·원본 연결

## 결과

repository가 선택한 정책 artifact를 실제 ArtifactService로 권한 검사·AES-GCM 복호화·digest 검사하고, 엄격한 typed JSON decoder로 해석한 뒤 원본 문서의 form state/graph에 연결하는 소비자를 구현했다. 기존 정책 경로는 요청자가 직접 전달한 정책 값만 다뤘지만, 새 경로는 source/정책 version을 함께 고정한 저장 파일을 읽는다. PostgreSQL metadata repository 연결은 아직 없으며 synthetic repository fixture가 이 인터페이스를 테스트한다. 이번 결과를 A13 전체 제품 정책 제공자 완료로 세지 않는다.

새 Rust 파일은 `source_policy.rs`, private `source_policy/wire.rs`, `stored_source_policy.rs`의3개다. 기존 actual_import 소스와 테스트 parent에는 module 선언만 추가했다. 기존 schema1~20, revision admission, artifact service, policy domain binding 및 제품 route guard는 변경하지 않았다. 의존성/설정/운영 권한 변경도 없다.

## 구현된 실제 소비자

`StoredImportedDocumentForms::bind_stored_policies`는 authenticated source에서 private read scope를 만들고 repository의 current version만 읽는다. 반환 row의 tenant/project/branch/document, source revision/head/Result artifact/package/provenance/observed graph digest, policy version/generation을 실제 원본과 비교한다. policy artifact는 Result와 달라야 하고 Evidence 역할, 전용 media type, available/verified/no quarantine,1MiB 이하 및 raw digest 일치가 필요하다.

payload에는 row와 정확히 같은 source/version/creator binding과 complete ordered policy set가 있어야 한다. unknown/duplicate/missing 필드는 거부하고 nullable defaults/validation도 반드시 명시해야 한다. 현재 값, 이름, items, native IDs, styles, source identity를 정책 JSON으로 덮어쓸 수 없다. 기존 PolicyBoundDocumentForms의 source anchor/order/kind/budget/default/group validation을 재사용한다.

생성 시 repository와 source를 다시 읽고, cached verify는 policy 재다운로드·재해석·complete graph/state/receipt 재구성과 whole comparison을 한다. 권한 취소·철회·head 변경·valid latest version 교체·policy ciphertext 변조를 cached receipt로 통과시킬 수 없다. 이 반복 fresh-read는 atomic SQL lease나 concurrent revoke/CAS 검증이 아니다. 소비자는 일반 read audit 이외 content ingest/head commit/manifest/publication을 하지 않는다.

## 실제 실행과 검증 범위

- 최신 정책 전용11 tests: 전체 graph/state 원래 바인딩과 일치, ten pinned source/output packages,16 metadata 변조,21 payload 변조 및 malformed/trailing/oversized/duplicate JSON, nullable omission와 nested duplicate, wrong role/media, 양쪽 ACL 취소, quarantine, latest/revocation, foreign authenticated provider, 정책만 변조한 실제 ciphertext, policy scanner Unverified 거부가 통과했다. loop assertions를 별도 test 개수로 부풀리지 않는다.
- 전체 hwpx-package/CLI batch는107 targets/1095 passed/failed0/ignored0/filtered0으로 끝났다. 그 batch는 새 정책10 tests 시점이었다. 뒤에 policy Unverified11번째 test를 추가했으므로 최종 소스로 변경된 stored-provider 전체100 tests를 별도로 실행해 failed0/ignored0/filtered0으로 완료했다.
- 기존 batch의99-check stored target을 최신100-check 결과로 대체하여 서로 다른 현재 coverage는1096이다(CLI162/package934). 두 실행을 단순 합산하지 않았으며, 하나의1096-check batch나 두 번의 독립 전체 batch로 주장하지 않는다. 각각의 원래 결과/실행 범위와107개의 result rows를 별도 receipt에 보존했다.
-5개 crate의 lib/tests/examples strict lint와 새3개 파일 개별 format/parent diff checks가 통과했다. 처음 잘못된 fixture 이름과 content-digest 역할 충돌, 새 코드 lint 오류, 실행 중 test EXE 때문에 발생한 Windows LNK1104는 실패 receipt와 원문 test archives에 별도로 남겼다. 원래 content uniqueness/guard를 완화하거나 실행 중 프로세스를 삭제·종료하지 않았다.

repository/scanner/주체·sealed revision metadata는 synthetic fixture이며 실제 PostgreSQL 제품 provider/외부 인증/issuer/real scanner가 아니다. AES-GCM encrypt/decrypt, ArtifactService ACL/state/quarantine/digest, actual source importer와 원래 전체 policy domain binding 코드는 실제로 실행했다. ten packages는 frozen actual/generated component sources이며 ten fresh native acceptance captures가 아니다. 이전 actual assembly example executable은 보존만 하고 다시 실행한 것으로 세지 않는다.

## 원본 보존

P59–P82 declared pin entries6933, original source1551 files/51047460 bytes, native originals75의 원문 hash가 보존됐다. P82 source546개 중544개는 현재 동일하고, 두 parent 변경 전 원문은 정확한 source archive에 있다. 두 선언을 제거한 전체 파일 역비교도 원래 bytes와 일치했다. P82의 source/archive/predecessor/actual-input667 entries를 별도로 검사했다. 원래 qualification 프로그램 전체를 재실행한 것으로 세지 않는다.

root PLANS.md는 사용자 삭제 지시대로 부재다. 과거 보관본/실패/native evidence/old guards/기존 검증 receipts는 삭제하거나 덮어쓰지 않았다. 비밀 값·전체 로그를 보고서에 포함하지 않았다. 한글/COM/UI/접근허용/native dispatcher/운영 DB/grant/배포/stage/commit/push는 실행하지 않았다.

## 남은 실제 제품 연결

다음은 SQL20의 exact schema/checksum/role/table/helper privilege admission을 가진 정책 read repository와 새 exact revision profile을 이 소비자에 연결하는 작업이다. 기존 Rust revision adapter의 schema1~19 guard는 그대로라20을 자동 수용하지 않는다. 정책 등록 서비스의 실제 payload/source 검증, 실제 scanner/issuer 및 publication/operation 경로, full importer/unsupported field meanings/native acceptance도 남아 있다.

A12/A13 및 P09 Gate OPEN, 목표 active, P10 새 구현 없음. 기존 P26 failed_semantic_non_green/P62 UNRESOLVED/native admission INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN을 그대로 유지한다. fixture/SQL/component 검사를 실제 native/product/Gate PASS로 승격하지 않았다.
