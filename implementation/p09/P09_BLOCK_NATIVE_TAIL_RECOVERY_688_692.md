> 후속 현재 상태: 새690의7~8번 캡처와 정리가 완료됐다. 명령을 다시 실행하지 않는다. 보존6종과 합친8종/32문서의 필드 API·그래프 및 전체Source 잔여는 [693~701 결과](P09_BLOCK_NATIVE_READBACK_AND_GRAPH_693_701.md)를 따른다. 목표 ACTIVE이며 현재 외부 실행 요청은 없다. 아래는 원래 준비/인계 이력이다.

# P09 Native684 실패 보존과 남은 7~8번 실행 준비

2026-10-25. 원래684 전체8종 실행은 FAILED로 보존한다. P09/A12/A13 OPEN, official249=158수용·91대기·next165, 잔여31개 closure 묶음/65기능은 변경하지 않는다.

## 확인된 실행과 원인

최종684 영수증은 `evidence/p09-361-prepared-bookmark684-native001.v1.json` 123,302B, SHA `970f50e7fad3b67c8f150cfd593873898f75d65535a8daf0400f1a399655ab27`이다. state는 `FAILED684_BLOCK_PRODUCT_CAPTURE`, error는 `XREF_PREPARED631_DRAIN_SINGLE_RETIREMENT_PER_SESSION`, cleanup=true, source974/974다. 원시 metadata 1,017,480B와 SHA `443570e4f6b4ba2d8aa43eb92d747066d3b0bd6a46a8a743f81af1c45b2794e2`를 별도 spool에 보존했다. 전체758.672초·시스템CPU최고42.97%·가용RAM최저46.3272%다. CPU/RAM 보호 중단이 아니다.

원인은 6종 tail용 `prepared_bookmark631_drain.wait`의 `len(records)<=12`를8종에서 그대로 호출한 구현 누락이다. 1~6번은12세션을 닫았고,7번 save 세션의13번째 정리 검사에서 실패했다. 부모의 실패 EOF가 worker에 전달돼7번 trace에는 `P09_XREF_BIND_HOST_REPLY_EOF`가 기록됐다. 최초 실패와 worker의 후속 EOF는 구분한다. 최종 worker/native cleanup은 완료했다.

## 688 보존 재감사

`audit_prepared_bookmark688 --audit-no-native`는 기존 source/실행 code, 각 사례의 닫힌 입력 경계, 정확한 PID/생성 시각/세션/owner 이력, initial/saved/reopened HWPX와 초기·재열기 BMP/trace를 실제 파일 SHA에 결속했다.6사례×6산출물=36개이고, Native를 다시 실행하지 않았다. 같은 과거 입력은 묶음 안에서 합집합으로 한 번 보관해 사례마다 전체 이력을 재검사하지 않는다.

7번의 initial/saved HWPX·초기BMP·실패 trace 4개는 부분 결과로 보존하며,8번은 NOT_RUN이다. 684의FAILED를8종 성공이나 의미 PASS로 바꾸지 않는다. 6개 캡처 보존도 실제 표시값/탐색 의미 PASS를 뜻하지 않는다.

- 영수증: `evidence/p09-361-prepared-bookmark688-retained-six001.v1.json`,82,432B, SHA `013282e1b1fe21a06744b094f7a30a826ecaba0436279021ffeffa7109f5a836`.
- state: `QUALIFIED688_SIX_CLOSED684_CAPTURES_RETAINED_SEVENTH_PARTIAL_NOT_PROMOTED`.
- source1016/1016·cleanup=true·185.844초·CPU최고39.65%·가용RAM최저49.8807%.

## 수정689와 새690 경계

소비된631/684 코드는 수정하지 않는다. 새689 `SessionRecords(planned_cases)`는 trusted fixed 사례 수1~8만 받아 최대 세션을 `2*planned_cases`로 계산한다. 각 record는 정확한 int PID·양의 생성 시각·세션 ID를 요구하며, 같은 세 키의 중복/계획 초과/잘못된 값이 생기면 후속 기록을 봉쇄한다. 단순히12를 큰 수로 바꾸지 않는다. 실제45초 drain 본문·원래 CPU/RAM/worker 관찰·정확한 handle/tree 종료·no force kill는 유지한다. 8종13번째/16번째 허용,17번째 거부와2종4회/5회 거부를 별도로 검사한다.

