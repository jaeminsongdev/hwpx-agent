# P09-309~310 잠금 STOP 후 원인 분리 관측 개선

현재 런타임 수용 **95/249**, 잔여154(일반148+corpus6), 다음102.
P09/A12/A13 OPEN, 목표 ACTIVE. 이번 작업은 CPU 원인 분리 지원이며 제품/Native 전체 검증 통과나 프리즈 해결이 아니다.

## 직전 단계와 이번 선택

P307 실제102는 준비86/fresh86을 완료한 뒤 source_frame_acquire에서 CPU98x4 STOP.
276 Native 핸들 모두 닫힘/잔여0, body/Job 시작 전, 원 실패 보존.
P308 typed review 및 r122 문서 증거를 현재 pin으로 검증했다.
직전 목표 턴은 내부 보호 연결/중복 읽기30 제거/실제 중단 단계 변경 및 정리 증거를 확보한 **progress**였다.

원 source 잠금 callback·rate14/20·bounded sleep·ancestor walk·GetSystemTimes 계산을 다시 확인했다.
실제 own CPU가 낮다는 이유만으로 파일 접근이 다른 시스템 작업을 간접 유발했을 가능성을 제외하지 않는다.
코드 결함이 특정되지 않은 상태에서 보호 기준을 낮추거나 같은 실패 세대를 다시 실행하지 않았다.
따라서 이번 다음 조치는 **Native 작업이 없는 대기 관측과, 기존 조회에서 누락됐던 프로세스까지 볼 수 있는 제한된 성능 카운터 경로**다.

## 원래 자원 관측기만 사용한 짧은 대기

P309 run01은 보호 Context의 허용되지 않은 phase 이름 때문에 `P193_CLOSED_PHASE`로 실패.
6개 입력/12 read/213692bytes/fresh6, 표본2 및 정리 확인. 16회 대기 루프는 시작하지 않았다.
원 실패를 보존했고 PASS로 바꾸지 않았다. 원 Context 자체는 수정하지 않았다.

run02는 기존 허용 `admission` phase에서 16개 원래 .5초 sleep/checkpoint를 실행(관측용 대기이며 새 제품 admission 아님).
Native 파일 잠금/바이트 검사/제품/Cargo/SQL/Hangul 실행 없음. 원 reader/CPU·RAM·시간 보호/기존 sampler 그대로, 새 감시 스레드 없음.

- 전체 표본18, system CPU 최고13.47%, own CPU 최고0.110375%.
- private27123712bytes/working set37953536bytes, free RAM 최소24.952972%.
- 마지막4 own CPU0/logical read delta0, system8.32/11.32/10.22/8.09%.
- cleanup TRUE / resource STOP 없음.
- 대기 기간에는 포화가 재현되지 않았다. Native 중단과 동시 관측이 아니므로 원인/해결 증거는 아니다.

PowerShell Get-Process 전후 창10.917380초는 접근 가능한 same PID/birth204개만 계산했고 Git2개 CPU증가0.
종료/새로 생성/접근불가 프로세스는 제외했다. 제외를 사용량0으로 취급하지 않는다.
이 방식에서는 Defender 값이 빠졌으므로 기존 자료만으로 Defender 부하를 배제할 수 없었다.

## 새 제한된 성능 카운터 경로

새 파일:
- `tools/p09/read_process_cpu_counter_snapshot.ps1`: 읽기 전용 PerfProc snapshot 1회 함수. 필드9개, operation timeout5초, projected rows4096/JSON4MiB 상한, 명령줄/이미지 경로/계정/비밀정보 조회 없음.
- `tools/p09/process_cpu_counter_window.py`: 전후 두 raw snapshot 차이를 계산하는 순수 함수.
- `tools/p09/tests/test_process_cpu_counter_window.py`: 계산/거부 조건24개.

이 필드는 raw 누적 CPU100ns 카운터이며 이름이 PercentProcessorTime이라고 이미 CPU%인 것이 아니다.
Timestamp_Sys100NS 차이와 논리 CPU16으로 나눠 machine CPU%를 계산한다.
PID/instance/creating PID/원 raw elapsed token이 다르면 재사용·이름변경 위험으로 제외하고 집계에 남긴다.
raw elapsed token을 UTC/경과초로 해석하지 않는다. uint64은 십진 문자열로 보존해 JS 부동소수점 손실을 막는다.
카운터 reset/진행하지 않는 창/잘못된 frequency/범위/키/경로/중복 PID를 거부하며 값을 조용히0 또는100으로 clamp하지 않는다.
PID parent 값만으로 현재 실행 중인 실제 부모를 확정하지 않는다.

