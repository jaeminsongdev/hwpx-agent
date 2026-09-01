# 관측성 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Trace hierarchy

`mcp_request → capability_plan → job → backend_execution → validation_step → artifact_commit`

## 필수 metrics

- tool latency/error by tool and tenant class
- capability route and fallback rate
- direct/automation success rate
- Hancom process startup/hang/modal/recycle counts
- package parse size/entry count
- validation level pass/fail/unverified
- page render time and visual diff failure
- idempotency hit, revision conflict, stale write
- queue wait and Windows pool saturation

## 로그 금지

문서 본문, 비밀번호, access token, signed URL, 개인 식별 값, 원본 binary를 로그에 남기지 않는다. 필요한 경우 artifact checksum, logical node id, parameter schema path만 기록한다.
