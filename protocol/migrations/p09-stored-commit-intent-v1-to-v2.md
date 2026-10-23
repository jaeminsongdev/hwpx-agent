# P09 커밋 의도 v2와 원 manifest 없는 복구

새 공통 저장 job은 원 execution manifest의 canonical bytes를 암호화 intent v2에 함께 보존한다.
`reconcile_archived_registered_stored_commit`는 원 manifest나 별도 `ServiceRequest` 없이 정확한 등록 locator와 현재 접근 가능한
intent/precommit에서 역사적 커밋과 결과 가용성을 읽는다. 기존 v1 자료와 실패/시도 이력은 변경하지 않는다.

## 저장 계약과 버전 전환

outer schema는 `hwpx-agent.stored-revision-commit-intent/v2`다. 필드는 다음3개뿐이다.

- `schema_version`: 정확한 v2 문자열.
- `commit_intent`: 기존 v1 intent 전체. tenant/subject,manifest/source/result SHA·크기와 정확한 서비스 요청을 그대로 보존한다.
- `manifest_canonical_json`: 원 manifest canonical UTF8 bytes의 u8 배열. 별도 실행 plan이나 새 route 권한이 아니다.

manifest bytes는16KiB, 전체 intent는 기존과 같은64KiB 이하다. 원 Receipt 종류·JSON media type·파일명과
원 artifact ingest/ACL/격리/AEAD/readback·등록·최종 CAS 순서는 유지한다. 새 DB schema나 역할 grant는 없다.
`PreparedStoredJob`은 준비 단계에서 원 manifest를 보관하고 모든 새 공통 job의 CAS에 이를 이동해 v2를 기본 저장한다.
명시적 server primitive `bind_registered_archived`도 같은 경로를 사용한다. 기존 `bind`/`bind_registered`의 v1 writer는 호환 경로로 남는다.

reader는 원 bytes의 schema를 구분한 뒤 해당 버전의 닫힌 typed envelope를 파싱한다.
중복·알 수 없는 필드·뒤따르는 JSON·미지원 버전은 거부하며 실패한 v2를 v1으로 해석하지 않는다.
원 manifest를 받는 기존 두 복구 API도 v2 내부 snapshot이 그 원본과 완전히 같을 때만 읽는다.
기존 reader binary는 v2를 지원하지 않으므로 reader 배포 없이 writer만 먼저 교체하거나 무조건 downgrade하지 않는다.
이미 저장된 v1을 재실행·덮어쓰기·자동 승격하지 않는다.

## 역사적 데이터와 실행 권한 분리

`ArchivedExecutionManifest`는 원 canonical bytes와 전체 SHA에 결속한 별도 읽기 타입이다.
실행용 `ExecutionManifest`에는 새 Deserialize나 archive 변환 constructor를 추가하지 않았다.
archive 자체도 일반 Deserialize를 제공하지 않으며, 크기·schema·typed IDs·비어 있지 않은 지문·정확한 canonical bytes를 확인하는
명시적 읽기 API만 제공한다. 과거 registry/route 지문은 현재 신뢰·health·승인·보호·source lease가 아니다.

등록 복구는 현재 tenant/subject/read scope와 원 row의 project/key/job/attempt·요청 canonical SHA·commit/result를 먼저 대조한다.
intent와 precommit의 현재 ACL/격리/종류/크기/전체 SHA·AEAD를 확인하고 archive의 source/base/plan을 원 서비스 요청에 대조한다.
precommit은 원 엔진의 정확한 canonical shape여야 하며 transaction/base/source·manifest/result SHA·크기와 content-derived artifact ID가 같아야 한다.
그 뒤 기존의 봉인 node·원 요청·역사적 receipt·결과 가용성 검사 본문을 그대로 공유한다.
읽기 감사 기록은 기존 서비스 정책대로 남지만 engine·claim·lease·ingest·등록·CAS·job/attempt 변경은 하지 않는다.

| 관측 | 의미 |
|---|---|
| `RegistrationNotObserved` | 현재 등록이 관측되지 않음. 무효과·안전한 재실행의 증명이 아님 |
| `LegacyManifestRequired` | v1 등록/영수증은 확인했지만 원 manifest가 별도로 필요함. 자동 재구성·실행하지 않음 |
| `Registered(NotObserved)` | 등록은 있으나 원 커밋은 현재 관측되지 않음. 자동 retry/rollback 허가가 아님 |
| `Registered(Committed)` | 원 역사적 커밋을 확인. 결과의 현재 `VerifiedAvailable`/`Unavailable`은 별도 판정 |

결과의 가용성은 현재 ACL/AEAD·전체 bytes/SHA 확인이며 전체 P09 의미·렌더·Native 자격을 대신하지 않는다.

## 구성요소와 실제 저장 경로 검증

[467 구성요소 결과](../../implementation/p09/evidence/p09-361-archived-manifest-recovery467.v1.json)는 신규23+직접 영향36개와
실행 타입 변환/일반 Deserialize 오용 차단2개를 수용했다. 원 엔진8개는466에서 본문이 통과했고 입력·실제 binary 동일성과467의
최종 대조로 재실행 없이 수용했다.466의 제품 시험 clock closure 타입 오류/본문0은 원본을 보존하고 helper의 공통 함수 포인터만 고쳤다.
467은879fresh/final879·산출물4final·진단없음·cleanupTrue다. 원 v1 checks와 봉인 node/result 관측 본문은 byte 동일하게 공유한다.

