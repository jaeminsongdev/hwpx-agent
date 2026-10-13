# P09-65 실제 저장소 full-IR 제품 요청 검증 정책

P64 실제 제품 라이브러리 요청을 **LocalPostgresMetadataRepository + LocalEncryptedBlobStore + LocalPostgresRevisionRepository** 조합으로 실행한다. 현재 production request/provider/compiler의 기대값이나 원래 SQL guard를 변경하지 않는다.

## 실행 경계

- 기존 고정 PostgreSQL 18.4 image만 사용하고 image pull은 하지 않는다. 전체 migration1~19와 원래 SQL28/P61 SQL25를 실행한다.
- 새 owner label/run ID의 DB container/volume만 만들며 127.0.0.1 ephemeral port/host file mount 없음으로 제한한다. artifact role과 revision role을 분리한다. 내부 leaf function/PUBLIC/direct revision·authorization table writes를 허용하지 않는다.
- 호스트에는 이번에 생성한 별도 임시 root만 사용한다. 실제 ArtifactService가 known fixture bytes를 암호화 저장한다. 실제 서비스의 metadata/ACL/canonical digest/AEAD를 사용하며 raw artifacts 테이블 insert로 대신하지 않는다.
- worker는 한 번 등록하고 네 root baseline job을 순차 genuine claim/lease/stage/validate/authorized CAS/complete한다. 이 fixture baseline은 실제 native import/signed form execution이 아니다.
- source는 별도의 **synthetic prior metadata payload**, result는 원래 locked HWPX source, IR은 **test-only caller whole graph**, receipt는 **synthetic fixture payload**다. Source/result의 역할·content identity를 조작하거나 동일 content의 kind 충돌을 우회하지 않는다.
- 원래 locked fixture constructors는 visibility/imports만 바꾸어 재사용하며 string literal과 body token을 대조한다. 원래 tests와 golden manifest/source/output을 편집하지 않는다.

## 실제 검증 요구

1. 네 HWPX 사례(five-kinds/empty-text/reset-defaults/clear-selections)의 sealed IR root 생성과 새 strict request 실제 실행.
2. whole HWPX candidate bytes의 고정 output oracle 일치, source IR digest/base graph/plan, test-only graph에서 form state 이외 모든 필드 정확한 보존.
3. fresh verify와 실제 기존 signed route 거부, ingest/stream head 변경 없음. READ audit 추가는 정상이다.
4. package/IR ciphertext 실제 filesystem read, plaintext와 다름/AEAD tag 길이, 잘못된 AES key로 같은 파일을 읽을 때 거부.
5. 별도 프로세스와 DB restart 뒤 같은 run 안의 exact receipt/candidate hashes. restart 후 loopback port/owner를 다시 검사한다. 불확실 commit을 retry하지 않는다.
6. 실제 project ACL 회수로 네 요청 모두 거부, 복구 후 새 프로세스 재검증.
7. 실제 IR ACL 회수→route 이전 거부→source 읽기 유지→ACL 복구→fresh verify. IR quarantine으로 encrypted object 실제 이동과 fresh verify 거부/source 유지/head와 ingest count 불변.
8. 원래 SQL53와 read-only 네 root graph rows·job succeeded 상태 postconditions. jobs.state와 wrapper returned_state의 별도 계약을 정확히 사용한다.
9. 같은 declared source pins/별도 executable hash로 독립된 새 DB에서 재실행. baseline artifact UUID가 새로 생성되므로 서로 다른 DB의 receipt identity를 전역 동일하다고 주장하지 않는다.

## 보존·상태

변경 전 Cargo.lock/product Cargo.toml/PLANS 전체, 모든 실패 시점 source 및 failure receipts를 보존한다. product에는 cached `postgres` dev-dependency만 추가하며 기존 production dependencies는 불변이다. 현재 native source admission은 INPUT_CHANGED_RE_ADMISSION_REQUIRED이다.

종료된 owned fixtures만 정확한 container/volume label/name/image와 임시 root 절대 경로/parent/prefix/link 검증 후 제거한다. 기존 DB/사용자 원본/private native 증거/실패 결과/설정/trust 상태는 수정하거나 정리하지 않는다. credentials/전체 backend logs/원문 HWPX/IR 값을 출력·저장하지 않고 closed error categories 및 digest만 기록한다.

이 결과는 **현재 제품 라이브러리 준비 경로의 bounded real-backend acceptance**다. 실제 전체 native HWPX importer/provenance/previous-result→input chain, issuer/ExecutionManifest/idempotent publication/IR retention·GC·sync·recovery/native 의미·render·direct differential/whole source admission/P09 Gate는 별도다. P09 Gate가 닫히기 전 P10 새 구현을 시작하지 않는다. 접근 허용창/Hwp COM/UI/native dispatcher는 실행하지 않는다.
