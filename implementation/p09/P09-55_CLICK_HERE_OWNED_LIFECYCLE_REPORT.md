# P09-55 누름틀 서식 보존 후보의 독립 lifecycle 연결

Updated: 2026-10-03. State: `IMPLEMENTED / SCOPED SOURCE PUBLICATION PASS /
INDEPENDENT FRESH SOURCE VERIFY PASS / NATIVE NOT_RUN`.

## 실제 구현 변경

이전 P54의 private worker에서 멈추지 않고, 고정 원본·계획·owned 세션·저장 후
read-only 검사·새 세션 검사를 연결한 **새 실행기**를 구현했다. 이전 P54 여섯
source와 receipt4891/c300baf9는 그대로 보존했다. 최신 사용자 지시는 접근 허용
금지이므로 실행기의 native 분기는 한 번도 실행하지 않았다.

- 실행기는 C01/C02의 정확한 원본 두 개와 고정 plan SHA만 허용한다. 원본/출력/
  RunDirectory/ProgID/build를 임의로 전달할 수 없다. 원본 링크·변조·기존 Hwp와
  기존 출력은 차단하고, self/new library/P54/P50/EXE/DLL/security module을 검사한다.
- 기존 P54 전체 글자서식 보존 함수를 호출하기 전에 원래 CharShape 전체 clone을
  독립적으로 얻고, 적용 직후·저장 후에 읽기 전용으로 비교하는 코드를 연결했다.
- 새 세션에서는 원본을 **다시** 열어 baseline을 새로 얻는다. 첫 세션의 COM
  clone을 넘겨 프로세스를 유지하지 않는다. 저장된 결과를 연 뒤에는 값을/서식을
  다시 적용하지 않고, 원본 전체 parameter-set 일치와 필드 값을 검사한다.
- HWND→PID→실행 파일/세션/생성 시각으로 소유자를 묶고 종료 직전 재확인한다.
  소유자 미확인 시 blanket Quit/강제 종료를 하지 않는다. 실패 후 저장 없이
  닫는 요청과 실제 프로세스 종료 결과를 분리해서 기록하도록 구현했다.
- 별도 Python 소비자는 실제 기존 SDK 출력과 **모든 expanded ZIP byte/전체
  inventory**를 비교한다. 필드 값이 같아도 header/resource 등의 변경은 거부한다.
  XML/metadata/공백/style ID를 정규화하거나 변경을 숨기지 않는다.

위 lifecycle와 ownership/cleanup은 **구현된 후보 코드**이지, 실제 native 효과
검증이 아니다. 정확한 HWND mapping·Close(false)의 프롬프트 없는 동작·IsEquivalent·
실제 rollback·saved package·render/differential은 NOT_RUN이다.

## 이번에 실제 실행한 검증

새 테스트 **11/11 PASS**, 출판과 독립 fresh 검증 각각 재실행했다.

- 두 정확한 원본→동일 frozen P54 plans, 기존 production-SDK 출력 두 개의 실제
  전체 package 비교. 기존 lowering fixture/원본을 재생성하거나 수정하지 않았다.
- 파일 내용을 그대로 두고 ZIP storage만 바꾼 실제 in-memory archive는 SOURCE
  비교만 통과한다. 이 결과를 native/render 성공으로 승격하지 않는다.
- unmanaged header 공백 한 byte 변경은 필드 state가 같아도 전체 비교에서 거부.
  extra part·원본을 결과로 제출·잘못된 ZIP/traversal·다른 case도 거부한다.
- 실제 **x86 STA** 자식에서 동일 실행기의 `-PreflightOnly`를 두 사례 모두 실행.
  `-ExecuteNative`는 전달하지 않았다. native boundary 전에 종료했고 Hwp.exe0 및
  새 native run directory 부재를 확인했다. wrong plan/self/library SHA 세 자식은
  각각 기대한 `P55_PLAN_SCOPE`/`P55_FILE_IDENTITY`로 거부됐다.
- pure parameter/selection 객체로 read-only 검사의 whole-style mismatch/잘못된
  값 차단을 확인했다. 이 synthetic fixture는 COM/native 증거가 아니다.
- 설치된 TLB에서 WindowHandle/두 Close/Quit/SaveAs의 다섯 exact declarations와
  parameter names를 검사했다. EXE/DLL/TLB identity/PID 집합은 그대로이며 COM
  server activation이나 native 메서드 호출은 없었다.

새 inspector 초기 수정에서 잘못된 C# loop-variable 이름 때문에 두 번 실패한
기록은 유지했다. 새 inspector의 이름을 실제 `k`/`obtained`로 고쳐 통과했으며,
기존 P54 inspector/기대 signature/검증 Gate는 변경하지 않았다.

## source 산출물과 보존

고정 private SOURCE plan bundle:
`evidence/private/p09-55-click-format-plans-20261003-r01`, **3 files/4635 bytes**.
두 plan1394/1396 bytes는 P54 compiler 결과와 exact; manifest1845 bytes/
SHA68c7f04574ffbec9a6ae74baba9cc0387e393f9dc240f1f733185ad667c460f3.
이것은 한글 trace/native 산출물이 아니라 이후 실행의 disposable 입력이다.
공개 source receipt에는 실제 값·폰트 문자열을 포함하지 않는다.

SOURCE progress receipt:
`evidence/p09-55-click-owned-lifecycle.source-progress.v1.json`, **6892 bytes**,
SHA`cb0a921596d1427d921063c8f0cd5bcc339749c5ff085e90d9a5a94810ce4b3b`.
새 source **7개 pin** 고정. 출판 session45975와 독립 fresh session28786은
각각 terminal exit0/PASS이며 fresh 결과 전체가 저장 receipt와 일치했다.

정확한 P54 여섯 source/receipt와 P48-P53 원본 identity graph, SDK fixtures,
기존 historical native 파일 **75개**를 전후 검사해 보존했다. 이전 workflow
자체를 다시 실행한 것은 아니며, 전체 ordinary Python/Rust suite PASS도 아니다.
`git diff --check` PASS. 새로운 한글 프로세스/실행 폴더/native trace/현재 native
결과는 생성하지 않았다. 생성한 source plans와 receipt는 삭제/덮어쓰기하지 않는다.

## 남은 작업과 다음 경계

이번 단계에서는 native owned runner와 whole-package 비교 함수를 만들었다.
그러나 실제 child exit/trace/artifact를 결합하는 현재 결과 binder 및 전체 대기
작업을 묶는 dispatcher/admission, 실제 render/direct-automation differential은
아직 필요하다. 비교 함수를 실제 저장 산출물에 적용한 native 결과도 NOT_RUN이다.

기존 P52 complete15 batch/P53 current consumer와 원래 920-pixel mismatch는
계속 미검증이다. 접근 허용을 금지한 동안 native branch나 작은 두 사례만의
permission batch를 시작하지 않는다. 목표 ACTIVE, P09 Gate OPEN/0 green,
P10 구현 없음. source 진행을 전체 제품 완료로 처리하지 않는다.
