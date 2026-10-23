# 등록 영수증 기반 읽기 전용 복구

새 공통 job의 intent v2와 `reconcile_archived_registered_stored_commit`는 원 manifest/별도 서비스 요청 없이 등록 locator와
현재 ACL/AEAD가 확인된 intent/precommit에서 복구한다.467 신규23+영향36·타입 차단2개와
[468 실제 SQL 재시작](evidence/p09-361-archived-manifest-sql468.v1.json)에서 원 파일3개가 없는 복구를 확인했다.
파일은 바이트 그대로 복원했고 새 claim/CAS/시도는 없었다. [v1에서 v2로의 저장·복구 계약](../../protocol/migrations/p09-stored-commit-intent-v1-to-v2.md)을 따른다.

기존 원 manifest를 받는 호환 API도 유지한다.
`reconcile_registered_stored_commit`는 정확한 DB 조회 키와 서버가 보관한 manifest를 받아,
등록 행과 현재 접근 가능한 암호화 intent/precommit 영수증에서 커밋 요청을 확인한다.
호출자가 별도 `ServiceRequest` 파일을 제공할 필요가 없다. 실행·lease·ingest·등록·CAS·작업/시도 상태 변경은 하지 않는다.
읽기 감사 기록은 기존 서비스 정책대로 남는다. 이 함수는 제품 route나 재시도 권한이 아니다.

## 복구 상태와 검사

반환은 `RegistrationNotObserved`, `Registered(NotObserved)`, `Registered(Committed)`를 구분한다.
앞의 두 상태는 no_effect 또는 재실행 허가가 아니다. 커밋 관측과 결과의 현재 가용성은 별도이며,
격리된 결과는 커밋을 지우지 않고 `RecoveredResult::Unavailable`로 남는다.

현재 context/read scope와 DB 행의 tenant/subject/project/key/job/attempt를 확인하고,
복원된 요청의 canonical SHA/commit/revision/result/summary를 원 등록 행에 대조한다.
intent와 precommit은 종류·크기·SHA·현재 ACL/격리/AEAD를 검사한다. 원 manifest·봉인된 node·
결과 검사는 기존 복구 함수와 공유하며 각 영수증을 한 번씩 읽는다. 기존 복구 함수의 조건은 역조합 해시로 보존했다.

신규10개와 변경 영향이 있는 기존 recovery12개가 PASS했다. 권한 철회/재부여·scope/context·
없는 등록·다른 조회 키/manifest·중복/unknown JSON·암호문 변조·precommit 격리·결과 가용성 분리를 확인했다.
다른 저장/등록/coordinator 시험과 공식249·이전 DB 응답 유실4개는 반복하지 않았다.
297은674fresh/final674·진단없음·cleanupTrue, 전체100.547초다.
신규 명령13.797초/Job CPU12.125초/private최고876.64MiB, 영향 명령0.328초/Job CPU0.203초/private최고53.85MiB다.

## 실제 DB 재시작 검증

새 전용 `D:/devdata/hwpx-agent-p09-pg18-storage-298`의 자격 검증용 fixture에서 실제 저장·등록·CAS·완료를 수행했다.
DB 재시작 뒤 별도 요청 파일을 `completed-handles.preserved.json`으로 옮겨 원 경로에서 읽을 수 없게 했다.
새 함수는 이 파일을 읽지 않고 DB 등록 행과 암호화 영수증으로 정확한 커밋·결과를 관측했다.
추가로 없는 등록의 구분과 잘못된 manifest 거부를 확인해 실제 DB 검사3개를 통과했다.
원 fixture 파일은 삭제하지 않았고, 원본·결과·영수증·기존 DB·실패 증거도 보존했다.

