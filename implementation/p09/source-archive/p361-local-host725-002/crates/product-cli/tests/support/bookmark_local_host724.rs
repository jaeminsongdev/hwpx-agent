//! Actual daemon wire and product/file APIs; repository/scanner/keys/commits are fixtures.
use super::*;
use local_companion_daemon::{LocalCompanionConfig, LocalCompanionDaemon, SessionToken,
    CONFIG_VERSION,TARGET_PROFILE,WORKFLOW_PROTOCOL_VERSION,DaemonError,
    bookmark_preview722::{BOOKMARK_PREVIEW_PROTOCOL,BookmarkPreviewRuntime,BookmarkWorkspaceContext,BookmarkPreviewMetadata}};
use hwpx_agent_cli::form_product_request::stored_operations::bookmark_insertion710::local_host723::CurrentBookmarkPreviewHost;
use std::{cell::Cell,path::PathBuf};
const TOKEN:&str="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
#[path="../../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]mod native;
fn token()->Result<SessionToken>{Ok(SessionToken::new(TOKEN.to_owned())?)}
fn config(root:&Path,source:&[u8])->Result<LocalCompanionConfig>{
    for name in["main","other"]{
        let w=root.join(name);std::fs::create_dir_all(w.join("input"))?;std::fs::create_dir(w.join("output"))?;
        std::fs::write(w.join("input/source.hwpx"),source)?;
        local_workflow::LocalWorkflow::open(&w,4194304)?.materialize("op_01",local_workflow::MaterializeSlot::Source,
            "input/source.hwpx",&Sha256::digest(source).into())?;
    }
    write_config(root,4194304)
}
fn write_config(root:&Path,max:u64)->Result<LocalCompanionConfig>{
    let path=root.join("config.json");
    std::fs::write(&path,serde_json::to_vec(&json!({"schema_version":CONFIG_VERSION,"target_profile":TARGET_PROFILE,
        "automation_mode":"disabled","network_mode":"disabled","max_file_bytes":max,
        "workspaces":[{"id":"main","root":root.join("main")},{"id":"other","root":root.join("other")}]}))?)?;
    Ok(LocalCompanionConfig::load(&path)?)
}
fn raw(s:&StoredFixture,p:&Provider<'_>)->Result<String>{
    let source=p.import_actual_forms(s.head,4)?;let(run,target)=selection(&source)?;
    raw_selected(s,&source,run,target)
}
fn raw_selected(s:&StoredFixture,source:&StoredImportedDocumentForms,run:SourceAnchorHandle,target:LogicalId)->Result<String>{
    Ok(json!({"schema_version":"hwpx-agent.product-bookmark-insertion-request/v1","idempotency_key":"host724-key",
        "project_id":s.project.public_id(),"document_id":DOC,"base_revision":s.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation":s.head.generation(),"expected_source_package_sha256":hex::encode(source.receipt().imported.source_package_sha256),
        "plan_id":"host724-plan","operation":{"kind":"insert_bookmark_crossref","run":run,"target_id":target,
            "display":"bookmark_name","hyperlink":false}}).to_string())
}
fn wire(raw:&str)->Value{json!({"protocol_version":BOOKMARK_PREVIEW_PROTOCOL,"request_id":"request724",
    "session_token":TOKEN,"method":"stage_bookmark_preview","params":{"workspace_id":"main","operation_id":"op_01","product_request_json":raw}})}
