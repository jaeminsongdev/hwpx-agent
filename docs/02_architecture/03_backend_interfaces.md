# Backend 인터페이스

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Rust trait 개념

```rust
#[async_trait]
pub trait HancomBackend: Send + Sync {
    fn descriptor(&self) -> BackendDescriptor;
    async fn probe(&self, target: &TargetProfile) -> ProbeResult;
    async fn inspect(&self, input: ArtifactRef, opts: InspectOptions) -> Result<InspectReceipt>;
    async fn execute(&self, req: BackendExecutionRequest) -> Result<ExecutionReceipt>;
    async fn validate(&self, req: BackendValidationRequest) -> Result<ValidationEvidence>;
    async fn render(&self, req: RenderRequest) -> Result<RenderReceipt>;
    async fn cancel(&self, execution_id: ExecutionId) -> Result<CancelReceipt>;
}
```

## BackendExecutionRequest

- request/project/revision/idempotency identifiers
- source artifact and checksum
- target profile: format, Hancom build, locale, fonts, printer profile
- edit mode
- normalized OperationPlan
- policy decision and granted capabilities
- expected output artifacts
- resource limits and timeout
- validation plan

## ExecutionReceipt

- backend identity/build/image digest
- exact capability bindings used
- input/output checksums
- touched package parts or automation action trace
- warnings and degradations
- semantic diff
- normalization events
- validation evidence references
- process logs with secrets/PII redacted

## 교차 백엔드 동일성

두 backend가 같은 capability를 구현하면 같은 operation fixtures를 실행하고 semantic snapshot을 비교한다. byte equality는 요구하지 않되, 의미·relationship·객체 식별·render tolerance가 동일해야 한다.
