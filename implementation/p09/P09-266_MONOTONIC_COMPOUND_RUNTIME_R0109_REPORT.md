# P09-266 — 실제 case092 누적 관측 연결과 runtime-r109 문서 마감

2026-10-09. P265 실제 case092 receipt는 본체/전체source/정리 검사를 통과했다.
이 보고서와 prefix 자체는 수용 증거가 아니며, P266 guarded 문서 검사 PASS로
원 r108 바이트와 현재 r109의 일치 여부를 별도 마감한다. 목표 active, P09·A12·A13 OPEN.

## 구현·검증 범위

- 수용된 P260/P262~P264와 원91 FAILED/본문 bytes는 수정하지 않았다.
  새 P265는 P264 결합을 원 anchor와 strict combine/advance로 다시 계산해 이전85를
  확인한다. literal P260 light002/failed91/body91, P262/P263/P264 각 지정 receipt만
  허용한다. 추가 실패·바뀐 bytes·누락·재실행 본체는 차단한다.
- 원 전체1555 입력에 P262/P263/P264/P265 helper/test8개를 더한1563 입력을 모두
  실제 잠금/전후 읽기한다. 과거 본체 PASS 재실행 없음. 처음 실행하는 exact case092 하나만 실행.
- P262의 생성 중 등록 adapter를 실제 post-body Reader에 명시 연결했다. Context/previous,
  q·전후전체readers·postmetadata 누적값은 유지하며 카운터 reset/실패 read 삭제/중복 등록은 없다.
  실제 원 코드가 줄어드는 카운터와 CPU/RAM STOP은 여전히 실패로 처리한다.
- 원 계약498(원1545 및 그 후1555의 명시 fixture domain)을 유지하고, 현재/다음1563
  synthetic 큐30+30을 추가해 총558 실행을 확인한다. 이는558개 제품 본체 PASS가 아니다.
  총수/직렬화/관측정책/실제post연결/Job CPU6.25%·affinity1·BelowNormal16384·active16·
  kill-close·no-breakaway 등을 strict 수용 조건 및 변조 검사에 포함했다.
- 원Native20/metadata32/byte1·2MiB/s, IO/Native600초, 공유metadata720읽기,
  98%x4/RAM·commit·가용메모리 보호, 실제 두 전체읽기/identity/정리를 유지한다.
  원600초·CPU/RAM 기준은 변경하지 않음. 추가 sampler/thread/Git/Cargo/SQL/Hangul/OS 설정변경 없음.
- 실행 전 filename/schema/revision 및718읽기 예산 경계를 정적 점검했다. 문서 helper의
  cold20계약도 PASS했다. 계약을 약화하거나 건너뛰지 않았다.

## 실제 결과

P265 light001 PASS: 계약558, selectedindex92, preparation340읽기/164bound=finalfresh,
STOPnull/cleanup확인, actual_product_child_executed=false. 정확한498+30+30=558이며
P265 producer·consumer·문서 counter가 같은 기준을 사용한다.

P265 case092 run002 PASS:

- 사례: `actual_import::formula_policy_revocation::denied_unknown_and_all_15_inexact_commit_replies_are_never_retried`.
  코드의 `0..17` 루프는 두 거부 응답+15 inexact commit 응답을 처리한다. 각 write1/ingest3/
  head 유지 및 재시도 없음 assertion이 포함돼 있다. 본체1PASS/exit0/Jobactive0, parent elapsed345.28초.
- frame COMMITTED/등록해제, 전후각1563reads/119418092bytes.
  held identity 확인, input lock1869 및 duplicate3126 모두close/잔여0.
- 원 preparation342reads/165bound=finalfresh, postmetadata2reads/1bound=finalfresh,
  공유합344/720. 누적 관측 연결 실제확인=true, 보호 STOP없음/cleanup=true.
- root908표본: 전체CPUmax44.19%, 자체CPUmax5.394011%, private최대55648256bytes,
  가용RAM최소34.741512641307835%. 조기90% 경고진입0/yield0.
  현재 관측상 중단 없이 끝났으나 고부하 개선 효과나 프리즈 원인을 입증한 것은 아니다.
- 입력 잠금 코드 추가점검에서 `check()`는 전체 핸들 전수 재순회를 하지 않았고,
  ancestor cache가 중복 순회를 줄이며 cleanup은 보호 중단과 별개로 끝까지 진행됐다.
  이번 점검만으로 새로운 병목이나 시스템 프리즈 원인은 확정하지 않았다.

## exact 증거 pin

| 증거 | bytes | SHA256 |
|---|---:|---|
| 이전 P264 case091 결합/runtime85/r108 |473724|2e638cd49227bce9154690cddd41a65b736b31be6e97260f891ad869bed93827|
| P265 light001 |27093|13ab50c976f4a0309c4d686a9102e3c30577cc3b03899e0b528897602d6b317e|
| P265 case092 root |613296|e5c477adf0ea021a15f80febcd70aef552b0135543bda273366db159095155ab|
| P265 case092 body |210883|ce02a8ece983c984b8ce31452a38e64338c686d31dd09d59d80b9212bc8cbde6|

root/body 경로는 `implementation/p09/evidence/locked-r07/p265-case-092-run002.v1.json`, `implementation/p09/evidence/locked-r07/cases/p265-case-092-run002.json`다.
이전/원 실패/수용 증거는 모두 보존하며 P266은 원 validator로 두 새 pair pin을 fresh 확인한다.

## 문서 동기화와 권위 경계

원 r108 CURRENT_STATE461582bytes SHA357d4318150ef8f8bd3de0b44fa60c9058d3c8fb3c4d38884b87839b6e34915f,
progress555214bytes SHA91836e0de2fdba51925ea20c9fb349f5fa5eeecb61dc0c3850e1a55fe8046c27를
`evidence/runtime-progress-r108/`에 no-overwrite exact bytes/hash로 보존했다.
current 문서는 원 전체 bytes를 suffix로 유지하고 동일 P265~P266 runtime-r109 prefix만 추가한다.

현재 실제 runtime 수용86/249, 잔여163(일반157+corpus6), 다음index93,
독립source 마감대기0, whole재조정대기83. P09·A12·A13 OPEN.
P266 문서20계약, 원실행558/원498/current30/following30·직렬화·누적관측 조건 일치,
모든 bound input의 finalfresh, report·원 r108 archive suffix·같은 두 prefix를 확인한다.
다음 metadata 읽기 예상은342+4(새 root/body first+final)+2(원 post)=348/720로
controller 회전이 당장 필요하진 않다. 예측은 실제 STOP을 대체하지 않으며 guard를 늘리지 않는다.

이는 P09 전체 완료율이 아니다. whole1470/historical67/full249/signed16/product_complete은
미수용이고 Gate를 닫지 않는다. 접근허용/Hangul/render/differential 등 별도 제품 증거를
문서/fixture 통과로 대체하지 않는다. 본문 재실행 없음. 원 STOP/FAILED 보존.
PC 프리즈 원인·해결 미확정. PLANS 재생성/P10 진입/원본·private·P00~P08 변경 없음.

CPU 보호 중단 시 정확한 구간·코드·관측값을 검토하고 확인된 병목의 새 수정/계약/연결
검증 후 이어간다. 보호 약화·자동 동일본문 재시도·실패 은폐 금지. 다음93은 아직 NOT_RUN.
