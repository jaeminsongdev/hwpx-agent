# P09-82 source-bound 정책의 버전·권한·철회 저장 정책

## 제품 요구와 현재 범위

요청자가 직접 제공하는 form policy만으로는 실제 제품의 정책 제공자 권위를 만들 수 없다. 원본 문서와 명시적으로 등록된 정책 파일을 버전별로 고정하고, 현재 프로젝트 권한과 원본 head/정책 generation을 검증하는 저장·조회·철회 경로가 필요하다. 새 schema20은 그 PostgreSQL metadata 기반이다. A13 전체 정책 제공자 완료는 아니다.

정책 값은 기존 encrypted Evidence artifact에 있어야 하며 전용 `application/vnd.hwpx-agent.source-form-policy+json` media type으로 구분한다. Evidence를 native acceptance 증거 또는 정책 자체의 의미 검증으로 승격하지 않는다. 이 migration은 정책 plaintext/기본값/검증 규칙을 SQL에 저장하거나 추론하지 않는다. 실제 blob/AEAD/typed decoder/scanner 검증은 후속 실제 제품 연결의 필수 조건이다.

## 권위와 동일성

- schema1~19의 함수·trigger·checksum·권한·검사·fixtures는 그대로 둔다. schema20을 뒤에 추가한다.
- 버전은 tenant/project/branch/document, 실제 source revision/head generation, Result artifact/package SHA, 원래 source provenance/observed graph SHA, policy artifact/raw SHA와 creator에 묶인다.
- 등록은 active tenant/project의 owner/editor와 source read + policy read/manage ACL이 필요하다. 조회는 project membership과 양쪽 artifact read ACL을 다시 검증한다. SQL session identity와 전달 actor/tenant가 정확히 같아야 한다. 이것은 기존 trusted application-session model이며 외부 인증/issuer 검증을 대신하지 않는다.
- 등록·철회는 원래 branch row를 잠근다. 등록의 source head CAS 및 policy generation CAS가 한 transaction에서 처리된다. 다른 generation, source head 또는 scope는 거부한다.
- policy version과 revocation은 immutable append-only 기록이다. 읽기는 가장 최신 version만 선택하고, 철회되었거나 원본이 바뀌면 거부한다. 과거 유효 버전으로 fallback하지 않는다.
- type/size/media/digest/service metadata/availability/verified/quarantine/ACL checks를 유지한다. 단순한 SQL의 verified metadata를 실제 scanner/AEAD 또는 완전한 policy qualification으로 세지 않는다.
- 공개 기본 EXECUTE/table rights는 없다. helper와 table direct write는 app에 허용하지 않는다. 실제 운영 application-role grant/배포는 하지 않는다.

## 보존과 검증

기존 schema19 뒤에20을 apply하고 registry/checksum을 확인한다. 명시적 gate 없는 rollback 거부, 빈 data에서 explicit rollback/reapply, data 있는 rollback 거부를 검사한다. 새32 metadata checks와 변경하지 않은 기존28+25 checks를 실행한다. 이것을 독립 동시성/lease/crash/실제 정책 payload 또는 native qualification으로 확대하지 않는다.

이미 설치된 pinned PostgreSQL18.4 image만 사용한다. pull 없음, network none, host port/volume 없음, DB는 이번 run 소유 tmpfs이며 exact run label/name/image를 확인한 후 제거한다. 운영 DB, 기존 container, 사용자 자료, 한글/COM/UI/접근허용, trust/security 설정은 건드리지 않는다. 전체 로그·비밀정보는 출력하지 않고 closed code와 hash만 남긴다.

Rust revision adapter의 기존 schema1~19 exact admission은 그대로 유지한다. schema20을 그 adapter가 자동 수용한다고 주장하지 않는다. 후속20-aware policy repository와 엄격한 typed encrypted-payload decoder/실제 source provider 연결이 필수다. 그때에도 old guard를 완화하거나 무조건 Verified를 부여하지 않는다.

root `PLANS.md`는 사용자의 삭제 지시대로 부재를 유지한다. 새 보고서와 evidence로 기록하며 P09 Gate OPEN, 전체 목표 active, P10 새 구현 없음 상태를 유지한다.
