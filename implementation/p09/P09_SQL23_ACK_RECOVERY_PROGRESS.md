> 2026-10-21 후속: 관측된 attempt unknown_outcome 보존은 기존 P14의 terminal/immutable 계약에 부합한다.
> 이력/SQL migration은 수정하지 않았으며, 등록 영수증 기반 새 복구 진입점은 [후속 현황](P09_REGISTERED_RECOVERY_PROGRESS.md)을 따른다.
> 아래는 이 계약 대조 전의 응답 유실 검증 이력이다.

# SQL23 응답 유실과 실제 DB 복구

실제 PostgreSQL23과 디스크 AEAD를 사용하는 저장 coordinator에서 호출자 응답 유실 네 경우를 확인했다.
주입은 호출자 경계에서 `CommitOutcomeUnknown`을 반환하는 합성 동작이며 실제 네트워크 장애가 아니다.
서비스·엔진·SQL migration과 기존 시험 본문은 변경하지 않았다. 입력 bytes/route/scanner/validator는 합성이다.

## 사례별 결과

| 사례 | 관측과 복구 | 판정 |
|---|---|---|
| register_after | 등록은 DB에 남았지만 커밋은 관측되지 않았다. 재시작 후 등록·영수증을 읽고 허위 committed 복구를 SQLSTATE55000으로 거부했다. | unknown 유지, no_effect 추론·실행 재시도 없음 |
| cas_before | CAS 호출자 경계에서 SQL CAS 실행 전에 결과 불명을 반환했다. 재시작 후 커밋 미관측과 committed 복구 거부를 확인했다. | unknown 유지, no_effect 추론·실행 재시도 없음 |
| cas_after | 실제 SQL CAS 후 응답을 버렸다. 재시작 후 봉인된 revision과 암호화 영수증으로 커밋을 관측했다. 잘못된 영수증의 복구는 거부하고 정확한 precommit으로 성공 복구했다. | job/record 성공, 새 실행·시도 증가 없음 |
| complete_after | 실제 성공 완료 후 응답을 버렸다. coordinator는 추가 unknown 변경을 하지 않았고 재시작 후 기존 성공 상태만 관측했다. | 추가 완료/복구 변경·실행 재시도 없음 |

네 사례 모두 원본·결과·별도 intent/precommit 영수증을 보존했다. 합집합은 암호화 객체24개와
committed oracle 거부3개이며, 각 작업은 attempt1/fence1이다. cas_after의 성공 복구 후에도
attempt_state는 원래 unknown_outcome으로 남는다. 전체 상태 정합성 기준에 따른 후속 검토가 필요하다.

## 보호 중단과 실행 비용 개선

292는 시스템CPU98.52%로 보호 중단했고 cleanupTrue다. 당시 검증 Job에는 CPU cap6.25%·한 코어·
BelowNormal이 적용됐으며 private최고73.83MiB였다. 중단 순간의 부하 주체와 Defender 인과는 미확정이다.
원 실패와 전용 DB는 보존했고 292의 부분 상태는 수용하지 않았다.

사례마다 cluster/schema를 초기화하던 실행기를 단일 cluster/schema와 사례별 tenant로 바꿨다.
사례별 복구·암호화 파일·정상 종료 증거를 즉시 독립 파일에 기록하고 flush/fsync한다.
293은 첫 사례 완료 뒤 다음 tenant slug의 underscore가 원 SQL 제약을 위반해 SQLSTATE23514로 실패했다.
첫 사례의 증거는 남았고 294에서684fresh/final684·runtime1583개 동일성·종료를 확인해 재실행 없이 확정했다.
원 293 전체는 실패로 유지한다. slug만 원 제약에 맞게 hyphen으로 고쳤다.

295는 이미 완료한 register_after를 실행하지 않고 새 전용
`D:/devdata/hwpx-agent-p09-pg18-ack-295`에서 나머지3개만 실행했다. 스키마 준비용 첫 tenant에는
artifact/job을 만들지 않았다. initdb1회/schema23 적용1회·세 사례 checkpoint3개·postmaster7회 정상 종료다.
따라서 고유4개는 이전1개 재사용+이번3개이며, 현재4개를 다시 실행한 결과가 아니다.

295는685fresh/final685·빌드 진단없음·cleanupTrue다. 전체123.438초이며 빌드3.672초/
Job CPU2.047초/private최고706.57MiB, 실제 DB 명령12.375초/Job CPU7.109초/private최고74.03MiB다.
시스템CPU최고21.63%·가용RAM최저41.8705%이며 두 소유 Job active0/empty/handle closed를 확인했다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.
이 결과는 PC 프리즈 원인 규명이나 해결 증거가 아니다.

## 남은 제품 경계

실제 네트워크 단절·실행 도중 crash·부모 임시 키를 잃은 뒤의 복구는 NOT_RUN이다.
실제 scanner/issuer·HWPX 의미 검증·전체 거부 경계·attempt 이력 정합성·자격 있는 P09 dispatcher/
제품 실행·Native/Gate는 미완료다. 다음은 이 상태 정합성과 남은 거부 경계 및 제품 실행 자격 연결이다.
시스템/Defender/WSL 설정·운영 DB·한글/접근 허용 창은 건드리지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: [기존 첫 사례의 입력 검사](evidence/p09-361-sql23-ack-case1-closure294.v1.json),
[나머지 세 사례](evidence/p09-361-sql23-ack-remaining295.v1.json),
[첫 사례 원 증거](../../target/p09-sql23-ack-case-293-register_after.json),
[새 세 사례 관측](../../target/p09-sql23-ack-observations-295.json).

문서 동기화는 확정된 위 실행 증거와 문서 변경 범위만 확인한다. Rust/DB 실행이나 전체 compile 입력의
세 번째 재검사를 하지 않으며, 문서 검사를 runtime 자격으로 승격하지 않는다.
