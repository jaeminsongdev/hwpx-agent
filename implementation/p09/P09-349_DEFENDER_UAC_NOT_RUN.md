# P09-349 — Defender 관리자 추적 요청 취소

## 후속 정정 — 사용자 외출 중 (P350)

사용자가 외출 중이라 PC를 직접 조작할 수 없다고 명확히 설명했다.
승인 UI/버튼 자체의 고장으로 확인된 것이 아니다. 이전의 버튼 상태 확인 요청은
더 진행하지 않는다. 관리자 추적을 최적화 선행 조건으로 삼지 않고 검증 코드의
중복 pathname 조회와 사용하지 않는 fixture 복사를 수정했다.
상세 상태와 미검증 경계는 `P09-350_UNPRIVILEGED_VERIFICATION_CODE_OPTIMIZATION.md`에 있다.
아래 기록은 당시의 시도/취소 이력이며 추가 UAC 실행 지시가 아니다.

날짜: 2026-10-10.

사용자가 15초 관리자 Defender 성능 추적에 동의했다. 고정 경로의 timed capture helper를
작성하고 PowerShell AST 구문 오류0을 확인했다. helper SHA256:
BCBCFC18B2F579EF3C0E782BB710200F4301C2A078336AA5C578176C0506436C

Windows PowerShell을 RunAs/Hidden/NoProfile/NonInteractive/File로 요청했지만,
사용자가 관리자 승인 버튼을 누를 수 없다고 알렸다. helper는 시작되지 않았고
출력 디렉터리·started receipt·ETL 모두 없었다.

요청 취소를 위해 exact owned launcher pwsh PID392228의 이름·부모PID708596·
helper 파일명·dispatch marker를 다시 확인한 뒤 해당 프로세스만 종료했다.
PTY63087 terminal exit-1을 확인했다. 이후 해당 helper/launcher0, started receipt없음,
ETL없음을 확인했다. consent.exe, Defender, Codex, MapleRust 등 다른 프로세스는 종료하지 않았다.

## 결과

- Defender 기록: NOT_RUN_USER_CANNOT_APPROVE_UAC.
- 관리자 원인: 승인 불가능하다는 사용자 보고 외 상세 원인은 아직 모른다.
- 필터 목록이나 ETW 권한을 우회하지 않았다.
- HWPX 검증/제품/계약검사 재실행0, Defender/OS/WSL 설정 변경0.
- helper는 보존했지만 이것은 구문 확인일 뿐 실제 capture/analyzer 자격이 아니다.
- P348의 source035 실패와 Defender85.2% 관측은 그대로 유지한다.
- P09 및 프리즈 원인·해결은 미완료다. 목표 상태를 임의 pause/blocked/complete로 바꾸지 않았다.

다음은 승인창이 보이지 않는지, 버튼이 비활성인지, 클릭이 반응하지 않는지를 확인하는 사용자 설명이다.
원시 trace 파일은 생성되지 않았으므로 비밀정보가 포함된 trace/log를 출력하거나 공유하지 않았다.

