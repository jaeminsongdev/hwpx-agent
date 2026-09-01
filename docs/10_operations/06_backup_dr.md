# 백업·재해 복구

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 보호 대상

- PostgreSQL project/revision/job/audit metadata.
- object storage artifacts/evidence/source locks.
- capability catalogs/bindings/target profiles.
- deployment config/secret references.
- Windows image manifests와 재구축 스크립트.

## 전략

DB PITR + object versioning/replication + immutable backup. artifact는 content-addressed이므로 restore 후 checksum sweep으로 누락을 검출한다.

## 복구 순서

1. control plane read-only mode.
2. DB restore and revision graph consistency.
3. object inventory/checksum reconcile.
4. capability/source lock restore.
5. job lease expiration/requeue safety analysis.
6. Windows pool rebuild and oracle smoke.
7. limited tenant canary, write reopen.

## drill

분기별 restore drill과 연 1회 region-loss drill. RPO/RTO는 배포 전에 제품 정책으로 확정하고 evidence를 release gate에 연결한다.
