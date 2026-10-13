# P09-82 원본에 묶인 정책 버전·권한·철회 저장 경로

## 결과

요청자가 직접 전달한 form policy만 다루던 제품 경로에 필요한 저장 기반을 추가했다. 새 schema20은 `source_form_policy_versions`와 append-only revocations, 등록/조회/철회 API를 제공한다. 기존 schema1~19와 Rust/제품 소스는 변경하지 않았다. 신규 구현 파일은 migration up/down, metadata fixture, 격리 검증 runner의4개다.

원본 head/revision/Result digest 및 provenance/observed graph digest, tenant/project/branch/document, 정책 artifact/digest, creator와 generation을 기록한다. 정책 값은 SQL에 저장하지 않고 기존 암호화된 Evidence artifact와 전용 policy media type을 참조하는 설계다. 실제 policy plaintext decoding/AEAD/scanner 연결은 아직 구현·검증하지 않았다.

등록은 project owner/editor와 양쪽 artifact read 및 policy manage 권한을 검사한다. 등록·철회는 branch row lock을 사용하며 source head와 policy generation의 stale 변경을 거부한다. 읽기는 현재 양쪽 read ACL을 재검사하고 최신 policy만 선택한다. 철회 또는 source 변경 시 과거 policy로 fallback하지 않는다. 버전/철회 기록은 immutable이며 direct table/helper 권한과 기본 PUBLIC EXECUTE는 없다.

## 실제 PostgreSQL 검증

원래 설치된 정확한 PostgreSQL18.4 image로 network none/host port·volume 없음/tmpfs인 독립 DB를 사용했다. 운영 DB와 기존 container는 건드리지 않았다.

현재 source에 대해 두 번 독립 실행했고 각각 새32 + 원래28 + 원래25 =85 metadata checks가 통과했다. 각각 schema1~20 registry, 명시적 gate 없는 rollback 거부, 빈 data rollback/reapply, 기존 idempotency28 및 authorized IR25 회귀, 새32 policy checks, data를 가진 rollback 거부를 확인했다.85를 두 번 실행했다고170개의 다른 검증으로 세지 않는다.

새32개는 named entry points/least privilege, 실제 등록·원본 고정 조회, stale generation/head, 잘못된 artifact role/digest, 잘못된 provenance, 다른 document, reader/nonmember, 양쪽 ACL 취소, manage 없는 read와 write 거부, null subject/generation, foreign tenant, nil policy version, stale/reader revocation, immutable version/revocation과 과거 version fallback 거부를 검사한다. 병렬 session의 독립 concurrency/lease/crash/restart 검증을 한 것으로 세지 않는다.

초기 fixture가 원래 존재하지 않는 `viewer` role을 사용해 기존 constraint에 거부됐다. 실패 receipt와 fixture/runner 전체 원문을 보존하고, 원래 `reader` role로 새 fixture만 수정했다. 먼저 통과한22-check source도 보존한 다음 기존22를 유지하고10개의 negative를 추가했다. old constraint/permission/trigger/fixture는 수정하지 않았다. 전체 로그와 값은 저장·출력하지 않고 closed diagnostic/hash만 남겼다.

이번 실행 소유 임시 container들은 run label/name/image 확인 후 제거했다. 데이터는 재현 가능한 테스트 fixture이며 사용자 원본은 삭제하지 않았다. 현재32 source 결과와 각 독립 run은 `evidence/p09-82-source-form-policy.actual-sql.v1.json` 및 `validation.v1.json`에 기록했다.

## 원본 보존

P59–P81 pin entries6302, original source files1551/51047460 bytes, native originals75가 원래 hash와 일치했다. P81 source535개는 전부 현재 그대로이며 P81 current raw source audit650 entries와 기존 actual probe executable도 그대로다. 루트 `PLANS.md`는 재생성하지 않았다. 이 단계에서 Rust 전체 회귀를 다시 실행하지 않았으므로 이전1085 검사를 이번 실행으로 세지 않는다.

## 남은 제품 경계와 다음 작업

이번 결과는 실제 SQL metadata 저장·권한·철회 기반의 검증이지 A13 전체 정책 제공자 완료가 아니다. 다음에는 엄격한 typed policy decoder, 실제 encrypted ArtifactService read,20-aware Rust repository, source model/원본 importer와의 일치 검증을 실제 저장 서비스에 연결해야 한다. 원래 Rust revision adapter의 schema1~19 exact admission은 그대로라20을 자동 수용하는 것으로 세지 않는다. 정책 값/구조가 실제 검증되기 전에는 metadata의 verified 상태만으로 신뢰하지 않는다.

실제 scanner/issuer/manifest/publication, 전체 importer와 native acceptance도 미완료다. A12/A13와 P09 Gate는 OPEN, 목표는 active, P10 새 구현은 없음 상태다. 기존 P26 semantic failure, P62 UNRESOLVED, current admission `INPUT_CHANGED_RE_ADMISSION_REQUIRED`, full native34 `NOT_RUN/0 green`을 유지한다. 접근허용/한글/COM/UI/native dispatcher 및 운영 grant/배포는 실행하지 않았다.
