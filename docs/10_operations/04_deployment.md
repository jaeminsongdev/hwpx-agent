# 배포 토폴로지

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Linux plane

- HTTPS ingress/WAF.
- MCP gateway/control plane.
- project/job/artifact services.
- PostgreSQL HA and S3-compatible object store.
- queue/optional Redis.
- renderer/direct HWPX workers.

## Windows plane

private network의 licensed automation/oracle pools. Linux coordinator가 scoped job token으로 호출한다. inbound public access 금지, outbound default deny.

## regional/data residency

tenant policy에 따라 artifact와 metadata region을 고정한다. Windows worker도 같은 residency boundary 안에 둔다. cross-region DR는 암호화와 법적 정책을 따른다.

## secrets

OIDC, vault, short-lived workload identity. static worker credential을 image에 굽지 않는다. signing key는 HSM/provider boundary 밖으로 내보내지 않는다.

## network domains

MCP/UI CSP, artifact CDN, auth, telemetry, optional providers를 별도 allowlist로 관리한다. 문서 내 링크는 이 allowlist에 자동 추가하지 않는다.
