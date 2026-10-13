# P09-196/197 — 현재 실행 입력 closing과 제한된 CPU 관측

2026-10-08. 목표active / P09·A12·A13 OPEN / product=false / P10 새 구현 없음.
compiled249=true/full249=false/signed16=false. CPU 포화·PC 프리즈 원인 및 해결은 미확정이다.

## 범위와 완료 판정

P09 로드맵과 제품/Release Gate의 실제 검증 요구를 유지한다. 새로운 판정은 단일
case의 **실제 runtime 입력 확인**에 한정한다. 원 whole1470 closing/Gate를 대체하지 않는다.
원 CASE_PASS 및 whole CLOSING_PASS 스키마/검증기/실패 receipt를 변경하지 않았다.

현재 runtime 기준 수용4/249, 잔여245(일반239+corpus6), runtime 미closing 후보0이다.
기존 whole 기준 수용3/249, 잔여246, whole closing 대기후보1(case004)은 그대로다.
245는 실제 미실행 테스트 수이기도 하며 P09 전체 작업 수/전체 완료율이 아니다.
다음 미실행 index5이나 **기존 runner는 여전히 whole 후보 때문에 시작을 거부한다**.
다음 구현은 분리된 runtime 판정을 사용하는 exact-one scheduler 연결이다. 기존 거부를
무시하는 fake whole PASS/alias는 만들지 않는다. case001~004 성공 body는 재실행하지 않는다.

## 구현과 안전 경계

- runtime_source_closing_r07.py 및 14개 계약검사: 현재 EXE와 모든 non-EXE 원 입력,
  scheduler 입력 및 새 closing controller를 모두 fresh byte로 확인한다.
- 새 스키마 `hwpx-agent.p09-r07-runtime-source-closing/v1`, 실제 PASS 이름
  `PASS_EXACT_R07_RUNTIME_SOURCE_CLOSING_NOT_WHOLE_OR_GATE`를 사용한다.
- 역사적 EXE67개는 과거 sealed whole anchor로만 참조한다. 현재 상태가 fresh라고
  주장하지 않으며 historical whole/Gate reconciliation 의무를 계속 남긴다.
- 기존 one-affinity/BelowNormal, .5초 표본, CPU98%4회, RAM/commit 비율 보호,
  600초 reader 제한, 실제 byte 읽기, source/EXE 불일치 거부를 유지한다.
- 신규 입력의 추가로 원 baseline identity1470을 재작성하지 않는다.
- 실패/성공 기존 receipt와 사용자 source를 보존한다. 삭제·Git·Cargo·SQL·한글·
  접근허용·OS/Defender/WSL 설정 변경은 이번 단계에서 실행하지 않았다.

## CPU 관측 구현

process_cpu_attribution.py와 10개 계약검사를 추가했다.
run_attributed_runtime_closing.py로 원 P196 body에 연결했다. controller 세 파일을
원 reader 입력으로 bind하고 마지막 fresh hash에서도 읽는다. 원 module의 글로벌
클래스를 변형하지 않도록 별도 observer namespace를 사용한다.

원 CPU/RAM/own-process 측정 및 보호 판정은 그대로다. 별도 관측은 1초 이상 간격,
process-only Toolhelp snapshot, 최대1024 entries, snapshot elapsed0.25초 제한 확인,
최대600 intervals/top8 closed groups, QUERY_LIMITED_INFORMATION(0x1000)만 사용한다.
새 sampler thread/권한 상승/보호된 프로세스 재시도/다른 프로세스 변경은 없다.
명령줄·전체 경로·환경·파일 내용·모듈/스레드 목록은 조회하지 않는다.
허용 목록 밖 이름은 즉시 OTHER로 바꾼다. 숫자 CPU counter와 허용된 이름별 개수만 저장한다.
PID＋생성 시각으로 재사용을 제외하며 접근 거부·종료·새로 생성된 프로세스를0으로
가정하지 않는다. 보호된 프로세스, 짧은 프로세스, kernel 작업은 누락될 수 있다.
snapshot은 원자적 표본이 아니므로 모든 CPU 귀속이나 프리즈 원인 입증이 아니다.

기초 관측은 stress 재현 없이5.0702초, 4 intervals PASS였다. hostCPUmax22.9%,
ownCPUmax0.191939%, availableRAMmin37.376071%, scan 최대9.730ms였다.
조회 불가 최대158개라 Defender의 CPU 점유를 배제하거나 과거 원인을 특정하지 않는다.
초기 light-run01 뒤 checkpoint_io 연결을 보완했고 수정 전 source/test 전체를
source-archive/p09-197-pre-checkpoint-repair/에 보존했다.

## case004 실제 runtime closing — PASS, whole/Gate 아님

실행 명령:

```powershell
python -B tools/p09/run_attributed_runtime_closing.py --mode close --run 1 --index 4 --attempt 1
```

case004 성공 body를 다시 실행하지 않았다. 현재 runtime1405개 입력과 closing/관측
controller/실제 case receipt/metadata를 bind했다. 원 historical EXE67 byte는 읽지 않았다.
별도 새 receipt에 실제 runtime 전후 확인을 남겼고 이전 whole 실패는 그대로 보존했다.

실행핸들exit0/state=PASS_EXACT_R07_RUNTIME_SOURCE_CLOSING_NOT_WHOLE_OR_GATE,
wall70.5803초, stop=null/cleanup=true/IO.finished=true, bound1420=fresh1420,
read2861/253734505bytes. 계약154＋관측10＋runtime14＋CPU귀속10=188 PASS.
hostCPUmax27.65%, ownCPU(machine)max4.127199%, ownprivate max48295936bytes,
availableRAMmin37.06350661%. CPU귀속67 intervals/error=null/scan 최대11.687ms.
이번 구간이 정상 종료됐다는 증거이며 앞으로의 프리즈 해결을 입증하지는 않는다.

light02와 plan01도 같은 controller에 대한 guarded fresh metadata 확인을 완료했다.
plan01에서 실제 runtime 수용4/잔여245/미closing후보0/next5를 다시 계산했다.
원 whole 수용3은 변하지 않았다. 새 product test/EXE child는 이번에 시작하지 않았다.

## 정확한 증거핀

경로는 implementation/p09/evidence/ 기준이다.

| 파일 | bytes | SHA256 |
|---|---:|---|
| runtime-r07/p196-case-004-attempt-001-light-02.v1.json | 44397 | ddbf864d61054a1df58a41dce2ee928af4a8456cc0262a7b74d7e0426949d586 |
| runtime-r07/p196-case-004-attempt-001-close-01.v1.json | 1160181 | c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd |
| runtime-r07/p196-case-004-attempt-001-plan-01.v1.json | 48223 | d1a5bdf9f0bf1ef46dfab08cc1a874726d5784bdfb949ad6fd01b45f51a85020 |
| p09-197-process-cpu-baseline-run01.v1.json | 24219 | 2b7e6a6b9ce9f431a44279b42aa3e1d9240b64fefef96a16aa5ada45fb599ca2 |

CURRENT_STATE/P09-149의 r65 전체 preimage는
source-archive/p09-197-pre-runtime-progress/에 보존했다. r66을 같은 prefix로 추가한다.
이 문서는 실제 closing 이후 작성했으며 closing의 입력이었다고 주장하지 않는다.

공식 API 근거: [Toolhelp process snapshot](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot),
[process entry](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/ns-tlhelp32-processentry32w),
[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes).
