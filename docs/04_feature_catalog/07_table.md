# 표·셀·계산 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

논리 grid와 병합 master cell을 보존하고, 수식은 FormulaAst로 관리한다. 페이지 분할과 반복 머리행을 실제 렌더로 확인한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (61개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| TABLE-001 | 표 만들기 | `table.create` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-002 | 표 그리기 | `table.draw` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-003 | 표 지우개 | `table.eraser` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-004 | 문자열을 표로 | `table.text_to_table` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-005 | 표를 문자열로 | `table.table_to_text` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-006 | 표 데이터로 차트 만들기 | `table.chart_from_table` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-007 | 표/셀 속성 | `table.properties` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-008 | 각 셀마다 테두리/배경 적용 | `table.cell_border_each` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-009 | 하나의 셀처럼 테두리/배경 적용 | `table.cell_border_unified` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-010 | 표 나누기 | `table.split_table` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-011 | 표 붙이기 | `table.join_table` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-012 | 줄 추가 | `table.insert_rows` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-013 | 칸 추가 | `table.insert_columns` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-014 | 줄 지우기 | `table.delete_rows` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-015 | 칸 지우기 | `table.delete_columns` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-016 | 셀 나누기 | `table.split_cell` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-017 | 셀 합치기 | `table.merge_cells` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-018 | 셀 높이 같게 | `table.equal_row_height` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-019 | 셀 너비 같게 | `table.equal_column_width` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-020 | 표마당/표 스타일 | `table.table_style` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-021 | 표 뒤집기/전치 | `table.transpose` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-022 | 블록 합계 | `table.block_sum` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-023 | 블록 평균 | `table.block_average` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-024 | 블록 곱 | `table.block_product` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-025 | 가로 합계 | `table.horizontal_sum` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-026 | 세로 합계 | `table.vertical_sum` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-027 | 가로 평균 | `table.horizontal_average` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-028 | 세로 평균 | `table.vertical_average` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-029 | 가로 곱 | `table.horizontal_product` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-030 | 세로 곱 | `table.vertical_product` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-031 | 계산식 입력 | `table.formula` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-032 | 1,000단위 구분 쉼표 넣기 | `table.thousands_add` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-033 | 1,000단위 구분 쉼표 빼기 | `table.thousands_remove` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-034 | 표 위치·정렬 | `table.position` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-035 | 표 크기 | `table.width_height` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-036 | 글자처럼 취급/떠 있는 표 | `table.inline_floating` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-037 | 표 주위 글 배치 | `table.wrap` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-038 | 표 바깥 여백 | `table.outer_margin` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-039 | 셀 안 여백 | `table.cell_padding` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-040 | 셀 가로/세로 정렬 | `table.cell_alignment` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-041 | 셀 글자 방향 | `table.cell_text_direction` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-042 | 제목 줄 자동 반복 | `table.repeat_header` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-043 | 쪽 경계 표 나눔 | `table.allow_page_split` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-044 | 행 쪼개짐 정책 | `table.row_split_policy` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-045 | 셀 보호/편집 가능 | `table.cell_protection` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-046 | 셀 면별 테두리 | `table.cell_border` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-047 | 셀 대각선 | `table.cell_diagonal` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-048 | 셀 배경색·무늬·그림 | `table.cell_fill` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-049 | 셀 숫자 형식 | `table.number_format` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-050 | 행 최소 높이 | `table.row_min_height` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-051 | 열 고정 너비 | `table.column_fixed_width` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-052 | 내용에 맞춤 | `table.autofit_content` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-053 | 쪽 너비에 맞춤 | `table.autofit_page` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-054 | 중첩 표 | `table.nested_table` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-055 | 표 캡션 | `table.caption` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-056 | 표 데이터 정렬 | `table.sort_cells` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-057 | 표 자동 채우기 | `table.auto_fill` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-058 | 자동 채우기 내용 정의 | `table.auto_fill_series` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-059 | 상대 셀 참조 | `table.formula_relative_ref` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-060 | 절대 셀 참조 | `table.formula_absolute_ref` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |
| TABLE-061 | 계산 결과 캐시 갱신 | `table.formula_cache` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P06 | schema·semantic_reopen·formula_readback·page_split·render_diff |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/07_table_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
