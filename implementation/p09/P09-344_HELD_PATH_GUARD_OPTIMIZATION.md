# P09-344 — Live held path guard와 계약 합성 원형 생성 최적화 (2026-10-10)

## 결론과 다음 경계

현재 고정 runtime 코드(v13)의 전체 계약 **252×2=504 PASS** 및 작은 실제 Native path adapter 확인을 완료했다. 그러나 전체 source-only run025는 Native 획득 전 anchor/metadata_read_parse에서 CPU98×4 보호로 중단했다. 원 FAILED 및 부분 기록은 그대로다. **수용101/249**, 잔여148(regular142+corpus6), next108, 성공제품108 source closing pending1, whole reconciliation pending98, P09/A12/A13 OPEN. 249개 검증군은 전체 P09 항목 수/진행률이 아니다. whole1470/full249/signed16/product_complete/PC_freeze_resolved는 FALSE 또는 미확정이다.

세 목표 턴(P342/P343/이번 P344)에서 동일 sustained system CPU 보호 중단을 확인했다. 본 턴에서 발견한 안전한 자체 중복 후보를 구현·검증한 후에도 원 full-source 요구 경로는 중단했다. 다음 필수 작업은 current95의 whole1658 source-only 전후 실제 읽기와 독립 compound102 수용이다. 보호 완화/검사 생략/성공제품 재실행/무차별 반복이나 외부 시스템 변경으로 해결할 권한은 없다. 따라서 원장 동기화 뒤 **goal BLOCKED**를 기록한다. 목표를 축소하거나 완료/임의 일시정지하지 않는다. 시스템이 작업 구간에서도 안정된 상태 또는 별도 진단을 진행할 범위가 필요하다.

## 구현 범위와 불변 조건

변경 runtime 파일은 tools/p09/resume_preserved106_queue_runtime.py 및 tools/p09/tests/test_preserved106_queue_runtime.py 두 개뿐이다. full1658/code95/controller191/directory308 및 frozen93, 실제 제품108 실행 v9 코드95, 원본 제품·실패 기록을 보존했다.

1. HeldPathGuard: original AuditEvidenceReader._source 함수와 is_file/is_symlink/is_junction boolean guard를 그대로 실행하되, 정확히 살아 있는 Frame/reader/Borrower binding 안에서 원 잠긴 regular-file handle의 **신선한 Native.inspect 결과**로 세 판정을 함께 공급한다. 파일명이 exact Frame input이고 Native identity/size/type/reparse/noninheritance가 acquisition 정보와 일치해야 한다. source 요청 사이 metadata를 cache하지 않는다.
2. 원 root/path facade를 라이브 binding-token으로 제한하고 stale 객체, 다른 root/원 source 대체, owner thread 불일치, unknown/absolute/traversal/alias, metadata drift, directory/reparse/inheritable 및 직접 facade open을 거부한다. 원 Borrower/P206 wrapper가 duplicate stream을 노출하기 전에 실행하는 별도 fresh stream identity 검사는 그대로다.
3. 각 경계의 reader.root adapter를 성공/STOP/error 모두 finally에서 복구하고 추가 metadata query를 원 lock counter와 **별도 진단**으로 기록한다. native metadata 내부 kernel 호출 수 감소 또는 CPU/프리즈 해결을 측정했다는 주장은 FALSE다. 원 source guard를 생략하거나 원 byte read/identity를 serialized pin으로 대신하지 않는다.
4. Closing synthetic fixture의 대형 frame 원형을 runner-local 한 번만 생성한다. 각 테스트 문서/expected pin/변조 가능한 scope map은 독립 deep-copy하고 current/following runner 사이 원형/build counter를 reset한다. 실제 receipt/Native/검사 PASS cache가 아니다. 기존 검사·guard/결과 처리를 삭제하지 않았다.
5. source021 실패 및 당시 qualified404 코드2/archive와 review022 부분14/13after CPU STOP/code2를 exact literal pin으로 독립 검토한다. 옛 실패를 PASS로 분류하거나 current Native/GO로 승격하지 않는다. 108 제품 재실행 금지는 유지한다.

own1LP/BelowNormal, CPU98×4(.5s), RAM 비율, Job CPU6.25%machine/active16/killclose/RAMcap8%·stop7%, acquisition14/native20/metadata32 no-burst, binary1/other2MiB/s, Native600/metadata720/parent1200, 전후 whole byte/held identity/cleanup 제한은 그대로다. Defender·WSL·OS 설정, 외부 process 종료, Git/빌드/설치/push/한글/접근허용/삭제·이동은 하지 않았다.

## 검증과 실패 보존

