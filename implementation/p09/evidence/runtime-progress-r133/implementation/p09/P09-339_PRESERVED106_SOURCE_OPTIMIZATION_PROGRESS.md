# P09-339 — CPU STOP 코드 최적화 및 보존106 독립 원본 마감 (2026-10-10)

## 현재 결과

목표 ACTIVE. 제품 runtime 수용 **100/249**, 잔여 **149 = 143 regular + 6 corpus**, next **107**. 성공 제품의 source-closing pending **0**, whole reconciliation pending **97**. P09/A12/A13 OPEN. 이 249개 검증군을 전체 P09 진행률이나 전체 잔여 작업 수로 바꾸어 해석하지 않는다. whole1470/full249/signed16/제품 완료/PC 프리즈 해결은 여전히 FALSE 또는 미확정이다.

105 제품 자식을 실제 Job에서 1회 실행하여 수용99까지 진행했다. 이후106 제품 자식도 정확히1 PASS/exit0였지만 후속 원본 검증이 CPU STOP이었다. 제품106을 다시 실행하지 않고 원 성공 capture와 별도 완전 원본 마감을 결합해 수용100을 확정했다. 원 FAILED root, STOPPED sidecar, 부분 after, 빈 body는 수정·재분류하지 않았다.

## STOP 단계와 own-code 검토

- `locked-r07/p335-case-106-run012.v1.json`: caller FAILED_NOT_ACCEPTED, owned_parent 단계; sidecar는 final_source_freeze STOPPED_NOT_ACCEPTED. 제품 자식은 실제 실행·Job/membership/제한 확인·exit0·passed1/failed0, capture 양쪽 완전, owned_tree_empty/정리TRUE. 원 before1654/120895337bytes 완료, after1172/84584950bytes 부분. caller의 actualFALSE를 자식 미실행 증거로 해석하지 않는다.
- 같은 실패의 잠금1962/1962, dup2826/2826 close, 잔여/실패/reader/stream0. 원 표본776개, hostmax100/ownCPUmax6.470588%/private65126400bytes/freeRAMmin38.420233%. 마지막4 host98.63/100/100/100, ownCPU0, 마지막3 읽기증가0. 외부 CPU 원인·간접 IO/보안검사 기여·프리즈 원인 미확정.
- 독립 마감 v1 `p338-source-run002.v1.json`: source_acquire CPU STOP, 제품 재실행0, 실제 Native 잠금612개 모두 close, byte boundary0. 원 표본131개 마지막4 host100/ownCPU0/읽기증가0, 정리TRUE. 당시 `actual_source_frame_executed=False`는 commit 이후에만 표시한 잘못된 상태 표현이었다. 원 기록을 덮지 않고 별도 검토에 실제 acquire 사실을 명시했다.

두 STOP 모두 원 실패·표본·정리 결과를 검토하고, 다음 GO 전에 수정된 코드의 새 독립 검토를 요구했다. 같은 명령 맹목 반복 없음.

## 구현한 최적화

변경 파일은 `tools/p09/complete_preserved106_source.py`, `tools/p09/tests/test_preserved106_source.py` 두 경로다. 원 P335 source/test와91개 코드 bytes/hash는 그대로다.

1. anchor가 **같은 Reader 안에서 실제 bind한 코드91개**를 다시 물리적으로 읽던 비용을 제거했다. 현재 Reader snapshot과 literal91 pin 일치를 확인하고 새2개만 bind한다. 별도 명령 간 cache로 fresh 검증을 대신하지 않으며, 모든 입력의 원 최종fresh·Native두 전체 byte·identity 검증은 유지한다.
2. source/accept는 정확히 같은 코드93·원106 불변pin·queue99·extended1656을 가진 qualified review만 재사용한다. **review61 실제 실행**, source/accept **새 계약 실행0·재사용61**로 구분한다. checkpoint61회를 실행한 것처럼 위조하지 않는다. 코드 drift/다른 review/missing count/가짜 current statistics는 거부한다.
3. Native 시도 표시를 Frame 생성 후 acquire 전에 기록하고 완전 자격은 commit 후 별도 표시한다. 실제 일부 acquire를 미실행이라고 표시하지 않는다.
4. v1 실패의 literal pin·원 code2 archive·612 전부 close·부분byte0·원 CPU표본을 새 review에서 독립 확인한다. 실패/guard 원인은 그대로 보존한다.
5. 원 startup1core/BelowNormal, CPU98x4/.5s, RAM/commit 비율, Native600/metadata720/parent1200, 획득14/Native20/metadata32 no-burst, chunk64KiB/binary1MiB/s/other2MiB/s, JobCPU6.25%/active16/killclose/8% RAM cap·7% stop을 바꾸지 않았다.

