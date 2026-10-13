# P09 P255~P256 중복 준비 경로 정리와 실제82·83

2026-10-09. 목표 active. P09·A12·A13 OPEN. PC 프리즈 원인·해결 미확정.

## 결과와 수용 경계

runtime 수용77/249 · 잔여172(일반166+corpus6) · 미closing후보0 · 다음index84 · whole재조정대기74.

미실행82와83을 각각 실제 한 번 실행하고 원 parent·전후 전체 source·identity·Job·정리 판정으로 수용했다. 통과 본문 재실행 없음. fixed EXE/fixture/repository double 제품 CLI 경로의 exact2이며 실제 SQL·생산 issuer·한글 UI 인수나 full249/P09 Gate 수용이 아니다. P239 실제 pre-GO CPU STOP 경계 NOT_RUN. 의도적인 CPU stress나 접근허용 창을 실행하지 않았다.

- 82: actual_import::formula_policy_registration::generated_allowance_never_bypasses_native_protection_or_invalid_second_section. 생성 허가가 원 native 보호나 잘못된 두 번째 section 검사를 우회하지 못함을 확인한다.
- 83: actual_import::formula_policy_registration::generated_four_target_registration_is_consumed_by_original_changed_and_current_product_paths. 네 target의 등록 정책이 원본·변경·현재 제품 경로에서 소비됨을 확인한다.

## 검토한 병목과 구현

이전 P254에서 다음 shared 읽기721/상한720 초과를 예상했으므로 실패가 날 것을 알면서82를 실행하지 않았다. CPU STOP의 새 관측은 없었다. 준비 단계는 이미 수용된 과거 기록의 recursive progress를 여러 세대에 걸쳐 읽고 해석하는 구조였고, 이 작업량이 계속 누적되고 있었다.

새 P255는 literal SHA/length r102 상태 checkpoint를 소비한다. 95개의 checkpoint 입력은 모두 첫 실제 byte pin과 최종 fresh를 유지한다. 상태 문서 두 개는 변경 가능한 현재 경로 대신 r102의 exact 별도 사본을 검사하며, 이 매핑을 명시적인 정책과 음성 검사로 묶었다. Reader/pin/json을 가로채는 캐시, 원 읽기 대신 돌려주는 parsed JSON/pin 값, 원 판정기의 monkey patch는 없다. 검증한 파일을 의미 판정에 쓰는 새 호출 구조다.

원 P253 actual81 판정기로 checkpoint의75수용 상태를 다시 확인하고 원 P250 actual80/historical fixture 판정도 유지한다. compiled249·1470 baseline manifest·원 Rust785 live inventory·legacy acceptance 검사, known 실패의 원 semantic 검사 및 최근 P241/P244/P250/P252/P253 namespace의 새로운/미검토 파일 차단을 유지한다. 모든 과거 receipt를 매 회 recursive fresh 재생하는 구조와 같은 검증 범위라고 주장하지 않는다. 과거 수용은 보존된 checkpoint로 소비하며 whole/historical67/full249/Gate 재조정은 여전히 미완료다.

제품 실행에서는 원 전체1543입력에 새 source/test2를 더한1545개를 모두 실제 잠금·전후 byte 읽기에 포함한다. 기존 수용 source/test·receipt·원 STOP/FAILED는 수정하지 않았다. Native20/metadata32 no-burst·EXE1MiB/s·기타2MiB/s·원 CPU/RAM/Job·IO/잠금600초·본문1200초·원 identity·정리를 유지한다. 원600초·CPU/RAM 기준은 변경하지 않음.

## 검증과 자원 증거

새 사전 계약은 원 P253의398 실행을 그대로 유지하고 현재26 및 명시적 synthetic 다음26을 더한450개다. 그 다음 synthetic 계약은 실제83/84 수용의 증거가 아니며 각각 별도 실제 실행이 있어야 한다.

| 범위 | 준비 읽기 / bound=finalfresh / 논리bytes | 원 parent | Job CPU / peak private |
|---|---|---|---|
| 사전 light001 | 246 / 117 / 25336604 | 제품 미실행 | 미관측 |
| 실제82/run002 | 248 / 118 / 25380534 | 255.77초 | 4.703초 / 30.38MiB |
| 실제83/run003 | 252 / 120 / 26917356 | 270.66초 | 20.297초 / 34.58MiB |

각 실제 실행의 후속 metadata2읽기를 합친 shared250/254는 원720 상한 안이다. 원 판정기는 실제83의 Job CPU가82보다 많다는 사실도 그대로 보존한다. 테스트를 하나씩 실행하고 원 Job hard CPU6.25%·affinity1·BelowNormal·RAM비율·max16·killclose/nobreakaway를 유지했으며 CPU 수치가 같다고 주장하지 않는다.

