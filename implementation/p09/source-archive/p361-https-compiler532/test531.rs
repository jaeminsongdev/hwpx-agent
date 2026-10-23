use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::https_target_output::compiled::{HttpsTargetCompileError as C,HTTPS_EDIT_CAPABILITY};
use domain_ir::{CanonicalArgumentValue,CompiledOperationPlan,OperationPlanLimits,PlanId};
fn plan()->Result<PlanId,Box<dyn Error>>{Ok(PlanId::parse("https-current-compiler")?)}
fn text<'a>(op:&'a domain_ir::CompiledOperation,key:&str)->Result<&'a str,Box<dyn Error>>{
    let value=op.arguments().get(key).ok_or("argument")?.value();
    if let CanonicalArgumentValue::Text(value)=value{Ok(value)}else{Err("text argument".into())}
}
#[test]
fn captured_candidate_uses_original_compiler_owner_and_hash_only_arguments_without_publication()->TestResult{
    let bytes=fixture::captured()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;
    let source=provider.import_actual_forms(f.head,9)?;let t=target("https://example.org/compiled?x=1&y=2");let s=selections(&bytes)?;let repository=repo(&f,&source,&policy(&[&t])?)?;
    let candidate=source.prepare_https_target_candidate(&provider,&repository,&[request(&s[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10)?;
    let output_digest=candidate.receipt().output.output_package_sha256;
    let compiled=candidate.compile(&provider,&repository,plan()?,11)?;
    assert_eq!(compiled.compiled().plan_id(),&plan()?);assert_eq!(compiled.compiled().operations().len(),1);
    assert_eq!(compiled.receipt().compiled_plan_sha256,compiled.compiled().canonical_sha256()?);
    assert_eq!(compiled.compiled().base_graph_sha256(),source.imported().graph().canonical_sha256()?);
    assert_eq!(compiled.compiled().base_revision().as_str(),f.head.revision_id().ok_or("head")?.public_id());
    let op=&compiled.compiled().operations()[0];assert_eq!(op.capability_id().as_str(),HTTPS_EDIT_CAPABILITY);
    let owner=source.imported().graph().sections().iter().flat_map(|s|s.body.children.iter()).find(|n|&n.common().node_id==op.target().node_id()).ok_or("actual graph owner")?;
    assert!(owner.common().source_anchor.is_some());assert_eq!(text(op,"source_reference_id")?,s[0].reference_id.as_str());
    assert_eq!(text(op,"output_target_sha256")?,t.external_approval_sha256(target_limits()?)?);
    assert_eq!(text(op,"source_field_sha256")?,hex::encode(s[0].source_field_sha256));
    let canonical=compiled.compiled().canonical_json()?;
    let restored=CompiledOperationPlan::from_canonical_json(&canonical,OperationPlanLimits::default())?;assert_eq!(restored,*compiled.compiled());
    for value in [String::from_utf8(canonical)?,serde_json::to_string(compiled.receipt())?,format!("{compiled:?}")]{assert!(!value.contains("https://")&&!value.contains("PRIVATE"));}
    assert_eq!(compiled.verify(&provider,&repository,12)?,compiled.receipt());
    let output=compiled.with_verified_bytes(&provider,&repository,13,|b|b.to_vec())?;
    assert_eq!(<[u8;32]>::from(Sha256::digest(&output)),output_digest);
    assert_eq!(output_uris(&output,"actual-form-document")?,vec![Some("https://example.org/compiled?x=1&y=2".into())]);
    assert!(matches!(compiled.require_current_product_route(&provider,&repository,14),Err(C::Stored(E::RouteUnqualified))));
    assert!(!compiled.receipt().execution_or_publication_authority);
    assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?,f.head);
    assert_eq!(f.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),3);Ok(())
}
fn run(id:u32,uri:&str)->Result<String,Box<dyn Error>>{
    let p=link(id,uri);Ok(p.split_once('>').ok_or("paragraph")?.1.strip_suffix("</hp:p>").ok_or("paragraph end")?.into())
}
#[test]
fn reordered_fields_resolve_actual_same_and_distinct_paragraph_owners_without_deduplication()->TestResult{
    let bytes=fixture::package(&format!("<hp:p id='1'>{}{}</hp:p>{}",run(1,"https://example.org/one")?,run(2,"https://example.org/two")?,link(3,"https://example.org/three")))?;
    let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;
    let s=selections(&bytes)?;let a=target("https://example.org/a");let b=target("https://example.org/b");let d=target("https://example.org/d");
    let repository=repo(&f,&source,&policy(&[&a,&b,&d])?)?;let requests=[request(&s[2],&d),request(&s[0],&a),request(&s[1],&b)];
    let compiled=source.prepare_https_target_candidate(&provider,&repository,&requests,limits()?,target_limits()?,WriterLimits::default(),10)?.compile(&provider,&repository,plan()?,11)?;
    let ops=compiled.compiled().operations();assert_eq!(ops.len(),3);
    let nodes=&source.imported().graph().sections()[0].body.children;
    assert_eq!(ops[0].target().node_id(),&nodes[1].common().node_id);assert_eq!(ops[1].target().node_id(),&nodes[0].common().node_id);assert_eq!(ops[2].target().node_id(),&nodes[0].common().node_id);
    for(op,selection)in ops.iter().zip([&s[2],&s[0],&s[1]]){assert_eq!(text(op,"source_reference_id")?,selection.reference_id.as_str());assert!(op.depends_on().is_empty());}
    let bytes=compiled.with_verified_bytes(&provider,&repository,12,|b|b.to_vec())?;
    assert_eq!(output_uris(&bytes,"actual-form-document")?,vec![Some("https://example.org/a".into()),Some("https://example.org/b".into()),Some("https://example.org/d".into())]);Ok(())
}
#[test]
fn revoked_policy_or_source_write_scope_prevents_compilation()->TestResult{
    for i in 0..3{let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
        let c=write_context(&f);let provider=writable(&f,&c)?;let read=f.provider()?;let source=provider.import_actual_forms(f.head,9)?;
        let s=selections(&bytes)?;let t=target("https://example.org/new");let repository=repo(&f,&source,&policy(&[&t])?)?;
        let candidate=source.prepare_https_target_candidate(&provider,&repository,&[request(&s[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10)?;
        match i{0=>repository.deny_after.store(0,Ordering::SeqCst),1=>{f.artifacts.set_permissions(&f.owner,f.result,f.reader.subject(),BTreeSet::new(),11)?;},_=>{}}
        assert!(matches!(candidate.compile(if i==2{&read}else{&provider},&repository,plan()?,12),Err(C::Stored(_))));
    }Ok(())
}
#[test]
fn compiled_delivery_rechecks_current_policy_both_acls_and_write_scope_before_consumer()->TestResult{
    for i in 0..4{let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
        let c=write_context(&f);let provider=writable(&f,&c)?;let read=f.provider()?;let source=provider.import_actual_forms(f.head,9)?;
        let s=selections(&bytes)?;let t=target("https://example.org/new");let repository=repo(&f,&source,&policy(&[&t])?)?;
        let compiled=source.prepare_https_target_candidate(&provider,&repository,&[request(&s[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10)?.compile(&provider,&repository,plan()?,11)?;
        match i{0=>repository.row.lock().map_err(|_|"row")?.binding.policy_generation+=1,
            1=>{f.artifacts.set_permissions(&f.owner,repository.row.lock().map_err(|_|"row")?.artifact,f.reader.subject(),BTreeSet::new(),12)?;},
            2=>{f.artifacts.set_permissions(&f.owner,f.result,f.reader.subject(),BTreeSet::new(),12)?;},_=>{}}
        let mut consumed=false;assert!(matches!(compiled.with_verified_bytes(if i==3{&read}else{&provider},&repository,13,|_|consumed=true),Err(C::Stored(_))));assert!(!consumed);
    }Ok(())
}
#[test]
fn policy_change_after_compilation_body_prevents_returning_a_compiled_candidate()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
    let c=write_context(&f);let provider=writable(&f,&c)?;let source=provider.import_actual_forms(f.head,9)?;let s=selections(&bytes)?;
    let t=target("https://example.org/new");let repository=repo(&f,&source,&policy(&[&t])?)?;
    let candidate=source.prepare_https_target_candidate(&provider,&repository,&[request(&s[0],&t)],limits()?,target_limits()?,WriterLimits::default(),10)?;
    repository.calls.store(0,Ordering::SeqCst);repository.deny_after.store(3,Ordering::SeqCst);
    // Original delivery reads 0/1/2; the compiler's final current-policy check is read 3.
    assert!(matches!(candidate.compile(&provider,&repository,plan()?,11),Err(C::Stored(E::Repository))));
    assert_eq!(repository.calls.load(Ordering::SeqCst),4);assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?,f.head);Ok(())
}
