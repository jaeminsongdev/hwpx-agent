# 프로젝트·리비전·작업·아티팩트 서비스 구현

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 데이터 모델

- `Project`: tenant, ACL, target profile defaults, retention policy.
- `Revision`: immutable parent(s), source/output artifact, operation plan hash, semantic diff, validation summary.
- `Checkpoint`: 사람이 붙인 immutable label.
- `Job`: state machine, lease, attempts, cancellation, receipts.
- `Artifact`: content-addressed blob + metadata + encryption/retention.
- `IdempotencyRecord`: key, normalized request hash, terminal result.

## revision commit

```sql
BEGIN;
SELECT head_revision FROM projects WHERE id=? FOR UPDATE;
ASSERT head_revision = expected_revision;
INSERT revision(... immutable ...);
UPDATE projects SET head_revision=new_revision WHERE id=? AND head_revision=expected_revision;
INSERT audit_event(...);
COMMIT;
```

artifact는 commit 전에 checksum이 확정돼야 한다. DB commit 실패 시 blob은 orphan marker를 달고 보존 기간 후 수거한다.

## job lease

worker는 자신의 target profile과 capability set을 보고하고 compatible job만 lease한다. lease에는 fencing token과 expiry가 있다. 늦은 worker가 결과를 업로드해도 current fencing token이 아니면 revision commit을 할 수 없다.

## 재시도

- planning/schema error: 재시도 없음.
- transient storage/network: 같은 stage에서 bounded retry.
- automation crash/timeout: fresh worker + reconciliation 후 retry.
- validation mismatch: 자동 재시도하지 않고 deterministic failure로 기록.
- user cancellation: safe point에서 중지하고 temporary output 폐기.

## artifact 보안

- content-addressed key와 tenant ACL을 분리한다.
- at-rest encryption, signed URL short TTL, download audit.
- untrusted input/output/evidence/temp를 다른 bucket/prefix로 격리한다.
- malware/OLE/script scan 결과와 quarantine state를 metadata에 둔다.
- widget 응답에는 대형 문서 본문 대신 ArtifactRef만 반환한다.

## Web↔Codex 연속성

둘 다 같은 `project_id`와 remote revision head를 사용한다. Codex local cache는 mirror이며 push 전에 expected revision을 확인한다. conflict는 `rebase operation plan`, `branch`, `manual merge` 중 하나로 처리하며 원격 head를 덮어쓰지 않는다.

## retention

원본, output, preview, logs, screenshots, traces의 보존 기간을 별도로 설정한다. 사용자 삭제는 legal hold를 제외하고 tombstone→background purge→verification receipt 순서로 진행한다.
