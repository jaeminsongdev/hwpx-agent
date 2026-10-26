# P09 블록 선택 진단 복구와 실제 문단 좌표 변환

> 최신 결과:670 source capture는 최종 cleanup=true로 성공했고 소비됐다. **아래670 명령은 재실행 금지다.** 두 원본의 블록8개 XML·텍스트는673에서 검증했다. 이후 진행은 [672~675 제품 읽기 모델](P09_BLOCK_BOOKMARK_SOURCE_AND_PRODUCT_672_675.md)을 따른다. 목표 ACTIVE, 현재 외부 실행 요청 없음.

2026-10-25 실행 전 기록. 당시 제품 기준은639이며 P09/A12/A13은 OPEN이었다. 아래는 F11 블록 책갈피 원본 확보를 위한 검증 코드 수정과 실행 전 인계 이력이다.

## 664 결과와 재실행 없는 복구

[664 원본](evidence/p09-361-block-selection-probe664-native001.v1.json)은 FAILED 상태와 SHA `20027de30f0248fdebcf54de81f639f244cae09c9728b161e5b96b7c9e4eea31`을 그대로 유지한다. Native worker는 의도한 진단 종료 신호를 반환했고8개 관측과 정확한 한글 owner의 정상 종료가 남았다. 원래 controller가 성공한 source capture에 필요한 case 종료 경계까지 요구한 것이 최종 실패 원인이다. 진단의 실패 finish는 해당 경계를 닫지 않으며, 이를 과거에 닫힌 것으로 바꾸지 않는다.

[667 복구](evidence/p09-361-block-selection-recovery667-audit001.v1.json)는 기존 Native를 재실행하지 않고 원본 영수증·private trace와 producer를 결속했다. 현재 source266/266·image1/1·shell1/1·runtime2/2를 확인하고 새 reader만 닫았다.10개 복구 조건·cleanup=true, 61.985초·CPU 최고31.59%·가용 RAM 최저46.7720%다. 상태는 `RECOVERED667_RETAINED_DIAGNOSTICS_NOT_SOURCE_OR_API_PASS`이며 원본 실패 재분류, 과거 종료 해시, source/API/제품 성공을 주장하지 않는다.

관측 결과는 다음과 같다. 고정 입력 전체 텍스트는132문자·UTF8 146바이트이며 예상 해시와 정확히 일치한다. 진입 및 종료 커서는 `[0,0,16]`, 선택 모드는1이다. PowerShell6 OUT과 명시적 .NET6 OUT은 모두 false였고, ParameterSet 방식도 false이며 List/Para/Pos 값이 생성되지 않았다. 선택 텍스트 읽기도 실패했다.664의 CPU 최고61.24%·가용 RAM 최저51.7576%로 자원 보호 중단이 아니다.

650/655/660/664는 모두 소비된 시험이다. 같은 명령을 다시 실행하지 않는다. private trace에는 원문·예외 메시지 대신 제한된 관측 값과 해시만 남긴다.

## 좌표 결함과668 수정

기존 계획643의 selection은 고정 문자열 안의 **논리적 문자 오프셋**이다. 기존 writer는 이를 HWP의 native 위치로 그대로 전달해 첫 범위에 `0~10`을 요청했다. 실제 진단에서 커서는16이었다. [한컴의 설명](https://forum.developer.hancom.com/t/allreplace-findall/845/17)에 따르면 첫 문단 앞에 보이지 않는 SecDef·ColDef가 각각8 위치를 차지할 수 있다. 이는 논리 오프셋과 native 위치를 동일시한 결함을 설명하는 근거다. 수정의 실제 한글 성공은 새 실행에서 확인해야 한다.

668 writer는 각 범위의 현재 owner를 확인하고 `SetPos(0, paragraph, 0)` 후 `GetPosBySet`으로 실제 시작점을 읽는다. List/Para/Pos의 자료형·문단·범위를 확인하고 시작점에 논리 오프셋을 더한다. 고정 `+16` 보정이나 대체 API 재시도는 없다. 이후 기존 typed Bookmark parameter 확인, 네 번의 범위별 host checkpoint, 정확한 여섯 선택 좌표 검사를 유지하며, 선택 텍스트의 길이·UTF8 SHA도 두 번 확인한다. 선택이 바뀌거나 텍스트가 다르면 Bookmark Execute 전에 중단한다. 임의 CRLF 제거 등 결과 정규화로 검사를 통과시키지 않는다.

[669 코드 검증](evidence/p09-361-block-bookmark-origin669-code001.v1.json)은20개 실제 함수 모델을 통과했다. 관측 시작점16/0 및 다른 문단별 시작점, 잘못된 좌표·자료형·owner·텍스트·정리 실패·재시도 금지를 검사했다.7/7·cleanup=true, 4.953초·CPU 최고17.61%·가용 RAM 최저49.1119%다. 실제 한글/API 성공은 미검증이다.

## 소비된670 source capture 실행 전 기록 — 아래 명령 재실행 금지

[671 진입점 코드 검증](evidence/p09-361-block-bookmark-source671-code001.v1.json)은 변경 controller19·worker8조건을 확인했다.669의20조건은 보존하고 반복하지 않았다. 기존 lifecycle·Native timeout·resource·입력 경계와 worker 실행 틀의 동일성을 확인했으며, 실제 worker에는 READY1회 거부만 전달하고 case는0이었다.322/322·cleanup=true, 57.797초·CPU 최고72.35%·가용 RAM 최저46.6335%다. Hwp 프로세스 집합은 변하지 않았고 source 폴더를 만들지 않았다.

새670은 현재 외부 실행자 자격과 세션 qualification을 통과할 때만 새 고정 문서1개·블록8개를 작성하고 저장·독립 재열기한다. 기존647의55요청, 두 owned session, CPU/RAM·commit95%·1코어·낮은 우선순위·정확한 PID/owner·강제 종료 금지·일회 claim을 유지한다. 원본643의 논리 범위, 실제 문단 시작점, 변환한 native 범위,16회 좌표·선택 텍스트 해시를 모두 검증한다.

별도로 연 PowerShell에서 다음 명령을 **한 번만** 실행한다. 이전664와650/655/660은 실행하지 않는다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_block_bookmark_source670.py' --execute-source-once
```

접근 허용 창이 나타나면 사용자가 눌러야 할 수 있다. 중간 worker 반환은 최종 cleanup·입력 감사 완료가 아니다. 최종 JSON으로 판단한다. 성공하더라도 블록 HWPX/XML의 이름·범위·텍스트 분석, 실제 제품의 블록 모델/생성 및 Content 양성, 남은 F11 기능과 P09 Gate는 별도다.

670 사전검사는 source324/324·image1/1·shell1/1·runtime2/2·cleanup=true다.69.235초·CPU 최고53.36%·가용 RAM 최저48.5641%였다. 한글 잔여 프로세스는0개이며, 유일한 실패 조건은 Codex 상위 Job의 `caller_lifecycle_native_safe`다. 이를 우회하지 않는다.670 claim·source 폴더·Native 실행은 아직 없으며, 외부 실행에서는 현재 자격을 다시 검사한다. 사용자 조건부 지시에 따라 위 새 명령 안내 후 목표를 PAUSED로 인계한다.
