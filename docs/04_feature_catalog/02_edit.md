# 편집·선택·클립보드 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

LLM이 커서 동작을 흉내 내지 않고 stable selector와 transaction으로 의미 편집한다. 순수 편집기 undo/clipboard는 automation session 기능이다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (28개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| EDIT-001 | 되돌리기 | `edit.undo` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-002 | 다시 실행 | `edit.redo` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-003 | 오려 두기 | `edit.cut` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-004 | 복사하기 | `edit.copy` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-005 | 붙이기 | `edit.paste` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-006 | 골라 붙이기 | `edit.paste_special` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-007 | 모양 복사 | `edit.format_painter` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-008 | 선택 내용 지우기 | `edit.delete` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P04 | semantic_reopen·selector_tests |
| EDIT-009 | 조판 부호 지우기 | `edit.delete_layout_marks` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P04 | semantic_reopen·selector_tests |
| EDIT-010 | 모두 선택 | `edit.select_all` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-011 | 텍스트 범위 선택 | `edit.select_text_range` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-012 | 문단 선택 | `edit.select_paragraph` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-013 | 개체/컨트롤 선택 | `edit.select_control` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-014 | 표 셀 범위 선택 | `edit.select_table_cell_range` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-015 | 커서 이동 | `edit.move_cursor` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-016 | 찾아가기 | `edit.go_to` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-017 | 정렬 | `edit.sort` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-018 | 고치기/속성 편집 | `edit.edit_properties` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-019 | OLE 연결 관리 | `edit.ole_link_manage` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-020 | OLE 개체 속성 | `edit.ole_properties` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-021 | 클립보드 내용 확인 | `edit.clipboard_inspect` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-022 | 텍스트로 복사 | `edit.copy_as_text` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-023 | 그림으로 복사 | `edit.copy_as_image` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | semantic_diff·session_state_probe·undo_smoke |
| EDIT-024 | 블록 이동 | `edit.move_block` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P04 | semantic_reopen·selector_tests |
| EDIT-025 | 블록 복제 | `edit.duplicate_block` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P04 | semantic_reopen·selector_tests |
| EDIT-026 | 컨트롤 삭제 | `edit.delete_control` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P04 | semantic_reopen·selector_tests |
| EDIT-027 | 컨트롤 교체 | `edit.replace_control` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P04 | semantic_reopen·selector_tests |
| EDIT-028 | 다중 편집 transaction | `edit.transaction_multi_edit` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P04 | semantic_reopen·selector_tests |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/02_edit_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
