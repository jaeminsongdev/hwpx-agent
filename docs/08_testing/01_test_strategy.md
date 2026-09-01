# 전체 테스트 전략

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 테스트 피라미드

1. pure unit: units, IDs, selectors, AST, style cascade, table grid.
2. property-based: package/relationship/ID allocation, edit idempotency.
3. schema/contract: JSON Schema, generated capability bindings.
4. fixture round-trip: direct HWPX parse/write/reparse.
5. differential: direct backend vs desktop automation.
6. real Hancom oracle: open/save/edit/export.
7. render/visual: page raster and layout metrics.
8. MCP/app E2E: ChatGPT/Codex simulated clients.
9. security/fuzz/performance/recovery.

## invariant tests

- input artifact immutable.
- same idempotency key → same committed result.
- failed operation → no partial revision.
- untouched parts satisfy byte/token preservation policy.
- all relationships resolve and no orphan resource unexpectedly deleted.
- logical IDs remain stable or remap receipt exists.
- unsupported capability never silently degrades.
- `verified` always points to evidence artifact.

## 환경

- Linux: control plane, direct HWPX, API, storage, fuzz.
- Windows images: target Hancom builds, desktop automation, print/export.
- browser: widget and accessibility.
- optional WebHWP deployment: dedicated integration lane.
