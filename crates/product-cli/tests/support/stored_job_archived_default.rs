use super::*;
#[test]fn shared_job_path_stores_original_manifest_in_v2_intent_by_default()->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-archived-default")?;let r=LifecycleJobs::service(&f,0);let c=writer(&f);let root=tempfile::tempdir()?;
    let report=run(&f,&m,&r,&c,&root.path().join("workspace"),SOURCE,true)?;assert_eq!(report.stage,StoredJobRunStage::Completed);
    let intent=report.intent.ok_or("intent")?;let raw=f.artifacts.download(&c,intent.artifact_id,20)?;let value:serde_json::Value=serde_json::from_slice(&raw)?;
    assert_eq!(value["schema_version"],"hwpx-agent.stored-revision-commit-intent/v2");
    let archive:Vec<u8>=serde_json::from_value(value["manifest_canonical_json"].clone())?;assert_eq!(archive,m.canonical_json()?);
    assert_eq!(value["commit_intent"]["schema_version"],"hwpx-agent.stored-revision-commit-intent/v1");
    assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);Ok(())
}
