# Fallback·degradation·오류 정책

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 허용되는 fallback

- Direct HWPX → desktop automation: semantic operation과 validation plan이 동일할 때.
- Direct HWPX → hybrid normalize: 한/글이 생성해야 하는 derived/cached 구조가 있을 때.
- WebHWP → desktop automation: 동일 capability가 verified된 경우.
- HWP import → automation convert to HWPX → direct edit → optional HWP export.

## 금지되는 fallback

- native equation → image/plain text 자동 대체.
- unsupported shape/chart/OLE → screenshot 자동 대체.
- 지정 font → 임의 font silent substitution.
- protected/signed document → protection 제거 후 수정.
- dynamic field → 보이는 text만 바꾸고 field를 제거.

## degradation receipt

사용자가 명시적으로 허용한 경우에만 `degradation`을 기록한다.

```json
{
  "capability":"obj.wordart_insert",
  "requested":"native",
  "delivered":"preserved_raster_export_only",
  "reason":"target backend unavailable",
  "user_approved":true,
  "reversibility":"none"
}
```

## 오류 taxonomy

- `CAPABILITY_UNAVAILABLE`
- `TARGET_VERSION_UNVERIFIED`
- `PROTECTED_DOCUMENT`
- `SIGNATURE_WILL_INVALIDATE`
- `SELECTOR_AMBIGUOUS`
- `LAYOUT_CONSTRAINT_UNSATISFIABLE`
- `AUTOMATION_MODAL_BLOCKED`
- `AUTOMATION_TIMEOUT`
- `HWPX_SCHEMA_INVALID`
- `PRESERVATION_CONFLICT`
- `EXPORT_FAILED`
- `LICENSE_GATE_BLOCKED`
