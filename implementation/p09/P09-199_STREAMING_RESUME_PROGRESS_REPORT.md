# P09-199 — 큐 계산 메모리 상한과 case006·007 실제 검증

2026-10-08. 목표active/P09·A12·A13 OPEN/product=false/P10 새 구현 없음.
compiled249=true/full249=false/signed16=false. 프리즈 원인·해결은 미확정이다.

## 현재 큐

runtime 수용7/249, 잔여242(일반236+corpus6), 미closing후보0, 다음index8이다.
이것은 현재 r07 회귀검증 큐이며 P09 전체 작업 수/전체 완료율이 아니다.
원 whole 수용3은 그대로며 whole미확인성공4(case004~007)는 별도 전체확인 대상이다.
개별 runtime 통과를 whole/Gate로 승격하지 않는다. corpus6/full249/signed16 및
실제 SQL/한글/native 제품 경로는 미완료 상태를 유지한다.

## 구현과 검증 보존

stream_runtime_resume_progress.py와 신규10 계약을 추가했다. 원P198의 큐 계산은
과거 성공 case의 samples/source list 전체를 passed map에 동시에 남겼다.
case 수가 증가하면 메모리 보관량도 늘어나는 구조라 해당 경로를 교체했다.
새 구현은 각 case를 검증한 뒤 public name/pin/controller key집합만 남기고 원payload를
해제한다. closing 검사에서는 원 case의 모든 byte를 다시 읽고 같은 pin 및 동일한
원 P196 case_scope/validate로 검증한다. source 읽기/실패/terminal/cleanup 검사를 줄이지 않는다.
성공body 재실행, 통과조건 변경, metadata를 PASS로 투영하는 동작은 없다.

기존8-controller case도 현재 pin이 같은 경우 원본 그대로 재사용한다.
새 실제 실행은 dispatcher/source-test2개를 추가한10-controller generation이며
원runtime1403＋scheduler2＋controller10=1415를 실제 body 전후에 모두 읽는다.
원P198/P196 코드는 수정하지 않았다. 기존202 계약은 원8-controller 역할로 검증하고
새10 계약을 더해212 PASS다. case fixture의 read count/bytes 변경을 검증 실패조건으로
사용한 synthetic 테스트는 실제 receipt를 변경하지 않는다.

전체case payload 동시 보관을 없앤 것은 구조적 메모리 개선이며, 아직249개 누적 상태의
실측 메모리 benchmark나 PC 프리즈 해결 증거는 아니다. latest plan의 parent private
최대52035584bytes와 가용RAMmin48.785916%를 기록했다. 별도 stress 부하는 만들지 않았다.

CPU/RAM/commit 비율 보호, one-affinity/BelowNormal, owned Job 상한/후손정리,
원1200초body/600초reader/32768stream cap/정확한1PASS＋248filtered를 유지한다.
원과 새 runner 모두 한 invocation에 body1개뿐이다. stop 이후 retry/next는 없다.
Git/Cargo/SQL/Hangul/접근허용/OS·Defender·WSL 설정 변경·삭제·이동은 하지 않았다.

## 실제 두 사례

case006은 원P198 `--mode actual --run 2`로 수행했다. 내용이 같은 result라도 head가
진행되면 cached source/range verify와 새 range import를 거부하는 실제 제품 구현 경로를 확인했다.
case007은 새 dispatcher `--mode actual --run 3`로 수행했다. 문서/branch/project/subject/
tenant 각각의 변경5종에서 cached range 검증과 새 import가 Binding 오류로 거부되는지 확인했다.
두 사례 모두 fixture-backed Rust 제품 경로이며 실제 SQL 서버/한글 GUI 확인은 아니다.
원 Rust/source/fixture/r07 EXE를 변경하거나 기존1~5번 성공body를 재실행하지 않았다.

| 사례 | body 입력 수·각 pass bytes | body 시간 | Job CPU / peakprivate | hostCPUmax / availableRAMmin |
|---|---|---:|---|---|
| case006 | 1413 / 117910771 | 136.84초 | 0.281초 / 29.02MiB | 82.99% / 40.003948% |
| case007 | 1415 / 117921706 | 139.14초 | 0.219초 / 28.9MiB | 40.42% / 48.460270% |

body는 둘 다 exact1PASS/248filtered/exit0/stop=null/cleanup·owned_tree_empty=true,
실제 모든 입력2회fresh였다. 위 body 시간은 source 확인을 포함하므로 순수 테스트 시간이 아니다.
CPU귀속관측도 error=null이며 접근 불가 프로세스의 사용량이나 프리즈 원인은 특정하지 않는다.

case006 closing은64.8775초/bound1414=fresh1414/read237788509bytes,
hostCPUmax33.72%/availableRAMmin49.067768%다.
case007 closing은65.3019초/bound1416=fresh1416/read237883832bytes,
hostCPUmax35.43%/availableRAMmin48.851864%다.
둘 다 원 runtime PASS 스키마로 실제 검증하고 exit0/stop=null/cleanup=true/IO.finished=true다.
과거EXE67 byte 확인을 다시 하지 않았으나 현재 whole/Gate 미검증 의무는 유지한다.

plan02는 새 streaming 큐로 수용7/잔여242/후보0/next8/whole미확인성공4를 재계산했다.
verify_streamed_runtime_progress_docs.py는 앞으로도 동일한 큐 계산으로 문서 수치,
검증된212 계약의 controller 동일성, closing pins, 동일prefix 및 이전본문 byte 보존을 확인한다.
문서 동기화에서 이미 통과한 제품 테스트/계약을 재실행하지 않는다.

## 정확한 증거핀

아래 경로는 implementation/p09/evidence/runtime-r07/ 기준이다.

| 파일 | bytes | SHA256 |
|---|---:|---|
| cases/p190-case-006-attempt-001.json | 946983 | a1e7525aeac1567bcd15ac28045a2f71f71c3e9411d280dc6c34786994764067 |
| p198-case-006-attempt-001-close-02.v1.json | 1132322 | 08d60ca30bb76ed5c88772c5b61d1551d0a27ceeedb4c755c8d2006e1a98a9de |
| cases/p190-case-007-attempt-001.json | 978242 | f80809b7a742d85496fb570837a2e0f8a97650e71d6e049aaa704a5358828c42 |
| p198-case-007-attempt-001-close-03.v1.json | 1137890 | d786ce0b729dd273f776870531de791f0a1493daf9f22a7b1f3b8d9b062fa8fc |
| p198-runtime-resume-light-run03.v1.json | 61712 | cb91f9ddf68299e67cece4f40a40711c1d73a645489e86a23988ac123faaeb4d |
| p198-runtime-resume-plan-run02.v1.json | 70260 | 8f5f319ea980828af3144c6a011993c960c7a40f355752d50d881b68d4b3b44f |

원수용4의 독립closing pin은1160181bytes /
c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd이고,
case005 closing pin은1135501bytes /
f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569다.
해당 원본은 P09-196/P09-198 보고서 경로에서 그대로 보존하며 새로운 단계의 실행으로 취급하지 않는다.

CURRENT_STATE/P09-149 r67 전체는 source-archive/runtime-progress-r67/에 보존했다.
같은 r68 prefix를 추가하며 과거본문은 그대로 유지한다. 이 보고서는 실제 closing 이후에
작성했으며 그 실행의 입력이었다고 주장하지 않는다. 다음 exact task는
`python -B tools/p09/stream_runtime_resume_progress.py --mode actual --run 4`로 next8만 실행하는 것이다.
