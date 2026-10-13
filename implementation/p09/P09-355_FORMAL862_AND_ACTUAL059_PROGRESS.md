# P09-355 현행862 자격·단일109 실제 경로 검토

2026-10-10. 목표 ACTIVE. 직전 P354는 코드 수정/AST/작은 검사로 진전한 턴이다.
이번 단계도 현행 정식 자격과 실제 경로의 새 증거를 얻은 진전이다. P09 Gate는 OPEN이다.

## 코드 수정 및 작은 검증

기존 `test_preserved106_queue_runtime.py`가 작은 pure 검사에도 과거 테스트 helper를
top-level에서 불러왔다. `test_admission_classified_queue_runtime` import를 최초 full
fixture 생성 시점으로 옮겼다. 원 builder/필요 fixture/테스트 독립성/전체 검사 범위는 유지한다.
기존 initialize/잘못된 projection 검사에 불필요한 import를 거부하는 검사를 추가했다.
검사 정의 수는 431 그대로이며 새 파일을 실행 입력에 추가하지 않았다.

처음 preimport 시도는 CPU100%로 target import 전에 DEFERRED, 실제 검사0이었다.
변경 후 새 작은 실행은 CPU13.25%, 가용 RAM23.637882%에서 시작해 정책2+fixture4=6 PASS.
과거 helper가 검사 전후 모두 `sys.modules`에 없고, full fixture/Native/제품을 만들지 않는
것을 확인했다. import 감소량이나 PC 프리즈 해소를 정량적으로 주장하지 않는다.

## 같은 프로세스의 독립 review → light → fresh

CPU8.45%, 가용 RAM23.748641%에서 원 preimport admission 후 시작했다. helper import만
공유하고 각 단계의 owner/reader/신선한 전체 preparation/자원 guard/정리는 독립적으로 유지한다.
단계 실패 시 뒤 단계를 실행하지 않는다. 재시도 loop는 없다.

| 단계 | 실제 결과 | 실제 계약 | 준비 fresh / 읽기 / bytes | host max / own max / private max |
|---|---|---:|---|---|
| stop-review056 | PASS_PRE_PRODUCT_STOP_REVIEW_NOT_GO | 0 | 224 / 451 / 49219123 | 24.24% / 1.893939% / 80969728 |
| light057 | PASS_NEXT_QUEUE_NOT_ACTUAL_OR_GATE | 862=431×2 | 225 / 453 / 49347455 | 59.09% / 6.626506% / 112586752 |
| light-review058 | PASS_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT | 0, exact862 재사용 | 226 / 455 / 49483723 | 28.08% / 1.571709% / 112181248 |

모두 preparation finished/감시 정리 true, selected109, 제품 child false다.
가용 RAM 최저는 순서대로23.267534%,18.298121%,19.887818%였다.
PTY73333은 exit0로 종료했다. 과거828을 현재862 PASS로 승격한 결과가 아니다.
현재 code2는 `evidence/p340-formal862-code/`에 동일 hash로 보존했다.

## 실제109 run059: 최적화 연결 확인, 제품 미시작 CPU STOP

CPU0.79%, 가용 RAM20.307391%에서 별도 실행을 시작했다. exact056/057/058과 현재 동일
code2 자격을 사용했다. 계약862/성공제품107·108 재실행0이다.

결과는 `FAILED_NOT_ACCEPTED / STOP_SUSTAINED_SYSTEM_CPU`, stage `owned_parent`다.
parent sidecar는 `DEFERRED_NOT_STARTED`, 실제 제품 child false, elapsed33.85초,
owned_tree_empty/cleanup true다. 제품109는 통과한 것으로 세지 않는다.

