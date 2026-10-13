# P09-133 최적화 후 전체 workspace 엄격 lint

## 판정과 범위

현재 Windows host/default feature의 Cargo workspace 32개 package/358개 target에
`cargo clippy --workspace --all-targets --locked --offline --jobs 1 ... -- -D warnings`를 실행했다.
성공한 d 기록은 394개 artifact record가 358개 고유 target과 정확히 대응한다.
build-finished=true/exit0, error/warning/diagnostic=0이다. all-features나 다른 host를 검증한 것은 아니다.

수정된 메모 비교 테스트를 별도 새 EXE로 빌드/목록 대조/실행해 전체 15개를 다시 통과했다.
failed/ignored/measured/filtered=0이다. lint는 테스트·앱을 실행하지 않고,
별도 15회 테스트는 typed-model 원본 비교이며 한글/실제 SQL/제품 Gate 증거가 아니다.
goal=active, P09_gate=OPEN, product_complete=false, P10 새 구현=false를 유지한다.

## 확인된 문제와 수정

첫 lint a에서 P132의 새 비교·측정용 Rust 테스트 모듈 문제 9건이 나왔다.

- items_after_test_module 2건: include한 원본/current private test 뒤에 revalidate 헬퍼를 놓았다.
  헬퍼를 include 앞에 놓았다. Rust의 선언 순서 변화이며 검증 동작/테스트 조건은 그대로다.
- struct_field_names 4건: library에서 공개된 원본 모델의 ID 구조체를 private embedding에 넣어
  공개 모델과 다른 유효 visibility로 lint했다. 두 embedding과 바깥 모듈을 **통합 테스트 binary에서만**
  공개했다. 원본/current 모델의 field 이름·native identity·직렬화 계약은 바꾸지 않는다.
  제품 library API에는 변경이 없다. 별도 lint allow를 추가하지 않았다.
- needless_pass_by_value 1건: request helper가 읽기만 하는 Value를 참조로 받도록 했다.
  해당 호출의 불필요한 clone을 제거했다. JSON 내용·순서·오류·대조 조건은 그대로다.
- semicolon_if_nothing_returned 2건: profiling sample push에 세미콜론을 추가했다.

두 번째 lint b에서 공개 측정 helper 두 개의 missing_errors_doc가 확인됐다.
정확한 validation error 반환을 설명하는 # Errors 문서를 각각 추가했다.
원본/current validator와 모든 assert 조건은 수정하지 않았으며 기존 allow 선언도 그대로다.

변경 전 fixture 전체 16,616 bytes와 test parent 전체 5,125 bytes를
`implementation/p09/source-archive/p09-133-pre-catalog-lint/`에 완전한 사본으로 보존했다.
b 시점 fixture도 `target/p09-121-resource-optimized/p133-intermediate-catalog-fixture.rs.txt`에
완전한 사본으로 남겼다. 원본→중간→현재 변경은 선언한 정확한 텍스트 치환으로 검증한다.
test parent 변경도 `mod catalog_index`의 test-only 공개 변경 한 개뿐이다.
이번 턴의 Rust 제품 코드·schema·원본·SQL·권한·설치·설정·배포·commit·push는 바꾸지 않았다.

## 실패·대기·현재 결과

| lint 시도 | 상태 | 관측 |
| --- | --- | --- |
| a | 실패/exit101 | 68.76초, 9개 lint error, 기록 보존 |
| b | 실패/exit101 | 4.36초, 2개 missing_errors_doc, 기록 보존 |
| c | 시작 안 함 | CPU97%/가용 RAM14231MiB로 사전 resource guard에서 대기 |
| d | 통과/exit0 | 12.01초, 전체 358 targets/394 records, 진단 0 |

c는 프로세스 실행/빌드/테스트 성공으로 계산하지 않는다. d 전에 CPU4%/RAM15364MiB를
확인했다. 관측 시간 제한만으로 재시작하지 않았으며 각 이전 실행의 terminal 상태 또는
시작되지 않은 상태를 확인했다. 기존 실패 파일을 덮어쓰거나 삭제하지 않았다.

