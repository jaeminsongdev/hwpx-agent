# P09 블록 책갈피 생성 실패 진단과 후속 실행

> 2026-10-25 현재: **650/655/660/664는 모두 소비된 시험이며 아래 명령은 재실행 금지다.** 최신 내용과 새670 명령은 [664 진단 복구·실제 문단 좌표 변환666~671](P09_BLOCK_SELECTION_RECOVERY_AND_ORIGIN_666_671.md)을 따른다.664 관측8개는667에서 재실행 없이 복구했다.668은 논리 문자 오프셋을 관측한 native 문단 시작점으로 변환한다. 실제 제품639·블록 원본/Content 미완료·P09/A12/A13 OPEN을 유지한다.

## 소비된664 실행 전 준비 기록 — 아래 명령 재실행 금지

새664는 현재 세션 자격을 먼저 검사하고, 고정된 새 문서의 첫 선택 범위에서8개 관측을 수집한 뒤 책갈피 Execute·저장 전에 종료한다. 기존 캡처 시험을 재실행하거나 좌표 검사를 생략한 성공 경로가 아니다. 별도로 연 PowerShell에서 아래 명령을 한 번만 실행한다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_block_selection_probe664.py' --execute-probe-once
```

고정 관측은 진입 시 선택 모드, 시작 커서, 전체 입력 텍스트 해시·일치 여부, 선택 텍스트 해시·일치 여부, PowerShell6 OUT, 명시적 .NET6 OUT, ParameterSet의 전후 상태와 반환, 마지막 커서·선택 모드다. 관측 중 API false·예외가 있더라도 그 자체를 숨기지 않고 남긴다. 모든 관측과 정확한 producer·cleanup·입력 경계가 닫히면 최종 상태는 `OBSERVED664_SELECTION_DIAGNOSTICS_NOT_SOURCE_CAPTURE`이며, source capture·API 자격·제품/Gate PASS는 모두 false로 유지한다. 중간 `intentional_diagnostic_stop_reported=true`는 책갈피 Execute 전에 의도적으로 멈췄다는 뜻이고 cleanup 완료를 뜻하지 않는다.

[665 code003](evidence/p09-361-block-selection-probe665-code003.v1.json)은 진입점 고유14모형 중12개를 보존하고 영향2개만 재실행해 모두 확인했다. 실제 worker는 READY1회 거부·case0, 전체327/327·cleanup=true다. 57.672초·CPU 최고20.70%·사용 가능 RAM 최저43.0441%였다. 663 본체14모형을 다시 돌리거나 한글을 실행하지 않았다.

[664 사전검사](evidence/p09-361-block-selection-probe664-inspection001.v1.json)는source329/329·image1/1·shell1/1·Python2/2·cleanup=true, 70.266초·CPU 최고12.40%·사용 가능 RAM 최저44.0661%다. Hwp0이며 caller lifecycle만 부적격이다. 상위 Job 보호를 우회하지 않고 외부 PowerShell의 현재 자격이 필요하다. claim·진단 폴더·새 Native 관측은 아직 미생성이다. 명령 안내 후 사용자 조건부 지시에 따라 목표를 PAUSED로 둔다.

665 code001은 모형 Boundary의 label 누락2건으로, code002는 원문 보관 파일 끝에 추가된1바이트 LF 때문에 전체 파일 SHA 대조에서 멈췄다. 두 실패와 당시 소스를 보존했다. code003은 보관 자료에서 원본 길이와 SHA로 원본 모든 바이트의 동일성을 확인하고 추가 LF만 별도 구분한다. 진입점 코드는 proof 포인터만 변경했고 검증 조건·실패 원본·원본 캡처 수용 조건은 완화하지 않았다.

## 660 조회 API false 진단

[실제 영수증](evidence/p09-361-block-bookmark-source660-native001.v1.json)은119507바이트, SHA256 `97da434dd6ca1dac41da5ba1b4d38c667f80b9682b91b18de8943d045831f1b1`다. 현재 세션 qualification은 exit0, 캡처는13요청 후 exit2였고 최종 cleanup=true다. 218.625초·CPU 최고47.85%·사용 가능 RAM 최저38.9933%로 자원 보호 중단은 아니다.

private trace에는 첫 범위의 `mode=1`, `returned=false`, `positions=null`이 남았다. [한컴 SelectionMode 설명](https://developer.hancom.com/en-us/webhwp/devguide/hwpctrl/properties/selectionmode)의 일반 텍스트 블록 모드와 일치하지만 좌표 조회 성공은 입증되지 않았다. 포인터 OUT 대신 ParameterSet을 쓰는 변경만으로 해결되지 않았으며 실제 문서의 입력 내용·선택 상태·호출 전달 중 무엇이 원인인지는 미확정이다.

662는 같은 고정 새 문서에서 텍스트 해시·길이·고정 입력과의 일치 여부, 커서 좌표, PowerShell OUT·명시적 .NET OUT·ParameterSet 결과와 전후 선택 모드를8개 고정 관측으로 수집한다. 명시적 .NET 호출은 [Microsoft의 ParameterModifier COM by-ref 방식](https://learn.microsoft.com/en-us/dotnet/api/system.reflection.parametermodifier?view=netframework-4.8.1)을 사용한다. 원문 텍스트·예외 메시지는 기록하지 않는다. 책갈피 Execute/SaveAs 전에 진단 전용 종료를 수행하며 API false/예외는 관측으로만 남기고 source/제품 성공으로 바꾸지 않는다.

[663 코드 검증](evidence/p09-361-block-selection-probe663-code001.v1.json)은 신규14모형·11/11·cleanup=true, 5.234초·CPU 최고11.91%·사용 가능 RAM 최저43.4124%다. 전체 controller/실제 세션 관측은 별도 검증이 필요하다. 원 CPU·RAM/commit95%·1코어·낮은 우선순위·정확한 owner·입력/lifecycle/강제종료 금지 경계는 유지한다.

## 655 선택 좌표 검사 실패

[655 실제 영수증](evidence/p09-361-block-bookmark-source655-native001.v1.json)은117019바이트, SHA256 `a077bc3bbf7799337061b0232493d6131d3c9319969111351e2daaee825435f5`다. 현재 세션 qualification은 exit0, 캡처는13요청 후 exit2였으며 최종 cleanup=true다. 217.047초 동안 시스템 CPU 최고20.31%, 사용 가능 RAM 최저52.3360%로 보호 중단은 아니었다.

실패 위치는 첫 범위의 `assert_selection`이며 실제 책갈피 Execute 전이다. 직접 name/type/Command 설정·readback, `SelectText`의 true 반환과 nonempty selection-mode 검사는 통과했다. HRESULT `0x80131501`은 좌표 불일치를 거부한 RuntimeException의 값이지, 원 COM 호출 실패가 확인됐다는 뜻은 아니다. 기존 trace에 실제6좌표가 없어 선택 자체의 차이와 포인터 OUT 전달 차이를 구분할 수 없다.

## 동일한 선택 조건을 유지하는 후속 경로

[설치본 선언657](evidence/p09-361-block-bookmark-selection657-inspection001.v1.json)은 원 GetSelectedPos의6개 LONG 포인터 OUT과 `CreateSet`·`GetSelectedPosBySet`의 실제 선언을 서버 활성화 없이 확인했다. [한컴의 ParameterSet 방식 설명](https://forum.developer.hancom.com/t/topic/1532)에 따라 새658은 ListParaPos 두 세트를 만들고 List/Para/Pos를 읽는다. 이는 포인터 전달 의존성을 없애는 별도 구현이며655의 정확한 원인이 입증됐다는 주장은 아니다.

시작/끝 목록 ID0, 정확한 두 문단·글자 위치, nonempty selection, API bool 반환, 현재 owner·document 일치를 그대로 요구한다. VARIANT 항목은 bool/실수/문자열/64비트/음수/overflow를 거부하고 I4로 정확히 표현 가능한 int32/uint32만 허용한다. 선택 직후와 실행 직전의 좌표16건이 모두 원 고정8범위와 일치해야 전체 캡처 결과를 결속한다. 실제 숫자 좌표는 private trace에만 남기며 문서 텍스트·원문 예외를 게시하지 않는다.

[659 선택 모형](evidence/p09-361-block-bookmark-selection659-code001.v1.json)은29개 통과·8/8·cleanup=true, 5.093초·CPU 최고18.55%·사용 가능 RAM 최저42.0553%다. [661 전체 진입점 코드](evidence/p09-361-block-bookmark-source661-code001.v1.json)는controller16·worker8모형과 실제 READY1회 거부/case0,309/309·cleanup=true다. 55.625초·CPU 최고30.08%·사용 가능 RAM 최저43.2988%였으며29개 선택 모형은 이 단계에서 다시 실행하지 않았다. 새 한글이나 기존650/655는 실행하지 않았다.

원 CPU·RAM/commit95%·1코어·낮은 우선순위·현재 lifecycle·owner·입력 검증·Native 제한과 강제종료 금지는 유지한다. 전체 원본 캡처와 실제 block XML/Content 양성은 아직 미완료다.

## 660 실행 전 명령 기록 재실행 금지

[660 실행 없는 사전검사](evidence/p09-361-block-bookmark-source660-inspection001.v1.json)는source311/311·image1/1·shell1/1·Python2/2·cleanup=true이며 한글·claim·원본 폴더를 만들지 않았다. 67.812초·CPU 최고28.12%·사용 가능 RAM 최저41.8933%였다. 기존 Hwp는0개이며 `caller_lifecycle_native_safe`만 거부돼 Codex 안에서 Native를 실행하지 않는다. 이 사전검사를 Native 세션 자격 통과로 취급하지 않는다.

별도로 연 PowerShell에서 새660을 한 번만 실행한다. 기존650/655 명령은 다시 실행하지 않는다. 현재 세션 자격을 통과할 때만 고정1문서·8블록의 생성/저장/독립 재열기를 시도한다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_block_bookmark_source660.py' --execute-source-once
```

