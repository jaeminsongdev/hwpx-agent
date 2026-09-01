# 비동기 Job·Artifact 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Job 상태

`queued → leasing → running → validating → committing → succeeded`

종료 상태: `succeeded`, `failed`, `cancelled`, `expired`, `quarantined`.

## Job DAG

한 요청은 다음 stage를 가질 수 있다.

```text
preflight → materialize → direct_edit/automation_edit → reopen
          → oracle_open → render → visual_diff → export → commit
```

각 stage는 immutable input hashes와 output refs를 남긴다. retry는 stage 단위며 같은 idempotency key가 중복 revision을 만들지 않는다.

## lease와 heartbeat

- worker가 lease를 획득하고 주기적으로 heartbeat.
- lease 만료 시 stage를 재시도하되 외부 side effect 여부를 receipt로 확인.
- desktop automation은 process/session identity를 기록하고 hang 시 전체 session을 폐기.

## progress

퍼센트가 거짓 정밀도를 주지 않도록 `stage`, `completed_units`, `total_units`, `message`, `updated_at`을 제공한다. page render는 페이지 단위, batch conversion은 파일 단위로 보고한다.

## ArtifactRef

- immutable `artifact_id`.
- SHA-256 checksum, size, media type, filename.
- provenance: source revision/job/backend/build.
- validation state and quarantine state.
- retention and ACL.
- optional relationships: preview-of, export-of, evidence-for.

## 다운로드

ChatGPT/Codex 파일 전달이 가능한 surface에서는 attachment를 우선한다. 그 외에는 ACL-bound signed URL을 사용한다. URL 자체는 source of truth가 아니며 만료 후 `artifact_get`으로 재발급한다.

## 정리

임시 working copy와 한/글 recovery/autosave 파일은 job 종료/timeout/worker recycle 시 secure cleanup한다. evidence artifact는 retention policy에 따라 별도 보관한다.
