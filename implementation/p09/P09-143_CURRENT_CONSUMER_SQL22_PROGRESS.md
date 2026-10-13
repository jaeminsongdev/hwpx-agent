# P09-143 — 현재 원본·서명·consumer SQL22 연결 증거

## 현재 판정과 범위

현재 소스의 main build-r7, test-profile unit-build-r2와 실제 unit-run2, owned DB run05, strict workspace lint-r2를 새 증거로 연결한다. 실제 원본 입력 1개의 Unchanged 결과에서 original source → leased revision/full IR binding → source-derived policy 등록 → 실제 Ed25519 승인 서명 → SQL22 승인 commit/readback → original mandatory consumer가 완료됐다. 원본 및 전체 후보 bytes가 독립 evaluator와 일치하며 fresh consumer 재검증과 head/artifact.ingest 수 불변도 확인했다.

결과는 COMPONENT PASS이다. durable blob storage, production key custody, atomic publication, 실제 scanner, native full fidelity, 한글 저장·재열기·시각 qualification을 완료했다는 뜻이 아니다. P09/A12/A13은 OPEN, product_complete=false, 목표는 active이다. P10 새 구현은 하지 않았다. 원본 corpus 36개 중 현재 연결 증거는 1개이며 전체 corpus 완료를 주장하지 않는다.

## 실제 검증

- Rust typed route unit6: 정확한 Changed/Unchanged RouteUnqualified만 인정. 서명·policy 오류, 분기 불일치, 성공, unknown outcome은 거부한다. 실제 Rust harness는 6 passed/0 failed/0 ignored/0 filtered이다.
- SQL22 run05: original full IR fixture25, original SQL22 checks37, credential metadata42, 원본 서명·consumer 연결18, 스키마 fingerprint 대조2와 최종 history/revocation 수치를 검증했다. 원본 입력은 frozen P77 manifest의 index0이다.
- strict workspace lint-r2: `cargo clippy --workspace --all-targets --locked --offline --jobs 1 -- -D warnings`, workspace32/targets361. compiler-artifact의 package/name/kind 집합과 전체 metadata target 집합을 대조했고 누락·예상 밖 target0, diagnostics0이다. 테스트 및 DB 실행을 lint 증거로 대신하지 않는다.
- 가벼운 source/resource 조건 검사는 별도 source-only 검사이며 Rust/DB/native acceptance와 구분한다.

## 자원 제한과 회수

run05는 43.19초, system CPU 최대17.77%, available RAM 최소16544.65MiB였다. CPU1/BelowNormal, owned PostgreSQL CPU1/RAM512MiB/pids64, loopback-only/no host mounts/read-only rootfs/tmpfs를 유지했다. 전체 source/EXE hash 완료 후에도 CPU≤50%·RAM≥8192MiB 3회 연속 안정 구간을 요구하고 원래 CPU85% 3회/여유 RAM4096MiB 중단 기준을 유지한다. UUID·라벨·image·isolation을 확인한 자기 DB만 회수했고 이름과 ID 모두 부재를 별도 확인했다. 기존 사용자 DB·설정·원본은 변경하지 않았다. 비밀값은 출력·증거 저장하지 않는다.

## 실패 및 역사 보존

run01/run02의 14개 부분 checks와 전체 FAIL_CLOSED, run03의 CPU 중단, 빌드 r1 실패/r4 CPU 중단/r5 시작 전 defer, 이전 resource preflight 결과를 보존한다. run04는 당시 소스로 18개 연결 검사가 통과한 역사적 결과이며 현재 소스 PASS로 재사용하지 않는다. 수정 전 Source/worker/lint runner 전체를 `p09-143-pre-strict-lint-corrections` archive에 보존했다.

strict lint-r1의 실제 실패3은 `unreadable_literal`, `unnecessary_literal_bound`, `items_after_statements`이다. 숫자 리터럴 underscore 표기, 정적 key ID 반환 lifetime, import 위치만 수정했다. 경고 suppress/skip, SQL 권한·schema fingerprint 완화, consumer·Gate 경로 우회는 없다. 기존 typed-route progress와 초기 implementation progress는 historical checkpoint로 그대로 보존하며 overwrite하지 않는다. 새 readonly auditor는 전체 archived preimage, 현재 compiled/runtime/strict-lint 입력과 과거 실패 기록을 분리해 검증한다.

## 다음 실제 작업

Changed 원본 후보를 원래 계산·서명·SQL·consumer 경로로 연결하고, 현재 SQL 기반 live revocation/CAS/race 및 나머지 corpus를 검증한다. 이후 durable storage/custody/atomic publication/native qualification을 원래 P09 요구 범위에 맞게 채워야 한다. coarse 잔여 최소6개/이 단계에서 닫힌 그룹0개는 유지하며 세부 최소30개는 완전한 전수목록이나 완료율로 사용하지 않는다.