새 claim/결과/scratch와 `private/p09-361-block-bookmark660-source-document001`을 사용한다. 접근 허용 창은 사용자가 직접 처리해야 할 수 있다. 종료 후 마지막 JSON을 확인하며 자동 재시도하지 않는다. 명령 안내 후 목표는 사용자 조건부 지시에 따라 PAUSED로 둔다.

## 아래 내용은 655 실행 전 준비 기록

650 외부 실행은 현재 세션 자격을 통과한 뒤 첫 책갈피 생성에서 실패했다. 최종 정리는 확인됐지만 블록 HWPX는 생성되지 않았다. **650은 소비된 시험이므로 재실행하지 않는다.** 새 655는 실제 설치본에서 확인한 직접 속성과 호출별 진단을 사용하며, 외부 PowerShell의 현재 자격 검사를 통과할 때만 별도 원본 캡처를 1회 수행한다.

P09 범위와 목표 P09~P20은 유지한다. 실제 제품 기준은639이고 P09/A12/A13은 OPEN이다. 블록 원본 캡처가 성공하더라도 XML 범위·이름·텍스트 결속과 제품 Content 양성 검증은 후속으로 남는다.

## 650 실행 결과

[실패 영수증](evidence/p09-361-block-bookmark-source650-native001.v1.json)은115375바이트이며 SHA256은 `1d468b67f6ed889cc67607ddd8ffc84004af1d534bee8d29c799693ebd5d927c`다. Qualification은 exit0/cleanup=true, 캡처는 exit2/cleanup=true다. 전체221.781초, 시스템 CPU 최고42.94%, 사용 가능 RAM 최저44.3215%로 CPU/RAM 보호 중단은 아니었다.

