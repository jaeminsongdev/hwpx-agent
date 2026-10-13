# P09 P238~P240 후속 실행기·원본36 등록 검증·중단 저장 경계 보강

2026-10-09. 목표 active, P09·A12·A13 OPEN, 제품 완료 및 PC 프리즈 원인·해결 미확정.

## 실제 진전

- runtime 수용 73/249, 잔여176(일반170+corpus6), 미closing후보0, 다음index80, whole재조정대기70.
- 새 P238 후속 실행기를 구현했다. 원 P230·P234~P237 수용 코드는 불변이며, 검증된 P236 결합72를 소비한다. 원 78 STOP/FAILED를 삭제하거나 PASS로 바꾸지 않는다.
- 사전 검증156+18 통과 후 미실행 case79를 한 번 실행했다. 제품 본문 재실행 없음. index80 실제 본문은 NOT_RUN이다.
- case79: `actual_import::formula_policy_registration::all_36_locked_originals_register_16_formula_sources_and_reject_20_without_formula_targets` exact1 PASS/248filtered/exit0.
- 이 검사에서 원본36개를 순차 처리하며 수식 대상16개 등록·대상 없는20개 거부를 확인했다. fixed EXE의 제품 CLI test 경로와 fixture/repository double 검사이며 실제 SQL·생산 issuer·한글 UI 인수나 249전체/Gate PASS가 아니다.

## 후속 실행기 불변식

새 runtime 범위는 원1512 + P234/P235/P236/P238 제어 코드8 = 1520입력이다. 실행 전후 각118987330 bytes를 모두 실제 읽으며 한 직렬 borrowed stream, 원 identity 검사, 원 read1MiB/s EXE·2MiB/s 기타, Native32open/s·no-burst, Job hardCPU6.25%/affinity1/BelowNormal·RAM비율 제한, 원 지속98x4/가용RAM/commit/IO600초/본문1200초 보호를 유지한다.

과거 정상 기록은 원 validator로 검증한다. 78번만 literal 실패 pin·완료 본문·별도 전체 source 증거를 P236 strict validator로 결합하며, 같은 본문 반복을 허용하지 않는다. 새 P238 FAILED/STOP/partial/admission 실패는 검사 후에만 재개할 수 있고 자동 재시도·뒤 사례 진행을 차단한다. 정상 parent/root는 원 packed writer, STOP는 정리 후 원 deferred sidecar writer를 사용한다. metadata JSON과 SHA/length 첫 binding의 중복 읽기 제거를 유지하며 마지막 fresh 읽기는 생략하지 않는다.

## 실제 case79 자원·정리 증거

- parent elapsed211.58초, terminal passed1/failed0/ignored0/measured0/filtered248, JobCPU11.266초/peak private26.88MiB/최종활성0.
- 원 두 실제 source byte 경계와 1520입력 일치, frame COMMITTED, 잠금1826·복제3040 모두close, 잔여0, 원 cleanup 확인.
- root preparation209fresh=finished, 논리읽기228907847 bytes, 계약156+18, resource_stop_reason=null.
- metadata 표본754, 전체CPUmax100%, 자체CPUmax4.96592%, 자체 private peak44683264 bytes(약42.61MiB), 가용RAM최소32.382149%. Native pressure warning0/pause0.
- 순간 시스템100%를 프리즈 원인이나 자체 CPU 풀로드로 해석하지 않는다. P240은 기존 표본만으로 null-safe peak 요약을 추가하며 새로운 stress/외부PID 조회/샘플러를 실행하지 않는다.
- 실제 실행 중 별도 제한 확인은 시스템CPU5%, 가용RAM10617MiB/33.32%, commit43%였다. 시점별 값이며 현재·평균·최대값으로 대체하지 않는다.

## 추가 코드 검토·보강 P239

정적 검토에서 original P227 terminal writer가 `borrowed_byte_streams`의 dict를 가정하는 경계를 확인했다. 실제 Frame은 pre-GO 이전 아직 Borrower가 생성되지 않았다면 이 필드를 None으로 보고한다. 이를 측정된0으로 임의 대체하지 않고, 새로운 helper가 다음 witness를 모두 요구하도록 구현했다.

