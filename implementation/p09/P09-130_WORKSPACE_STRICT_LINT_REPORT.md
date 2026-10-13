# P09-130 workspace 엄격 lint와 테스트 crate 루트 수정

## 판정

현재 Windows host/default feature 구성에서 32개 workspace 패키지와 358개 대상의
엄격 lint가 통과했다. 실제 테스트/앱/한글/SQL 실행이나 전체 제품 Gate 통과가 아니다.
goal=active, P09_gate=OPEN, product_complete=false, P10 새 구현=false를 유지한다.

## 발견과 수정

최초 `clippy --workspace --all-targets --locked --offline --jobs 1 -- -D warnings`는
114.20초에 exit=101로 종료했다. `review_table_create_context.rs`의 23/40/47/54행에서
crate 루트에 존재하지 않는 `super`를 참조한 E0433 네 건이 관측됐다.
같은 문제가 `table_create_hwpx.rs`의 네 헬퍼에도 있었다.

두 파일 각각 네 곳의 `pub(super) fn`만 `pub(crate) fn`으로 변경했다.
이들은 독립 테스트와 다른 테스트의 하위 모듈에서 함께 쓰이는 테스트 헬퍼이며,
라이브러리의 제품 API나 테스트 본문/검증 조건/데이터는 변경하지 않았다.
대상을 제외하거나 경고 기준을 낮추지 않았다.

두 파일의 완전한 원본은 `implementation/p09/source-archive/p09-130-pre-test-root-visibility/`에 보존했다.
현재 파일의 네 변경을 역변환하면 각 원본과 바이트 단위로 정확히 일치한다.
원본 크기/SHA256은 다음과 같다.

- `crates/hwpx-package/tests/review_table_create_context.rs`: 18535 bytes,
  bcb2f5dd92a7e1b66654b67d4d548002ff675f346563d825c16bf3b75d082b07.
- `crates/hwpx-package/tests/table_create_hwpx.rs`: 28561 bytes,
  e72301a5b231ebeb097d5bf87d0c633ddd360e340ec52fa2aebe016dcb6a689d.

## 실제 lint 증거

- 최초 a 영수증: source freeze 770개 일치, 보호 EXE 6개 일치,
  workspace artifact 251개/고유 대상 223개, E0433 네 건. 실패 상태 그대로 보존.
- 수정 후 b 영수증: 51.72초, exit=0, build-finished success=true, error/warning=0.
  workspace artifact 394개가 실제 Cargo metadata의 고유 358개 대상 전체를 포함한다.
  artifact 중복은 lib/test profile 등이며 대상 개수에 더하지 않는다.
- cargo metadata는 UTF-8로 읽고 전체 대상/소스 경로를 현재 metadata와 정확히 대조한다.
- stdout/stderr, rendered 진단, 소스 본문은 저장/공개하지 않고 진단 code/level/primary span만 보존한다.

## 부하와 보존

CPU affinity=1, BelowNormal, Cargo jobs=1, 2초 sample, CPU 85% 이상 3회 연속,
사용 가능 RAM 4096MiB 미만, 루트 WorkingSet 2048MiB 초과, 시간 제한/관측 실패에서
소유 실행만 중단한다. affinity는 시스템 전체 CPU 사용률 상한이 아니다.

a: CPU 최고 관측 38%, 사용 가능 RAM 최저 14598MiB, 자식 제한 확인 205회.
b: CPU 최고 관측 19%, 사용 가능 RAM 최저 14451MiB, 자식 제한 확인 90회.
루트 WorkingSet은 모든 rustc 자식 메모리 합계가 아니며 관측은 연속 최대값 보장이 아니다.

P129 이전 증거는 두 원본 사본으로만 읽기를 전환한 역사적 source view에서
수정하지 않은 기존 guard를 실행해 재검증했다. 동적 P09 import도 같은 view를 적용하고
검사 종료 시 import factory/loader와 기존 ROOT를 복원한다. cwd와 다른 파일은 실제 경로다.
이를 현재 변경 후의 새 runtime 회귀 통과로 승격하지 않는다.

처음 보존 검사기는 동적 import에 view가 전달되지 않아 fixture_visibility_shape_drift로 실패했다.
그 검사기 전문은 `target/p09-121-resource-optimized/p130-initial-preimage-audit.py.txt`에 보존했다.
인라인 byte-check 호출의 shell quoting 오류는 파일 기반 정확한 역변환 검사로 대체했다.
Cargo metadata의 경로 인코딩 오류도 UTF-8 명시 후 해소했다. 이 실패를 lint 실패나 제품 통과로 바꾸지 않는다.

## 검증과 다음 경계

- `python tools/p09/verify_workspace_lint_progress.py`: 과거 증거, byte inverse, 실제 전체 lint,
  입력/EXE/metadata/원장 대조.
- `python tools/p09/tests/test_workspace_lint_progress.py`: 실제 실패/성공, 불완전 대상,
  낮춘 경고·자원 기준, 원본 추가 변경, 진단 원문 유출 등의 반례 19개 통과.
- `git diff --check`: 통과. 사용자 변경/원본/실패 증거/과거 EXE 보존, PLANS.md 재생성 안 함.
- source graph 1151개 = P129의 1147개에서 기존 두 테스트만 치환 + 새 source/report 네 개.
  inherited raw pin 2869개. 원장: `implementation/p09/evidence/p09-130-workspace-strict-lint.source-progress.v1.json`.

다음은 바뀐 헬퍼를 포함한 table/review integration test의 새 runtime 회귀 및 현재 코드 통합이다.
실제 SQL/production trust/issuer/atomic publication/native 의미/한글·렌더링 qualification은 미완료다.
접근허용/UI/운영 DB/설치/배포/commit/push/삭제/이동은 하지 않았다.
