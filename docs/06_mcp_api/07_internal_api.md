# Control Plane ↔ Backend 내부 API

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## BackendExecutionRequest

```json
{
  "execution_id":"exec_...",
  "target_profile":"hancom-2024-13.x-ko-KR",
  "source_artifact":{"artifact_id":"art_...","sha256":"..."},
  "mode":"surgical_preserve",
  "resolved_operations":[],
  "validation_contract":[],
  "resource_limits":{"wall_seconds":120,"memory_mb":2048,"max_output_mb":256},
  "security_policy":{"allow_ole_execution":false,"allow_external_network":false},
  "trace_level":"safe"
}
```

## BackendExecutionReceipt

- backend name/version/build.
- resolved capability binding version.
- per-operation state, changed nodes/parts, warnings.
- input/output checksum.
- opaque IDs remap table.
- generated resources and garbage collection report.
- validation evidence refs.
- dialogs/events encountered.
- process/session and timing metrics.

## invariants

- backend는 project DB를 직접 수정하지 않는다.
- backend는 입력 artifact를 in-place 변경하지 않는다.
- backend는 operation capability 외 기능을 실행하지 않는다.
- file/network access는 manifest allowlist를 따른다.
- receipt 없이 성공으로 간주하지 않는다.

## protocol

초기 구현은 JSON/MessagePack over local authenticated gRPC 또는 named pipe를 사용한다. binary artifact는 object storage ref 또는 local staged path handle로 전달하고 RPC 본문에 base64로 넣지 않는다. wire schema는 versioned이며 Rust/Python/.NET 모두 동일 conformance tests를 통과한다.