- 전체 입력1658 + ancestor308 =1966 모두 획득했다.
- 실제 before 부분에서 fresh held metadata247, 원 predicate741, pathname probe0이었다.
- actual adapter selected/restored true, reader root 복구 true, adapter inactive다.
- 원 handle1966/복제247 모두 close. 잔여 handle/복제/reader/stream/probe/close failure0.
- frame CLOSED, registered false, 완전한 byte boundary0. 전체 before/after PASS로 표시하지 않는다.
- host max100%, own max1.515152%, private max80445440bytes(76.72MiB), RAMfree min18.100582%.
- 마지막4 표본은 host100/parent CPU tick증가0. 마지막3 논리 read증가0이다.
- Native 획득 inspect1966건 합계0.063587초/max0.000447초.
  open-with-pacing1966건 합계140.653434초에는 원 대기/pacing이 포함된다.
- 원 빈 body placeholder0bytes/실패 sidecar/receipt를 그대로 보존했다. PTY62424 exit1로 종료했다.

현재 실제 경로에 최적화가 연결됐다는 증거는 얻었지만, PC 프리즈 해소나 Native 전체
경로의 성공·성능 개선을 입증한 것은 아니다. own CPU가 낮아도 간접적인 시스템 부하를
유발할 가능성을 배제하지 않는다. 이번 단계 특권 Defender 추적은 하지 않았다.

## STOP 뒤 코드 재검토

`HeldPathGuard.source`의 fresh held metadata, 원 `verify_stream`의 복제 stream metadata,
borrower의 단일 대여/offset reset/close, Frame/reader 복구 및 원 pacing/자원 callback을
따라 확인했다. 앞의 두 metadata 검사는 서로 다른 handle의 동일성을 증명하므로 합쳐
제거하지 않는다. 실제 byte stream은 원 held handle의 DuplicateHandle을 이용하며
pathname reopen0, 불필요한 descriptor 전 metadata query0이다.

이 구간에서 새 busy-spin/자동 retry/누수 결함은 특정하지 못했다. 통과처럼 보이기 위한
guard 제거, 필요 동일성 검사 삭제, 무근거 코드 변경은 하지 않고 현행862 자격을 보존했다.
같은 actual 전체 명령은 재실행하지 않았다.

## 정확한 pins

현재 runtime:152778bytes,
`9fcf1446bf38e14b67c05f10f25b693e6656a9864227d7d71a21ae9bc27b8473`.
현재 test:123113bytes,
`c01811db277830995f6fb911cd7f181800f17170cfdf0a8037938d1583c54819`.

056:64166bytes/`b6a55cbe91c82661f68ae75e24dcc4f8aa995130247c66f09e96c5d88160b4c8`.
057:68134bytes/`a64c0ba40d8c0f0225539d3775514c5edb3983d3c381ee796c6eca4406a51e0f`.
058:64018bytes/`61a00fcb8ffb378d8ae6977fe7ab6bf3185c427f33698954f3b253117a7df853`.
059:509270bytes/`c08b42a7f820e8cd214a502d0f3cff055e3c839f06d3a28a236c9b856b99eaad`.
059sidecar:36123bytes/`34ef1dfb932721e7c6e81481f44322e645980d4005166a380aa808ab35a48d9f`.

## 다음 경계와 미완료 상태

새059의 독립 STOP review는 아직 NOT_RUN이다. 재개 시 exact056 승인을 유지한 상태에서
059를 새 target으로 검토해야 한다. 성공한862를 불필요하게 다시 돌리지 않되, 코드가
바뀌면 기존 자격을 새 코드의 자격으로 쓰지 않는다. 안정성 및 구체적인 최적화 근거 없이
실제109를 맹목 반복하지 않는다. 접근 허용을 선행조건으로 추가하지 않는다.

수용102/249, 잔여147(일반141+corpus6), next109, 성공 body 마감 pending0,
whole재조정99, P09/A12/A13 OPEN, full249/signed16/whole1470 미완료,
문서 final-fresh NOT_RUN, P10 시작0, 목표 ACTIVE다. 특정 큐 수치는 P09 전체 잔여율이 아니다.

UAC/한글 허용/Git/빌드/Defender·OS·WSL 설정 변경/외부 process 종료/삭제·이동0.
