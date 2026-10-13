# P09 case160 실패 검토 재사용의 실제 연결

실패 검토의 선언 재사용을 실제 26쌍 전체 Binding의 private 연결에 적용했다. 원래 전체 검토 1회 뒤 두 중복 호출에서 선언만 재사용했고 최종 freshness를 유지했다. 새 제품 controller와 공유 720초 실행 완료는 아직 미검증이며, 공식 승인은 153/249와 P09, A12, A13 OPEN을 유지한다.

## 연결과 계약 검사

`failure_review_current_connection_v1.py`는 기본 모듈을 수정하지 않고 별도로 만든 raw namespace에만 연결한다. 현재 controller의 원래 `own_inputs`, partial role, manifest, bootstrap이 같은 private attempt를 참조하는지 확인한다. 원래 검토 함수는 보존하고 검증 후 복원한다. 제품, Native, GO와 큐 승인은 호출하지 않는다.

계약 검사 22개는 helper 14개와 연결 8개로 구성된다. 기본 모듈 거부, 다른 호출 지점의 dependency 거부, 중복 연결 거부, 잘못된 qualification 및 review pin 거부, 원래 함수 복원을 검사한다. 초기 계약 검사에서 기본 모듈을 검사하기 전에 `M`을 읽는 순서 오류를 수정했다. 실제 raw 연결에서는 `M`에 `attempt`가 없음을 확인해 원래 `own_inputs`의 globals에서 dependency를 확인하도록 수정했고, 실패 r814를 보존했다.

## 실제 전체 Binding 결과

r815는 실제 DATA038과 preflight038을 승인하는 전체 Binding을 실행했다. 원래 compiled Rust 787개, 26쌍 manifest 및 capsule과 이전 전체 oracle 경로를 유지했다. 계약 검사 22개, fresh 및 final 1,126개와 cleanup을 확인했고 원래 private 검토 함수도 복원했다. 시스템 CPU 최고 39.65%, 사용 가능 RAM 최저 49.15095%였다.

원래 전체 실패 검토 1회와 중복 선언 재사용 2회가 확인됐다. 재사용으로 실패 원본 4,128,024바이트와 review 1,433바이트를 두 번 다시 읽지 않아 해당 호출에서 8,258,914바이트를 피했다. 파일 바이트, runtime JSON 행이나 hash 계산을 캐시하지 않으며 첫 전체 검토와 최종 freshness는 수행한다.

최종 검사 전 실제 읽기는 1,236회, 341,868,664바이트였고 반복 읽기는 163,277,580바이트였다. 이전 r811의 354,229,890바이트와는 진단 SELF 및 review 입력이 다르므로 차이 전체를 실제 runtime 개선량으로 해석하지 않는다. 과거 case158 run005의 6회, case159 run001의 5회 읽기는 여전히 남아 있다.

## 다음 실행 경계

원본 및 실패 증거를 유지하면서 남은 큰 승인 호출의 중복을 검토한다. 이후 새 실행 identity와 controller DATA에 연결하고 전체 source 및 import inventory, Native 600초와 공유 720초의 전체 비용을 검증해야 한다. 기존 case160 run002 파일이 있으므로 같은 실행 번호를 다시 사용하지 않는다. 두 Native 읽기와 독립 승인 전에 공식 건수를 늘리지 않으며 P10 구현을 시작하지 않는다.

현재 나타난 다른 Python 프로세스는 hwpx-agent가 아닌 `D:\dev\books` 작업이었다. 외부 작업에는 변경을 가하지 않았다. 접근 허용, UAC, OS 설정 변경, 외부 프로세스 종료, 원본 삭제·이동과 원격 push는 수행하지 않았다. 컴퓨터 프리즈 해결 및 Defender 인과관계는 이번 연결 검증으로 입증하지 않는다.
