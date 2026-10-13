# P09 P212~P214: 독립 compound 수용과 다음 borrowed runtime

2026-10-08. 목표 active. P09/A12/A13 OPEN, product=false, P10 새 구현 없음.

## 결과

1. P208 case012의 원 STOP/FAILED를 보존하고, exact 정상 본문과 P211 전체1480입력
   source frame을 새 P212 compound 스키마로 결합했다. 원 STOP receipt 자체를
   PASS로 변경하지 않았다. 정상 본문 12번을 다시 실행하지 않고 runtime12 수용.
2. P213이 이 큐를 실제로 소비하여 13번을 선택했다. 12계약 및 light PASS 후
   case013 하나만 실행: exact1 PASS / 248 filtered / exit0 / Job cleanup true.
3. case013 입력1484개/306디렉터리, 전후 실제 각118,707,105bytes 일치.
   완료 source frame 뒤의 큐 후처리 오류를 발견했으며 원 receipt/source를 보존했다.
4. P214가 원 정상 부모 및 완료 frame을 각각 원 strict validator로 확인하고,
   후처리 오류를 재현·보존한 별도 새 스키마로 runtime13을 독립 수용했다.
   제품 본문·전체 source frame을 다시 실행하지 않았다.

현재 runtime 수용13/249, 잔여236(일반230+corpus6), 미closing후보0, 다음index14.
이는 P09 전체 완료율이 아니라 고정 r07 EXE의 개별 runtime 사례 진행 상태다.
원 whole 수용3, 전체 성공 본문 중 whole 재조정 대기10(13-3).
기존 legacy-plan의 원 pending field는1로 유지되어 있으며, 통합 pending10과 범위가 다르다.
compiled249=true/full249=false/signed16=false. whole1470·historical67 최신성 및 Gate는 미승격.

## 수용 기준과 보존

P212는 원 parent/state를 조작하여 기존 `CASE_PASS` validator를 통과시키지 않는다.
별도의 compound에서 다음을 모두 요구한다:

- 고정 원 P208 frame/parent와 P211 source frame의 literal bytes/SHA pin.
- 현재 compiled inventory249 이름·동일1470 baseline identity·동일 고정 r07 EXE.
- exact 이름/인자/완료 bounded capture/empty stderr/exit0 및 실제 Job/GO/limit/cleanup.
- 원 실행1473입력 전체 before bytes와 독립 closing1480입력의 실제 두 전체 읽기.
- 원 partial post hash·STOP/FAILED·원 parent counter 미완료를 보존한다.
- 모든 held/duplicate handle 정리, 같은 stream identity, seek(0), 600초/원 pacing/보호 유지.
- 기존1~11 runtime validator/closing을 그대로 재검증하고 이름 중복/기존 미closing을 거부한다.
- 새로운 compound 결과만 runtime 원장에 합친다. 원 whole/전체249/제품/Gate에는 반영하지 않는다.

P212 run01은 원 STOP에서 `tests_passed` 필드가 없는데 직접 읽어 KeyError가 발생했다.
원 C.run은 final source 뒤에 이 필드를 작성하며, 정상 본문 증거는 별도 exact
terminal/capture에 있다. `.get()`로 결측을 보존하고 임의 카운터를 채우지 않도록
수정, 누락/잘못된 nonnull counter 계약을 추가했다. 실패와 수정 전 source를 보존했다.
run02는20계약·metadata bound82=fresh82/finished=true·exit0/stop=null로 PASS다.

## P213 실제 연결 및 발견한 후처리 오류

기존 원 GO/Job/환경/capture/정리 `c.run`을 호출하되, 전후 source reader가
P209 borrowed handle을 사용하도록 연결했다. 원 두 전체 byte 읽기는 그대로다.
원 실행1473입력 + P211제어7 + P212제어2 + P213제어2 =1484입력.

P213 light12계약 PASS. actual case013 결과:

