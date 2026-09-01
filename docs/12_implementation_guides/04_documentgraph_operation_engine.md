# DocumentGraph·OperationPlan·트랜잭션 엔진 구현

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## DocumentGraph 원칙

DocumentGraph는 HWPX XML의 복사본이 아니라 문서 의미를 표현한다. 각 노드는 `logical_id`, `kind`, `properties`, `children`, `source_binding`, `opaque_extensions`를 갖는다. `source_binding`은 특정 backend lowering을 위한 힌트이며 public API에 노출하지 않는다.

## selector 해석

selector는 다음 우선순위로 resolve한다.

1. stable logical ID.
2. template slot/field/bookmark 이름.
3. structural path + expected fingerprint.
4. text query + context hash.
5. cursor/session selector는 automation 전용.

텍스트 위치만 저장하지 않는다. 편집 후 offset drift를 막기 위해 anchor pair와 content fingerprint를 사용한다. 후보가 0개 또는 여러 개면 정책에 따라 실패하며 임의 첫 항목을 선택하지 않는다.

## OperationPlan compile

```text
JSON schema validation
 -> capability lookup
 -> selector type check
 -> unit/default normalization
 -> operation dependency DAG
 -> static precondition check
 -> backend route plan
 -> preservation impact
 -> validation plan
 -> risk/permission prompt plan
```

compile 결과는 실행 전 사용자/agent가 읽을 수 있는 `PlanReceipt`다. 모호한 mm/pt, 표 셀 범위, 수식 source, 출력 형식, 보호 해제는 `needs_resolution`로 남긴다.

## transaction state machine

```text
RECEIVED
 -> PLANNED
 -> PRECONDITIONS_VERIFIED
 -> WORKSPACE_PREPARED
 -> EXECUTING
 -> READBACK
 -> VALIDATING
 -> ARTIFACT_COMMITTED
 -> REVISION_CAS_COMMITTED
 -> COMPLETED
```

어느 단계든 실패하면 source revision은 바뀌지 않는다. artifact commit 후 revision CAS가 실패한 경우 artifact는 orphan quarantine으로 옮겨 garbage collection 대상이 된다.

## operation executor pseudo-code

```rust
async fn execute(plan: OperationPlan, ctx: RequestContext) -> Result<RevisionReceipt> {
    let compiled = planner.compile(plan, &ctx).await?;
    policy.authorize(&compiled, &ctx.actor)?;
    idempotency.claim(&ctx.idempotency_key, compiled.hash())?;
    revisions.assert_head(&ctx.project_id, ctx.expected_revision)?;

    let workspace = workspace_factory.create(compiled.mode()).await?;
    for op in compiled.topological_operations() {
        let route = router.select(op, &workspace.snapshot(), &ctx.target_profile)?;
        let receipt = route.execute(op, &mut workspace).await?;
        workspace.record(receipt);
    }
    let snapshot = workspace.readback().await?;
    validator.verify(&compiled.postconditions, &snapshot).await?;
    let artifact = workspace.commit_artifact().await?;
    revisions.compare_and_swap_commit(ctx, artifact, workspace.receipts()).await
}
```

## semantic diff

텍스트 diff만 제공하지 않는다. `NodeAdded/Removed/Moved`, property delta, style mapping, table grid/span, MathAst, object geometry, reference target, review/security change를 별도 타입으로 기록한다. 사용자 preview에서는 영향 요약과 affected pages를 제공한다.

## idempotency

같은 key와 같은 normalized plan hash는 같은 결과를 반환한다. 같은 key에 다른 plan은 `IDEMPOTENCY_KEY_REUSED`로 거부한다. backend timeout 후 결과가 불확실하면 readback/reconciliation 전까지 재실행하지 않는다.

## 완료 기준

- DAG cycle, stale selector, conflict, CAS failure, worker timeout에 대한 테스트.
- 1,000개 operation batch에서도 deterministic result/hash.
- dry-run과 실제 실행 route가 environment drift 외에는 동일.
- partial backend output이 public revision이 되지 않음.
