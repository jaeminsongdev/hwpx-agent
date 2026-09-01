# 인쇄·내보내기·접근성 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

인쇄·내보내기는 별도 job이다. 원본을 바꾸지 않고 loss report와 reopen/spool evidence를 생성한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (34개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| EXPORT-001 | 인쇄 미리 보기 | `export.print_preview` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-002 | 인쇄 범위 | `export.print_range` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-003 | 부수·한 부씩 인쇄 | `export.print_copies` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-004 | 양면 인쇄 | `export.print_duplex` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-005 | 모아 찍기/N-up | `export.print_nup` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-006 | 용지에 맞춤·확대축소 | `export.print_scaling` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-007 | 프린터 용지 공급 | `export.print_paper_source` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-008 | 인쇄 워터마크 | `export.print_watermark` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-009 | 메모/변경 내용 인쇄 | `export.print_comments` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-010 | 개체 인쇄 여부 | `export.print_object_visibility` | `external_service` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-011 | PDF 내보내기 | `export.export_pdf` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-012 | PDF 품질·글꼴·책갈피 옵션 | `export.export_pdf_options` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-013 | 태그된 PDF 내보내기 | `export.export_pdf_tagged` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-014 | 쪽별 이미지 내보내기 | `export.export_page_images` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-015 | 선택 영역 이미지 | `export.export_selection_image` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-016 | 텍스트 내보내기 | `export.export_text` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-017 | HTML 내보내기 | `export.export_html` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-018 | XML 내보내기 | `export.export_xml` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-019 | RTF 내보내기 | `export.export_rtf` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-020 | DOCX 내보내기 | `export.export_docx` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-021 | HWP 내보내기 | `export.export_hwp` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-022 | HWPX 내보내기 | `export.export_hwpx` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-023 | 문서 제목 지정 | `export.access_document_title` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-024 | 문서 기본 언어 | `export.access_language` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-025 | 그림/개체 대체 텍스트 | `export.access_alt_text` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-026 | 표 머리글 지정 | `export.access_table_headers` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-027 | 읽기 순서 | `export.access_reading_order` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-028 | 제목/개요 구조 | `export.access_heading_structure` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-029 | 의미 있는 링크 텍스트 | `export.access_link_text` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-030 | 색 대비 검사 | `export.access_contrast_check` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-031 | 문서 접근성 검사 | `export.access_document_checker` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |
| EXPORT-032 | DAISY 내보내기 | `export.daisy_export` | `artifact_semantics` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P12 | provider_contract·manual_accessibility_review |
| EXPORT-033 | 점자 문서 변환 | `export.braille_export` | `artifact_semantics` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P12 | provider_contract·manual_accessibility_review |
| EXPORT-034 | 내보낸 파일 재열기·검증 | `export.export_validation` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P12 | export_open·page_metrics·visual_diff·accessibility_scan |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/16_export_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
