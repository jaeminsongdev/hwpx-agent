# P323~P324: 부모 반환 기록 순서 수정 및 source acquisition STOP 검토

2026-10-09. 목표 ACTIVE, P09/A12/A13 OPEN.

## 결과와 수용 경계

개별 runtime97/249 수용, 잔여152(일반146+corpus6), 다음104. whole재조정94, source마감미완료후보0.
이번 실제104는0개 수용이며 제품/SQL/Cargo/Hangul child를 시작하지 않았다. 예정1650/code87의 두 전체 byte·Native closing qualification은 미완료다. 이전 actual103의1644/code81 Native 수용과 구분한다.
whole1470/historical67/full249/signed16/product 완료 및 CPU 폭주·PC 프리즈 해결은 미확정/FALSE다. 이 숫자는 P09 전체 완료율이 아니다.

## 실제 수정

새 `tools/p09/resume_recorded_parent_return_runtime.py`와 해당 test는 기존P320을 수정하지 않은 별도 실행 경로다.

- literal P320 CPU STOP root/sidecar, 독립 STOP review, r127 accepted97 상태를 typed classifier로 바인딩한다. 실패 root에는 PASS 전용 classifier를 사용하지 않는다.
- 불변P320 runtime/test2와 compact2를 현재 live/final-fresh 확인한다. 기존1644 source를 그대로 유지하고 새6을 포함하여1650/120,643,529bytes, ancestor308/controller183/code87을 예정 범위로 사용한다.
- 부모 반환 직후 원 반환code와 capture.pending/rejected의 boolean만 기록하고 **같은** `held.mark('after_parent')` guard를 정확히1회 호출한다. 원 실패 receipt나 private 내용을 새 필드에 복제하지 않는다.
- STOP/KeyboardInterrupt를 삼키거나 예외를 교체하지 않는다. 추가 I/O/native query/sampler/child를 만들지 않는다.
- 성공 classifier는 반환0/정수형, pending·rejected FALSE, 기록 marker TRUE를 요구한다. failed/deferred/미정리 핸들은 수용하지 않는다.
- 원 CPU98x4/RAM/commit/600초/720읽기/두전체byte/Native identity/Job/cleanup/byte rates/acquisition14/global20/no idle burst를 유지한다. CPU 성능 개선 자체를 입증한 수정은 아니다.

## 검증

현재134 + following134 =268 실제 동작·거부 계약을 사전 및 정식 light에서 실행했다. 기존100개 계약을 유지하고 새34개로 STOP 바인딩, 이전200 결과의 재사용·실행횟수 분리, 입력 누락, 기록 순서/예외/동일guard1회/개인자료 비복제 등을 검증했다.

각 검사 전후268회/runner 전후2회는 기존 checkpoint를 사용했다. 원78/compact26/helper21/retained1486 및 이전104의200은 qualified 재사용이며 이번268에 더하지 않았다. 새 thread/sampler/sleep/검사 제외 없음.

- 사전268:100bound/fresh100/200read/8,488,992bytes, cleanupTRUE/STOP없음. comment 설명 수정 전 pin은 해당 preformal receipt에 보존했다.
- 정식 light268:100bound/fresh100/200read, 실제 제품/Native 실행 아님.
- 독립 light 재확인:101bound/fresh101/202read/8,561,386bytes, cleanupTRUE/STOP없음. 현재87 코드 pin과 light의 실제바인딩을 대조했다.
- formal 이후 새runtime/test 및 원P320/수용103/원실패는 불변이다.

소스37,079bytes SHA256 `b91bada47ceff9bd8861603f310642015bdf1e8befaa1a14782167f618fb31a1`.
test26,985bytes SHA256 `c90818a5d2790f1abf576b519eea09abd879ebf8248f477085ef15b8a421c84b`.

## actual104: source_frame_acquire에서1회 STOP

`python -B tools/p09/resume_recorded_parent_return_runtime.py --mode actual --run 3`.

현재268 계약 및 준비101bound/fresh101/202read/8,561,386bytes는 완료됐다. 이후 원CPU guard가 input acquisition에서 STOP_SUSTAINED_SYSTEM_CPU를 냈다.

- planned inputs1650/120,643,529bytes, directory308.
- Native194open/194close/잔여0, metadata194, close실패0/active readers0/streams0.
- acquisition194/1958 미완료, 원20rate 복원. Frame CLOSED/등록해제, byte boundaries=[]/held closing NULL.
- 원 acquire 코드는 directory를 먼저 확보한다. 194<308이고 source byte read0이므로 source 파일/제품에 진입하기 전 directory194를 열던 시점이다.
- 원 guard2423회/first error18.6445388초 <600, pacing sleep13.4259082초.
- early90 경고1회/8windows/4초 bounded 대기 뒤 원hard CPU STOP; guard를 완화하지 않았다.
- 부모 반환 adapter/Job/제품 이전에 종료됐다. body/sidecar가 존재하지 않는다. 새 반환 marker FALSE는 그 경로까지 도달하지 않았다는 의미다.
- 새 기록 순서의 실제 부모-return 경로 qualification은 NOT_RUN이다. 사전268 동작 계약 PASS를 실제 parent 경로 PASS로 바꾸지 않는다.

