# P09-264 — case091 관측 연결 수정과 독립 source 결합 수용 / runtime-r108

2026-10-09. 이 보고서·상태 prefix 자체는 수용 증거가 아니다. P264 실제 guarded
결합/문서 검사 receipt가 PASS이고 모든 pin이 일치할 때만 아래 r108 수용을 적용한다.
그 전에는 r107의 runtime 수용84/249가 권위 있는 상태다. P09·A12·A13 OPEN.

## 원 중단과 확인된 코드 원인

- P260 actual91은 원본체 exact1PASS/exit0, 전체1555 입력 두 실제 읽기를 완료했다.
  후처리 metadata 생성 시 누적 Context.reader를 새 단일 reader로 바꾸고 복구하지
  않아 `P193_READ_COUNTER_RESET` / `STOP_RESOURCE_OBSERVATION_FAILED`로 종료했다.
  이번 중단은 `STOP_SUSTAINED_SYSTEM_CPU`가 아니다. 원 failed root는 수용하지 않는다.
- 원frame CLOSED/등록해제, input lock1861 및 duplicate3110 모두 닫힘/잔여0.
  held identity commit은 누락됐고, metadata는1read/131072bytes/0bound/finished=false다.
  이 미완료 결과를 완료로 승격하지 않는다. 원본체와 Job cleanup은 원검사로 별도 검증한다.
- 원 실행 관측753표본의 전체CPUmax100%, 자체CPUmax3.340203%, private최대55648256bytes,
  가용RAM최소31.1703025662686%는 관측치일 뿐 CPU 가해자 또는 프리즈 원인 증거가 아니다.
- P260 light run001은 admit/본문 전 중복 keyword 초기화 TypeError로 실패했고 receipt는
  없었다. 수정 전 source/test는 `evidence/preflight-controller-snapshots/p260-light-init-run001/`
  에 exact bytes로 보존했다. 수정은 중복 arg 제거뿐; flags의 false는 유지했다.
  원 source20990bytes SHA cfc45896ddc5326ccb34488ea1ca68f5b91f34cf6701763280ac9f2b48001c45,
  test3716bytes SHA509086292b0d11bb45cef9aec872c902951ebf349562a00cb715069d4c535cbe.
  P260 light002는 원450/current24/following24 총498계약과151bound 최종fresh를 통과했다.

## 수정 범위 및 검증

- 수용된 P260 및 모든 이전 source/test/receipt는 수정하지 않았다. 새 P262
  `AggregateContext`는 원 Context와 previous를 그대로 두고 생성자의 reader 대입을
  누적 aggregate에 즉시 등록한다. 생성 중 checkpoint가 표본을 찍어도 읽기량 이력은
  유지한다. 실패한 reader의 실제 카운터도 삭제하지 않는다. 중복 등록·실제 감소는 차단한다.
- 생성 실패 시 만들어진 entry binding만 정리하고 원 STOP을 다시 전달한다. 별도 sampler,
  thread, 카운터 reset, unknown의 0 치환, read/identity 생략은 없다.
- P262 원관측10 + 연결14 + 원실패 변조12 =36계약 PASS. 작은 실제18bound
  (첫 reader15/30reads, 연결 reader3/6reads) 모두 finalfresh, STOP없음/cleanup확인.
  cold 연결14+원관측10도24/24 PASS였다. 실제 runtime 전체 연결 수용 증거는 아니다.
- P263은 원91 본체 재실행 없이 독립 전체1559(원1555+P262/P263 helper4) 입력 frame을
  생성했다. 전후 각각119374764bytes/1559reads, COMMITTED/등록해제/held identity확인,
  input lock1865 및 duplicate3118 모두 닫힘/잔여0. 새로운 reader를 source 전체 읽기 후
  누적 aggregate에 연결하고 원91 body의 같은 byte pin을 최종fresh로 재확인했다.
