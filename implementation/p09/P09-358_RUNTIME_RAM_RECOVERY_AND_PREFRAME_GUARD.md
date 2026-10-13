# P09-358 RAM 보류 복구 연결과 잠금 전 확인의 실제 검증

2026-10-10. 목표 ACTIVE. P357는 RAM 거절 처리 결함의 진단 코드 구현으로 진전했다.
이번에는 실제 실행기와 계약 검사 두 파일을 v22로 수정했다. 정식890/fresh가 통과했고,
실제110 요청에서 새 RAM 확인이 Native 잠금 전에 보류하는 것을 확인했다.
제품110을 실행하거나 수용한 것은 아니다.

## 변경과 보존

- `tools/p09/resume_preserved106_queue_runtime.py`: 원 RAM 시작10%/두 연속 표본,
  RAM 중단8%, CPU98%×4, commit95%, identity·전체 두 byte·Job·pacing·cleanup 유지.
- 기존 owner의 checkpoint와 최신 표본 두 개만 이용해 `preframe_ram_window`를 실행한다.
  표본 최대 나이0.5초를 확인한다. 새 sampler/thread/Native/대기·재시도는 없다.
  시작 조건 미달이면 Frame/InputLocks 구성 전에 실패 음성 기록으로 보류한다.
  통과하더라도 원 parent admission을 다시 수행한다.
- 원 CPU 전용 terminal validator를 수정하지 않는다. 원 거절 기록·sidecar·0byte
  placeholder를 보존하고, 제품·worker·Job·byte reader 미시작/1966 handle 전부 정리/
  원6개 RAM 표본/정확한 scope·자격·fresh를 대조하여 독립 음성 검토만 허용한다.
  검토는 제품 PASS, cursor 증가 또는 새 GO가 아니다.
- 과거 정식862의 정확한 archive/code2와 literal receipt들을 과거 v21/431×2 oracle에
  연결했다. 성공109는 원 body·전체 Native/byte·Job 증거로 다시 검증하지만 제품 재실행은 없다.
  과거862 자격을 새 코드의 GO 후보에 넣지 않는다. 미검토 STOP 차단은 유지한다.
- 잠금 전 CPU 보호가 발동하면 원 실패/표본/reason을 바꾸지 않고, Native/body 미시작을
  확인한 뒤 원 pre-product CPU oracle에 음성 검토 단계만 바인딩한다.
- `tools/p09/tests/test_preserved106_queue_runtime.py`: 작은 RAM/epoch 검사14개 추가.
  COUNT445/EXECUTED890. 이14개는 정식890 안에 포함되며 별도로 합산하지 않는다.

## 실행 증거

| 실행 | 결과 | 범위 |
| --- | --- | --- |
| 066 | FAILED_NOT_ACCEPTED | anchor에서 과거 native107/v5 record가 새 preframe 필드를 요구한 KeyError. Native/제품/계약0, 정리true. |
| 067 | PASS_PRE_PRODUCT_STOP_REVIEW_NOT_GO | v5 record namespace 수정 뒤 정확한065 RAM 보류 독립 검토. 이후 코드 보완 전 receipt/code archive 보존. |
| 068 | PASS_PRE_PRODUCT_STOP_REVIEW_NOT_GO | 최종 현재 코드에서065 RAM 보류 검토. 제품0, 계약0, cursor103. |
| 069 | PASS_NEXT_QUEUE_NOT_ACTUAL_OR_GATE | 실제445 현재+445 합성 following=890 계약. 독립 원 owner/reader 및 final-fresh. |
| 070 | PASS_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT | 현재069의 자격을 별도 fresh owner/reader로 대조. 계약 재실행0. |
| 071 | FAILED_NOT_ACCEPTED / DEFERRED_PREFRAME_RAM_WINDOW | 기존 자격/fresh 대조 뒤, Native·제품 전에 RAM 보류. 핸들 획득0, body 파일 미생성, cursor 증가0. |

066 원 실패와 두 당시 코드 파일은 `evidence/p358-v22-preformal066-code`에 보존했다.
067 당시 코드 두 파일은 `evidence/p358-v22-review067-code`에 보존했다.
최종890 코드 두 파일은 `evidence/p340-formal890-code`의 물리 바이트/SHA256와 같다.
원065와 원066 기록은 수정하지 않았다.

069 preparation: bound/fresh245, read496, finishedtrue. hostCPUmax22.85%,
ownCPUmax6.547619%, private117886976bytes, RAMfree min9.954300%.
070: bound/fresh246, read499, bytes55879615, finishedtrue,
hostCPUmax14.79%, own1.657459%, private88178688bytes, RAMfree min10.305129%.
071: bound/fresh247, read504, bytes56149199, finishedtrue,
hostCPUmax18.15%, own1.956947%, private116686848bytes, RAMfree min9.857039%.
각 최대치는 서로 다른 표본/실행의 값이며 합산하지 않는다.

071 잠금 전 실제 원 표본 두 개:

- CPU12.14%, RAMfree9.857038556862438%, commit43.240600251178584%.
- CPU9.51%, RAMfree9.924372225719818%, commit43.168542018985995%.

원 sample_count69, latest age0.3240828000125475초. 기존 metadata 관측의 같은 표본과 일치한다.
원 checkpoint는 실행됐고 새 sampler/thread/Native는 시작하지 않았다.
`source_attempted=false`, frame없음, body path없음, childfalse, 정리true.
065에서는 이런 보류를 판단하기 전1966 source lock을 열었지만 071은0개다.
CPU 보호 중단이나 제품 테스트 실패가 아니며 CPU 풀로드/프리즈 원인을 확정하지 않는다.

최종 literal069/070/071 byte/SHA, 자격/fresh 링크, 동일 current95 code2,
live/archive code2, 관측 표본과 preframe 표본의 일치, body 미생성을 별도 대조했다.
이 대조는 `PASS_LITERAL071_PREFRAME_NEGATIVE_NOT_STOP_REVIEW_OR_GO`이며,
독립071 STOP 검토나 새 runtime GO를 대신하지 않는다.

## 현재 경계

수용103/249, 잔여146(일반140+corpus6), next110, 성공body 마감pending0,
whole재조정100. 기존 성공107/108/109를 재실행하지 않았다.
P09/A12/A13 OPEN, full249/signed16/whole1470 미완료, 문서 final-fresh NOT_RUN,
P10 시작0, 목표 ACTIVE. 해당 큐의 수치는 P09 전체 진행률이 아니다.

최종 세션22347/94737 terminal. 071 이후 actual 재시도0.
다음은 기존 자원 admission이 허용될 때 원071의 독립 음성 STOP 검토를 수행하는 것.
071 검토 없이 actual을 반복하지 않는다. 새 v22의 성공 Native/제품 경로는 아직 NOT_RUN.
실패 보류를 제품 PASS로 바꾸거나 RAM 기준을 낮추지 않는다.
관리자/UAC/한글/특권 Defender 추적/Git/빌드/Defender·OS·WSL 설정 변경/
외부 process 종료/삭제·이동은 하지 않았다. PC 프리즈 해결은 미확정이다.
