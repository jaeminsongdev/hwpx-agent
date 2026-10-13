# P09-125 — 단일-case 이어 실행의 준비 비용 절감

## 범위와 구현

P124 checkpoint/source/runtime 및 사용자 소유 변경/원본/실패 증거를 유지했다.
새 `run_resumable_formula_batch.py`는 이전 전체 보존 audit를 소규모 batch의 시작과 끝에
호출하며 각 case는 수정하지 않은 원래 resource runner로 실행한다.
매 case의 original Rust14/binary pin/terminal1PASS/227filtered/name/CPU1/BelowNormal/worker1,
CPU85%3연속/RAM4GiB/test RAM2GiB/2초 샘플/600초 상한 검사는 그대로다.
완료된 receipt는 매 case 이후 재검증하며 중단 또는 실패 시 즉시 batch를 끝내고 재시도하지 않는다.
batch 최대30개이며 이번 실행은25개, 새 case 시작 budget120초를 사용했다.
120초는 새 시작 금지 경계다. 이미 시작한 case를 무조건120초에 죽이는 hard deadline은 아니다.
단일 invocation의 원래600초 process deadline은 별도로 유지한다.

## 실제 실행 결과

P124 방식으로 cases3~12를 순차 실행: 추가10개 terminal PASS, 누적12개.
새 batch 첫 실행 session30440: cases13~37 모두25개 PASS, batch 기록91.82초.
두 번째 session10831: cases38~48 모두11개 PASS,128.95초 후 시작 budget 경계에서 정상 종료.
case48은63.68초이며 종료 후 case49를 시작하지 않았다. resource failure/auto retry 없음.
현재 같은 frozen binary의200 actual_import 중48개를 단일-case 실행으로 수용,152개 남았다.
앞선 interrupted actual_import200의 marker50은 최종 suite PASS로 수용하지 않는다.
P123 documents20/root8 PASS는 별도 유지; 전체228 single-process 통합 및 P09 Gate는 미수용이다.

실제 보호 거부 case47은21.02초, current derivative 만료/새 policy 거부 case48은63.68초 PASS다.
모든 완료 case는 source14 exact 및 동일 executable10688512 bytes/SHA04fefdf7…이다.
첫 batch의 양수 test RAM 최대21.82MiB, 최저 여유 RAM16094MiB였다.
두 번째 batch에는39/40/44/46/47/48의 양수 test RAM 관측이 있으며 source 검사를 유지했다.
이것은 native/Hangul/실제 issuer 운영 신뢰/SQL/원자적 publication acceptance가 아니다.

## 관측 표시 보완 및 검증

원래 resource sampler는 baseline 또는 이미 종료된 child에 대해 RAM/CPU0을 기록한다.
case21은 sample2개지만 둘 다 child RAM0/CPU0이었다. 최초 batch 요약에서 sampled=true/0MiB로
보였던 표시를 확인했고, 원래 receipt/runner를 바꾸지 않고 새 요약 함수에서 양수 WS 관측만
RAM sampled로 인정하도록 보완했다. 양수 관측이 없으면 max는 null/unobserved다.
최초 실행 driver 전체 소스는 `target/p09-121-resource-optimized/p125-batch-runner.initial-source.py.txt`에
별도 보존했다. 최초 batch 결과가 수정 후 driver로 실행됐다고 주장하지 않는다.
원래 runner나 stop threshold는 바뀌지 않았으며 해당 correction은 관측 표시뿐이다.

새 scheduler8 unit 및 실제case19/21 metric 요약2 unit =10 PASS.
기존 resume14 unit/P124 전체 checkpoint audit도 다시 PASS했다.
모두 compile-free 검증이며 Python unit/mock는 실제 runtime 성공과 구분한다.
같은 workload의 정량 A/B benchmark는 아니므로 성능 배수/CPU 감소율은 주장하지 않는다.
매 case마다 반복하던 전체 보존 audit를 batch 시작/끝으로 옮겨 준비 비용을 줄인 구조적 변경이다.

## 현재 경계 및 다음 작업

새 source는 driver/test/report3개, 이전 source1125/현재1128/inherited raw pins2385다.
P125 checkpoint는 신규 runtime46개/cases3~48, 원래P124 checkpoint 및 initial source archive를 pin한다.
이전 checkpoint는 과거 snapshot의2개 수용 상태로 보존하며 현재48개는 새 checkpoint에 기록한다.
다음은 case49부터 같은200-case 회귀를 이어서 실행한다. 이152개는 P09 전체 잔여 항목 수가 아니다.
그 이후 전체 통합 및 미완료 comment mutation/lowering 등 원래 제품 요구사항은 여전히 남는다.
한글/Hwp/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없음.
PLANS 삭제 유지/P09 Gate OPEN/P10 새 구현 없음/목표 active다.
