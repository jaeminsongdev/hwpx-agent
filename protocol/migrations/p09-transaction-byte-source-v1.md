# bytes 원본 트랜잭션과 게시 무결성

`WorkspaceTransaction::execute_bytes`는 검증된 저장 원본을 파일 경로가 아닌 불변 bytes로 받는 엔진 API다.
기존 파일 입력과 같은 staging·validator·게시·CAS·실패 복구 상태 절차를 공유한다.
P09 제품의 현재 실행 자격을 발급하거나 저장 서비스를 직접 호출하지 않는다.

## 입력과 상태 보존

bytes의 크기/SHA를 원 manifest와 대조한 뒤 Cow::Borrowed로 전달한다. 외부 원본 평문 파일은 요구하지
않으며 원본 staging은 격리 작업공간 안에만 만든다. 원 파일 입력은 원래 링크·포함 범위·읽기·변경 감지
메서드로 위임한다. 상태, fault point, source unchanged, no overwrite, 실패·quarantine·CAS 기록은 공유한다.

## 재현한 결함과 보강

probe251은 기존 P04 시험 파일의 원장 누락 KeyError로 Cargo/시험0이다. 원 Git HEAD blob과9개 시험 본문을
대조해 새 시험 child만 추가했음을 확인했다. probe-recovery252는 validator에서 staging 파일을 바꾼 뒤에도
성공이 반환되는 음성 시험 실패1개를 재현했다. 이 결과는 수용0의 결함 증거이며 실패 원본을 보존한다.

components253은 validator 뒤·게시 뒤·CAS 뒤에 실제 파일의 크기/SHA를 다시 확인한다. 게시 전 손상은
게시/CAS를 차단한다. CAS 뒤에 손상이 확인되면 완료나 자동 rollback으로 포장하지 않고
Incomplete/CommittedOutcomeUncertain으로 남긴다.

추가 재검사만64KiB 버퍼를 사용하는 bounded streaming이다. 기존 validator readback 전체 버퍼는 유지하며
트랜잭션 전체가64KiB라는 뜻이 아니다. 입력/출력 상한은 그대로고 초과·짧은 읽기·동일 크기 hash 변조를
거부한다. 이 검사는 동시 쓰기를 막는 파일 잠금이나 파일·DB 사이 분산 원자성 보장이 아니다.

## 검증 결과

253 신규14+영향 파일9=23pass·844fresh/final844·진단/경고없음·cleanupTrue다.
원 파일9개 시험 본문과 probe의 원 음성 사례를 바꾸지 않았다. bytes/파일 receipt 동등성과 외부 원본 파일
불필요, SHA/크기/빈 입력 거부, 상한·validator 실패, CAS 충돌/실패, 모든 정상 전이의 앞뒤 fault,
복구 fault·single use·no overwrite·비노출·staging 변조·CAS 후 손상·무관한 외부 파일 보존을 확인했다.

전체111.766초·명령3.344초·시험0.23초·Job CPU2.062초·private최고440.98MiB/1.38409%·
시스템CPU최고19.07%·가용RAM최저56.9722%다. Job active0/empty/handle closed와 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초/guard600초를 유지했다.
자식 TEMP/TMP만 target/p09-transaction-byte-scratch-253으로 고정하고 시험 하위 폴더가 비었음을 확인했다.
시스템 환경·보안 설정을 바꾸지 않았으며 PC 프리즈 해결 증거가 아니다.

근거: implementation/p09/evidence/p09-361-transaction-bytes-components253.v1.json 및
p09-361-transaction-bytes-probe-recovery252.v1.json. compact_receipt_json.unpack으로 원래 row를 복원한다.

## 남은 제품 저장 연결

실제 filesystem 동작은 자기 소유 시험 scratch이고 manifest/validator/CAS는 합성이다.
제공자가 소유한 현재 원본과 출력 검증을 이 API에 연결하고 실제 ArtifactService 수입·RevisionService CAS·
영속 멱등 처리를 완결해야 한다. 현재 target/registry 실행 자격과 Native/Gate는 미완료다.

원 RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
