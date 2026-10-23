# P09 블록 원본 고정 worker·채널 — 648~649

## 결과와 남은 경계

647 host 순서에 맞춘 고정 PowerShell worker·채널과 created 저장→독립 재열기→reopened 저장/이미지 경로를 연결했다. 아직 이 worker를 실제 Native로 실행하지 않았다. 현재 세션 자격 검사·live handoff·전체 입력 경계·일회용 claim·실제 산출물/producer 검사·결과 게시를 묶는 최상위 controller/외부 entry는 다음 작업이다. 사용자 실행 명령은 아직 없다.

P09/A12/A13 OPEN·31미마감묶음/65기능·최신 실제 제품639·목표 ACTIVE를 유지한다. 모델/READY 거부 결과는 실제 블록 HWPX나 Content 양성, F11 또는 P09 완료가 아니다.

## 구현

- `run-block-bookmark-source648-worker.ps1`: 원32비트 STA PowerShell/제한 worker envelope, 정확한 worker kernel identity와 현재 host release를 요구한다. COM 활성화/fallback Native launch는 하지 않고 기존 preassigned owner에만 연결한다. release 전에는 owner 연결/문서 동작/출력 폴더 생성 단계에 들어가지 않는다.
- `block-bookmark-source648-channel.ps1`: 647의 닫힌54요청 순서와 고정 pulse/step wire. 생성2개 응답에만 owner descriptor를 허용하며 엄격한 타입/정규 JSON/실행 허가=false를 확인한다. host 거부 후 새 작업은 금지하고 실패 finish1회만 허용한다. 기존 owner의 Admit 함수는 worker-local 새 채널을 사용한다.
- `block-bookmark-source648-flow.ps1`: 고정643 private 폴더, 미저장 document→645 seed/8범위→created.hwpx/BMP→원 소유 세션 종료→독립 owner의 created 재열기→reopened.hwpx/BMP→종료. 원 P58/preassigned owner/631 read lease·IO·BMP·cleanup 함수를 재사용한다. 원본 덮어쓰기/임의 CLI 경로/재시도는 없다. 아직 모델 경로이며 실제 SaveAs/Open/Close 효과는 미검증이다.
- `block_bookmark_source648_worker.py`: 고정 bootstrap·script·mode만 구성하고 기존 worker CPU/Job/memory/affinity 구현을 바꾸지 않는다. 새 결과 profile의 실패/불완전 결과를 성공처럼 표시하지 않는 제한된 진단 함수를 추가했다. 실제 controller는 이 함수를 초기 result notice에 연결해야 한다.

## 001 실패와 정확한 원인 확인

최초001은 PowerShell7의17모델 중5개가 실패했다. 정상 채널 응답을 받는 시험들이 엄격한 INT32 검사에서 거부됐으며 Python6/READY 시험에 도달하지 않았다. cleanup=true, fresh60/final0, 11.703초, CPU 최고15.04%였다. 자원 보호 중단은 아니다. 원 영수증과 당시 test/driver 소스를 보존했다.

002의 읽기 전용 decoder probe에서 같은 JSON `{"sequence":1}`이 시험 PowerShell7에서는 `System.Int64`, 실제 대상 Windows PowerShell5.1 x86에서는 `System.Int32`임을 확인했다. Native 채널의 타입 검사를 완화하지 않았다. 새 채널 모델17개는 **검증 대상 shell이 바뀌었으므로** 실제5.1 x86에서 모두 실행했다. 이전7의12개 통과를 현재5.1의 증거로 대체하지 않았다. 기존645/647 시험 묶음은 재실행하지 않았다.

## 002 검증

새 channel/flow17과 fixed command/notice6이 통과했다. channel schema, current descriptor, pulse bound, 잘못된 권한/순번/키/정규 JSON 거부, host 거부와 실패 finish, 고정 step/seed dispatch/8범위, SaveAs 반환/이름 제한/이미지 범위/오류 비노출을 검사했다. 저장·문서 외부 포트는 모델이며 실제 HWPX 생성 근거가 아니다.

추가로 **실제 제한 worker**를 띄워 READY에 거부 응답만 보냈다. 같은 kernel worker lease, requests1/READY1/case0, exit2, completed0, retained owner0, 출력 디렉터리 미생성, Hwp PID 집합 불변, worker/IO thread/Job cleanup=true를 확인했다. 새 Native 시작·owner 연결·문서 생성/저장은0회다. 이는 실제 Native session 자격을 통과했다는 뜻이 아니다.

[649 code002](evidence/p09-361-block-bookmark-source649-code002.v1.json):9151bytes, SHA256 `62a35a83cbdd2a2ff694f63fdade9b945b6f0d6eed195e14be0bd69494166fb0`.

- fresh/final63/63, model shell/worker shell final 각1, cleanup=true.
- 27.5초, CPU 최고9.61%, 가용 RAM 최저50.0003%.
- 기존1논리CPU/BelowNormal·CPU·RAM/commit95% 보호 유지; 보호 중단0.
- [001 실패](evidence/p09-361-block-bookmark-source649-code001.v1.json)는 실패/final0 그대로 보존했다.

## 다음 작업

고정 source controller/entry를 구성하고 현재 lifecycle→동일 호출 live handoff→입력 전후 검증→1문서54요청→원 producer/owner cleanup→실제 산출물 해시→결과 보존/게시를 연결한다. 전체 entry를 Native 없이 검증하고 현재 외부 실행 필요 여부/허가를 확인한 뒤에만 실제 원본 캡처로 넘어간다. 이후 실제 HWPX block 이름/범위/텍스트를 관측하여 제품 block-target/Content 양성을 구현한다. 범용 P10 host나 다른 완료 시험 전체 재검증으로 확대하지 않는다.
