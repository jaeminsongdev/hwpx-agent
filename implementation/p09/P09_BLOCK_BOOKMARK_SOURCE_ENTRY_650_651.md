# P09 블록 책갈피 원본 일회용 entry — 650~651

> 2026-10-23 현재: **650은 외부 실행 후 `create_bookmarks`에서 실패한 소비된 시험이다. 재실행 금지.** 세션 qualification과 최종 cleanup은 확인됐지만 블록 HWPX는 생성되지 않았다. [652~656 진단·직접 속성 후속 실행](P09_BLOCK_BOOKMARK_TYPED_SUCCESSOR_652_656.md)을 따른다. 아래 명령과 준비 상태는 실행 전 역사 기록이며 현재 실행 지시가 아니다.

## 이하 650 실행 전 준비 기록 — 현재 실행 대기 아님

고정1문서·8블록 범위의 현재 세션 검사→동일 호출 live handoff→캡처→producer/정리→최종 입력/결과 보존 entry를 연결했다. 코드/모델 검증과 현재 Codex 사전검사까지 완료했지만 **새 Native 실행과 블록 HWPX 생성은0회**다. 실제 XML 매핑·제품 block-target/Content 양성·F11/P09 Gate PASS가 아니다.

현재 Codex의 상위 Job 종료 정책이 원 Native lifecycle 조건에 맞지 않는다. 이를 우회/완화하지 않고 외부 PowerShell의 현재 자격을 다시 검사한 뒤 통과할 때만1회 실행하도록 한다. 사용자 조건부 지시(외부 명령이 필요하면 안내하고 정지)에 따라 목표를 PAUSED로 두고 외부 결과를 기다린다.

P09/A12/A13 OPEN·31미마감묶음/65기능·최신 실제 제품639를 유지한다. 목표 P09~P20은 축소하지 않으며 새 P10/249전체/소비된 Native를 실행하지 않는다.

## 650 연결과 경계

- `run_block_bookmark_source650.py`의 `--inspect-only`는 claim/Native/source folder를 만들지 않는다. `--execute-source-once`는 코드/전체 의존 입력·현재2이미지 Python·x86 shell·등록/실행 파일·기존 Hwp 부재·jobless caller를 확인한 후에만 독점 claim을 기록한다.
- 원 SessionQualifier를 현재 호출에서 수행하고 실제 lifecycle/cleanup이 닫힐 때만 원 live handoff를 발행·소비한다. 저장된 코드 영수증은 Native 세션 허가가 아니다.
- 647 host/648 worker로1문서54요청(+READY1)을 실행한다. 각 범위 pulse는 원 kernel/CPU·RAM 보호를 사용하고 과거 시험 전체를 재검증하지 않는다.
- 현재 실행 파일·source·Python/shell은 준비/qualification/capture/case/final의 닫힌 경계에서 fresh/final 확인한다. 준비·qualification·capture·batch_close·final_audit5단계, 단계600초/전체1800초를 사용한다. 원 Native 시작/제품10초/CPU·RAM·정확한 owner·강제종료 금지 정책과 자원 이력은 바꾸지 않는다.
- 고정 산출물은 `private/p09-361-block-bookmark643-source-document001` 안의 created/reopened HWPX2개·BMP2개·trace다. 생성/재열기2개의 원 kernel producer/cleanup,8범위의 타입/좌표/반환,파일SHA/owner/이미지 profile을 결속한다. 이는 원본 캡처 결속이며 아직 실제 block XML/Content 의미의 수용이 아니다.
- 새 worker profile의 실제 실패/불완전 result를 원 IO의 legacy 성공 추측으로 표시하지 않도록 알림을 연결했다. 조기 notice와 원 forensic을 결과 게시보다 먼저 보존한다. claim 이후 자동 재실행은 없으며 기존 실패를 PASS로 고치지 않는다.

## 코드 시험과 원 실패 보존

651 code001에서15모델 중2error/1failure가 발생했다. 시험용 guard에 `windows` 속성이 빠져2경로가 실제 분기에 도달하지 못했고 정상 흐름 모델에는 I/O 인수 위치 오류가 있었다. Native0, cleanup=true, fresh275/final0, CPU 최고6.67%였다. 원 실패와 당시 entry/test/driver3개를 보존했다. 제한된3실패 진단에서 예외 타입/소스 위치만 확인하고 값/전체 traceback은 출력하지 않았다.

code002는 시험용 guard/모델 인수 위치와 새 코드 영수증 포인터만 수정했다. 원 controller 본문은 유지했다. 영향 없는 통과11개는 전체 본문/의존 입력을 결속해 재실행하지 않고, 실패3개와 fixture 영향으로 다시 확인해야 하는 거부1개만 실행해4/4 통과했다. 기존649의23모델/READY 시험도 다시 실행하지 않았다.

고유15제어는 CLI mode 제한, 단계 순서/닫힌 입력/자원 실패 latch/이력 보존, 실제 producer/5개 pin 검사 본문과 누락·BOOL범위·잘못된SHA/owner·의미 승격 거부, 코드 변경/비정수 카운터 거부, qualification 실패 시 capture worker 차단, 정상 controller 경계 순서, inspect/거부 entry의 no-claim을 포함한다. 외부 owner/Native/파일 IO는 모델이며 실제 Native 성공을 주장하지 않는다.

[651 code002](evidence/p09-361-block-bookmark-source651-code002.v1.json):26881bytes, SHA256 `55699bac142e9f1f8515e5d615b36904abd1747557f7617b0ee8a9acf202043e`.

- 실행 의존 입력 fresh/final279/279, x86 shell final1, cleanup=true.
- 49.407초, CPU 최고7.38%, 가용 RAM 최저50.8465%; 보호 중단0.
- [원 code001 실패](evidence/p09-361-block-bookmark-source651-code001.v1.json)는 실패/final0 그대로다.

## 현재 Codex 사전검사

[650 inspection001](evidence/p09-361-block-bookmark-source650-inspection001.v1.json):31929bytes, SHA256 `a627a439f7dd418583d70d6c12e973f32293ebe6c8f5e801c1b968280abba3bf`.

원 자원 정책/등록 server/현재 실행 파일/기존 Hwp 부재는 true다. `caller_lifecycle_native_safe`만 false이고 원 코드는 `XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE`다. 실행 중 Hwp0, source281/281·Native image1/1·x86 shell1/1·Python2/2, cleanup=true, 63.782초, CPU 최고8.33%, 가용 RAM 최저50.8228%다. Native claim/result/scratch/source folder가 모두 아직 없는 것을 확인했다.

이 관측은 외부 PowerShell의 자격을 대신하지 않는다. 외부 entry가 현재 조건을 다시 검사하고 실패하면 생성하지 않는다.

## 외부 실행 — 1회만

Codex가 아닌 별도로 연 PowerShell에서 실행한다. 관리자 권한은 필요 없다. 한글을 사용하지 않는 상태에서 실행하고 접근 허용 창이 나오면 사용자가 눌러야 할 수 있다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_block_bookmark_source650.py' --execute-source-once
```

종료 시 마지막 JSON을 전달한다. 중단/실패했더라도 같은 명령을 재실행하지 않는다. 이번 것은 보통 책갈피 CROSSREF8종의 재실행이 아니라 **블록 원본1문서/8범위 생성**이다. 캡처가 성공해도 P09 전체 완료는 아니며, 다음은 실제 HWPX 범위/이름/텍스트 분석과 제품 block-target/Content 양성 구현이다.
