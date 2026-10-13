# P09-143 — 원본 정책·실제 승인 서명·consumer SQL22 연결 진행

## 현재 판정

`PARTIAL_IMPLEMENTATION_RUNTIME14_CURRENT_OUTCOME_FIX_NOT_RUN`. 전체 제품 목표를 이 구성요소로 축소하지 않는다. P09/A12/A13 OPEN, 제품 false, 목표 active, coarse 잔여 최소6개 그룹/닫힌 그룹0개다. 최소30 세부조건은 전수목록이나 정확한 완료율이 아니다. P10 새 구현은 없다.

## 구현과 실제 실행 증거

새 example은 P77 manifest의 36개 원본 중 고정된 첫 원본 한 개를 bytes/SHA256로 확인하고 RAM에 읽는다. 기존 ArtifactService의 AEAD로 원본·관찰 graph를 보관하고, 기존 scheduler claim → 실제 lease → validating → lease-bound revision commit → success completion 순서를 사용한다. caller AST, 위조 policy record 생성자, job/lease/revision 직접 INSERT는 추가하지 않는다. 원래 SQL21 registrar가 생성 정책을 CAS 등록한 다음 원래 프로비저너가 ephemeral Ed25519 승인 서명·AEAD·SQL22 등록·commit ack·fresh readback을 실행한다.

build-r1은 컴파일 오류로 실패했고 전체 preimage와 receipt를 보존했다. 스레드 안전한 구체적 workflow 오류 타입을 사용하고 이전 worker의 미정의 타입을 제거한 build-r2/r3는 당시 소스에 대해 dev main 빌드를 통과했다. 현재 수정된 소스의 빌드 통과로 승격하지 않는다.

runtime-run01/run02는 원래 full-IR fixture25, SQL22 fixture37, Rust metadata42를 실행했고 새 root·원본 AEAD·실제 lease/revision·원본 생성 정책·실제 승인 서명 등록 재조회까지 14개 checks를 통과했다. 그러나 최종 workflow는 FAIL_CLOSED다. 통과한 단계와 실패한 전체 상태를 모두 보존한다. failed_stage는 `original_mandatory_signature_consumer`이며, run02의 제한된 consumer 오류 표시는 없었다. 현재 소스 검사상 다음 독립 기대값 계산이 이미 정확한 원본의 NoChange를 오류로 처리할 가능성을 확인했다. 이는 새 실행으로 확정한 원인이라고 주장하지 않는다.

## 현재 수정과 미검증 경계

독립 evaluator의 정확한 `FormulaResultOutputError::NoChange`만 원본 전체 bytes로 비교하고 모든 다른 오류는 계속 거부하도록 수정했다. 실제 consumer receipt의 Changed/Unchanged와 독립 evaluator 결과 종류도 일치해야 한다. 기존 signature/source/policy/math/protection 검사는 변경하지 않는다. 오류·미지원 입력 전반을 원본으로 대체하는 fallback은 없다.

이 수정의 build-r4는 전체 CPU 지속 초과로 보호 장치가 중단했고 EXE가 생성되지 않았다. build-r5는 시작 전 CPU99%로 deferred되어 cargo를 시작하지 않았다. 최신 수정의 build/runtime와 전체 workspace strict lint는 NOT_RUN이다. changed 후보, 다른 35개 원본, live revoke/CAS/race consumer negatives, durable blob storage, production key custody, 원자적 publication, native 저장·재열기·시각 acceptance는 이 증거로 qualification하지 않는다.

scanner와 baseline prior/validation receipt는 명시적 synthetic 테스트 구성이다. 실제 관찰 graph를 full native fidelity IR로 주장하지 않는다. blob은 RAM이며 ephemeral 키와 DB 비밀번호를 receipt/소스/로그에 저장하지 않는다. SQL22 root/approval writer, artifact role, worker 역할을 분리하고 worker에 registry direct-table/helper/writer 권한을 주지 않는다. PostgreSQL 스킬의 최소 권한·forced RLS 원칙을 적용했다.

## 자원과 보존

CPU1·BelowNormal·cargo jobs1, CPU85%3회/freeRAM4096MiB/rootWS2048MiB 중단 제한을 유지했다. build-r2는 7.52초, 측정 CPUmax13/freeRAMmin14169MiB다. run01은 14.84초, run02는 15.44초로 종료했다. 최신 r4는 17.96초 중단, r5는 시작하지 않았다. 검증 종료/미시작 상태에서도 CPU 고부하가 관찰되어 Rust 검증만의 원인이라고 단정하지 않는다. 이번 턴은 추가 heavy retry/lint를 실행하지 않는다.

각 DB는 새 UUID·전용 label·고정 cached image, loopback·read-only rootfs/tmpfs·CPU1/RAM512MiB/pids64로 격리했다. 기존 DB와 설정을 변경하지 않았다. 자체 생성 컨테이너 두 개만 exact ID/label/image/isolation 확인 후 제거했다. receipt상 제거와 별도로 ID/name 부재를 현재 확인했다. 전체 preimages 3개 archive, 실패 및 deferred receipt 모두 보존한다. P142 직접 pins29와 기존 EXE42 보호 범위를 다시 대조했다. 현재 동작을 구형 build/runtime에 소급 적용하지 않는다.

가벼운 source-boundary unittest6, 현재 driver AST parse, rustfmt --check, git diff --check는 통과했다. readonly 진행 auditor는 현재 r4 freeze842와 역사적 r1/r2/r3 및 run01/run02 inputs를 current bytes 또는 exact whole preimage에 대조했다. guard6은 소스 경계 검사일 뿐 실제 Rust consumer/DB/native/Gate 실행 증거가 아니다. 과거 전수 verifier graph와 현재 strict workspace lint를 다시 실행했다고 주장하지 않는다.

## 다음 순서

자원 안정 시 새 suffix의 제한 dev main 빌드 → 같은 현재 source freeze로 새 owned SQL22 runtime → Changed/Unchanged와 실제 오류 구분 확인 → 원래 consumer의 변경 후보 및 live denial/CAS/race 검증 → strict workspace lint 및 현재 evidence 갱신 순서다. 그 이후 durable storage/custody/atomic publication/native 경계를 채운다. 한글/접근허용 창은 이번 턴에 띄우지 않았다.