원 root `evidence/locked-r07/p323-case-104-run003.v1.json`,163,476bytes SHA256 `ec440376ecc9ee92c634a8f1ae716347e7778df2c7604576e21506f797b17c84`.
전후 rawpacket259,034bytes SHA256 `9775416dc0706a08e208adbd4c83512535e1532cf2ecda8aa65701f0e974e87c`.
바깥PowerShell exit0과 실제exit2를 구분한다. 같은 실패 세대를 재시도하지 않았다.

## STOP 원인 검토와 증거

원 observer99표본: systemmax100%, ownmax6.153846%, private47,616,000bytes/working set58,814,464bytes/freeRAMmin21.8608833927%.
last4 host100/own0/logical read증가0. 기존 원 raw CPU delta를 추가 검토했다. 마지막4개는 idle0/total80,000,000(100ns), ownProcessTimes증가0이며 kernel+user 합 및 ratio와 일치한다. 단순 표본 분모 오류나 검증 부모100%라고 해석할 근거가 없다. 이는 원 sampler의 관측이지 순간 범인 확정은 아니다.

별도PerfProc55.6173122초 창: before378/after371/비교365/drift2제외/종료9/새2. hostbusy22.965126%, MsMpEng평균8.1191/System2.99901/RadeonSoftware2.898926/maple-re0.946409%. 평균은 순간100%의단독원인·검증유발인과를 증명하지 않으며 counter는 원guard에 공급되지 않았다.

기존 **실행 전** snapshot에는 clippy-driver533752←cargo709616←cargo-clippy184992←cargo611440←python504664←maple-re658140 작업이 있었다. 해당 compilation branch는 실행 후 snapshot에서 사라졌다. 우리 실제검증은 before snapshot 뒤 시작했고 child 이전에 STOP했다. 따라서 이 branch를 이번 검증이 생성한 Cargo로 분류하지 않는다. 구간 중 종료되어 해당branch의 interval CPU는 알 수 없으며0으로 만들지 않는다. 다른 작업의 process/명령/설정 변경·종료는 하지 않았다. 자원 경합 후보이지 단독 root cause 확정이 아니다.

## 코드 재검토

이번 STOP 호출 경로: source_frame_acquire → OpenPacer.reserve → 원pressure/checkpoint → TimedInputLocks.check → 원resourceguard.

- directory ancestor visited-set의 기존 중복 순회 제거를 유지한다. input마다 처음 발견한 ancestor만 추가되며 ancestor307이다.
- Native open14/s/noidleburst, reserve 최대64회/최대0.05초 sleep/원checkpoint 유지. cleanup은 guard/pacing에 막히지 않는다.
- sampler는 lock으로 직렬화되어 기존 watcher만 사용한다. 원 raw counter 값과 ratio는 일치한다.
- bounded early90 대기 뒤 원guard가 종료시킨 상황이다. 추가 무한spin/중복sampler/불필요pathname reopen은 찾지 못했다.
- 디렉터리194를 과거 receipt pin으로 치환하거나 더 적은 scope/더 느슨한 CPU 기준으로 통과시키는 변경은 하지 않았다.

새 독립 STOP 검토는 root/rawpacket2개 live/finalfresh:2bound/fresh2/4read/845,020bytes/cleanupTRUE/STOP없음. 원 rawdelta1개 검토도 별도 fresh receipt로 보존했다. 제품 또는 Native 재시도0.

## 다음 경계

반환 기록 수정268 qualification은 유지하되 실제 Native/parent 경로는 미완료다. 원P323 STOP/194cleanup/동시 compilation endpoint 증거를 qualified accepted97에 바인딩한 다음 안전한 실행 경로가 필요하다. 같은 작업을 즉시 다시 돌리지 않는다. 지속적인 host 포화에서는 강제실행이나 보호 완화 대신 검토 가능한 코드·증거 작업을 진행한다. 외부 compilation을 종료하거나 OS/Defender/WSL 설정을 바꾸지 않는다.

r127 두 문서 전체를 `evidence/runtime-progress-r127/`에 byte-exact 복사했다. r128 prefix 이외 suffix를 보존하며 최종fresh 검증은 별도 receipt에서만 확정한다. 성공97개 본문 재실행/실패PASS승격 없음. P09 Gate 전 P10 진행하지 않는다.

