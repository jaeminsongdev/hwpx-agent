# P09 P257 실제90 STOP 검토와 조기 source 완화 후보

2026-10-09. 목표 active. P09·A12·A13 OPEN. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.

## 실제 결과와 누적

runtime 수용83/249 · 잔여166(일반160+corpus6) · 독립source 마감대기1 · 다음index90 · whole재조정대기80.

직전 r105/실제88·89까지 수용83이며90/run010만 새로 실행했다. actual_import::formula_policy_revocation::changed_current_policy_denies_before_revocation_write 본문 exact1/failed0/ignored0/measured0/filtered248/exit0을 캡처했으나 이후 원 parent final_source_freeze 중 CPU 보호로 종료했다. 원 root FAILED_NOT_ACCEPTED, sidecar STOPPED_NOT_ACCEPTED, STOP_SUSTAINED_SYSTEM_CPU를 그대로 보존한다. 본문 재실행 없음. 기존 실행을 runtime 수용84로 승격하지 않았고91을 시작하지 않았다.

원 preparation280읽기/134bound=finalfresh/finished. 전후source의 before1545입력·119242806bytes는 완료, after321입력·53845255bytes만 읽고 중단했다. 원 original_partial_post_source_hash_completed를 true로 바꾸지 않았다. before/partial after를 두 전체 읽기라고 주장하지 않는다. 별도 독립 전체source와 compound 판정이 필요하다. 이는 새 단일 runtime 경계이며 whole1470/historical67/full249/signed16/제품완료/Gate는 별도 미완료다.

## 자원과 정리

root558표본/전체CPUmax100%/95%이상4/98%이상4/최대연속4. 경고 phase는 final_fresh_hash이고 경고 자체CPUmax0.195312%; 직전90.72% 표본의 자체CPU0.189394%. root전체 자체CPUmax5.890139%, private최대54890496bytes, 가용RAM최소34.763802%. 각 경고 표본의Job값은 null이며 이를0으로 만들지 않았다. 기존 단일 보조 표본은 종료 직후전체CPU20%/가용RAM36.91%였다. 모든 물리순간이나 외부PID의 원인을 증명하지 않는다.

원 parent165.61초/319표본, 마지막 자체표본 전체94.89%/자체CPU0.189394%, Job 누적CPU1.156초/peak23.64MiB. body자체표본과 rootowner표본은 서로 다른 시점/분모이므로 parent94.89와 root100을 같은 시점 값으로 합성하지 않는다. root owner의hardSTOP가 전달됐다. 원 Native pressure1회·3표본1.5초yield 관측; 원 owned-reader pressure warning0. 이미 완화를 실행했으나98%x4 hardSTOP를 억제하지 않았다.

원 sourceframe CLOSED/등록해제. 잠금1851 opened=closed, duplicate1866 opened=closed=seekreset, stream identity1866, 남은handle/stream/reader/close실패0. 원 Jobactive0/ownedtreeempty/cleanuptrue. COMMITTED나 원 전체 post hash 완료가 아니다. 전 입력frame의 original_owned_cleanup_confirmed_before_release false는 실패경로의 commit 미수행이며 실제Job cleanup/핸들close 확인과 구분한다.

원 JobCPU6.25% hardcap/affinity1/BelowNormal/active16/kill-on-close/no-breakaway readback 검증, RAM비율보호와 원1200본문·600 IO/Native 제한, Native20·metadata32 및 EXE1/기타2MiB/s를 변경하지 않았다. 원600초·CPU/RAM 기준은 변경하지 않음. CPU 보호 중단 시 자동 재시도 금지. 작업이 없어진 것으로 추정해 중복 실행하지 않고 실제 terminal핸들 확인 후 증거를 읽었다.

## 관련 코드 검토와 최적화 후보

90번 본문은 단일 fixture와 정책 digest 변경 후 revoke 거부/쓰기0 검증이며 무한반복이나 병렬폭증은 확인되지 않았다. 본문 CPU1.156초이고 중단 단계는 실행후source읽기다. run_locked_runtime_r07_case.py의 fresh factory/원 guard, runtime_input_frame.py의 두 boundary와 실패close, borrowed_locked_streams.py의 단독duplicate/seek/identity, locked_runtime_inputs.py의 OpenPacer·Native·stream wrapper, native_open_backpressure.py/near_saturation_read_backpressure.py와 owned_read_backpressure.py의 두 기존표본 경로를 읽어 검토했다. accepted소스/테스트는 수정하지 않았다.

