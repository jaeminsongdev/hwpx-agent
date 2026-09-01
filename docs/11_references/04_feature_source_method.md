# 기능 전수 목록 작성 방법

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## source union

```text
Hancom Help menus/details
  ∪ OWPML/HWPX schemas and package parts
  ∪ Automation Action/Parameter/Object/Event manuals
  ∪ WebHWP actions/controls/APIs
  ∪ target-build runtime probe/macro discovery
  ∪ observed document fixtures
```

어느 하나만으로 “모든 기능”을 정의하지 않는다. 도움말은 UI 기능을, schema는 저장 의미를, automation은 실행 가능성을, runtime은 build drift를 보여 준다.

## normalization

원문 label → candidate capability → semantic name → scope class → operation schema → backend bindings. 같은 기능이 메뉴와 action에 중복 등장하면 하나의 capability 아래 source references를 여러 개 둔다.

## scope class

- `artifact_semantics`: 문서에 저장되는 의미.
- `editor_workflow`: 문서를 바꾸지만 편집기 실행이 핵심.
- `workstation_ui`: 보기/창/환경 설정.
- `external_service`: OCR/번역/한컴독스/메일 등 provider.
- `security_control`: 암호/보호/서명/스크립트.

## completeness

`FEATURE_COVERAGE_MATRIX.csv`는 사람이 시작한 v2 baseline이다. P02 importer가 공식 source를 구조화한 뒤 다음 diff를 낸다.

- missing official item.
- catalog item without official/runtime binding.
- renamed/deprecated/build-specific item.
- one-to-many or many-to-one mapping needing review.

따라서 609는 고정된 영원한 숫자가 아니라 2026-08-31 설계 baseline이며, production claim은 target build generated registry 기준이다.
