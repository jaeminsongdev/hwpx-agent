# P09-129 현재 코드의 저장소 처리 회귀

## 판정과 범위

현재 코드의 `form_stored_provider` 독립 사례 228개가 모두 통과했다.
원본/변경/보호 수식의 정제된 marker 재수집 4개도 정상 종료했고 기존 해시 결합 결과와 정확히 일치했다.
최종 판정은 PASS_CURRENT_DISTINCT_SCOPED228_AND_SIGNED_MARKERS_NOT_NATIVE_OR_GATE이다.
목표는 active, P09 Gate는 OPEN, product_complete=false, P10 새 구현은 시작하지 않았다.

| 현재 코드의 범위 | 독립 종료한 통과 사례 |
| --- | ---: |
| actual_import | 200 |
| full_document | 20 |
| 저장소 기본 계약 | 8 |
| 합계 | 228 |

각 사례는 새 실행 파일에서 `--exact --nocapture --test-threads=1`로 실행했다.
각 영수증은 passed=1, failed=0, ignored=0, measured=0, filtered=227 및 정확한 사례 이름을 검증한다.
동일한 228개 inventory와 일대일 대응한다. 한 프로세스의 전체 228개 실행, 전체 workspace,
실제 SQL/한글/렌더링/제품 Gate 통과로 승격하지 않는다.
P128의 현재 메모 관련 50개 통과와 P127의 보호 수정 및 실패 반례는 별도 증거로 보존한다.

## 새 실행 파일과 과거 증거 보존

- 과거 파일: `target/p09-121-resource-optimized/debug/deps/form_stored_provider-658c5ea10a96d565.exe`.
  bytes=10688512, SHA256=04fefdf71582488f4490a5e572203994d89fbc890c1282b5336b3703a581a5ca.
- 같은 bytes/hash 사본: `target/p09-121-resource-optimized/p129-historical-executable/form_stored_provider-658c5ea10a96d565.exe`.
- 현재 파일: `target/p09-121-resource-optimized/debug/deps/form_stored_provider-p129-current.exe`.
  bytes=10688512, SHA256=aadf093a65dfc451feda8ae96d64938d51fb0e90af3cf7810e6072c65d073941.

현재 빌드는 cargo rustc의 `extra-filename=-p129-current`로 출력 이름을 분리했다.
과거 EXE를 덮어쓰거나 Cargo 출력에 과거 EXE를 복원하지 않았다.
P128 및 그 이전의 원본 guard와 과거 영수증을 그대로 재검증했다.
P129는 crates의 전체 파일 756개, workspace Cargo.toml/Cargo.lock, 내장 trust 입력 2개,
현재 runner 1개를 합한 761개 파일의 bytes/hash를 실행 전후 확인한다.
trust 값과 stdout/stderr 원문은 공개하지 않는다. 설정/원본/운영 DB는 변경하지 않았다.

## 부하 제한과 관측

- CPU affinity 1, BelowNormal, Cargo jobs=1, test worker=1.
- test profile opt-level=1, debug assertions/overflow checks=true, codegen-units=1.
- 2초 주기로 시스템 CPU, 사용 가능한 RAM, 루트/테스트 process WorkingSet을 관측한다.
- CPU 85% 이상 3회 연속, 사용 가능 RAM 4096MiB 미만, 루트/테스트 WorkingSet 2048MiB 초과,
  최대 시간 또는 관측 실패이면 해당 소유 실행만 중단한다. 시작 시 이미 압력이 높으면 실행하지 않는다.
- 빌드 28.30초, 빌드 중 사용 가능 RAM 최저 15093MiB.
- 228개 wrapper 시간 합계 832.09초; 전체 경과 시간이나 통제된 성능 비교가 아니다.
- 228개 영수증의 관측 491개: 성능 카운터 CPU 최고 65%, 사용 가능 RAM 최저 15833MiB,
  양수로 관측된 테스트 WorkingSet 최고 25.18MiB, 실패/중단 0개.
- 짧은 테스트의 baseline/exited process WorkingSet=0은 RAM 최대 사용량 0이라는 뜻이 아니다.
  빌드 루트 WorkingSet 제한도 모든 rustc 자식의 메모리 합계 제한이 아니다.
- 별도의 Win32_Processor LoadPercentage에서 100이 관측되었지만 인접한 누적 시간 기반 CPU는 10.1%,
  guard 성능 카운터는 5%였다. 원인을 특정하거나 측정 창이 같다고 주장하지 않는다.

## 실패와 잘못된 선택 보존

최초 preparation 검사에서는 rg 목록의 순서 차이만으로 source_freeze_drift가 발생했다.
761개 경로/bytes/hash의 집합은 동일했고 테스트를 시작하지 않았다.
경로별 순서 무관 비교로 수정하되 중복, 누락, 해시/크기 변경은 계속 거부한다.

추가 marker 재수집의 a 시도 4개는 PowerShell 문화권 정렬 순서 때문에 다른 사례가 선택되었다.
해당 사례 자체의 통과를 요구된 원본/변경/보호 marker 통과로 인정하지 않는다.
`p129-current-marker-01..04-a.json`을 보존하며, 정확한 사례 이름 검사는 marker_case_identity_drift로 거부한다.
정확한 Python inventory의 이름을 사용한 b 시도는 별도 새 영수증으로 실행했다.
a 시도를 삭제하거나 덮어쓰거나 통과 수에 더하지 않는다.

b 시도 4개는 각각 58.88, 3.58, 204.71, 23.12초에 정상 종료했다.
원본 36개 결과는 P120 원본 결과와, 변경 후보 16개 결과는 기존 P124-051 결과와 정확히 일치했다.
추가 입력 변조 16개와 보호 거부 32개 marker도 확인했다.
이 재수집은 228개 안의 같은 사례 반복이며 독립 통과 개수에 더하지 않는다.
marker runner는 기존 761개 입력에 runner와 두 support 파일을 추가한 764개 입력을 전후 대조한다.

## 검증 방법과 남은 경계

- `python tools/p09/run_current_stored_batch.py`와 `python tools/p09/verify_current_stored_regression.py --progress`:
  현재 EXE, 과거 EXE/사본, 전체 compile 입력 및 독립 사례 inventory/영수증 대조.
- `python tools/p09/tests/test_current_stored_batch.py`: 17개 통과.
- `python tools/p09/tests/test_current_stored_regression.py`: 11개 통과.
  이 28개 guard unit은 제품 사례나 native qualification 개수가 아니다.
- `git diff --check`: 통과. HEAD와 사용자 소유 tracked 변경은 보존했고 PLANS.md는 재생성하지 않았다.
- `python tools/p09/verify_current_stored_regression.py`: 현재 228개, signed marker, 보존된 잘못된 선택,
  전체 physical pin 및 P128 이전 증거의 최종 전수 대조.
- 원장: `implementation/p09/evidence/p09-129-current-stored-regression.source-progress.v1.json`.
  현재 source graph 1147개 = P128 1140개 + 새 source/report 7개; inherited raw pin 2621개.
- 현재 전체 workspace/엄격 lint의 포괄적 재검증은 미완료다.
  실제 SQL, production trust/issuer, atomic publication, 원본 source의 native 의미와 한글 실사용/렌더링은
  이번 범위에서 실행하거나 인정하지 않았다. `RouteUnqualified` 차단을 제거하지 않았다.
- 다음 작업은 현재 코드의 포괄적 통합/lint와 원본 source admission 및 제품 경로의 실제 미완료 항목이다.
  접근허용/UI/운영 DB/설치/배포/commit/push/삭제/이동은 하지 않았다.
