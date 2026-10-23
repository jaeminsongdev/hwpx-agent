use super::*;
use operation_engine::ArchivedExecutionManifest as Archive;
fn original()->Result<ExecutionManifest,Box<dyn Error>>{fixture_manifest("archive-readonly",SOURCE)}
fn parsed(bytes:&[u8])->Result<Archive,operation_engine::ManifestArchiveError>{Archive::from_canonical_json(bytes,Sha256::digest(bytes).into())}
fn precommit(m:&ExecutionManifest)->Result<Vec<u8>,Box<dyn Error>>{
    let root=tempfile::tempdir()?;let mut tx=WorkspaceTransaction::create(&root.path().join("workspace"),m.clone(),Default::default())?;let mut saved=None;
    let mut callback=|r:&RevisionCommitRequest|match r.canonical_json(){Ok(bytes)=>{saved=Some(bytes);RevisionCasOutcome::Committed},Err(_)=>RevisionCasOutcome::Failed};
    tx.execute_bytes(SOURCE,OUTPUT,&mut |_:&[u8]|ValidationOutcome::Valid,&mut callback,&mut FaultPlan::none())?;
    saved.ok_or_else(||"engine precommit missing".into())
}
#[test]fn capture_preserves_exact_original_bytes_and_redacts_debug()->TestResult{
    let m=original()?;let archive=Archive::capture(&m)?;
    assert_eq!(archive.canonical_json(),m.canonical_json()?);assert_eq!(archive.canonical_sha256(),m.canonical_sha256()?);
    assert_eq!(archive.expected_source_sha256(),m.expected_source_sha256());assert_eq!(archive.source_artifact_id(),m.source_artifact_id());
    assert_eq!(archive.base_revision(),m.base_revision());assert_eq!(archive.compiled_plan_sha256(),m.compiled_plan_sha256());
    assert_eq!(format!("{archive:?}"),"ArchivedExecutionManifest(<redacted>; historical_data_not_execution_authority)");Ok(())
}
#[test]fn exact_hash_and_size_are_required_before_decoding()->TestResult{
    let raw=original()?.canonical_json()?;assert!(Archive::from_canonical_json(&raw,[0;32]).is_err());
    assert!(Archive::from_canonical_json(&raw,[1;32]).is_err());assert!(parsed(&[]).is_err());assert!(parsed(&vec![b' ';16385]).is_err());Ok(())
}
#[test]fn malformed_versions_ids_hashes_and_counts_never_become_archive_data()->TestResult{
    let raw=original()?.canonical_json()?;let good:serde_json::Value=serde_json::from_slice(&raw)?;
    for(key,bad)in[("schema_version",serde_json::json!("future/v2")),("transaction_id",serde_json::json!("")),("plan_id",serde_json::json!("a\n")),
        ("expected_source_size",serde_json::json!(0)),("route_count",serde_json::json!(0)),("registry_sequence",serde_json::json!(0)),
        ("route_set_sha256",serde_json::json!(vec![0;32]))]{let mut value=good.clone();value[key]=bad;assert!(parsed(&serde_json::to_vec(&value)?).is_err());}Ok(())
}
#[test]fn duplicate_unknown_trailing_and_noncanonical_archive_json_are_rejected()->TestResult{
    let raw=String::from_utf8(original()?.canonical_json()?)?;
    for bytes in[raw.replacen('{',"{\"extra\":0,",1),raw.replacen('{',"{\"schema_version\":\"duplicate\",",1),format!("{raw} {{}}"),format!(" {raw}")]{assert!(parsed(bytes.as_bytes()).is_err());}Ok(())
}
#[test]fn exact_actual_engine_precommit_matches_historical_data_without_execution_conversion()->TestResult{
    let m=original()?;let archive=Archive::capture(&m)?;archive.verify_precommit(&precommit(&m)?,Sha256::digest(OUTPUT).into(),OUTPUT.len()as u64)?;Ok(())
}
#[test]fn precommit_from_a_different_manifest_or_result_is_rejected()->TestResult{
    let m=original()?;let raw=precommit(&m)?;let other=fixture_manifest("another-archive-transaction",SOURCE)?;let archive=Archive::capture(&other)?;
    assert!(archive.verify_precommit(&raw,Sha256::digest(OUTPUT).into(),OUTPUT.len()as u64).is_err());
    let archive=Archive::capture(&m)?;assert!(archive.verify_precommit(&raw,[8;32],OUTPUT.len()as u64).is_err());
    assert!(archive.verify_precommit(&raw,Sha256::digest(OUTPUT).into(),0).is_err());Ok(())
}
#[test]fn precommit_content_id_and_source_identity_cannot_be_substituted()->TestResult{
    let m=original()?;let raw=precommit(&m)?;let archive=Archive::capture(&m)?;let original:serde_json::Value=serde_json::from_slice(&raw)?;
    for key in["result_artifact_id","source_artifact_id","base_revision","transaction_id"]{let mut value=original.clone();value[key]=serde_json::json!("different-valid-identity");
        assert!(archive.verify_precommit(&serde_json::to_vec(&value)?,Sha256::digest(OUTPUT).into(),OUTPUT.len()as u64).is_err());}Ok(())
}
#[test]fn precommit_duplicate_unknown_and_oversize_payloads_are_rejected()->TestResult{
    let m=original()?;let archive=Archive::capture(&m)?;let text=String::from_utf8(precommit(&m)?)?;
    for raw in[text.replacen('{',"{\"extra\":true,",1).into_bytes(),text.replacen('{',"{\"result_size\":1,",1).into_bytes(),vec![b' ';16385]]{
        assert!(archive.verify_precommit(&raw,Sha256::digest(OUTPUT).into(),OUTPUT.len()as u64).is_err());}Ok(())
}
