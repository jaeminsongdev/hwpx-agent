# P09 P215: 완료 원장을 소비하는 범용 잠금 runtime 계속 실행

2026-10-08. 목표 active. P09/A12/A13 OPEN, product=false. P10 새 구현 없음.

## 결과와 경계

P214 runtime13 원장을 소비하는 고정 진입점 `resume_generic_locked_runtime.py`를
구현했다. 사례마다 새 스크립트를 복제하거나 이전 성공 본문을 다시 실행하지 않는다.
같은 source로 case014/run001, case015/run002를 각각 단독 실행하고 원 strict
본문/frame 검사 및 정리까지 완료했다. 현재 runtime15/249, 잔여234(일반228+corpus6),
미closing후보0, 다음index16. 전체 성공 본문 중 whole 재조정 대기12(15-3).
기존 legacy whole 수용3/pending1은 별도 범위 그대로이며 원 STOP/FAILED 보존.
이는 고정 r07 EXE의 개별 runtime 진행 상태이고 P09 전체 완료율이 아니다.
compiled249=true/full249=false/signed16=false, whole1470·historical67 최신성 및 Gate 미승격.

## 수정·최적화와 검토

- 완료 원장을 strict 재검증하여 다음 미수용 일반 사례만 선택한다. light3은15,
  light4는16을 선택했고 이전 성공 본문은 재실행하지 않았다. corpus6은 수용하지 않는다.
- P213의 premature-PASS/error 모순을 반복하지 않도록 최종 성공을 후보로 보관한다.
  원 watcher 정리·resource 필드 채움·원 closing validator·큐 계산이 모두 끝난 뒤
  overall PASS를 기록한다. 후처리 예외, resource stop, 정리 실패는 FAIL이다.
- CPU 보호 중단 시 자동 재시도 금지. worker 요청 후 실패와 보호 중단은 다음
  실행의 원장 소비를 차단한다. 원 증거·통과 본문은 보존하고 중단 구간의 코드,
  CPU/RAM 표본·논리 읽기·Job/핸들 정리를 검토한 후 별도 개선/검증이 필요하다.
  검증 기준을 낮추거나 중단 receipt를 PASS로 바꾸지 않는다.
- own receipt 파일명/index/run 범위를 제한하며 body 경로가 일치하지 않으면 읽기 전
  거부한다. 다른 경로나 임의 test index로 진행을 바꿀 수 없다.
- 입력 잠금 코드 추가 검토: 조상 디렉터리 중복 순회 제거, READ handle 직렬 복제,
  seek(0), 원 stream identity 유지, 중복 metadata 조회 제거 경로를 재확인했다.
  원 입력 제외·두 전체 실제 byte 읽기 생략·검사 결과 캐시 재사용은 없다.
- 기존 affinity1/BelowNormal, Job CPU6.25%/RAM 비율 제한, 원 CPU·RAM·commit
  hard stop, 600초 input/IO deadline, 32open/s/바이트 pacing/backpressure를 유지한다.
  새 sampler thread, Git/Cargo/build/SQL/Hangul/접근허용/OS·보안 설정 변경 없음.

18개 지원 계약은 큐 연속 진행/불변성/기존 성공·임의index·corpus·pending 거부,
후처리 예외/CPU 중단/정리 실패의 FAIL 유지, 접근 전 경로 제한 등을 검사한다.
light2~4 및 두 actual에서18계약 PASS. 원 제품 계약246과 지원 계약18을 합쳐
제품 통과 수로 표시하지 않는다. 원 P213 실패 source/evidence는 수정하지 않았다.

## 실제 검증

| 항목 | case014/run001 | case015/run002 |
|---|---:|---:|
| 본문 | exact1 PASS/248 filtered/exit0 | exact1 PASS/248 filtered/exit0 |
| 전후 전체 byte 검사 | 각1488개/118737453bytes | 각1488개/118737453bytes |
| READ 잠금 / 복제 stream |1794 / 2976, 전부 close|1794 / 2976, 전부 close|
| frame / Job |COMMITTED / 잔여 프로세스0|COMMITTED / 잔여 프로세스0|
| 시스템 CPU 최고 |28.49%|68.15%|
| 제어 프로세스 CPU 최고(머신 분모) |1.70778%|1.340996%|
| 제어 private 메모리 최고 |35942400bytes(34.28MiB)|35737600bytes(34.08MiB)|
| RAM 여유 최저 |44.5863%|44.2254%|
| 제품 Job CPU 누적 / peak private |0.156초 /21.07MiB|0.141초 /20.34MiB|
| 준비 metadata fresh |28/28, finished=true|30/30, finished=true|
| 보호 / cleanup |stop=null / true|stop=null / true|

각 case는 원 전후 whole source 입력 읽기와 exact 제품 본문1개를 수행한다.
부모의 전체 elapsed194.54/197.85초는 source/Job 관측을 포함하며 제품 연산 CPU
0.156/0.141초와 다르다. light3에서 시스템 CPU84.19%를 관측했지만 own CPU 최고
1.160542%, stop=null이었다. foreign PID/물리 disk IO/Defender 원인 분석은 하지 않았다.
PC 프리즈 원인·해결은 미확정. 두 번 무중단으로 통과한 사실만 수용한다.

## 증거 pin

경로 기준 `implementation/p09/evidence/locked-r07/`.

| 파일 | bytes | SHA256 |
|---|---:|---|
|`p215-case-014-run001.v1.json`|2036363|`0adc30d144213c49b9aca37a878a8286e4bb4271bfcdd7daf31fd3ffe263c952`|
|`cases/p215-case-014-run001.json`|792014|`8beaf52d17fc1061cc43b400747993f1b3764014776ea666561f78f853c1b1da`|
|`p215-case-015-run002.v1.json`|2052380|`47282ac819b91c50a9c47a4171e8783610ddd682e078b2531e8d76bfcdf42ab7`|
|`cases/p215-case-015-run002.json`|805843|`52f6e875bda1c73ddc35498e8ba5cc67892f757e258b6c2b0d3ff77608113684`|

light1 이후 경로/보호 재시도 계약을 추가하기 전 source는
`evidence/p215-light01-preimage/`에 보존했다. r78 원 문서 bytes/SHA를 확인하여
`evidence/runtime-progress-r78/`에 복사한 뒤 같은 r79 prefix만 두 현행 문서 앞에
추가한다. 문서 동기화 검사는 원 anchor/두 actual receipt/원 strict validator/
next16 light/18계약/current controller pins/모든 bound input 최종 fresh hash/
r78 exact byte suffix를 재검증하되 제품·전체 source frame은 다시 실행하지 않는다.

다음은 같은 진입점의 index16 단독 실행이다. CPU 보호가 다시 걸리면 그대로
증거를 남겨 중단 구간을 검토·최적화한다. 통과 사례를 다시 돌려 증거를 만들지 않는다.
