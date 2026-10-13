# P09-336 — CPU STOP warm 재개 최적화와 실제104 수용 (2026-10-10)

## 확인된 결과

목표 ACTIVE, 제품 수용 **98/249**, 잔여 **151=145 regular+6 corpus**, next **105**. 성공 제품 source-closing pending0, whole reconciliation pending **95**. P09/A12/A13 OPEN. 249개는 이 runtime 검증군이며 전체 P09 진행률이 아니다. whole1470/full249/signed16/제품 완료/PC 프리즈 해결을 주장하지 않는다.

**실제104** `actual_import::formula_product_request::nochange_protected_and_invalid_second_section_cannot_be_successful_noop_or_partial_product`의 제품 자식 1개가 실제 Job 안에서 PASS, full1654의 원 두 byte/identity/정리 후 caller의 수용 PASS. 기존 통과 본체 재실행0. 이후 105를 대상으로 계약과 독립 fresh를 마쳤으며 아직 105 제품을 실행하지 않았다.

## 이번 own-code 최적화

같은 두 controller 경로를 P333→P335(v4)로 갱신했다. full1654/controller187/code91/directory308은 불변. 변경 전 두 파일의 정확한 bytes/hash는 `evidence/p333-formal482-code/`, 현재 수용된 코드는 `evidence/p335-formal528-code/`에 보존했다. 원 P333 실패·빈 body·수용되지 않은 STOP와 이전 모든 증거는 그대로다.

- 원 감시기/잠금/reader/stream 정리가 확인되고 제품 시작 전인 CPU STOP만 **작은 코드 자격을 유지하며 blocking stdin idle**로 돌아간다. 실패 결과를 actual 수용으로 바꾸지 않는다.
- 마지막 원 실패 root의 write를 원 writer 한 번에 hash/bytes 기록한다. 추가 재읽기·샘플러·Native query·새 자식을 만들지 않는다.
- 실패 즉시 actual 자격은 지운다. 다음 요청은 정확히 같은 root pin의 독립 STOP review여야 한다. 다른 root·직접 actual·fresh만으로 review 건너뛰기 모두 거부한다.
- STOP review 이후에도 새 독립 light-review 없이는 actual GO를 거부한다. 자동 재시도 없음.
- Native partial acquire는 모든 열린 handle/dup/reader/stream 정리가 필수. owned_parent는 원 sidecar가 실제 DEFERRED_NOT_STARTED/workerFALSE/JobFALSE/owned_tree_empty/cleanupTRUE임이 필수다. post-product/불명확한 정리/부분 sidecar/다른 resource 오류는 계속 세션을 닫는다.
- warm 시험의 바깥 pending STOP pin도 원 객체로 복원한다. idle summary에는 큰 원장·표본·Frame·Reader·Native handle을 넣지 않는다.
- P333 원본 코드 archive와 메타데이터 qualification을 논리 source pin과 구분한다. p333 run006 anchor STOP도 새 Reader에서 독립 분류·최종 fresh했다. 과거 source를 현재 Native 자격으로 위장하지 않는다.

구문검사 PASS. 기존241에 23개 계약을 더해 current264/following264, **총528** 실제 계약 검사 PASS. fixture 독립복사/원 per-test checkpoint·두 runner·skipped0 범위를 유지했다. 단일코어/BelowNormal·원 CPU98x4·RAM/commit 비율·Native600/metadata720·14/20/32 no-burst·원 1/2MiB byte pacing·Job 제한/cleanup 불변.

## CPU STOP 후 단계별 검토

`locked-r07/p335-case-104-run003.v1.json`는 **source_frame_acquire** CPU STOP, 실제제품0:
잠금624 opened/624 closed, remaining/failed close/reader/stream0, Frame CLOSED/unregistered, byte boundary0, parent adapter/connectionFALSE, sidecar없음. prep128bound/128fresh/256read/12,226,110bytes finishedTRUE.

149 원 표본에서 own private 최대53,313,536bytes, own CPU 최대6.463878%, RAM free 최소39.409960%. 마지막4표본은 host99.03/100/100/100, ownCPU 모두0, logical read delta 모두0. 즉 이 표본에서 own process가 전체 CPU/RAM을 먹었다는 증거는 없다. 간접 IO/보안검사 기여나 외부 CPU 원인, PC 프리즈 원인은 미확정이다.

