# 609개 기능 Conformance 체계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


`FEATURE_COVERAGE_MATRIX.csv`의 각 row는 하나 이상의 테스트 case와 binding되어야 한다.

## 상태

`cataloged → bound → unit_passed → integration_passed → oracle_verified → release_enabled`

build별로 상태를 분리한다. 새 한/글 patch에서는 이전 `oracle_verified`를 그대로 상속하지 않고 smoke/delta suite를 실행한다.

## capability test manifest

- capability ID / feature ID.
- target profile.
- input fixture and precondition.
- semantic operation payload.
- expected changed properties.
- expected unchanged regions.
- backend/binding ID.
- validation sequence.
- rollback/retry test.
- risk and permission negative tests.

## completeness query

GA gate는 다음이 0인지 확인한다.

- feature row without capability.
- capability without operation schema.
- release-enabled capability without target binding.
- mutation capability without negative/rollback test.
- automation capability without timeout/modal test.
- external feature without provider/license state.
