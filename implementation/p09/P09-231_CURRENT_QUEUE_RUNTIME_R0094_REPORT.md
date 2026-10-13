# P09 r94: 현재 next-case fixture 분리와 61·62번 실제 수용

2026-10-09. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용56/249 · 잔여193(일반187+corpus6) · 미closing후보0 · 다음index63.
whole재조정대기53. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.
이 수는 고정 r07 개별 runtime 큐이며 P09 전체 완료율이 아니다.

## 현재 진행 계약의 오류 예방

P228은 최초 case60 재개를 검증하는 계약에서 감사된 STOP의 next60/plan53과
현재 계획을 동일 fixture로 사용한다. 그 코드와 tests는 이미 수용60의 source1510에
포함되어 있으므로 수정하지 않았다. 현재 next61/plan54를 그대로 대입하면 정상 큐를
과거 STOP fixture와 혼동하여 실패할 수 있다. 이는 새 본문 실행 전 검토에서 확인한
계약 범위 문제이며 CPU 풀로드 원인이나 CPU 성능 개선의 증거는 아니다.

새 P230 resume_current_queue_runtime.py와 test_current_queue_runtime.py를 추가했다.
이전 anchor/strict record로 고정 P22860을 수용54/next61로 대조하고
SEALED60 572432bytes/SHAf864face44fdfaf2277c0c4bf958fffacf0f968955fd8cc7d169f369e7dac04f를 확인한다.
이전144계약은 감사된 STOP.prior_runtime_plan53을 전달하여 원 범위를 유지한다.
새 현재 큐12계약은 current plan/advance/next 선택을 별도로 검사한다.
합계156=기존144+새12이며 runtime156개 통과라는 뜻이 아니다.
중단·실패 기록은 수용하지 않으며 FAILED/부분 기록의 자동 재실행을 차단한다.

원1510입력은 변경·제외하지 않고 새 코드2개만 추가해1512 scope/extra45를 사용했다.
Rust785/고정EXE/전체 두 실제 byte 읽기/held identity/finalfresh/cleanup은 유지한다.
실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결을 유지했다.
Job CPU6.25%/affinity1/BelowNormal/RAM percent/GO 후 실행/한 watcher/
Native32open/s/no burst/600초/1440표본/원 CPU hard STOP는 바꾸지 않았다.
CPU 보호 중단 시 자동 재시도 금지. 중단 경로·소유 프로세스·CPU·RAM·입력 잠금·
최종 쓰기/정리 증거를 검토하고, 가능한 개선을 새 버전으로 검증한 후 재개한다.
합격한 본문은 다시 실행하지 않고 원장과 소스 무결성만 확인한다.

## 지원 및 실제 결과

LIGHT root37922bytes/SHAa94cea19bcf1378419d69738101d5f60fe445b7de99d0bf44f812afcd4715de1.
160bound=fresh/finished/선택61/accepted product0/지원156/stop=null/cleanup.
이후 서로 겹치지 않게 actual61/run001과 actual62/run002를 한 번씩 실행했다.

61 root578100bytes/SHAdf7488565acdc9066f194b261b7d24a944ea6ce8ff0ae7cb3ab8c44a0b714547.
body174551bytes/SHA26b6963d176c0f5a211a6b6a87d5b473202a3f1bc80355a2cb896e3bf2620dd6.
actual_import::formula_policy_issuer::provision::provision_genuine_root_and_approval_drive_original_changed_and_current_product.
원본/현재 입력의 신뢰 루트·승인 artifact를 구분하고 signer 호출1회,
검증된 bytes==current(original), 미허용 current product route 거부/receipt redacted/no_publication을 검사한다.
합성 fixture registry와 명시적 NOT_production_key_custody이며 운영 SQL/생산 키 인수는 아니다.
exact1PASS/248filtered/exit0/COMMITTED/지원156/Job active0/tree empty.
prep161bound=fresh/finished/read196170076bytes. parent222.22초.
739표본/전체CPU최대35.86%/자체machineCPU최대2.814259%/
자체private최대41988096bytes/가용RAM최소42.075451225694685%.
Job CPU25.469초/peak31.94MiB. STOP/Native warning·pause 없음.

