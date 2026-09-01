# 찾기·치환·텍스트 변환 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

텍스트·스타일·컨트롤 인덱스를 사용해 run 경계를 넘는 검색을 지원하고, 치환 전에는 반드시 diff와 상한을 계산한다.

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
| SEARCH-001 | 일반 문자열 찾기 | `search.find_literal` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-002 | 정규식 찾기 | `search.find_regex` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-003 | 글자/문단 모양 조건 찾기 | `search.find_style` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-004 | 개체/필드/조판 부호 찾기 | `search.find_control` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-005 | 다시 찾기 | `search.find_next` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-006 | 문자열 찾아 바꾸기 | `search.replace_literal` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-007 | 정규식 찾아 바꾸기 | `search.replace_regex` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-008 | 서식 찾아 바꾸기 | `search.replace_style` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-009 | 특정 컨트롤 치환 | `search.replace_control` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-010 | 쪽/구역/문단/개체 찾아가기 | `search.find_by_page` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-011 | 한글을 한자로 바꾸기 | `search.convert_hanja` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | language_oracle·manual_review |
| SEARCH-012 | 한자를 한글로 바꾸기 | `search.convert_hangul` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | language_oracle·manual_review |
| SEARCH-013 | 대문자/소문자 바꾸기 | `search.case_convert` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-014 | 전각/반각 바꾸기 | `search.full_half_width` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-015 | 일어 바꾸기 | `search.japanese_convert` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | language_oracle·manual_review |
| SEARCH-016 | 간체/번체 바꾸기 | `search.simplified_traditional` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | language_oracle·manual_review |
| SEARCH-017 | 로마자로 바꾸기 | `search.romanize` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | language_oracle·manual_review |
| SEARCH-018 | 외래어 표기 변환 | `search.foreign_word_notation` | `editor_workflow` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | language_oracle·manual_review |
| SEARCH-019 | 개인정보 바로 바꾸기 | `search.personal_info_replace_direct` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-020 | 개인정보 찾아서 바꾸기 | `search.personal_info_find_replace` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-021 | 텍스트/문단 정렬 | `search.sort_text` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-022 | Unicode 정규화 | `search.normalize_unicode` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-023 | 공백·탭·줄바꿈 정규화 | `search.normalize_whitespace` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-024 | 폰트 일괄 대체 | `search.replace_fonts` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |
| SEARCH-025 | 스타일 일괄 대체 | `search.replace_styles` | `editor_workflow` | `DIRECT_FULL` | `direct_hwpx` | P09 | match_set·semantic_diff·reopen |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/03_search_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