새690은681 manifest의 source 사례7·8만 선택한다. 런타임 ordinal1·2를 source index7·8에 결속하며, 새 private 폴더 `p09-361-prepared-bookmark690-native001-c07/c08`에만 쓴다. 기존684의7번 부분 파일도 덮어쓰지 않는다. 초기값은 `SessionRecords(2)`라 최대4세션이고, 4개의 세션과2개 입력 경계가 닫혀야 batch를 닫는다. 기존1~6번은 처음/최종 묶음 경계에서 실제 SHA를 확인하며 재실행하지 않는다.

현재 signed Python/한글/x86 shell, original limited Job·1코어/낮은 우선순위·CPU/RAM/commit95% 보호·정확한 PID/owner·입력 lease/fresh/final SHA·실행마다 session 자격과 같은 handoff·제품10초·section600초/전체1800초·실패/no retry를 유지한다. 새 런의 `fixed_eight_executed`는 false다. 이 실행은2종뿐이며, 성공 시 `remaining_two_executed`와 보존6+새2 캡처 완결 여부를 별도로 기록한다. 의미나 P09 완료는 계속 false다.

## 코드 자격 검사

기존687의34조건은 동일 코드로 보존하고, 새 계획 정리/중복/CPU거부/handle 오류/7~8 mapping/실행 경계/ports·worker projection에 대한24조건과 PS syntax/profile4조건을 검사한다. 691의 최초24조건은23통과·worker 시작 guard의 옛8종 옵션 참조1개 실패였다. 실패 원본과 당시 worker/entry를 보존하고 guard 참조 한 곳만 새2종 옵션으로 수정했다. 692는 통과23을 보존하고 수정1과 아직 미실행인 PS4·실제 READY 거부를 검사한다. 실제 READY에서는 Native release를 보내지 않는다.

692 자격 검증은 `QUALIFIED692_BLOCK_TAIL_TWO_CODE_AND_REAL_READY_DENIAL_NOT_NATIVE`로 통과했다. 새24모형은691의 통과23개를 정확한 입력으로 유지하고 수정된1개만 실행했다. 새 PS4검사는 현재 실행했다. 기존34모형과 실제1~6번 Native는 재실행하지 않았다. 실제 worker READY1프레임에 거부 응답을 보내 planned2/completed0/retained0/exit2/cleanup=true를 확인했고, 한글 프로세스는 전후0이다.

영수증 `evidence/p09-361-prepared-bookmark692-code001.v1.json`은90,840B, SHA `d2c25b7ef52eccc66b2d3b152fbe664e708141eae4efbb7385baa25ba2637728`이다. source1037/1037·cleanup=true·178.719초·CPU최고34.5%·가용RAM최저50.0670%다. 691 실패는 보존한다.

새690 Native는 미실행이다. 현재 Codex caller 사전검사도 완료했다. `OBSERVED690_CURRENT_PREREQUISITES_NOT_NATIVE_OR_SESSION`·cleanup=true·source1038/1038·189.765초·CPU최고44.73%·가용RAM최저48.9765%다. 원래 자원 정책/한글 등록/실행파일/no preexisting Hwp는 true, `caller_lifecycle_native_safe`만 false다. 새 Native/claim/접근 허용 요청은0이다. 영수증 `evidence/p09-361-prepared-bookmark690-inspection001.v1.json`은80,556B, SHA `2970585cb60ef5fdf5cfaaab136595b439c6d8cd3533ef274262ad13a695252d`이다.

## 실행 명령과 일시정지

Codex 밖에서 별도로 연 PowerShell에서 아래 명령을 한 번만 실행한다. 관리자 권한은 필요 없다. 현재 session 자격을 통과한 경우에만 source7·8의 새2종을 실행한다. 접근 허용 창이 나오면 사용자가 직접 누른다. 기존684 명령과1~6번은 재실행하지 않는다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_prepared_bookmark_native690.py' --execute-remaining-two-once
```

사용자의 외부 명령 전달 후 정지 조건에 따라 목표를 PAUSED로 인계한다. 최종 JSON과 PowerShell 프롬프트 복귀를 확인한다. 중간 worker 결과는 최종 정리 완료가 아니며, 실패하면 이 명령도 자동/수동으로 반복하지 않고 원본 결과를 먼저 확인한다. 실제2종과 보존6종의 표시/target 의미·시각 비교·다른 F11/P09 closure는 아직 닫히지 않았다.