62 root573472bytes/SHA18947d61dad90d325cec87285e1208341a5ce731e9e51c018b60194bbaf6ca27.
body166043bytes/SHA2d85f2227c3a1381e56248d9b4ffbff6ad2d98ae9cd3b4f28a7a6b84e28f218a.
actual_import::formula_policy_issuer::provision::provision_live_registry_revocation_blocks_original_consumer_callback_and_publication.
prepare 뒤 registry read_denied를 설정한 합성 fixture에서 with_verified_bytes 실패/
consumer callback 미호출/current route 거부/no_publication을 검사한다.
exact1PASS/248filtered/exit0/COMMITTED/지원156/Job active0/tree empty.
prep163bound=fresh/finished/read197849929bytes. parent199.4초.
696표본/전체CPU최대37.13%/자체machineCPU최대2.767528%/
자체private최대42496000bytes/가용RAM최소42.17131465555555%.
Job CPU3.312초/peak29.14MiB. STOP/Native warning·pause 없음.

두 사례 모두 전후1512입력 각118919360bytes, 잠금1818/복제3024 모두close/
잔여0/close실패0/resets3024/directory306/ancestor305/별도pathname reopen0.
원 source frame COMMITTED, 원 cleanup 확인 전 release 금지/두 전체 byte 읽기 유지.
JSON 값 제거0/기존 원장 재작성false/new sampler false/CPU 개선 주장false.
전체·자체 CPU는 원 watcher의 표본 최대값이며 전 PC 과정의 무중단 보장은 아니다.
최종 root 쓰기는 owner 종료 이후여서 이 표본의 CPU 측정 범위 밖이다.

## 실패 증거와 경계

원 P222 STOP root208007bytes/SHA78c11517c8bb36289de5b9ade68f0910c2e583c5cba1058895a38b81bb4ff9b0 및
0byte body/SHAe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855는 그대로 보존한다.
P227 parent 연결 지원6857bytes/SHA3e980627f22938f16a9fc46f14b1fa1cf3fe8b63fa7907e73333bc93e1f60c68는
실제 parent 호출/합성 Frame·Job·STOP 반환/정리 후 sidecar 쓰기를 검증한 지원 증거다.
실제 CPU STOP 재현은 NOT_RUN. 새61·62 모두 STOP가 없으므로
실제 중단에서 새 sidecar를 기록했다거나 프리즈 원인·해결이 확정됐다고 주장하지 않는다.
STOP 시 adapter 참조 보관→frame/outer owner 정리→fresh failure sidecar 경로는 유지한다.
CPU STOP를 강제 재현하는 부하 검사·보호 완화·외부 PID 종료·OS 설정 변경은 하지 않았다.

다음index63은 provision_root_failure_keeps_artifact_and_distinguishes_commit_outcome.
현재 남은193(일반187+corpus6)은 개별 runtime 큐이며 전체 P09 잔여 개수는 아니다.
whole1470/historical67/current full249/signed16/실제 SQL/생산 issuer/한글 UI·접근허용/
통합·제품 Gate는 별도 미완료다. full249_current_qualified=false/product=false.
목표는 active로 유지한다.

## 문서 동기화 검증

r93 receipt44541bytes/SHA392248e4886f9955c959f14c7fb5f0d64d9d70168782de5f86bf742160d92532와
그 rootdoc 두 개의 크기·SHA를 대조하여 runtime-progress-r93에 덮어쓰기 없는 정확한 사본을 만들었다.
CURRENT_STATE.md 434668bytes/SHA3e21764923b2886edb2fc4d57d805f5aee8520f0a458d76d98462d16da7ccb9d.
P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md 528300bytes/SHA697598c318046b94cfa1baaf80d439cdb60e17c8bf39201cdcaa5e7585e6d2c9.
새 동일 prefix만 앞에 붙였으며 이전 bytes 전체를 suffix로 보존한다.
P231 새 문서 driver는 현재156계약과 문서16계약/새 actual pair2개/원 STOP·0body/
모든 bound finalfresh/cleanup 후에만 r94 문서 수용을 허용한다.
문서 검증 자체는 새 EXE·GO·full source frame을 실행하지 않는다.
