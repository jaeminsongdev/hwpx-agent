# P09 저장 서비스와 revision CAS 연결

StoredResultRevisionCas는 WorkspaceTransaction의 봉인된 precommit 요청을 실제 ArtifactService 수입과
RevisionService CAS에 연결하는 서버 저장 primitive다. 현재 P09 실행 자격을 발급하지 않으며,
CLI/MCP/JSON 실행 경로나 합성 검증을 실제 HWPX 의미 검증으로 승격하는 기능은 없다.

## 서버 입력과 저장 절차

인증된 두 서비스 context는 같은 tenant/subject와 document.read/write를 가져야 한다.
서버는 manifest·검증된 출력·validation summary, project/branch·expected head·commit/revision ID를
보관하며 사용자가 보낸 Verified 플래그나 실행 문자열로 이를 대체하지 않는다. 원본/출력은 각각32MiB
이하이고 빈 출력·원본과 같은 결과·일치하지 않는 base revision은 거부한다.

엔진 요청의 transaction/source/base/manifest SHA와 결과 SHA/크기를 대조한다. 현재 head와 sealed node의
원본 결과를 확인하고 실제 descriptor·ACL·격리 상태·복호화 AEAD·크기/SHA를 검증한다. 실제 수입 뒤
결과의 Result/Available/Verified·MIME·크기/SHA와 복호화 readback을 확인한다. 마지막 원본/head 및
결과 descriptor를 다시 확인한 뒤 원 compiled plan SHA·validation summary·precommit receipt SHA를
RevisionService 요청에 결속한다. 서버 clock callback은 각 저장 경계에서 호출된다.

이 관측과 CAS 사이의 ACL/격리 상태를 분산 잠금으로 고정하지는 않는다. 마지막 head 경합은 실제 CAS가
판정한다. 최종 결과 receipt도 요청 SHA·새 revision·head generation과 대조한다.

## 실패와 복구

| 결과 | 엔진 처리 | 서비스 산출물 처리 |
|---|---|---|
| 정상 commit와 일치하는 receipt | Committed | 실제 UUID 결과를 sealed revision에 연결 |
| 알려진 head 충돌 또는 실패 | 기존 Conflict/Failed와 로컬 격리 | 수입 결과를 복구 대상으로 보존 |
| CommitOutcomeUnknown 또는 다른 성공 receipt | RevisionCasOutcome::Unknown → RevisionOutcomeUnknown, Incomplete/CommittedOutcomeUncertain | 보존하고 조사, 자동 rollback·격리·재실행 금지 |

반환된 descriptor·서비스 요청/receipt·출력 SHA를 조회할 수 있다. 수입 결과는 dedup으로 다른 요청과
공유됐을 수 있으므로 삭제/격리하지 않는다. 수입 오류에도 저장 부수효과가 있을 수 있으므로 반환 descriptor
부재를 저장 부재로 해석하지 않고 SHA로 조사해야 한다. 단일 adapter의 재호출은 다시 수입/CAS하지 않는다.
후속 의도 저장 경로는 CAS 전에 불변 Receipt를 수입하고 원 요청의 읽기 전용 커밋 판별을 제공한다.
영속 job의 intent ID/SHA 등록과 기존 v2 멱등 권한 연결은 미완료이며 파일/저장소/DB 분산 원자성은 없다.
[커밋 의도와 복구 계약](p09-stored-commit-intent-v1.md)을 따른다. 아래255/256은 의도 저장 전 검증 이력이다.

## 검증 범위

components255는 엔진 신규3+기존23=26pass 뒤 새 서비스 시험의 match arm 반환형 E0308로 컴파일 실패·
서비스 시험0이었다. recovery256은 그 시험 arm만 고쳤고 엔진/서비스 구현과 기존 시험의 해시를 유지했다.
서비스13pass·852fresh/final852·진단/경고없음·cleanupTrue이며 엔진26과 공식249는 반복하지 않았다.
증거 합집합39개 중 신규16개다. 정상 저장/커밋, 커밋 전후 응답 유실, 잘못된 성공 receipt, 실제 CAS 경합,
알려진 실패, 원본 권한 철회/격리/AEAD, 결과 스캐너 미확인/AEAD, 공유 dedup 보존, scope/binding/한도,
single use와 비노출을 확인했다. 기존 원본·bytes·무결성·fault 시험 본문은 바꾸지 않았다.

256 전체112.828초·명령3.422초·시험0.08초·Job CPU3.0초·private최고727.44MiB/2.28318%·
시스템CPU최고15.79%·가용RAM최저46.9934%다. Job active0/empty/handle closed,
CPU cap6.25%·private8%/stop7%·RAM/commit95%와 기존 시간 보호를 유지했다.
엔진26이 실행된255는 전체66.750초·시스템CPU최고29.36%·가용RAM최저46.6954%이며
컴파일 실패를 포함한 owned Job 최고 private는869.53MiB다. PC 프리즈 해결을 주장하지 않는다.

서비스 암호화/수입/CAS 코드는 실제 구현이지만 저장소는 in-memory,
manifest/graph/bytes/scanner/validator/validation summary는 합성 시험이다.
실제 HWPX 의미 검증·영속 DB/멱등·현재 P09 제품 실행 연결/자격·Native/Gate는 미완료다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거는 implementation/p09/evidence/p09-361-stored-revision-commit-components255.v1.json 및
p09-361-stored-revision-commit-recovery256.v1.json이다. compact_receipt_json.unpack으로 원래 row를 복원한다.
