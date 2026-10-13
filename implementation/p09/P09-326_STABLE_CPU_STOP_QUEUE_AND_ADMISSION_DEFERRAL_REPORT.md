# P326~P327: 고정 CPU STOP 검토 큐, 진입 포화 유예 및 처리 범위 차이

2026-10-09. 목표 ACTIVE, P09/A12/A13 OPEN.

## 현재 수용 상태

개별 runtime97/249, 잔여152(일반146+corpus6), 다음104. whole재조정94/source마감미완료후보0.
이번 실제 실행은 admission에서 유예되어 수용0, 검증 Reader/소스파일 잠금/Job/제품 child 미시작이다.
P09 전체 완료율을 이 개별 cohort 숫자로 표시하지 않는다. whole1470/historical67/full249/signed16/product 완료 및 CPU 폭주·프리즈 해결은 미확정/FALSE.

## 구현한 own-verification 최적화

과거에는 실패를 검토한 뒤 새로운 runtime/test 세대를 추가해야만 다음 시도가 가능했다. 새 `tools/p09/resume_reviewed_stop_queue_runtime.py`와 해당 test는 고정된 실행 코드에서 **명시적으로 독립 재검토된, 제품 실행 전 hard CPU STOP**을 처리하는 큐다. 이후 해당 CPU STOP만으로 소스/controller 범위를 늘리지 않도록 실행 로직과 검토 receipt를 분리했다.

- 원1644 source + compact2 + 불변P3202 + 불변P3232 + 새runtime/test2 =1652/120,736,387bytes, ancestor308/controller185/code89 예정 범위. 이전 파일/원본/실패/수용 body를 수정하거나 제외하지 않았다.
- 불변P323 directory194 CPU STOP 및 독립 r128 상태, 현재 code87을 literal pin과 live/final-fresh 읽기로 바인딩했다.
- `--mode stop-review --stop-root-pin <exact JSON pin>`: 별도 invocation에서 pre-product CPU STOP/원 cleanup/current code89/정확한 큐·범위/원 빈 body를 다시 확인한다. source frame/제품 child를 시작하거나 계약을 재실행하지 않는다.
- `--review-pin <exact independent review pin>`: 다음 실행은 해당 review와 원 실패 root를 live/final-fresh 읽고 typed classification을 다시 계산한다. 검토되지 않은 실패, 다른 root/hash/code/범위, 미완료·미정리 review, post-product 단계는 GO를 막는다.
- 실패 행을 수용으로 세거나 cursor를 전진시키지 않는다. 성공 body는 원 typed Native/Job/두전체byte/current scope classifier로만 단일 전진한다.
- sidecar는 owned_parent의 DEFERRED_NOT_STARTED/workerFALSE/jobFALSE/productFALSE/cleanupTRUE일 때만 pre-product 후보로 취급한다. 제품이 실행된 실패나 상태가 모호한 실패는 재개 대상으로 거부한다.
- 알려진0byte placeholder만 원 pin으로 확인해 보존한다. 비어 있지 않은 제품 body, 알 수 없는 placeholder는 재개 대상이 아니다.
- 원 CPU98x4/RAM/commit/600초/720읽기/acquisition14/global20/noidleburst/두전체byte/identity/Job/cleanup 유지. guard를 완화하거나 성공 본문을 재실행하지 않았다.
- source가 더 이상 늘지 않는다는 정책은 이 **hard CPU STOP 경로**에 한정한다. admission 포화 유예 등 모든 오류를 지원한다는 주장은 하지 않는다. 아래 새 처리 범위 차이가 실제로 확인됐다.

정식 검증 후 이 runtime/test는 불변이다. CPU 성능이나 프리즈 해결 자체를 입증한 변경은 아니다.

## 동작 및 거부 검증

현재182 + following182 =364 실제 계약 PASS, 각 검사 전후364회/runner 전후2회를 기존 checkpoint로 확인했다. 기존134개 계약을 유지하고 새48개로 명시 review/변경된 pin·scope·코드 거부, cursor불변, 제품 실행 여부, 핸들 정리, 빈 body/비어 있지 않은 body 구분 등을 검증했다. 기존P323268 및 원78/compact26/helper21/retained1486 재사용을 이번364 실행에 합산하지 않았다.

- preformal364:104bound/fresh104/208read/9,222,492bytes, cleanupTRUE/STOP없음.
- 정식 light364:104bound/fresh104/208read, selected104, 제품/Native 실행 아님.
- 독립 light 재확인:105bound/fresh105/210read/9,305,248bytes, current89 pin 대조/최종fresh 완료/cleanupTRUE/STOP없음. 계약·제품·Native 재실행0.
- 사전 observer58표본: hostmax34.6%, ownmax6.496063%, private47,353,856bytes/freeRAMmin22.7682695603%. 샘플 최대값은 own Job hard cap과 혼동하지 않으며 이 구간만의 측정이다.

소스53,147bytes SHA256 `78d6be8603070e5c5377ee2643b23fd9eb27af3390ff093d5f3c8e172563db76`.
test39,711bytes SHA256 `c7e1454f21011f2c2ffb92eb52f749be6c621d20d7a53a58a70d92cc415bd7cb`.

364 동작 계약은 실제 STOP-review mode, review-pin을 사용하는 제품 재개, full1652 Native closing qualification이 아니다. 이 실제 경로들은 아직 NOT_RUN이다.

## 실제104 진입 유예: hard CPU STOP와 구분

