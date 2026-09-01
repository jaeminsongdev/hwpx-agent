# 스크립트·자동화·이벤트 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

오토메이션은 raw action 실행기가 아니라 버전 고정 allowlisted semantic binding 계층이다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (25개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| AUTO-001 | HwpObject 생성·종료 | `auto.hwpobject_lifecycle` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-002 | 오토메이션 문서 열기·저장 | `auto.document_open_save` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-003 | allowlisted Action 실행 | `auto.action_execute` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-004 | ParameterSet 생성·검증 | `auto.parameterset_build` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-005 | ParameterArray 생성·검증 | `auto.parameterarray_build` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-006 | 커서 위치 읽기·이동 | `auto.cursor_position` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-007 | 선택 범위 API | `auto.selection_api` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-008 | 본문 텍스트 추출 | `auto.text_extract` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-009 | 컨트롤 열거 | `auto.control_enumerate` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-010 | 컨트롤 속성 읽기·수정 | `auto.control_properties` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-011 | 이벤트 핸들러 등록 | `auto.event_subscribe` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-012 | 메시지/대화상자 정책 | `auto.messagebox_policy` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-013 | 파일 경로 보안 승인 모듈 | `auto.file_path_security` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-014 | 스크립트 매크로 정의 | `auto.macro_define` | `editor_workflow` | `DISABLED_BY_POLICY` | `desktop_automation` | P11 | policy_negative_test·trusted_mode_e2e |
| AUTO-015 | 스크립트 매크로 중지 | `auto.macro_stop` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-016 | 스크립트 매크로 실행 | `auto.macro_run` | `editor_workflow` | `DISABLED_BY_POLICY` | `desktop_automation` | P11 | policy_negative_test·trusted_mode_e2e |
| AUTO-017 | 매크로 기록 기반 action 발견 | `auto.macro_record_discovery` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-018 | 예상치 못한 modal 탐지 | `auto.modal_watchdog` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-019 | 한/글 프로세스 회수·재시작 | `auto.process_recycle` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-020 | 빌드별 기능 runtime probe | `auto.runtime_probe` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-021 | WebHWP HwpCtrl lifecycle | `auto.webhwp_ctrl` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `webhwp` | P10 | webhwp_contract·conformance |
| AUTO-022 | WebHWP Action 실행 | `auto.webhwp_action` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `webhwp` | P10 | webhwp_contract·conformance |
| AUTO-023 | WebHWP 이벤트 | `auto.webhwp_events` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `webhwp` | P10 | webhwp_contract·conformance |
| AUTO-024 | 배치 자동화 | `auto.batch_automation` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |
| AUTO-025 | action/parameter 실행 trace | `auto.automation_trace` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | worker_integration·state_probe·timeout_recovery |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/14_auto_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
