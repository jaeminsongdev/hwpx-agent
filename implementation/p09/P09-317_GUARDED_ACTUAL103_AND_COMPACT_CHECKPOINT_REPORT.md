# P317~P318: 계약별 보호 실행기 연결, actual103 수용, 반복 metadata 체인 최적화

2026-10-09. 목표 ACTIVE. P09/A12/A13 OPEN.

## 결과와 경계

개별 runtime 수용97/249, 잔여152(일반146 + corpus6), 다음104. whole 재조정94, source 마감 미완료 후보0.

원 수용102, 원103 준비 STOP, P316 마감 STOP, 새 독립 검토 STOP 모두 불변 보존했다. 기존 성공 본문·Native source를 재실행하지 않고 새 actual103을 1회 수행했다. 별도 독립 compact classifier가 96→97을 닫았다.

whole1470/historical67/full249/signed16/product 완료 및 PC 프리즈 해결은 FALSE/미확정이다. 해당 숫자는 P09 전체 완료율이 아니다.

## 구현과 검증

`tools/p09/resume_completed102_guarded_contract_runtime.py` + 해당 test: 수용102와103 실패, P315 helper qualification을 고정 pin으로 바인딩한 새 P317 namespace.

- 각 unittest setUp 전/tearDown 후 및 runner 전후에 기존 Reader checkpoint를 호출한다.
- STOP 시 다음 검사를 시작하지 않고 원 runner를 복원한다. 부분 statistics도 보존한다.
- 현재88 + following88 + 원30 + leading18 + inner30 = 254 실제 검사, 전후 각254 확인, runner5 전후 확인5. helper21/원1486/PerfProc24 재사용을 이번 실행횟수에 합산하지 않았다.
- full1640 + helper/test2 + 새runtime/test2 =1644, ancestor308, controller177. 기존 두 전체 byte/Native identity/Job/CPU98x4/RAM/600/720/cleanup 유지.
- preformal254 및 정식 light254, 독립 light review105fresh/210read PASS. 가정 수정은 formal 실제 실행 전에 했으며 정식 실행 이후 소스·테스트는 불변이다.

## actual103 실제 제품 경로

`python -B tools/p09/resume_completed102_guarded_contract_runtime.py --mode actual --run 2`.

- exit0, 제품 테스트1 PASS/failed0/filtered248. 부모가 보고한265.04초는 전체 source 전후 검사 포함 경과이며 실제 제품 테스트 CPU 시간과 다르다.
- source before/after 각각1644개/120,516,712bytes, exact 전체 pin/identity 확인.
- Native1952open/1952close/잔여0, duplicate3288open/close/offset resets/잔여0, metadata7192, native reservations5240.
- Frame COMMITTED, 등록해제. before_release405.736523초 < 원600초. acquire14 완료 후 원20 복원.
- 원 Job active0/owned[]; CPU4.219초, peak private29.78MiB(물리RAM 약0.09346%). 캡·affinity·capture·owned cleanup은 기존 typed validator로 검증.
- 준비105bound=105finalfresh/210read/13,830,974bytes.
- 원 표본838: system CPU 최대30.1%, own 최대6.470588%, parent private50,171,904bytes, 가용 RAM 최소23.420555%. CPU STOP 없음, watcher 정리 TRUE. own CPU 측정값은 기존 표본의 값이며 Job hard cap 값과 혼동하지 않는다.
- early90 경고 진입/대기0. 고부하에서 냉각 개선이 실증됐다고 주장하지 않는다.

원 root: `evidence/locked-r07/p317-case-103-run002.v1.json`, 646,652bytes, SHA256 `57e2ac01febecd9f718a4b71578722fcf51534d4c5a07c5fd3a8d2e4fa0b13cd`.
본문: `evidence/locked-r07/cases/p317-case-103-run002.json`, 190,979bytes, SHA256 `64a8caed8fa915304f264136f324f50faa11e696f509cd246441553a871aef2c`.

## 별도 CPU 상관 관측

전후 PerfProc snapshot2개, 428.791123초 창, before367/after366/비교356/drift2제외/종료7/새6. Idle-derived busy8.844384%, MsMpEng 평균0.155324%, Git2 평균0%. Python 생성·종료로 endpoint 비교에서 빠진 값을0으로 꾸미지 않는다.

