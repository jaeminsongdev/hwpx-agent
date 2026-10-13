# P09-131 현재 table/review runtime 회귀

## 판정과 범위

P130에서 수정한 테스트 헬퍼를 사용하는 네 대상을 새 실행 파일로 빌드/목록 대조/실행했다.
총 67회 실행이 모두 통과했다. 고유 소스 테스트 본문은 29개이고 재사용 헬퍼 반복은 38회다.
이 수치를 제품 기능 수나 native/한글/SQL/Gate 통과 수로 바꾸지 않는다.
goal=active, P09_gate=OPEN, product_complete=false, P10 새 구현=false를 유지한다.

| 대상 | 실행 통과 | 직접 정의 | 빌드 초 | 테스트 초 |
| --- | ---: | ---: | ---: | ---: |
| table_create_hwpx | 8 | 8 | 251.48 | 0.31 |
| review_table_create_context | 15 | 7 | 4.67 | 1.07 |
| review_table_output | 21 | 6 | 5.73 | 2.06 |
| review_filled_table_output | 23 | 8 | 6.55 | 5.31 |

Context는 Create의 native 모듈을, Output/Filled는 Context와 그 native 모듈을 재사용한다.
실제 EXE 목록을 각 파일의 테스트 정의 및 정확한 모듈 이름과 대조했다.
각 실행은 terminal ok, failed/ignored/measured/filtered=0, 정확한 전체 이름 목록을 요구한다.
보존, 문맥/ID/헤더/flow binding, 보호/오염/부적합 template 거부 및 bounded debug를 검사한다.
패키지를 다시 읽는 동작은 Rust의 메모리상 ZIP/XML reader이며 한글 save/reopen이 아니다.

## 새 EXE와 기존 증거

기존 target cache를 재사용하되 cargo rustc의 extra-filename=-p131-current를 사용했다.
네 EXE는 `target/p09-121-resource-optimized/debug/deps/<대상>-p131-current.exe`이다.
P130가 보존한 기존 EXE 여섯 개의 bytes/hash를 각 단계 전후 대조했다.
P130의 기록된 lint와 그 이전 원본/실패/변경/보호 증거도 원래 guard로 역사적 범위에서 재검증했다.
이번 턴에 Rust 제품 코드, 테스트 본문/조건, 원본/SQL/설치/설정/배포/commit/push는 바꾸지 않았다.

## 파일 목록 문제와 실패 보존

Create 실행 후 Context Build 시작 전, Output List 후 Test 시작 전에 목록 검사에서 중단됐다.
두 실패는 프로세스를 시작하거나 runtime 영수증을 만들기 전 발생했다.
당시 source count/rg exit는 관측하지 못했으므로 null과 NOT_DETERMINED를 유지한다.
재확인 당시 770개 목록에는 추가/삭제가 없었다. 실패 사실은 startup observation으로 따로 보존했다.

직접 rg 프로세스로 수집하도록 보강하는 과정에서 다음 두 문제가 실제 확인됐다.

- Get-Command rg가 실행 파일 두 개를 반환했다. 배열을 한 FileName으로 변환해 시작에 실패했다.
  우선순위상 첫 Application 하나를 명시적으로 선택하도록 수정했다.
- 기본/도구별/단일 스레드 목록에 기존 `crates/artifact-service/src/bin/p14_cleanup_worker.rs`의 포함 차이가 있었다.
  단일 스레드 수집은 이 파일을 포함한 771개 입력, 기존 수집 결과는 770개 입력이었다.
  이 파일은 이전 원장에 이미 있던 SHA256
  78dedad5c76a750962a17394af0e74a94165da773c3ff29d0b6c7c3c94ec5d44와 정확히 일치한다.
  파일 추가/변경이나 P14 새 구현/실행은 아니다. 최초 두 실패의 당시 원인까지 단정하지 않는다.

새 수집은 UTF-8, 명시적 cwd/경로, rg threads=1, CPU affinity=1/BelowNormal,
10초 timeout, 직접 확인한 exit=0/stderr 없음과 전체 입력 개수를 요구한다.
Output Test와 Filled Build/List/Test에서 연속 771개 수집이 성공했다.

초기 runner 및 직접 수집의 첫 실패 runner는 완전한 사본으로 보존했다.
초기 runner에서 바뀐 부분은 입력 목록 수집 블록뿐이며 나머지 바이트는 정확히 동일하다.
완료된 초기 8개 영수증은 770개 입력/초기 runner 사본에, 새 4개는 771개/현재 runner에 결합했다.
실패한 startup 시도 네 개는 runtime 통과 수에 포함하지 않는다.
이전 원장을 재검증할 때만 기존 multi-root rg 명령 하나의 결과에서 해시가 별도로 결합된 worker 한 개를
당시 목록처럼 제외한다. 실제 단일 스레드 수집 결과를 사용하며 다른 항목은 바꾸지 않는다.
현재 runtime 검사는 worker를 포함한 771개를 요구한다. 과거 guard 함수/조건은 수정하지 않고
subprocess 호출은 종료 시 복원한다. 이 차이를 현재 전체 workspace runtime 승인으로 승격하지 않는다.
처음 이 역사적 목록 view가 없었던 검사기도 완전한 사본으로 보존했다.
Context Build는 b, Output Test는 d 영수증이며 다른 성공은 a 영수증이다.

## 자원과 검증

CPU1, BelowNormal, Cargo jobs=1, test worker=1, opt-level=1,
debug assertions/overflow checks=true, codegen-units=1을 사용했다.
2초 관측, CPU 85% 이상 3회 연속/사용 가능 RAM 4096MiB 미만/
루트·테스트 WorkingSet 2048MiB 초과/시간 제한/관측 실패에서 소유 실행만 중단한다.

Build/Test 영수증의 CPU 최고 관측 39%, 사용 가능 RAM 최저 10061MiB,
양수로 관측한 테스트 WorkingSet 최고 13.93MiB다.
빌드 중 실제 rustc 자식은 수 GiB를 사용했다. 루트 제한은 자식 메모리 합계 제한이 아니다.
짧은 실행의 baseline/exited WorkingSet=0을 최대 RAM=0으로 해석하지 않는다.

- `python tools/p09/verify_table_review_regression_progress.py`: 현재 실행/목록/전체 입력/EXE/
  runner 전환/이전 전체 증거/원장 대조.
- `python tools/p09/tests/test_table_review_regression_progress.py`: 18개 반례 검사 통과.
- `git diff --check`: 통과. 원본·기존 사용자 변경·실패 증거 보존, PLANS.md 재생성 안 함.
- source graph=1155, 이전=1151, inherited raw pin=2881.
  원장: `implementation/p09/evidence/p09-131-current-table-review-regression.source-progress.v1.json`.

전체 workspace runtime, 실제 SQL/production trust/atomic publication/native 의미/한글·렌더링은
미완료이며 이번 통과로 승격하지 않는다. 다음은 현재 코드의 더 넓은 허용 범위 통합과
실제 미완료 제품 경로다. 접근허용/UI/운영 DB/삭제/이동은 하지 않았다.