v1 코드2는 `evidence/p338-v1-source-code/`, v2 qualified 코드2는 `evidence/p338-v2-qualified-code/`에 정확한 bytes/hash로 보존했다. v2 source33090bytes SHA `d2c97f3723be25194c43a2142a95c58ae299b2f66919bba33b8442664b49518a`; test11920bytes SHA `943a4496515e6f13f2a25c87f52bc80d54dfe600ef6a783db184a09a8eb1027a`.

## 실제 검증 결과

| 증거 | 실제 수행과 결과 |
| --- | --- |
| p335-case-105-run009.v1.json | 제품1·원full1654 전후완료·FrameCOMMITTED·528 계약·정리TRUE·수용99 |
| p338-review-run001.v1.json | v1 독립 semantic review54 PASS, source 미완료/제품 재실행0 |
| p338-source-run002.v1.json | v1 source acquire CPU STOP·Native612close·수용0·원본보존 |
| p338-review-run003.v1.json | v2 구문/61 계약 PASS·142bound/142fresh/284reads·finished/정리TRUE·Native/제품0 |
| p338-source-run004.v1.json | 새 계약0/검토61재사용·full1656 전후 완전 읽음·FrameCOMMITTED/unregistered·143bound/fresh/286reads·정리TRUE |
| p338-accept-run005.v1.json | 새 계약0/검토61재사용·독립144bound/fresh/288reads·정리TRUE·정확한106 compound1 수용·runtime100 |

Source004 scope **1656 inputs/120940347bytes**, 코드93, directory308. before와 after 각각1656reads/120940347bytes: binary14216704/other106723643, 총241880694bytes. lock1964/1964close, duplicate3312/3312close, 실패/잔여/reader/stream0, pathname reopen0, 입력 범위 축소0. 원 exact identity/기한/pacing/closing 검증을 유지했다. 제품 자식 재실행0.

Source004 ownCPUmax **1.136364%**, own private max **58142720bytes (약55.45MiB)**, RAM free min **39.2510048863%**, hostCPUmax **49.15%**. v2 review ownCPUmax5.978261/private56623104bytes. 이는 해당 실행의 측정값이며 STOP v1과 동일 조건의 성능 비교나 프리즈 해결 인과를 입증하지 않는다.

## 핵심 불변 pin

- 105 root668176bytes SHA `e3a3047caa98ff92bc7e7dd2f2c15ee13b98d658c9940b548965df2f2ec15837`
- 106 FAILED root1025232bytes SHA `41b553fc2d006ee1b17323deba5a8c10f91f256fb70e03f978859b5c196b18e8`
- 106 STOPPED sidecar636884bytes SHA `79c712145aa973c9ccdfafa980945f2f4b4fe74c8a59f9be2637f9e86a37e686`
- 106 body0bytes SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- v2 review293891bytes SHA `612b841e87840352adae2e1fab8819fc02556060da26912af028b372128e43f2`
- v2 source628772bytes SHA `2d19eaa5057ceac9b3dbc93e5c8f889facd5734ca720c451d0b547ec7d8688db`
- compound accept293887bytes SHA `c46d5d978246006da2a1164adeafcd4d14662acf2f2cd6bd9e7f86a47853513b`

## 다음 단계와 문서 경계

기존 warm 세션16972는 post-product STOP 후 종료됐고 이번 review/source/accept 프로세스도 모두 정상 종료했다. 활성 Native/제품/Job/감시기를 남기지 않는다. 빌드/Git/Review/한글/접근허용/OS·Defender·WSL 변경 없음.

현재 P335 큐는 post-product 실패106을 그대로 지원하지 않으므로, **기존 P335 actual106을 다시 실행하면 안 된다.** 다음은 새 안정된 큐에 literal compound100과 원93 코드를 연결하고 코드/계약/독립fresh를 확인한 뒤107을 실행하는 것이다. 107은 `actual_import::fresh_service_read_does_not_turn_stale_or_wrong_policy_into_authority`. compiled249 목록에서106/107 순서를 확인하고 `actual_import.rs:346`의 제한된 fixture import/잘못된 source digest·정책 순서 거부 검사를 정적으로 검토했다. 107 runtime은 NOT_RUN.

r132 CURRENT_STATE/진행원장/P336 보고서는 `evidence/runtime-progress-r132/`에 전체 bytes/hash 보존했다. r133 prefix와 본 보고서/compact diagnostic을 새로 기록했다. **현재 문서 final-fresh 자격은 NOT_RUN**; 마지막 기존 문서자격 r128/P325와 새 runtime100 수용을 구분한다. 목표 ACTIVE, P10 진입 금지 유지.
