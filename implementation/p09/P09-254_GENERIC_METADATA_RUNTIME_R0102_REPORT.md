# P09 P252~P254 현재 큐 판정 보강과 실제81

2026-10-09. 목표 active. P09·A12·A13 OPEN. PC 프리즈 원인·해결 미확정.

## 수용 경계

- runtime 수용 75/249, 잔여174(일반168+corpus6), 다음index82, 미closing후보0, whole재조정대기72.
- 통과 본문 재실행 없음. 미실행81만 실제 한 번 실행하고 전후 전체1543입력/119204138 bytes와 원 identity·Job·정리 검사를 통해 수용했다.
- test: actual_import::formula_policy_registration::five_foreign_writer_scopes_and_fresh_source_acl_revocation_never_write_policy.
- 다른 writer의 다섯 범위 대체 및 source ACL의 최신 철회가 policy 쓰기로 이어지지 않는 fixed EXE/fixture/repository double 제품 CLI 검사다. 실제 SQL·생산 issuer·한글 UI 인수, 249 전체, P09 Gate 수용이 아니다.
- P239 실제 pre-GO CPU STOP 경계 NOT_RUN. 의도적인 CPU stress를 실행하지 않았다.

## 이번 코드 검토·수정

CPU STOP는 이번 실행에서 발생하지 않았다. 이전 Native20·metadata32·no-burst·원 byte 제한·ancestor 재사용·held byte stream·압력 검사·정리 경로를 유지했다. 새 caller의 판정 오류는 본문 실행 전에 고쳤으며 수용된 과거 코드는 수정하지 않았다.

1. P250/run004는 원 positive test의 고정 수용74와 과거660 fixture를 현재 큐에 적용해 거부했다. 과거204 계약은 원 P23879/기준73 fixture에서 그대로 유지하고 현재156 계약과 새 큐 계약을 분리했다. 새 큐 positive는 이전 수용 수+1을 요구한다. synthetic 다음19도 별도로 검사하지만 다음 실제 본문 수용으로 표시하지 않는다.
2. P252 light001은 392계약 사전 통과로 보존됐다. actual/run002는 이전 세대의 PASS/LIGHT 상수를 사용하는 closed_attempt 때문에 자신의 light 기록을 거부했다. 새 P253의 exact schema·own PASS/LIGHT 검사와 foreign/FAILED 음성 계약을 추가했다.
3. P253 light001은 parent namespace의 packed 과거 receipt를 해석하지 못해 거부했다. 미수용 원 source/test를 SHA/length exact 사본으로 보존한 뒤, 원 packed schema·canonical·unpack을 namespace와 무관하게 적용했다. 내용·schema·pin·cleanup·Gate 판정은 완화하지 않았다.

이 세 실패는 모두 선택/Native/제품 본문 미실행이고 CPU STOP가 아니다. 알려진 literal 실패·정리 witness만 명시적으로 검토하며 다른 실패/CPU STOP/실행 본문 실패의 자동 재시도를 허용하지 않는다. 원 private 자료·실패·기존 수용 코드/테스트·receipt를 보존했다.

## 실제 및 사전 관측

- 수정 사전: 과거204+현재156+현재 큐19+명시적 synthetic 다음19=398 실행 계약. metadata713읽기/261bound=finalfresh/237457697 논리bytes/finished/cleanup/STOP없음.
- 수정 사전254표본: 전체CPUmax23.75%, 자체max5.656445%, private51924992 bytes, 가용RAM최소33.858451%.
- 실제 preparation715읽기/262bound=finalfresh/237563005 논리bytes. 원 parent 후속2읽기를 합쳐 shared717≤720. count/CPU/RAM/IO600초 상한은 그대로다.
- 원 parent253.3초, exact passed1/failed0/ignored0/measured0/filtered248/exit0. Job CPU0.938초/peak private26.28MiB/최종active0/owned_tree_empty.
- 전후1543입력 각119204138 bytes, frame COMMITTED/등록해제. 잠금1849/복제3086 opened=closed, byte identity3086, probe0/경로 재열기0/reader·stream·정리 실패·잔여0.
- Native20회/s/4935예약/no-idle-burst/압력warning0/pause0. 원 EXE1MiB/s·기타2MiB/s·두 실제 전체 읽기·원 identity 유지.
- root931표본: 전체CPUmax89.88%, 자체max5.756039%, 자체 private51769344 bytes(약49.37MiB), 가용RAM최소31.246905%. 원 parent494표본 전체CPUmax86.93%. 두 범위 모두95% 이상 경고표본0/지속98%4연속0.
- 기존 표본만 요약하며 외부 PID·전체 로그를 복제하거나 새 sampler/thread를 실행하지 않는다. 이번 조건에서 중단 없이 완료됐다는 증거이지, 인과적인 CPU 개선률이나 PC 프리즈 해결의 증거가 아니다.

