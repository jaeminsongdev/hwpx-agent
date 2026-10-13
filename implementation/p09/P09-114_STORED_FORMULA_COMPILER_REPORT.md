# P09-114 — 실제 저장 원본의 계산 필드와 기존 작업 컴파일러 연결

## 변경한 제품 코드

authenticated source → actual field ranges/meanings → original evaluator → preserving whole candidate를
원래 OperationPlanCompiler에 연결했다. source head/revision과 실제 meaning graph/fieldBegin ID를 사용한다.
호출자 공급 map/AST/result/IR로 대체하지 않으며 partial markers와 full-source admission guard를 유지한다.
변경된 필드만 original Atomic plan에 묶고 source/candidate/math SHA 및 actual Decimal을 locked args로 고정한다.
원래 결과 API는 유지하며 새 prepared plan은 fresh ACL/AEAD/head/source/math 검사를 재수행한다.
reference-ID 인덱스를 사용하여 반복 선형 검색을 줄이고 duplicate bindings는 거부한다.
이것은 컴파일된 후보 데이터 연결이지 issuer/registry/backend 실행 권한이나 transactional lease가 아니다.

capability table.formula의 기존 P06 native route 자격은 새 Field-result argument 계약에 상속하지 않는다.
original result route는 여전히 RouteUnqualified이고 full-source context는 Projection으로 거부한다.
완전하지 않은 actual graph의 marker를 지우거나 합성 full-document graph로 경로를 열지 않았다.

## 검증 및 증거

최종 production/test source를 고정한 뒤 package lib +11 integration suites136개는 통과했다
(08e328/session62418 →0ccd64/exit0).
저장 경로176 + 기존 제품 요청10 + form 작업18 =204개도 통과했다
(609573/session22718 →134b1d/exit0; stored384.04초). 총340개 실행은 서로 다른
executable + fully-qualified function pair340개이며 신규6개를 포함한다. --list15개는
2fcdf0/exit0로 실제 확인했다. 이 숫자는 제품 기능/고유 fixture 개수가 아니다.
최종 strict lint는 경고를 오류로 처리하여 통과했다(2270a0/exit0).
새 Rust4개 format와 git diff --check도 통과했다(b9d658/exit0).

새 integration6개는 여러 구역4수식, current/empty 혼합과 changed field2개,
원래 Field target/source revision/graph 및 direct whole candidate와의 동일성,
canonical compiler roundtrip, ACL/AEAD/head/quarantine, 5 provider-scope 대체,
두 번째 구역 보호/invalid numeric 전체 거부, full import/route 거부를 검사한다.
immutable actual36 manifest는 그대로이며 새 test data는 in-memory derivative다.
native 재캡처/재계산 또는 실제 SQL/durable publisher 검증이 아니다.

최종 이전 관측에서 handle이 사라진 CLI run의 부분 출력은 완료 증거로 세지 않았다.
프로세스 부재를 확인하고 final-source 새 회귀를 실행했다(609573/session22718).
동일한 live handle을 기다리며 관측 timeout만으로 재시작하지 않았다.
Focused pre-lint6 및 부분 run은 최종 고유 실행 합계에 더하지 않는다.

## 실패·원본 보존

초기 compile 타입 오류(set_permissions u64/unit), 함수110lines/doc Markdown lint,
duplicated fixture module lint, adapter import의 extra super 오류를 고쳤다.
초기 source와 pre-lint executable은 보존했고 lint suppression/guard 완화는 없다.
batch fixture 몸체는 원래 P113 helper와 같고 import만 기존 evaluation module로 재사용하도록 바꿨다.
exact-body 비교는 독립 Python 검사로 통과했다(addab7).

P113 source1009 중1007 unchanged + 부모2 whole preimage/정확한 역변환을 확인했다.
P113 unmodified current audit를 preimage view에서 실행하여 inherited raw2012, oldexe401을 보존했다
(124158/exit0). 현재 original source 보존은 source1021/delta14/archive8/predecessor2/executable18으로 기록한다.
이18개는 final test15, 실행하지 않은 CLI copy2, pre-lint diagnostic1이다.
old executables/native qualifications 전체를 재실행한 것이 아니다.

현재 source component validators15 PASS/green0(a0e041) 및 original default matrix_drift/exit1(ca1557)은 유지한다.
PLANS 삭제 상태, private/reference locks, P00~P08 및 사용자 dirty 변경을 보존한다.
새 receipts의 byte/SHA는 source-progress에 고정하고 최종 Python/physical audit는 final-audit에 따로 남긴다.

## 남은 구현과 다음 경계

generic original compiler 연결은 구현했지만 full document importer 및 field-result용 strict product request,
full field/date/external/document semantics, trusted protection/policy/issuer/signed registry,
atomic durable execution/publication은 미완료다.
다음은 원래 strict 제품 요청이 form_input만 받는 계약과 실제 source field-result 연결을 통합하는
전체 계약을 구현하는 것이다. 부분 graph/후보를 full import 또는 실행 권한으로 승격하지 않는다.
fresh source 검사와 request identity가 실제 durable CAS/idempotency/publication을 대신하지 않는다.

metadata/coordinates, full comment/rich compiler/source mapping, durable integration,
field/date/external/document 의미·전체 제품 연결, trusted issuer/protection/atomic publication,
actual P84 SQL 원인·회귀의 최소6 큰 묶음은 유지한다. 이번에 닫힌 큰 묶음은0이며 정확한 작업6개가 아니다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED/product false/no P10/full goal active.
한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동은 실행하지 않았다.
