# 상태·revision·transaction

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 데이터 객체

- `Project`: 문서 작업의 논리 컨테이너.
- `Revision`: 부모 revision, source artifact, operation plan, result artifact, evidence를 가리키는 immutable node.
- `Artifact`: checksum으로 식별되는 immutable blob.
- `Checkpoint`: revision에 붙는 사용자 의미 label.
- `Branch`: project 안의 가변 head pointer.
- `Job`: 실행 DAG와 상태.

## mutation protocol

1. client가 `expected_revision`과 `idempotency_key`를 보낸다.
2. 서버가 현재 branch head를 확인한다.
3. dry-run plan hash를 확정한다.
4. backend는 격리 temp output을 만든다.
5. validation gate를 통과하면 artifact를 content-addressed storage에 업로드한다.
6. DB transaction에서 revision과 head update를 원자적으로 commit한다.
7. retry는 같은 idempotency key와 plan hash면 기존 receipt를 반환한다.

## conflict

- head가 다르면 `REVISION_CONFLICT`와 base/head semantic diff를 반환한다.
- 자동 rebase는 text-only, non-overlapping logical node edits에 한해 명시적으로 수행한다.
- layout, table structure, review/protection, automation operations는 기본적으로 수동 재계획한다.
