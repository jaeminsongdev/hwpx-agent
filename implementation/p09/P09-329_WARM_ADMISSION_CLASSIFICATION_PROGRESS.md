# P09-329 — 진입 유예 분류·pre-import 제한·명시적 warm 명령 (2026-10-09)

## 결론과 경계

- 목표 ACTIVE. 권위 있는 개별 제품 수용 **97/249**, 잔여 **152 = regular146 + corpus6**, 다음 **104**, whole 재조정 **94** 그대로.
- P09/A12/A13 OPEN. whole1470/historical67/full249/signed16/제품 완료/PC 프리즈 해결을 주장하지 않는다.
- P329 예열 preformal450 및 정식 light452 계약은 PASS. 독립 P330 fresh 검사는 CPU STOP으로 FAILED_NOT_ACCEPTED이며 fresh/PASS checkpoint로 쓰지 않는다.
- 이번 턴 제품 자식/Native Frame/새 제품 본체 실행은 0. 수용된 제품 본체를 다시 실행하지 않았다.
- 모든 소유 PTY 세션은 정상 종료 또는 GO 전 취소되어 live handle이 남지 않았다. 목표 일시정지/완료 처리 없음.

## 변경한 코드 (현재 Native 자격 없음)

`tools/p09/resume_admission_classified_queue_runtime.py` / `tools/p09/tests/test_admission_classified_queue_runtime.py`.

1. no-work admission defer는 원 error=`DEFERRED_ALREADY_SATURATED_SYSTEM`, resource_stop_reason=NULL 그대로 검토한다. CPU hard STOP과 별도 failure_kind; Reader/계약/선택/Frame/Job/제품 미실행, 원 표본/정리, Gate OPEN이 필수다.
2. heavy helper import 이전 own Python에 허용된 최저 한 코어/BelowNormal 적용·readback. GetCurrentProcess만 사용하며 다른 프로세스를 설정하거나 종료하지 않는다.
3. blocking stdin의 단일 동기 warm 명령. 명시적 light/actual/stop-review/quit whitelist, 64KiB 입력·64 review-pin 제한, 중복 key/unknown key/잘못된 run 거부. 자동 재시도·idle watcher 없음.
4. 첫 light 실패도 metadata-only review가 가능하다. 유예 검토는 light qualification 또는 실제 GO/수용을 대신하지 않는다.
5. qualified warm 코드 pin과 현재 코드가 다르면 선택/GO 전 거부. 명령마다 원 admission/Reader/final-fresh/Native·Job·정리 유지. 불확실한 partial Native/post-product 실패는 session을 닫는다.
6. full1654 = baseline1644 + 추가10; controller187/directory308/code91. 이전 P326 원본 두 파일은 변경하지 않았다. 두 전체 byte/identity 검사·14/20/32 pacing·CPU98x4·RAM 비율·600s·720reads·Job 정책은 불변.

## 실행 결과와 정확한 근거

| 증거 | 실제 결과 | 수용 의미 |
| --- | --- | --- |
| locked-r07/p329-preformal-admission-defer-run01.v1.json | 원 admission 1표본 host100/own0/private29,507,584 bytes, cleanup TRUE, stop=NULL | Reader/계약/제품 미실행; FAILED |
| locked-r07/p329-idle-original-perfproc-counters-run01.v1.json | 제품/검사 없는 원 Windows 3표본 모두100, idle delta0; 별도 PerfProc 진단 창에 MsMpEng 기여 큼 | 동시 동일 창이 아님; 원인/프리즈 해결 입증 아님 |
| locked-r07/p329-warm-preformal450-run02.v1.json | 실제225+225=450; 110bound/110fresh/220read/9,746,542 bytes; cleanup TRUE | 테스트/메타데이터 PASS, Native/제품 PASS 아님 |
| locked-r07/p329-light-run001.v1.json | 현재226+226=452; light PASS·next104·원 guard/정리 유지 | 현 code91 메타데이터 자격만; 실제 제품 미실행 |
| locked-r07/p330-warm-light452-fresh-review-CPU-stop-run01.v1.json | CPU STOP; 65bound/0fresh/66read/2,977,510 bytes, finished FALSE, cleanup TRUE | 독립 마감/자격 FAILED, 본체 재실행 없음 |

