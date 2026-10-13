# P09 r342: case159 공통 입력 그래프와 strict window 연결

## 공식 상태와 완료 경계

- 공식 승인: 152/249, 잔여 97, 다음 실제 사례 159, current-generation 승인 47.
- P09/A12/A13 Gate OPEN. full249-current 및 signed16 완료 아님. P10 새 구현 없음.
- 목표 ACTIVE. 성공한 case158은 재실행하지 않았고 원장 승인 수는 늘리지 않았다.
- 이번 결과는 연결·manifest admission·검사 코드 검증이다. 실제 case159 Native frame, worker dispatch, 제품 GO 및 독립 승인은 실행하지 않았다.

## 먼저 수행한 커밋

기존 r341 체크포인트는 `e102eef`이다. 요청에 따라 미커밋 r342 공통 그래프 코드와 r736 증거 3개만 `6271296`으로 먼저 커밋했다. P08/P17/공유 Rust 변경, private 원본 및 기타 사용자 변경을 포함하지 않았다. 원격 push도 하지 않았다.

## 구현 및 검증

1. `successor_runtime_graph_v1.py`는 원본 16개 core source를 핀 확인 후 private namespace로 로드한다. parent, frame, worker raw policy, full oracle이 같은 case159 Binding 타입을 사용한다. 실제 20쌍 worker capsule을 디코드하되 engine/body/frame을 실행하지 않는다.
2. `successor_strict_window_v1.py`는 원본 strict-window oracle의 case 정수 literal 하나만 157에서 159로 연결한다. 역변환이 전체 원본 code와 같아야 한다. 원본 defaults/closure/kwdefaults와 15초 제한, COMMITTED frame, 실제 GO/capture 각 1회, cleanup, 원래 자원·scope 검사는 유지한다. 관측 row나 기본 namespace는 수정하지 않는다.
3. 새 검사 12개와 기존 검사 9개를 함께 실행했다. 각 원본 scalar 조건 변조, bool/float/다른 case, 15초 경계, 비유한 시간, 마지막 검사 시간 불일치, 원본 코드와 row 보존을 검사한다. 합성 fixture PASS는 제품 실행 증거가 아니다.
4. 원래 case158 manifest admission을 그대로 실행한 별도 graph와 새 case159 graph를 연결했다. 실제 manifest023과 capsule001.v2의 20쌍 descriptor 및 manifest pin이 정확히 같고, 원래 failed003/004 provenance가 실패 역할 그대로 남음을 확인했다.

## 기록

- r736: `PASS_SUCCESSOR159_UNIFIED_PARENT_WORKER_ORACLE_BINDING_AND_PRIVATE_ENGINE_NOT_NATIVE_OR_GO`; fresh 38/final 38, CPU 최대 27.29%, 최소 가용 RAM 55.8418517%, cleanup true.
- r737: 21/21 코드 검사는 통과했으나 원래 engine template 구성 시 `FLAT_QUEUE_CONFIG_REQUIRED`로 실패. 실제 제품·Native 실행 전 실패, delta 0, cleanup true. 이 실패 receipt를 보존했다. 실패 receipt에 source pins와 최종 fresh/resource 통계는 없으므로 이를 확인한 것으로 주장하지 않는다.
- 수정: 원래 manifest admission 뒤, engine template을 만들기 전에 실제 STEP159/before152를 명시적으로 configure하고 일치 여부를 검사했다. 검사 조건을 삭제하거나 완화하지 않았다.
- r738: `PASS_SUCCESSOR159_FULL_MANIFEST_SHARED_GRAPH_AND_WINDOW_CODE21_NOT_CURRENT_CONTROLLER_NATIVE_OR_GO`; 21/21, errors/failures/skipped 0, fresh 138/final 138. 같은 실제 manifest·capsule·parent/worker/oracle 타입과 원래 engine 연결을 확인했다. 전체 CPU 최대 66.48%, 최소 가용 RAM 51.6410498%. actual engine/frame/worker dispatch 0, cleanup true, 승인 delta 0.

## 자원 및 안전 경계

모든 관련 qualifier는 BelowNormal/affinity 1 및 기존 guard를 사용한다. fresh read/final hash, 원래 CPU/RAM 중단 조건과 입력 읽기 속도를 유지했다. 전체 CPU 최대치는 검증기 단독 CPU를 뜻하지 않는다. 이번 성공으로 과거 PC 프리즈 원인이 해결되었다고 판정하지 않는다.

한글·접근 허용·UAC 요청, Defender/WSL/OS 설정 변경, 외부 프로세스 종료, 원본 삭제·이동, 원격 push는 하지 않았다.

## 다음 필수 작업

새 case159 controller/DATA와 독립 predecessor158 전체 oracle 연결 → 현재 source/import/Rust inventory를 포함한 whole scope 및 complete cost → whole preflight → 실제 case159 단일 제품 실행 → 독립 승인 순서다. 현재의 graph/manifest/capsule/window 코드 PASS나 이전 case158 실행, r734 baseline 비용을 case159 제품 PASS/GO 권한으로 사용하지 않는다.

근거: `implementation/p09/evidence/p09-361-case159-unified-runtime-graph-r736.v1.json`, `p09-361-case159-full-graph-window-code21-r737.v1.json`, `p09-361-case159-full-graph-window-code21-r738.v1.json`.
