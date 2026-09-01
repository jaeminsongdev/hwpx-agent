# 보안·보호·개인정보 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

보안 기능은 별도 trust boundary에서 처리한다. 암호·서명·보호 우회는 절대 암묵적으로 수행하지 않는다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (24개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| SEC-001 | 문서 열기 암호 설정 | `sec.open_password_set` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-002 | 문서 암호 변경 | `sec.open_password_change` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-003 | 문서 암호 해제 | `sec.open_password_remove` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-004 | 배포용 문서로 저장 | `sec.distribution_save` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-005 | 배포용 문서 편집 | `sec.distribution_edit` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-006 | 배포용 문서 암호 변경/해제 | `sec.distribution_password` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-007 | 선택 글자 보호 | `sec.protect_selection` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-008 | 개인정보 찾아서 보호 | `sec.privacy_find_protect` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-009 | 개인정보 보호 해제 | `sec.privacy_unprotect` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-010 | 개인정보 보호 암호 변경 | `sec.privacy_password_change` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-011 | 문서 보안 설정 | `sec.document_security_settings` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-012 | 편집 제한 | `sec.edit_restriction` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-013 | 개체 보호 | `sec.object_protection` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-014 | 양식 입력만 허용 | `sec.form_protection` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-015 | 전자서명 상태 확인 | `sec.signature_inspect` | `security_control` | `READ_ONLY` | `direct_hwpx` | P11 | signature_state·policy |
| SEC-016 | 수정 시 서명 무효화 경고 | `sec.signature_invalidation` | `security_control` | `READ_ONLY` | `direct_hwpx` | P11 | signature_state·policy |
| SEC-017 | 승인된 외부 서명 연동 | `sec.digital_sign` | `security_control` | `OPTIONAL_EXTERNAL` | `external_signing_service` | P19 | provider_contract·signature_verify |
| SEC-018 | 개인정보/메타데이터 제거 | `sec.sanitize_metadata` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-019 | 스크립트 매크로 보안 설정 | `sec.macro_security` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-020 | 외부 링크 차단/허용 정책 | `sec.external_link_policy` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-021 | 암호 문서 열기 | `sec.encrypted_open` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-022 | 보호 상태 유지 복제 | `sec.protected_copy` | `security_control` | `AUTOMATION_FULL` | `desktop_automation` | P11 | negative_auth·save_reopen·protection_state |
| SEC-023 | 문서 보안 요소 감사 | `sec.security_audit` | `security_control` | `READ_ONLY` | `direct_hwpx` | P11 | signature_state·policy |
| SEC-024 | 암호·보호 우회 | `sec.password_bypass` | `security_control` | `UNSUPPORTED` | `` | N/A | policy_negative_test |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/12_sec_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
