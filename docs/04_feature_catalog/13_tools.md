# 도구·언어·외부 서비스 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

맞춤법·사전·번역·자산 등은 provider, consent, license, provenance가 있는 외부 기능으로 취급한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (23개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| TOOLS-001 | 맞춤법 검사 | `tools.spellcheck` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-002 | 문법/문장 교정 | `tools.grammarcheck` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-003 | 한컴 사전 | `tools.dictionary_hancom` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-004 | 한자 사전 | `tools.dictionary_hanja` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-005 | 유의어/반의어 사전 | `tools.dictionary_thesaurus` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-006 | 번역 | `tools.translation` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-007 | 빠른 교정 내용 관리 | `tools.quick_correct_content` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-008 | 빠른 교정 동작 | `tools.quick_correct_behavior` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-009 | 입력어 자동 실행 | `tools.input_auto_execute` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-010 | 빠른 교정 효과음 | `tools.quick_correct_sound` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-011 | 한컴 애셋 | `tools.hancom_assets` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-012 | 문서 찾기 | `tools.document_search` | `external_service` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_or_ui_probe·manual_e2e |
| TOOLS-013 | 프레젠테이션 실행 | `tools.presentation_run` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-014 | 프레젠테이션 설정 | `tools.presentation_settings` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-015 | 프레젠테이션 범위 | `tools.presentation_range` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-016 | 글자판 바꾸기 | `tools.keyboard_change` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-017 | 글자판 보기 | `tools.keyboard_view` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-018 | 언어 선택 사항 | `tools.language_options` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-019 | 글자판 자동 변경 | `tools.keyboard_auto_change` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-020 | COM 추가 기능 설정 | `tools.com_addins` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-021 | 사용자 설정 | `tools.customize_ui` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-022 | 환경 설정 | `tools.preferences` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |
| TOOLS-023 | 스킨 설정 | `tools.skin` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | workstation_state_probe |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/13_tools_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