공식 정의 근거: [Microsoft Win32_PerfRawData_PerfProc_Process](https://learn.microsoft.com/en-us/previous-versions/aa394323(v=vs.85)).
이 클래스의 raw CPU 틱/타임스탬프 의미와 PID lifetime 제한을 참고했다.
실제 현재 PC에서 사용할 수 있는지는 아래 실제 조회로 별도 확인했다. 단일 프로세서 그룹(≤64) 범위이며 그 밖의 PC에서는 거부한다.

## 검증 결과

- PowerShell parser 오류0.
- 원 보호 owner 아래 합성 단위·거부 검사24 PASS, 새 child/thread 금지; 입력 code3/fresh3 재검증 및 종료 확인.
- 실제 전후 **PerfProc 조회2회** PASS: 각365행, process363개 동일 token 비교, drift/새PID/종료PID0.
- 원 raw packet을 파일에 보존했고 화면에 전체 목록/로그를 출력하지 않았다.
- 실제 카운터 창3.149079초, idle96.010221%, derived host busy3.989779%; total including idle99.638514% (타이밍/카운터 양자화가 있어 host busy의 다른 창·피크와 혼동하지 않음).
- 그 대기 창에서 **MsMpEng0.062022%, Git2개0%**. 제품/Native 중단과 동시 창은 아니므로 Defender 원인 배제/확정 불가.
- collector 측 pwsh1.333475%, WmiPrvSE0.496177% 등이 포함된다. 진단 자체 부하도 측정 대상이며 무부하라고 주장하지 않는다.
- runtime의 기존 CPU sampler/STOP 판단에 이 값을 공급하거나 덮어쓰지 않았다. 연속 polling/새 watcher thread 없음.
- 이 관측 경로는 아직 다음 full Native/runtime 실행과 결합하지 않았다.

## immutable 증거

| 증거 | bytes | SHA256 |
|---|---:|---|
| `locked-r07/p309-post-stop-idle-observation-run01.v1.json` (FAIL 보존) |15070|`443a7961f625bddbbd8e6e08d49d654ef78355da34cd60a954abf8f57a02e70a`|
| `locked-r07/p309-post-stop-idle-observation-run02.v1.json` (idle 지원PASS) |34461|`83b17294df61963c79be80b188849133e953a14b5e3233089a5afeee02c3dcfd`|
| `locked-r07/p310-counter24-qualification-run01.v1.json` (24계약 지원PASS) |7990|`ab7c78a874de38595b936bda926815a78b102f3bc2ecd4e779a36d9e7b25e06d`|
| `locked-r07/p310-two-real-perfproc-queries-run02.v1.json` (two-query 지원PASS) |285517|`432c9b510a82ea79cc0c66367e6a27fc84d5b9e2a4a21d9e44022f566309e5ad`|
| `process_cpu_counter_window.py` |5271|`a30f807bce406d98b5ebc6a73b9819fd6dc3ce2b2801efb3164b92260ec1502b`|
| `tests/test_process_cpu_counter_window.py` |4001|`8e63f4479615a0eddc365c89b1d55ff7b39e02542257cdb7025c5054a87ae628`|
| `read_process_cpu_counter_snapshot.ps1` |2410|`1821224c3937c90041ba304c627aa80b11f8cf5351b3be96b452bd761dc82b3c`|

증거 폴더는 `implementation/p09/evidence/`, code는 `tools/p09/`.
현재 기존 code72+새진단3=75 pin을 별도 metadata로 바인딩한다.
last Native-covered code는62이며 나머지13이 현재 Native 전체 source로 통과했다고 주장하지 않는다.

## 다음 경계

원P307 STOP/정리/P309 대기/P310 두 조회의 qualified code·pin을 바인딩한 **새 실행 세대**에서 미수용102를 이어갈 준비가 됐다.
전후 성능 카운터는 제품 fullsource 증거와 분리된 부하 상관관계 지원으로만 기록해야 한다.
관련 새 code·test·collector도 full Native source 범위에 추가하고 원 두 전체 byte/identity/CPU98x4/RAM/600·720/Job/cleanup을 유지해야 한다.
다시 STOP이면 exact phase·code·정리·동시성 한계·counter window를 검토한 뒤 개선 가능한 부분만 수정한다. 근거 없는 rate 저하/guard완화/같은failed generation blindretry 금지.

runtime95/249·잔여154·다음102·whole재조정92·source마감미완료후보0 유지.
P09/A12/A13 OPEN; whole1470/historical67/full249/signed16/product완료/CPU원인/PC프리즈해결 미확정.
접근허용/한글/빌드/Git/OS·Defender·WSL 설정 변경, 프로세스 종료, 삭제·이동은 하지 않았다.
