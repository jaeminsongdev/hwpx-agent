# P09 case159 선행 전체 검증과 입력 수집

159번의 현재 설정을 유지하면서 승인된 158번의 원래 전체 oracle과 실제 입력 수집 경로를 연결했다. 158번 제품과 Native frame을 재실행하지 않았으며 공식 승인 수는 152/249로 유지한다. 다음 실제 사례는 159번, 잔여 개별 사례는 97개이고 P09/A12/A13 Gate는 OPEN이다.

## 독립된 선행 설정과 원래 oracle

isolated_predecessor158_prepare_v1.py는 원래 V25 함수군을 별도 globals에 연결한다. 함수 code/defaults/closure/kwdefaults를 유지하고 원래 admission wrapper를 private callback에 다시 연결한다. 임시 CONFIG 교체 없이 private 설정 158/before151과 현재 설정 159/before152를 분리한다.

원래 frozen prepare의 r.CONFIG도 private 설정에 연결한다. 실제 STEP158과 authority152/root158 핀, 원래 DATA·manifest·선행 범위, COMMITTED frame·두 실제 byte 경계, 제품·resource·cleanup·strict-window 전체 oracle을 확인한다. 원본 runtime row나 자원 카운터는 바꾸지 않는다.

## 159번의 실제 입력 수집

successor_current_binding_v1.py는 원래 frozen binding AST와 authority·compiled roster·현재 Rust 787개·bootstrap·archive 검사를 실행한다. 이전 사례 callback에서 독립적으로 검증한 158번 row/roster와 원래 입력을 대조한다. 단순 hash 확인으로 전체 선행 oracle을 대체하지 않는다.

독립 manifest admission과 실제 20쌍 capsule을 검증한 뒤 원래 입력 범위와 semantic 범위, fresh reader가 확인한 핀을 합친다. parent/frame/worker/full oracle이 같은 새 Binding 타입을 사용한다. 실패 003/004 provenance는 이전 사례의 실패 역할로 보존한다.

## 검증 결과와 보존한 실패

| 기록 | 결과 | 의미 |
| --- | --- | --- |
| r740 | FAILED, run 0/error 1, cleanup true | 이미 configure한 테스트에서 다시 configure하여 원래 1회 불변 조건이 거부했다. 설정이 없을 때만 테스트가 configure하도록 수정했다. |
| r741 | CODE8 통과, 전체 연결 FAILED, cleanup true | frozen prepare의 r.CONFIG가 현재159를 보아 158의 실제 root 경로 검사가 거부했다. private r.CONFIG 연결을 추가했다. |
| r742 | run 9/failure 1, cleanup true | 독립적으로 두 번 compile한 code의 객체 identity를 비교했다. 동일 compile 결과의 전체 code equality로 확인하도록 수정했다. |
| r743 | CODE9 9/9 및 실제 전체158 oracle PASS | fresh 228/final 228, 전체 CPU 최대 28.97%, 최소 가용 RAM 55.36061%, cleanup true. 현재159 CONFIG 객체와 기본 binding/checkpoint를 유지했다. |
| r744 | CODE8 8/8 및 실제159 원래 binding PASS | Rust 787개, 20쌍, semantic/physical 입력 각각 2698개, fresh 1028/final 1028, 전체 CPU 최대 56.06%, 최소 가용 RAM 51.98427%, cleanup true. |

실패 receipt와 성공 receipt는 별도 파일로 보존한다. 실패 기록에 source pins나 최종 fresh 통계가 없는 항목을 관측한 것으로 주장하지 않는다. 위 CODE 검증은 실제159 제품 실행이나 독립 승인 결과가 아니다.

## 입력 수집 단계의 비용과 제품 실행 경계

r744의 입력 수집 범위는 directories 372, physical bytes 251664289, semantic bytes 286153707이다. 원래 식과 14/s acquisition, 20/s byte/open ceiling, binary 1MiB/s·other 2MiB/s 읽기, 두 실제 byte 읽기, 60초 margin, 15초 product window 및 shared decoder 5초를 유지한 모델은 596.307694초다.

이 모델은 새 controller·DATA·전체 import inventory·whole preflight를 아직 포함하지 않는다. 이 값이나 component PASS만으로 GO를 발행하지 않는다. 실제 controller·DATA와 전체 source/import/Rust inventory를 연결하고 비용을 새로 확인한 뒤 whole preflight, 실제159 단일 제품 실행, 독립 승인 순서로 진행한다. full249-current, signed16 및 전체 P09 Gate는 별도 완료 조건이다.

## 자원과 원본 보호

검증기는 BelowNormal/affinity 1 및 기존 resource guard를 사용했다. 단일 실행을 관찰하면서 fresh read와 final hash를 완료했다. 전체 시스템 CPU 수치는 검증기 단독 CPU가 아니며 과거 PC 프리즈 해결 증거로 사용하지 않는다.

P08/P17/공유 Rust 코드와 private 원본, 성공158 및 실패 증거를 보존했다. 한글·접근 허용·UAC 요청, Defender/WSL/OS 설정 변경, 외부 프로세스 종료, 삭제·이동, 원격 push는 없었다. 목표는 ACTIVE이고 P10 새 구현은 시작하지 않았다.

근거는 implementation/p09/evidence 아래 p09-361-case159-isolated-prior158-code8-r740.v1.json, p09-361-case159-isolated-prior158-code8-r741.v1.json, p09-361-case159-isolated-prior158-code9-r742.v1.json, p09-361-case159-isolated-prior158-code9-r743.v1.json, p09-361-case159-original-current-binding-code8-r744.v1.json이다.
