# 공식 기능 카탈로그 importer와 binding 생성기

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 목적

“한/글의 모든 기능”을 사람이 기억으로 관리하지 않고 대상 build별 증거가 있는 capability registry로 만든다. 메뉴 도움말, HWPX/OWPML 스키마, ActionTable, ParameterSetTable, Automation 객체/이벤트, WebHWP 문서, runtime probe를 합집합으로 수집한다.

## 파이프라인

```text
immutable source lock
  -> format-specific extractor
  -> SourceRecord[]
  -> normalization/dedup candidates
  -> reviewer mapping to semantic capability
  -> target-build binding generator
  -> runtime probe
  -> signed capability registry
  -> coverage/missing/drift report
```

## SourceRecord 최소 필드

```json
{
  "source_id": "hancom-actiontable-2504",
  "source_sha256": "...",
  "source_kind": "action_table|parameter_table|help|xsd|runtime",
  "locator": {"page": 12, "section": "...", "anchor": "..."},
  "original_name": "...",
  "description_ko": "...",
  "parameters": [],
  "availability": {"product": "...", "build_range": "...", "locale": "ko-KR"}
}
```

## 정규화 알고리즘

1. Unicode NFC와 공백/괄호/단축키 표기를 정규화한다.
2. 원문 이름은 절대 덮어쓰지 않고 `normalized_label`을 추가한다.
3. 메뉴와 action 이름을 문자열 유사도만으로 자동 병합하지 않는다.
4. `feature_ko`, 저장 의미, 입력/출력, side effect, 대상 객체가 모두 맞을 때만 같은 capability 후보로 묶는다.
5. one-to-many는 composite operation, many-to-one은 alias/source reference로 표현한다.
6. reviewer가 semantic capability와 scope/support level을 승인한다.

## AutomationBinding

```json
{
  "binding_key": "table.merge_cells@hancom-2024/13.x/ko-KR",
  "capability_id": "table.merge_cells",
  "target_profile": "...",
  "invocation": {
    "kind": "action|method|control_property|event",
    "action_id": "TARGET_DISCOVERED_VALUE",
    "parameter_set": "TARGET_DISCOVERED_VALUE",
    "parameter_map": []
  },
  "probe": {
    "fixture_id": "...",
    "pre_snapshot": "...",
    "post_snapshot": "...",
    "expected_effect": "..."
  },
  "source_refs": [],
  "status": "candidate|verified|disabled|deprecated"
}
```

## Runtime probe 절차

- disposable 문서와 disposable Windows desktop을 사용한다.
- action 실행 전 UI/문서/selection state를 정규화한다.
- default ParameterSet을 읽고 필드 이름·타입·enum/range를 기록한다.
- 최소값, 정상값, 경계값, 잘못된 값을 각각 실행한다.
- pre/post DocumentSnapshot과 control/property readback을 비교한다.
- 예상치 못한 modal/network/file side effect가 있으면 binding을 high-risk로 격리한다.
- 저장 후 새 process에서 reopen하고 의미가 남는지 확인한다.

## Drift 처리

새 build가 들어오면 이전 registry와 비교해 `added`, `removed`, `renamed`, `parameter_changed`, `behavior_changed`, `render_changed`, `unknown`을 출력한다. `behavior_changed` 또는 `unknown` capability는 자동 승격하지 않고 기존 production target을 유지한다.

## 검토 UI

reviewer는 한 화면에서 원문 source, 후보 capability, target binding, fixture diff, render diff, 위험/권한을 비교해야 한다. 승인에는 reviewer, timestamp, source hashes, code revision, target image digest가 서명된다.

## 완료 기준

- 모든 official/runtime item이 mapped/ignored-with-reason 중 하나다.
- 모든 `AUTOMATION_FULL`/`HYBRID` capability에 target binding 또는 명시적 unavailable가 있다.
- generated registry는 schema-valid, deterministic, signed다.
- source drift 시 CI가 support claim을 자동으로 재평가한다.
