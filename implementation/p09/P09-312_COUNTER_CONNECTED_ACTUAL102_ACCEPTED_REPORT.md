# P09-312 관측 코드 full-scope 연결 및 실제102 수용

상태: **runtime96/249·다음103·잔여153(일반147+corpus6)**.
P09/A12/A13 OPEN. 목표 ACTIVE. whole1470/historical67/full249/signed16/제품 완료/PC 프리즈 해결은 미증명이다.

## 이번 변경·검증

- 새 `tools/p09/resume_completed101_compound_runtime_r3.py`와 `tools/p09/tests/test_completed101_compound_runtime_r3.py` 생성.
- 기존 수용101·P299 source·P304/P307 CPU STOP·P309 idle 실패/지원PASS·P310 24계약/실제2query·P311 원장 영수증은 불변 보존.
- 원P307 Native276close/잔여0/본문 미시작을 typed 실패 조건으로 바인딩했다. 실패를 PASS로 분류하지 않는다.
- 신규 current76/following76 +원frame/parent30 +leading18 +inner30 = **230 실행 PASS**.
- 원1486/PerfProc24는 불변 code/qualification 재사용 증거이며 이번230에 합산하지 않았다.
- P310 diagnostic source/test/PS collector와 보존 P307 source/test, 새 source/test를 필수 source 범위로 포함했다.
- 원1625 +수용후 helper/보존/새15 = **1640 입력**, ancestor308/controller173, **120455622 bytes**.
- 원 hard guard→inner90→원95/outer90/entry32, source early90, original acquire14→global20, no-burst/read1·2MiB/720/600/Job/정리 유지.
- 원 현재 live distinct pin 투영 및 마지막 fresh 유지. source/identity/원본/사례/byte 제외 없음.

새 case102 명칭:
`actual_import::formula_product_request::identity_mismatches_and_advanced_head_deny_original_provider_before_formula_preparation`.
원 stored-result product 경로에서 identity 대체와 head advance를 formula preparation 전에 거부하는 실제 compiled249 테스트 1개다.
다른 제품 기능이나 P09 전체 수용을 대신하지 않는다.

## 시작 전 유예와 scoped cache-write 개선

원 light230 PASS 뒤 영수증 재검토의 `owner.admit`에서
`DEFERRED_ALREADY_SATURATED_SYSTEM`이 나왔다. Reader/actual102/Native 시작 전이었다.
표본이 반환되지 않았으므로 해당 순간 CPU 숫자/Native 측정값을 꾸미지 않았다.
기록: `p312-light-review-admission-deferred-run01.v1.json`. 원 원본을 보존했다.

그 뒤 Native가 없는 별도 PerfProc2query/3.177356초 창에서는 host busy19.873680%,
MsMpEng5.440107%, Git2 CPU0%, 관측 가능한 기존 python0%였다.
유예 순간과 다른 창이고 다른 작업도 포함돼서 원인 배제/확정 불가.
외부 프로젝트/app/프로세스를 변경하거나 종료하지 않았다.

새 검사 모듈의 `.pyc` 생성이 확인되어 이후 부모 검증 실행에 **`python -B`**를 선택했다.
새 비필수 bytecode cache 쓰기를 막는 실행 옵션만 변경; 기존 cache 삭제/OS환경 설정/제품 source 변경 없음.
light/code 검토에서 `sys.dont_write_bytecode=True`를 확인하고 같은 코드/pin을 사용했다.
자식 worker 전체까지 `-B`가 자동 전달됐다고 주장하지 않는다.
이번 성공을 cache write 차단의 효과나 이전 CPU 원인 증명으로 해석하지 않는다.

## 실제 실행 및 독립 수용 재계산

명령: `python -B tools/p09/resume_completed101_compound_runtime_r3.py --mode actual --run 2`.
동기 실행 전후 읽기 전용 PerfProc 조회2개를 바깥 실행기에서 수집.
이 값은 original runtime sampler/STOP 결정에 공급하지 않았고 단위/제품 수용에도 사용하지 않았다.
실행 세션 종료·exit0 확인, body terminal PASS1/exit0, source frame COMMITTED/등록해제, 원 Job empty.

독립 protected metadata Reader에서 원95 plan을 다시 계산한 뒤
새 immutable root/body/frozen scope/원 typed record를 결합하여 **96·next103·remaining153 단일 전진**을 재계산했다.
제품 본문 또는 Native 전체 검사를 재실행하지 않았다. 원102를 중복 수용하지 않았다.

