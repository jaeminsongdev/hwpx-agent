# P09 630 — 제품 생성 후보 8개용 Native 캡처 실행기

> 630 native001은 소비됐고 부분 캡처 뒤 실패했다. 아래630 명령은 역사 기록이며 **재실행하지 않는다**. 현재 명령과 수정/검증 근거는 [631 잔여6개 인계](P09_PREPARED_BOOKMARK_NATIVE_TAIL_631.md)를 따른다. 630의 원본 실패·cleanup=false와 사례3 부분 산출물을 보존하고, 닫힌 사례1·2만 캡처 증거로 결속했다. 필드/렌더 의미 PASS는 아니다.

## 결과와 실행 범위

[code006](evidence/p09-361-prepared-bookmark630-code006.v1.json)은 **외부 단발 캡처 실행기의 코드 자격**을 확인했다. 통신14조건, port 모델7조건, entry 예외 처리3조건, 묶음 이력 reader2조건의 고유26조건과 실제 x86 worker의 ready 거부/현재 세션 worker의 상위 Job 거부를 결속했다. 코드 자격 확인 중 한글·COM 서버·Native·Cargo·운영 SQL은 실행하지 않았다.

이것은 **실제 한글 8종 실행 성공이나 필드 의미/렌더 PASS가 아니다.** 실제 실행은 아래 사용자 명령에서 현재 조건을 다시 검사하고, 같은 호출의 세션 자격이 통과할 때만 시작한다. 629의 과거 성공 영수증은 세션 허가로 사용하지 않는다.

새 worker는 628이 생성한8개 후보를 차례대로 열고 `initial.hwpx`, `initial.pdf`, `saved.hwpx`를 새로 저장한 뒤 첫 세션을 종료한다. 다른 정확한 kernel lifetime의 한글 세션에서 `saved.hwpx`를 열어 `reopened.hwpx`, `reopened.pdf`를 저장하고 종료한다. 사례마다 producer/owner·입력 원본·해시·실패/종료 상태를 남긴다. PDF는 Native 저장 후 관측이며, 저장 전 화면이 직접 관측됐다거나 초기 계산이 맞았다고 주장하지 않는다.

SDK 삽입·REF-036 새로고침·원본 덮어쓰기·revision 게시·CAS·기존 소비001~010/Native008~011 실행은 없다. 다른 대상 종류와 의미/이동/이름 변경·렌더 차분 등의 F11 마감 조건은 계속 남는다.

## 외부 PowerShell — 한 묶음 1회

