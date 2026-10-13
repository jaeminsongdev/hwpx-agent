# P09-84 PostgreSQL 저장 정책 소비자 연결 정책

## 범위와 완료 경계

P09-83의 실제 암호화 정책 payload 소비자와 원본 문서 importer를 SQL20의 current policy read에 연결한다. artifact/revision repository의 기존 구현을 재사용하되 새 exact schema1~20 admission을 별도 API로 제공한다. 원래 migration/schema, 기존 admission/lease/CAS/readback/decoder/policy guard는 변경하지 않는다. 정책 등록의 typed source/payload 검증 서비스, 실제 issuer/scanner/인증/registered app, full importer, 실행·publication·native Gate는 이 작업의 결과로 완료되지 않는다.

## 연결과 권한

- 모든 연결은 기존 bounded local config의127.0.0.1/NoTls와 connect3초, statement5초, lock1초, idle transaction5초, transaction10초 한도를 사용한다. credential을 보관하거나 raw DB 오류를 공개하지 않는다.
- 새 artifact/revision 연결은 migration1~20의 compile-time 원문 SHA와 DB registry를 비교한다. LIMIT21로 누락·변경·추가 버전을 거부한다.
- 기존 artifact 연결은 migration1~17 prefix만 검사하므로20도 받아들인다. 이 기존 동작은 보존한다. 이를 exact17 거부나 exact20 qualification으로 주장하지 않는다. 기존 revision 연결은 exact19이고20을 거부한다.
- 기존 role/RLS/policy/privilege/guarded-write 검사를 모두 재사용한다. 새 revision profile은 replication/owner role SET·USAGE/table TRIGGER/schema CREATE/registry write도 거부한다.
- SQL20 정책 history/revocation의 FORCE tenant RLS와 immutable trigger, 직접 table 접근 금지, named function EXECUTE 및 helper/PUBLIC EXECUTE 금지, SECURITY DEFINER와 bounded search_path를 확인한다. 런타임 함수 본문 전체 fingerprint나 admission 뒤 관리자 DDL 변조를 감시하는 기능은 아니다.
- policy repository는 생성 당시 tenant/subject에 고정된다. 매 호출에서 context와 bounded document/current nonempty head를 검증하고 실제 SQL read를 RepeatableRead 안에서 수행한다. SQL의 active project membership/head/latest version/revocation/양쪽 artifact ACL 검사를 사용한다.
- 반환 row를 exact request scope/head 및 typed identity/digest로 검증한다. provider private scope에서만 요청을 구성하고 원래 strict payload consumer로 전달한다. public 요청자의 artifact selector/raw policy/authorization flag는 추가하지 않는다.

## 실제 소비와 동시성 경계

원래 ArtifactService metadata/ACL/state/quarantine/AES-GCM/digest, 실제 source importer와 whole policy domain binding, repository 재읽기와 fresh source 재검증을 변경하지 않는다. 동일 원본의 전체 graph/state/receipt와 비교한다. 새 repository의 revision accessor는 원래 Arc/try-lock/scoped transaction/실제 lease·CAS commit 구현을 사용한다. 새 read bridge가 제품의 signed issuer·실행 권한을 발급하거나 head를 변경하지 않는다.

반복 fresh-read와 프로세스 간 재읽기는 atomic policy read+source lease나 concurrent revoke/CAS, DB restart/crash recovery의 증거가 아니다. 테스트 PostgreSQL은 tmpfs이므로 DB 재시작을 시험하지 않는다. 고립된 로컬 검증에서만 synthetic worker의 genuine SQL lease/CAS 및 정책 등록·철회 API를 호출한다.

## 검증 및 보존

기존 parent3개에 module 선언만 추가하고 전체 변경 전 원문/선언 제거 역비교를 보존한다. 새 Rust5개만 개별 format한다. SQL1~20·Cargo 의존성·운영 DB·P17 frozen/private/user originals는 수정하지 않는다. PLANS.md는 사용자 삭제 지시대로 부재를 유지한다.

검사 DB는 preinstalled pinned image, run UUID label,127.0.0.1 ephemeral port, no host mount/volume,512MiB tmpfs 제한으로 생성한다. owned temp encrypted directory만 사용한다. runtime password는 env/stdin만 거치며 receipt에 출력하지 않는다. 관리자 fault injection은 이 폐기용 DB에서만 수행한다. registry trigger는 같은 transaction에서 복구하고 활성 상태를 확인한 뒤 application admission을 검사한다. 실패와 성공 기록을 분리하고 테스트용 DB·ciphertext만 ownership 확인 뒤 정리한다.

원래 SQL85 metadata assertions와10 pinned source/output packages를 사용한다. 실제 PG metadata/revision/policy read와 암호화 disk를 실행하지만 scanner/actor/worker operation metadata/explicit policy choices는 synthetic이다. 원본 파일을 덮어쓰거나 native/Hwp/COM/UI/접근허용을 실행하지 않는다. 앞선 간헐 실패를 최신 성공으로 지우거나 원인 해결로 단정하지 않는다.

P09 Gate OPEN, A12/A13 OPEN, 목표 active, P10 새 구현 없음. 모든 native/product claim은 기존 authority evidence의 미완료 상태를 유지한다.