| 항목 | 실제 결과 |
|---|---|
| preparation | 96 bound/fresh96, 192 read, 11614530 bytes, finished TRUE |
| 본문 terminal | passed1/failed0/ignored0/measured0/filtered248; exit0 |
| 두 원 전체 byte pass | 각각1640 read /120455622 bytes |
| Native lock |1948 open/1948 close/remaining0|
| borrowed duplicate |3280 open/3280 close/remaining0; offset reset3280|
| metadata / reservation |7176 /5228|
| acquisition |14/s로1948 획득 완료, 원20/s복원|
| held frame |COMMITTED, registry에서 해제|
| before_release |408.663468초, 원600초 이내|
| Job |active0/owned[]; CPU2.266초; peak private29.14MiB|
| capture |complete streams, error 없음, perstream32768bytes, raw log 저장 없음|
| resource |STOP 없음, watcher cleanup TRUE|
| source early90 |warning2 /bounded windows6 /sleep3초|

원 nominal 예산586.576396초는 예측일 뿐 수용 증거가 아니다. 실제408.663468초를 별도로 기록했다.
own guard calls58598은 원 바이트·Native·deadline 호출을 유지한 실제 계측이다.

## 자원 관측과 해석 한계

original runtime 표본823:
system CPU 최고95.58%, own 최고5.823646%, private50794496bytes,
working set62570496bytes, free RAM 최소21.202480%.
이번 실행에서는 CPU98x4 중단이 발생하지 않았다. 물리 PC 전체 프리즈가 해결됐다는 주장은 아니다.

별도 PerfProc 전후430.337345초 창:
before371/after364, compared356, drift2 제외/종료11/새4.
host busy(Idle 기준)9.119717%, MsMpEng 평균0.340394%, Git2 평균0%.
이는 **긴 구간 평균**이며 순간95.58% 표본과 동일한 수치/범위가 아니다.
종료·새·instance drift 프로세스가 제외되므로 순간 최고 부하 원인을 찾았다고 주장하지 않는다.
code/start/write-cache 선택과 성공의 인과관계는 검증하지 않았다.

## immutable pins

| 경로 (repository relative) |bytes|SHA256|
|---|---:|---|
| `tools/p09/resume_completed101_compound_runtime_r3.py` |44007|`9e88bfb0d6676270fc1714c75c0e5f2beec5d4f103a917cbc292865f47d1e006`|
| `tools/p09/tests/test_completed101_compound_runtime_r3.py` |15257|`f8b2eaf92402524d36986a5f553aa4fabbc766999b8dec77f7772850e9b41647`|
| `implementation/p09/evidence/locked-r07/p312-light-run001.v1.json` |30821|`ddfb7d0c63ce0129e302a192dd362182041e0a9e9be7e0f7100c15cf4423a2e2`|
| `implementation/p09/evidence/locked-r07/p312-case-102-run002.v1.json` |639564|`fd829ade757b3108d48085d09f417fdc87bceb41a75ab43ce18642c2f50adcc6`|
| `implementation/p09/evidence/locked-r07/cases/p312-case-102-run002.json` |188979|`e912207e3038a70103d40e4f2785b9e9c6070899e5dd68bf140307a445dd235f`|
| `implementation/p09/evidence/locked-r07/p312-actual102-perfproc-before-after-raw-run03.v1.json` |254449|`2c57c7fd67f2037c92abcc81397cf3ed00cd96cf031cef07e20ebfa766dfa6d7`|

현재 code75+새2=77은 이번 full Native1640에 실제 포함되어 둘의 byte/identity/정리 증거로 수용했다.
향후 수정 또는 실행기가 추가되면 기존 pin 검증과 새 scope qualification이 필요하다.
외부 Counter raw 영수증/문서가 product Native1640에 들어 있다고 주장하지 않는다.

## 다음 경계

다음 미수용은103. 성공102 본문 반복 없음. 현재 P312 code/test와 required scope 불변을 확인하고 해당 runtime queue에서 resume할 수 있다.
CPU 보호/유예이면 exact 단계·코드·표본·Native/Job/reader 정리를 검토하고 정당한 개선 뒤 이어간다.
새 측정 창이 전체 runtime을 감싼다고 순간 원인 증명으로 사용하거나 원 guard를 완화하지 않는다.
P09 Gate가 실제 닫히기 전 P10 구현으로 가지 않는다.
접근허용/한글/빌드/Git/OS·Defender·WSL 설정 변경, 삭제·이동·프로세스 종료 없음.

현재 runtime96/249·잔여153(일반147+corpus6)·다음103·whole재조정93·source마감미완료후보0.
P09/A12/A13 OPEN, 목표 ACTIVE. whole1470/historical67/full249/signed16/product완료/CPU원인/PC프리즈해결 FALSE 또는 미확정.