명령: `python -B tools/p09/resume_reviewed_stop_queue_runtime.py --mode actual --run 2`.

원 상태 FAILED_NOT_ACCEPTED, error DEFERRED_ALREADY_SATURATED_SYSTEM, **resource_stop_reason NULL**, watcher cleanup TRUE. admission 최초 완료 표본1개가 host100%여서 원 admission guard가 즉시 유예했다. 이는98% 연속4회 hard CPU STOP가 아니다.

- selected index NULL, runtime contract count NULL.
- 검증 Reader/Frame/소스 잠금/부모 adapter/Job/제품 미시작. 관련 연결 flags 전부FALSE.
- body/case root/sidecar 없음. `p326-admission-run002.v1.json`만 보존했다.
- own parent CPU0, own private31,301,632bytes/working set41,791,488bytes, freeRAM22.6181174404%, commit41.9366754697%.
- 원 raw system delta idle0/kernel9,531,250/user70,468,750/total80,000,000(100ns), own ProcessTimes 증가0. 원 ratio와 일치한다.
- 바깥PowerShell exit0과 실제exit2를 구분한다. 이 실행을 즉시 재시도하지 않았다.

원 admission receipt10,649bytes SHA256 `5f2baeab8d3a1a1c61dfc75af46acd0280dd46d617227ce666e7f56a549548fa`.
raw packet257,303bytes SHA256 `e3591882093ff2906581071dd537ea83af459cd98bd623672460a942a30caa2e`.

## 현재 CPU 상관 관측

별도 전후 PerfProc2 snapshot의3.6661036초 counter window에서 host busy100%, MsMpEng 평균75.33117%, RadeonSoftware5.647174%, System3.169876%였다. 이 짧은 실행 구간에는 MsMpEng의 큰 기여가 관측됐다. 누가 Defender 활동을 유발했는지, 순간100%의 단독 원인, 프리즈 root cause까지 확정한 결과는 아니다. 구간 중 생성·종료되어 빠진 우리 Python의 interval CPU를0으로 만들지 않는다. 원 admission 표본의 ownCPU0과 별도 endpoint interval의 누락은 구분한다.

실행 전 compiler family filter에는 maple-re90516만 있었으며 cargo/clippy-driver/rustc는 없었다. 이전 턴의 Clippy chain을 현재 상태라고 재사용하지 않았다. 어떤 foreign process/Defender/WSL/OS 설정도 변경·종료하지 않았다. counter는 원 자원 guard에 공급하지 않았다.

독립 admission 검토: root/rawpacket2bound/fresh2/4read/535,904bytes/finishedTRUE/cleanupTRUE/STOP없음. 원 NULL reason/미실행/단일 표본/ratio를 확인했다. 제품·Native 재시도0.

## 확인한 새 처리 범위 차이와 다음 구현

문서 최종 마감 P328 run01은 final-fresh metadata 경로에서 STOP_SUSTAINED_SYSTEM_CPU로 종료됐다. 114bound/fresh55/169read/10,068,961bytes/finishedFALSE, watcher정리TRUE다. 전체 최종fresh 완료나 현재문서 PASS를 주장하지 않는다. 이미 독립적으로 완료된 light364/105fresh 및 admission review2fresh qualification은 별도 유지한다. 실패/부분 IO와정확한명령을 p328-r129-status-final-fresh-CPU-stop-run01.v1.json에 보존했다. 원inner90·hard callback/2MiB/600/720·cleanup을 재검토했으며 같은문서검증을 반복하거나 guard를완화하지 않았다.

정식 P326 pre-product 재개 classifier는 `error_code == resource_stop_reason == STOP_SUSTAINED_SYSTEM_CPU`만 지원한다. 실제 발생한 admission deferral은 error DEFERRED_ALREADY_SATURATED_SYSTEM/reasonNULL이다. 따라서 P326 큐는 이 실패를 hard CPU STOP로 승인하지 않으며 해당 실패가 남은 상태의 자동 GO를 막는다. 이 차이는 해결된 상태가 아니라 **구현 미완료 항목**이다.

다음 코드 변경은 별도의 불변 새 세대에서 admission deferral을 독립된 실패 유형으로 분류해야 한다. Reader/Frame/Job/제품이 시작되지 않았음, cleanup TRUE, 원 reasonNULL/원 표본/현재 코드·light qualification을 보존하고 새로운 실제 실행에서는 원 admission을 다시 수행하도록 검증한다. NULL을 hard CPU STOP로 바꾸거나 검토 없이 실패를 건너뛰는 방식은 금지한다.

콜드 Python invocation마다 큰 검증 helper graph를 다시 import하는 부담도 측정 가능한 own 최적화 후보다. 이를 줄이려면 loaded-code identity/current source/full scope/owner lifecycle를 보존하는 설계와 검증이 먼저 필요하다. 현재는 구현·CPU 개선·Defender 유발 인과를 주장하지 않는다.

host 포화 시 강제 실제 검증/맹목재시도는 하지 않는다. 사용자 목표는 ACTIVE이며 안전한 코드 수정·증거 작업은 아직 가능하므로 BLOCKED나 완료로 바꾸지 않는다. P09 Gate 전 P10 구현 없음.

r128 두 문서 전체를 `evidence/runtime-progress-r128/`에 byte-exact 복사했다. r129 prefix 외 suffix를 보존하며 문서 최종fresh 검증은 별도 receipt로만 확정한다. 접근허용/Hangul/빌드/Git/OS·Defender·WSL 변경/프로세스 종료 없음.

