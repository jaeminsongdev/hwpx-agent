# 보기·작업환경 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

보기·작업 창·도구 상자는 session-scoped workstation state이며 HWPX artifact 기능과 분리한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (47개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| VIEW-001 | 화면 확대/축소 | `view.zoom` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-002 | 쪽 윤곽 보기 | `view.page_outline` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-003 | 조판 부호 표시 | `view.show_layout_marks` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-004 | 문단 부호 표시 | `view.show_paragraph_marks` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-005 | 교정 부호 표시 | `view.show_correction_marks` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-006 | 투명 선 표시 | `view.show_transparent_lines` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-007 | 그림 표시/숨기기 | `view.show_images` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-008 | 메모 보이기/숨기기 | `view.show_comments` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-009 | 메모 안내선 | `view.comment_guides` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-010 | 메모 내용 보기 | `view.comment_content_pane` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-011 | 한자 발음 표시 | `view.hanja_pronunciation` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-012 | 한자 발음 설정 | `view.hanja_pronunciation_settings` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-013 | 격자 보기 | `view.grid_view` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-014 | 격자 설정 | `view.grid_settings` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-015 | 그리기 안내선 | `view.drawing_guides` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-016 | 개체 이동 안내선 | `view.move_guides` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-017 | 개체 이동 안내선 설정 | `view.move_guide_settings` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-018 | 문서 보기 색 | `view.document_view_color` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-019 | 기본 도구 상자 | `view.toolbar_default` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-020 | 서식 도구 상자 | `view.toolbar_format` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-021 | 사용자 도구 상자 | `view.toolbar_customize` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-022 | 쪽 모양 작업 창 | `view.pane_page_shape` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-023 | 빠른 실행 작업 창 | `view.pane_quick_run` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-024 | 스타일 작업 창 | `view.pane_styles` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-025 | 책갈피 작업 창 | `view.pane_bookmarks` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-026 | 개요 보기 작업 창 | `view.pane_outline` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-027 | 스크립트 작업 창 | `view.pane_script` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-028 | 번역 작업 창 | `view.pane_translation` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-029 | 양식 개체 속성 작업 창 | `view.pane_form_properties` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-030 | 클립보드 작업 창 | `view.pane_clipboard` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-031 | 사전 검색 작업 창 | `view.pane_dictionary` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-032 | 태그 이름 작업 창 | `view.pane_tag_names` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-033 | 문서 탭 | `view.document_tabs` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-034 | 상황 선 | `view.status_bar` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-035 | 가로 이동 막대 | `view.horizontal_scroll` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-036 | 세로 이동 막대 | `view.vertical_scroll` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-037 | 가로 눈금자 | `view.horizontal_ruler` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-038 | 세로 눈금자 | `view.vertical_ruler` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-039 | 편집 화면 나누지 않음 | `view.split_none` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-040 | 가로로 나누기 | `view.split_horizontal` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-041 | 세로로 나누기 | `view.split_vertical` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-042 | 가로 세로 나누기 | `view.split_both` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-043 | 창 가로 배열 | `view.arrange_horizontal` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-044 | 창 세로 배열 | `view.arrange_vertical` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-045 | 창 겹치게 배열 | `view.arrange_cascade` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-046 | 모두 아이콘으로 | `view.minimize_all` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| VIEW-047 | 열린 창 목록 | `view.window_list` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/15_view_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