[468 실제 SQL 결과](../../implementation/p09/evidence/p09-361-archived-manifest-sql468.v1.json)는 새 전용 SQL24 DB와 OS 시험 키에서
원 HWPX compiler/guard3회/validator·v2 job/등록/CAS·disk AEAD·서명 다운로드를 실행했다.
별도 Rust 프로세스가 DB 재시작 전후에 정확한 locator만 받아 복구했다. 복구 동안 기존 handles/state/공개 요청 파일3개의 원 경로는
없었고, 각각 다른 이름으로 보존한 뒤 모든 bytes/SHA를 확인해 복원했다. 원 manifest나 별도 서비스 요청을 복구 함수에 전달하지 않았다.
새 claim/CAS/시도는 없었고 전후 artifact6/job2/attempt2/intent1/revision2/head2·암호문6개의 bytes/SHA가 같았다.

SQL7개 probe·905fresh/final905·설치 설정1final·산출물2final·진단없음·cleanupTrue다.
소유 postmaster2회 정상 종료·OS 시험 키3개 삭제를 확인했다.59개 구성요소와 타입 검사2개·기존 키 전달 모델4개는 다시 실행하지 않았다.
전체181.266초, 빌드12.750초/Job CPU11.344초/private최고997.79MiB, SQL8.250초/CPU5.656초/private최고76.00MiB였다.
시스템CPU최고28.17%·가용RAM최저22.545%이며 한 코어/낮은 우선순위·CPU cap·RAM/commit95% 등 기존 보호를 유지했다.
전용 fixture의 자료와 영수증은 보존했으며 이전 DB/job·한글·Native·운영 DB는 실행하지 않았다.

## 공개 요청에서 등록 결과 복구

`PreparedCatalogRequestLookup::recover_registered`는 원 strict 공개 요청과 현재 provider scope에서 정확한 SQL 관측을 먼저 한다.
같은 key/job과 관측된 attempt로만 등록 locator를 만들고 기존 v2 복구를 호출한다. 완료 metadata의 revision은 복구된 커밋과 일치해야 한다.
마지막 SQL 조회에서 현재 요청/ACL·job/state/attempt/영수증이 달라지면 `ObservationChanged` 또는 조회 오류로 종료한다.
이는 한 시점의 전체 snapshot/권한 lease가 아니며 자동 재시도·job 상태 변경·새 실행으로 전환하지 않는다.

기존 `observe`의 metadata-only fast path는 바꾸지 않았다. 복구도 ZIP/import/head 재검색·카탈로그 읽기·regex/compiler를 실행하지 않는다.
`NotObserved`, `AttemptNotStarted`, `Existing`의 effect와 legacy/등록 미관측/커밋/결과 가용성은 별개다.

[470](../../implementation/p09/evidence/p09-361-catalog-request-recovery470.v1.json)은 신규10+영향14개의 본문에서23pass/1fail이었다.
시험 저장소가 완료 영수증 ID를 매번 새로 만들어 새 상태 변경 검사가 실패했다. 제품 조건은 유지하고 해당 fixture ID만 고정했다.
[471](../../implementation/p09/evidence/p09-361-catalog-request-recovery471.v1.json)은 실패1개만 재실행해 통과했다.
원23개 본문/제품·검증 입력의 동일성을 확인했고872fresh/final872·산출물2final·진단없음·cleanupTrue다.
원470의 final fresh 누락/실패는 보존하며 원 결과를 PASS로 다시 쓰거나 P09 Gate로 승격하지 않았다.

[472](../../implementation/p09/evidence/p09-361-public-request-recovery-sql472.v1.json)은 새 전용 SQL24/OS 키 scope에서
원 공개 요청만 받아 재시작 전후 같은 job/attempt·커밋 revision·현재 가용 결과를 복구했다. handles/state/요청/locator의 원 경로4개가 없는
상태였고 bytes/SHA를 확인해 전부 복원했다. 변경 요청의 typed conflict·없는 key의 미관측도 확인했다.
원 manifest·claim·locator·별도 ServiceRequest를 전달하지 않았으며 새 engine/claim/lease/CAS/시도·job 상태 변경은 없었다.
SQL7probe·905fresh/final905·설정1final·산출물2final·소유 DB 정상 종료2회·전용 키3개 삭제·cleanupTrue다.
207.766초, 빌드38.719초/Job CPU3.188초/private733.26MiB, SQL8.265초/CPU5.844초/private76.34MiB였다.
시스템CPU최고78.86%·가용RAM최저12.351%이며 보호 중단은 없었다. 원23개/수정1개·과거59개/키 모델/공식249는 반복하지 않았다.

## 남은 제품 경계

운영 키 발급/유실 복구·실제 scanner와 현재 신뢰 registry·Native 의미 및 P09 Gate는 미완료다.
P09/A12/A13 OPEN·공식158/249·잔여91·P10 미시작을 유지한다.
