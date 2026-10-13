# P09-132 메모 참조 목록 검증 최적화

## 실제 변경과 판정

`crates/domain-ir/src/comment_model.rs`의 전체 상태 검증은 각 comment의 작성자·스타일과
해결 작성자 존재 여부를 매번 전체 목록에서 선형 탐색했다. 목록과 메모 수의 곱에 비례하는
탐색이 반복됐고, 이미 검증한 작성자·스타일 ID 집합은 사용하지 않았다.

전체 상태 검증은 기존 `BTreeSet<u32>`를 재사용한다. 집합을 추가 생성하거나 상태·목록을
정렬/축소하지 않는다. 단일 삽입·해결 변경은 기존 목록 탐색을 유지하며 같은 validator에
존재 여부 함수를 전달한다. 호출 순서·오류 우선순위·중복 검사·보호·native binding·시간·digest·
출력 제한·canonical bytes·계획/결과/영수증은 변경하지 않는다. 제품 route는 여전히 unqualified다.

이 변경은 typed comment IR의 계산 비용 개선이지 실제 native mapping/product Gate 완성이 아니다.
goal=active, P09_gate=OPEN, product_complete=false, P10 새 구현=false를 유지한다.

## 원본과 공개 경로 비교

변경 전 현재 모델 전체(55,861 bytes)와 기존 P127 테스트 전체(4,943 bytes)를
`implementation/p09/source-archive/p09-132-pre-comment-catalog-index/`에 완전한 사본으로 보존했다.
모델의 변경은 선언한 9개 byte 치환의 정확한 결과이며, 기존 테스트는 외부 검증 모듈
한 개의 include만 덧붙였다. 기존 테스트 본문/조건/사용자 변경은 유지했다.

새 외부 Rust 모듈은 원본 모델과 현재 모델을 같은 EXE에 포함한다. 실제 공개 library API와
원본 구현에 동일한 JSON을 전달해 허용/거부 코드와 성공 canonical bytes를 비교한다.
5개 작업의 request/plan/result state/receipt bytes도 비교한다. 기존 모델 소스의 private plan
tampering test는 원본/current embedding에서 각각 실행한다. 이것은 두 제품 기능 추가가 아니다.

검사에는 작성자·스타일 순서, 빈 작성자 목록, 0/없는 ID·해결 작성자, 중복 catalog와 오류 우선순위,
payload/시간/anchor/identity 오류, 모든 5개 작업, 보호·noop·stale·삽입/해결 참조 오류,
설정된 출력 제한, 대형 상태 전체 바이트 비교 및 구간 profiling이 포함된다.

| 현재 target | 전체 실행 통과 | 빌드 초 | 테스트 wrapper 초 |
| --- | ---: | ---: | ---: |
| comment_style_section_protection | 15 | 153.44 | 0.62 |
| comment_model | 10 | 2.12 | 0.25 |
| comment_operation | 16 | 150.74 | 0.30 |
| stored_comment_provider | 24 | 8.47 | 0.52 |

총 65회 실행, failed/ignored/measured/filtered=0. Catalog 15회는 기존 보호 4개,
새 비교/profiling 9개, 원본/current private test 반복 2회로 구성된다.
목록은 실제 EXE --list와 정확한 소스 정의/모듈 경로를 대조했다.
Stored target의 저장소는 기존 in-memory fixture이며 실제 SQL/운영 DB 검증은 아니다.

## 측정된 성능 범위

동일한 4,096개 작성자, 4,096개 스타일, 2,048개 메모의 유효 상태를 사용했다.
모든 메모의 작성자/스타일/해결 작성자가 목록 끝에 있는 입력이다. 전체 상태는 8MiB 내의
명시적 허용 제한으로 실제 승인되고, 공개 상태의 canonical bytes는 원본과 동일하다.

`validate_document_state`만 7회씩 교대 순서로 측정하고 actual nanoseconds를 보존했다.
입력 decode/생성/clone/serialization/I/O 및 전체 제품 실행은 측정 구간에서 제외했다.

- 원본 중앙값: 9.628 ms
- 현재 중앙값: 1.897 ms
- 이 입력·구간의 관측 속도 비율: 5.07배, 중앙값 시간 약 80.3% 감소

전체 제품이 5배 빨라졌다거나 모든 입력에서 동일한 개선이 있다고 주장하지 않는다.
성능 임계값으로 Rust 기능 검사를 통과시키지 않는다. 별도 검증기는 실제 기록의 중앙값에서
개선이 관측됐는지 확인하고, 관측이 없으면 개선 판정을 거부한다.

## 자원 제한과 중단/실패 보존

