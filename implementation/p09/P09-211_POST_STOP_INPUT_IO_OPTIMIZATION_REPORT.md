# P09 P208~P211: post-source CPU 중단 검토와 입력 IO 최적화

2026-10-08. 목표 active. P09/A12/A13 OPEN. P10 새 구현 없음.

## 결론과 수용 경계

원 P208 case012 제품 본문은 exact 1 PASS / 248 filtered / exit 0로 끝났으나,
그 후 두 번째 전체 source hash의 EXE 읽기 도중 CPU 보호가 작동했다.
원 parent `STOPPED_NOT_ACCEPTED` 및 frame `FAILED_NOT_ACCEPTED`는 변경하지 않았다.
제품 본문은 재실행하지 않았다. P210 조사에서 semantic 후보 1개로만 확인했다.

새 P209 borrowed stream을 사용한 P211 전체 current-source frame은 PASS다.
원 1473입력에 새 제어 코드 7개를 더한 1480입력/306디렉터리,
각 118,680,486bytes를 실제로 두 번 읽고 동일 byte pin을 확인했다.
독립 source frame의 PASS는 원 runtime receipt를 자동 승격하지 않는다.

- runtime 수용 11/249, 잔여 238(일반232+corpus6) 유지.
- 원 runtime 큐의 미closing 후보 0과 별도로, P208 semantic 후보 case012 1개 존재.
- 다음 제품 본문 실행 전에 이 후보와 current-source frame의 독립 수용/큐 연결을 검토한다.
- 성공한 본문 1~12 재실행 금지. 단, case012는 runtime 수용된 12번째 사례가 아니다.
- 원 whole 수용3/미확인 성공8, compiled249=true/full249=false/signed16=false 유지.
- 프리즈 원인 및 해결은 미확정. 검증을 약화하거나 OS/Defender/WSL 설정을 바꾸지 않았다.

## 원 CPU 중단의 구체적 구간

| 항목 | 원 P208 증거 |
|---|---|
| 제품 | exact 1 PASS/248 filtered/exit0, bounded complete capture |
| 중단 phase | `final_source_freeze` / `final_fresh_hash` |
| 첫 전체 읽기 | 1473입력 / 118,633,094bytes 완료 |
| 두 번째 읽기 | 1362회 / 112,470,052bytes에서 중단 |
| 중단 파일 | 고정 r07 EXE, 두 번째 읽기에서 12,779,520bytes까지 진행 |
| owned Job | 마지막 고온 표본에서 active0 / Job CPU0, 최종 cleanup/tree empty true |
| 제품 Job 비용 | CPU누적0.172초 / peak private20.97MiB |
| frame 정리 | 잠금1779개 모두 close / 잔여0 |
| host / 검증 프로세스 | host100% / own max0.790514%, 마지막 고온 표본 own0% |
| 메모리 | own private max41,959,424bytes / RAM 여유 최저33.066% |

이 구간에서 제품 본문의 CPU 폭주를 입증하지 못했다. 파일 IO의 간접 영향,
백그라운드·보안 필터·커널 부하는 아직 분리하지 못했으며 Defender 원인으로 단정하지 않는다.

## 코드 검토와 구현

| 경로 | 검토 결과 / 조치 |
|---|---|
| byte stream 생성 | 이미 READ로 잠근 파일을 매회 pathname으로 다시 열던 부분을 동일 프로세스 `DuplicateHandle` 기반 stream으로 대체 |
| 중복 metadata | 복제 후 사전 조회를 없애고, 원 P206 `verify_stream`의 읽기 직전 파일 ID/크기/비상속 검사를 유지 |
| 소유권 전환 | Win32 handle → CRT descriptor → Python stream 단계별로 정확히 해당 소유 자원만 정리 |
| 복제 위치/상속 | 공유 file position은 매회 seek(0), 단일 owner/thread·단일 직렬 stream; HANDLE 비상속 및 descriptor `O_NOINHERIT` |
| reader 수명 | 원 wrapper가 없는 직접 읽기, 중첩 binding/stream, 지난 binding의 source facade, 사용 중 close를 거부 |
| close 실패 | 실패한 복제 자원을 추적하고 나머지 원 잠금 정리를 계속 시도. 실패 이력이 있으면 재사용/정상 수용 차단 |
| 출력/정리/worker | 기존 bounded32KiB capture·GO 후 Job 실행·CPU/메모리 limit·Job 종료·전체 handle 정리를 유지; Cargo/Git fan-out 없음 |
| sampler/누적 counter | 원 수동 .5초 표본과 전후 누적 counter 사용, 새 sampler thread·외부 PID 반복 조회 없음 |
| 원 입력/검증 | 전후 전체 실제 byte 읽기2회, 원 hash/fixture 범위, binary1/other2MiB/s 및 stream32/s pacing 유지 |
| 중복 실행 | P208 기존 시도 존재 시 재실행 차단 유지. P210은 본문 통과와 source 미완료를 분리하며 runtime_accepted=false 반환 |

P211 source scope에서 byte stream용 pathname 재열기 2960회를 제거했다.
원 잠금 취득의 pathname open1786회와 byte stream 복제2960회는 남는다.
`open_reservations=4746`은 기존 pacing 예약 수이며 CreateFile 실행 횟수가 아니다.
원 `_source` 파일/link 검사와 held metadata 확인도 남아 있다. 모든 파일 IO가 없어졌다는 뜻이 아니다.

