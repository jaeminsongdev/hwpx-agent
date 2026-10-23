# P09 커밋 의도와 읽기 전용 복구

아래는 v1 호환 계약과 초기 검증 이력이다. 새 공통 job의 v2 저장과 원 manifest 없는 등록 복구는
[v1에서 v2로의 계약](p09-stored-commit-intent-v1-to-v2.md)과467/468 결과를 따른다. v1 자료를 재작성하거나 자동 승격하지 않는다.

StoredResultRevisionCas는 CAS 전에 커밋 의도를 기존 ArtifactService의 불변 Receipt로 저장한다.
별도 workspace-precommit.json은 엔진 canonical JSON과 같은 transaction SHA를 갖는다.
이 receipt는 더 큰 intent envelope와 다른 UUID/SHA로 저장하고 복호화 readback한다.
미확인/손상된 precommit은 intent/CAS 전에 거부한다. 새 저장 job SQL과 미완료 연결은
[Precommit와 저장 job 계약](p09-stored-revision-jobs-v1.md)을 따른다. 아래259는 이 별도 저장 전 검증이다.
복구는 서버가 보관한 기대 식별 정보와 저장 의도를 대조하고 기존 sealed revision을 읽는다.
이 경로는 P09 실행 자격이나 자동 재시도를 발급하지 않는다. 영속 job의 intent ID/SHA 등록과
기존 v2 멱등 권한 연결은 미완료이며 실제 DB/프로세스 재시작 검증도 NOT_RUN이다.

## 의도 저장

hwpx-agent.stored-revision-commit-intent/v1은 tenant/subject, manifest/source/result SHA와 크기,
정확한 RevisionService 요청을 보존한다. 평문 원본 본문은 포함하지 않는다.
JSON은64KiB 이하이고 ArtifactKind::Receipt·application/json·revision-intent.json으로 수입한다.
Available/Verified 상태와 복호화 readback의 크기/SHA가 맞아야 원본/head/결과 상태를 다시 확인하고
유일한 CAS를 호출한다. 의도가 미확인/격리되면 CAS를 호출하지 않는다. 수입 오류나 중단 뒤의
저장 부수효과를 자동 삭제하거나 공유 dedup 산출물을 격리하지 않는다.

서버는 조회 가능한 intent ID/SHA와 정확한 요청을 기존 job 기록에 영속 결속해야 재시작 복구를
보장할 수 있다. Receipt 저장만으로 이 job 결속이 완료된 것은 아니다. 사용자가 넘긴 Receipt나
Verified 표기는 실행 허가가 아니며 기대 manifest/request/result 식별 정보를 대체하지 않는다.

## 커밋과 결과의 관측

RevisionService::observe_commit는 기존 sealed node reader를 사용한다. 전체 원 요청·commit/branch·
source/result·plan/validation/transaction·generation·subject·full IR과 봉인 상태를 대조해 정확한
역사적 receipt를 복원한다. 현재 head가 더 진행돼도 그 head를 원 receipt에 대신 넣지 않는다.
PostgreSQL 구현의 기존 reader는 저장된 request/receipt/graph seal 결속을 검증하며 새 SQL/schema나
권한 변경을 요구하지 않는다. 이 코드 재사용을 이번 실제 DB 재시작 증거로 취급하지 않는다.

reconcile_stored_commit는 현재 tenant/subject/read scope·intent ACL/격리/AEAD·서버의 기대 SHA와
manifest/request/result 결속을 확인한다. 잘못된 schema, 중복/알 수 없는 필드, 변조·한도 초과를 거부한다.
복구 중 ingest/CAS/필드 업데이트/job 전이를 호출하지 않는다.

| 관측 | 의미 | 허용하지 않는 해석 |
|---|---|---|
| Committed와 VerifiedAvailable | 원 커밋과 현재 읽을 수 있는 결과를 확인 | 새 실행 자격이나 전체 P09 완료 |
| Committed/Unavailable | 원 커밋은 확인했지만 결과의 현재 사용 가능성을 확인하지 못함 | 결과가 정상 제공되거나 커밋이 없었다는 주장 |
| NotObserved | 원 revision이 현재 관측되지 않음 | 무효과 확정, 안전한 재실행 허가 |
| 바인딩/저장소 오류 | 복구 판정 불가 | 임의 성공, 자동 rollback/재실행 |

## 검증

components259 신규12+영향 기존13=25pass·860fresh/final860·진단/경고없음·cleanupTrue다.
기존13개 시험 본문을 유지하고 영향 범위만 재실행했다. engine26·공식249는 재실행하지 않았다.
정확한 암호화 intent와 새 서비스 인스턴스, 커밋 전후 응답 유실, 후속 head, 요청/subject 결속,
중복/unknown/외부 schema·SHA·64KiB 상한, 의도 격리/AEAD, 결과 격리, scope와 미확인 의도 스캐너를
확인했다. 새 서비스 인스턴스 시험의 backings는 in-memory이며 프로세스나 DB 재시작 시험이 아니다.

전체123.375초·명령12.641초·시험0.16초·Job CPU10.812초·private최고875.72MiB/2.74857%·
시스템CPU최고64.31%·가용RAM최저46.8754%다. Job active0/empty/handle closed와
CPU cap6.25%·private8%/stop7%·RAM/commit95%·기존 시간 보호를 유지했다.
시스템 전체 CPU를 검증 자체 CPU나 프리즈 해결 증거로 해석하지 않는다.

서비스 코드는 실제 구현이지만 저장소는 in-memory이고 manifest/bytes/scanner/validator는 합성 시험이다.
실제 P09 제품 실행/영속 멱등/Native/Gate는 미완료다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: implementation/p09/evidence/p09-361-stored-commit-intent-components259.v1.json.
compact_receipt_json.unpack으로 원래 row를 복원한다.
