//! Original compiler and real service guards with isolated memory/scanner/key fixtures.
use super::*;
use domain_ir::{CanonicalArgumentValue,CompiledOperationPlan,OperationPlanLimits,PlanId};
use hwpx_agent_cli::form_stored_provider::actual_import::bookmark_insertion_output::compiled707::{
    BookmarkInsertionCompileError as C,BOOKMARK_INSERTION_CAPABILITY};
#[path="../../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]
mod native;
fn plan_id()->Result<PlanId>{Ok(PlanId::parse("bookmark-first-insertion708")?)}
fn text<'a>(plan:&'a CompiledOperationPlan,key:&str)->Result<&'a str>{
    match plan.operations()[0].arguments().get(key).ok_or("argument")?.value(){
        CanonicalArgumentValue::Text(value)=>Ok(value),_=>Err("argument kind".into())}
}
fn unchanged(s:&StoredFixture,raw:&[u8])->Result{
    require(s.revisions.head(&s.revision_context,s.project,s.branch)?==s.head
        &&s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count()==2
        &&s.artifacts.download(&s.owner,s.result,20)?==raw)
}
pub(super) fn observation()->Result<Value>{
    const INPUT:&str=include_str!("../../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json");
    let input:Value=serde_json::from_str(INPUT)?;let raw=read_pin(&input["source"])?;
    require(input["cases"].as_array().ok_or("cases")?.len()==8)?;let mut rows=Vec::new();
    for(i,display)in[Display::Page,Display::BookmarkName,Display::Content,Display::RelativePosition].into_iter().enumerate(){
        for hyperlink in[false,true]{
            let index=i*2+usize::from(hyperlink);let expected=&input["cases"][index];
            let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
            let source=p.import_actual_forms(s.head,4)?;let(run,target)=native::select(source.imported(),&raw)?;
            let candidate=source.into_bookmark_insertion_candidate(&p,Request{run:&run,target_id:&target,display,hyperlink},limits()?,WriterLimits::default(),5)?;
            let original=candidate.receipt().output.clone();let c=candidate.compile(&p,plan_id()?,6)?;
            let out=c.with_verified_bytes(&p,7,|bytes|bytes.to_vec())?;
            require(hex::encode(Sha256::digest(&out))==expected["stages"]["candidate"]["pin"]["sha256"]
                &&hex::encode(original.command_sha256)==expected["stages"]["candidate"]["command_sha256"]
                &&c.receipt().compiled_plan_sha256==c.compiled().canonical_sha256()?
                &&text(c.compiled(),"selected_target_id_sha256")?==hex::encode(Sha256::digest(target.as_str().as_bytes()))
                &&text(c.compiled(),"source_run_anchor_json")?==serde_json::to_string(&run)?)?;
            let restored=CompiledOperationPlan::from_canonical_json(&c.compiled().canonical_json()?,OperationPlanLimits::default())?;
            require(restored==*c.compiled()&&c.verify(&p,8)?==c.receipt())?;
            require(matches!(c.require_current_product_route(&p,9),Err(C::Stored(E::RouteUnqualified))))?;
            c.verify(&p,10)?;unchanged(&s,&raw)?;
            rows.push(json!({"case_index":index+1,"output_sha256":hex::encode(Sha256::digest(&out)),"compiled_receipt":c.receipt(),
                "source_and_output_exact":true,"plan_reopened":true,"route_qualified":false}));
        }
    }
    require(read_pin(&input["source"])?==raw)?;
    Ok(json!({"state":"QUALIFIED708_ACTUAL_BLOCK_EIGHT_ORIGINAL_COMPILER_CURRENT_STORED_SOURCE_NOT_EXECUTION",
        "source":input["source"],"cases":rows,"memory_repository_scanner_keys_and_commits_are_fixtures":true,
        "Native_started":false,"head_changed":false,"result_ingested":false,"P09_complete":false}))
}
#[test]
fn first_insertion_plan_binds_original_plain_run_owner_target_revision_output_and_receipt()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let source=p.import_actual_forms(s.head,4)?;let(run,target)=selection(&source)?;
    let graph_sha=source.imported().graph().canonical_sha256()?;
    let owner=source.imported().graph().sections()[0].body.children.get(1).ok_or("second paragraph")?.common().node_id.clone();
    let candidate=source.into_bookmark_insertion_candidate(&p,Request{run:&run,target_id:&target,display:Display::Page,hyperlink:true},limits()?,WriterLimits::default(),5)?;
    let original=candidate.receipt().clone();let before=candidate.with_verified_bytes(&p,6,|v|v.to_vec())?;
    let c=candidate.compile(&p,plan_id()?,7)?;let plan=c.compiled();
    require(plan.operations().len()==1&&plan.base_graph_sha256()==graph_sha
        &&plan.base_revision().as_str()==s.head.revision_id().ok_or("head")?.public_id()
        &&plan.plan_id()==&plan_id()?&&plan.operations()[0].capability_id().as_str()==BOOKMARK_INSERTION_CAPABILITY
        &&plan.operations()[0].arguments().len()==10
        &&c.receipt().compiled_plan_sha256==plan.canonical_sha256()?
        &&c.receipt().source_artifact==s.result&&c.receipt().head_generation==s.head.generation())?;
    for(key,expected)in[("source_package_sha256",hex::encode(Sha256::digest(&bytes))),
        ("output_package_sha256",hex::encode(original.output.output_package_sha256)),
        ("source_run_sha256",hex::encode(run.fingerprint_sha256)),
        ("source_run_anchor_json",serde_json::to_string(&run)?),
        ("output_command_sha256",hex::encode(original.output.command_sha256)),
        ("selected_target_id_sha256",hex::encode(Sha256::digest(target.as_str().as_bytes())))]{require(text(plan,key)?==expected)?;}
    // The original selector is the actual second paragraph, not the bookmark wrapper.
    require(plan.operations()[0].target().node_id()==&owner)?;
    require(c.with_verified_bytes(&p,8,|v|v.to_vec())?==before
        &&CompiledOperationPlan::from_canonical_json(&plan.canonical_json()?,OperationPlanLimits::default())?==*plan)?;
    for value in[String::from_utf8(plan.canonical_json()?)?,serde_json::to_string(c.receipt())?,format!("{c:?}")]{for secret in["private-target","private-display","原文","<hp:"]{require(!value.contains(secret))?;}}
    require(!c.receipt().execution_or_publication_authority&&c.receipt().display_text_preserved_not_evaluated_or_refreshed)?;
    unchanged(&s,&bytes)
}
#[test]
fn acl_denial_before_compilation_cannot_yield_a_plan()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let c=prepare(p.import_actual_forms(s.head,4)?,&p,Display::Page,false)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;
    require(matches!(c.compile(&p,plan_id()?,7),Err(C::Stored(_))))
}
#[test]
fn compiled_candidate_acl_regrant_cannot_revive_denied_delivery()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let c=prepare(p.import_actual_forms(s.head,4)?,&p,Display::Page,false)?.compile(&p,plan_id()?,6)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),7)?;
    let mut called=false;require(c.with_verified_bytes(&p,8,|_|called=true).is_err()&&!called)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),9)?;
    require(matches!(c.with_verified_bytes(&p,10,|_|called=true),Err(C::Stored(E::PreviouslyDenied)))&&!called)
}
#[test]
fn compiled_candidate_head_advance_blocks_consumer_and_stays_denied()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let c=prepare(p.import_actual_forms(s.head,4)?,&p,Display::RelativePosition,false)?.compile(&p,plan_id()?,6)?;
    advance(&s)?;let mut called=false;require(c.with_verified_bytes(&p,7,|_|called=true).is_err()&&!called)?;
    require(matches!(c.verify(&p,8),Err(C::Stored(E::PreviouslyDenied))))
}
#[test]
fn compiled_candidate_aead_restoration_cannot_revive_failed_delivery()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let c=prepare(p.import_actual_forms(s.head,4)?,&p,Display::BookmarkName,true)?.compile(&p,plan_id()?,6)?;
    s.blobs.tamper.store(true,Ordering::SeqCst);let mut called=false;require(c.with_verified_bytes(&p,7,|_|called=true).is_err()&&!called)?;
    s.blobs.tamper.store(false,Ordering::SeqCst);require(matches!(c.verify(&p,8),Err(C::Stored(E::PreviouslyDenied))))
}
#[test]
fn foreign_document_provider_is_not_a_compiler_or_output_authority()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&ctx,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign708")?)?;
    let c=prepare(p.import_actual_forms(s.head,4)?,&p,Display::Page,false)?;
    require(matches!(c.compile(&other,plan_id()?,6),Err(C::Stored(_))))?;
    let c=prepare(p.import_actual_forms(s.head,4)?,&p,Display::Page,false)?.compile(&p,plan_id()?,6)?;
    let mut called=false;require(c.with_verified_bytes(&other,7,|_|called=true).is_err()&&!called)
}
#[test]
fn compiled_insertion_route_denial_is_not_native_registry_claim_or_source_poison()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let c=prepare(p.import_actual_forms(s.head,4)?,&p,Display::BookmarkName,false)?.compile(&p,plan_id()?,6)?;
    require(matches!(c.require_current_product_route(&p,7),Err(C::Stored(E::RouteUnqualified))))?;
    c.verify(&p,8)?;unchanged(&s,&bytes)
}
