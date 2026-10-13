# P09-56 실제 결과 결합 검사와 전체 ready 대기열

Updated: 2026-10-03. State: `IMPLEMENTED / COMPLETE READY SOURCE PREFLIGHT PASS /
INDEPENDENT FRESH SOURCE VERIFY PASS / ACTUAL NATIVE NOT_RUN`.

## 이번에 구현한 것

이전 P55의 owned runner와 package comparator 다음 단계인 **실제 child 종료
코드·trace·산출물 결합 검사**, 전체 ready 대기열과 현재 결과 소비자를 구현했다.
현재 사용자 지시가 접근 허용 금지이므로 `--execute-native`는 호출하지 않았다.

- 새 field binder는 frozen P55의 정확한 trace schema/target/source/plan/self/
  library/security hash, UTC·서로 다른 두 세션·소유자·정리·종료 코드·서식 검사·
  실패 가능 단계 순서를 검사한다. 완료 문구만으로 성공을 인정하지 않는다.
- 완료 문구가 있어도 종료 코드/cleanup이 실패이면 lifecycle failure로 유지한다.
  rollback 또는 empty-field dirty/cache/prompt/package 복구 성공을 만들어내지 않는다.
- 주장된 파일은 실제 hash/bytes/PDF signature와 일치해야 한다. HWPX는 기존
  P55의 모든 expanded ZIP byte/inventory 비교 함수에 연결했다. 일치하지 않거나
  malformed인 파일은 거부 상태를 유지하고 render/product로 승격하지 않는다.
- 알려진 부분 파일은 보존하고, 0-byte 파일도 hash/count로 남기되 저장 성공으로
  인정하지 않는다. 알 수 없는 file inventory/외부 값/가짜 green은 거부한다.
- 고정 대기열은 기존 **양식15 + 누름틀2 = ready17 사례** 전부다. 원래 P52
  dispatcher의 **전체 run()을 그대로 호출**하고, 다음 두 P55 사례를 실행하도록
  연결했다. 복사한 일부 loop/selector/작은 두 사례만의 permission batch가 아니다.
- 완료 뒤 전체 P52 dispatch와 두 실제 P55 trace/artifact/exit를 재결합하고,
  기존 P53의 실제 SDK current consumer를 호출하도록 연결했다. 실제 배치 부재
  시에는 현재 결과를 생성하지 않고 NOT_RUN/0 cases를 반환한다.

이는 **변경된 ready17**의 실행 준비이며, P09 전체 owned46 reference coverage나
전체 제품 완료가 아니다. Render/direct-automation differential 소비자는 추가하지
않았으며 여전히 필요하다. Native 실행 분기는 인간이 다시 허용한 뒤에만 사용한다.

## 이번에 실제 실행한 검증

새 테스트 **11/11 PASS**. 출판·독립 fresh 검증 각각 실제 재실행했다.

- 정확한17 inventory, subset/reorder/alias/boolean coercion 차단.
- synthetic trace로 두 완전한 후보·실패 prefix·종료 코드/cleanup/단계 gap/
  중복·coerced PID/잘못된 시간/가짜 hash·target·green·서식 write claim 차단.
- 실제 SDK package bytes를 hypothetical output으로 쓰는 **in-memory** artifact
  결합 검사와 전체 package 비교. 이 synthetic traces는 native 파일로 쓰지 않았다.
- 0-byte partial은 보존하고 package comparison/acceptance로 승격하지 않음.
- complete17 dispatch가 없을 때 NOT_RUN/0 cases. Native/current capsule 미생성.
- 전체 dispatcher source가 원래 full15를 호출하며 timeout/kill/retry가 없는지 검사.

추가로 **17개 전부의 실제 x86 STA pre-native prefix**를 실행했다. P52의15
원본 prefix 및 P55 두 `-PreflightOnly`를 실행했으며 모두 exit0였다. 이는 단순
목록 작성이 아니라 실제 원본/계획/library/security/module/build/process 상태
검사이지만, COM 활성화·문서 열기·접근 허용·저장·재열기 증거는 아니다.
Source/context/기존 plans를 전후 재검사했고 모든 run directory가 부재였다.

## Source admission 및 보존

`evidence/p09-56-reference-native-queue.source-admission.v1.json`, **12622 bytes**,
SHA`3869c502ed4b7e1ba08f85e181f9dada3622a72a45e63a222fe8d6a267dd0de7`.
새 source **5개 pin** 고정. 출판 session81429와 독립 fresh session33451은
모두 terminal exit0/PASS. Fresh는 unit11와 actual17 prefixes 및 source/context
전후 검사를 다시 수행하고 receipt 전체 bytes가 같은지 확인했다.

실제 `--current` session24306도 terminal exit0:
`state=NOT_RUN,case_count=0,native_session_started=false,p09_complete=false`.
현재 결과나 가짜 dispatch는 쓰지 않았다. 알려진 실제 배치가 없으므로 성공
문구로 바꾸지 않았고 source proof를 현재 native evidence로 사용하지 않았다.

P55 source7/receipt6892/cb0a9215/계획3files4635, P54 및 P48-P53 original
source/receipt identity graph, 기존 SDK fixtures와 historical native 파일 **75개**
가 그대로다. 기존 source/workflow 자체를 재실행한 것은 아니며 P52 prefix15는
새 combined17 protection에 실제 재사용한 것이다. 전체 ordinary suites PASS도 아니다.
원래 실패/920-pixel mismatch는 미해결 상태로 보존했다. Hwp.exe0이며 새 native
run directory/trace/dispatch/current capsule은 없다. `git diff --check` PASS.

## 남은 실제 완료 경계

현재 native 실행 금지를 유지한다. 나중에 인간이 허용하면 같은 고정 전체 ready17
대기열을 실행하되, 변경된 source/environment/이미 사용한 attempts는 먼저 차단한다.
Known safe-cleanup failure는 보존하며 계속하고, 누락/invalid trace·남은 프로세스·
변경된 source는 다음 활성화를 중단한다. Partial batch를 자동 재시도/덮어쓰기하지 않는다.

실제 callback/owner/cleanup/clone/style/rollback, 빈 필드 의미, 저장·재열기,
전체 package 결과와 unmasked render/direct-automation differential은 NOT_RUN이다.
Full reference coverage·입력/date/default/validation/protection·signed route/
publication/CAS/idempotency/CLI/full import 및 P09 Gate도 미완료다. Goal ACTIVE,
0 green, P10 구현 없음. 전체 목표를 ready17 source 성공으로 축소하지 않는다.