fn preview(root:&Path,w:&str)->PathBuf{root.join(w).join(".hwpx-agent/work/op_01/generated-preview.hwpx")}
fn call(d:&LocalCompanionDaemon,v:&Value,h:&dyn BookmarkPreviewRuntime)->Result<Value>{
    Ok(d.handle_with_bookmark_runtime(&serde_json::to_vec(v)?,&token()?,h))
}
fn unchanged(s:&StoredFixture,root:&Path)->Result{
    require(!preview(root,"main").exists()&&!preview(root,"other").exists()
        &&std::fs::read_dir(root.join("main/output"))?.count()==0
        &&s.revisions.head(&s.revision_context,s.project,s.branch)?==s.head)
}
#[test]
fn authenticated_wire_uses_configured_workspace_and_current_product_without_publication()->Result{
    let manifest:Value=serde_json::from_str(include_str!("../../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json"))?;
    let bytes=read_pin(&manifest["source"])?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let temp=tempfile::tempdir()?;let config=config(temp.path(),&bytes)?;
    let host=CurrentBookmarkPreviewHost::bind(&p,config.bookmark_preview_binding("main")?);let d=LocalCompanionDaemon::new(config);
    let source=p.import_actual_forms(s.head,4)?;let(run,target)=native::select(source.imported(),&bytes)?;
    let result=call(&d,&wire(&raw_selected(&s,&source,run,target)?),&host)?;require(result["ok"]==true)?;
    let m=&result["result"];let output=std::fs::read(preview(temp.path(),"main"))?;
    require(m["preview_package_sha256"]==hex::encode(Sha256::digest(&output))&&m["preview_bytes"]==output.len()as u64
        &&m["preview_package_sha256"]==manifest["cases"][2]["stages"]["candidate"]["pin"]["sha256"]
        &&m["private_preview_only"]==true&&m["public_output_or_revision_adoption_authority"]==false
        &&!preview(temp.path(),"other").exists()&&std::fs::read_dir(temp.path().join("main/output"))?.count()==0
        &&s.revisions.head(&s.revision_context,s.project,s.branch)?==s.head)?;
    let text=result.to_string();for secret in[TOKEN,"private-display","private-target","<hp:",temp.path().to_str().ok_or("path")?]{require(!text.contains(secret))?;}
    Ok(())
}
struct Spy(Cell<u32>);
impl BookmarkPreviewRuntime for Spy{
    fn stage(&self,_:&BookmarkWorkspaceContext<'_>,_:&[u8],_:u64)->std::result::Result<BookmarkPreviewMetadata,DaemonError>{
        self.0.set(self.0.get()+1);Err(DaemonError::Request)
    }
}
#[test]
fn default_off_wrong_session_unknown_workspace_and_old_protocol_never_reach_runtime()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let t=tempfile::tempdir()?;
    let d=LocalCompanionDaemon::new(config(t.path(),&bytes)?);let spy=Spy(Cell::new(0));let request=wire("{}");
    require(d.handle(&serde_json::to_vec(&request)?,&token()?)["ok"]==false)?;
    let mut value=request.clone();value["session_token"]=json!("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB");
    require(call(&d,&value,&spy)?["ok"]==false)?;
    let mut value=request.clone();value["params"]["workspace_id"]=json!("unknown");require(call(&d,&value,&spy)?["ok"]==false)?;
    let mut value=request;value["protocol_version"]=json!(WORKFLOW_PROTOCOL_VERSION);require(call(&d,&value,&spy)?["ok"]==false)?;
    require(spy.0.get()==0)?;unchanged(&s,t.path())
}
#[test]
fn duplicate_unknown_oversized_and_path_parameters_fail_before_runtime()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let t=tempfile::tempdir()?;
    let d=LocalCompanionDaemon::new(config(t.path(),&bytes)?);let spy=Spy(Cell::new(0));let request=wire("{}");
    for (key,value) in[("path",json!("input/source.hwpx")),("generated_bytes",json!("secret")),("permit",json!(true))]{
        let mut v=request.clone();v["params"][key]=value;require(call(&d,&v,&spy)?["ok"]==false)?;
    }
    let mut v=request.clone();v["params"]["operation_id"]=json!("../escape");require(call(&d,&v,&spy)?["ok"]==false)?;
    let mut v=request.clone();v["params"]["product_request_json"]=json!("x".repeat(17000));require(call(&d,&v,&spy)?["ok"]==false)?;
    let encoded=request.to_string().replace("\"workspace_id\":\"main\"","\"workspace_id\":\"other\",\"workspace_id\":\"main\"");
    require(encoded!=request.to_string()&&d.handle_with_bookmark_runtime(encoded.as_bytes(),&token()?,&spy)["ok"]==false&&spy.0.get()==0)?;
    unchanged(&s,t.path())
}
#[test]
fn workspace_and_config_substitution_cannot_reuse_provider_binding()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let t=tempfile::tempdir()?;let config=config(t.path(),&bytes)?;let host=CurrentBookmarkPreviewHost::bind(&p,config.bookmark_preview_binding("main")?);
    let d=LocalCompanionDaemon::new(config);let mut v=wire(&raw(&s,&p)?);let audits=s.metadata.audit_events()?.len();
    v["params"]["workspace_id"]=json!("other");require(call(&d,&v,&host)?["ok"]==false)?;
    let changed=LocalCompanionDaemon::new(write_config(t.path(),4194303)?);
    v["params"]["workspace_id"]=json!("main");require(call(&changed,&v,&host)?["ok"]==false&&s.metadata.audit_events()?.len()==audits)?;
    unchanged(&s,t.path())
}
#[test]
fn nested_product_duplicates_raw_xml_and_document_spoof_are_rejected()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let t=tempfile::tempdir()?;let config=config(t.path(),&bytes)?;let host=CurrentBookmarkPreviewHost::bind(&p,config.bookmark_preview_binding("main")?);
    let d=LocalCompanionDaemon::new(config);let raw=raw(&s,&p)?;
    let duplicated=raw.replace("\"hyperlink\":false","\"hyperlink\":true,\"hyperlink\":false");require(duplicated!=raw)?;
    let mut xml:Value=serde_json::from_str(&raw)?;xml["operation"]["xml"]=json!("<hp:run/>");
    let mut foreign:Value=serde_json::from_str(&raw)?;foreign["document_id"]=json!("foreign-document");
    for input in[duplicated,xml.to_string(),foreign.to_string()]{require(call(&d,&wire(&input),&host)?["ok"]==false)?;}
    unchanged(&s,t.path())
}
#[test]
fn revoked_acl_tampered_source_and_changed_head_never_create_preview()->Result{
    for mode in["acl","aead","head"]{
        let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
        let t=tempfile::tempdir()?;let config=config(t.path(),&bytes)?;let host=CurrentBookmarkPreviewHost::bind(&p,config.bookmark_preview_binding("main")?);
        let d=LocalCompanionDaemon::new(config);let v=wire(&raw(&s,&p)?);
        match mode{
            "acl"=>s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?,
            "aead"=>s.blobs.tamper.store(true,Ordering::SeqCst),
            _=>advance(&s)?,
        }
        require(call(&d,&v,&host)?["ok"]==false&&!preview(t.path(),"main").exists())?;
    }Ok(())
}
#[test]
fn successful_private_wire_is_create_new_and_repeat_does_not_adopt_or_overwrite()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let t=tempfile::tempdir()?;let config=config(t.path(),&bytes)?;let host=CurrentBookmarkPreviewHost::bind(&p,config.bookmark_preview_binding("main")?);
    let d=LocalCompanionDaemon::new(config);let v=wire(&raw(&s,&p)?);require(call(&d,&v,&host)?["ok"]==true)?;
    let saved=std::fs::read(preview(t.path(),"main"))?;require(call(&d,&v,&host)?["ok"]==false
        &&std::fs::read(preview(t.path(),"main"))?==saved&&std::fs::read_dir(t.path().join("main/output"))?.count()==0
        &&s.revisions.head(&s.revision_context,s.project,s.branch)?==s.head)?;Ok(())
}
#[test]
fn authenticated_source_must_match_managed_workspace_source()->Result{
    let bytes=sample()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let ctx=write_context(&s);let p=provider(&s,&ctx)?;
    let t=tempfile::tempdir()?;let config=config(t.path(),b"wrong managed source")?;
    let host=CurrentBookmarkPreviewHost::bind(&p,config.bookmark_preview_binding("main")?);let d=LocalCompanionDaemon::new(config);
    require(call(&d,&wire(&raw(&s,&p)?),&host)?["ok"]==false)?;unchanged(&s,t.path())
}
