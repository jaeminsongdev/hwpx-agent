# P09-86 저장 원본 정책 → 기존 제품 준비 경로

## 결과

등록된 최신 정책을 기존 strict product request와 원본 폼 inventory compiler/출력 생성기에 연결했다. 공개 요청에서 map/policy/artifact/path/approval을 받지 않고, 기존 원본 바인더가 실제 검증한 native map과 merged policies를 immutable 객체에 보관해 내부에서 전달한다. 별도 importer/정책 merge/default 구현을 만들지 않았다.

새 Rust4개/검사 runner1개와 parent3개의 제한된 변경이 범위다. parent는 module 선언, 검증된 native binding 보관 및 whole binding 동등성 검사를 추가했다. 기존 request/parser/domain/native reader/compiler/SQL1~20/full-document admission/의존성/설정은 그대로다. 원본을 덮어쓰거나 후보 문서를 자동 저장·게시하지 않는다.

## 실제 저장소 검증

서로 다른 owned disposable PostgreSQL 두 회차에서 같은 최종 source72개와 executable로 각492 assertions가 통과했다. 같은492 coverage를 재실행한 것이므로984개 독립 검사로 세지 않는다.

- 기존 SQL metadata85, 원래 source/암호화/current read/admission/ACL/철회207 검사를 유지했다.
- 원래 typed policy registration100을 유지했다. 기존 seed generation1은 fixture이며 generation2는 실제 준비/ArtifactService ingest/AEAD/strict decoder/domain/SQL head-generation CAS 등록 경로로 생성한다.
- 새 policy-product100은10 source/output paths에서 기존 제품 처리기와 후보 전체 bytes/receipt 비교, fresh 전체 재검증, 원래 route denial, 동일 정책 값의 새 generation 뒤 old request/policy 거부, 새 정책의 재준비 및 whole candidate 일치를 검사한다.
- 제품10 cases는 독립 프로세스에서 실행했고 selected_product_case와 단일 receipt를 대조해 IDs0~9 전체 coverage를 확인했다. 기존 probe의 cases 필드는 fixture inventory 크기10이며 각 제품 프로세스가10 사례를 실행했다는 뜻으로 세지 않는다.

각 회차에서 policy versions20/revocations10을 확인했다. 두 회차의 owned48 ciphertext files/189398 bytes와 disposable container는 정리됐다. 이전 한 batch의180초 제한 실패도 별도 보존됐고 그 회차의 owned45 files/178861 bytes/container는 정리됐다. 테스트 임시 데이터만 정리했으며 기존 원본·Evidence·운영 데이터는 삭제하지 않았다.

actor/scanner/worker metadata/정책 선택은 synthetic fixture다. 외부 issuer/authentication, atomic policy/source execution lease, DB restart/crash recovery, 한글 native 검증을 시험한 것이 아니다.10 paths는10 distinct digests나 새 native captures라는 주장도 아니다.

## 현재 소스 회귀

현재 변경 뒤4 affected Rust targets의135 tests가 모두 통과했다: stored product request8, stored provider112, policy-bound import1, package policy binder14. 새 policy-product7, 기존 stored policy11 및 registration5는112에 포함되므로 중복 합산하지 않는다.

새7 tests는 source5 사례의 SDK 전체 candidate/receipt 일치, source/output10의 original native state/receipt 보존, public map/policy/artifact/approval·duplicate·oversize·stale scope 거부, 동일 값의 새 정책 version 뒤 old cache 거부, product 검증 뒤 철회 재읽기, 정책 ACL/원본 AEAD/head/provider/server access 변경 거부와 no publish를 검사했다.

원본 v1 native state는 원래 bind_policies 및 독립 v1 SHA로 비교하고, 관리 값 v2 출력은 원래 제품 처리기로 비교한다. 원래 서로 다른 opaque 지문 정의를 같게 만들지 않았다.

5 crate lib/tests/examples strict lint, 새 Rust4개 개별 format, runner syntax 및 diff check가 통과했다. 이번4 targets135를 전체 workspace/P09/native Gate PASS로 확대하지 않는다. P09-84의107 targets1096 전체 batch는 과거 결과다.

## 실패와 남은 위험

초기 테스트의 v1/v2 직접 비교 오류, single-control 실제 capture에 잘못 선택한 multi-control fixture helper, probe의 없는 revision receipt field 참조 및 전체 SQL 제품 batch180초 초과를 기록했다. 첫 실패 테스트와 timeout 실행 소스의 whole preimages를 보존했다. 기존 helper/receipt schema/guard를 변경하거나 검사 수·deadline을 줄이지 않았고, SQL은 case별180초 상한의 독립 프로세스로 나눴다.

기존 conformance validator는 현재 소스에서도 matrix_drift로 실패했다. 원본 matrix/admission을 바꿔 green으로 만들지 않았다. 과거 P09-84 SQL intermittence2건 원인은 여전히 미확정이며 이번 두 성공을 원인 해결 증거로 세지 않는다. 반복 fresh read는 atomic 실행 권한이 아니다. 준비 비용/읽기 증폭의 product performance acceptance도 아직 주장하지 않는다.

## 보존 및 다음 단계

P59~P85 pin entries8959, original source1551 files/51047460 bytes 및 native originals75가 현재 raw bytes 또는 whole archives로 보존됐다. P85 source589개 중586개는 동일하며 parent3개의 raw whole preimage/변경 제거 inverse를 확인했다. 과거 original qualification 전체를 재실행한 것은 아니다. 기존 policy-registration/assembly executable도 exact 보존했으며 이번 검증으로 재집계하지 않는다.

다음은 실제 원본의 전체 문서 의미/미지원 field·comments·Date/external validation 등 importer 지원을 완성하고, 원본에 결합된 정책을 권한 있는 full-document operation/issuer/atomic execution/publication 경로에 연결하는 일이다. 읽기 증폭 최적화는 source/latest-policy/ACL/AEAD/whole compiler 불변식을 유지해야 한다. 별도 conformance source drift admission과 native 의미·저장·재열기 acceptance도 남아 있다.

PLANS.md 부재를 유지했다. 한글/COM/UI/접근허용, 운영·trust DB, stage/commit/push는 실행하지 않았다. P09 Gate/A12/A13 OPEN, 목표 active, P10 새 구현 없음. 기존 P26 failed_semantic_non_green/P62 UNRESOLVED/native INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN은 유지한다.
