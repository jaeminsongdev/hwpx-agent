# 문서 인덱스

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`

이 인덱스는 ZIP 루트 기준 **278개 최종 파일**을 탐색하기 위한 안내서다. `DOCUMENT_INDEX.md`와 자체 해시 파일 `MANIFEST.sha256`은 목록에서 제외했다. generated 대용량 파일은 처음부터 순서대로 읽기보다 `feature_id`, `capability_id`, `task_id`로 검색한다.

## 권장 읽기 순서

1. `README.md`
2. `00_START_HERE.md`
3. `EXECUTIVE_REVIEW_AND_DELTA.md`
4. `IMPLEMENTATION_PLAYBOOK.md`
5. `FEATURE_COVERAGE_MATRIX.md`
6. `docs/09_roadmap/00_master_roadmap.md`
7. `DESIGN_VALIDATION_REPORT.md`

## 00. 루트 진입점·현황·전체 산출물

- `00_START_HERE.md` — START HERE — 새 ChatGPT/Codex/개발 세션 진입점 (2,271 bytes)
- `CURRENT_STATE.md` — CURRENT STATE (1,964 bytes)
- `DESIGN_VALIDATION_REPORT.md` — 설계 검증 보고서 (3,501 bytes)
- `EXECUTIVE_REVIEW_AND_DELTA.md` — v1 검토 결과와 v2 수정 요약 (3,691 bytes)
- `FEATURE_COVERAGE_MATRIX.csv` — 609개 기능 coverage 원본 CSV (190,495 bytes)
- `FEATURE_COVERAGE_MATRIX.md` — 한/글 기능 전수 매트릭스 요약 (1,987 bytes)
- `IMPLEMENTATION_PLAYBOOK.md` — HWPX Agent 통합 구현 플레이북 (8,173 bytes)
- `README.md` — HWPX Agent Product Design v2 — ChatGPT Web·Codex 공용 한컴 문서 제작 플러그인 (4,409 bytes)
- `ROADMAP_STATUS.yaml` — ROADMAP_STATUS.yaml (1,270 bytes)
- `WORK_BREAKDOWN_STRUCTURE.csv` — P00~P20 실행 작업 원본 CSV (36,621 bytes)

## 01. 검토 결과

- `docs/00_review/01_executive_review.md` — 상세 설계 검토 (2,826 bytes)
- `docs/00_review/02_gap_analysis_v1_to_v2.md` — v1 → v2 갭 분석과 문서 매핑 (2,412 bytes)
- `docs/00_review/03_architecture_decision_summary.md` — 아키텍처 결정 요약 (1,526 bytes)

## 02. 제품·요구사항

- `docs/01_product/01_product_definition.md` — 제품 정의 (2,000 bytes)
- `docs/01_product/02_scope_and_support_levels.md` — 범위와 지원 수준 (2,594 bytes)
- `docs/01_product/03_requirements_traceability.md` — 요구사항 추적성 (1,715 bytes)
- `docs/01_product/04_acceptance_criteria.md` — 제품 완료 기준 (1,819 bytes)
- `docs/01_product/05_user_cases.md` — 사용자 사례 전수 목록 (1,830 bytes)

## 03. 시스템 아키텍처

- `docs/02_architecture/01_system_architecture.md` — 전체 시스템 아키텍처 (3,086 bytes)
- `docs/02_architecture/02_capability_routing.md` — Capability Registry와 백엔드 라우팅 (2,846 bytes)
- `docs/02_architecture/03_backend_interfaces.md` — Backend 인터페이스 (1,767 bytes)
- `docs/02_architecture/04_deployment_topology.md` — 배포 토폴로지 (1,654 bytes)
- `docs/02_architecture/05_state_revision_transactions.md` — 상태·revision·transaction (1,404 bytes)
- `docs/02_architecture/06_security_threat_model.md` — 보안 위협 모델 (2,025 bytes)
- `docs/02_architecture/07_repository_structure.md` — 권장 저장소 구조 (1,333 bytes)
- `docs/02_architecture/08_observability.md` — 관측성 설계 (956 bytes)
- `docs/02_architecture/09_license_and_compliance.md` — 라이선스·법적·배포 준수 (1,321 bytes)

## 04. DocumentGraph·OperationPlan·문서 모델

- `docs/03_document_model/01_document_graph_ir.md` — DocumentGraph IR v2 (3,132 bytes)
- `docs/03_document_model/02_units_ids_coordinates.md` — 단위·좌표·식별자 규약 (1,876 bytes)
- `docs/03_document_model/03_style_model.md` — 스타일 모델 (2,088 bytes)
- `docs/03_document_model/04_page_section_layout.md` — 쪽·구역·레이아웃 모델 (2,112 bytes)
- `docs/03_document_model/05_text_paragraph_numbering.md` — 텍스트·문단·번호 모델 (1,937 bytes)
- `docs/03_document_model/06_table_model.md` — 표 모델과 구현 규격 (2,439 bytes)
- `docs/03_document_model/07_equation_model.md` — Native Equation 모델 (2,234 bytes)
- `docs/03_document_model/08_drawing_image_chart.md` — 그림·도형·글상자·차트·OLE 모델 (2,013 bytes)
- `docs/03_document_model/09_fields_controls_references.md` — 필드·양식 개체·주석·참조 모델 (1,972 bytes)
- `docs/03_document_model/10_review_protection_accessibility.md` — 검토·보호·접근성 모델 (1,774 bytes)
- `docs/03_document_model/11_operation_plan.md` — OperationPlan v2 (2,343 bytes)
- `docs/03_document_model/12_preservation_roundtrip.md` — 보존 편집과 round-trip 알고리즘 (2,178 bytes)

## 05. 한/글 기능 전수 카탈로그

- `docs/04_feature_catalog/01_file.md` — 파일·문서 수명주기 기능 설계 (8,380 bytes)
- `docs/04_feature_catalog/02_edit.md` — 편집·선택·클립보드 기능 설계 (6,074 bytes)
- `docs/04_feature_catalog/03_search.md` — 찾기·치환·텍스트 변환 기능 설계 (5,557 bytes)
- `docs/04_feature_catalog/04_char.md` — 글자 모양·문자 입력 기능 설계 (7,934 bytes)
- `docs/04_feature_catalog/05_para.md` — 문단·탭·목록·스타일 기능 설계 (8,946 bytes)
- `docs/04_feature_catalog/06_page.md` — 쪽·구역·다단·머리말 기능 설계 (10,592 bytes)
- `docs/04_feature_catalog/07_table.md` — 표·셀·계산 기능 설계 (12,632 bytes)
- `docs/04_feature_catalog/08_eq.md` — 수식 기능 설계 (7,915 bytes)
- `docs/04_feature_catalog/09_obj.md` — 그림·도형·개체·차트 기능 설계 (11,932 bytes)
- `docs/04_feature_catalog/10_ref.md` — 필드·양식·주석·참조 기능 설계 (11,394 bytes)
- `docs/04_feature_catalog/11_review.md` — 검토·비교·이력 기능 설계 (4,933 bytes)
- `docs/04_feature_catalog/12_sec.md` — 보안·보호·개인정보 기능 설계 (5,672 bytes)
- `docs/04_feature_catalog/13_tools.md` — 도구·언어·외부 서비스 기능 설계 (5,104 bytes)
- `docs/04_feature_catalog/14_auto.md` — 스크립트·자동화·이벤트 기능 설계 (5,989 bytes)
- `docs/04_feature_catalog/15_view.md` — 보기·작업환경 기능 설계 (8,642 bytes)
- `docs/04_feature_catalog/16_export.md` — 인쇄·내보내기·접근성 기능 설계 (7,982 bytes)
- `docs/04_feature_catalog/17_contract_usage.md` — 기능별 구현 계약 사용법 (1,597 bytes)

## 06. 609개 기능별 상세 구현 계약

- `docs/04_feature_catalog/contracts/01_file_contracts.md` — 파일·문서 수명주기 — 기능별 구현 계약 (102,376 bytes)
- `docs/04_feature_catalog/contracts/02_edit_contracts.md` — 편집·선택·클립보드 — 기능별 구현 계약 (63,432 bytes)
- `docs/04_feature_catalog/contracts/03_search_contracts.md` — 찾기·치환·텍스트 변환 — 기능별 구현 계약 (65,383 bytes)
- `docs/04_feature_catalog/contracts/04_char_contracts.md` — 글자 모양·문자 입력 — 기능별 구현 계약 (99,697 bytes)
- `docs/04_feature_catalog/contracts/05_para_contracts.md` — 문단·탭·목록·스타일 — 기능별 구현 계약 (109,194 bytes)
- `docs/04_feature_catalog/contracts/06_page_contracts.md` — 쪽·구역·다단·머리말 — 기능별 구현 계약 (137,146 bytes)
- `docs/04_feature_catalog/contracts/07_table_contracts.md` — 표·셀·계산 — 기능별 구현 계약 (157,690 bytes)
- `docs/04_feature_catalog/contracts/08_eq_contracts.md` — 수식 — 기능별 구현 계약 (100,256 bytes)
- `docs/04_feature_catalog/contracts/09_obj_contracts.md` — 그림·도형·개체·차트 — 기능별 구현 계약 (153,163 bytes)
- `docs/04_feature_catalog/contracts/10_ref_contracts.md` — 필드·양식·주석·참조 — 기능별 구현 계약 (137,665 bytes)
- `docs/04_feature_catalog/contracts/11_review_contracts.md` — 검토·비교·이력 — 기능별 구현 계약 (47,323 bytes)
- `docs/04_feature_catalog/contracts/12_sec_contracts.md` — 보안·보호·개인정보 — 기능별 구현 계약 (62,349 bytes)
- `docs/04_feature_catalog/contracts/13_tools_contracts.md` — 도구·언어·외부 서비스 — 기능별 구현 계약 (52,896 bytes)
- `docs/04_feature_catalog/contracts/14_auto_contracts.md` — 스크립트·자동화·이벤트 — 기능별 구현 계약 (64,587 bytes)
- `docs/04_feature_catalog/contracts/15_view_contracts.md` — 보기·작업환경 — 기능별 구현 계약 (102,435 bytes)
- `docs/04_feature_catalog/contracts/16_export_contracts.md` — 인쇄·내보내기·접근성 — 기능별 구현 계약 (92,865 bytes)

## 07. 백엔드·라우팅

- `docs/05_backends/01_direct_hwpx_backend.md` — DirectHWPXBackend (1,688 bytes)
- `docs/05_backends/02_desktop_automation_backend.md` — HancomDesktopAutomationBackend (2,300 bytes)
- `docs/05_backends/03_webhwp_backend.md` — WebHWPBackend (1,310 bytes)
- `docs/05_backends/04_oracle_render_export.md` — HancomOracleBackend·렌더·내보내기 (1,393 bytes)
- `docs/05_backends/05_capability_registry_generation.md` — Capability Registry 생성과 유지 (1,399 bytes)
- `docs/05_backends/06_fallback_degradation.md` — Fallback·degradation·오류 정책 (1,587 bytes)

## 08. MCP·내부 API

- `docs/06_mcp_api/01_tool_surface.md` — MCP 도구 표면 (3,856 bytes)
- `docs/06_mcp_api/02_tool_contracts.md` — MCP 도구 계약 상세 (5,673 bytes)
- `docs/06_mcp_api/03_operation_examples.md` — 대표 OperationPlan 예제 (3,577 bytes)
- `docs/06_mcp_api/04_error_model.md` — 오류·경고·검증 모델 (2,799 bytes)
- `docs/06_mcp_api/05_auth_permissions.md` — 인증·권한·승인 (1,952 bytes)
- `docs/06_mcp_api/06_jobs_artifacts.md` — 비동기 Job·Artifact 계약 (1,988 bytes)
- `docs/06_mcp_api/07_internal_api.md` — Control Plane ↔ Backend 내부 API (1,688 bytes)

## 09. ChatGPT Web·Codex 앱

- `docs/07_apps/01_universal_plugin.md` — ChatGPT·Codex 공용 플러그인 패키지 (2,069 bytes)
- `docs/07_apps/02_chatgpt_web_app.md` — ChatGPT Web 앱 설계 (1,464 bytes)
- `docs/07_apps/03_codex_plugin_local.md` — Codex 플러그인과 로컬 Companion (1,498 bytes)
- `docs/07_apps/04_widget_ui.md` — Preview·Diff·Capability Widget (1,688 bytes)
- `docs/07_apps/05_skills_design.md` — 플러그인 Skills 설계 (1,595 bytes)
- `docs/07_apps/06_cross_surface_continuity.md` — ChatGPT Web ↔ Codex 연속성 (1,262 bytes)
- `docs/07_apps/07_packaging_submission.md` — 패키징·연결·제출 (1,300 bytes)

## 10. 테스트·검증

- `docs/08_testing/01_test_strategy.md` — 전체 테스트 전략 (1,404 bytes)
- `docs/08_testing/02_golden_corpus.md` — Golden 문서 corpus (1,268 bytes)
- `docs/08_testing/03_feature_conformance.md` — 609개 기능 Conformance 체계 (1,255 bytes)
- `docs/08_testing/04_equation_conformance.md` — 수식 적합성 테스트 (1,391 bytes)
- `docs/08_testing/05_layout_table_visual.md` — 레이아웃·표·시각 회귀 테스트 (1,329 bytes)
- `docs/08_testing/06_hancom_version_matrix.md` — 한/글 버전·빌드 적합성 행렬 (1,270 bytes)
- `docs/08_testing/07_security_fuzzing.md` — 보안·퍼징 테스트 (1,511 bytes)
- `docs/08_testing/08_e2e_matrix.md` — End-to-End 시나리오 행렬 (1,614 bytes)
- `docs/08_testing/09_release_gates.md` — Release Gate 정의 (1,132 bytes)

## 11. P00~P20 로드맵

- `docs/09_roadmap/00_master_roadmap.md` — MASTER ROADMAP — 설계에서 1.0과 전 기능 패리티까지 (3,770 bytes)
- `docs/09_roadmap/P00_source_license_target_freeze.md` — P00 — Source·License·Target Freeze (4,233 bytes)
- `docs/09_roadmap/P01_repository_ci_security_foundation.md` — P01 — Repository·CI·Security Foundation (3,884 bytes)
- `docs/09_roadmap/P02_official_catalog_importer_capability_registry.md` — P02 — Official Catalog Importer·Capability Registry (3,799 bytes)
- `docs/09_roadmap/P03_hwpx_package_preserving_xml_core.md` — P03 — HWPX Package·Preserving XML Core (3,824 bytes)
- `docs/09_roadmap/P04_documentgraph_operationplan_transactions.md` — P04 — DocumentGraph·OperationPlan·Transactions (3,745 bytes)
- `docs/09_roadmap/P05_text_character_paragraph_page_section.md` — P05 — Text·Character·Paragraph·Page·Section (3,772 bytes)
- `docs/09_roadmap/P06_table_engine.md` — P06 — Table Engine (3,661 bytes)
- `docs/09_roadmap/P07_native_equation_engine.md` — P07 — Native Equation Engine (3,635 bytes)
- `docs/09_roadmap/P08_images_shapes_drawing_charts.md` — P08 — Images·Shapes·Drawing·Charts (3,611 bytes)
- `docs/09_roadmap/P09_fields_forms_notes_references.md` — P09 — Fields·Forms·Notes·References (3,594 bytes)
- `docs/09_roadmap/P10_windows_hancom_automation_bridge.md` — P10 — Windows Hancom Automation Bridge (3,840 bytes)
- `docs/09_roadmap/P11_advanced_desktop_features.md` — P11 — Advanced Desktop Features (3,619 bytes)
- `docs/09_roadmap/P12_template_surgical_edit_cross-backend_normalization.md` — P12 — Template Surgical Edit·Cross-backend Normalization (3,834 bytes)
- `docs/09_roadmap/P13_validation_hancom_oracle_render.md` — P13 — Validation·Hancom Oracle·Render (3,640 bytes)
- `docs/09_roadmap/P14_projects_revisions_jobs_artifacts.md` — P14 — Projects·Revisions·Jobs·Artifacts (3,687 bytes)
- `docs/09_roadmap/P15_remote_mcp_control_plane.md` — P15 — Remote MCP Control Plane (3,486 bytes)
- `docs/09_roadmap/P16_chatgpt_web_plugin_widget.md` — P16 — ChatGPT Web Plugin·Widget (3,648 bytes)
- `docs/09_roadmap/P17_codex_remote_local_companion.md` — P17 — Codex Remote·Local Companion (3,559 bytes)
- `docs/09_roadmap/P18_quality_security_performance_dr.md` — P18 — Quality·Security·Performance·DR (3,603 bytes)
- `docs/09_roadmap/P19_production_deployment_license_submission.md` — P19 — Production Deployment·License·Submission (3,669 bytes)
- `docs/09_roadmap/P20_post-ga_parity_rust-native_expansion.md` — P20 — Post-GA Parity·Rust-native Expansion (3,622 bytes)

## 12. 운영·배포

- `docs/10_operations/01_local_dev.md` — 로컬 개발 환경 (1,489 bytes)
- `docs/10_operations/02_ci_cd.md` — CI/CD (1,209 bytes)
- `docs/10_operations/03_windows_worker_ops.md` — Windows 한/글 Worker 운영 (1,494 bytes)
- `docs/10_operations/04_deployment.md` — 배포 토폴로지 (1,183 bytes)
- `docs/10_operations/05_observability_incidents.md` — 관측성·장애 대응 (1,317 bytes)
- `docs/10_operations/06_backup_dr.md` — 백업·재해 복구 (1,106 bytes)
- `docs/10_operations/07_release_rollback.md` — 릴리스·롤백 Runbook (971 bytes)
- `docs/10_operations/08_support_runbook.md` — 지원·문제 해결 Runbook (1,176 bytes)

## 13. 공식 자료·용어·결정

- `docs/11_references/01_official_sources.md` — 공식 자료 기준 목록 (1,801 bytes)
- `docs/11_references/02_glossary.md` — 용어집 (1,710 bytes)
- `docs/11_references/03_open_decisions.md` — Open Decisions (1,473 bytes)
- `docs/11_references/04_feature_source_method.md` — 기능 전수 목록 작성 방법 (1,759 bytes)
- `docs/11_references/05_license_checklist.md` — 라이선스·법무 체크리스트 (1,170 bytes)

## 14. 상세 구현 가이드

- `docs/12_implementation_guides/01_repository_bootstrap.md` — 저장소 부트스트랩과 개발 규율 (4,707 bytes)
- `docs/12_implementation_guides/02_catalog_importer_and_binding_generator.md` — 공식 기능 카탈로그 importer와 binding 생성기 (3,875 bytes)
- `docs/12_implementation_guides/03_hwpx_package_and_preserving_editor.md` — HWPX 패키지 파서·작성기·보존 편집기 구현 (3,675 bytes)
- `docs/12_implementation_guides/04_documentgraph_operation_engine.md` — DocumentGraph·OperationPlan·트랜잭션 엔진 구현 (3,816 bytes)
- `docs/12_implementation_guides/05_page_table_layout_algorithms.md` — 문서 크기·쪽·다단·표 레이아웃 알고리즘 (3,619 bytes)
- `docs/12_implementation_guides/06_native_equation_pipeline.md` — Native 한컴 수식 엔진 구현 (3,459 bytes)
- `docs/12_implementation_guides/07_windows_automation_worker.md` — Windows 한/글 오토메이션 워커 구현 (4,052 bytes)
- `docs/12_implementation_guides/08_validation_oracle_visual_diff.md` — 검증·실제 한/글 Oracle·시각 차이 시스템 (3,130 bytes)
- `docs/12_implementation_guides/09_project_jobs_storage.md` — 프로젝트·리비전·작업·아티팩트 서비스 구현 (2,696 bytes)
- `docs/12_implementation_guides/10_mcp_chatgpt_codex_apps.md` — MCP 서비스·ChatGPT Web·Codex 플러그인 구현 (3,313 bytes)
- `docs/12_implementation_guides/11_security_privacy_license.md` — 보안·개인정보·라이선스 구현 (2,641 bytes)
- `docs/12_implementation_guides/12_vertical_slices_and_release.md` — 수직 슬라이스·완료 순서·릴리스 운영 (2,730 bytes)

## 15. 대표 구현 레시피

- `docs/13_reference_recipes/01_custom_page_table_equation.md` — 사용자 정의 문서 크기 + 표 + 수식 (875 bytes)
- `docs/13_reference_recipes/02_two_column_math_exam.md` — A3 2단 수학 시험지 (782 bytes)
- `docs/13_reference_recipes/03_surgical_template_fill.md` — 학교 양식 보존 채우기 (680 bytes)
- `docs/13_reference_recipes/04_advanced_table.md` — 병합·반복 머리행·수식 표 (698 bytes)
- `docs/13_reference_recipes/05_native_equation_edit.md` — 기존 native 수식 편집 (683 bytes)

## 16. ADR

- `decisions/ADR-0001-capability-driven-multi-backend.md` — ADR-0001 — Capability-driven multi-backend (883 bytes)
- `decisions/ADR-0002-hwpx-canonical-artifact.md` — ADR-0002 — HWPX canonical artifact (820 bytes)
- `decisions/ADR-0003-documentgraph-and-operationplan.md` — ADR-0003 — DocumentGraph and OperationPlan (771 bytes)
- `decisions/ADR-0004-three-edit-modes.md` — ADR-0004 — Three edit modes (770 bytes)
- `decisions/ADR-0005-isolated-windows-automation.md` — ADR-0005 — Isolated Windows automation (761 bytes)
- `decisions/ADR-0006-native-hancom-equation-mandatory.md` — ADR-0006 — Native Hancom equation mandatory (801 bytes)
- `decisions/ADR-0007-version-scoped-capability-registry.md` — ADR-0007 — Version-scoped capability registry (771 bytes)
- `decisions/ADR-0008-evidence-based-validation.md` — ADR-0008 — Evidence-based validation (753 bytes)
- `decisions/ADR-0009-remote-project-state-canonical.md` — ADR-0009 — Remote project state canonical (759 bytes)
- `decisions/ADR-0010-semantic-mcp-surface.md` — ADR-0010 — Semantic MCP surface (759 bytes)
- `decisions/ADR-0011-commercial-license-hard-gate.md` — ADR-0011 — Commercial license hard gate (770 bytes)
- `decisions/ADR-0012-mcp-apps-standards-first.md` — ADR-0012 — MCP Apps standards first (780 bytes)
- `decisions/ADR-0013-no-raw-action-execution-from-models.md` — ADR-0013 — No raw action execution from models (767 bytes)
- `decisions/ADR-0014-immutable-artifacts-and-atomic-revisions.md` — ADR-0014 — Immutable artifacts and atomic revisions (782 bytes)
- `decisions/ADR-0015-csharp-dotnet-windows-worker.md` — ADR-0015 — C#/.NET Windows Hancom Worker (900 bytes)
- `decisions/ADR-0016-protobuf-grpc-agent-and-named-pipe-worker.md` — ADR-0016 — Protobuf/gRPC Control Plane, Named-pipe Local Worker (932 bytes)
- `decisions/README.md` — Architecture Decision Records (453 bytes)

## 17. JSON Schema·기계 판독 계약

- `specs/artifact-ref.schema.json` — artifact-ref.schema.json (1,806 bytes)
- `specs/backend-execution.schema.json` — backend-execution.schema.json (3,468 bytes)
- `specs/capability-binding.schema.json` — capability-binding.schema.json (1,349 bytes)
- `specs/capability-contract-v1.schema.json` — capability-contract-v1.schema.json (1,780 bytes)
- `specs/capability-contracts.generated.json` — 609개 기능별 기계 판독 구현 계약 (3,645,399 bytes)
- `specs/capability-registry.schema.json` — capability-registry.schema.json (4,744 bytes)
- `specs/document-graph-v2.schema.json` — document-graph-v2.schema.json (12,052 bytes)
- `specs/error-envelope.schema.json` — error-envelope.schema.json (1,545 bytes)
- `specs/feature-coverage-matrix.json` — 기능 coverage JSON 원본 (396,759 bytes)
- `specs/feature-row.schema.json` — feature-row.schema.json (1,691 bytes)
- `specs/job.schema.json` — job.schema.json (2,945 bytes)
- `specs/operation-plan-v2.schema.json` — operation-plan-v2.schema.json (6,251 bytes)
- `specs/project-state-v2.schema.json` — project-state-v2.schema.json (2,953 bytes)
- `specs/source-lock.schema.json` — source-lock.schema.json (1,981 bytes)
- `specs/style-v2.schema.json` — style-v2.schema.json (5,850 bytes)
- `specs/target-profile.schema.json` — target-profile.schema.json (1,915 bytes)
- `specs/template-contract.schema.json` — template-contract.schema.json (2,333 bytes)
- `specs/validation-report.schema.json` — validation-report.schema.json (2,559 bytes)
- `specs/work-breakdown-structure.json` — 190개 WBS JSON 원본 (81,512 bytes)

## 18. 스키마 예제·OperationPlan 레시피

- `specs/examples/operation-plan.example.json` — operation-plan.example.json (1,708 bytes)
- `specs/examples/recipes/01_custom_page_table_equation.json` — 01_custom_page_table_equation.json (2,959 bytes)
- `specs/examples/recipes/02_two_column_math_exam.json` — 02_two_column_math_exam.json (2,911 bytes)
- `specs/examples/recipes/03_surgical_template_fill.json` — 03_surgical_template_fill.json (1,861 bytes)
- `specs/examples/recipes/04_advanced_table.json` — 04_advanced_table.json (2,704 bytes)
- `specs/examples/recipes/05_native_equation_edit.json` — 05_native_equation_edit.json (1,293 bytes)
- `specs/examples/target-profile.example.yaml` — target-profile.example.yaml (579 bytes)

## 19. 플러그인 패키지 blueprint

- `specs/examples/plugin-codex-local/.codex-plugin/plugin.json` — plugin.json (1,426 bytes)
- `specs/examples/plugin-codex-local/.mcp.json` — .mcp.json (216 bytes)
- `specs/examples/plugin-codex-local/AGENTS.md` — HWPX Agent local instructions (351 bytes)
- `specs/examples/plugin-codex-local/README.md` — Codex local companion package blueprint (358 bytes)
- `specs/examples/plugin-codex-local/agents/hancom-document-engineer.md` — hancom-document-engineer.md (552 bytes)
- `specs/examples/plugin-codex-local/assets/icon.png` — icon.png (644 bytes)
- `specs/examples/plugin-codex-local/assets/logo.png` — logo.png (2,938 bytes)
- `specs/examples/plugin-codex-local/commands/create.md` — Command (185 bytes)
- `specs/examples/plugin-codex-local/commands/edit.md` — Command (161 bytes)
- `specs/examples/plugin-codex-local/commands/exam.md` — Command (113 bytes)
- `specs/examples/plugin-codex-local/commands/resume.md` — Command (89 bytes)
- `specs/examples/plugin-codex-local/commands/validate.md` — Command (105 bytes)
- `specs/examples/plugin-codex-local/skills/build-hancom-tables/SKILL.md` — Build Hancom Tables (1,070 bytes)
- `specs/examples/plugin-codex-local/skills/compose-math-exam/SKILL.md` — Compose Math Exam (1,463 bytes)
- `specs/examples/plugin-codex-local/skills/configure-page-layout/SKILL.md` — Configure Page Layout (1,116 bytes)
- `specs/examples/plugin-codex-local/skills/create-hancom-document/SKILL.md` — Create Hancom Document (1,690 bytes)
- `specs/examples/plugin-codex-local/skills/edit-hancom-document/SKILL.md` — Edit Hancom Document (1,295 bytes)
- `specs/examples/plugin-codex-local/skills/insert-native-equations/SKILL.md` — Insert Native Equations (965 bytes)
- `specs/examples/plugin-codex-local/skills/resume-hancom-project/SKILL.md` — Resume Hancom Project (1,028 bytes)
- `specs/examples/plugin-codex-local/skills/template-preserve-fill/SKILL.md` — Preserve and Fill Hancom Template (1,115 bytes)
- `specs/examples/plugin-codex-local/skills/validate-export-hancom/SKILL.md` — Validate and Export Hancom Document (1,102 bytes)
- `specs/examples/plugin-codex-remote/.codex-plugin/plugin.json` — plugin.json (1,426 bytes)
- `specs/examples/plugin-codex-remote/.mcp.json` — .mcp.json (172 bytes)
- `specs/examples/plugin-codex-remote/README.md` — Codex remote MCP blueprint (272 bytes)
- `specs/examples/plugin-codex-remote/assets/icon.png` — icon.png (644 bytes)
- `specs/examples/plugin-codex-remote/assets/logo.png` — logo.png (2,938 bytes)
- `specs/examples/plugin-codex-remote/skills/build-hancom-tables/SKILL.md` — Build Hancom Tables (1,070 bytes)
- `specs/examples/plugin-codex-remote/skills/compose-math-exam/SKILL.md` — Compose Math Exam (1,463 bytes)
- `specs/examples/plugin-codex-remote/skills/configure-page-layout/SKILL.md` — Configure Page Layout (1,116 bytes)
- `specs/examples/plugin-codex-remote/skills/create-hancom-document/SKILL.md` — Create Hancom Document (1,690 bytes)
- `specs/examples/plugin-codex-remote/skills/edit-hancom-document/SKILL.md` — Edit Hancom Document (1,295 bytes)
- `specs/examples/plugin-codex-remote/skills/insert-native-equations/SKILL.md` — Insert Native Equations (965 bytes)
- `specs/examples/plugin-codex-remote/skills/resume-hancom-project/SKILL.md` — Resume Hancom Project (1,028 bytes)
- `specs/examples/plugin-codex-remote/skills/template-preserve-fill/SKILL.md` — Preserve and Fill Hancom Template (1,115 bytes)
- `specs/examples/plugin-codex-remote/skills/validate-export-hancom/SKILL.md` — Validate and Export Hancom Document (1,102 bytes)
- `specs/examples/plugin-universal/.app.json` — .app.json (103 bytes)
- `specs/examples/plugin-universal/.codex-plugin/plugin.json` — plugin.json (1,451 bytes)
- `specs/examples/plugin-universal/README.md` — Universal ChatGPT Web/Codex package blueprint (477 bytes)
- `specs/examples/plugin-universal/assets/icon.png` — icon.png (644 bytes)
- `specs/examples/plugin-universal/assets/logo.png` — logo.png (2,938 bytes)
- `specs/examples/plugin-universal/skills/build-hancom-tables/SKILL.md` — Build Hancom Tables (1,070 bytes)
- `specs/examples/plugin-universal/skills/compose-math-exam/SKILL.md` — Compose Math Exam (1,463 bytes)
- `specs/examples/plugin-universal/skills/configure-page-layout/SKILL.md` — Configure Page Layout (1,116 bytes)
- `specs/examples/plugin-universal/skills/create-hancom-document/SKILL.md` — Create Hancom Document (1,690 bytes)
- `specs/examples/plugin-universal/skills/edit-hancom-document/SKILL.md` — Edit Hancom Document (1,295 bytes)
- `specs/examples/plugin-universal/skills/insert-native-equations/SKILL.md` — Insert Native Equations (965 bytes)
- `specs/examples/plugin-universal/skills/resume-hancom-project/SKILL.md` — Resume Hancom Project (1,028 bytes)
- `specs/examples/plugin-universal/skills/template-preserve-fill/SKILL.md` — Preserve and Fill Hancom Template (1,115 bytes)
- `specs/examples/plugin-universal/skills/validate-export-hancom/SKILL.md` — Validate and Export Hancom Document (1,102 bytes)

## 20. Skill·Agent·Command

- `agents/hancom-document-engineer.md` — hancom-document-engineer.md (552 bytes)
- `commands/create.md` — Command (185 bytes)
- `commands/edit.md` — Command (161 bytes)
- `commands/exam.md` — Command (113 bytes)
- `commands/resume.md` — Command (89 bytes)
- `commands/validate.md` — Command (105 bytes)
- `skills/build-hancom-tables/SKILL.md` — Build Hancom Tables (1,070 bytes)
- `skills/compose-math-exam/SKILL.md` — Compose Math Exam (1,463 bytes)
- `skills/configure-page-layout/SKILL.md` — Configure Page Layout (1,116 bytes)
- `skills/create-hancom-document/SKILL.md` — Create Hancom Document (1,690 bytes)
- `skills/edit-hancom-document/SKILL.md` — Edit Hancom Document (1,295 bytes)
- `skills/insert-native-equations/SKILL.md` — Insert Native Equations (965 bytes)
- `skills/resume-hancom-project/SKILL.md` — Resume Hancom Project (1,028 bytes)
- `skills/template-preserve-fill/SKILL.md` — Preserve and Fill Hancom Template (1,115 bytes)
- `skills/validate-export-hancom/SKILL.md` — Validate and Export Hancom Document (1,102 bytes)

## 21. 운영 템플릿

- `templates/ADR.md` — ADR-NNNN — 제목 (275 bytes)
- `templates/CAPABILITY_BINDING.md` — Capability Binding Review (451 bytes)
- `templates/HANDOFF.md` — HANDOFF — YYYY-MM-DD / Phase / 작업명 (272 bytes)
- `templates/INCIDENT.md` — Incident — ID / 제목 (313 bytes)
- `templates/OPERATION_REVIEW.md` — OperationPlan Review (298 bytes)
- `templates/PROJECT_STATE.json` — PROJECT_STATE.json (402 bytes)
- `templates/RELEASE_CHECKLIST.md` — Release Checklist (449 bytes)
- `templates/SOURCE_LOCK.md` — Source Lock Entry (167 bytes)
- `templates/TARGET_PROFILE.yaml` — TARGET_PROFILE.yaml (326 bytes)
- `templates/TEST_EVIDENCE.md` — Test Evidence (305 bytes)

## 22. Handoff

- `handoffs/0001-v2-design-complete.md` — HANDOFF 0001 — v2 설계 완료 및 구현 착수 기준선 (2,545 bytes)
- `handoffs/README.md` — Handoff 기록 (751 bytes)

## 23. 설계 생성·검증 도구

- `tools/README.md` — 설계 유지 도구 (585 bytes)
- `tools/design-generation/generate_capability_contracts.py` — generate_capability_contracts.py (52,689 bytes)
- `tools/design-generation/generate_wbs.py` — generate_wbs.py (31,138 bytes)
- `tools/design-validation/validate_design.py` — validate_design.py (7,480 bytes)