P252 light001에는 전체CPU100%의 단일 표본이 있었지만 지속98%4연속은 아니었다. 당시 경고 자체CPU는0.183824%이고 Job 값은 미관측(null)이다. 외부 원인이나 특정 프로세스를 단정하지 않는다. P253/실제81의 피크와 혼합하지 않는다.

## Exact 증거

상대 기준 implementation/p09/evidence/locked-r07/.

| 증거 | 경계 | bytes / SHA256 |
|---|---|---|
| p251-metadata-entry-status-doc-r0101-run01.v1.json | r101/기준74 | 23578 / f717f7e05dc4ae518e1d27e28c206478bd96a0ca50d340724e1300d1f55f816f |
| p250-admission-run004.v1.json | 고정 fixture/본문 미실행 실패 | 143215 / ac9c1805040421eb945cc3b78cb2577572e9df807312bad20bc7726020e08fb2 |
| p252-light-run001.v1.json | 사전392/제품 아님 | 51782 / fb9487a96565fe301ea371227a2cf5d0734774e71e5cc2f7086fd4487fcc9558 |
| p252-admission-run002.v1.json | own state 거부/본문 미실행 실패 | 142584 / 402074bdc08665425dd86b5293e908857d71633285f28820ef8dfedf73ea6f84 |
| p253-light-run001.v1.json | 과거 packed 해석/본문 미실행 실패 | 142590 / 74b117c05a97b5b3d901cd6cdd6a260069d0edd382650656fd503acaadd7dd23 |
| p253-light-run002.v1.json | 사전398/제품 아님 | 52654 / 251416aca6b7e1bc84771447f51a5e3f9b8cc36fecd8b18181f95daca8295c06 |
| p253-case-081-run003.v1.json | 실제81/수용75/다음82 | 615984 / 22d57ddd87d213c6d41c39c536c5d83e2fec295ea34d110540f5406284b2a246 |
| cases/p253-case-081-run003.json | 원 parent exact1/두 읽기/Job 정리 | 180087 / 52b6c06b1f55c3d92fb95ef63691c9924f9c1673aa912d916a4224c1710df951 |

원 P253 decode 실패 코드의 별도 exact 사본:

- preflight-controller-snapshots/p253-light-run001/resume_generic_metadata_runtime_r2.py: 29024 bytes / 78c53b714a6d629545fa7b54d8725478996b8310345421c1e2e561ddd4ca44e4.
- preflight-controller-snapshots/p253-light-run001/test_generic_metadata_runtime_r2.py: 3690 bytes / 15b91de262ffece4fb79aae6e2244d8a0495014c0bd4b0c5df7f193c0e312686.

별도 사본 상대 기준은 implementation/p09/evidence/다. r101 문서 사본 runtime-progress-r101/도 보존했으며 현재 두 상태 문서는 같은 새 prefix와 exact r101 bytes suffix를 유지한다.

## 후속 범위와 보호

index82 NOT_RUN. 실제81의 preparation715에 새 root/body JSON 각1과 최종fresh 각1(합4), 원 parent 후속2를 더하면 다음 shared721로720 상한 초과가 예상된다. 이는 코드 호출 경로의 예상이지 관측된 STOP나 실제82 실패가 아니다. 무작정 다음 실행을 시작해 실패 증거를 만들지 않는다.

다음은 누적 receipt를 소비하는 중복 호출 검토·최적화다. 원 필요한 첫 byte pin·최종 fresh·전체1543 source/identity와 CPU/RAM/600초 guard를 유지하는 새 caller를 사전 검증한 후 미실행82로 재개한다. 수용 P250/P252/P253 코드는 불변으로 보존한다. CPU 보호 중단 시 자동 재시도 금지; 중단 단계·표본·관련 코드 검토→안전한 최적화·검증→다음 미실행 순서를 유지한다.

P254는 새 문서 상태 snapshot이며 P253의 원 record/parent/frame 검증으로 실제 pair를 소비하고 실행 당시76 controller pins·literal 실패·실패 코드 보존·문서14 계약·최종fresh를 검사한다. 제품이나 전체 source 본문을 재실행하는 문서 검사가 아니다. Git/Review/Cargo/build·원격push·SQL·한글 GUI·접근허용·Defender/WSL/OS 설정 변경 없음.
