# P09-85 검증된 저장 정책의 실제 등록 연결

## 결과

현재 원본에서 정책 binding/version/creator를 생성하고 complete typed 정책을 검증한 뒤 실제 암호화 artifact로 저장·재읽기하는 등록 서비스를 추가했다. 새 PostgreSQL registrar는 기존 SQL20 register/read를 하나의 transaction 안에서 수행해 source head/policy generation CAS와 row 전체 readback을 확인한다. P09-84의 저장 정책 소비자에 새 등록 결과를 다시 연결했다.

새 코드6개(Rust5/runner1)와 parent3개의 module 선언이 변경 범위다. 원래 SQL1~20·artifact/revision/source guard·strict decoder/domain binder·의존성/설정은 유지했다. source artifact를 덮어쓰거나 정책 등록을 문서 head commit/실행/publication 권한으로 바꾸지 않았다.

## 실제 실행

서로 다른 owned PostgreSQL DB에서 같은 최종 소스63개와 probe executable로 각각392 assertions가 통과했다. 하나의392 coverage를 두 번 실행한 것이며784개의 서로 다른 테스트로 세지 않는다.

- 기존 SQL metadata85 및 P09-84 source/암호화/current read/admission/ACL/철회207 assertions를 그대로 실행했다.
- 새 등록100: ten pinned source/output paths에서 기존 generation1을 source-bound typed preparation/실제 ingest/AEAD/decoder/domain 검증 후 generation2로 SQL 등록했다. 새 row/whole state/graph/receipt를 소비자로 확인했고 stale generation 재등록 거부, 이전 cached policy 거부, 새 current 정책 fresh verify가 통과했다.
- typed 등록 뒤 각 테스트 tenant에 policy versions20/revocations10이 남는 것을 확인했다. baseline generation1 seed/worker metadata는 fixture이며 typed service는 generation2를 만든다.
- 실제 scanner/issuer/외부 인증은 검증하지 않았다.10 fixture paths는10 distinct raw digests나 새 native captures가 아니다. DB restart/crash recovery/atomic execution lease도 시험하지 않았다.

각 run의 owned48 ciphertext files/189398 bytes와 disposable container는 owner 확인 후 제거됐고 원본은 유지했다. runtime password·본문·전체 로그는 출력하지 않았다. Docker bridge가 있으므로 network-none으로 주장하지 않는다.

## 현재 소스 회귀

등록 전용5 tests: whole policy 소비/새 generation, read-only scope/incomplete set/exhausted generation의 no-write denial, source-head drift의 no-write denial, repository denial/unknown ack/손상 reply의 구분과 no retry, Unverified policy scanner의 no repository-write denial이 통과했다.

기존 stored policy11 및 revision lib16도 통과했다. 이번 현재 소스의 서로 다른 집중 회귀는32 tests다.5 crate lib/tests/examples strict lint, 새 Rust5개 개별 format, runner syntax, parent inverse/diff check도 통과했다. 초기 signed cast/doc lint 실패는 별도 records 및 관련 source preimages로 보존했고 검사 약화 없이 수정했다.

P09-84 전체107 targets/1096 batch는 이전 receipt이며 이번 변경 후 전체 batch를 새로 실행한 것으로 세지 않는다. 이번 scoped 검사를 전체 product/native Gate PASS로 확대하지 않는다.

## 실패·불명확한 효과

정책 등록용 ArtifactService ingest는 실제 쓰기다. 이후 stale CAS/repository denial이나 불명확한 commit 결과가 생기면 unregistered/ambiguous Evidence가 남을 수 있다. 원본·Evidence 삭제나 automatic retry를 하지 않는다. 준비 자체는 metadata generation을 예약하지 않는다.

SQL transaction commit acknowledgement loss는 별도 OutcomeUnknown이다. 잘못된 repository reply도 no-effect 확정으로 표현하지 않는다. 이후 실행에는 최신 정책/원본/권한을 다시 검증해야 한다.

기존 matrix_drift와 P09-84 간헐 SQL 실패2건 원인 미확정은 유지한다. 이번 두 회차에서는 실패가 관측되지 않았지만 과거 원인이 해결됐다는 증거로 세지 않는다. 기존 matrix/qualification/guard를 바꿔 green으로 만들지 않았다.

## 보존과 다음 단계

P59–P84 pin entries8259, original source1551 files/51047460 bytes 및 native originals75가 current bytes 또는 whole archives로 보존됐다. P84 source575개 중572개는 동일하고 parent3개는 whole preimages/선언 제거 inverse가 정확하다. 과거 qualification 전체를 재실행한 것은 아니다. PLANS.md 부재를 유지한다.

다음은 등록된 정책을 실제 권한 있는 제품 operation/preparation/issuer 및 publication 경로에 연결하는 작업이다. 전체 importer의 unsupported meanings/comments/Date·외부 validation/native acceptance와 conformance admission 및 SQL intermittence 원인 확정도 남아 있다. local registry 등록이 외부 issuer나 signed execution capability를 대신하지 않는다.

한글/COM/UI/접근허용/운영 DB·grant/배포/stage/commit/push는 실행하지 않았다. P09 Gate/A12/A13 OPEN, 목표 active, P10 새 구현 없음. 기존 P26 failed_semantic_non_green/P62 UNRESOLVED/native INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN은 유지한다.
