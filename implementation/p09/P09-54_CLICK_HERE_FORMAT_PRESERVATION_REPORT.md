# P09-54 누름틀 글자서식 전체 보존 후보

Updated: 2026-10-03. Status: `PRIVATE WORKER IMPLEMENTED / SCOPED SOURCE CHECKS
PASS / INDEPENDENT FRESH SOURCE VERIFY PASS / NATIVE NOT_RUN`.

## 실제 변경

사용자 지시 `접근허용 띄우지 말고 딴거 해`에 따라 한글 실행·문서 열기·COM
활성화·접근 허용·native worker 호출·저장·재열기를 하지 않았다. 목표 ACTIVE,
P09 Gate OPEN, P10 구현 없음.

기존 P22 C01의 실제 920-pixel direct/native 차이를 조사해, 누름틀 값을 바꿀
때 원래 선택 영역의 글자서식 **전체**를 보존하는 private 후보 함수를 추가했다.
기존 SDK lowerer는 원래 서식을 보존하며 변경하지 않았다. 기존 실패를 삭제하거나
native 보존 성공으로 바꾸지 않았다.

- `tools/p09/click_here_format_plan.py`: 정확한 원본 두 캡처에서 입력 계획 생성.
  패키지/section/opaque parameters/원래 글자서식 정의/값 SHA 및 색·크기·기울임·
  굵기·7개 언어 폰트를 결합한다. 공개 결과에는 실제 값·폰트 문자열을 넣지 않는다.
- `implementation/p09/tools/click-here-format-preservation.ps1`: 함수 정의만 제공.
  유일한 필드 목록·원래 값·선택 상태를 검사하고, pinned P50 helper로 전체
  CharShape parameter set을 복제한다. 값 변경 전에 원래 서식과 폰트를 검사한다.
  변경 후 전체 clone을 적용하고 전체 IsEquivalent·필드 값·목록을 다시 검사한다.
- `tools/p09/inspect_click_here_character_typelib.ps1`: 별도의 REGKIND_NONE
  읽기 전용 inspector. 기존 P50 inspector·library·harness는 변경하지 않았다.
- 14개 테스트와 고정·exclusive SOURCE progress 기록기, 정책 문서를 추가했다.

혼합/누락 서식은 값 변경 전에 거부한다. source ID를 runtime ID로 추정하거나
CharShapeID만 재지정하지 않는다. rollback은 원래 값을/서식을 복원하려는 후보
동작이며, 빈 누름틀 dirty/cache/prompt/원본 package 복원을 증명하지 않는다.
오류 발생 시 미래의 owned-session harness가 흔적을 보존하고 **저장 없이**
자기 disposable 세션을 닫아야 한다. 실제 rollback 검증은 NOT_RUN이다.

## 근거와 검증

공식 cached `HwpAutomation.pdf`의 SHA는
`c787c69d46f26a9fca49ac9d34106bb4f146fb29da9f1caf92c6e77d46cef45b`.
PDF skill로 pp14-15/18의 실제 페이지를 렌더링해 확인하고 pp18-19 내용을
읽었다. 문서의 선택 영역 CharShape·혼합 값 누락·전체 필드 선택·동일 이름 전체
필드 변경 설명이 전체 clone/유일한 inventory/혼합 서식 거부에 반영됐다.
설명 자체가 현재 빌드의 native 보존 성공을 증명하는 것은 아니다.

실제 설치 TLB473120/abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9에서
37개 정확한 선언을 검사했다. COM server는 활성화하지 않았고 Hwp.exe는 0이었다.

- Python14/14 PASS: 두 실제 원본의 style7/red/italic 및 style0/black/nonitalic,
  Unicode UTF8 hash, strict plan, 잘못된 입력/ZIP/XML/서식/폰트 차단.
- 실제 x86 STA 및 pwsh에서 plan을 검증했다. style/selection objects는 순수
  fixture이며, 15개 style negative와 6개 selection negative는 native 증거가 아니다.
- 기존 production SDK `click_here_hwpx` Rust8/8 PASS,0 fail/ignored/filtered.
  actual captured package lowering을 포함하는 기존 원본 테스트를 수정하지 않았다.
- 출판 및 독립 fresh `--verify`가 각각 위 Python14/Rust8을 실제 재실행하고,
  source/원본/전체 predecessor identity/75개 historical native files를 전후 비교했다.
  이전 workflow 자체는 재실행하지 않았으며 전체 ordinary suite PASS도 주장하지 않는다.

SOURCE progress receipt:
`evidence/p09-54-click-format.source-progress.v1.json`, **4891 bytes**,
SHA`c300baf9ccbd79084a6ab8f841cf1c2dde6bc7982ee18b50e3f4205a9aa16b36`.
새 source6개 pin은 고정했다. 출판 session13229와 fresh session52688은 모두
terminal exit0/PASS. 원본 두 캡처·공식 PDF·P48-P53 graph·75개 native 원본은 exact.
Private plan/native run/current native capsule은 생성하지 않았다.

초기 실패 기록은 남겼다: 최초 Python12 중4개는 legacy shell의 모듈 초기화
progress stderr 때문에 실패했다(실제 validator 오류가 아님). 새 실행기의
ProgressPreference만 local child에서 지정해 수정했다. 최초 출판은 새 경로
검사 함수 위치 오류로 AttributeError, 다음 출판은 CRLF 및 x86 method 이름의
숫자를 놓친 reader regex로 실패했다. 새 reader만 수정했으며 기존 source,
정책/기대값/실패 artifact/증거 Gate는 약화하지 않았다.

## 아직 완료하지 않은 것

이 후보에는 새 owned lifecycle harness/dispatcher/native batch admission/product
route가 없다. 실제 호출하지 말고 다음 구현에서 원본 SHA·plan SHA·disposable
session·owner cleanup·실패 trace·전체 저장 package 비교와 결합해야 한다.

빈 필드 선택/전체 clone/IsEquivalent/서식 setter/rollback/caret 복원 실제 동작,
저장·재열기 후 opaque parameters/style bindings/모든 part 보존, unmasked render와
direct/automation differential은 모두 NOT_RUN. 원래 920-pixel mismatch는 미해결
검증 상태다. P52 complete15 batch와 P53 current consumer도 계속 NOT_RUN이다.
사용자가 접근 허용을 금지한 동안 의미 있는 permission-free 구현만 진행한다.