Preformal450: 원65표본 host 최대26.46%, own 최대6.470588%, own private 최대47,575,040 bytes, RAM free 최소22.335137%. 이 수치는 **수정 전 preformal450 버전**의 관측이며 P330 또는 실제 제품 결과로 옮겨 쓰지 않는다. 정식452 전 첫 light pin namespace 보완 1계약이 추가됐다.

P330는 원 diagnostic stage 문자열 `p326_light_review`가 template에서 유지되어 있다. 실제 명령/파일은 P329 warm-light 독립 검토다. 최신 중단의 own CPU/RAM 표본은 해당 receipt에 보존되지 않았으므로 숫자를 만들어 채우지 않는다.

P330 proof SHA256 `96a375afd803d549462cefe32248f6dc669d4afc63f867122188dc02e1990e09`는 40자 chunk stdout에서 복원 후 실제 파일 hash와 일치했다. outer process exit0은 semantic 실패를 바꾸지 않는다. 명령·raw stdout은 별도 transport receipt에 보존했다.

Preformal450 raw ConPTY stdout도 별도 receipt에 보존했다. 1,403개의 col80 같은 문자 redraw만 terminal 규칙에 따라 제거했고 mismatch0 후 JSON을 읽었다. 값/표본/상태 대체는 없었다.

## 전·후 버전 보존

- evidence/p329-preformal450-code: 원 preformal source68,967 bytes/SHA75f95b…fe9b, test51,490/SHA654853…e73. 원 reader pin과 동일 bytes/hash 확인.
- evidence/p329-formal452-code: 정식 source68,973/SHAb6f923…e00a, test51,766/SHA1cc4d7…c60f. 현재 파일과 동일 bytes/hash 확인.
- evidence/runtime-progress-r129: 이번 상태 문서 수정 전 전체 두 파일 복사. 기존 기록/실패/원본/산출물을 삭제·이동하지 않았다.

## 중단 뒤 추가 코드 검토 — 다음 구현 항목

**아직 미해결**: 계약 안의 합성 `serve()` 테스트가 모듈 전역 `WARM_EXPECTED_CODE`/`LAST_TERMINAL`을 초기화한다. 첫 light 뒤 actual 계약 실행에 들어가면 바깥 warm 자격이 사라져 이후 재자격이 필요해질 수 있다. 현재 guard는 계약 전 적용되고 실제 GO의 전체 Native 검사는 유지되므로 이를 검사 우회나 실제 제품 PASS로 해석하지 않는다. 이번에 actual은 시작하지 않았다.

다음은 이 전역 상태를 계약 테스트 범위에서 반드시 복원하고, 독립 light fresh 검토도 동일 예열 세션의 별도 원 admission/Reader/final-fresh 명령으로 연결하는 것이다. 반복 cold helper import/불필요한 재자격을 줄이되 현재 소스 검사/원 표본/정리/실패 증거/제품 검증 범위를 약화하지 않는다.

현재 두 controller만 버전 갱신하되 정확한 위 preimage와 원 light receipt를 보존하고, 새 namespace와 이전 메타데이터 자격 재사용 관계를 명시적으로 바인딩하는 방향을 검토한다. **STOP마다 source/controller 수를 자동으로 늘리는 재개는 하지 않는다.** 이전 메타데이터 qualification을 새 Native 자격으로 승격하지 않는다.

Defender/WSL/OS 설정, 외부 프로세스, Git/Review, Cargo/build, 한글/접근 허용은 변경·실행하지 않았다. 같은 P330 마감 명령의 즉시 재시도 없음.
