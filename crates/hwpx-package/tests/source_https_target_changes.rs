use domain_ir::{DocumentId,ExternalLinkPolicy,ExternalTargetApproval,HyperlinkTarget,LinkReferenceLimits,ReferenceAuxiliaryLimits,ReferenceAuxiliaryLimitConfig};
use hwpx_package::{WriterLimits,document_import::{ImportedSourcePackage,SourceImportLimits,
    fields::{ImportedDocumentFields,semantics::{ImportedFieldMeaning,source_index::{SourceFieldMeaningIndex,https_targets::{SourceHttpsTargetChange,SourceHttpsTargetError as E}}}}}};
#[path="support/document_import_field_fixture.rs"]pub mod fixture;
pub type Result<T=()>=std::result::Result<T,Box<dyn std::error::Error>>;
pub fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
pub fn target_limits()->Result<LinkReferenceLimits>{Ok(LinkReferenceLimits::new(Default::default())?)}
pub fn target(uri:&str)->HyperlinkTarget{HyperlinkTarget::Https{uri:uri.into()}}
pub fn policy(targets:&[&HyperlinkTarget])->Result<ExternalLinkPolicy>{
    let mut approvals=targets.iter().map(|t|Ok(ExternalTargetApproval{kind:t.external_kind().ok_or("external")?,target_sha256:t.external_approval_sha256(target_limits()?)?})).collect::<Result<Vec<_>>>()?;
    approvals.sort();approvals.dedup();Ok(ExternalLinkPolicy{allow_https:true,allow_mailto:false,allow_managed_documents:false,approvals,policy_revision_sha256:"a".repeat(64)})
}
pub fn link(id:u32,uri:&str)->String{
    let uri=uri.replace('&',"&amp;");let command=uri.replacen("https://","https\\://",1);
    format!("<hp:p id='{id}'><hp:run><hp:ctrl><hp:fieldBegin id='{id}' type='HYPERLINK'><hp:parameters cnt='6' name=''><hp:integerParam name='Prop'>0</hp:integerParam><hp:stringParam name='Command'>{command};1;0;0;</hp:stringParam><hp:stringParam name='Path'>{uri}</hp:stringParam><hp:stringParam name='Category'>HWPHYPERLINK_TYPE_URL</hp:stringParam><hp:stringParam name='TargetType'>HWPHYPERLINK_TARGET_BOOKMARK</hp:stringParam><hp:stringParam name='DocOpenType'>HWPHYPERLINK_JUMP_CURRENTTAB</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>PRIVATE-CACHED-LABEL-{id}</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl></hp:run></hp:p>")
}
pub fn request<'a>(fields:&'a ImportedDocumentFields<'_>,index:&SourceFieldMeaningIndex<'_,'_>,i:usize,target:&'a HyperlinkTarget)->Result<SourceHttpsTargetChange<'a>>{
    let field=&fields.fields()[i];Ok(SourceHttpsTargetChange{reference_id:&field.reference_id,expected_source_field_sha256:field.begin_anchor.fingerprint_sha256,
        expected_meaning_sha256:index.meaning_sha256(i)?,target})
}
pub fn output_uris(bytes:&[u8],document:&str)->Result<Vec<Option<String>>>{
    let forms=fixture::forms(bytes,document)?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;
    Ok(index.observations().iter().map(|o|match &o.meaning{ImportedFieldMeaning::HttpsTarget{target:HyperlinkTarget::Https{uri}}=>Some(uri.clone()),_=>None}).collect())
}
pub fn rewrite(bytes:&[u8],name:&str,change:impl FnOnce(String)->String)->Result<Vec<u8>>{
    use std::io::{Cursor,Read,Write};use zip::{ZipArchive,ZipWriter,write::SimpleFileOptions};
    let mut reader=ZipArchive::new(Cursor::new(bytes))?;let mut writer=ZipWriter::new(Cursor::new(Vec::new()));let mut change=Some(change);
    for i in 0..reader.len(){let mut f=reader.by_index(i)?;let path=f.name().to_owned();let mut data=Vec::new();f.read_to_end(&mut data)?;
        if path==name{data=change.take().ok_or("duplicate")?(String::from_utf8(data)?).into_bytes();}
        writer.start_file(path,SimpleFileOptions::default().compression_method(f.compression()))?;writer.write_all(&data)?;}
    assert!(change.is_none());Ok(writer.finish()?.into_inner())
}
#[test]
fn captured_https_target_changes_only_approved_command_and_path_leaves()->Result{
    let bytes=fixture::captured()?;let original=bytes.clone();let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;
    let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let new=target("https://example.org/new?x=1&y=2#fragment");let p=policy(&[&new])?;
    let r=request(&fields,&index,0,&new)?;let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let candidate=index.lower_https_target_candidates(&proof,&[r],&p,target_limits()?,WriterLimits::default())?;
    let output=candidate.with_verified_bytes(|b|b.to_vec())?;assert_eq!(output_uris(&output,"https-change")?,vec![Some("https://example.org/new?x=1&y=2#fragment".into())]);
    assert_eq!(candidate.receipt().changed_parameter_leaves,2);assert_eq!(candidate.receipt().changed_parts,1);
    assert!(candidate.receipt().outside_selected_parameter_contents_exact&&candidate.receipt().unselected_meanings_and_cached_text_bytes_preserved);
    assert!(!candidate.receipt().native_protection_issuer_update_or_execution_qualified);
    for text in [format!("{candidate:?}"),format!("{:?}",candidate.receipt()),serde_json::to_string(candidate.receipt())?]{assert!(!text.contains("https:")&&!text.contains("PRIVATE")&&!text.contains("Command"));}
    assert_eq!(bytes,original);Ok(())
}
#[test]
fn batch_preserves_unselected_fields_and_cached_text_and_rejects_any_bad_member()->Result{
    let body=link(1,"https://example.org/old-one")+&link(2,"https://example.org/keep")+&link(3,"https://example.org/old-three");
    let bytes=fixture::package(&body)?;let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;
    let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let a=target("https://example.org/new-one");let b=target("https://example.org/new-three");let p=policy(&[&a,&b])?;
    let proof=forms.reconstruct_source_for_verification(&bytes)?;let changes=[request(&fields,&index,0,&a)?,request(&fields,&index,2,&b)?];
    let candidate=index.lower_https_target_candidates(&proof,&changes,&p,target_limits()?,WriterLimits::default())?;
    let output=candidate.with_verified_bytes(|b|b.to_vec())?;
    assert_eq!(output_uris(&output,"https-change")?,vec![Some("https://example.org/new-one".into()),Some("https://example.org/keep".into()),Some("https://example.org/new-three".into())]);
    assert_eq!(candidate.receipt().changes.len(),2);let mut bad=request(&fields,&index,2,&b)?;bad.expected_meaning_sha256=[0;32];
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&a)?,bad],&p,target_limits()?,WriterLimits::default()),Err(E::Selection)));Ok(())
}
#[test]
fn stale_duplicate_foreign_proof_and_unsupported_targets_fail_before_output()->Result{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;
    let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let a=target("https://example.org/new");let p=policy(&[&a])?;let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let mut bad=request(&fields,&index,0,&a)?;bad.expected_source_field_sha256=[0;32];
    assert!(matches!(index.lower_https_target_candidates(&proof,&[bad],&p,target_limits()?,WriterLimits::default()),Err(E::Selection)));
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&a)?,request(&fields,&index,0,&a)?],&p,target_limits()?,WriterLimits::default()),Err(E::Selection)));
    let foreign=fixture::forms(&bytes,"https-change")?;let foreign_proof=foreign.reconstruct_source_for_verification(&bytes)?;
    assert!(matches!(index.lower_https_target_candidates(&foreign_proof,&[request(&fields,&index,0,&a)?],&p,target_limits()?,WriterLimits::default()),Err(E::Source)));
    let mail=HyperlinkTarget::Mailto{address:"person@example.org".into()};
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&mail)?],&p,target_limits()?,WriterLimits::default()),Err(E::Unsupported)));Ok(())
}
#[test]
fn document_signals_and_supported_tracking_deny_but_unrelated_contexts_are_preserved()->Result{
    let body=link(1,"https://example.org/old");let new=target("https://example.org/new");let p=policy(&[&new])?;
    // These native locations do not admit a lock attribute in the original structure profile.
    // Keep that earlier rejection; do not relax the parser to reach a later guard.
    for invalid in [body.replace("<hp:p id='1'","<hp:p lock='1' id='1'"),body.replace("<hp:fieldBegin id=","<hp:fieldBegin lock='1' id=")]{
        let bytes=fixture::package(&invalid)?;assert!(fixture::forms(&bytes,"https-change").is_err());
    }
    for body in [body.replace("<hp:p id='1'","<hp:p paraTcId='7' id='1'"),body.replace("<hp:run>","<hp:run charTcId='7'>")]{
        let bytes=fixture::package(&body)?;let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;
        let proof=forms.reconstruct_source_for_verification(&bytes)?;assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&p,target_limits()?,WriterLimits::default()),Err(E::Protection)));
    }
    let bytes=fixture::package(&(body+"<hp:p id='2' paraTcId='7'><hp:run><hp:t>PRIVATE-TRACKED-OTHER</hp:t></hp:run></hp:p>"))?;
    let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;
    let proof=forms.reconstruct_source_for_verification(&bytes)?;let _=index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&p,target_limits()?,WriterLimits::default())?;
    let protected=rewrite(&bytes,"Contents/header.xml",|_|"<header password='PRIVATE'/>".into())?;
    let forms=fixture::forms(&protected,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let proof=forms.reconstruct_source_for_verification(&protected)?;
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&p,target_limits()?,WriterLimits::default()),Err(E::Protection)));Ok(())
}
#[test]
fn missing_exact_policy_approval_and_noop_are_not_partial_success()->Result{
    let old=target("https://example.org/old");let new=target("https://example.org/new");let bytes=fixture::package(&link(1,"https://example.org/old"))?;
    let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let proof=forms.reconstruct_source_for_verification(&bytes)?;
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&policy(&[&old])?,target_limits()?,WriterLimits::default()),Err(E::Policy)));
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&old)?],&policy(&[&old])?,target_limits()?,WriterLimits::default()),Err(E::NoChange)));Ok(())
}
#[test]
fn empty_batches_and_unknown_fields_cannot_be_treated_as_https_edits()->Result{
    let bytes=fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>PRIVATE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>")?;
    let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let new=target("https://example.org/new");let p=policy(&[&new])?;
    assert!(matches!(index.lower_https_target_candidates(&proof,&[],&p,target_limits()?,WriterLimits::default()),Err(E::Limit)));
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&p,target_limits()?,WriterLimits::default()),Err(E::Unsupported)));Ok(())
}
#[test]
fn off_spine_native_fields_and_tiny_writer_limits_cannot_yield_candidate_bytes()->Result{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;
    let hidden=rewrite(&bytes,"Contents/header.xml",|_|"<header xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'><hp:fieldBegin id='99' type='DATE'/><hp:fieldEnd beginIDRef='99'/></header>".into())?;
    let new=target("https://example.org/new");let p=policy(&[&new])?;
    let forms=fixture::forms(&hidden,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let proof=forms.reconstruct_source_for_verification(&hidden)?;
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&p,target_limits()?,WriterLimits::default()),Err(E::Source)));
    let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let tiny=WriterLimits::new(hwpx_package::WriterLimitConfig{max_output_bytes:1})?;
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&p,target_limits()?,tiny),Err(E::Writer)));Ok(())
}
#[test]
fn target_and_metadata_limits_remain_bounded_without_silent_clamping()->Result{
    let bytes=fixture::package(&link(1,"https://example.org/a"))?;let forms=fixture::forms(&bytes,"https-change")?;let fields=ImportedDocumentFields::import(&forms)?;
    let bounded=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{text_bytes:24,..Default::default()})?;
    let index=SourceFieldMeaningIndex::import(&fields,bounded)?;let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let new=target("https://example.org/too-long-for-this-source-profile");let p=policy(&[&new])?;
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&p,target_limits()?,WriterLimits::default()),Err(E::Limit)));
    let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let new=target("https://example.org/new");let p=policy(&[&new])?;
    let tight=LinkReferenceLimits::new(domain_ir::LinkReferenceLimitConfig{target_bytes:10,..Default::default()})?;
    assert!(matches!(index.lower_https_target_candidates(&proof,&[request(&fields,&index,0,&new)?],&p,tight,WriterLimits::default()),Err(E::Policy)));
    assert!(ImportedSourcePackage::import(&bytes,DocumentId::parse("https-change")?,[0;32],SourceImportLimits::default()).is_err());Ok(())
}