- 상태 DEFERRED_NOT_STARTED, heavy/body 미실행, 원 Job/parent 정리·identity 검증 유지.
- 실제 `frame.held.borrower is None`, reader/boundary 객체0, Native byte identity 검사0, 활성stream/reader0.
- frame CLOSED/등록해제, 소유 잠금의 opened=closed 및 잔여0, probe0, 정리 실패0.
- 이 명시적 미생성 증거로만 logical duplicate 수명 개수가0임을 표현한다. Job/counter의 누락을 측정0으로 표현하지 않는다. 원 document 및 None summary는 변경하지 않는다.
- 정상 Borrower가 존재하면 원 writer로 즉시 위임해 불필요한 추가 frame.summary 전체 복제를 피한다. 원 PASS/생성된 Borrower STOP 경로를 약화하지 않는다. short/partial write는 재시도하지 않는다.

P239 지원계약52=원44+새8은 통과했으나 P239 실제 실행기 연결 NOT_RUN이다. 실제 pre-GO CPU STOP·새 Native frame·제품 실행을 이 지원 검사로 수행하거나 수용하지 않았다. 다음 작업은 해당 새 코드/검사까지 전체 source scope에 묶고 실제 후속 실행기에 연결·검증한 뒤 index80을 진행하는 것이다. 기존 P238 frozen 소스를 고쳐 연결하지 않는다.

## Exact receipts

상대 기준 `implementation/p09/evidence/locked-r07/`.

| 증거 | 결과 | bytes / SHA256 |
|---|---|---|
| `p236-case078-compound-run01.v1.json` | 원 STOP 보존/72수용 anchor | 355396 / `1761365334369863fd3aaf9afc5747456b6a4101dac37cdddbb9e69b3cfbf462` |
| `p237-compound-status-doc-r0098-run01.v1.json` | r98 상태 snapshot | 17363 / `0814a03940aecb2102a3afa85d912ded6f1f3e55d1a1a2bac5c063218e7cedfb` |
| `p238-light-run001.v1.json` | 사전156+18/다음79/제품 미실행 | 45762 / `040d552b8b923a845b9a2672c2a926c8f04201251283f7ccfc7048c883fd8399` |
| `p238-case-079-run002.v1.json` | actual79 수용73/다음80 | 587604 / `a26dbc68b08b95a4b4f124f3e5ccb19377b27c4f8a19e5f88acb802288ad9b31` |
| `cases/p238-case-079-run002.json` | 원 parent exact1/1520 두 읽기 | 172191 / `c443a565cdb0acbca91dd323e4f01f5badc4af93a6a11114a5414c1f50777ad4` |
| `p239-uncreated-borrower-support-run01.v1.json` | 지원52/실제 연결 NOT_RUN | 4694 / `c05d84929932d7b99ec988eaef0137ec53b75869f115ae5e69b625fd83a5cfc4` |
| 원 `p230-case-078-run018.v1.json` | FAILED_NOT_ACCEPTED 그대로 | 885680 / `0f426067907084932489b7bb00425cca017851b726ca2f466dba4777d456ebf1` |
| 원 `cases/p230-failure-078-run018.json` | STOPPED_NOT_ACCEPTED 그대로 | 600156 / `66127715459940855848724d8e918add4f3bad4fa3227a73e804cee5702904db` |

P240는 새 문서 상태 snapshot이며 실제 새 pair를 원 P238 validator로 읽어 검증하고 원r98 byte suffix를 대조한다. 제품/전체 source 재실행·runtime 전체 재검증은 아니다. 새 receipt는 `p240-post-stop-status-doc-r0099-run01.v1.json`에 exclusive-create하며 최종 검증 성공을 앞서 기록하지 않는다.

r98 문서 exact 사본 `implementation/p09/evidence/runtime-progress-r98/`은 no-overwrite로 SHA/length 검증했다. 기존 문서 bytes·기존 수용·원 STOP/0-byte/sidecar·원본은 보존한다. CPU 보호 중단 시 자동 재시도 금지. Gate 상태·프리즈 원인·해결 미확정. P10 새 구현·Git/Review/Cargo/build·접근허용·한글 GUI·SQL·Defender/WSL/OS설정 변경 없음.