현재 catalog Build 15.53초, Test wrapper 0.64초, 실제 Rust terminal 0.37초/15PASS이다.
새 실행 파일은 `target/p09-121-resource-optimized/debug/deps/comment_style_section_protection-p133-current.exe`다.
P132의 실행 파일을 덮어쓰지 않았다. source/EXE/list/terminal 이름을 현재 파일의 정확한 해시와 결합했다.

기존 큰 입력의 비교/측정도 다시 실행했다. 4096 authors/4096 styles/2048 comments의
isolated validator 중앙값은 원본 10.100ms/current 1.735ms, 관측 비율 5.82배였다.
P132의 9.628/1.897ms 기록은 그대로 남긴다. 입력/측정 구간의 결과이며 전체 제품 속도 주장이 아니다.

## 자원과 보호

CPU1, BelowNormal, Cargo jobs=1, Rust test worker=1을 유지한다.
2초 관측, CPU85% 이상 3회 연속/가용 RAM4096MiB 미만/
루트 WorkingSet2048MiB 초과/시간 제한/관측 실패에서 해당 소유 실행만 중단한다.
컴파일러 자식의 CPU1/BelowNormal을 검사하며 루트 제한을 자식 메모리 합계 제한으로 해석하지 않는다.

성공한 lint d의 CPU 최고 관측40%, 가용 RAM 최저14122MiB, child limit check20회다.
catalog Build는 CPU 최고34%/가용 RAM 최저14504MiB였다. 짧은 테스트의 baseline/exited=0은
실제 최대 RAM=0이라는 뜻이 아니다. 대기한 CPU97% 관측을 숨기거나 성공 실행의 최고40%와 혼동하지 않는다.

기존 P130 6개/P131 4개/P132 4개 EXE, 총14개 bytes/SHA256을 모든 단계 전후 대조했다.
현재 lint와 catalog는 각각 774개 실제 source 입력을 결합하며 원본 모델 embedding/preimage도 포함한다.
다른 실행 프로세스를 임의 종료하거나 P120 CPU-heavy EXE를 재실행하지 않았다.

## 증거 보존과 남은 경계

P132의 65회 결과 및 그 이전 원장 전체는 두 변경된 테스트 파일을 완전한 원본으로 읽는
역사적 view에서 원래 guard로 재검증했다. guard 함수·조건은 바꾸지 않았고 ROOT/import loader는
종료 시 복원했다. 이 65회를 이번 턴에 새로 실행했다고 주장하지 않는다. 현재 새 실행은 catalog15회다.
제품 모델은 P132의 최적화 이후 그대로이며 전체 current workspace lint는 실제로 새 실행했다.

- `python tools/p09/verify_optimized_workspace_lint.py`: 이전 증거/정확한 fixture 변경/실패 2회·대기 1회/
  current 전체 lint inventory/774개 input/EXE14개 보호/current catalog15회/실제 profiling/원장 검증.
- `python tools/p09/tests/test_optimized_workspace_lint.py`: 16개 정상·반례 검사 통과.
- `git diff --check`: 통과. PLANS.md 재생성 없음, 삭제·이동·한글/UI/운영 DB 실행 없음.
- source graph=1165, 이전=1160, inherited raw pin=2940.
- 원장: `implementation/p09/evidence/p09-133-optimized-workspace-lint.source-progress.v1.json`.

현재 전체 workspace runtime, 실제 SQL/production trust/atomic publication/native metadata 의미/
한글 저장·재열기·렌더링·P09 Gate는 미완료다. 이 lint를 실제 제품 기능 또는 Gate 통과로 승격하지 않는다.
다음은 접근허용이 불필요한 실제 미완료 제품 경로를 현재 요구사항과 대조해 구현·통합하는 범위다.
