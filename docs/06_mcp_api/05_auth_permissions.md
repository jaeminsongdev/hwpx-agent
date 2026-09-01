# 인증·권한·승인

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 주체

- `EndUser`: ChatGPT/Codex 사용자의 계정.
- `Workspace`: 조직/tenant.
- `ServicePrincipal`: MCP gateway, worker, CI oracle.
- `ExternalProviderIdentity`: WebHWP/한컴독스/서명 서비스 등.

## 권한 범주

- `document.read`, `document.write`, `document.delete`.
- `project.manage`, `project.publish`.
- `template.use`, `template.admin`.
- `automation.use`, `automation.admin`.
- `review.accept`, `security.modify`.
- `external_service.use`, `credential.use`.
- `audit.read`, `support.impersonate`(break-glass만).

## 도구 annotation

- inspect/plan/check/get/history는 read-only.
- create/edit/transform/export/checkpoint/publish/cancel은 mutation.
- `document_export`가 외부 서버 업로드·메일 발송까지 포함하지 않도록 분리한다. 외부 전송은 별도 명시적 capability와 승인 필요.
- 서명 무효화, 비밀번호 제거, 배포용 문서 수정, 개인정보 보호 해제는 high-risk confirmation을 요구한다.

## OAuth/OIDC

원격 MCP는 OAuth/OIDC를 사용하고 토큰의 tenant/user/scopes를 서버에서 검증한다. signed artifact URL은 사용자·artifact·operation에 binding되고 짧은 TTL을 사용한다.

## credential vault

문서 암호, 외부 provider token, signing key는 요청 payload·log·revision metadata에 저장하지 않는다. vault handle만 job에 전달하며 worker 종료 후 메모리와 임시 파일을 정리한다.

## 승인 수준

1. `silent-safe`: read-only, deterministic, local document scope.
2. `normal-write`: 새 revision 생성, idempotent.
3. `high-impact`: 서명 무효화/보호 변경/외부 전송/인쇄/메일.
4. `admin-only`: automation allowlist, worker image, licensing, provider credentials.
