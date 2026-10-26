# Handoff 기록

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`

개발 세션 종료 시 `templates/HANDOFF.md`를 복사해 순번 파일을 추가한다. Handoff는 채팅 요약이 아니라 저장소 상태, 완료/미완료 작업, 검증 증거, 결정, 다음 명령을 연결하는 실행 기록이다.

최근 조사: [P09 이후 잔여 범위와 병렬 개발 진행안](0003-p09-p20-delivery-audit-20261026.md) 및 [작업별 목록](0003-p09-p20-task-audit-20261026.csv). 목표는 일시정지 상태이며 제품 Gate 변경은 없다.

규칙:

- 파일명: `NNNN-<topic>.md`
- 현재 `CURRENT_STATE.md`, `ROADMAP_STATUS.yaml`, 관련 ADR/WBS task와 일치해야 한다.
- “완료”에는 실행한 검증과 증거 경로를 반드시 적는다.
- 실제 한/글 oracle을 수행하지 않았다면 `unverified`로 기록한다.
- 비밀, 사용자 문서 원문, 라이선스 파일은 기록하지 않는다.
