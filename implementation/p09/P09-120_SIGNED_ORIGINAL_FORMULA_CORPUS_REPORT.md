# P09-120 — 모든 frozen 실제 원본의 signed 수식 SOURCE 소비

## 범위와 구현

P119 production 서명 경로, Cargo dependency/SQL21, 기존 tests/guards는 변경하지 않는다.
기존 P119 test 파일에 child module declaration 한 개만 추가하고 전체 원본을 보존했다(d2ebd2).
새 corpus tests3개와 independent package/section verifier를 별도 파일로 구현했다.
immutable P77 source manifest/원본36의 path/size/SHA는 기존 unmodified loader로 전수 확인한다.
private 원본 HWPX, 기존 native/실패 증거 및 PLANS 삭제 상태는 변경하지 않는다.

원래 private generated policy record → synthetic explicit issuer/root → 실제 ring Ed25519 →
ArtifactService Evidence AES-GCM → current policy/proof/root/source/target 검사 → original product
compiler/candidate/callback의 전체 소비 경로를 실행한다. 단위 issuer/root/metadata 저장소는 RAM이며
production key/trust/승인 registry/actual SQL을 설정하거나 실행하지 않는다.

전체 후보를 original direct importer/evaluator/lowerer와 비교한다. 별도 expanded ZIP inventory 및
validated spine/sec XML 이름·parent·attributes와3개 결과 leaf 바깥 원래 bytes를 대조한다.
이는 독립 preservation comparator이며 scalar 계산기는 공유하므로 independent math/native oracle가 아니다.

## 발견과 검증

초기 strict lint eb273c/session20759 →313d42/exit1은 새 verifier의 case-sensitive extension lint1건이다.
78ef83에서 이미 컴파일된 source3/실행 파일을 보존하고, 새 verifier만 validated original spine/sec
역할·namespace로 section을 선택하도록 변경했다. 파일명 case folding/guard suppression/원본 변경 없음.
수정 strict lint7c4957/exit0 PASS. 1f8a70에서 새2 파일 pre-privacy 원본을 추가 보존하고,
새 byte/corpus/attribute 비교 실패가 원문 전체를 덤프하지 않도록 closed bool assertions로 바꿨다.
privacy 수정 strict lint929a9a/exit0 PASS. 기존 tests는 변경하지 않았다.

이미 컴파일되어 실행 중이던 initial corpus process는 재시작하지 않고 같은 handle을 끝까지 확인했다.
12cea3/session76145 →8a7319/exit0은3 PASS/0failed/0ignored/222filtered/768.31초다.
이 실행은 보존된 initial compiled source snapshot의 증거이며, 이후 수정 source 실행으로 바꾸지 않는다.

실제 원본36의 결과: 수식16/수식 없음20/targets16/source-cell bindings128.
수식16은 모두 source 재계산과 원래 결과가 같아 NoChange16/Changed0였다. 후보 bytes는 원본과 정확히
같다. 이는 실제 original Changed16 승인 또는 native 회복을 증명하지 않는다. no-formula20는 정책/
proof/결과를 생성하지 않으며 initial artifacts2/head를 유지한다. 수식16에서 policy+proof 후 artifacts4,
원래 head/Result 유지, route 거부, latest proof 철회 후 old callback/fresh prepare 거부를 확인한다.

current16은 original과 동일한 bytes의 in-memory inputs이며 새 실제 원본16개로 세지 않는다.
정확한 NoChange·만료 거부·policy generation2 명시적 deny·old product 거부를 전수 확인한다.
보호 변형32는 original16/current16에서 cell protection을 메모리에만 적용하고 유효한 allow 서명에도
product를 거부한다. 원본 파일은 전체 전후 재읽기 equality 및 size/SHA 검사를 유지한다.

최종 source11개 bytes/SHA를06d0a2에서 고정했고 수정 source로 전체 stored225 회귀
b9258e/session72833을 실행한다. source11은 원래 production/module/Cargo8 + 연결 parent1 + 새2개다.
새3개는 stored225 안에 포함하며 추가로 더하지 않는다. 이전 P119의 library/artifact/product/form/
revision suites를 다시 실행했다는 주장, 전체 workspace/package/native/SQL/Gate 주장은 하지 않는다.
최종 accepted run과 byte/negative evidence 결과는 아래 및 동일 이름 원장에 기록한다.

## 보존과 미완료

bb8731/exit0은 unmodified P119 validator를 whole original parent view로 실행한 PASS다.
1081 이전 source 중1080 unchanged/whole parent inverse1 exact/inherited raw2271 및 old executable497
보존. 새 부모1/initial compiled3/pre-privacy2의 whole source archives6개를 유지한다.
P00~P08/user-owned dirty/private/실패 증거/HEAD1f8cd23/PLANS absent를 보존한다.

