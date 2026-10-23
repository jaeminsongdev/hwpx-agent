// Original strict request -> private deterministic job binding. No product execution authority.
use super::*;
use hwpx_agent_cli::stored_revision_commit::job::identity::{StoredRequestJobIdentity,StoredJobPolicy};
fn identity(p:&Provider<'_>,f:&Feed,v:&Value)->Result<StoredRequestJobIdentity,Box<dyn Error>>{
    let out=manifest(p,f,v)?;let(c,r)=route(6,0)?;Ok(out.with_verified_storage_preparation(p,f,&c,&r,6,|s|s.job_identity().clone())?)
}
#[test]
fn original_request_controls_all_three_ids_and_claim_content()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(c,r)=route(6,0)?;out.with_verified_storage_preparation(&p,&f,&c,&r,6,|input|->R{
        let prepared=input.prepare_bound_job(Default::default(),rev::CommitId::generate(),rev::RevisionId::generate(),Default::default())?;
        let i=prepared.claim().input();let bound=input.job_identity();assert_eq!((i.key,i.job,i.request),(bound.key(),bound.job(),bound.request()));
        assert_ne!(i.key,i.job);assert_ne!(i.job,i.request);assert_ne!(i.request,i.key);
        assert_eq!(i.request_sha.hex(),out.compiled_receipt().canonical_request_sha256);assert_eq!(i.source,s.result);assert_eq!(i.expected_head,s.head);
        assert_eq!(i.capability_sha.as_bytes(),&input.manifest().route_set_sha256());Ok(())
    })??;assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn equivalent_json_and_repeated_preparation_keep_the_same_unclaimed_ids()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;let a=identity(&p,&f,&v)?;
    let pretty:Value=serde_json::from_str(&serde_json::to_string_pretty(&v)?)?;let b=identity(&p,&f,&pretty)?;assert_eq!(a,b);
    let out=compile(&p,&f,&v)?;let(c,r)=route(6,0)?;let out=out.prepare_execution_manifest(&p,&f,&c,&r,tx("different-job-transaction")?,6)?;
    let b=out.with_verified_storage_preparation(&p,&f,&c,&r,6,|i|i.job_identity().clone())?;assert_eq!(a,b);Ok(())
}
#[test]
fn changed_request_does_not_evade_collision_by_getting_new_ids()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;let a=identity(&p,&f,&v)?;
    for change in 0..3{let mut next=v.clone();match change{0=>next["plan_id"]=json!("other-bound-plan"),1=>next["operation"]["max_matches"]=json!(9999),_=>next["operation"]["mask_policy"]=json!("three_asterisks_per_text_group")}
        let b=identity(&p,&f,&next)?;assert_eq!((a.key(),a.job(),a.request()),(b.key(),b.job(),b.request()));assert_ne!(a,b);}Ok(())
}
#[test]
fn new_source_and_revision_with_same_project_key_still_use_original_ids()->R{
    let mut identities=Vec::new();
    for text in ["A MARK","B MARK"]{let bytes=raw(text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");identities.push(identity(&p,&f,&req(&s,&bytes,&f,false)?)?);}
    let a=&identities[0];let b=&identities[1];assert_eq!((a.key(),a.job(),a.request()),(b.key(),b.job(),b.request()));assert_ne!(a,b);Ok(())
}
#[test]
fn changed_key_is_distinct_and_debug_never_reveals_it()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let mut v=req(&s,&bytes,&f,false)?;let a=identity(&p,&f,&v)?;
    v["idempotency_key"]=json!("PRIVATE-OTHER-KEY");let b=identity(&p,&f,&v)?;assert_ne!(a.key(),b.key());assert_ne!(a.job(),b.job());assert_ne!(a.request(),b.request());
    assert_eq!(format!("{b:?}"),"StoredRequestJobIdentity(<redacted>; unclaimed)");Ok(())
}
#[test]
fn original_sql_policy_and_new_revision_limits_are_not_bypassed_by_bound_ids()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(c,r)=route(6,0)?;out.with_verified_storage_preparation(&p,&f,&c,&r,6,|i|->R{
        for mode in 0..4{let mut policy=StoredJobPolicy::default();match mode{0=>policy.max_attempts=0,1=>policy.base_delay_seconds=0,2=>policy.max_delay_seconds=0,_=>policy.ttl_seconds=1}
            assert!(i.prepare_bound_job(policy,rev::CommitId::generate(),rev::RevisionId::generate(),Default::default()).is_err());}
        assert!(i.prepare_bound_job(Default::default(),rev::CommitId::generate(),s.head.revision_id().ok_or("head")?,Default::default()).is_err());Ok(())
    })??;assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
