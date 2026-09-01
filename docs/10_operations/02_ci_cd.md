# CI/CD

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## PR lanes

- formatting/lint/static analysis.
- JSON Schema validation and generated-code drift.
- Rust/Node/.NET unit tests.
- direct HWPX fixtures/property/fuzz smoke.
- API/tool descriptor snapshot.
- documentation links/manifest/checksum.

## protected lanes

- Windows Hancom integration.
- full golden/render comparison.
- security fuzz extended.
- plugin staging connection.
- backup/restore and migration.

## artifact provenance

빌드 산출물은 source commit, lockfiles, compiler versions, worker image digest, target profile, SBOM, signatures를 기록한다.

## promotion

`dev → staging → canary → production`. schema migration과 capability enablement는 별도 feature flag. direct backend와 automation backend를 capability 단위로 canary한다.

## rollback

서버 rollback과 문서 artifact rollback을 분리한다. artifact/revision은 immutable이므로 이전 head를 publish할 수 있다. DB migration은 expand/contract 또는 backward-compatible pattern을 사용한다.
