# P10 — Windows Hancom Automation Bridge

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P03`

## 목표

Windows Hancom Automation Bridge를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (10개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P10-01` | Protocol | Rust↔Agent gRPC와 Agent↔STA named-pipe protobuf를 정의한다. | `proto v1/generated SDK` | compatibility test |
| `P10-02` | Windows Agent | job lease, artifact staging, sandbox, upload를 구현한다. | `agent service` | lease/fencing E2E |
| `P10-03` | STA worker | C#/.NET message pump와 command loop를 구현한다. | `STA worker` | COM apartment tests |
| `P10-04` | HwpObject lifecycle | create/open/close/quit/process ownership을 구현한다. | `HancomSession` | leak/crash tests |
| `P10-05` | Security module | file path approval와 safe open policy를 연결한다. | `security adapter` | allowed/denied path tests |
| `P10-06` | Binding executor | signed allowlist와 typed ParameterSet을 실행한다. | `executor` | unknown/raw action rejection |
| `P10-07` | Event/modal watchdog | events, expected/unknown dialog, screenshot metadata를 구현한다. | `watchdog` | unknown modal fail-closed |
| `P10-08` | Isolation | interactive desktop/user/VM, network/clipboard/temp 정책을 구현한다. | `worker image/runbook` | residue/isolation audit |
| `P10-09` | Timeout/recycle | cancel, unknown outcome reconciliation, process recycle을 구현한다. | `supervisor` | hang/retry/no duplicate effect |
| `P10-10` | Runtime probe | target build health/capability report를 registry에 공급한다. | `probe agent` | profile mismatch no lease |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [x] `P10-01` 산출물 `proto v1/generated SDK` 존재, 검증: compatibility test.
- [x] `P10-02` 산출물 `agent service` 존재, 검증: lease/fencing E2E.
- [x] `P10-03` 산출물 `STA worker` 존재, 검증: COM apartment tests.
- [x] `P10-04` 산출물 `HancomSession` 존재, 검증: leak/crash tests.
- [ ] `P10-05` 산출물 `security adapter` 존재, 검증: allowed/denied path tests.
- [ ] `P10-06` 산출물 `executor` 존재, 검증: unknown/raw action rejection.
- [x] `P10-07` 산출물 `watchdog` 존재, 검증: unknown modal fail-closed.
- [ ] `P10-08` 산출물 `worker image/runbook` 존재, 검증: residue/isolation audit.
- [ ] `P10-09` 산출물 `supervisor` 존재, 검증: hang/retry/no duplicate effect.
- [ ] `P10-10` 산출물 `probe agent` 존재, 검증: profile mismatch no lease.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

현재-PC 개발용 P10-08 core와 실제 감사는 완료됐지만, 실제 감사에서 OS outbound deny,
전용 identity/profile/window station, clipboard 격리와 profile/recovery/printer residue 감사가
미충족으로 확인됐다. 따라서 위 P10-08 hard-gate checkbox는 전용 환경 증거 전까지 열어 둔다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
