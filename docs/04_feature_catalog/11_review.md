# 검토·비교·이력 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

한/글 변경 추적/비교와 제품 revision DAG를 혼동하지 않고 별도 그래프로 유지한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (20개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| REVIEW-001 | 변경 내용 추적 켜기/끄기 | `review.track_enable` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-002 | 변경 내용 표시 설정 | `review.track_display` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-003 | 검토자별 변경 필터 | `review.track_filter_author` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-004 | 변경 내용 보호 | `review.track_protect` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-005 | 선택 변경 내용 적용 | `review.track_accept_one` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-006 | 선택 변경 내용 취소 | `review.track_reject_one` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-007 | 모든 변경 적용 | `review.track_accept_all` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-008 | 모든 변경 취소 | `review.track_reject_all` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-009 | 검토자 이름 설정 | `review.reviewer_name` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-010 | 문서 이력 관리 | `review.document_history` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-011 | 문서 비교 | `review.document_compare` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-012 | 비교 결과 병합 | `review.document_merge_review` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-013 | 메모 작성자/시간 | `review.comment_author` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-014 | 이전/다음 메모 | `review.comment_navigation` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-015 | 메모 삭제 | `review.comment_delete` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-016 | 모든 메모 삭제 | `review.comment_delete_all` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-017 | 교정 부호 표시 | `review.correction_marks_show` | `workstation_ui` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-018 | 검토 내역 보고서 | `review.revision_export` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | change_readback·save_reopen·visual_diff |
| REVIEW-019 | 제품 semantic diff | `review.semantic_diff` | `artifact_semantics` | `DIRECT_FULL` | `direct_hwpx` | P04 | diff_golden |
| REVIEW-020 | 제품 revision DAG | `review.revision_graph` | `artifact_semantics` | `DIRECT_FULL` | `direct_hwpx` | P04 | diff_golden |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/11_review_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
