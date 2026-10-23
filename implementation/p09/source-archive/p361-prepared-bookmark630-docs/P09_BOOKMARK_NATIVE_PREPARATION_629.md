# P09 629 — 새 삽입 8종의 읽기 전용 외부 준비 검사

## 현재 상태와 한계

[code002](evidence/p09-361-bookmark-native-preparation629-code002.v1.json)은 **읽기 전용 준비 검사만 검증**했다. 18조건 실행/오류0/실패0/skip0, 후보8개·입력210개 fresh/final210·cleanup true다. 전체42.281초, 시스템 CPU 최고11.72%, 가용 RAM 최저45.0616%다. Rust 제품·249큐·한글·COM은 실행하지 않았다.

**실물8종 실행기 준비 완료가 아니다.** 아래 명령은 후보8개/원본/출처와 현재 외부 프로세스·Python/한글 image·등록·빈 Job 제한만 검사한다. 문서를 열거나 저장하지 않으며 접근 허용 창도 요청하지 않는다. 성공 영수증은 미래 실행의 세션/owner 자격이나 승인으로 사용할 수 없다.

현재 Codex 안의 실제 검사에서는 상위 Job 때문에 `caller_lifecycle_native_safe`가 거부됐다. 거부를 우회하지 않았고 빈 Job도 만들지 않았다. 검증된 current Python558의 두 image profile을 재사용하며, 오래된 단일 Python image 해시로 fallback하지 않는다.

[게시 후 reader 검사](evidence/p09-bookmark-native-preparation629-published-code-check.v1.json)도 실제 명령의 `load_code`와 `validate_prepared`를 통해 통과했다. 이미 통과한18조건을 반복하지 않고 게시된 proof/현재 코드/파일210개 fresh/final만 확인했다. 27.547초·시스템 CPU 최고26.99%·가용 RAM 최저42.2303%·cleanup true다. [문서 동기화](evidence/p09-stored-bookmark628-preparation629-document-sync.v1.json)는5개 상태 문서의 역사 본문 전체 SHA와31개 묶음/65기능의 ID·UNCLOSED 상태를 확인했다. 최초 문서 검사에서 `state` 대신 실제 키 `status`를 사용해야 하는 검사식 오류를 바로잡았다. 묶음의 상태를 바꾼 것은 아니다.

## 외부 PowerShell 명령 — 읽기 전용 1회

Codex가 아닌 별도로 연 PowerShell에서 실행한다. 관리자 권한은 필요 없다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\inspect_bookmark_native_batch629.py' --inspect-only
```

영수증은 `implementation/p09/evidence/p09-361-bookmark-native-preparation629-external001.v1.json`에 새로 저장한다. 같은 명령을 반복 실행해 덮어쓰지 않는다. 다른 프로그램이나 한글 프로세스를 종료하지 않는다. `OBSERVED629_CURRENT_EXTERNAL_PREREQUISITES_AND_EIGHT_FILES_NOT_NATIVE_ENTRY_READY`도 Native/제품 PASS가 아니다. 실패·보호 중단이면 원 기록을 남기고 원인 코드부터 검토한다.

최초 로컬 code001은 실행 파일 allowlist에 Cargo를 지정한 오류로 Python 시험 실행 전에 거부됐다. 원 실패와 당시 entry/verifier source는 보존했다. Python의 정확한 경로만 허용하도록 수정한 code002에서18조건을 처음 실행했다. 어떤 보호 조건도 낮추지 않았다.

## 실물 묶음에 남은 구현 순서

| 순서 | 필요한 경계 | 현재 상태 |
| --- | --- | --- |
| 1 | 고정8파일과 원본·stored receipt·정확한 표시/hyperlink 순서·현재 runtime/등록/빈 자원 제한 | 로컬 코드/실제 Codex 거부 검사 완료. 외부 현재 관찰은 NOT_RUN |
| 2 | 새 목적의 verified entry/worker: 현재 preassigned Native 세션 자격·정확한 kernel owner와 살아 있는 단발 handoff | 미완. 옛 SDK 삽입기/소비010을 재사용하지 않음 |
| 3 | 후보8개를 차례로 열어 초기 결과/필드/대상 결속 관찰, 별도 새 저장본·독립 재열기16세션과 readback | NOT_RUN. SDK insert를 다시 호출하는 시험이 아님 |
| 4 | 실제 대상에서 독립 관측한 기대값과 계산/표시·hyperlink 이동·필요 텍스트/geometry/render 차분, 삽입 지점 밖 보존 | 검증기/관측 경계 준비와 실제 근거 필요. 현재 문자열을 기대값으로 돌려 쓰지 않음 |
| 5 | 시작/종료 fresh 입력·같은 owner의 종료·각 case 실패/원본·출력 보존, 전체8개 결과 판정 | NOT_RUN. 부분 성공을 전체 성공으로 승격하지 않음 |

한 묶음의 실행 준비·검증이 끝나고 실제 실행 범위가 확인된 후에만 실물 명령을 준다. 현재의 가능 여부 응답은 준비 지원이며, 과거 소비 실행이나 Native011의 새 실행 허가가 아니다. 현재 자격 실패를 무시하거나 우회 실행하지 않는다.

CPU/RAM/commit95%·1코어·낮은 우선순위·기존 Native hard cap/operation 제한·정확한 owner/Job·원본/입력 검증은 유지한다. 준비와 실제 제품의 보호 정책을 혼동하지 않는다. 실패 후 같은 검증의 자동 재시도는 없다. 종료 미확인이면 정확한 프로세스 증거를 보존하고 새 작업을 진행하지 않는다.

## 인계 상태

사용자의 “검사 준비되면 실행 명령을 주고 목표를 멈춰둘 것” 요청에 따라 위 읽기 전용 명령을 인계하고 목표는 PAUSED로 둔다. 현재 진행에서 동일 외부 장애가3회 연속 반복된 상태는 아니므로 도구의 BLOCKED 요건을 충족했다고 꾸미지 않는다. P09/A12/A13 OPEN·31미마감묶음·공식158수용/91대기/next165·P10 새 구현 보류는 그대로다. 이 인계는 F11이나 실물 실행 준비의 완료가 아니다.
