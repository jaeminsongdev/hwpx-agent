# P09-307 내부 metadata90 연결·중복 읽기 최적화 및 102 잠금 STOP

상태: **FULL RUNTIME FAILED_NOT_ACCEPTED / runtime 95/249 유지 / 다음102 / P09·A12·A13 OPEN**.
목표 ACTIVE. 실제 제품 수용·whole1470·full249·signed16·제품 완료·PC 프리즈 해결 증거가 아니다.

## 변경 및 검증 범위

- 새 실행 세대 `tools/p09/resume_completed101_compound_runtime_r2.py` 및 `tools/p09/tests/test_completed101_compound_runtime_r2.py` 생성.
- P304 원 코드/light/실패, P305 원 지원 코드/30계약/실제 작은IO qualification, P302 수용101, P299 원1625 전체 source 증거 모두 변경하지 않았다.
- P305 Reader를 준비 및 기존 monotonic 집계에 연결되는 post Reader에 명시 선택했다. 실제 이번 실행은 post Reader 전 중단됐다.
- 하드 CPU·RAM·IO600 guard 먼저 → 내부 bounded90 → 원95/outer90/entry32 유지. 종료 시 콜백 복원. 새 sampler/thread/Native query 또는 원 guard/시간/읽기 범위 완화 없음.
- 현재 불변 code70을 각각 원 보호 Reader로 읽고, 겹치는 source26/post4 helper 그룹은 **같은 현재 live preparation의 결과에서** 투영한다. 이전 디스크 읽기의 캐시나 역사 pin을 현재 읽기 대신 사용하지 않는다. 중복 호출30만 제거; distinct 현재 pin 전부와 마지막 fresh 전부 재확인한다.
- 원 Native1625 source + 수용 뒤 helper4 + 보존 P304 source/test2 + P305 source/test2 + 새 source/test2 = **1635 입력**, ancestor308/controller168. 제품 전·후 두 전체 byte pass·Native identity·정리 검사는 유지. 이번에는 그 전체 검사가 완료되지 않았다.
- 60 현재 +60 다음 사례 합성 거부/결합 검사 +원 frame/parent30 +leading18 +inner30 = **198 실행 PASS**. 기존1486 불변 qualification은 재사용 증거이지 이번 실행 횟수가 아니다. 합성 테스트는 실제 제품 수용 증거가 아니다.
- 다음 case index102/수용95를 original typed classifier로 다시 계산했다. 본문101·이전 통과 사례 재실행 없음.
- 추가 source/qualification/기록/marker 거부 검사, 원 Job/affinity/CPU/RAM/Native/byte/identity/STOP/중복 수용 거부 검사 유지.

## 증거

| 항목 | bytes | sha256 | 결과 |
|---|---:|---|---|
| `implementation/p09/evidence/locked-r07/p307-light-run001.v1.json` | 28813 | `5346cc9730949df4946e9863aec388dbfa02dda963a0b8cf6e20f986aee27311` | PASS_COMPLETED101_INNER90_ANCHOR_SELECTION_NOT_ACTUAL_OR_GATE |
| `implementation/p09/evidence/locked-r07/p307-case-102-run002.v1.json` | 126223 | `f3fea7070b06517cded460b9738eff4675f47c78e9484d7c313318750d653cce` | FAILED_NOT_ACCEPTED / STOP_SUSTAINED_SYSTEM_CPU |
| `tools/p09/resume_completed101_compound_runtime_r2.py` | 37083 | `6e05d6cac17ccd10ebd3d6800a513cbe138e0ff5a5208154cef7cb619fe3ec63` | frozen code |
| `tools/p09/tests/test_completed101_compound_runtime_r2.py` | 13173 | `ca455c00088c424c650ab6c3ed8ad63f76dd5c038f28f87697777772112778cc` | frozen test |

실행: `python tools/p09/resume_completed101_compound_runtime_r2.py --mode light --run 1` (exit0), 이후 동일 코드 `--mode actual --run 2` (exit1). 실행 세션들은 종료 확인. 원본 보고/영수증을 PASS로 바꾸지 않았다.

Light는 **85 distinct bound/fresh85 /170 read /10369148 bytes**. P304 light는79 distinct/188 read였으며, 이번 세대는 입력6개가 더 있는데도 반복30호출 제거로 총18호출 감소했다. 같은 입력 계획의 모델상 반복 감소이며, CPU 효과나 물리 디스크 IO 효과의 측정값은 아니다. Light 표본19/systemmax17.51%/ownmax5.667669%/private47747072bytes/freeRAMmin25.038476%; 경고대기0이므로 CPU 개선 인과 주장 불가.

