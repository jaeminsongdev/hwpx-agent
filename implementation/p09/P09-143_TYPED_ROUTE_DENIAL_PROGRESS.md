# P09-143 — 제품 경로 거부 사유의 정확한 판별

## 변경과 목적

원래 `require_current_product_route`의 모든 오류를 `.is_err()`로 통과시키던 probe를 보완했다. 기존 consumer 구현·서명·policy·source·math·protection·SQL 코드는 변경하지 않았다. 원래 오류 enum의 정확한 `RouteUnqualified`만 정상적인 미승인 제품 경로 차단 증거로 인정한다. 서명 거부/권한·policy 거부/드리프트/컴파일 실패/예상 결과 분기 불일치/예상 밖 성공은 이 검사에서 PASS가 아니다.

- Unchanged: `Issuer::Product(Policy::Product(Operation::RouteUnqualified))`만 허용.
- Changed: 원래 compiler/source 출력 경로의 `Issuer::Product(Policy::Product(Operation::Compiler(Compiler::Source(Output::RouteUnqualified))))`만 허용.

이는 제품 경로를 열거나 Gate를 완화하는 변경이 아니다. 실제 정상 consumer 완료를 검증하기 전에는 어떠한 product acceptance도 주장하지 않는다. 독립 evaluator의 정확한 NoChange 구분은 보존하고, 다른 오류의 원본 fallback을 추가하지 않았다.

## 검증 범위

정확한 두 거부 분기, 서명/policy 오류 거부, 결과 분기 불일치 거부, 성공 거부, unknown outcome 거부를 위한 Rust unit6을 추가했다. CPU 고부하 때문에 이 Rust unit의 컴파일·실행, 현재 example 빌드, SQL22 runtime, 전체 workspace strict lint는 NOT_RUN이다.

가벼운 검사15(이전 소스 경계6 + resource 조건6 + 새 route source-shape3), rustfmt --check, git diff --check는 통과했다. source-shape 검사나 포맷 검사로 Rust 타입/실제 consumer 실행 PASS를 대신하지 않는다. 새 readonly auditor는 현재 변경을 제거한 전체 소스가 보존한 이전 전체 preimage와 일치하는지 확인한다. 허용 delta는 원래 call 한 곳, typed classifier, pending unit6뿐이다. 현재 whole Rust input coverage와 기존 EXE42를 확인하되 이전 컴파일 snapshot은 현재 성공으로 승격하지 않는다.

readonly auditor의 첫 실행은 reconstruction에서 unit module을 제거한 뒤 trailing newline을 하나 더 붙이는 오류로 FAIL_CLOSED했다. 초기 auditor 전체와 실패 receipt를 보존하고 추가한 newline만 제거했다. 전체 이전 소스 일치 조건을 유지한 수정 후 audit가 통과했다. 이 감사는 historical 입력과 current source delta 검증이며 runtime PASS가 아니다.

같은 소스·EXE를 여러 historical receipt마다 반복해서 전체 읽기하던 auditor도 최적화했다. 한 번의 audit 안에서 unique 경로의 첫 전체 bytes/SHA256를 재사용하고, 끝에 모든 unique 파일을 독립적으로 다시 전체 hash하여 drift를 거부한다. metadata-only hash 대체나 턴 사이 cache 재사용은 없다. before/after 전체 hash 검증을 유지하면서 동일 EXE·소스의 중복 I/O를 줄인다. 최적화 전 전체 auditor도 보존했다. 이것이 Codex 멈춤의 원인을 해결했다거나 실제 CPU 고부하 원인이었다고 주장하지 않는다.

## 자원과 역사 보존

새 preflight-r2는 20.55초/10회 측정에서 CPU70.78~97.42%, available RAM12572.32~13062.45MiB, 연속 안정0회였다. 판정은 DEFERRED_RESOURCE_PRESSURE_NO_HEAVY_WORK_STARTED이다. cargo/rustc/formula 테스트를 시작하지 않았으며 한글/접근허용/기존 DB·설정 변경도 없다. 반복 heavy retry를 하지 않는다.

변경 전 현재 소스는 `p09-143-pre-typed-route-denial` 전체 archive로 보존했다. 기존 implementation-progress.v1은 당시의 current snapshot으로서 이제 historical이며 overwrite하지 않는다. 새 typed-route progress는 현재 구현과 미실행 경계를 별도로 기록한다. r1 컴파일 실패, 당시 r2/r3 빌드 성공, run01/run02 전체 FAIL_CLOSED/14개 부분 checks, r4 CPU 중단, r5 시작 전 defer, 이전 idle-preflight-r1은 보존한다. P142 직접 pins29 및 기존 EXE42는 유지한다.

## 목표 경계와 다음 순서

P09/A12/A13 OPEN, product false, goal active. 잔여 coarse 최소6개/닫힌 그룹0개이며 세부 최소30은 전수목록이라고 주장하지 않는다. P10 새 구현 없음. 자원 안정 시 fresh 제한 dev build와 Rust typed unit6 → 현재 SQL22 consumer runtime에서 Changed/Unchanged·정확한 route denial 확인 → live revocation/CAS/race 및 변경 후보 → strict workspace lint 순서로 진행한다. 전체 corpus, durable storage, production key custody, atomic publication, native 저장·재열기·시각 qualification을 별도로 채워야 한다.
