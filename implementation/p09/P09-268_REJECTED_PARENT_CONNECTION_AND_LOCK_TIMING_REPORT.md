# P268 실패 parent 연결 / 원 잠금 시간 계측

2026-10-09. 현재 runtime 수용87/249, 잔여162(일반156+corpus6), 다음index94.
P09·A12·A13 OPEN. 원600초·CPU/RAM 기준은 변경하지 않음. PC 프리즈 원인·해결 미확정.

현재94 실패는 수용하지 않고, 92/93의 통과 본체도 재실행하지 않는다. 실제 full runtime 연결 NOT_RUN.
P268 qualification 완료 여부는 `evidence/locked-r07/p268-rejected-parent-connection-run01.v1.json`의 실제 state로 판단한다. 파일이 없거나 FAILED면 완료가 아니다.

## 코드 검토와 변경

- 94번 Rust 본체는 단일 fixture/정해진 revoke·callback 검증이다. 해당 함수에서 무제한 반복·스레드 fan-out은 확인하지 못했다. 실행 결과가 유실되었으므로 PASS나 중단 사유를 추정하지 않는다.
- 기존 입력 경로는 조상 캐시, 동일 stream handle identity, 단일 owner 직렬 Borrower, Native20/s·metadata32/s·byte1/2MiB/s와 원600초 보호를 사용한다. 원 reader의 link/path/metadata guard는 보안·identity 조건이므로 제거하지 않는다.
- `ParentConnection`은 원 `p.run_parent`를 그대로 호출하면서 P267 Capture를 명시 연결한다. 예외 후에도 caller가 Capture를 소유한다. 원 오류는 다시 발생시키며 PASS/CPU STOP writer를 바꾸지 않는다. 동일 connection의 두 번째 parent 호출은 금지한다.
- `TimedInputLocks`는 원 lower-native instance를 상속한다. 매 check에서 원 보호 함수를 호출하고, 다섯 구간 경계/첫 예외에서만 추가 시계를 읽는다. Native600초 시작점·제한을 새로 만들거나 연장하지 않는다. CPU/RAM query·Native query·sample·thread는 추가하지 않는다. 원 오류 코드/elapsed/phase를 bounded 진단으로 남기고, 미측정 시간은 None을 유지한다. cleanup에 checkpoint/pressure를 추가하지 않는다.

## qualification 범위와 방법

신규28개 예비 계약은 통과했다. 최종 qualification은 원 P26752개를 유지하여 총80개, P267 receipt/helper의 exact SHA·길이, 기존92/93 strict pair 재계산, 원94 실패·0byte 보존, 모든 metadata bound input final fresh를 원720읽기/600초 watcher 아래 확인한다.

실제 Native probe는 새 helper/test와 불변 P267 helper의 **작은3파일**만 사용한다. 원 parent bridge의 `pins` 호출 두 번을 실제 Frame.read_boundary에 연결하여 전후 byte 읽기/identity/offset reset을 유지한다. 예상 잠금7/duplicate6/Native reservations13, 모두 close/잔여0; 추가 held identity 검사도 원 API로 수행한다.

제품 `ORIGINAL_RUN`은 합성 함수로 대체하며 실제 제품 EXE/Job/Cargo/SQL/Hangul은 실행하지 않는다. 합성 원 parent가 `OWNED_RUNNER_FAILURE`를 기록할 때 CPU 전용 원 validator의 거절이 그대로 발생하고, live stream은 비어 있으며, caller의 Capture 참조는 유지돼야 한다. 이 작은 probe는 실제94의 소실된 Job·본체 결과를 복원하지 않는다. 원 Job 미측정 값은 None이다.

owner 종료와 CLOSED/unregistered frame 이후 별도 `cases/p268-rejected-parent-probe-run01.json`에 bounded diagnostic-only envelope를 exclusive-create로 한 번만 기록한다. 이 파일은 **작은 실제 Native + 합성 parent** 증거이지 현재 실제94 runtime 증거가 아니다. 원 실패94 root와0byte 파일은 그대로 보존한다.

따라서 P268 PASS는 작은 Native/합성 원 parent 연결의 qualification뿐이다. 전체1563+후속controller 범위와 실제 parent 실행기는 별도 immutable 세대/사전검증이 필요하다. 그 검증 전 94 자동 재실행·95 건너뛰기·Gate 승격은 하지 않는다.

## 원 증거

- P267 receipt160731bytes: `b0e307c3548c41f843565d87bdfa9a073dc47fd8c722883c875ba332e0afc06d`
- 원94 root1345290bytes: `c347fd3df25cd2b4d52db6f8c27e6325c039f803ab0987f8e0902ac9005f31f9`
- 원94 placeholder0bytes: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

유실된 원 parent reason을 deadline으로 단정하지 않는다. 이 변경의 시간·CPU 개선 효과는 아직 측정·확정하지 않았으며 PC 프리즈 해결도 입증되지 않았다.
