# P09-359 실제110 수용과 자원·정리 증거

2026-10-10. 목표 ACTIVE. 직전 P358는 v22 RAM 복구/잠금 전 확인 연결과 정식890,
fresh070, 실제071 Native0 보류 증거로 진전했다. 이번에는 원071 독립 검토072,
fresh073 및 미실행110의 실제074를 완료했다. 코드 변경이나 성공 제품 replay는 없다.

## 실행 순서

1. live code2가 P358/정식890 archive의 크기·SHA256와 같음을 확인했다.
2. 기존 pre-import Windows 표본 CPU12.9%, RAMfree10.159709%에서 원 시작 조건으로
   071의 독립 STOP 검토072를 수행했다. `STRICT_PREFRAME_RAM_DEFER_NOT_PRODUCT_OR_GO`.
   원 실패071/보류 표본/제품 미실행 상태를 보존했다. Native/제품/계약0, 정리true.
3. 별도 실행 전 CPU8.76%, RAMfree10.599879%에서 원 시작 조건을 다시 확인했다.
   한 process에서 helper import만 공유하며 독립 owner/reader의 fresh073→actual074를 직렬 실행했다.
   실패 시 뒤 단계/자동 retry가 없는 단1회 체인이다.
4. fresh073은 기존069 정식890을 별도 fresh로 대조했다. 계약 재실행0.
5. actual074는 새 preframe 원2표본 RAMfree10.306514091090488/10.327932867400365%,
   CPU7.81/8.44%, commit42.978673716348936/42.968129245473456%로 시작 조건을 통과했다.
   sample_count70, latest age0.2616139000165276초. 추가 sampler/thread/Native는 없고
   원 checkpoint와 parent admission 재확인은 유지됐다.
6. 미실행110의 실제 제품 child를 실행했다. body `PASS_SCOPED_NOT_GATE`, tests1,
   exit0, parent elapsed262.56초. root `PASS_EXACT_PRESERVED106_NEXT_RUNTIME_NOT_WHOLE_OR_GATE`.
   890 재사용/계약 재실행0. 이전 성공107/108/109와 성공110의 추가 재실행0.

검증이 늦게 출력됐지만 원 handle12880을 계속 관찰했고 재시작하지 않았다.
본문 파일의 존재/부재를 완료 또는 process terminal 신호로 쓰지 않았다.
93329/12880은 최종 terminal(exit0)이며 소유 child/Job 정리는 검증됐다.

## 실제 제품 및 전체 입력 증거

- before/after 각각 full1658, 121244581bytes, 원 reader1658 passes/동일 바이트 전체 읽기.
- frame COMMITTED/unregistered. source lock1966 획득/1966 close.
- duplicate3316 open/3316 close, duplicate remaining/close failure0, active borrowfalse.
- 원 source handle/reader binding/byte stream/close failure 잔여0. 정리true.
- 실제 각 byte 경계의 held metadata1658/원 path predicate4974/pathname probe0.
  원 stream identity를 유지했고 각 경계 metadata는 재사용하지 않았다. adapter 복구true.
- Job 최종 active0/owned processes[]/owned tree emptytrue/cleanuptrue.
- 원 제한 readback verifiedtrue: CPU hard cap machine6.25%, affinity1,
  priority16384(BelowNormal), kill_on_close/breakaway_disabledtrue.

## 자원 관측과 해석

| 구간 | 시스템CPU 최고 | 검증 parent CPU 최고(머신 기준) | parent private 최고 | RAM 여유 최소 |
| --- | ---: | ---: | ---: | ---: |
| 072 독립 검토 | 19.8% | 2.083333% | 88178688bytes | 9.871984% |
| 073 fresh | 26.18% | 1.893939% | 88936448bytes | 10.088072% |
| 074 actual parent | 42.08% | 1.941748% | 118636544bytes | 8.396173% |

body 원518개 표본의 hostCPU 최고도42.08%, RAM 여유 최소8.396173%다.
child Job peak private25.3MiB(총RAM0.079422%); 이는 parent private와 별개다.
표본·실행이 다른 최대값은 합산하지 않는다.
RAM 여유가 중간에10% 미만이었어도 원 runtime hard-stop8% 기준을 완화한 것이 아니다.
각 시작 및 원 child admission은 그대로 적용됐다. 전체 PC RAM 변동 원인이나
Defender 인과를 이 기록으로 확정하지 않으며 PC 프리즈 해결도 미확정이다.

072 prep bound/fresh248, read507, bytes56715407, finishedtrue.
073 prep bound/fresh249, read509, bytes56849531, finishedtrue.
074 prep bound/fresh250, read512, bytes56984047, finishedtrue;
post body reader bound/fresh1, read2, bytes382166, finishedtrue.

## 현재 상태와 다음 경계

수용104/249, 잔여145(일반139+corpus6), next111, 성공 body 마감pending0,
whole재조정101. 이 큐의 수치를 P09 전체 진행률로 바꾸지 않는다.
현재 v22의 성공 Native/제품 경로는 실제110으로 확인했지만 P09 전체 Gate는 OPEN이다.
P09/A12/A13 OPEN, full249/signed16/whole1470 미완료, 문서 final-fresh NOT_RUN,
P10 시작0, 목표 ACTIVE.

현재 cursor104/next111의 별도 계약 자격/fresh는 아직 NOT_RUN이다.
과거 cursor103의069/073 GO를 새111 GO로 승격하지 않는다. 다음은 기존 자원 admission이
허용될 때 cursor104의 현재/following 자격과 fresh를 수행하는 것. 성공110은 다시 실행하지 않는다.

UAC/한글/특권Defender 추적/Git/빌드/Defender·OS·WSL 설정 변경/외부 process 종료/
삭제·이동은 하지 않았다. 기존 실패와 archive는 보존했다.