- P263 추가 source16 + 원관측/연결/실패36 =52계약 PASS. metadata prep18bound/36reads,
  post1bound/2reads 모두 finished/finalfresh, 공유720읽기 내, STOP없음/cleanup확인.
  699표본 전체CPUmax49.9%, 자체CPUmax4.878049%, private최대40345600bytes,
  가용RAM최소33.995987197775484%. 조기90% 경고진입0/yield0이므로 고부하 개선 효과를
  입증한 것은 아니다. 원600초·CPU/RAM 기준은 변경하지 않음.
- P263 source는 원91 실행 전체에 걸친 하나의 연속 frame을 복구한 것이 아니라 별도
  독립 frame이다. 원 failed root/미완료 metadata를 소급 PASS로 바꾸지 않는다.
- P264는 원 anchor/record로 이전 수용84를 재구성하고 literal P260 light002/failed91/
  body91만 허용한다. 추가 실패·변경·missing·재실행 body가 있으면 차단한다.
  원 EXE/worker/core/249 binding과 Job CPU6.25%/affinity1/BelowNormal(16384)/
  active16/kill-close/no-breakaway/active0, 원본문 exact1 PASS, 독립frame1559를 strict 검증한다.
  26개 변조·중복·누락·범위/보호/연결 계약과 문서 동기화 검사 후에만 r108을 수용한다.

## exact 증거 pin

| 증거 | bytes | SHA256 |
|---|---:|---|
| 원 P260 failed91 root |1186964|8f67957fad03a952aec0ce47893f1b2ce7e06d91a6386c1efc6cf21d3dd76cff|
| 원 P260 case091 body |183603|3bed523c8db3404c537cf341a4bb23742cc976975a6793ea3ef0d2ccfd048b2a|
| P260 light002 |24621|5fa419f43368571f5f981a854a6d3c21fd443e97b6e01efa1974e5947e1835d4|
| P262 관측 검토/연결 검증 |22383|782f871474195561a4b6cd794fde8bff11e67565d44ec75f39980157ff7d826d|
| P263 독립 전체source |1880734|85fda297ba865d15588c62dd1e14248d8f1caa8991374c1d9ea6e448a4b49e05|
| 이전 P259 수용84/r107 |457284|fb23580ab7ba0a0dccf6caaf0e19c693e6d12be0705c51f35d0711443a19c3ea|

모두 `implementation/p09/evidence/locked-r07/`의 literal 파일이며 body는 `cases/` 아래다.
P264 결과는 `p264-case091-compound-run01.v1.json`에 별도로 기록한다. 원본 삭제/재작성 없음.

## 문서 보존과 단계 경계

원 r107 CURRENT_STATE459418bytes SHA9f260fc1fbcbb4200756feb990d6e3bba3178096c8c40fc67754a709044ee86f,
progress553050bytes SHAf53c87a6ef52682e11cefdb42fca12709abb286c93eb30b543ab0eef22e8ed08를
`evidence/runtime-progress-r107/`에 동일 bytes/hash로 no-overwrite 보존한다.
두 current 문서는 기존 전체 bytes를 suffix로 유지하고 동일 r108 prefix만 추가한다.

P264 PASS 조건부 runtime 수용85/249, 잔여164(일반158+corpus6), 다음index92,
독립source 마감대기0, whole재조정대기82. 이는 P09 전체 완료율이 아니다.
현재 whole1470/historical67/full249/signed16/Gate/product_complete은 미수용이다.
현재 참고 conformance matrix53행(P09 owned46/P11 deferred7)의 green은0이며,
actual HWPX/Hangul/automation/render/differential 수용은 별도 검증이 필요하다.
P10으로 넘어가지 않는다. PLANS 재생성 없음. private/original/P00~P08 보존.

CPU 보호로 중단되면 구간/코드/관측 증거 검토 → 확인된 병목의 새 안전한 수정 및 계약
검증 → 미실행 항목 순으로 진행한다. 자동 동일본문 재시도/보호 약화/실패 은폐 금지.
PC 프리즈 해결은 입증하지 않음. 이번 작업은 접근허용/Hangul/Git/Cargo/SQL/OS/
Defender/WSL 설정변경 없이 수행한다. 다음92는 새 후속 실행기 연결 qualification 뒤 진행한다.
