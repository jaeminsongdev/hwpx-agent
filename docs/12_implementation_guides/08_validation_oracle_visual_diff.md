# 검증·실제 한/글 Oracle·시각 차이 시스템

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 검증은 계층형 evidence다

```text
L0 request/schema
L1 package/ZIP safety
L2 XML/XSD/relationship/reference
L3 semantic reopen/readback
L4 backend differential
L5 target Hancom open
L6 target Hancom save/reopen
L7 render/visual/layout
L8 print/export/accessibility/security
```

수행하지 않은 단계는 pass가 아니라 `unverified`다.

## ValidationEvidence

```json
{
  "validator_id": "hancom-save-reopen",
  "validator_version": "...",
  "target_profile": "...",
  "state": "pass|fail|unverified|skipped_by_policy",
  "input_sha256": "...",
  "output_sha256": "...",
  "assertions": [],
  "artifact_refs": [],
  "environment_digest": "...",
  "started_at": "...",
  "duration_ms": 0
}
```

## semantic snapshot

문서의 전체 raw XML hash와 별도로 text flow, styles, page/section setup, tables/grid/formulas, equations AST, objects/assets/geometry, fields/references, review/security를 canonical JSON으로 만든다. feature별 비교기는 관련 영역만 strict하게, unrelated 영역은 preservation policy로 비교한다.

## Hancom oracle

- 생성 worker와 별도 fresh process/image에서 실행한다.
- open error, repair prompt, font substitution, save warning, format conversion warning을 모두 evidence로 수집한다.
- save/reopen 후 semantic snapshot을 다시 만든다.
- oracle 자체의 build와 image digest를 고정한다.
- Oracle이 성공했다고 의미가 맞는 것은 아니므로 postcondition 비교와 함께 사용한다.

## render pipeline

가능하면 같은 target 한/글에서 PDF 또는 page image를 생성한다. 대체 renderer는 fast feedback이며 final oracle을 대체하지 않는다. page별 픽셀 외에 OCR이 아니라 text/object bounding box, baseline, line/page break, table grid, equation bounds를 구조적으로 비교한다.

## visual diff tolerance

전역 하나의 픽셀 threshold를 사용하지 않는다.

- text: baseline/line break/page membership strict.
- table: grid line/merged region/cell content bounds strict.
- equation: object/baseline/ink box tolerance.
- raster image: placement/size strict, pixel content hash or perceptual threshold.
- antialiasing/color profile: narrow configurable tolerance.

layout 변화가 의도된 operation이면 expected affected region을 명시하고 그 밖 영역은 더 엄격하게 검사한다.

## fixture minimization

실패 문서에 대해 part, section, paragraph, control을 delta-debugging으로 줄이되 실패 증상을 oracle로 재확인한다. 라이선스/개인정보 문서는 원본을 공개 corpus로 이동하지 않고 synthetic reproduction을 만든다.

## release report

capability×target profile matrix에서 required evidence의 freshness, flaky rate, last pass, known degradation을 표시한다. target build 변경 또는 binding/schema/compiler 변경 시 관련 evidence를 invalidation한다.
