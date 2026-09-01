# 글자 모양·문자 입력 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

언어별 글꼴 슬롯, 글자 크기·장평·자간·장식·색·언어 정보를 CharacterStyle delta로 표현한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (41개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| CHAR-001 | 언어별 글꼴 지정 | `char.font_slots` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-002 | 글꼴 지정 | `char.font_family` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-003 | 글꼴 대체 목록 | `char.font_fallback` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-004 | 글자 크기 | `char.font_size` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-005 | 장평 | `char.character_scale` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-006 | 자간 | `char.character_spacing` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-007 | 진하게 | `char.bold` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-008 | 기울임 | `char.italic` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-009 | 밑줄 | `char.underline` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-010 | 밑줄 모양·색 | `char.underline_style` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-011 | 취소선 | `char.strike` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-012 | 이중 취소선 | `char.double_strike` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-013 | 외곽선 | `char.outline` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-014 | 그림자 | `char.shadow` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-015 | 양각 | `char.emboss` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-016 | 음각 | `char.engrave` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-017 | 위 첨자 | `char.superscript` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-018 | 아래 첨자 | `char.subscript` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-019 | 글자 색 | `char.text_color` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-020 | 형광펜/강조색 | `char.highlight` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-021 | 글자 테두리 | `char.char_border` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-022 | 글자 배경 | `char.char_background` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-023 | 기준선 위치 | `char.baseline_offset` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-024 | 커닝 | `char.kerning` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-025 | 숨은 글자 | `char.hidden_text` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-026 | 선택 글자 보호 | `char.protected_text` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-027 | 글자 스타일 적용 | `char.char_style_apply` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-028 | 글자 스타일 해제 | `char.char_style_clear` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-029 | 글자 겹치기 | `char.character_overlap` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-030 | 덧말 넣기 | `char.additional_text` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-031 | 문자표 문자 입력 | `char.special_character` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-032 | 한자 입력 | `char.hanja_input` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-033 | 한자 단어 등록 | `char.hanja_register` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-034 | 한자 부수/총획 입력 | `char.hanja_radical` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-035 | 한자 새김 입력 | `char.hanja_meaning` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-036 | 날짜/시간 문자열 | `char.date_time_literal` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-037 | 묶음 빈칸 | `char.nonbreaking_space` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-038 | 조건부 하이픈 | `char.soft_hyphen` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-039 | 문자 언어 지정 | `char.language_tag` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-040 | 양방향 문자 방향 | `char.bidi_direction` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |
| CHAR-041 | 맞춤법 검사 제외 | `char.spellcheck_exclude` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P05 | schema·semantic_reopen·font_probe·render_diff |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/04_char_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