비교 기준 실제81의 준비715읽기/237563005bytes에서 새 실제82의248읽기/25380534bytes로 준비 작업량이 감소했다. 사례와 검증 호출 구조가 바뀐 측정이므로 같은 작업의 인과적 CPU 개선률이 아니다. 원 현재 제품 입력 두 byte pass의 크기는 줄이지 않았다.

- 사전37표본: 전체CPUmax18.01%, 자체max5.651053%, private51888128bytes/가용RAM최소32.610007%/STOP없음.
- 실제82 root722표본: 전체CPUmax54.53%, 자체max5.745342%, private53850112bytes/가용RAM최소31.343467%/STOP없음.
- 실제83 root755표본: 전체CPUmax40.82%, 자체max5.810129%, private55087104bytes(약52.54MiB)/가용RAM최소31.278647%/STOP없음. 원 parent531표본 전체CPUmax30.49%.
- 두 실제 실행 모두95% 경고표본0/지속98%4연속0. Native pressure warning/pause0. 기존 표본만 요약하며 새 sampler/thread나 외부 PID 원인 판정은 없다.
- 각 실제 전후1545입력 각119242806bytes, COMMITTED/등록해제. 잠금1851·복제3090 모두close, byte identity3090, Native20회/s/4941예약/no-burst. 별도 경로 byte 재열기·probe·잔여·active reader/stream·정리 실패0. 원 Job 최종active0/owned_tree_empty/cleanup.

이번 조건에서 두 사례가 중단 없이 완료됐다는 증거다. PC 프리즈 원인·해결 미확정이며 장시간 시스템 안정성 전체를 입증하지 않는다.

## Exact receipts

상대 기준 implementation/p09/evidence/locked-r07/.

| 증거 | 경계 | bytes / SHA256 |
|---|---|---|
| p254-generic-metadata-status-doc-r0102-run01.v1.json | r102/75수용 checkpoint95 | 40000 / f394aded5f736eae6b46ccb8885d5e46e99a845b7135849126f526d366b49e9e |
| p253-case-081-run003.v1.json | 원 actual81 pair | 615984 / 22d57ddd87d213c6d41c39c536c5d83e2fec295ea34d110540f5406284b2a246 |
| p255-light-run001.v1.json | 사전450/제품 아님 | 21965 / 6a5f7f5d431bb3105d35ed7495d01c558c5cb1b9b6e57f6f30fc85e540c03b3a |
| p255-case-082-run002.v1.json | actual82/76수용 | 587528 / ed45ccea9cf1908178a26e4150176047c69e0b39801f49c3af2d703b68e79698 |
| cases/p255-case-082-run002.json | 원 parent82/두 읽기/정리 | 180883 / 2d7d0fd4a8f8353c6f1567674cc34d2ad975f1969ee9e15c350118a1848212ea |
| p255-case-083-run003.v1.json | actual83/77수용 | 590216 / d993f764dfbccb017a85cdfcdcc559af3a6645fff70b12c177e2e06d4b863a9f |
| cases/p255-case-083-run003.json | 원 parent83/두 읽기/정리 | 186103 / 9d80988e819700b75396ac98acb4a8497feab253b37c005e65eaef4627b65d59 |

## 문서 및 다음 경계

새 문서 상태 snapshot/P256은 P255의 원 anchor·progress·record로 누적 pair를 검사하고, 원 판정 결과에서 수용 수/잔여/다음 index를 계산한다. 후속 회차에서도 같은 수용 코드를 재사용하도록 문서 검사 값을 특정77에 고정하지 않았다. 문서14 계약과 모든 bound 입력의 최종 fresh를 요구한다. 이 문서 검사가 제품이나 전체 source 본문을 재실행하는 것은 아니다.

r102 문서 exact 사본 runtime-progress-r102/과 두 현재 상태 문서의 동일 새 prefix/원bytes suffix를 보존·검증한다. CPU 보호 중단 시 자동 재시도 금지; 새 STOP가 나면 단계·표본·코드를 검토하고 안전한 최적화/검증 후 재개한다.

다음index84 실제 NOT_RUN. 실제83 preparation252에 새 root/body 첫 읽기2와 최종fresh2 및 원 후속2를 더하면 다음 shared258≤720 예상이다. 예상과 실제 검증은 구분한다. 같은 불변 P255 caller로 미실행84를 진행하며 향후 누적 읽기 상한이나 CPU STOP가 나오기 전/후 각각 검토한다. Gate를 닫거나 P10으로 넘어가지 않는다. Git/Review/Cargo/build·원격push·SQL·한글 GUI·접근허용·Defender/WSL/OS 설정 변경 없음.
