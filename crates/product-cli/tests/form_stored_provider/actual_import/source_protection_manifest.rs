//! Actual provider source facts cannot be replaced by synthetic Unprotected route context.
use super::*;
#[allow(dead_code)]
#[path="../../../../hwpx-package/tests/support/source_protection_fixture.rs"]mod security_fixture;
use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,protection::SourceProtectionObservationError as PE};
fn parsed(bytes:&[u8])->Result<ImportedSourcePackage,Box<dyn Error>>{
    Ok(ImportedSourcePackage::import(bytes,DocumentId::parse("actual-form-document")?,*ContentDigest::of(bytes).as_bytes(),SourceImportLimits::default())?)
}
#[test]
fn protection_all16_source_families_block_document_metadata_even_with_unprotected_context()->TestResult{
    for i in 0..16{let bytes=security_fixture::header_signal(&source(i)?,"protect","0")?;
        let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let compiled=compile(i,&s,&p,&bytes)?;let(context,catalog)=routing(compiled.receipt().capability_id,5,0)?;
        assert!(matches!(compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("source-signal")?,5),Err(E::SourceProtection(PE::ObservedDocumentSignal))));
        assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
        assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    }Ok(())
}
#[test]
fn protection_settings_outside_selected_body_cannot_be_bypassed_by_routing_state()->TestResult{
    for path in["settings.xml","SeTtInGs.XmL"]{let bytes=security_fixture::add_xml(&source(3)?,path,"<s readOnly='false'/>")?;
        let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let compiled=compile(3,&s,&p,&bytes)?;
        let(context,catalog)=routing(compiled.receipt().capability_id,5,0)?;
        assert!(matches!(compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("source-settings")?,5),Err(E::SourceProtection(PE::ObservedDocumentSignal))));
    }Ok(())
}
#[test]
fn protection_unselected_local_locks_do_not_become_fake_document_wide_denials()->TestResult{
    let locked=table::table(300).replace("lock='0'","lock='1'");
    let body=para(1,"K")+&para(2,&format!("OTHER</hp:t>{locked}<hp:t>TAIL"));
    let bytes=security_fixture::package(&body.replace(" charStyleIDRef='0'",""))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let compiled=compile(3,&s,&p,&bytes)?;
    let(context,catalog)=routing(compiled.receipt().capability_id,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("local-only")?,5)?;
    assert!(out.source_protection_observation().counts().local_blocked_elements>0);assert_eq!(out.source_protection_observation().counts().document_signal_parts,0);
    let(context,catalog)=routing(out.compiled_receipt().capability_id,6,0)?;
    let actual=out.with_verified_bytes(&p,&context,&catalog,6,section)??;assert_eq!(actual,section(&bytes)?.replace(">K<",">X<"));Ok(())
}
#[test]
fn protection_selected_local_lock_keeps_original_candidate_rejection()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::CompiledSearchError as CE;
    use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::StoredLiteralSearchError as SE;
    let locked=table::table(300).replace("lock='0'","lock='1'");
    let bytes=security_fixture::package(&para(1,&format!("K</hp:t>{locked}<hp:t>TAIL")).replace(" charStyleIDRef='0'",""))?;
    assert!(parsed(&bytes)?.observe_protection_signals()?.counts().local_blocked_elements>0);
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let mut v=req(3,&s,&bytes)?;v["operation"]["query"]=json!("CELL-OLD");
    assert!(matches!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4),
        Err(CE::Request(DE::SearchMutation(ME::SelectorLiteral(LE::Stored(SE::Output(Compile::Protection))))))));Ok(())
}
#[test]
fn protection_clean_source_stays_unknown_and_retained_verification_reuses_immutable_observation()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let compiled=compile(3,&s,&p,&bytes)?;
    let cap=compiled.receipt().capability_id;let(context,catalog)=routing(cap,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("unknown-not-clear")?,5)?;
    let observation=out.source_protection_observation();let before=serde_json::to_value(observation)?;
    assert_eq!(observation.source_package_sha256(),*ContentDigest::of(&bytes).as_bytes());observation.verify_binding(&parsed(&bytes)?)?;
    for key in["native_protection_verified","cryptographic_signature_verified","execution_authority"]{assert_eq!(before[key],false);}
    for now in[6,7,8]{let(context,catalog)=routing(cap,now,0)?;out.verify(&p,&context,&catalog,now)?;
        assert!(std::ptr::eq(observation,out.source_protection_observation()));assert_eq!(before,serde_json::to_value(out.source_protection_observation())?);}
    let(context,catalog)=routing(cap,9,0)?;assert!(matches!(out.require_current_product_route(&p,&context,&catalog,9),Err(E::Candidate(_))));Ok(())
}
#[test]
fn protection_observation_is_not_retained_write_permission_or_acl_authority()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let compiled=compile(3,&s,&p,&bytes)?;
    let cap=compiled.receipt().capability_id;let(context,catalog)=routing(cap,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("not-authorization")?,5)?;
    out.source_protection_observation().require_no_observed_document_signals()?;let reader=s.provider()?;let(context,catalog)=routing(cap,6,0)?;
    let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,&context,&catalog,6,|_|called.set(true)).is_err());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;
    assert!(out.with_verified_bytes(&p,&context,&catalog,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;
    let(context,catalog)=routing(cap,8,0)?;out.verify(&p,&context,&catalog,8)?;Ok(())
}
#[test]
fn protection_metadata_text_and_namespace_declarations_are_not_fabricated_flags_or_disclosed()->TestResult{
    let bytes=security_fixture::header_xml(&source(3)?,"<hh:probe xmlns:password='urn:private'>PRIVATE protect password encrypt signature rights readonly</hh:probe>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let compiled=compile(3,&s,&p,&bytes)?;
    let(context,catalog)=routing(compiled.receipt().capability_id,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("text-not-signal")?,5)?;
    assert_eq!(out.source_protection_observation().counts().document_signal_parts,0);
    assert!(!serde_json::to_string(out.source_protection_observation())?.contains("PRIVATE"));assert!(!format!("{:?}",out.source_protection_observation()).contains("PRIVATE"));Ok(())
}
#[test]
fn protection_observation_binds_provider_source_not_another_package_with_same_routing_catalog()->TestResult{
    let a=source(3)?;let b=security_fixture::header_xml(&a,"<hh:probe code='1'/>")?;
    let sa=StoredFixture::new(&a,ArtifactKind::Result,false)?;write_provider!(sa,actor_a,pa);
    let sb=StoredFixture::new(&b,ArtifactKind::Result,false)?;write_provider!(sb,actor_b,pb);
    let ca=compile(3,&sa,&pa,&a)?;let cb=compile(3,&sb,&pb,&b)?;let(context,catalog)=routing(ca.receipt().capability_id,5,0)?;
    let oa=ca.prepare_execution_manifest(&pa,&context,&catalog,transaction("source-a")?,5)?;let ob=cb.prepare_execution_manifest(&pb,&context,&catalog,transaction("source-b")?,5)?;
    assert_ne!(oa.source_protection_observation().source_package_sha256(),ob.source_protection_observation().source_package_sha256());
    assert_eq!(oa.source_protection_observation().verify_binding(&parsed(&b)?),Err(PE::Binding));
    assert_eq!(ob.source_protection_observation().verify_binding(&parsed(&a)?),Err(PE::Binding));Ok(())
}
