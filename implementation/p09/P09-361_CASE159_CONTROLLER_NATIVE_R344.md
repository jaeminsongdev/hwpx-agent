# P09 case159 controller와 실제 Native 제품 실행

159번의 controller와 전체 사전 검증을 연결한 뒤 단일 제품 실행이 통과했다. 입력 frame이 COMMITTED로 종료되고 두 실제 전체 byte 경계와 원래 cleanup을 완료했다. 독립 승인은 아직 수행하지 않았으므로 공식 수치는 152/249, 잔여 개별 사례 97, 다음 승인 대상 159로 유지한다. P09/A12/A13 Gate는 OPEN이며 P10 새 구현은 없다.

## Controller와 import 한도

V26은 원래 engine·worker·단일 physical adapter와 20쌍 Binding, Native timing, CPU/RAM 보호, Native 600초 및 product capture 15초 조건을 연결했다. r746의 원래 검사 14개가 모두 통과했다.

첫 전체 preflight034는 helper import가 원래 64개 한도를 넘어서 제품·Native 실행 전에 실패했다. 한도를 올리지 않고 새 V27에서 helper/controller 10개와 원래 test source를 핀 검증한 private namespace로 연결했다. 모든 non-import AST와 함수·초기화 코드를 유지하고 모든 원본 파일을 입력 범위에 남겼다. 실제 module을 import한 뒤 숨기거나 sys.modules를 제거·수정하지 않는다.

새 preflight 목적지와 해당 검사 기대 filename만 034에서 035로 연결한다. 역변환으로 전체 원래 code가 같음을 확인하며 검사 14개를 삭제하거나 완화하지 않았다. 실패 controller V26, CODE r746, DATA034, preflight034는 그대로 보존한다.

## 검증 기록

| 기록 | 결과 | 자원과 경계 |
| --- | --- | --- |
| r746 controller CODE14 | 14/14, fresh31/final31 | CPU 최대13.47%, 최소 가용RAM58.29078%, cleanup true, 제품·Native 실행0 |
| preflight034 | helper64 한도 초과로 FAIL, 193.43873초 | CPU25.65%, 가용RAM58.54833%, cleanup true, 제품·Native 실행0 |
| r748 namespace CODE14 | 14/14, fresh39/final39 | CPU23.54%, 가용RAM57.61120%, cleanup true, 제품·Native 실행0 |
| preflight035 | 전체 PASS, 329.36622초 | Rust787/import64, fresh1037/final1037, read2197/464653513bytes, CPU48.24%, 가용RAM53.51210%, cleanup true |
| actual159 run001 | Native·제품 candidate PASS, 715.68초 | 제품1 PASS/failed0/ignored0/filtered248, 전체CPU47.68%, 최소 가용RAM57.02411%, 소유 process tree empty 및 cleanup true |

preflight035의 raw 입력은 2727개/300924814bytes이다. 명시적인 무손실 표현을 적용한 physical 모델은 입력2707개/251718262bytes, semantic286207680bytes, directories372개이고 전체 비용은 597.002024초다. a5a1e46으로 controller·DATA·실패/성공 사전 검증을 체크포인트한 뒤 실제159를 한 번만 실행했다.

## 실제 frame과 시간 조건

실제 runtime root는 implementation/p09/evidence/p09-361-case159-current-runtime-run001.v1.json이며 4580676bytes, SHA256 090e2e069852a45d2db306f9968c2ca997962222e3bc622c7c10c7dee2d830d2이다.

- Frame COMMITTED, 실제 전체 byte 경계2개, physical 입력2708개/252002317bytes. 성공 preflight035도 actual Native 범위에 추가한 뒤 전체 비용을 다시 계산했다.
- handles3080개를 열고 모두 닫았으며 remaining0이다. Native before_release512.663800초로 기존 600초 제한 안이다.
- 실제 GO1회/capture1회, GO부터 complete capture까지3.461506초로 기존 15초 제한 안이다.
- 40개 decode가 합계0.613506초로 두 경계가 공유하는 5초 제한 안이다. 실제 전체 비용 모델은597.344348초이며 완료 보장이 아니라 실행 전 비용 검사다.
- reserve/checkpoint 총220.070431초, 순수 CreateFileW 총0.608411초를 각각3080회 집계했다. accounting 불완전 상태는 false이며 경로·handle·오류 값이나 per-input trace를 남기지 않는다.
- parent 최대 CPU6.31517%, private70.13281MiB. 전체 시스템 CPU 수치는 검증기 단독 사용률이 아니며 과거 PC 프리즈 원인 해결 증거가 아니다.

## 승인과 보존 범위

이 root는 PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE이다. 기존 authority152/성공158과 원본·실패 증거, P08/P17/공유 Rust 사용자 변경을 보존했다. 한글·접근 허용·UAC 요청, Defender/WSL/OS 설정 변경, 외부 프로세스 종료, 원본 삭제·이동, 원격 push는 없다.

다음 작업은 실제159의 별도 전체 read-only prepare/oracle과 독립 승인이다. 그 승인이 생성·검증된 뒤에만 공식 수치를153/249로 전진한다. 제품이 통과한159를 다시 실행하지 않는다. full249-current와 signed16, 전체 P09 Gate는 별도 완료 조건이다.

근거는 implementation/p09/evidence 아래 CODE r746/r748, DATA034/035, preflight034/035 및 actual159 run001이다.