- AST와 실제 compile 두 source PASS. 처음 adapter 순수 계약25 PASS 후 binding-token 재사용 거부를 추가했고, 최종 순수26 PASS(0.026초). Native/제품0이며 이를 full504 또는 제품 자격으로 쓰지 않는다.
- review022(v12) CPU STOP: current14 started/stopped/before, after13, runner1/returned0; metadata193bound/193read/18082911bytes/0fresh/미완료. 원 FAILED/정리TRUE, Native/제품0. 코드2는 evidence/p340-v12-partial484-code/에 정확히 보존했다. 484 PASS가 아니다.
- review023(v13) CPU STOP: current152 started/stopped/before, after151, runner1/returned0; metadata196bound/196read/18685721bytes/0fresh/미완료. ownCPUmax6.358382%, private94277632bytes, last4 host100/own5.871212,0,0,0·readDelta0. 원 FAILED/정리TRUE, Native/제품0. 504 PASS나 개별 통과목록 재사용 증거가 아니다.
- Passive idle: 새 workload/Native lock/제품/thread 없이 원 guard로6표본. 마지막 host20.77/0.76/5.53/6.37 및 own0, RAM free 약32.6~33.0%. 시스템이 항상100%라고 주장하지 않는다. 이 관찰은 qualification이 아니다.
- 실제 작은 Native 확인: 현재 source/test 및 frozen locked_runtime_inputs.py **3개 실제 파일**, 원 초기3 read/179427bytes, 두 실제 whole-small byte boundaries. 각3 native metadata query/9 original predicates; 합계6 fresh query/18 original predicates, path metadata probe0, 원 duplicate stream identity 유지. 실제 held identity after regular3/directory4, original handle7/7close, duplicate6/6close/reset6, remaining/closefail/readers/streams0, FrameCLOSED/unregistered, root adapter 둘 다 restore, cleanupTRUE. 원 Job을 합성하거나 FrameCOMMITTED를 주장하지 않았다. hostmax2.72/ownmax0.3861/private28979200/freeRAMmin33.81804%. **full1658/source closing/제품/Gate 자격이 아니다.** evidence/p09-344-held-path-guard-small-native.v1.json은 실제 guarded stdout을 그대로 구조화한 진단이다.
- review024: stop023 bytes/hash/current code/cleanup을 검토하고, 위 실제 Native 확인 및 idle 관찰 후 한 번 진행했다. 전체252+252=504 실제 계약, before/after504·runner2 전후 모두 PASS. metadata196bound/196fresh/392read/37371442bytes/정리TRUE. hostmax17.11/ownmax6.445312/private95010816/freeRAMmin33.10894%. Native/제품0. 이전 failed14/152는 변경하지 않았다.
- source025: 전체source 시도는 **anchor**에서 CPU STOP. metadata182bound/183read/15920654bytes/0fresh·미완료, current whole source Frame acquire 미시작/adapter 미사용/제품0·정리TRUE. 30표본, ownCPUmax1.5625%, private72757248bytes(약69.4MiB), freeRAMmin30.291704%. 마지막4 host100/own0.183824,0,0,0, readDelta857283,0,0,0, readPass183고정, commit약40.4~40.7%. 자체 CPU·RAM 풀로드나 단일 프리즈 원인을 증명하지 않는다. 해당 구간의 원 guarded checkpoint/metadata reader/pacing과 988355byte 원108 receipt 읽기는 bounded이며 새 Native adapter는 아직 연결되지 않았다. 같은 명령을 다시 실행하지 않았다.

## 코드와 증거 pins

Current v13 code2:
- source103973bytes SHA b816eff344fb0d0c179e89a7ddd84293963076a37133c1481678f928d7495f8a
- test59989bytes SHA 2d5be72150a82ac05159e03ae42b49c4dc51889ae39c080c75c3f7d0fb0f599d

evidence/p340-formal504-code/에 현재 bytes/hash와 같은 archive2를 보존했다. review023 실패 실행 코드와 review024 qualified 코드가 동일하다. **current95 fullNative/source는 아직 미자격**이며 작은3-file Native 또는504 계약을 whole Source로 승격하지 않는다.

locked-r07 receipts:
- closing-review022:438848bytes SHA626321cae7d63f9b45d896d986186aa812c1094a59405d06f94c9c43a5af6288
- closing-review023:436239bytes SHA7cf8f144c52682fb8db7c79ceab920bbc47de03b8ab77148f3f1f160acaf3051
- closing-review024:187771bytes SHA3c71d341e8c63086187c8abc22fa6833cbfa64a306da57f793d27e5828464ad5
- closing-source025:81648bytes SHA75675ac835ef192466c5b7adde17e358caabd6559dcc9c06abf6469676c35c2c

Summary evidence/p09-344-held-path-guard-progress.v1.json. Root025 lacks completed preparation/Frame and must be freshly reviewed before any future source attempt. review024 may be reused only for **exact unchanged code95** with complete independent freshness; after any source changes 새 전체 계약 자격을 요구한다.

## 문서, 중단과 다음 재개 조건

r136 문서3개 전체 bytes/hash를 evidence/runtime-progress-r136/에 보존하고 CURRENT_STATE.md와 P09-149에 r137 요약만 prepend했다. 원 기록·원본은 지우거나 덮어쓰지 않았다. 문서 suffix/AST/compile/JSON/pin/archive 검사만 실행했고 **현재 문서 final-fresh qualification NOT_RUN**(마지막 기존 r128/P325와 구분)이다.

이번 PTYs66026/37973/30388/3359는 각각 review022/review023/review024/source025 모두 terminal로 확인했다. 별도 idle/순수계약/작은Native 프로세스도 exit0이고 원 감시기/Native handle/adapter cleanup을 각각 확인했다. 다른 Python process를 자체 세션으로 간주하거나 종료하지 않았다.

다음 재개는 원 실패025/부분23와 현재코드 정확성·cleanup·CPU/RAM 안정성 검토 → 같은 code95의504 자격 재사용 조건 확인/전체 metadata fresh → full1658 전후 실제 source-only 읽기 → 원108 Job/semantic 성공 증거와 독립 compound102 수용 → 다음109 순서다. 성공 제품107/108 재실행, 과거 partial after/full Frame 승격 및 P10 착수는 금지한다. Gate와 전체 제품 완료는 미확정 그대로다.
