# P09 P248~P251 metadata 시작 밀도 제어의 실제 실행기 연결

2026-10-09. 목표 active. P09·A12·A13 OPEN. PC 프리즈 원인·해결 미확정.

## 결과

- runtime 수용 74/249, 잔여175(일반169+corpus6), 다음index81, 미closing후보0, whole재조정대기71.
- 통과 본문 재실행 없음. index80을 실제 한 번 실행해 exact1 PASS/248filtered/exit0, 전후 전체1539입력/119139656 bytes, 원 정리·identity 검사로 수용했다.
- test: actual_import::formula_policy_registration::explicit_denials_are_storable_data_but_never_allow_current_or_changed_recalculation.
- 명시적 거부를 저장 자료로 인정하되 현재/변경 재계산의 허가로 인정하지 않는 제품 CLI test 경로다. fixed EXE와 fixture/repository double 검사이며 실제 SQL·생산 issuer·한글 UI 인수나 P09 전체/Gate PASS가 아니다.
- Native20·metadata32의 전체 실행기 연결은 이 exact1/source pair에서 실제 확인했다. P239 실제 pre-GO CPU STOP 경계 NOT_RUN이며 의도적인 CPU stress는 수행하지 않았다.

## 중단 경로 보강과 검증

기존 P241 Native STOP·P244 metadata CPU STOP·P245 검토 초기 실패·수용된 P242/P243/P245/P246 지원·r100 문서는 수정하지 않았다. 새 실행기를 구현하면서 발견된 비CPU preflight 오류도 실패로 보존하고 본문 실행 전에 고쳤다.

1. P248은 runtime light에 없는 bound_input_pins를 참조했다. 실제 extra_frame_controller_pins 형식으로 교정했다. 원 root 및 실행 당시 source/test는 그대로 보존했다.
2. P249은 지원 단계의660회 read 예상에 도달한 뒤 finalfresh가212/242로 남아 중단했다. 원 CPU/RAM STOP가 아니며 본문/Native 미실행이다. 실제 요구량660+(242-212)=690을 근거로 새 count 상한720과 예상591.366초를 계산했다. 원 지원660 예측은 수정하지 않았고 원 CPU/RAM/IO600초 보호는 늘리지 않았다.
3. P250 초기 preflight는 과거660 형식을 현재720 형식과 비교해 거부했다. 과거 실패 검토에서만 원660을 명시하고 현재 runtime은720을 요구하도록 교정했다. 음성 검사를 두 개 추가했다. 당시 source/test는 preflight-controller-snapshots/p250-light-run001/에 SHA/length exact 사본으로 보존했다.

새 caller가 복제하던52/16 지원 검증은 제거하고 불변 P244 anchor의 원 strict 검증에 위임했다. 원 입력·원 반복 fresh·최종 fresh·CPU/RAM/parse/IO guard를 삭제하지 않았다. 새 code/proof 검증만 추가한다. 알려진 P250 최초 실패의 exclusive pin·미선택/본문/Native 미실행·비CPU·정리 witness만 별도 검토해 허용하며, 다른 FAILED/CPU STOP/본문 실패는 자동 재시도하거나 건너뛰지 않는다.

## 사전 및 실제 자원·정리