긴 구간 평균은 순간 peak나 프리즈 원인을 증명하지 않는다. 원 guard에 이 counter를 공급하지 않았다. 별도 현재 부모 단일 조회에서는 BelowNormal/affinity1/private약49MB/가용RAM약24%를 확인했으나 역시 순간 진단일 뿐이다.

원 packet: `evidence/locked-r07/p317-actual103-perfproc-before-after-raw-run03.v1.json`, 253,747bytes, SHA256 `78375fa9a4d1b79f60d89e5d88889c8855258224b50eedede85d32be1d0142fd`.

## 독립 검토 STOP와 실제 추가 최적화

첫 독립 검토는 옛 authority 체인 재구성 중85read/85bound/fresh0에서 STOP_SUSTAINED_SYSTEM_CPU, 정리 TRUE로 종료됐다. 실제103 PASS를 바꾸거나 본문을 다시 실행하지 않았다.

불변 실패: `p317-actual103-independent-review-stop-run04.v1.json`, 8,266bytes, SHA256 `4ccbcd692eff9823d93eca7d79b84440d1a0af8c37f9e176dede2b4725f50544`.

새 `review_compact_completed103_anchor.py`는 이미 독립 수용된96의 literal P313 PASS receipt를 qualified boundary로 사용한다. 과거 본문 재실행·옛 전체 metadata 체인 재구성 없이 다음을 검증한다.

- 체크포인트 pin/schema/state/완료/fresh/cleanup/typed96/code77 검증. failed/partial/declared plan은 거부.
- 현재 code81을 각각 live 읽고 마지막에 모두 다시 fresh 확인.
- 원103 root/body 고정 pin, 원1640 입력 전부 불변 + 정확한 새4, 범위1644/controller177.
- 기존 typed runtime classifier로 원254 checkpoint statistics, 두 whole source byte/Native/Job/600/720/cleanup, 단일96→97 검증.
- 원 자료·실패·scope는 보존. 새 review/test2는 metadata qualification이며 원103 Native code81에 포함됐다고 주장하지 않는다.

preformal 초안은 whole1470과 개별 source를 동일 목록으로 가정해 KeyError로 거부됐다. 실패를 보존한 뒤 4개 live 입력의 관계 진단(4fresh/8read)을 했다. 실제로 이전1640과 현재1644의 모든 이전 pin은 같고 새4만 증가했으며 whole manifest의 기존67개 미닫힘은 양쪽에서 동일했다. 이 사실에 맞춰 정확한 이전 범위+새4를 검증하도록 수정했다. 역사67·whole1470을 현재 개별 수용으로 승격하지 않는다.

정식 compact26 동작·거부 계약 + typed103 review PASS. 92bound=92finalfresh/184read/7,095,180bytes, cleanup TRUE/STOP 없음. review system max16.64%, own max5.913978%, private48,041,984bytes.

기존 P317 준비 preview의208read/13,760,250bytes와 compact preview의176read/6,541,070bytes는 서로 다른 진입 경로의 측정이다. 반복 metadata 바이트 감소는 확인했지만 속도·CPU·프리즈 개선 인과를 단정하지 않는다. 제품 자체의 source 두 읽기는 줄이지 않았다.

수용 결과: `p318-compact-checkpoint-actual103-accepted-run02.v1.json`, 71,816bytes, SHA256 `8ad8c1da2fc26e4bd873e0c73b75d7e834fbf66ae519521120f0a993dc791c07`.

## 다음 단계

qualified compact97 및 새 review/test2를 다음 runtime의 전체 source 범위에 연결하고, 새 실행기·test도 포함한 범위/시간 budget/현재·following 검사 후 미수용104를 진행한다. 원 P317 단순 재시도로 최적화를 우회하지 않는다.

CPU 보호 중단 시 정확한 phase/코드/표본/정리 검토 후 정당한 최적화만 한다. 성공 본문 재실행, 실패 PASS 승격, 원 guard·읽기 제외 금지. 접근허용/Hangul/빌드/Git/Defender/WSL/OS 설정 변경·프로세스 종료 없음.

r125 미완료 주의를 포함한 두 문서 전체를 `evidence/runtime-progress-r125/`에 byte-exact 복사했다. r126은 새 prefix 외 그 suffix를 보존한다. 문서 최종 fresh 확인은 별도 결과로 기록한다.

