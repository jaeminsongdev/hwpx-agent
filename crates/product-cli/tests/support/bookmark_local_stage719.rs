//! Real private files + current Artifact/Revision logic, with isolated repository/scanner/key fixtures.
use super::*;
use local_workflow::{LocalWorkflow,MaterializeSlot};
use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductRequest as Entry,
    bookmark_insertion710::{BOOKMARK_INSERTION_PRODUCT_REQUEST_SCHEMA as SCHEMA,PreparedBookmarkInsertionProduct,BookmarkInsertionProductLimits}};
use revision_service::{RevisionRepository,RevisionError,RevisionNode};
use std::path::PathBuf;
#[path="../../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]mod native;
fn request(s:&StoredFixture,source:&StoredImportedDocumentForms,run:SourceAnchorHandle,target:LogicalId,display:&str,link:bool)->Result<Vec<u8>>{
    Ok(serde_json::to_vec(&json!({"schema_version":SCHEMA,"idempotency_key":"local-stage719-key","project_id":s.project.public_id(),
        "document_id":DOC,"base_revision":s.head.revision_id().ok_or("head")?.public_id(),"expected_head_generation":s.head.generation(),
        "expected_source_package_sha256":hex::encode(source.receipt().imported.source_package_sha256),"plan_id":"local-stage719-plan",
        "operation":{"kind":"insert_bookmark_crossref","run":run,"target_id":target,"display":display,"hyperlink":link}}))?)
}
fn raw_request(s:&StoredFixture,p:&Provider<'_>)->Result<Vec<u8>>{
    let source=p.import_actual_forms(s.head,4)?;let(run,target)=selection(&source)?;request(s,&source,run,target,"bookmark_name",false)
}
fn prepare_request(s:&StoredFixture,p:&Provider<'_>)->Result<PreparedBookmarkInsertionProduct>{
    Ok(Entry::prepare_bookmark_insertion_json(p,&raw_request(s,p)?,BookmarkInsertionProductLimits::standard()?,5)?)
}
fn workspace(root:&Path,source:&[u8],operation:&str)->Result<LocalWorkflow>{
    std::fs::create_dir_all(root.join("input"))?;std::fs::create_dir(root.join("output"))?;
    std::fs::write(root.join("input/source.hwpx"),source)?;
    let w=LocalWorkflow::open(root,4194304)?;
    w.materialize(operation,MaterializeSlot::Source,"input/source.hwpx",&Sha256::digest(source).into())?;Ok(w)
}
fn preview(root:&Path,operation:&str)->PathBuf{root.join(".hwpx-agent/work").join(operation).join("generated-preview.hwpx")}
pub(super) fn observation(root:&Path)->Result<Value>{
    const INPUT:&str=include_str!("../../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json");
    let manifest:Value=serde_json::from_str(INPUT)?;let bytes=read_pin(&manifest["source"])?;
    require(!root.exists())?;std::fs::create_dir(root)?;let mut rows=Vec::new();
    for(i,display)in["page","bookmark_name","content","relative_position"].into_iter().enumerate(){for hyperlink in[false,true]{
        let index=i*2+usize::from(hyperlink);let case=&manifest["cases"][index];let directory=root.join(format!("c{:02}",index+1));
        let w=workspace(&directory,&bytes,"op_01")?;
        let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
        let raw={let source=p.import_actual_forms(s.head,4)?;let(run,target)=native::select(source.imported(),&bytes)?;request(&s,&source,run,target,display,hyperlink)?};
        let operation=Entry::prepare_json(&p,&raw,None,5)?;let product=operation.as_bookmark_insertion().ok_or("variant")?;
        let staged=product.stage_private_local_preview(&p,&w,"op_01",6)?;
        let reopened=LocalWorkflow::open(&directory,4194304)?;
        let readback=reopened.inspect_generated_preview("op_01",&staged.source_package_sha256,&staged.preview_package_sha256)?;
        let persisted=std::fs::read(preview(&directory,"op_01"))?;
        require(hex::encode(staged.preview_package_sha256)==case["stages"]["candidate"]["pin"]["sha256"]
            &&hex::encode(Sha256::digest(&persisted))==case["stages"]["candidate"]["pin"]["sha256"]
            &&readback.preview.size_bytes==staged.preview_bytes&&staged.current_source_checked_before_and_after_staging
            &&!staged.publication_execution_or_revision_adoption_authority
            &&reopened.publish("op_01","not-qualified.hwpx",&staged.preview_package_sha256).is_err()
            &&std::fs::read_dir(directory.join("output"))?.count()==0
            &&s.revisions.head(&s.revision_context,s.project,s.branch)?==s.head
            &&s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count()==2)?;
        rows.push(json!({"case_index":index+1,"receipt":staged,"persisted_bytes_exact":true,"workspace_reopened":true,
            "existing_public_publish_cannot_read_preview":true,"source_and_head_unchanged":true}));
    }}
    require(read_pin(&manifest["source"])?==bytes)?;
    Ok(json!({"state":"QUALIFIED719_ACTUAL8_CURRENT_SOURCE_PRIVATE_FILES_STAGED_REOPENED_NOT_PUBLICATION_OR_REVISION",
        "source":manifest["source"],"cases":rows,"fixture_repository_scanner_keys_commits":true,
        "Native_started":false,"result_ingested":false,"revision_adopted":false,"P09_complete":false}))
}
#[test]
fn current_owned_request_stages_exact_disk_preview_and_reopens_without_publication()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let temp=tempfile::tempdir()?;let root=temp.path().join("workspace");let w=workspace(&root,&bytes,"op_01")?;
    let product=prepare_request(&s,&p)?;let staged=product.stage_private_local_preview(&p,&w,"op_01",6)?;
    let output=product.with_verified_bytes(&p,7,|v|v.to_vec())?;
    require(std::fs::read(preview(&root,"op_01"))?==output
        &&LocalWorkflow::open(&root,4194304)?.inspect_generated_preview("op_01",&staged.source_package_sha256,&staged.preview_package_sha256)?.preview.size_bytes==output.len()as u64
        &&!staged.publication_execution_or_revision_adoption_authority&&staged.private_preview_not_publish_candidate
        &&w.publish("op_01","result.hwpx",&staged.preview_package_sha256).is_err()
        &&s.revisions.head(&s.revision_context,s.project,s.branch)?==s.head)?;
    for text in[serde_json::to_string(&staged)?,format!("{staged:?}")]{require(!text.contains("private-display")&&!text.contains("private-target")&&!text.contains("<hp:"))?;}Ok(())
}
#[test]
fn different_managed_source_rejects_before_preview_write()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let temp=tempfile::tempdir()?;let root=temp.path().join("workspace");let w=workspace(&root,b"different managed source","op_01")?;
    require(prepare_request(&s,&p)?.stage_private_local_preview(&p,&w,"op_01",6).is_err()&&!preview(&root,"op_01").exists())
}
#[test]
fn acl_revoke_then_regrant_never_revives_failed_staging()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let temp=tempfile::tempdir()?;let root=temp.path().join("workspace");let w=workspace(&root,&bytes,"op_01")?;let product=prepare_request(&s,&p)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;
    require(product.stage_private_local_preview(&p,&w,"op_01",7).is_err()&&!preview(&root,"op_01").exists())?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),8)?;
    require(product.stage_private_local_preview(&p,&w,"op_01",9).is_err()&&!preview(&root,"op_01").exists())
}
#[test]
fn aead_restoration_never_revives_failed_private_staging()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let temp=tempfile::tempdir()?;let root=temp.path().join("workspace");let w=workspace(&root,&bytes,"op_01")?;let product=prepare_request(&s,&p)?;
    s.blobs.tamper.store(true,Ordering::SeqCst);require(product.stage_private_local_preview(&p,&w,"op_01",6).is_err())?;
    s.blobs.tamper.store(false,Ordering::SeqCst);
    require(product.stage_private_local_preview(&p,&w,"op_01",7).is_err()&&!preview(&root,"op_01").exists())
}
#[test]
fn changed_head_before_io_blocks_private_file_creation()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let temp=tempfile::tempdir()?;let root=temp.path().join("workspace");let w=workspace(&root,&bytes,"op_01")?;let product=prepare_request(&s,&p)?;
    advance(&s)?;require(product.stage_private_local_preview(&p,&w,"op_01",6).is_err()&&!preview(&root,"op_01").exists())
}
struct PostStageHead{inner:InMemoryRevisionRepository,preview:PathBuf,enabled:AtomicBool}
impl RevisionRepository for PostStageHead{
    fn authorize_context(&self,c:&RevisionRequestContext)->Result<(),RevisionError>{self.inner.authorize_context(c)}
    fn head(&self,t:TenantId,p:revision_service::ProjectId,b:BranchId)->Result<RevisionHead,RevisionError>{
        let h=self.inner.head(t,p,b)?;
        if self.enabled.load(Ordering::SeqCst)&&self.preview.exists(){RevisionHead::new(h.revision_id(),h.generation()+1)}else{Ok(h)}
    }
    fn node(&self,t:TenantId,p:revision_service::ProjectId,r:revision_service::RevisionId)->Result<RevisionNode,RevisionError>{self.inner.node(t,p,r)}
    fn compare_and_swap(&self,_:&RevisionRequestContext,_:&RevisionCommitRequest)->Result<CommitOutcome,RevisionError>{Err(RevisionError::InvalidRequest)}
}
#[test]
fn head_change_after_file_write_denies_receipt_and_leaves_unqualified_evidence_only()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);
    let temp=tempfile::tempdir()?;let root=temp.path().join("workspace");let w=workspace(&root,&bytes,"op_01")?;
    let revisions=RevisionService::new(PostStageHead{inner:s.revisions.repository().clone(),preview:preview(&root,"op_01"),enabled:AtomicBool::new(true)});
    let p=StoredFormProvider::bind(&s.artifacts,&revisions,&ctx,&s.revision_context,s.project,s.branch,DocumentId::parse(DOC)?)?;
    let source=p.import_actual_forms(s.head,4)?;let(run,target)=selection(&source)?;let raw=request(&s,&source,run,target,"bookmark_name",false)?;
    let product=Entry::prepare_bookmark_insertion_json(&p,&raw,BookmarkInsertionProductLimits::standard()?,5)?;
    let sha=product.receipt().compiled.output_package_sha256;
    require(product.stage_private_local_preview(&p,&w,"op_01",6).is_err()&&preview(&root,"op_01").is_file()
        &&w.publish("op_01","result.hwpx",&sha).is_err()&&std::fs::read_dir(root.join("output"))?.count()==0)?;
    revisions.repository().enabled.store(false,Ordering::SeqCst);
    require(product.stage_private_local_preview(&p,&w,"op_01",7).is_err())
}
#[test]
fn foreign_provider_document_cannot_enter_private_workspace_writer()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let temp=tempfile::tempdir()?;let root=temp.path().join("workspace");let w=workspace(&root,&bytes,"op_01")?;let product=prepare_request(&s,&p)?;
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&ctx,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign719")?)?;
    require(product.stage_private_local_preview(&other,&w,"op_01",6).is_err()&&!preview(&root,"op_01").exists())
}