CPU affinity=1, BelowNormal, Cargo jobs=1, Rust test worker=1,
opt-level=1/debug assertions=true/overflow checks=true/codegen-units=1을 적용했다.
2초 관측, CPU 85% 이상 3회 연속/가용 RAM 4096MiB 미만/
루트 WorkingSet 2048MiB 초과/시간 제한/관측 실패에서 해당 소유 실행만 중단한다.
컴파일러 자식에도 CPU1/BelowNormal을 적용했다. 루트 메모리 제한은 자식 메모리 합계 제한이 아니다.

완료된 Build/Test에서 가용 RAM 최저 9821MiB, CPU 최고 관측 100%였다.
100%는 일시적 관측이며 완료된 실행에서 3회 연속 조건은 발생하지 않았다.
짧은 Test의 WorkingSet은 baseline/exited=0만 잡혔다. 실제 최대 RAM=0이라는 뜻이 아니다.

세 번의 불승인/대기 시도를 보존했다.

1. Catalog Test a: Rust terminal 15 PASS/exit0이지만 `--nocapture`가 profiling 출력과 test status를
   같은 줄에 섞어 수집기가 profile/정확한 전체 이름을 확보하지 못했다. 결과는 불승인으로 유지한다.
   runner 전체 사본을 보존하고 `--show-output`으로 변경했다. Test b에서 15개 이름/profile을 확보했다.
2. Operation Build a: runner가 디렉터리명 product-cli를 Cargo 패키지명으로 사용해 exit101이었다.
   `cargo pkgid --offline -p product-cli`에서도 실제 패키지 불일치를 확인했다.
   원본 runner를 보존하고 실제 `hwpx-agent-cli` 이름으로 수정했다. Rust 제품 실패로 취급하지 않는다.
3. Operation Build b: 시작 전 CPU100%로 `DEFERRED_RESOURCE_PRESSURE_NOT_STARTED`였다.
   당시 별도 cargo/rustc를 관측했지만 이 실행은 시작하지 않았고 그 프로세스도 종료하지 않았다.
   10:31:38 UTC 교차 관측에서 GetSystemTimes CPU99.9%/CIM59%/RAM14890MiB였다.
   원인을 특정 프로세스로 단정하지 않는다. 10:32:44 UTC에는 native14.52%/CIM14%/RAM14845MiB로
   내려간 것을 확인했다. Build c에서 실행 완료했다. 대기 시도는 테스트 통과 수에 포함하지 않는다.

성공한 Catalog Build/List는 첫 runner, Catalog Test b/Model은 두 번째 runner,
Operation/Stored는 현재 runner 전체 사본/해시와 각각 결합했다.
runner 전환은 출력 표시 옵션 한 개 및 패키지명 두 개의 정확한 치환뿐이다.

## 통합과 증거 경계

네 새 실행 파일은 `<target>/debug/deps/<target-name>-p132-current.exe`로 별도 생성했다.
기존 P130의 실행 파일 6개와 P131 실행 파일 4개의 bytes/SHA256은 매 단계 전후 동일하다.
현재 source freeze는 기존 Rust/프로토콜/xtask 입력과 Cargo/내장 P04 입력/runner/자원 helper/
검증 overlay/원본 사본을 포함한 774개다. signed original·private 원본·실패 증거는 보존했다.

P131과 이전 원장 전체는 두 변경 파일을 완전한 preimage로 읽는 역사적 view에서 원래 guard로
재검증했다. 종료 후 ROOT/import loader를 복원했다. 이는 과거 228/50/67 scoped 결과의
보존 검증이며 현재 전체 workspace runtime으로 승격하지 않는다. 기존 guard 함수/조건은 수정하지 않았다.

- `python tools/p09/verify_comment_catalog_optimization.py`: 현재 65회 실행/정확한 목록·전체 입력·EXE/
  선언된 byte 변경/이전 증거/실패·대기 기록/실제 profiling/원장 대조.
- `python tools/p09/tests/test_comment_catalog_optimization.py`: 16개 정상·반례 검사 통과.
- `git diff --check`: 통과. PLANS.md 재생성/원본 삭제·이동/설치·설정·SQL·UI·commit·push 없음.
- source graph=1160, 이전=1155, inherited raw pin=2909.
- 원장: `implementation/p09/evidence/p09-132-comment-catalog-optimization.source-progress.v1.json`.

현재 전체 workspace 엄격 lint는 이 변경 이후 아직 실행하지 않았다. P130의 과거 lint는
역사적 보존 상태일 뿐 현재 lint 승인으로 바꾸지 않는다. 다음 안전한 통합 검증은 현재
코드의 자원 제한 엄격 lint다. 전체 workspace runtime, 실제 SQL/production trust/atomic publication/
native author·time·state 의미/한글 저장·재열기·렌더링 및 P09 Gate는 미완료다.
