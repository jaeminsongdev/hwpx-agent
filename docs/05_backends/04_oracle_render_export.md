# HancomOracleBackend·렌더·내보내기

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## oracle 의미

실제 한/글에서 문서를 열 수 있다는 사실과, 저장 후 의미가 유지되고, 페이지가 기대대로 렌더된다는 사실은 서로 다른 evidence다.

## evidence 단계

1. `app_open`: 경고/복구 대화 없이 열림.
2. `app_inspect`: page/section/control count와 핵심 property readback.
3. `app_save_reopen`: 저장 후 새 session에서 재열림.
4. `native_edit_smoke`: 수식/표/개체가 native editor로 편집 가능.
5. `export_pdf/images`: 고정 profile로 렌더.
6. `visual_diff`: golden 또는 이전 revision과 비교.
7. `print_preview`: page range, paper/printer settings 확인.

## render profile

- Hancom build and OS image digest.
- locale, DPI, scaling.
- installed font inventory.
- default printer/virtual PDF driver.
- color profile.
- export options.

profile이 다르면 visual baseline을 직접 비교하지 않는다.

## visual metrics

page count, page dimensions, bounding boxes, overflow/clipping, blank pages, text line count, table split points, equation/object bounds, pixel diff/SSIM 등의 지표를 사용한다. 픽셀 diff는 semantic test를 대체하지 않는다.