| 항목 | 확인값 |
|---|---|
| 본문 | exact1 PASS/248 filtered/exit0, 원 `PASS_SCOPED_NOT_GATE` |
| source | 전후 각각1484개118,707,105bytes 일치 / frame COMMITTED |
| 실제 Job | cleanup/tree empty true, CPU누적0.266초, peak private23.36MiB |
| 잠금 | 1790개 전부close/잔여0 |
| 복제 | 2968개 전부close/잔여0, seek reset2968회 |
| reader/stream | active0, stream identity2968회, 별도 byte pathname 재열기0 |
| root 준비/본문 receipt | 준비 bound64=fresh64, 본문 metadata bound1=fresh1 |
| 관측 | 원512표본, 시스템 CPUmax34.67%, ownmax1.565558% |
| 메모리 | own private max35,033,088bytes(33.41MiB), RAM 여유 최저45.88174% |
| 보호 | 경고0/CPU·RAM 보호 중단null/정리true |

그 뒤 P213이 `resource_stop_reason` 및 watcher 정리 필드를 finally에서 채우기
전에 `validate_closing`을 호출하여 KeyError가 발생했다. 또 except에서 성공 state를
무효화하지 않아 원 root는 source-frame PASS 문자열과 nonnull error를 동시에 기록했다.
따라서 원 root의 exit0/PASS를 overall runtime/큐 수용의 근거로 사용하지 않는다.
원 runtime_plan도 작성되지 않았다. 원 데이터의 모순을 없애려고 재작성하지 않았다.

P214는 원 literal receipt를 읽어 정상 부모의 strict `validate_parent`와 완료 frame의
strict `validate_closing`을 각각 수행했다. 당시 finalize 전 조건에서 동일 missing
`resource_stop_reason`을 재현했다. 원 error 및 overall 미수용을 명시하고, 별도
새 pair receipt에서만 runtime13/next14를 계산했다. 원 parent가 nonzero/STOP,
capture 미완료, 입력 subset, byte/identity 불일치, cleanup 실패, resource stop이면 거부한다.

P21414계약 PASS, 새 metadata bound25=fresh25/finished=true, exit0/stop=null.
신규 지원 계약은 P21220 + P21312 + P21414 =46개다. 기존 제품246계약과 구분한다.

향후 실행 진입점은 모든 검증·큐 계산·정리 필드를 채운 다음 최종 성공 state를
작성해야 한다. 예외는 반드시 overall FAIL로 내려야 하며 component PASS와 구분한다.
P213의 원 코드/실제 성공 body를 수정·재실행하여 오류를 숨기지 않는다.

## 증거 pin

경로 기준: `implementation/p09/evidence/locked-r07/`.

| 파일 | bytes | SHA256 |
|---|---:|---|
| `p212-case-012-compound-run02.v1.json` |124287|`e3659306fa6daa34531be0049a18117265124ef3509cbb44e79a2ebd9df3837d`|
| `p213-borrowed-frame-light-run01.v1.json` |35518|`9dbf66cee2a1d4fe98d8dc4ae23d8a08f1472cce10f1e0fa7b4ac7c440cdfe33`|
| `cases/p213-case-013-run01.json` |789210|`425791485d0d79724b50f345f05619e0b3c29b2ad6dbf196931dbbe470a2a928`|
| `p213-borrowed-frame-actual-run01.v1.json` |1312117|`48a9f05f2e37c6d9334ec65553bd2581f652e38f4b6385082dffbe38fae54126`|
| `p214-case-013-pair-closing-run01.v1.json` |34085|`a05a85a61a7caffe91c8c3bf7fa8b5934c9d67c4c6d6d296fbeff56dd67edfaa`|

원 source 보존은 `p212-missing-terminal-counter-preimage/`와
`p213-premature-finalization-preimage/`. 원 r77 문서 bytes는 `runtime-progress-r77/`에 보존했다.
원 P208/P211/P212/P213 receipt·원 실행 코드·EXE·Rust source는 재작성하지 않았다.

## 次の境界

- 14번 이후를 통합된 runtime13 원장에서 선택하는 범용 계속 실행 진입점을 구현·검증한다.
- 통과한1~13번을 재실행하지 않고 같은 정상 부모/live frame/입력 두 읽기/원 보호를 유지한다.
- P213 후처리 오류를 overall PASS로 다루지 않는다. component/queue/final state를 분리한다.
- CPU 보호 중단 시 재시도 전에 새로운 중단 구간을 검토·최적화한다.
- 미지원 corpus6/whole/Gate의 전제는 별도 확인하고, 접근허용은 지금 발생시키지 않는다.

이번 접근허용/Git/Cargo/build/SQL/Hangul/OS 변경 없음. PC 프리즈 원인·해결은 미확정이다.