- 수정 사전: 계약156+18+8+8+14=204, metadata683읽기/248bound=finalfresh/233801735 논리bytes, finished/cleanup true/STOP없음.
- 사전249표본 전체CPUmax27.12%, 자체max5.431675%, 자체 private44339200 bytes, 가용RAM최소33.404341%.
- 실제: preparation685읽기/249bound=finalfresh/233904987 논리bytes, finished/cleanup true/STOP없음. 본문 증거의 두 후속 metadata 읽기도 같은 owner 상한720 안에 있다.
- 실제 원 parent251.73초, terminal passed1/failed0/ignored0/measured0/filtered248, JobCPU2.562초/peak private27.63MiB/최종active0/owned_tree_empty.
- 실제 전후1539입력 각119139656 bytes. frame COMMITTED/등록해제, 잠금1845·복제3078 opened=closed, byte identity3078, active reader/stream·잔여·정리 실패0.
- 실제 Native 최대20회/s/4923예약/no-burst, pressure warning0/pause0. 원1MiB/s EXE·2MiB/s 기타 및 두 실제 전체 byte 읽기 유지.
- 실제 root926표본 전체CPUmax24.6%, 자체max5.021368%, 자체 private45473792 bytes(약43.37MiB), 가용RAM최소33.436402%. 기존 표본만으로 관찰하며 추가 sampler/thread/외부PID 관측은 없다.
- 실제 실행 중 제한된 시스템 확인은 CPU2%/가용RAM34.03%/부모42.18MiB 및 CPU3%/가용RAM33.71%/부모42.36MiB였다. 순간값을 전체 최대·현재값으로 대체하지 않는다.

원 지속98%4연속/가용RAM·commit/Job hardCPU6.25%·affinity1·BelowNormal·RAM비율·max16·killclose/nobreakaway·IO600초·본문1200초/원 잠금600초는 유지했다. 데이터/JSON/pin 캐시로 원 byte 읽기를 대체하지 않았다. 이번 조건에서 중단 없이 실행됐다는 증거이며 인과적 CPU 개선률이나 PC 프리즈 해결을 확정하지 않는다.

## Exact receipts

상대 기준 implementation/p09/evidence/locked-r07/.

| 증거 | 상태 | bytes / SHA256 |
|---|---|---|
| p247-density-control-status-doc-r0100-run01.v1.json | r100/수용73 | 22362 / e8cac0eeb28af2e3e7a7e89b09862a5f1428fcc7f2317bcad7ed368554500341 |
| p248-light-run001.v1.json | 없는 필드 참조/FAILED 보존 | 139294 / d70c4606a6e396dd148236a3444ed9824835dcf414ce66df9366b1708c452c12 |
| p249-light-run001.v1.json | count 예상 부족/FAILED 보존 | 246502 / fdd23ccb0ee0f940ce9509c34cc38673426c6347ae512ca19a092c4556b5781d |
| p250-light-run001.v1.json | 과거/current 형식 비교 오류/FAILED 보존 | 138454 / afd2e42cb1f34b69ad5d346e38003d33727800c1b3f55e4c71d3af56f9246290 |
| p250-light-run002.v1.json | 수정 사전204/제품 아님 | 51626 / a345e59325b199403e4d0261e364ac054c787455c03074644f5b28bb02a9ed13 |
| p250-case-080-run003.v1.json | actual80/수용74/다음81 | 612696 / b353add7c8a0e49134d0a7f2983e3a8083192f47151f15f5364a9cdf2fe8e4cd |
| cases/p250-case-080-run003.json | 원 parent exact1/1539 두 읽기 | 177787 / 41b0c0d99669cd9367c7f3e8b511bab7ba1cb781e2ffb98cb41d3e14b246d2a1 |

이전 CPU STOP·지원 literal pins은 P250의 불변 anchor·P247/r100 증거에 보존돼 있다. P251은 새 문서 상태 snapshot이며 실제 pair를 P250 원 validator로 검사하고 현재 실행 코드 및 별도 보존된 실패 코드 SHA/length를 확인한다. 제품·전체 source 재실행이나 전체 runtime 재검증이 아니다.

## 다음 단계 및 문서 보존

다음은 같은 수용된 P250 실행기의 미실행 index81이다. 통과80이나 이전73개는 반복하지 않는다. 새 CPU STOP가 발생하면 실패 단계·표본·코드를 먼저 검토·최적화한 후에만 재개한다.

r100 문서 exact 사본 runtime-progress-r100/과 현재 두 문서의 동일 prefix/원bytes suffix를 검증한다. 원본·private 자료·기존 수용·모든 실패를 보존했다. Git/Review/Cargo/build·원격push·SQL·한글 GUI·접근허용·Defender/WSL/OS 설정 변경 없음.