Actual 준비는 light 영수증도 재검증하여 **86 bound/fresh86 /172 read /10426774 bytes /finished TRUE**. 내부guard1525회·콜백복원/기존reader/pacer 유지 확인. 이후 Native 획득에서 STOP.
실제 총 source bytes120384676, nominal 예산585.651593초 < 원600초(완료 보증 아님).

## 새 STOP의 정확한 단계와 정리

- failure stage `source_frame_acquire`; selected102; runtime contract198 완료; 수용0.
- source Frame 입력1635로 시작했지만 획득 미완료. 원 lock guard2730번째에서 원600초 한도 중 elapsed23.499998초에 CPU98x4 보호가 작동.
- **실제 Native handle276 open/276 close/remaining0**, metadata276; ancestor walk307; Frame CLOSED/등록해제. cleanup confirmed, close 실패0, active reader0/byte stream0.
- original global rate20 유지, acquire rate14 / reservations276 / acquisition_complete FALSE / 정리시20복원. 같은 original pacer/clock/sleeper/credit/counter 유지, 원 sleep18.875540초.
- borrowed stream summary는 **NULL(아직 생성하지 않은 항목)**; 두 전체 byte pass 및 제품 본문/Job은 시작하지 않았다. byte stream identity0은 실제 계측값; NULL을 0으로 꾸미지 않았다.
- `cases/p307-case-102-run002.json` 없음. parent failure sidecar 없음. 원102 실패를 수용 후보로 승격하지 않으며 source 마감 미완료 후보도0.
- 원 source early90 warning1/window6/sleep3초; Native95 warning0. 기존 조기대기가 이미 Native95 이전에 동작하는 graph다.
- 표본67/systemmax100%/ownmax3.076923%/private47595520bytes/WS58994688bytes/freeRAMmin22.636373%.
- 마지막4 system100%, own CPU0%, logical read delta0. 따라서 이 Python의 직접 CPU 풀로드·대량 RAM 할당이 확인된 것은 아니다. Native 접근이 다른 시스템 작업을 간접 유발했는지, 타 프로세스 부하인지, 원 CPU 샘플의 환경 문제인지는 미확정. 외부 프로세스의 동시 CPU 증거는 없다.

## 이번 STOP 뒤 코드 검토

정확한 traceback/코드 확인:
`locked_runtime_inputs.OpenPacer.reserve` → `PressureInputLocks.open_pressure(self.check)` → `TimedInputLocks.check` → 원 InputLocks.check → original early90 → owner.checkpoint_io → 기존 CPU/RAM/IO guard.
Original `near_saturation_read_backpressure.PressureCheckpoint`는 self.check를 매번 먼저 호출하여 내부 early90도 먼저 적용되며, 원95는 그대로 뒤에서 실행된다. metadata에서 발견했던 선행 순서 결함과 동일하지 않다.

- 원 OpenPacer는 최대64회·sleep≤0.05초·no idle burst. ancestor walk는 이미 방문한 부모에서 멈추고 원307회이며 파일별 중복 전체조상 순회 없음.
- 파일 open/inspect/identity 및 원 체크를 생략하거나 CPU98x4/RAM/600초 기준을 낮출 근거 없음.
- 근거 없이 새로운 대기 wrapper를 겹치거나 rate를 계속 낮추지 않았다. 예를 들어 acquire12/s는 동일 nominal 모델에서 약608.78초가 되어 원600초와 양립하지 않음.
- Native 부분에 추가 코드 결함/정당한 제거 가능 반복을 이번 증거로 특정하지 못했다. CPU STOP 자체를 버그 증명 또는 이번 최적화 성공으로 해석하지 않는다.
- `conservative_maintenance.sample`의 GetSystemTimes 분모는 kernel+user delta, idle을 빼는 기존 계산이며 새 sampler 중복 생성은 없었다. 특정 PC 환경에서 측정 정확도/원인까지 검증된 것은 아니다.

## 현재/다음 경계

런타임 수용95/249, 잔여154(일반148+corpus6), 다음102, whole재조정92, source마감미완료후보0 유지.
P09/A12/A13 OPEN; whole1470/historical67/full249/signed16/product완료/PC프리즈해결 FALSE.
이번 세대 failed namespace의 blind retry 금지. 다음은 이 literal STOP·정리·Native callback review를 바인딩하고 원 전체 범위·보호를 보존하는 새 실행 세대 또는 관련 부하 상관관계의 제한된 진단. 기존 수용 본문 반복 금지.
접근허용/한글/UI/빌드/Cargo/Git/OS설정/Defender/WSL 변경, 삭제·이동·비밀정보·전체 로그 출력은 하지 않았다.
