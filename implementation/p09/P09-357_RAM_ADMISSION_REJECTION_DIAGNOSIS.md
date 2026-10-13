# P09-357 cursor103 검증·RAM admission 거절 처리 경계

2026-10-10. 목표 ACTIVE. 직전 P356는 실제109 수용으로 진전했다.
이번에는 cursor103/next110의 정식 자격과 fresh를 완료했고, 실제110의 비CPU 보류 원인을
확인하여 엄격한 음성 진단 코드를 구현·검증했다. 제품110은 아직 수용하지 않았다.

## 실제 순서와 결과

첫 가벼운 조회 CPU1%/RAMfree9.66%. 실행 전 원 admission에서는 CPU0.6%, RAMfree10.382602%,
commit42.925372%로 기존 시작 조건을 통과했다. helper import만 공유하는 같은 프로세스에서
light063→fresh064→actual065를 직렬 실행했다. 단계 실패 시 뒤 단계/자동 retry는 없다.

| 단계 | 결과 | 실제 계약 | 준비 fresh/reads/bytes | host max / own max / private max / RAMfree min |
|---|---|---:|---|---|
| light063 | PASS_NEXT_QUEUE_NOT_ACTUAL_OR_GATE | 862=431×2 | 234/472/52829457 | 14.46% / 6.573705% / 96706560bytes / 9.846544% |
| fresh064 | PASS_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT | 0, exact862 재사용 | 235/474/52968069 | 18.32% / 1.858736% / 96206848bytes / 9.815954% |
| actual065 | FAILED_NOT_ACCEPTED | 0, exact862 재사용 | 236/478/53236857 | 26.94% / 2.067669% / 118759424bytes / 9.359135% |

현재 live runtime/test code2는 기존 qualified862 archive와 동일하다. 원 cursor102의 GO를
새 cursor103의 GO로 승격하지 않고 새 현재/합성 다음 위치 검사를 완료했다.
성공한 제품107/108/109는 재실행하지 않았다. PTY90533은 exit1로 종료했다.

## 065의 정확한 원인

root error `TERMINAL_FAILURE_EXACT_STOP_NOT_PASS`, resource_stop_reason null,
stage owned_parent다. CPU 포화·제품 테스트 실패로 재분류하지 않는다.

sidecar 원 parent는 `DEFERRED_NOT_STARTED / DEFERRED_STABLE_RESOURCE_WINDOW`,
operation_phase admission, elapsed3.0초다. 원 여섯 RAM 표본은9.453331~9.790931%로 모두
시작 조건10% 미만이었다. CPU98/commit95/RAM8의 hard STOP과는 구분된다.
worker/job/writer/membership/heavy/product child는 모두 false, source reader passes[],
Job final은 미생성, owned_tree_empty/cleanup true다.

CPU STOP 전용 `terminal_failure_receipt_r2.validate_parent`가 이 정상 RAM admission 보류를
`EXACT_STOP_NOT_PASS`로 거절했다. 원 `review_rejected_parent_diagnostic.Capture`가 거절
원문을 별도 sidecar로 보존했다. CPU-only 처리가 비CPU RAM 보류를 지원하지 않는 경계다.
이는 이번 실행을 막은 원인이며 PC 프리즈의 원인이 입증됐다는 뜻이 아니다.

이미 source Native1966(1658+308)을 획득한 뒤 parent admission에 도달했다.
원1966은 모두 close, 잔여 handle/reader/stream/close failure0, borrower 미생성,
frame CLOSED/unregistered/완전 byte boundary0다. actual adapter는 복구됐고
actual path diagnostics[]다. 원 root/sidecar/0byte placeholder를 그대로 보존했다.
실제 product child false, 수용·큐 진전 없음이다.

## 구현한 엄격한 진단 코드

`tools/p09/qualify_ram_admission_rejection.py`는 exact063/064/065/sidecar를 hash와 크기로
결속하고, 원 RAM 보류·미시작 worker/job·전체 정리·byte 경계 없음·정확한 코드2·기존
자격을 검증한다. CPU STOP/하드 RAM·commit STOP/이미 시작한 작업/잔여 핸들/큐 수용
승격은 거부한다. 결과 `PASS_STRICT_RAM_ADMISSION_DIAGNOSTIC_NOT_RUNTIME_OR_GO`다.

알 수 없는 pre-job metrics는 0으로 만들지 않는다. 실제 미생성 job_final/tests_passed
키를 처음 null 키가 존재하는 것으로 가정해 KeyError가 발생한 진단 후보를 수정했다.
키 생략을 unknown으로 읽되, worker/job 미생성 flags 및 원본 상태를 별도로 필수 검증한다.
원본 필드/상태/실패는 변경하지 않았다.

파일별 최대1MiB, 알려진 pin만 허용, direct-file guard, expected bytes+1 한정 읽기,
SHA 확인 뒤 JSON 해석이다. 커진/다른 파일을 먼저 전체 할당하지 않는다.
최종 모의8 PASS, oversized/foreign input은 open 전에 거부, 실제 literal4개 대조 PASS.
subprocess/thread start를 거부한 작은 검사이며 제품/Native 실행은 없다.

이 새 코드는 **독립 음성 진단만 구현**했으며 현재 main runtime의 재개 경로에 연결하지 않았다.
현재862 검사에 diagnostic8을 더해 새 runtime870 자격이라고 부르지 않는다.
원 CPU-only validator/guard를 넓혀 RAM 보류를 PASS로 만들지 않는다.

## 정확한 증거

- light063:69306bytes/`3a1216d510063794c449a5fc622c46a4bfaadf99b87079ca9359a2de344094c6`
- fresh064:65674bytes/`72be9720d93578ac456412ec2565e24f0999e3a17a41f3b05e9d9da90c734434`
- actual065:461324bytes/`60fd6251f28f09f7ad6dbeb24524d5cb5ca9511cacdb7f0dfbc8d35d00519283`
- sidecar065:12256bytes/`a020fbb8a93f1220e84b3e8aa78d5559d242af755090564b0b413945f682d805`

## 다음 구현 경계와 전체 상태

다음은 엄격한 RAM 보류 분류를 실제 재개 검토에 연결하고, 동일한 RAM 시작 조건을
비싼 Native 획득 전에 확인할 수 있도록 검증 코드를 보완하는 것이다.
원10% 시작/8% 중단·CPU·commit·identity·두 전체 byte·기존 성공 및 실패 증거는 유지한다.
live code를 바꿀 때에는 정확한 과거 qualified862/code2/성공109 및 실패065를 독립적으로
검증하는 epoch 연결이 필요하다. 코드 변경을 과거 자격으로 통과시키거나 original RAM
보류를 CPU STOP/PASS로 바꾸지 않는다. 아직 runtime 연결/새 코드 자격은 NOT_RUN이다.

큐 수용103/249, 잔여146(일반140+corpus6), next110, 성공 body 마감 pending0,
whole재조정100, P09/A12/A13 OPEN, full249/signed16/whole1470 미완료,
문서 final-fresh NOT_RUN, P10 시작0, 목표 ACTIVE다. 특정 큐 수치를 P09 전체 잔여율로 쓰지 않는다.

065 이후 전체 실제 실행 재시도0. UAC/한글/특권Defender 추적/Git/빌드/Defender·OS·WSL
설정 변경/외부 process 종료/삭제·이동0. 이번 검증/진단 세션은 모두 terminal이다.
