#[allow(dead_code)]
#[path="support/source_protection_fixture.rs"]mod fixture;
use domain_ir::DocumentId;
use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,protection::{SourceProtectionObservationError as E,SOURCE_PROTECTION_OBSERVATION_PROFILE}};
use sha2::{Digest as _,Sha256};
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
fn source(bytes:&[u8],document:&str)->Result<ImportedSourcePackage,Box<dyn Error>>{
    Ok(ImportedSourcePackage::import(bytes,DocumentId::parse(document)?,Sha256::digest(bytes).into(),SourceImportLimits::default())?)
}
fn base()->Result<Vec<u8>,Box<dyn Error>>{fixture::package("<hp:p id='1'><hp:run><hp:t>PRIVATE K</hp:t></hp:run></hp:p>")}
#[test]
fn source_protection_whole_counts_and_unknown_qualification_are_not_unprotected_attestation()->TestResult{
    let bytes=base()?;let s=source(&bytes,"source-observation")?;let out=s.observe_protection_signals()?;let counts=out.counts();
    assert_eq!(counts.parts,s.receipt().parts);assert_eq!(counts.xml_parts,s.receipt().xml_parts);assert_eq!(counts.xml_elements,s.receipt().xml_elements);
    assert_eq!(counts.document_signal_parts,0);assert_eq!(out.source_package_sha256(),<[u8;32]>::from(Sha256::digest(&bytes)));out.verify_binding(&s)?;out.require_no_observed_document_signals()?;
    let v=serde_json::to_value(&out)?;assert_eq!(v["profile"],SOURCE_PROTECTION_OBSERVATION_PROFILE);
    for field in["native_protection_verified","cryptographic_signature_verified","execution_authority"]{assert_eq!(v[field],false);}
    assert!(!serde_json::to_string(&out)?.contains("PRIVATE"));assert!(!format!("{out:?}").contains("PRIVATE"));Ok(())
}
#[test]
fn source_protection_original_sensitive_name_families_and_false_values_still_remain_signals()->TestResult{
    let bytes=base()?;
    for name in["protect","password","encrypt","signature","rights","readonly"]{for value in["0","false","1"]{
        let changed=fixture::header_signal(&bytes,&format!("prefix{name}Suffix"),value)?;let s=source(&changed,"sensitive-name")?;
        let out=s.observe_protection_signals()?;assert_eq!(out.counts().document_signal_parts,1);assert_eq!(out.counts().document_xml_signal_elements,1);
        assert_eq!(out.require_no_observed_document_signals(),Err(E::ObservedDocumentSignal));
    }}Ok(())
}
#[test]
fn source_protection_settings_outside_spine_and_ascii_case_are_observed()->TestResult{
    for path in["settings.xml","SeTtInGs.XmL"]{
        let bytes=fixture::add_xml(&base()?,path,"<x:settings xmlns:x='urn:future' readOnly='0'/>")?;
        let s=source(&bytes,"settings")?;let out=s.observe_protection_signals()?;assert_eq!(out.counts().document_signal_parts,1);
        assert_eq!(out.counts().document_xml_signal_elements,1);assert_eq!(out.require_no_observed_document_signals(),Err(E::ObservedDocumentSignal));
    }Ok(())
}
#[test]
fn source_protection_signature_encryption_and_rights_parts_block_without_crypto_claims()->TestResult{
    for(path,kind)in[("META-INF/signatures.xml",0),("META-INF/encryption.xml",1),("META-INF/rights.xml",2)]{
        let bytes=fixture::add_xml(&base()?,path,"<m:record xmlns:m='urn:opaque'/>")?;let out=source(&bytes,"sensitive-part")?.observe_protection_signals()?;
        let c=out.counts();assert_eq!([c.signature_parts,c.encryption_parts,c.rights_parts][kind],1);assert_eq!(c.document_signal_parts,1);
        assert_eq!(out.require_no_observed_document_signals(),Err(E::ObservedDocumentSignal));assert_eq!(serde_json::to_value(&out)?["cryptographic_signature_verified"],false);
    }Ok(())
}
#[test]
fn source_protection_local_locks_keep_original_namespace_false_value_and_ancestor_rules()->TestResult{
    for(attributes,blocked)in[("lock='1'",3),("lock='&#x31;'",3),("lock='false'",0),("lock='0'",0),("u:lock='1'",0)]{
        let bytes=fixture::package(&format!("<hp:p id='1' {attributes}><hp:run><hp:t>K</hp:t></hp:run></hp:p>"))?;
        let out=source(&bytes,"local-lock")?.observe_protection_signals()?;assert_eq!(out.counts().local_blocked_elements,blocked);
        assert_eq!(out.counts().document_signal_parts,0);out.require_no_observed_document_signals()?;
    }Ok(())
}
#[test]
fn source_protection_original_tc_and_table_size_propagation_is_not_a_global_lock()->TestResult{
    for body in["<hp:tbl><hp:sz protect='1'/><hp:tr><hp:tc><hp:p id='1'><hp:run><hp:t>K</hp:t></hp:run></hp:p></hp:tc></hp:tr></hp:tbl>",
        "<hp:tbl><hp:tr><hp:tc protect='1'><hp:p id='1'><hp:run><hp:t>K</hp:t></hp:run></hp:p></hp:tc></hp:tr></hp:tbl>"]{
        let out=source(&fixture::package(body)?,"table-local")?.observe_protection_signals()?;
        assert!(out.counts().local_blocked_elements>=4);assert_eq!(out.counts().document_signal_parts,0);out.require_no_observed_document_signals()?;
    }Ok(())
}
#[test]
fn source_protection_text_namespace_declarations_and_nonmetadata_names_are_not_global_signals()->TestResult{
    let bytes=fixture::header_xml(&base()?,"<hh:probe xmlns:password='urn:secret'>protect PASSWORD encrypt signature rights readonly</hh:probe>")?;
    let out=source(&bytes,"text-not-flags")?.observe_protection_signals()?;assert_eq!(out.counts().document_signal_parts,0);
    let bytes=fixture::add_xml(&bytes,"Other/signatures.xml","<x:signature xmlns:x='urn:future' password='1'/>")?;
    let out=source(&bytes,"other-not-metadata")?.observe_protection_signals()?;assert_eq!(out.counts().signature_parts,0);assert_eq!(out.counts().document_signal_parts,0);Ok(())
}
#[test]
fn source_protection_same_bytes_foreign_document_and_changed_package_cannot_rebind()->TestResult{
    let bytes=base()?;let original=source(&bytes,"original")?;let out=original.observe_protection_signals()?;
    let same=source(&bytes,"original")?;out.verify_binding(&same)?;let foreign=source(&bytes,"foreign")?;
    assert_eq!(out.verify_binding(&foreign),Err(E::Binding));let changed=source(&fixture::header_xml(&bytes,"<hh:probe code='1'/>")?,"original")?;
    assert_eq!(out.verify_binding(&changed),Err(E::Binding));Ok(())
}
#[test]
fn source_protection_large_inventory_has_exact_linear_guard_visit_accounting()->TestResult{
    let mut body=String::new();for n in 1..=1000{body.push_str(&format!("<hp:p id='{n}'><hp:run><hp:t>K</hp:t></hp:run></hp:p>"));}
    let bytes=fixture::package(&body)?;let s=source(&bytes,"large-observation")?;let out=s.observe_protection_signals()?;
    let header=s.parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").and_then(|p|p.xml()).ok_or("header")?;
    assert_eq!(out.counts().protection_element_visits,s.receipt().xml_elements*2+header.elements().len());assert_eq!(out.counts().local_blocked_elements,0);
    out.verify_binding(&s)?;assert_eq!(out,s.observe_protection_signals()?);Ok(())
}
#[test]
fn source_protection_multiple_signal_parts_and_unrelated_local_lock_are_counted_independently()->TestResult{
    let bytes=fixture::package("<hp:p id='1' lock='1'><hp:run><hp:t>K</hp:t></hp:run></hp:p>")?;
    let bytes=fixture::header_signal(&bytes,"pRoTeCt","0")?;let bytes=fixture::add_xml(&bytes,"settings.xml","<s signature='0'/>")?;
    let bytes=fixture::add_xml(&bytes,"META-INF/signatures.xml","<s/>")?;let out=source(&bytes,"multiple")?.observe_protection_signals()?;
    let c=out.counts();assert_eq!(c.document_signal_parts,3);assert_eq!(c.document_xml_signal_elements,2);assert_eq!(c.signature_parts,1);assert_eq!(c.local_blocked_elements,3);Ok(())
}