전후 artifact6/available6·job2/성공2·attempt2·authorization0·intent1·revision2/seal2·head2와
암호화 객체6개 SHA가 같다. 복구가 새 실행·도메인 변경이나 요청 파일 재생성을 하지 않았다.
298은681fresh/final681·진단없음·cleanupTrue, 전체116.672초다. 빌드3.625초/Job CPU2.156초/
private최고705.48MiB, 실제 DB 명령6.188초/Job CPU3.906초/private최고72.95MiB다.
시스템CPU최고20.90%·가용RAM최저43.0679%이며 postmaster2회 정상 종료와 두 Job active0/empty/handle closed를 확인했다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 프리즈 해결 증거는 아니다.

## 시도 이력 해석

기존 [P14 durable 정책](../p14/P14-07_DURABLE_POLICY.md)의 State and retry bounds는 이전 시도를 terminal/immutable로 보존한다.
SQL7은 결과 불명 시도에 `unknown_outcome`을 기록하고 SQL23 committed 복구는 job/record를 성공으로 바꾸되
그 attempt 이력을 수정하지 않는다. 295에서 관측한 차이는 이 계약과 일치한다. 실행 당시 이력을 성공으로 덮어쓰거나
기존 SQL migration을 수정하지 않았다. 이는 해당 관측의 해석이며 전체 상태 공간이나 새 상태 조회 API의 완료 증거는 아니다.

## 남은 제품 경계

현재 artifact 키의 읽기 전용 Windows 연결은462에서, 새 SQL24 HWPX 저장·DB 재시작/서명 다운로드 연결은
[464](evidence/p09-361-catalog-windows-custody-sql464.v1.json)에서 확인했다. 현재 전용 경로의 부모는 artifact AES/HMAC 키를 보관하지 않는다.
그 뒤467/468은 새 v2 intent의 원 canonical manifest 보존과 원 manifest 없는 API·실제 SQL 복구를 확인했다.
기존 v1 API는 원 manifest를 계속 요구하며 새 API의 v1 관측은 `LegacyManifestRequired`로 구분한다.
공개 요청 key의 결속은470/471 구현 시험과[472 실제 SQL](evidence/p09-361-public-request-recovery-sql472.v1.json)에서 연결했다.
`PreparedCatalogRequestLookup::recover_registered`는 현재 SQL 관측의 같은 key/job/attempt만 등록 locator로 사용하고,
복구된 revision과 완료 metadata를 대조한 뒤 마지막 SQL 관측이 바뀌면 결과를 전달하지 않는다.
원 공개 요청만 필요하며 원 manifest/claim/locator 파일은 받지 않는다. 기존 metadata-only 조회는 그대로다.
470의23pass/1fail은 보존했고 시험용 영수증 ID만 고정해471에서 실패1개만 통과했다. 원23개는 반복하지 않았다.
472는 재시작 전후 원 파일4개가 없는 복구·변경 요청 충돌·없는 key의 미관측과 bytes 복원,7probe·905fresh/final905·설정1final·산출물2final·cleanupTrue다.
소유 DB 정상 종료2회와 시험 키3개 삭제를 확인했다. 합성 route/scanner와 전용 키이므로 신뢰 제품 실행 자격은 아직 아니다.
기존 v1/실패/시도 이력은 변경하지 않고 복구 관측을 실행·자동 재시도 권한으로 쓰지 않는다.
운영 발급/키 유실 복구·신뢰 scanner/registry는 별도 미완료다. [키 보관 계약](../../protocol/migrations/p09-artifact-windows-key-custody-v1.md)을 따른다.

아래는297/298 원 검증의 경계다. 입력/route/scanner/validator는 합성이며 부모가 보관한 임시 시험 키를 재사용했다.
실제 HWPX 의미·scanner/issuer·네트워크/crash/키 유실 복구·전체 거부 경계와 자격 있는 P09 dispatcher/제품 실행/Native/Gate는 남는다.
다음은 남은 거부 경계와 실제 제품 실행 자격 연결이다. 한글/접근 허용·운영 DB·시스템/Defender/WSL 설정은 건드리지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: [신규10개와 영향12개](evidence/p09-361-registered-recovery-components297.v1.json),
[실제 DB 검사3개](evidence/p09-361-registered-recovery-postgres298.v1.json),
[실제 DB 관측](../../target/p09-sql23-storage-observations-298.json).
