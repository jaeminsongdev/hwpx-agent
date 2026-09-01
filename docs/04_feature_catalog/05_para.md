# 문단·탭·목록·스타일 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

문단 정렬·간격·들여쓰기·탭·목록·스타일을 참조 그래프로 관리하고 번호 매기기 연속성을 검증한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (45개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| PARA-001 | 왼쪽 정렬 | `para.align_left` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-002 | 오른쪽 정렬 | `para.align_right` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-003 | 가운데 정렬 | `para.align_center` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-004 | 양쪽 정렬 | `para.align_justify` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-005 | 배분 정렬 | `para.align_distribute` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-006 | 문단 왼쪽 여백 | `para.margin_left` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-007 | 문단 오른쪽 여백 | `para.margin_right` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-008 | 첫 줄 들여쓰기 | `para.first_line_indent` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-009 | 내어쓰기 | `para.hanging_indent` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-010 | 줄 간격 비율 | `para.line_spacing_percent` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-011 | 고정 줄 간격 | `para.line_spacing_fixed` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-012 | 최소 줄 간격 | `para.line_spacing_minimum` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-013 | 글자 기준 줄 간격 | `para.line_spacing_font_based` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-014 | 문단 위 간격 | `para.space_before` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-015 | 문단 아래 간격 | `para.space_after` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-016 | 문단 테두리 | `para.paragraph_border` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-017 | 문단 배경 | `para.paragraph_background` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-018 | 탭 위치 | `para.tab_stop` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-019 | 탭 채움선 | `para.tab_leader` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-020 | 다음 문단과 함께 | `para.keep_with_next` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-021 | 문단 줄 함께 유지 | `para.keep_lines` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-022 | 외톨이줄 방지 | `para.widow_orphan` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-023 | 문단 앞 쪽 나누기 | `para.page_break_before` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-024 | 문서 격자에 맞춤 | `para.snap_grid` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-025 | 낱말/줄 나눔 규칙 | `para.word_break` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-026 | 문단 첫 글자 장식 | `para.drop_cap` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-027 | 문단 띠 | `para.paragraph_band` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-028 | 글머리표 적용/해제 | `para.bullet_apply` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-029 | 글머리표 모양 정의 | `para.bullet_definition` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-030 | 문단 번호 적용/해제 | `para.numbering_apply` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-031 | 문단 번호 모양 정의 | `para.numbering_definition` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-032 | 문단 번호 새로 시작 | `para.number_restart` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-033 | 개요 적용/해제 | `para.outline_apply` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-034 | 개요 번호 모양 | `para.outline_definition` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-035 | 한 수준 증가 | `para.outline_level_up` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-036 | 한 수준 감소 | `para.outline_level_down` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-037 | 스타일 적용 | `para.named_style_apply` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-038 | 스타일 추가 | `para.named_style_create` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-039 | 스타일 편집 | `para.named_style_edit` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-040 | 스타일 삭제 | `para.named_style_delete` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-041 | 스타일 순서 변경 | `para.named_style_reorder` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-042 | 스타일 가져오기 | `para.style_import` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-043 | 스타일 내보내기 | `para.style_export` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-044 | 스타일마당 적용 | `para.style_gallery` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |
| PARA-045 | 다음 문단 스타일 지정 | `para.next_style` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·render_diff·style_count |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/05_para_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