고정 문서의 텍스트 삽입과 첫 `bookmark_prepare` checkpoint는 반환됐다. 첫 `bookmark_select`와 책갈피 `Execute` 전 실패했으며, `block_ranges`는 비어 있다. 기존 진단이 예외를 일반 오류로 바꿨기 때문에 정확히 어느 getter·GetDefault·설정·readback 호출이 실패했는지는 확정할 수 없다. 실패 원본과 private trace·forensic 자료, 사용한 소스와 claim은 보존한다.

## 실제 설치본 선언과 수정 내용

[완전 선언 검사652](evidence/p09-361-block-bookmark-surface652-inspection001.v1.json)는 COM 서버를 활성화하지 않고 실제2020 `HBookMark`의 전체 멤버를 읽었다. 기존 대소문자 구분 필터의 `Name`·`Type` 목록은 실제 lowercase `name`·`type`을 놓쳤다. 따라서 이전의 직접 속성 미관측 판단은 더 이상 적용하지 않는다. 이 검사 결함과650의 정확한 예외 원인은 구분한다. generic `SetItem('Name', ...)`가 실제 실패 호출이었다고 단정하지 않는다.

| 직접 속성 | DISPID | 읽기 반환형과 쓰기 입력형 |
| --- | --- | --- |
| `name` |28703| BSTR |
| `type` |28704| UI4 |
| `Command` |28705| UI4 |

