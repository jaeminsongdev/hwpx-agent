# 릴리스·롤백 Runbook

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## release

- source/catalog locks 확인.
- schema backward compatibility.
- migration dry-run/restore point.
- capability enablement diff.
- primary/secondary target oracle results.
- plugin manifest/tool descriptor diff.
- legal/license/security approvals.
- canary tenant and rollback criteria.

## rollback triggers

- semantic corruption.
- unexpected page/layout regression.
- worker modal/hang spike.
- auth/tenant boundary error.
- invalid signature/protection behavior.
- duplicate/partial revisions.

## rollback action

새 writes 차단 → capability flag disable → prior service image → affected jobs quarantine → artifact/revision integrity scan → 사용자 통지/복구 branch. 이미 생성된 artifact를 덮어쓰지 않는다.
