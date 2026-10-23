//! All16 original product families compiled against actual source-owner selectors, never route authority.
use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::{PreparedCompiledSearchMutation as Compiled,CompiledSearchError as CE};
use domain_ir::{CanonicalArgumentValue,Node,NodeCommon,Selector,SelectorLimits,SelectorSnapshot};
fn arg<'a>(op:&'a domain_ir::CompiledOperation,key:&str)->Result<&'a str,Box<dyn Error>>{
    match op.arguments().get(key).ok_or("argument")?.value(){CanonicalArgumentValue::Text(s)=>Ok(s),_=>Err("not text".into())}
}
fn nodes(g:&domain_ir::DocumentGraph)->Vec<&NodeCommon>{
    let mut result=Vec::new();let mut flows:Vec<_>=g.sections().iter().map(|s|&s.body).chain(g.notes().iter().map(|n|&n.body)).collect();
    while let Some(flow)=flows.pop(){for n in &flow.children{result.push(n.common());match n{Node::Table(t)=>flows.extend(t.cells.iter().map(|c|&c.body)),Node::Drawing(d)=>flows.push(&d.children),_=>{}}}}
    result
}
fn verify_plan(s:&StoredFixture,p:&Provider<'_>,bytes:&[u8],out:&Compiled)->TestResult{
    let original=p.import_actual_forms(s.head,5)?;let f=original.imported();let graph=f.graph();let all=nodes(graph);let plan=out.compiled();let r=out.verify(p,6)?;
    assert_eq!(r.compiled_plan_sha256,plan.canonical_sha256()?);assert_eq!(r.source_graph_sha256,graph.canonical_sha256()?);
    assert_eq!(r.source_package_sha256,*ContentDigest::of(bytes).as_bytes());assert!(!r.execution_authority);
    assert_eq!(plan.operations().len(),r.source_edit_operations);assert!(!plan.operations().is_empty());let snapshot=SelectorSnapshot::build(graph,r.base_revision.clone(),SelectorLimits::default())?;
    let mut anchors=BTreeSet::new();let mut owners=BTreeSet::new();
    for(n,op)in plan.operations().iter().enumerate(){assert_eq!(op.operation_id().as_str(),format!("source-edit-{n:06}"));assert_eq!(op.capability_id().as_str(),r.capability_id);assert_eq!(op.arguments().len(),12);
        assert_eq!(arg(op,"source_edit_index")?,n.to_string());assert_eq!(arg(op,"request_schema")?,r.request_schema);
        assert_eq!(arg(op,"edit_inventory_sha256")?,hex::encode(r.edit_inventory_sha256));assert_eq!(arg(op,"raw_request_sha256")?,r.raw_request_sha256);
        let anchor:domain_ir::SourceAnchorHandle=serde_json::from_str(arg(op,"source_anchor_json")?)?;assert!(anchors.insert(anchor.opaque_handle.clone()));
        let at=f.source().resolve_anchor(&anchor)?;let part=at.part();let xml=part.xml().ok_or("xml")?;let mut next=at.element_index();let mut nearest=None;
        while let Some(i)=next{let key=part.element_anchor(i).ok_or("anchor")?;let found:Vec<_>=all.iter().filter(|node|node.source_anchor.as_ref()==Some(key)).collect();
            if !found.is_empty(){assert_eq!(found.len(),1);nearest=Some(found[0].node_id.clone());break;}next=xml.elements()[i].parent();}
        assert_eq!(Some(op.target().node_id().clone()),nearest);owners.insert(op.target().node_id());
        let independently_resolved=snapshot.resolve_one(&snapshot.expectation(),&Selector::by_logical_id(op.target().node_id().clone()))?;
        assert_eq!(&independently_resolved,op.target());
    }
    assert_eq!(owners.len(),r.structural_owner_nodes);let output=out.with_verified_bytes(p,6,<[u8]>::to_vec)?;
    assert_eq!(r.output_package_sha256,*ContentDigest::of(&output).as_bytes());assert!(matches!(out.require_current_product_route(p,6),Err(CE::Product(_))));
    assert!(!format!("{out:?}{r:?}").contains("PRIVATE"));assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
macro_rules! compiled_case {($name:ident,$i:literal)=>{#[test] fn $name()->TestResult{
    let bytes=source($i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=req($i,&s,&bytes)?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;drop(v);verify_plan(&s,&p,&bytes,&out)
}}}
compiled_case!(compiled_literal_v1,0);
compiled_case!(compiled_literal_atoms_v2,1);
compiled_case!(compiled_review_literal_v3,2);
compiled_case!(compiled_selector_literal_v4,3);
compiled_case!(compiled_regex_v1,4);
compiled_case!(compiled_regex_insertion_v2,5);
compiled_case!(compiled_character_style_v1,6);
compiled_case!(compiled_text_style_v1,7);
compiled_case!(compiled_paragraph_style_v1,8);
compiled_case!(compiled_unicode_scope_v1,9);
compiled_case!(compiled_unicode_matches_v2,10);
compiled_case!(compiled_case_v1,11);
compiled_case!(compiled_width_v1,12);
compiled_case!(compiled_whitespace_v1,13);
compiled_case!(compiled_text_control_v1,14);
compiled_case!(compiled_number_control_v1,15);
#[test]
fn compiled_entry_rejects_unknown_legacy_and_malformed_each_schema_before_reads()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let before=s.metadata.audit_events()?.len();
    for i in 0..16{let mut v=req(i,&s,&bytes)?;v["operation"]["approved"]=json!(true);assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());}
    for schema in ["hwpx-agent.product-operation-request/v2","hwpx-agent.product-form-request/v1","hwpx-agent.product-operation-request/v999"]{
        let mut v=req(3,&s,&bytes)?;v["schema_version"]=json!(schema);assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn compiled_multiple_changes_resolve_actual_distinct_owners_instead_of_first_paragraph()->TestResult{
    let body=(para(1,"KA")+&para(2,"KB")).replace(" charStyleIDRef='0'","");let bytes=definition::package(&body)?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_compiled_search_json(&p,&wire(&req(3,&s,&bytes)?)?,Limits::standard()?,4)?;
    assert_eq!(out.receipt().source_edit_operations,2);assert_eq!(out.receipt().structural_owner_nodes,2);verify_plan(&s,&p,&bytes,&out)
}
#[test]
fn compiled_review_payload_targets_use_actual_enclosing_source_context_and_exact_anchor()->TestResult{
    for i in [2,3,6,7,8]{let mut body=fixture::body().replace("<hp:run>","<hp:run charPrIDRef='0'>");if i==7{body=body.replace("<hp:t>","<hp:t charStyleIDRef='0'>");}
        for n in [1,11,12]{body=body.replace(&format!("<hp:p id='{n}'>"),&format!("<hp:p id='{n}' paraPrIDRef='0' styleIDRef='0'>"));}
        if i==8{
            use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::paragraph_styles::StoredParagraphStyleError as StoredPara;
            use hwpx_package::document_import::search::replacement::atoms::styles::paragraphs::SourceParagraphStyleReplacementError as CorePara;
            let protected=definition::package(&body)?;let guarded=StoredFixture::new(&protected,ArtifactKind::Result,false)?;write_provider!(guarded,guard_actor,guard_provider);
            let error=Dispatch::prepare_compiled_search_json(&guard_provider,&wire(&req(i,&guarded,&protected)?)?,Limits::standard()?,4).err().ok_or("whole cached paragraph unexpectedly admitted")?;
            assert!(matches!(error,CE::Request(DE::SearchMutation(ME::ParagraphStyle(paragraph_styles::ParagraphStyleProductError::Stored(
                StoredPara::Output(CorePara::Compile(Compile::FieldContent))))))));
            body=body.replace("BODY K K","BODY");
        }
        let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let out=Dispatch::prepare_compiled_search_json(&p,&wire(&req(i,&s,&bytes)?)?,Limits::standard()?,4)?;verify_plan(&s,&p,&bytes,&out)?;
    }Ok(())
}
#[test]
fn compiled_review_selection_is_bound_without_expanding_semantic_write_scope()->TestResult{
    let bytes=definition::package(&fixture::body().replace("<hp:run>","<hp:run charPrIDRef='0'>"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let mut v=req(3,&s,&bytes)?;let inv=inventory(&p,&v)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"memo_body",7,8)?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;verify_plan(&s,&p,&bytes,&out)?;
    assert_eq!(out.with_verified_bytes(&p,5,section)??,section(&bytes)?.replace("MEMO K K","MEMO K X"));assert_eq!(out.receipt().source_edit_operations,1);Ok(())
}
#[test]
fn compiled_raw_canonical_scoped_plan_and_key_identity_bind_without_claiming_a_key()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=req(3,&s,&bytes)?;
    let a=Dispatch::prepare_compiled_search_json(&p,&wire(&good)?,Limits::standard()?,4)?;let mut padded=wire(&good)?;padded.extend_from_slice(b"  ");
    let b=Dispatch::prepare_compiled_search_json(&p,&padded,Limits::standard()?,4)?;assert_ne!(a.receipt().raw_request_sha256,b.receipt().raw_request_sha256);
    assert_eq!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_ne!(a.receipt().compiled_plan_sha256,b.receipt().compiled_plan_sha256);
    for(key,value)in[("idempotency_key",json!("OTHER-PRIVATE-KEY")),("plan_id",json!("other-compiled-plan"))]{let mut v=good.clone();v[key]=value;
        let b=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;assert_ne!(a.receipt().compiled_plan_sha256,b.receipt().compiled_plan_sha256);
        assert_eq!(a.receipt().output_package_sha256,b.receipt().output_package_sha256);assert_eq!(a.receipt().edit_inventory_sha256,b.receipt().edit_inventory_sha256);assert!(!b.receipt().execution_authority);}
    assert!(!serde_json::to_string(a.receipt())?.contains("PRIVATE"));Ok(())
}
#[test]
fn compiled_many_actual_edits_share_one_source_graph_and_noop_is_not_a_fake_operation()->TestResult{
    let mut body=String::new();for n in 1..=128{body.push_str(&para(n,"K"));}let bytes=definition::package(&body.replace(" charStyleIDRef='0'",""))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=req(3,&s,&bytes)?;v["operation"]["max_replacements"]=json!(128);
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;assert_eq!(out.receipt().source_edit_operations,128);assert_eq!(out.receipt().structural_owner_nodes,128);
    verify_plan(&s,&p,&bytes,&out)?;v["operation"]["replacement"]=json!("K");assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());Ok(())
}
#[test]
fn compiled_current_write_permission_is_required_for_compile_verify_and_byte_delivery()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let b=wire(&req(3,&s,&bytes)?)?;let out=Dispatch::prepare_compiled_search_json(&p,&b,Limits::standard()?,4)?;
    let reader=s.provider()?;let called=Cell::new(false);assert!(Dispatch::prepare_compiled_search_json(&reader,&b,Limits::standard()?,4).is_err());assert!(out.verify(&reader,5).is_err());
    assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn compiled_retained_plan_cannot_rebind_five_foreign_provider_scopes()->TestResult{
    let bytes=source(15)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_compiled_search_json(&p,&wire(&req(15,&s,&bytes)?)?,Limits::standard()?,4)?;let called=Cell::new(false);
    for i in 0..5{let tenant=if i==4{TenantId::new(Uuid::from_u128(1213))?}else{s.reader.tenant_id()};let subject=if i==3{SubjectDigest::from_authenticated_subject("foreign-compiled")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if i==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if i==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if i==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn compiled_acl_revocation_quarantine_aead_and_regrant_keep_original_security_boundary()->TestResult{
    for mode in 0..3{let bytes=source(7)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let b=wire(&req(7,&s,&bytes)?)?;
        let out=Dispatch::prepare_compiled_search_json(&p,&b,Limits::standard()?,4)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("COMPILED_SOURCE")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;}
    }Ok(())
}
#[test]
fn compiled_final_head_check_after_operation_construction_rejects_raced_plan()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,_p);let b=wire(&req(3,&s,&bytes)?)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"compiled race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    let Operation::SearchMutation(a)=Dispatch::prepare_json(&bound,&b,None,4)?else{return Err("kind".into())};repo.repository().calls.store(0,Ordering::SeqCst);(*a).compile(&bound,5)?;
    let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=5);let Operation::SearchMutation(a)=Dispatch::prepare_json(&bound,&b,None,4)?else{return Err("kind".into())};
    repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);assert!(matches!((*a).compile(&bound,6),Err(CE::Source(_))));Ok(())
}
#[test]
fn compiled_consumer_final_head_race_never_delivers_bytes_from_retained_plan()->TestResult{
    let bytes=source(6)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_compiled_search_json(&p,&wire(&req(6,&s,&bytes)?)?,Limits::standard()?,4)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"compiled consumer race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    out.with_verified_bytes(&bound,5,|_|())?;let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);
    let called=Cell::new(false);assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn compiled_server_limits_wrong_source_revision_and_client_policy_injections_fail_closed()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=req(3,&s,&bytes)?;
    for(key,value)in[("expected_source_package_sha256",json!("0".repeat(64))),("expected_head_generation",json!(s.head.generation()+1)),("document_id",json!("foreign")),("limits",json!({"max_operations":u64::MAX})),("approved",json!(true))]{let mut v=good.clone();v[key]=value;assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());}
    let mut limits=Limits::standard()?;limits.writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&good)?,limits,4).is_err());
    let mut v=good;v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id());assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());Ok(())
}
#[test]
fn compiled_text_controls_use_final_span_inventory_not_one_whole_write_per_control()->TestResult{
    let bytes=raw(&format!("A{TAB}B{TAB}C"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_compiled_search_json(&p,&wire(&req(14,&s,&bytes)?)?,Limits::standard()?,4)?;
    assert_eq!(out.receipt().source_edit_operations,1);assert_eq!(arg(&out.compiled().operations()[0],"source_edit_domain")?,"span_changes");verify_plan(&s,&p,&bytes,&out)
}
#[test]
fn compiled_number_noop_subset_uses_only_actual_changed_control_anchors()->TestResult{
    let style="<hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/>";
    let bytes=definition::package(&format!("<hp:p id='1'><hp:run><hp:t>A</hp:t><hp:ctrl><hp:autoNum num='9' numType='PICTURE'>{style}</hp:autoNum></hp:ctrl><hp:ctrl><hp:autoNum num='2' numType='PICTURE'>{style}</hp:autoNum></hp:ctrl></hp:run></hp:p>"))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_compiled_search_json(&p,&wire(&req(15,&s,&bytes)?)?,Limits::standard()?,4)?;
    assert_eq!(out.receipt().source_edit_operations,1);verify_plan(&s,&p,&bytes,&out)
}
#[path="sort_compiled_product.rs"]mod sort_v1;
