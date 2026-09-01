# ChatGPT Web ↔ Codex 연속성

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## canonical state

```text
Project
 ├─ target_profile
 ├─ branches / head pointers
 ├─ immutable revisions
 ├─ artifacts / evidence
 ├─ checkpoints
 ├─ unresolved warnings
 └─ operation/audit history
```

## 전환 시나리오

1. Web에서 template upload와 초안 생성.
2. checkpoint `web-draft-1`.
3. Codex에서 같은 `project_id` open.
4. local fixture·코드 기반 일괄 편집 후 remote revision publish.
5. Web에서 새 head와 semantic diff 확인.
6. Hancom oracle validation 후 final checkpoint.

## conflict

- 동일 head에서 분기된 revision은 자동 overwrite하지 않는다.
- 텍스트·스타일·표·개체 단위 semantic 3-way merge를 시도.
- 같은 node/property 충돌은 conflict object로 반환.
- 사용자가 branch 선택/merge/fork를 명시하도록 한다.

## schema migration

project open 시 state/document/operation schema version을 검사한다. 읽기 가능한 이전 버전은 migrator로 새 immutable revision을 만들고, 원본은 유지한다.