원 native acquire/open_pacer/phase14과 source frame 경로를 정적으로 재검토했다. 조상 방문은 이미 중복 재순회하지 않고, pacing은 실제 sleep/최대64반복이며 원 deadline·checkpoint를 수행한다. 실사용 byte/identity를 생략하거나 정리된 과거 partial byte·잠금을 재사용하지 않았다. STOP 이후 독립 review와 새 fresh가 통과한 뒤 명시적 한 번의 재개만 했다.

## 실제104 run006 검증

- root667,184bytes SHA `1ceb8955c548d5defe07f5f4aca97180a637c5cc55441e7e7eab75cae01c5fd9`
- body191,227bytes SHA `04644c29b17b108a89d7c13b6b1749cbfc092e58a48911433cd8f41071f31930`
- 전체 **1,654 inputs / 120,895,337bytes**를 **before와 after 각각 완전 읽음**. 원 binary1MiB/s/other2MiB/s. bytes 합계241,790,674.
- 1,962 입력/조상 lock 전부 close. 3,308 borrowed duplicate 모두 close. 실패·remaining·reader·stream0.
- Frame COMMITTED/unregistered. closing identity regular1654/directory308, pathname reopen0.
- 실제 worker_created/job_assigned/actual_job_membership_checked TRUE, actual productTRUE, exact test1 PASS, exit0, owned tree empty/cleanupTRUE, parent elapsed262.35s.
- prep131bound/131fresh/262read/12,822,858bytes, post body1bound/1fresh/2read/382,454bytes, finishedTRUE.
- 현재 code91을 별도 fresh의 code pins/제품 source_freeze/원 bound metadata와 비교한 결과 **91/91 모두 일치**.
- 원 watcher858표본, own CPU 최대6.500956%, own private 최대57,331,712bytes, RAM free 최소39.466443%, STOP없음. host 순간max100은 98x4 sustained STOP 또는 프리즈 원인을 뜻하지 않는다.

Native는 여기서 Windows 소유 입력 잠금·byte frame 검증이다. 한글 저장·재열기/시각 oracle PASS가 아니다.

## 독립 fresh 및 다음 경계

모든 receipt는 `implementation/p09/evidence/locked-r07/` 아래.

| receipt | 결과 | 별도 fresh |
| --- | --- | --- |
| p335-light-run001.v1.json | 528 계약 PASS, actual0 | 126bound/126fresh/252read |
| p335-light-review-run002.v1.json | 독립 메타데이터 PASS, 계약 재실행0 | 127bound/127fresh/254read |
| p335-case-104-run003.v1.json | CPU STOP, 624 전부 정리, actual0 | prep128fresh |
| p335-stop-review-run004.v1.json | 원 STOP 독립 검토 PASS, 원FAILED 그대로 | 129bound/129fresh/258read |
| p335-light-review-run005.v1.json | 재개 전 별도 독립 fresh PASS | 130bound/130fresh/260read |
| p335-case-104-run006.v1.json | 실제104 수용+원 전체 frame PASS | prep131fresh/post1fresh |
| p335-light-run007.v1.json | 수용98/next105에서 계약528 PASS, 제품 재실행0 | 133bound/133fresh/266read |
| p335-light-review-run008.v1.json | 같은98/151/105/code91의 독립 fresh PASS | 134bound/134fresh/268read |

독립 fresh008의 SHA `ec92b0fe4a6fce0443e0b4fccd5feaac85a2dc357b6b9380fd21a3142b232655`, 40,338bytes, 14,630,596bytes 읽음. whole reconciliation pending95와 P09 GateOPEN을 유지한다.

추가 요약 `p336-warm-stop-actual104-diagnostic-run01.v1.json`은 진단 요약이지 새 제품/문서 자격이 아니다. 현재 상태 문서 final-fresh 마감은 **NOT_RUN**. r128/P325가 마지막 기존 문서 자격이며, 새 실제104 수용과 독립98 fresh는 원본 새 receipt로 입증한다. r131 문서 전문은 `evidence/runtime-progress-r131/`에 보존했다.

목표를 일시정지하거나 완료하지 않았다. 다음은105의 exact-one 실제 검증과 새로운 STOP가 있으면 해당 코드/표본/정리 검토다. PTYS16972/ownPython167172는 fresh008 후 단일코어 BelowNormal의 blocking stdin idle로 유지한다. 활성 감시기·Frame·제품 자식·Job0, 자동실행0. 다음 explicit actual은 run9와 기존 review004 pin을 사용하며, 소스변경/세션소실이면 새 fresh 자격 없이는 GO하지 않는다.

Git/Review·Cargo/build·한글/접근허용·외부 프로세스/Defender/WSL/OS 변경·원격 push·설치·삭제·이동 없음.