관측90.72→100 및 parent94.89에 비해 원 완화 시작95%가 늦을 가능성을 줄이는 새 EarlySourceCheckpoint 후보를 추가했다. 기존originalcheckpoint를 먼저 실행하고 기존owner의가장최근표본이90%이상이면0.5초씩 쉰다.90%미만의서로다른원표본2회로냉각을판정하고최대8회/4초만대기한다. hard98%x4/RAM/commit/600초guard·deadline은 매대기마다 그대로 실행한다. cached표본·누락/잘못된CPU·시간guard실패는 failclosed. 원95%전역상수나 수용코드를변경하지않는다.

이는 실행을허용하는35%startup gate가아니며, 정상부하에서대기하지않는source읽기의조기yield다. 새로운샘플러/스레드/외부PID조회/CPU stress/OS설정 변경 없음. cleanup은새callback으로감싸지않는다. actualsource연결·낮은CPU입증·PCfreeze해결은 NOT_RUN. 독립source frame에 명시연결해전체읽기/identity/정리를검증하기전에는 runtime수용이나실제최적화완료로주장하지않는다. 입력범위축소·단축source읽기·guard완화는 하지않는다.

## 계약·상태 문서

새 test_checkpoint_queue_stop.py의 실제 literal 실패fixture 변조거부20계약, 가짜표본EarlySourceCheckpoint12계약, 기존peak8계약을 실행한다. 조기90구간yield/두냉각/최대8대기/cached거부/원98%x4STOP/RAM·commit·600실패전달/유한대기/새스레드없음을 검증한다. 이40은 product/body/full-source통과수가아니다.

r105 문서 CURRENT_STATE455630bytes SHA31e24513c3504b5d7372f1947e174cc7e823f2a87fdf4d8a74c9cb6e29a81c48, PROGRESS549262bytes SHAa5cdd8735dc94722935169a71834c5a77c1518ea787a45a26fee051e41733a15를 runtime-progress-r105/에 exact보존했다. 새동일prefix/원bytes suffix와 prior83/실제90pending/GateOPEN 경계를 원Reader의 first+finalfresh로 검증한다. 이전 r105수용문서receipt를 변경하지 않는다. 이번은새P257STOP검토·후보qualification상태이며 누적증가를요구하는불변P256을우회해PASS로만들지않는다.

## Exact 증거

- 이전r105문서: implementation/p09/evidence/locked-r07/p256-checkpoint-metadata-status-doc-r0105-run01.v1.json
  57941bytes / 987793c7fbef6a1cec7d3916c1f69c6622cb29a824721ede08e3ddca7ab5e5f3
- 원실패root: implementation/p09/evidence/locked-r07/p255-case-090-run010.v1.json
  766447bytes / cc598cbc42c399b64eadcd35868f142b3ba51a09d81265029b95f2e4be3595f6
- 원STOP본문sidecar: implementation/p09/evidence/locked-r07/cases/p255-failure-090-run010.json
  483214bytes / 8ce9dfaa8a5efc8f7ef5290f254f6e551098dfcc50aa5ba3ec3393831d8e8e4c
- 원0byte placeholder: implementation/p09/evidence/locked-r07/cases/p255-case-090-run010.json
  0bytes / e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

비밀정보나전체로그를보고서에출력하지않았다. 원failedroot·sidecar·placeholder·수용된코드·원본/private 자료를삭제/이동/덮어쓰지않았다.

## 다음 단계

원단일실패90을먼저검토하고새checkpoint후보를독립전체source경로에연결한다. 원1545입력과새helper/test모두를full실제byte로읽고잠금/동일성/600제한/정리를검증한뒤 별도compound수용판정으로90의본문을연결한다. 그전91/본문90재실행금지. 현재P255.progress는새FAILED90을원래대로차단하므로이를수정하거나무시하지않는다. 새독립증거가실패하면또자동재시도하지않는다. 목표범위와P09 Gate기준은그대로다.