관리자가 아닌 별도로 연 PowerShell에서 아래를 **한 번만** 실행한다. 현재 사용 중인 한글이 없어야 한다. 접근 허용 창이 나타나면 사용자가 직접 누른다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_prepared_bookmark_native630.py' --execute-prepared-eight-once
```

기존629 `--inspect-only` 명령은 반복하지 않는다. 630은 현재 사전 조건 → 단발 claim → 같은 호출 세션 자격 → 고정8개 캡처 순서이며 case/generation/path/retry 선택 인수가 없다. 오류가 나거나 일부 사례만 반환해도 재실행하지 않는다. 마지막 JSON을 전달하고 원인을 먼저 검토한다.

`CURRENT_NATIVE_WORKER_ACTIVE`는 현재 작업의 자원 표본이다. `WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL`의 `work_continuing:false`/`cleanup_pending:true`는 작업 진전이 아니라 동일 owner의 종료 대기다. 이 상태이면 반복 실행하지 말고 상태를 전달한다. Ctrl+C는 새 실행 허가가 아니며, 미확인 cleanup도 통과로 만들지 않는다.

산출물은 새 비공개 `evidence/private/p09-361-prepared-bookmark630-native001-c01`~`c08`에만 생성한다. claim과 최종 영수증은 각각 `evidence/p09-361-prepared-bookmark630-claim001.v1.json`, `evidence/p09-361-prepared-bookmark630-native001.v1.json`이다. 원본·준비 후보·기존 실패 파일을 덮어쓰거나 삭제하지 않는다. claim을 만든 호출이 실패하면 그 실행을 재사용하지 않는다.

## 보호 및 구현

- 기존 preassigned Native 시작·정확한 PID/birth/session/이미지/window 검증·같은 owner의 종료·살아 있는 단발 handoff와 비강제 종료 정책을 그대로 사용한다. Codex 상위 Job을 탈출시키거나 scheduled task/detach/breakaway 우회를 하지 않는다.
- CPU/RAM/commit95%·1코어·낮은 우선순위·기존 Job hard cap/메모리 분할/입력·시간 제한은 유지한다. Native 자원 보호에 준비 전용 CPU 정책을 적용하지 않는다.
- 공개 protocol 단계는 `candidate_open`, `initial_snapshot`, `initial_pdf`, `saved_save`, `fresh_saved_open` 등 새 목적이다. 내부 자원 상태 기계의 기존16-slot 순서만 재사용한다. 내부 `sdk_insert` 슬롯은 여기서는 `initial_pdf`의 자원 checkpoint일 뿐 실제 SDK 호출/결과를 뜻하지 않는다. 이전 SDK dispatcher나 고정 배치를 호출하지 않는다.
- 원본 후보와 재열기 입력은 Open 전에 read/no-write/no-delete lease를 얻고 같은 바이트의 해시를 확인한다. 실제 paired document/collection/application/window/owner 검사를 유지한다. uncertain owner가 남으면 lease도 유지하고 같은 Native 종료 뒤 EOF에서만 해제한다.
- 첫 case 실패를 finish acknowledgement보다 먼저 보존해 정리 오류가 주 실패를 가리지 않게 했다. 새 entry는 subprocess timeout/OS 오류/interrupt를 안전한 코드로 기록하고 자동 재시도를 금지한다. 원문 문서 값·전체 로그·arbitrary exception 문자열은 출력하지 않는다.
- 현재 코드/실제 실행 입력은 사례마다 fresh/final 검사한다. 과거 영수증·시험·archive 이력은 묶음 시작/종료의 원본 확인에만 두며 사례마다 과거 검증 체인을 다시 읽지 않는다. 기존 보호나 실제 실행 입력을 제외한 것이 아니다.

## 검증 세대와 실패 보존

| 세대 | 실제 확인한 범위 | 결과 |
| --- | --- | --- |
| code001 | 원606 영수증 SHA 복사 오타 | 제품/시험 시작 전 FAILED, 원본 보존 |
| code002 | 현재 session worker5730bytes가 과거407의5277bytes와 다름을 탐지 | 시험 시작 전 FAILED, 과거 source를 현재 자격으로 잘못 쓰지 않음 |
| code003 | 통신14·새 worker 실제 ready 거부·현재 session worker 실제 상위 Job 거부/constructor trap0 | 254fresh/final254·cleanup true·48.610초·CPU22.61%·가용 RAM43.1461% |
| code004 | 동일 본문14 보존, port 모델7, 변경된 worker의 실제 준비 거부 확인 | 259fresh/final259·cleanup true·49.656초·CPU19.34%·가용 RAM46.6374% |
| code005 | 동일한14+7/두 실제 거부 근거 보존, 새 entry 예외3만 실행 | 263fresh/final263·cleanup true·34.375초·CPU23.88%·가용 RAM45.7707% |
| code006 | 동일한24조건/실제 거부 근거 보존, 묶음 이력 reader2만 실행 | 267fresh/final267·cleanup true·35.172초·CPU21.39%·가용 RAM46.7074% |

code006은 과거 이력을 Native 사례별 입력에서 분리하면서도 실제 묶음의 reader가 이력 전체를 시작/종료에 읽도록 결속했다. Native의 사례별 실행 입력240개와 별도 이력/외부 proof 입력을 구분한다. 테스트로 변경된 이력의 거부와 ‘이력은 전체 확인하되 case 경로에 넣지 않음’을 확인했다. 같은24조건을 다시 실행해 횟수를 늘리지 않았다.

[게시된 entry reader 확인](evidence/p09-prepared-bookmark630-published-entry-check.v1.json)은 최종 code006을 실제 `load_code`로 읽고 현재 실행 입력240개+별도 이력/바깥 입력28개 및 후보8개의 전체 byte를 확인했다. 268fresh/final268·cleanup true·35.032초·시스템 CPU 최고18.16%·가용 RAM 최저46.3551%다. 이전 시험을 재실행하거나 entry의 Native 분기를 호출하지 않았다.

원 session worker 파일을 이번에 수정한 것이 아니다. 변경된 현재 source를 명시적으로 결속하고 기존 constructor trap/정확한 worker kernel lease와 genuine root denial을 실제로 다시 확인했다. 407의 자격을 근거 없이 이어 붙이지 않았다. 과거 product249/Native 시험은 재실행하지 않았다.

port 모델은 모의 객체이며 실제 한글 SaveAs/계산·표시·이동·재열기 성공의 대체 근거가 아니다. 실제 ready 거부 역시 문서 실행 전에 이루어졌으며 Native 생성0이다. PC 프리즈의 원인 규명이나 완전 해결을 주장하지 않는다.

## 인계와 다음 판정

사용자 요청에 따라 외부 명령을 인계하고 결과 대기 동안 목표를 PAUSED로 둔다. 실제 현재 세션 자격이 실패하면 제품8개를 실행하지 않는다. 모두 반환돼도 우선 캡처 결속/cleanup/최종 hash를 확인하고, 실제 HWPX 필드·대상·보존과 PDF/text/geometry 의미를 별도 판정한다. `CAPTURED630...SEMANTICS_UNQUALIFIED`를 F11/P09 PASS로 바꾸지 않는다.

P09/A12/A13 OPEN·31미마감묶음·65기능·공식249의158수용/91대기/next165·P10 새 구현 보류는 그대로다.
