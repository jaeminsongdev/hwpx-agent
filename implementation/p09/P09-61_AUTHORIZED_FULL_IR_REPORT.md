# P09-61 승인된 전체 IR 커밋 구현 결과

- 일자: 2026-10-03
- 상태: **격리된 실제 SQL metadata component PASS / P09 Gate 미완료**
- Goal: ACTIVE; P10 보류; 접근 허용 및 Hwp COM/UI 활성화 없음.
- 정책: [P09-61_AUTHORIZED_FULL_IR_POLICY.md](P09-61_AUTHORIZED_FULL_IR_POLICY.md)

## 구현 결과
P60의 schema18 IR CAS leaf를 기존 실제 idempotency 승인 흐름과 연결했다. schema19의 새 claim/commit API, immutable IR intent, receipt trigger로 저장할 IR을 admission부터 커밋까지 고정한다. 임의 IR 교체, IR 누락, 다른 scope/subject, 무승인/잘못된 fence/검증 전 상태, 이미 소비한 승인 token, 기존 API로 IR을 버리는 우회가 거부된다.

새 schema19만 추가했으며 기존1~18 migration/함수/검증 기준은 변경하지 않았다. 기존 v2 claim/commit 전체 body를 각각5개 additive transformation 아래 정확히 보존했고, 실제 runner가 대조한다. 내부/leaf PUBLIC EXECUTE와 테이블 직접 쓰기는 허용하지 않는다. 실제 lease API가 발급한 authorization만 사용하며 fixture는 auth row/flag를 조작하지 않는다.

## 실제 실행
고정 로컬 PostgreSQL image18.4(Debian18.4-1.pgdg12+1), network none, no host ports/mounts, tmpfs DB에서 **전체 schema1~19**를 적용했다. 원래28개 reconciliation 회귀와 새25개 IR 검사를 같은 전체 schema에서 실행했다.

| 실행 | 결과 | 증거 |
|---|---|---|
| 새 첫 실행 cdb14d | FAIL: 무승인 P60 fixture가 새 intent guard에서 먼저 거부됨. 새 runner가 예전 첫 오류만 기대한 결손 | initial-failure |
| 두 번째71138/d66092 | 기존28 PASS; 새 fixture 완료 단계 FAIL IDEMPOTENCY_COMMITTED_ORACLE_FAILED | completion-fixture-failure |
| 수정 후57548/866d6b | 실제 기존28 + 새25 PASS, host exit0 | actual-sql-pass |
| 독립 새 컨테이너71313/228814 | 실제 기존28 + 새25 다시 PASS, host exit0, 동일 source26 pins | actual-sql-fresh-pass |

두 번째 실패의 원인은 새 fixture receipt artifact SHA=5와 요청 transaction receipt SHA=6 불일치다. receipt fixture와 object-key를 요청의6으로 일치시켰다. 완료 oracle/원래 guard는 손대지 않았다. 첫 오류는 새 BEFORE trigger의 정상적인 선행 거부였고, 새 harness의 기대값만 해당 명시적 거부로 수정했다. 최초4개 소스와 두 번째 harness, 변경 전 PLANS 전체를 별도 archive에 보존했다.

새25개: table 직접 INSERT/내부 leaf 호출 거부; null/wrong-kind/digest/package 거부; 실제 claim/exact replay/IR 교체 충돌; 무승인 거부; 실제 worker/lease/attempt/fence 확인; wrong fence/stage/scope/subject/IR 거부; 원래 API 우회 거부; 실제 generation1 커밋; token 일회성 소비; 실제 완료/terminal replay; 단일 job/attempt/IR/revision 및 head/링크/승인 소진 확인; intent/revision 불변; 읽기 ACL 재검사.

모든 성공 실행에서 rollback gate 거부, 빈 intent down/reapply, IR data가 있는 down 거부와 기존 링크1개 보존을 확인했다. 원래 P60 fixture9개 전체는 원문 그대로 실행하여 여전히 **FAIL**이다. schema19에서는 새 intent guard가 FULL_IR_COMMIT_INTENT_MISMATCH를 먼저 발생시킨다. 원래 schema18의 IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED 실패 증거를 PASS로 바꾸지 않았다.

## 보존/정리
- 이번 턴 실제000358: P59/P60 source/archive39 pins 모두 exact.
- 원래 P48 전체1551 files/51,047,460 bytes를 기존10개 archive origins로 hash 재검사했고 모두 exact. **전체 원래 CLI 재실행은 아니다.**
- 원래 native75개 전체 hash exact, Hwp.exe0. 마지막 process count도 재확인했다.
- 이번 테스트 컨테이너4개는 각각 run label/name/image를 확인 후 제거했으며 해당 prefix 잔여0을 확인했다. 테스트 데이터만 제거되었고 원래 문서/증거/운영 DB는 변경하지 않았다.
- Rust 파일 변경/신규 Rust 실행은 이번 턴 없다. P60의135개 Rust PASS는 이전 턴 결과로 그대로 보존한다.

## 증거
- [첫 실패](evidence/p09-61-authorized-ir.initial-failure.v1.json)
- [완료 fixture 실패](evidence/p09-61-authorized-ir.completion-fixture-failure.v1.json)
- [실제 SQL PASS](evidence/p09-61-authorized-ir.actual-sql-pass.v1.json)
- [독립 fresh PASS](evidence/p09-61-authorized-ir.actual-sql-fresh-pass.v1.json)
- [소스/보존 진행 영수증](evidence/p09-61-authorized-ir.source-progress.v1.json)
- 원본 archive: source-archive/p09-61-initial-authorized-ir/

## 다음 안전한 작업
durable Rust revision repository/실제 SQL API binding과 최상위 stored full-IR product request를 연결하고, 실제 importer/issuer/publication 및 retention/GC/recovery의 미검증 경계를 닫아야 한다. 네이티브34회 묶음은 원래 전체 source replay + 새 admission 및 사용자 허용 전 실행하지 않는다. SQL metadata PASS를 native/visual/semantic/differential/제품/P09 Gate PASS로 승격하지 않는다.

