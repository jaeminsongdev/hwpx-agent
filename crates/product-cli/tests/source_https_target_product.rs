use domain_ir::{DocumentId,HyperlinkTarget};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source_field_semantics::{ReferenceSourceFieldMeaningAssessment,ReferenceSourceMeaningSelection}};
use hwpx_package::{WriterLimits,document_import::{SourceImportLimits,
    fields::semantics::source_index::https_targets::{SourceHttpsTargetChange,SourceHttpsTargetError as E}}};
use sha2::{Digest as _,Sha256};
#[path="../../hwpx-package/tests/source_https_target_changes.rs"]mod support;
use support::{fixture,limits,target_limits,target,policy,link,output_uris,Result};
fn assess(bytes:&[u8],document:&str)->Result<ReferenceSourceFieldMeaningAssessment>{
    Ok(Product::assess_package_field_semantics(bytes,DocumentId::parse(document)?,Sha256::digest(bytes).into(),SourceImportLimits::default(),limits()?)?)}
fn request<'a>(selection:&'a ReferenceSourceMeaningSelection,target:&'a HyperlinkTarget)->SourceHttpsTargetChange<'a>{
    SourceHttpsTargetChange{reference_id:&selection.reference_id,expected_source_field_sha256:selection.source_field_sha256,
        expected_meaning_sha256:selection.meaning_sha256,target}}
#[test]
fn real_source_selection_drives_owned_candidate_without_url_execution_or_overwrite()->Result{
    let bytes=fixture::captured()?;let original=bytes.clone();let assessment=assess(&bytes,"https-product")?;let new=target("https://example.org/product?x=1&y=2");
    let requests=[request(&assessment.selections()[0],&new)];let p=policy(&[&new])?;
    let candidate=Product::prepare_package_https_target_changes(&bytes,DocumentId::parse("https-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),
        limits()?,&requests,&p,target_limits()?,WriterLimits::default())?;
    let output=candidate.with_verified_bytes(|b|b.to_vec())?;assert_eq!(output_uris(&output,"https-product")?,vec![Some("https://example.org/product?x=1&y=2".into())]);
    assert!(!candidate.receipt().native_protection_issuer_update_or_execution_qualified);assert_eq!(candidate.receipt().source_package_sha256,<[u8;32]>::from(Sha256::digest(&bytes)));
    for value in [serde_json::to_string(candidate.receipt())?,format!("{candidate:?}"),format!("{:?}",requests[0])]{assert!(!value.contains("https:")&&!value.contains("Command"));}
    assert_eq!(bytes,original);Ok(())
}
#[test]
fn stale_package_foreign_document_or_meaning_selector_and_missing_policy_deny_candidate()->Result{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let own=assess(&bytes,"https-product")?;let foreign=assess(&bytes,"other-document")?;
    let new=target("https://example.org/new");let p=policy(&[&new])?;
    let run=|digest,changes:&[SourceHttpsTargetChange<'_>],policy:&domain_ir::ExternalLinkPolicy|Product::prepare_package_https_target_changes(&bytes,DocumentId::parse("https-product").expect("fixed document"),digest,SourceImportLimits::default(),
        limits().expect("fixed limits"),changes,policy,target_limits().expect("fixed target limits"),WriterLimits::default());
    assert!(matches!(run([0;32],&[request(&own.selections()[0],&new)],&p),Err(E::Source)));
    assert!(matches!(run(Sha256::digest(&bytes).into(),&[request(&foreign.selections()[0],&new)],&p),Err(E::Selection)));
    let mut wrong=request(&own.selections()[0],&new);wrong.expected_meaning_sha256=[0;32];
    assert!(matches!(run(Sha256::digest(&bytes).into(),&[wrong],&p),Err(E::Selection)));
    assert!(matches!(run(Sha256::digest(&bytes).into(),&[request(&own.selections()[0],&new)],&policy(&[])?),Err(E::Policy)));Ok(())
}
#[test]
fn one_batch_and_policy_digest_bind_all_requested_source_targets_and_preserve_other_fields()->Result{
    let bytes=fixture::package(&(link(1,"https://example.org/one")+&link(2,"https://example.org/keep")+&link(3,"https://example.org/three")))?;
    let own=assess(&bytes,"https-product")?;let a=target("https://example.org/new-one");let b=target("https://example.org/new-three");
    let changes=[request(&own.selections()[0],&a),request(&own.selections()[2],&b)];let p=policy(&[&a,&b])?;
    let run=|p:&domain_ir::ExternalLinkPolicy|Product::prepare_package_https_target_changes(&bytes,DocumentId::parse("https-product").expect("fixed document"),Sha256::digest(&bytes).into(),SourceImportLimits::default(),
        limits().expect("fixed limits"),&changes,p,target_limits().expect("fixed target limits"),WriterLimits::default());
    let first=run(&p)?;let mut updated=p.clone();updated.policy_revision_sha256="b".repeat(64);let second=run(&updated)?;
    assert_eq!(first.receipt().changes.len(),2);assert_ne!(first.receipt().policy_sha256,second.receipt().policy_sha256);assert_ne!(first.receipt().request_sha256,second.receipt().request_sha256);
    let output=first.with_verified_bytes(|b|b.to_vec())?;
    assert_eq!(output_uris(&output,"https-product")?,vec![Some("https://example.org/new-one".into()),Some("https://example.org/keep".into()),Some("https://example.org/new-three".into())]);Ok(())
}
#[test]
fn malformed_original_tuple_is_rejected_and_unknown_kind_is_not_upgraded_to_https()->Result{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let own=assess(&bytes,"https-product")?;let new=target("https://example.org/new");let p=policy(&[&new])?;
    let malformed=fixture::package(&link(1,"https://example.org/old").replace("HWPHYPERLINK_TYPE_URL","OTHER"))?;
    assert!(matches!(Product::prepare_package_https_target_changes(&malformed,DocumentId::parse("https-product")?,Sha256::digest(&malformed).into(),SourceImportLimits::default(),
        limits()?,&[request(&own.selections()[0],&new)],&p,target_limits()?,WriterLimits::default()),Err(E::Source)));
    let bytes=fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>PRIVATE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>")?;
    let own=assess(&bytes,"https-product")?;assert!(matches!(Product::prepare_package_https_target_changes(&bytes,DocumentId::parse("https-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),
        limits()?,&[request(&own.selections()[0],&new)],&p,target_limits()?,WriterLimits::default()),Err(E::Unsupported)));Ok(())
}