설치본 typelib SHA256은 `abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9`다. 후속653 범위 writer는 이 세 직접 속성을 사용하고 각 읽기 직후 타입·값을 검사한다. 블록 Type1/생성 Command0, 정확한 선택 좌표, 실행 직전 재확인, host checkpoint, owner identity, RCW 해제와 실패 후 재시도 금지는 유지한다. generic item-key의 대소문자를 추정하지 않는다.

실패 진단은 고정 call-site·범위 번호·예외 종류·관측된 HRESULT만 보존한다. 원문 예외 메시지나 문서 값은 게시하지 않는다. PowerShell ScriptProperty 모형은 getter 예외를 null로 바꾸는 특성이 있어, 해당 경우에는 즉시 readback 거부 위치와 그 거부 예외를 기록한다. 이를 원 COM 예외 HRESULT가 복구된 것으로 주장하지 않는다.

## 로컬 검증 결과

| 범위 | 결과 | 입력 fresh와 final | 자원과 정리 |
| --- | --- | --- | --- |
| [654 code003 직접 속성과 오류 주입](evidence/p09-361-block-bookmark-source654-code003.v1.json) |24모형 통과|9/9|4.594초, CPU 최고13.28%, 사용 가능 RAM 최저45.7470%, cleanup=true|
| [656 code001 새 controller와 worker](evidence/p09-361-block-bookmark-source656-code001.v1.json) |controller15·worker8모형 통과, 실제 READY1회 거부, case0|295/295|53.750초, CPU 최고21.68%, 사용 가능 RAM 최저43.0244%, cleanup=true|
| [655 실행 없는 현재 사전검사](evidence/p09-361-block-bookmark-source655-inspection001.v1.json) |claim·Native·문서 생성0, Hwp0, caller lifecycle만 거부|source297/297, image1/1, shell1/1, Python2/2|66.234초, CPU 최고13.65%, 사용 가능 RAM 최저44.7499%, cleanup=true|

656은 직전654의24개 통과 모형을 다시 돌리지 않고 같은 소스 해시로 유지했다. 기존650 controller/entry와 새655의 변경이 namespace·typed-port wiring·제한된 진단에 한정되는지도 대조했다. CPU·RAM/commit95%·1코어·낮은 우선순위·정확한 owner·원 lifecycle·입력 검증·Native 제한은 낮추지 않았다. 이 과정에서 새 한글은 실행하지 않았다.

654 code001의4개 모형 실패와 당시 소스는 보존했다. 모형 GetDefault가 public setter 오류를 너무 일찍 주입한 문제와 ScriptProperty getter 예외 동작을 확인한 뒤 모형 및 즉시 readback 진단을 수정했다. code002는 private spool 경로가001과 충돌해 게시되지 못했으며 수용 결과로 세지 않는다. 해당 driver도 별도 source-archive에 남겼다. 새 code003은 별도 immutable spool로 검증과 게시를 완료했다.

## 외부 PowerShell에서 새 원본 캡처

현재 Codex parent는 원래의 `caller_lifecycle_native_safe` 조건을 만족하지 않는다. 보호를 우회하지 않으며 별도로 연 PowerShell에서 아래 명령을 **한 번만** 실행한다. 관리자 권한은 필요 없다. 접근 허용 창이 나오면 사용자가 직접 처리해야 할 수 있다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_block_bookmark_source655.py' --execute-source-once
```

새655는 사용하지 않은 claim·결과·scratch와 `private/p09-361-block-bookmark655-source-document001` 경로를 사용한다. 이전650의 경로나 claim을 재사용하지 않는다. 현재 세션 qualification과 정리가 닫힌 뒤에만 고정1문서·8블록의 생성/저장/독립 재열기를 시도한다. 이는 CROSSREF8종이나 제품 SDK 삽입 수용이 아니다.

현재 claim과 원본 폴더는 미생성이다. 사용자 조건부 지시에 따라 명령을 안내하고 목표를 PAUSED로 유지한다. 종료 후 마지막 JSON을 받으면 그 영수증부터 확인하며, 실패하더라도 이 명령을 자동 재시도하지 않는다.
