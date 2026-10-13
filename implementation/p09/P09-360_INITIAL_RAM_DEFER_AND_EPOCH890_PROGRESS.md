# P09-360 初期RAM 보류 처리와 정식890 epoch 보존

2026-10-10. 목표 ACTIVE. 직전 P359는 실제110 수용104로 진전했다.
이번에는 cursor104/next111의 기존 v22 정식890을 실행해 통과했으나 fresh는 원RAM
admission에서 보류됐다. 초기 보류의 처리 경계를 구현하고 작은22개 검사와 literal076을 대조했다.
새v23 정식906/독립 STOP 검토/제품111은 아직 NOT_RUN이다.

## 실제 순서와 결과

현재 code2가 P359/정식890 archive와 같음을 확인했다. 첫 조회 CPU4.84%,
RAMfree10.629537%, commit42.847950%. 새 pre-import 원표본 CPU7.6%, RAM10.234938%로
원10%/두연속 시작조건을 확인한 뒤, 단일 process에 light075→fresh076→actual077 체인을 예약했다.
각 모드는 독립 owner/reader이며 단계 실패 뒤에는 실행하지 않는 직렬 체인이다.

- 075: `PASS_NEXT_QUEUE_NOT_ACTUAL_OR_GATE`, cursor104/next111의 실제445+합성following445=890 PASS.
  prep bound/fresh252/read518/bytes58965255/finishedtrue, hostCPUmax25.51%,
  ownCPUmax6.571936%, private100151296bytes, RAMfree min9.753978%, cleanuptrue.
- 076: `FAILED_NOT_ACCEPTED`, error `bootstrap_idle_window_not_admitted`, phase admission,
  resource_stop_reason null, Source/Reader/Frame/body/제품 미시작, 계약0, cleanuptrue.
  원6표본 CPU6.68~12.38%, RAMfree9.930992797675934~9.937870836319231%, commit약43.15%.
  private는6표본 내내95797248bytes(약91.36MiB), ownCPU max0.0%였다.
- 077: 전 단계 실패로 호출하지 않음. 제품111은 실행되지 않았다.
- 세션3708 terminal(exit1). 원075/076은 보존했다. 제품 성공110은 재실행하지 않았다.

이 기록은 CPU 폭증이나 검증 프로세스의 큰 메모리 증가를 보여주지 않는다.
다만 process를 공유하면 Python의 이전 작업 메모리가 종료 때까지 남을 수 있으므로 다음 실행은
mode별로 별도 process를 쓰기로 했다. 누수나 PC 전체 RAM 변동의 원인은 아직 확정하지 않았다.

## 코드 수정과 검증 범위

실행기와 검사 파일을 v23/COUNT453/EXECUTED906으로 변경했다.

1. `initial_ram_deferred`: 原RAM admission 실패를 CPU STOP 또는 PASS로 바꾸지 않는다.
   미시작 flags/원정책/원표본/Reader·code95·cursor·Frame·body 없음/정리true를 엄격히 대조한다.
   원 연속 admission 계산에서2개 시작 표본이 나오지 않았고 실제RAM<10 표본이 존재해야 한다.
   CPU98%, RAM8% hard-stop, commit95% 또는 잘못된 표본은 이 분류에 들어오지 않는다.
2. 초기 admission에는 원cursor가 없음을 명시한다. 독립 검토의 cursor는 현재 또는 승인된
   과거 검토의 projection일 뿐, 원 실패cursor로 꾸미거나 cursor를 증가시키지 않는다.
   승인된 과거 projection은 cursor가 나중에 증가해도 보존한다. 미검토 실패는 GO를 차단한다.
3. 원 정식890/code2/실제110/fresh/STOP 검토의 정확한 literal pin과 물리 code archive를
   v22/445×2 oracle에 연결했다. 기존 성공110은 원 증거로 검토하며 재실행하지 않는다.
   과거890 자격은 새v23 GO로 쓰지 않는다. 기존862/828 및 실패066 epoch 연결도 유지한다.
4. 새8개+기존 관련14개, 합계22개의 작은 합성 검사 PASS. 현재 전체 suite inventory453.
   실제076 byte/SHA와 음성분류 대조 PASS_NOT_RUNTIME_OR_GO.
   22개를 정식906으로 승격하거나 기존890에 더해 새자격을 주장하지 않는다.

후속 원자원 조회는 RAM8.568994%였으며, 마지막 두 표본은 RAM8.135494/8.172348%,
CPU7.23/8.64%, commit44.663196/44.663613%였다. 원10% 시작 조건 미충족으로
새정식906/독립076 STOP 검토/제품을 실행하지 않았다. 강행·자동retry·보호 기준 완화는 없다.

후보 code2는 `evidence/p360-v23-initial-ram-code`에 보존했다. 정식906 archive가 아니다.
원 정식890과 실제110의 archive/receipt는 유지했다. frozen93/제품 구현/P00~P08는 수정하지 않았다.

## 현재 경계

수용104/249, 잔여145(일반139+corpus6), next111, 성공body 마감pending0,
whole재조정101. 기존 성공110과 전체 제품을 재실행하지 않았다.
P09/A12/A13 OPEN, full249/signed16/whole1470 미완료, 문서final-fresh NOT_RUN,
P10 시작0, 목표 ACTIVE. 해당 큐 수치는 P09 전체 진행률이 아니다.

다음은 원 자원 조건이 허용될 때 별도 process에서 원076 독립 음성 STOP 검토,
현재v23 정식906 자격, 별도 fresh, 미실행111 단1회 순으로 진행하는 것.
검토·새 코드 자격 없이 actual을 반복하지 않는다. 새 실행기 runtime 연결의 실제 검증은
아직 NOT_RUN이며 작은22개 PASS만으로 성공했다고 하지 않는다.

관리자/UAC/한글/특권Defender 추적/Git/빌드/Defender·OS·WSL 변경/외부 process 종료/
삭제·이동은 하지 않았다. PC 프리즈 해결과 Defender 인과는 미확정이다.
