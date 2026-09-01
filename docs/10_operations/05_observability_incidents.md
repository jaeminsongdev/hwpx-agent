# 관측성·장애 대응

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## telemetry

- request/tool latency and status.
- capability/backend routing.
- job queue/lease/retry/stage.
- Windows worker startup/hang/recycle/modal.
- document size/pages/features, 단 원문·파일명은 기본 수집 금지.
- validation failure by target build.
- artifact/storage/DB errors.

## correlation

`request_id → job_id → execution_id → revision_id → evidence_id`를 연결한다. 사용자에게 표시되는 오류 코드와 내부 trace를 연결하되 secret/path/content redaction.

## SLO 예시

- read-only control-plane availability.
- queued job start percentile.
- small direct edit completion percentile.
- automation job success excluding invalid input.
- duplicate/partial commit rate = 0.
- verified evidence integrity = 100%.

## incident classes

- data integrity/revision mismatch.
- tenant or signed URL leakage.
- automation license/service outage.
- target build drift/regression.
- malware/OLE/script escape.
- mass rendering/export failure.

data integrity/security 사고는 capability disable/worker pool quarantine/publish freeze를 자동화한다.
