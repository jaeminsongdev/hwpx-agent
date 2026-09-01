# 쪽·구역·다단·머리말 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

문서 크기, 여백, 방향, 제본, 구역, 다단, 머리말·꼬리말, 쪽 번호를 구역 단위로 모델링한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (50개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| PAGE-001 | 용지 종류 preset | `page.paper_preset` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-002 | 사용자 정의 용지 크기 | `page.paper_custom` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-003 | 용지 세로/가로 방향 | `page.orientation` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-004 | 상하좌우 여백 | `page.margin_all` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-005 | 머리말/꼬리말 거리 | `page.margin_header_footer` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-006 | 제본 여백 | `page.gutter` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-007 | 한쪽 제본 | `page.binding_single` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-008 | 맞쪽 제본 | `page.binding_facing` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-009 | 위로 넘기기 제본 | `page.binding_top` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-010 | 가로/세로 글자 방향 | `page.text_direction` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-011 | 쪽 테두리 | `page.page_border` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-012 | 쪽 배경색 | `page.page_background_color` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-013 | 쪽 배경 그림 | `page.page_background_image` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-014 | 바탕쪽 | `page.master_page` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-015 | 홀짝/첫 쪽 바탕쪽 | `page.master_page_variant` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-016 | 머리말 넣기 | `page.header_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-017 | 꼬리말 넣기 | `page.footer_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-018 | 홀수/짝수/첫 쪽 머리말·꼬리말 | `page.header_footer_variants` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-019 | 쪽 번호 매기기 | `page.page_number_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-020 | 쪽 번호 모양·위치 | `page.page_number_format` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-021 | 쪽 번호 새로 시작 | `page.page_number_restart` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-022 | 그림/표/수식 번호 새로 시작 | `page.object_number_restart` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-023 | 현재 쪽 요소 감추기 | `page.hide_current_page` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-024 | 줄 번호 표시 | `page.line_number_enable` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-025 | 줄 번호 간격·시작·구역 설정 | `page.line_number_config` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-026 | 쪽 나누기 | `page.page_break` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-027 | 단 나누기 | `page.column_break` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-028 | 균등 다단 설정 | `page.column_config_equal` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-029 | 사용자 너비 다단 | `page.column_config_custom` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-030 | 단 사이 간격 | `page.column_gap` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-031 | 단 구분선 | `page.column_separator` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-032 | 단 진행 방향 | `page.column_direction` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-033 | 마지막 쪽 단 균형 | `page.column_balance` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-034 | 단 설정 나누기 | `page.column_layout_break` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-035 | 구역 설정 | `page.section_config` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-036 | 구역 나누기 | `page.section_break` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-037 | 구역별 용지 | `page.section_paper_override` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-038 | 구역별 번호 체계 | `page.section_numbering` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-039 | 구역별 각주/미주 모양 | `page.section_note_style` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-040 | 구역별 바탕쪽 | `page.section_master` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-041 | 원고지 설정 | `page.manuscript_paper` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-042 | 라벨 문서 만들기 | `page.label_document` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-043 | 라벨 새 쪽 추가 | `page.label_new_page` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-044 | 쪽 지우기 | `page.delete_page` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-045 | 문서 격자/원고지 그리드 | `page.page_grid` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-046 | 기본 탭 간격 | `page.default_tab` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-047 | 빈 줄 끌어올림 | `page.empty_line_pullup` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-048 | 첫 쪽 다르게 | `page.first_page_special` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-049 | 새 구역 홀수/짝수 쪽 시작 | `page.page_start_side` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |
| PAGE-050 | 구역 내 단 구간 | `page.section_columns_span` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·page_metrics·hancom_open·render_diff |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/06_page_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