구현: `borrowed_locked_streams.py`, `probe_borrowed_locked_streams.py`,
`review_post_stop_frame.py`, `close_borrowed_source_frame.py`와 해당 테스트.
원 P206/P207/P208 구현·원 제품 EXE·Rust 소스·실패 receipt는 수정하지 않았다.

## 검증

새 계약은 P209 24 + P210 12 + P211 10 = 46개. child/thread 생성 차단하에 PASS.
P208 frame/bridge30은 이전 원 증거에 보존되어 있다. 제품246계약과 보조 계약은 구분한다.

P209 첫 probe는 통합 mock의 크기 identity 불일치로 FAILED_NOT_ACCEPTED였다.
fixture와 테스트 기대 오류를 수정했으며 실패 receipt 및 수정 전 source를 보존했다.
run02 작은 실제 Native PASS 후 중복 metadata 조회를 더 제거하고 source를 보존한 뒤
run03을 실행했다. 최신 run03: 입력4/잠금9/복제8, 두 실제 읽기 및 전수 정리 PASS.

P210: 고정 원 frame/parent receipt를 새 byte로 읽고 최종 fresh 확인4/4,
semantic 후보 조사12계약 PASS. 원 실패 상태·partial post hash·P09 OPEN 보존.

P211 actual run01:

- `PASS_FULL_BORROWED_CURRENT_SOURCE_FRAME_NOT_RUNTIME_WHOLE_OR_GATE`, exit0/stop=null.
- 전체1480입력/306디렉터리, 두 번 각118,680,486bytes.
- READ 잠금1786/close1786/잔여0, 복제2960/close2960/잔여0, 위치 초기화2960회.
- 원 stream identity2960회, held identity 검증, active reader/stream0, close 실패0.
- metadata6532회, ancestor traversal305회. probe 없음.
- 준비 reader20회/5,571,011bytes, bound9=fresh9/finished=true.
- 원 .5초 관측494개: 시스템 CPU max51.33%, own max0.587084%.
- own private max34,357,248bytes(32.77MiB), RAM 여유 최저34.04764%.
- 경고 진입0/보호 중단null/전체 cleanup true. 제품 child·Cargo·Git·SQL·한글·접근허용 없음.

원 P208과 이번 P211은 시간·백그라운드 상태·제품 실행 유무가 다르다.
위 CPU 수치를 통제된 성능 개선율 또는 프리즈 해결 증거로 해석하지 않는다.

## 증거 pin

| 상대 경로 (`implementation/p09/evidence/locked-r07/`) | bytes | SHA256 |
|---|---:|---|
| `p208-frame-actual-run01.v1.json` | 1043780 | `01818f2b948d46e2f25b1ea4ad47bbd78ab18f2e6f53480fc2766e2bf565dbe2` |
| `cases/p208-case-012-run01.json` | 781629 | `be515561752ee9cf873a1b3c959d99a1d70da0d7c5d2b20cc66f2fed91df0199` |
| `p209-borrowed-stream-probe-run03.v1.json` | 9211 | `408e1a943fab183ee22aae4654fda223d492b213f3830ea86467a93682b2dd6a` |
| `p210-post-stop-review-run01.v1.json` | 11713 | `d41d0734897a616fa97f0497a8cf04a03f99b8fb6f6381785e02c8a314a9620d` |
| `p211-borrowed-source-frame-run01.v1.json` | 1281951 | `1f5d45554d2d6c288b5dc602761ffcebc7d15ee1b8be33784e7df0b5e54d8c51` |

수정 전 source: `p209-contract-fixture-failure-preimage/`,
`p209-small-native-run02-preimage/`. 이전 두 진행 문서의 byte 보존:
`runtime-progress-r76/`. 삭제/이동 없음.

## 앞으로 CPU 보호 중단 시 진행 규칙

1. 원 중단 receipt, 실행 단계, 마지막 완료/중단 입력, 정상 terminal 여부, 정리를 먼저 확정한다.
2. 동일 검증을 자동 재시도하지 않는다. 관련 읽기/open/import/작업 fan-out/메모리 수명/정리 코드를 검토한다.
3. 근거 있는 최적화는 source preimage와 실패를 보존한 뒤 구현한다. unrelated OS 설정은 바꾸지 않는다.
4. 예외·소유권·중단 계약 → 작은 실제 API 확인 → 필요한 전체 경로 확인 순서로 진행한다.
5. 통과 본문은 재실행하지 않고 남은 source closing/수용 연결부터 처리한다. 미통과는 통과로 바꾸지 않는다.
6. 재중단 시 새 구간을 다시 검토한다. 검증 범위 제외·보호 기준 완화·원인 없는 단순 재시도는 하지 않는다.

다음 목표 단계는 case012 원 semantic 증거와 P211 source frame을 함께 검토하는
명시적 독립 수용/큐 연결이다. 현재는 NOT_RUN이며 runtime12/P09 완료를 선언하지 않는다.

## API 근거

- [Microsoft DuplicateHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle)
- [Microsoft _open_osfhandle ownership](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/open-osfhandle?view=msvc-170)
- [Python msvcrt flags](https://docs.python.org/3/library/msvcrt.html#msvcrt.open_osfhandle)
