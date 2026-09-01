# 파일·문서 수명주기 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

파일 생성·열기·저장·변환·인쇄·외부 전송을 artifact mutation, workstation UI, external service로 분리한다. 원본은 불변이며 모든 결과는 새 artifact다.

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
| FILE-001 | 빈 새 문서 만들기 | `file.new_document` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-002 | 새 탭 만들기 | `file.new_tab` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P10 | session_state_probe |
| FILE-003 | 문서마당/템플릿으로 새 문서 | `file.new_from_template` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-004 | 문서 시작 도우미 | `file.new_wizard` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P10 | session_state_probe |
| FILE-005 | HWPX 불러오기 | `file.open_hwpx` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-006 | HWP 바이너리 불러오기 | `file.open_hwp` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·save_reopen·export_open |
| FILE-007 | RTF·DOCX·TXT 등 지원 형식 불러오기 | `file.open_other` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·save_reopen·export_open |
| FILE-008 | 파일 형식 자동 판별 | `file.detect_format` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-009 | 현재 형식 저장 | `file.save` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-010 | 다른 이름/형식으로 저장 | `file.save_as` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·save_reopen·export_open |
| FILE-011 | 자동 저장·복구본 처리 | `file.autosave_recovery` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | recovery_fixture·session_state_probe |
| FILE-012 | 문서 닫기 | `file.close_document` | `editor_workflow` | `AUTOMATION_FULL` | `desktop_automation` | P10 | session_state_probe |
| FILE-013 | 문서 정보 읽기·수정 | `file.document_info` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-014 | 사용자 정의 문서 속성 | `file.document_properties` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-015 | 문서 끼워 넣기 | `file.insert_document` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-016 | 여러 문서 병합 | `file.merge_documents` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-017 | 문서 분할 | `file.split_document` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-018 | 손상 HWPX 패키지 진단·복구 | `file.package_repair` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-019 | XML 서식 만들기 | `file.xml_form_create` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-020 | XML 서식마당 | `file.xml_form_gallery` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-021 | XML 문서 불러오기 | `file.xml_import` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-022 | XML 문서 저장하기 | `file.xml_export` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-023 | PDF를 오피스 문서로 변환 | `file.pdf_import` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-024 | 그림을 오피스 문서로 변환 | `file.image_ocr_import` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-025 | PDF로 저장 | `file.pdf_export` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·save_reopen·export_open |
| FILE-026 | 모바일 최적화 문서로 저장 | `file.mobile_export` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·save_reopen·export_open |
| FILE-027 | 한컴독스 저장·연동 | `file.hancom_docs` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-028 | DAISY로 저장 | `file.daisy_export` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-029 | DAISY 스타일 가져오기 | `file.daisy_style_import` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-030 | 문서 전체 점자로 변환 | `file.braille_document` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-031 | 선택 글자 점자로 변환 | `file.braille_selection` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-032 | 점자 변환 설정 | `file.braille_settings` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-033 | CCL 표시 넣기 | `file.ccl_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-034 | 공공누리 표시 넣기 | `file.kogl_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P04 | schema·semantic_reopen·hancom_open·render_diff |
| FILE-035 | 편지 보내기(본문) | `file.send_mail_body` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-036 | 편지 보내기(첨부) | `file.send_mail_attachment` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-037 | 웹 브라우저로 보내기 | `file.send_browser` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-038 | 웹 서버로 올리기 | `file.upload_web_server` | `external_service` | `OPTIONAL_EXTERNAL` | `external_connector` | P11 | provider_contract·manual_e2e |
| FILE-039 | 미리 보기 | `file.preview` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·save_reopen·export_open |
| FILE-040 | 인쇄 | `file.print` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·save_reopen·export_open |
| FILE-041 | 일괄 형식 변환 | `file.batch_convert` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·save_reopen·export_open |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/01_file_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
