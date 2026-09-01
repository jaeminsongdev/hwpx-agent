# 필드·양식·주석·참조 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

필드·양식·각주·메모·책갈피·상호참조·차례·메일머지의 target graph와 갱신 정책을 관리한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (53개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| REF-001 | 필드 입력 | `ref.field_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-002 | 사용자 정의 필드 | `ref.field_user` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-003 | 누름틀/클릭 안내 필드 | `ref.field_click_here` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-004 | 날짜/시간 코드 | `ref.field_date_time` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-005 | 파일 이름 필드 | `ref.field_filename` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-006 | 쪽 번호 필드 | `ref.field_page_number` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-007 | 구역 번호 필드 | `ref.field_section_number` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-008 | 개체 번호 필드 | `ref.field_object_number` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-009 | 필드 결과 새로 고침 | `ref.field_update` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-010 | 필드 결과 잠금 | `ref.field_lock` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-011 | 텍스트 양식 개체 | `ref.form_text` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-012 | 체크 상자 | `ref.form_checkbox` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-013 | 라디오 단추 | `ref.form_radio` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-014 | 콤보 상자 | `ref.form_combo` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-015 | 목록 상자 | `ref.form_list` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-016 | 명령 단추 | `ref.form_button` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | property_readback·save_reopen·render_diff |
| REF-017 | 날짜 양식 | `ref.form_date` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-018 | 양식 개체 속성 | `ref.form_properties` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-019 | 양식 탭 순서 | `ref.form_tab_order` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-020 | 양식 데이터 연결 | `ref.form_data_binding` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | property_readback·save_reopen·render_diff |
| REF-021 | 각주 넣기 | `ref.footnote_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-022 | 미주 넣기 | `ref.endnote_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-023 | 각주/미주 모양 | `ref.note_style` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-024 | 각주↔미주 변환 | `ref.note_convert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-025 | 주석 저장하기 | `ref.note_export` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-026 | 숨은 설명 | `ref.hidden_explanation` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-027 | 메모 넣기 | `ref.comment_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-028 | 메모 모양 | `ref.comment_style` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-029 | 메모 보이기/숨기기 | `ref.comment_show_hide` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-030 | 메모 해결 처리 | `ref.comment_resolve` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-031 | 책갈피 넣기 | `ref.bookmark_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-032 | 책갈피 지우기 | `ref.bookmark_delete` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-033 | 하이퍼링크 넣기 | `ref.hyperlink_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-034 | 하이퍼링크 편집 | `ref.hyperlink_edit` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-035 | 상호 참조 넣기 | `ref.crossref_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-036 | 상호 참조 새로 고침 | `ref.crossref_update` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | property_readback·save_reopen·render_diff |
| REF-037 | 제목 차례 표시 | `ref.toc_mark` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-038 | 차례 표시 숨기기 | `ref.toc_hide_mark` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-039 | 차례 만들기 | `ref.toc_create` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-040 | 차례 새로 고침 | `ref.toc_update` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | property_readback·save_reopen·render_diff |
| REF-041 | 색인 표시 | `ref.index_mark` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-042 | 색인 만들기 | `ref.index_create` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-043 | 참고 문헌 관리 | `ref.bibliography_manage` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | property_readback·save_reopen·render_diff |
| REF-044 | 인용 삽입 | `ref.citation_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-045 | 참고 문헌 목록 생성 | `ref.bibliography_generate` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | property_readback·save_reopen·render_diff |
| REF-046 | 메일 머지 필드 넣기 | `ref.mailmerge_field` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-047 | 메일 머지 만들기 | `ref.mailmerge_generate` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | property_readback·save_reopen·render_diff |
| REF-048 | 캡션 번호 체계 | `ref.caption_sequence` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-049 | 날짜/시간 형식 | `ref.date_time_format` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-050 | 파일 이름 문자열 넣기 | `ref.file_name_literal` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-051 | 교정 부호 넣기 | `ref.correction_mark` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-052 | 자료 연결 | `ref.data_link` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |
| REF-053 | 깨진 참조 검사 | `ref.reference_validate` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P09 | semantic_reopen·field_readback·reference_update·hancom_open·render_diff |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/10_ref_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
