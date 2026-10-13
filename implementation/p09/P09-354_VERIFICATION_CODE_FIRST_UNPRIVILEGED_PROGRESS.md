# P09-354 검증 코드 우선 수정·비관리자 검토

작성일: 2026-10-10. 목표 ACTIVE. P09/A12/A13 OPEN. P10 시작하지 않음.

## 범위와 결론

사용자는 외출 중이므로 UAC/한글 접근 허용을 누를 수 없다. 관리자 Defender 추적을
진행의 선행조건으로 삼지 않고 검증 코드 자체를 재검토·수정한다.
현재 코드가 무결하거나 PC 프리즈가 해결됐다고 결론 내리지 않는다.

제품 큐 수용은 102/249, 잔여 147(일반 141+corpus 6), 다음 109이다.
성공 제품 107/108은 재실행하지 않았다. 이것은 특정 큐의 수치이며 P09 전체 잔여율이 아니다.

## 코드 변경 및 유지한 검사

1. 실제 parent 경로에도 `ActualHeldPathGuards`를 연결한다. 원 bound method를 통해
   before/after 두 전체 byte 경계를 실행하고, reader root/owner/token/stream identity를
   유지한다. 정상 종료와 STOP 모두 instance method를 복구한다.
2. V20 LIGHT048/FRESH049/STOP050은 정확한 과거 코드 2개와 literal 828 oracle에만
   연결한다. V21 GO로 승격하지 않는다. `_scan`의 `UNREVIEWED_STOP_BLOCKS_GO`는
   유지하며 별도 현행 STOP review가 필요하다.
3. `sys.dont_write_bytecode=True`, 프로세스 한정 `PYTHONDONTWRITEBYTECODE=1`,
   launcher `python -B`로 불필요한 `.pyc` 쓰기를 막는다. 기존 cache는 삭제하지 않으며
   시스템/Defender 설정을 변경하지 않는다. 검증 증거 저장 자체를 없애는 변경이 아니다.
4. bytecode 정책의 음성 검사는 full1658/body/frame fixture를 만들지 않도록 이동했다.
   `common`에서 정책을 queue 선택보다 먼저 검사한다. False/숫자/문자열/None/키 누락이
   정확히 해당 guard에서 거부되고, queue가 호출되지 않는 것을 작은 모의 검사로 검증한다.
   이 마지막 변경의 실행 검사는 CPU 포화 admission에서 보류됐으므로 아직 NOT_RUN이다.

원 Native 획득/잠금, 전체 입력 1658, 두 전체 byte, 원 Job/CPU/RAM/deadline,
파일 열기·읽기 pacing, 독립 fresh hash, 실패 증거, 정리는 유지한다.
추가 sampler/thread/제품 child/자동 retry는 만들지 않았다.

## 실제 확인 결과와 자격 경계

| 확인 | 결과 |
|---|---|
| 작은 합성 55개 | 처음 54 PASS + mock alias AttributeError 1건. alias 수정 뒤 그 1건만 별도 PASS. 54개 재실행하지 않음 |
| 실제 경로 adapter 모의 6개 | 위 55개 안에서 PASS. 실제 Native/제품 검증이 아님 |
| bytecode 플래그 작은 1개 | `python -B`, 원 preimport admission 뒤 PASS. 진단 CPU 24.17%, 가용 RAM 23.517289% |
| 최신 코드 2개 AST | PASS. 정의/선언 431 일치. own affinity mask 1. 테스트·제품 실행 아님 |
| 최신 정책 음성·양성 2개 | target module import 전 CPU 100%, 가용 RAM 22.369834% → admission DEFERRED, 실제 검사 0 |
| 현재 정식 자격 431×2=862 | NOT_QUALIFIED. 과거 828을 현행 862 PASS로 재사용하지 않음 |
| 문서 final-fresh / 전체 runtime / P09 Gate | NOT_RUN / 미완료 / OPEN |

