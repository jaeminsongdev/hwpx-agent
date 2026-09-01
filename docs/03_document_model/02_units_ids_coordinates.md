# 단위·좌표·식별자 규약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## public unit

API는 `mm`, `pt`, `percent`, `deg`, `px@dpi`를 사용한다. backend 전용 HWPUNIT 또는 내부 정수는 공개하지 않는다.

```json
{"value": 12.0, "unit": "mm"}
```

정규화 규칙:

- 문서 layout 길이는 내부적으로 `LengthMicrometers(i64)`에 저장한다.
- 글자 크기는 `PointMilli(i64)`로 저장한다.
- 비율은 fixed-point millionths로 저장한다.
- 변환은 banker's rounding이 아니라 명시된 half-away-from-zero를 사용하고 receipt에 rounding delta를 기록한다.
- source 값은 가능한 경우 raw integer도 provenance에 보존한다.

## 사용자 정의 용지

한/글 2024 도움말에 맞춰 target desktop compatibility profile의 사용자 정의 용지는 기본적으로 폭·높이 각각 20mm 이상 1188mm 이하를 허용한다. 다른 버전/백엔드는 capability constraint로 별도 선언한다.

## 좌표계

- `page`: 편집 용지 좌상단 원점.
- `content`: 본문 영역 좌상단 원점.
- `anchor`: 문단/글자 기준 anchor.
- `object-local`: 개체 자체 좌표.

모든 drawing position은 좌표계와 anchor를 함께 명시한다. 절대 x/y만 있는 operation은 reject한다.

## Z-order와 그룹

Z-order는 sparse signed integer로 관리하고 backend lowering 때 연속 ID로 변환한다. 그룹 내부 좌표계와 문서 좌표계를 분리한다.

## ID 종류

- `DocumentId`, `ProjectId`, `RevisionId`, `ArtifactId`
- `LogicalNodeId`, `StyleId`, `ResourceId`, `BookmarkId`, `FieldId`, `ChangeId`
- `BackendOpaqueId`는 source anchor 내부에만 존재

ID는 type-safe newtype으로 구현해 문자열 혼용을 막는다.