현재 original 사례들은 모두 NoChange라 independent outside-leaf verifier의 changed section branch는
이번 실제 원본들에서 실행되지 않았다. 다음 제품 검증은 원본16개에서 numeric input만 RAM에서 바꾼
전체 Changed 수식 후보와 해당 comparator의 populated branch다. original/signature/보호 guard를
유지하고 direct math 결과·캐시/visible tuple·whole package·원본 보존을 대조해야 한다.

production issuer/config/key custody/승인·trust registry/actual SQL21/native/원자적 실행/
idempotency/publication/transport, whole import/metadata/coords/comment/rich compiler/field-Date-external
의미 및 P84 SQL 원인은 미완료다. 최소6 coarse groups/closed0 및 최소30 세분 조건 유지.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, P10 미착수/product false/full goal active.
한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없음.

## Final verification

PASS_SOURCE_COMPONENT_STORED225: resource-bounded optimized 재실행의 실제 terminal을 확인했다.

컨텍스트 복구 후 이전 cell242/session72833은 not found/Unknown process였고 같은 이름의 실제
test process도 없었다. b9258e 실행의 최종 terminal이 회수되지 않아 PASS로 채택하지 않는다.
이는 observation timeout만으로 재시작한 경우가 아니다. 현재 source11을 a53abc에서 다시 고정하고
fa9432/session24926으로 같은 전체 stored225를 새로 실행했다. 원본/제품 source 변경은 없다.
047031에서 실행 중 source11 exact, Hwp0, 실제 binary --list225/new corpus3를 확인했다.
a2b063/session43468 →02938a/exit0은 이전 전체 증거 보존 재검증 PASS다.
16734e/exit0은 현재 stored test strict clippy -D warnings PASS다.
522080에서는 현재 전체 회귀의 protection32 test PASS가 확인됐으나 전체 PASS는 아직 채택하지 않는다.

사용자가 PC CPU 압박으로 현재 test executable 중단을 요청했다. 8667c6/exit0에서 정확한
target/p09-120-signed-original-corpus/debug/deps/form_stored_provider-9df9b9ece65a1dfd.exe
경로의 PID26432만 중단하고 해당 경로의 잔여 process0을 확인했다. 자동 재실행하지 않는다.
전체 runtime/current evidence negative8 최종 검증은 미완료이며 원본/기존 증거는 유지한다.

사용자 요청으로 먼저 자원 제한/최적화 빌드를 진행했다. 상세 기록은
`P09-120_RESOURCE_BOUNDED_VALIDATION_REPORT.md`와 `p09-120-resource-optimization.v1.json`에 있다.
기존 executable/중단 source receipt는 원형을 유지했고1f2952에서 whole finalization preimages4개를
추가 보관했다. source11는 동일하며 test worker1/CPU2/BelowNormal/CPU·RAM 자동 중단 보호를 적용한다.
opt-level1/debug assertions true/overflow checks true 빌드는 a5a3d9/exit0 PASS_BUILD_NOT_TEST_EXECUTION.
동일 generated signed case는 ce27fe/exit0으로1 PASS/224filtered/41.39초다. unoptimized301초
미완료와 비교되는 특정 사례 관측이며 전체 성능/원본 Changed/native/SQL/Gate로 확대하지 않는다.
새 binary658c5ea10a96d565의 c38830/session51730/PID12640 →dfbc2d/exit0은 전체225 PASS,
failed0/ignored0/filtered0/544.01초이며 새 corpus3도225에 포함된다. 원본 결과는
16formula/20noformula/16targets/128bindings/Changed0/NoChange16과 current16/protected32 PASS다.
CPU·RAM98samples에서 system CPU max60%/RAM 여유 min17635MiB/test RAM max27.17MiB.
원본 Changed 비교 branch/production trust/actual SQL/native/P09 Gate를 증명하지 않는다.
source evidence checker는 추가 resource receipts/tool pins를 포함하도록 보강했다. e99d57은
현재 component/원본/전체 predecessor 보존 PASS이고 e20452/exit0은 확장 negative tests10 PASS다.
이전1081 source 중1080 unchanged/parent inverse1 exact, inherited raw2271, current source1095,
source delta15/whole archives10/predecessors2/executables7/resource receipts4를 전수 대조한다.
old executables497 + current7 = preserved504이며 전부 재실행했다는 주장은 하지 않는다.
현재 terminal 원장만 SOURCE component PASS로 채택하고 초기 lint, 초기 compiled source PASS,
사용자 CPU 중단, unoptimized bounded duration 중단, 이전 missing-handle 실행은 구분해 보존한다.