작은 검사 최초 launcher에서 첫 CPU 표본을 생성 직후 요청하여
`CPU_SAMPLE_INTERVAL_MISSING`이 발생했다. 검증 대상 import/검사 전이며, 원 표본 간격
0.5초를 둔 launcher로 수정 후 위 1개 PASS를 얻었다. guard를 완화하지 않았다.

## 실패·보류 증거와 CPU 해석

기존 실제 109 run050은 원 handle 1966 획득 뒤 before805 부분에서 CPU STOP했다.
제품 body는 `DEFERRED_NOT_STARTED`, 실제 제품 child false다. 원 1966/dup805는 모두
닫혔고 frame CLOSED/정리 true다. host 최고100%, own 최고1.584158%, private140472320bytes.
이 실패 원본은 그대로 보존한다.

현행 stop-review052는 `final_fresh_preparation`에서 CPU STOP했다. contracts0,
source_attempted false, actual_product_child false, watcher 정리 true. 독립 검토 PASS가 아니다.
종료 표본의 마지막 네 system CPU는 98.63/100/100/100, own0이다. 마지막 세 논리 읽기 증가0.
0.5초·16 logical CPU의 전체 tick 증가80000000은 극단적으로 짧은 표본 간격 오판의 근거가 아니다.

새 stop-review056은 본 runtime import 전 CPU100%, 가용 RAM22.333077%에서 원 admission으로
보류됐다. main/reader/계약/Native/제품 미시작, 056 receipt 없음. light057/fresh058/actual059도
실행하지 않았다. 같은 전체 명령을 무조건 반복하지 않았다.

052 종료 후 **별도** 비관리자 WMI 표본에서 MsMpEng가 machine 환산69.562%(앞선 표본80.875%),
System2.625%였다. OS processor `_Total`의 별도 표본은100%였다. sampling window가 동일하지
않으므로 정확히 한 순간의 합으로 해석하지 않는다. PerfProc `_Total`은 Idle을 포함할 수
있으므로 해당1599/16=99.938%를 system busy CPU라고 사용하지 않는다.
Defender가 CPU의 큰 부분을 사용한 관측은 있지만, 특정 검증 파일/쓰기가 scan을 유발했다거나
PC 프리즈의 단일 원인이라는 인과는 입증하지 못했다.

## 정확한 현행 코드 및 원본 보존

현행 `tools/p09/resume_preserved106_queue_runtime.py`: 152778bytes,
SHA256 `9fcf1446bf38e14b67c05f10f25b693e6656a9864227d7d71a21ae9bc27b8473`.

현행 `tools/p09/tests/test_preserved106_queue_runtime.py`: 122705bytes,
SHA256 `460c5b21a7bba065e9c77c888f573b8d9d4dd1487c3532f60a9cc7eb335ee880`.

현재 2개는 `evidence/p354-v21-policy-fixture-optimized-code/`에 동일 hash로 보존했다.
mock 수정 전은 `p354-v21-before-mock-repair-code/`, bytecode 후보는
`p354-v21-bytecode-candidate-code/`, 정확한 qualified828은 `p340-formal828-code/`에 별도 보존한다.
과거 실패/빈 placeholder/qualified790·828/성공 제품 body를 덮어쓰거나 삭제하지 않았다.

## 다음 경계

작은 정책 음성 검사 → 정확한 STOP050의 독립 현행 review → 현재862 자격 → 별도 fresh →
미실행109 단일 사례 순서다. CPU STOP이면 그 단계의 코드·필요 작업을 재검토하며 맹목 반복하지 않는다.
이 과정에 UAC/한글 허용/Defender 특권 추적을 요구하지 않는다. 보호 기준을 낮추거나 STOP을
PASS로 바꿔 통과시키지 않는다.

이번 단계 UAC/한글/관리자 추적/Git/빌드/Defender·OS·WSL 설정 변경/외부 process 종료/
삭제·이동은 0이다. 목표는 ACTIVE이고 실제 Gate 완료로 표시하지 않았다.
