//! Whole admitted source signals, not absence-of-protection or cryptographic-signature attestation.
use super::ImportedSourcePackage;
use domain_ir::DocumentId;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

pub const SOURCE_PROTECTION_OBSERVATION_PROFILE:&str="hwpx-agent.source-protection-signals/partial-v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
pub struct SourceProtectionSignalCounts{
    pub parts:usize,pub xml_parts:usize,pub xml_elements:usize,pub protection_element_visits:usize,
    pub local_blocked_elements:usize,pub document_signal_parts:usize,pub document_xml_signal_elements:usize,
    pub signature_parts:usize,pub encryption_parts:usize,pub rights_parts:usize,
}
#[derive(Eq,PartialEq,Serialize)]
pub struct SourceProtectionObservation{
    profile:&'static str,document_id:DocumentId,source_package_sha256:[u8;32],source_provenance_sha256:[u8;32],
    counts:SourceProtectionSignalCounts,native_protection_verified:bool,cryptographic_signature_verified:bool,execution_authority:bool,
}
impl fmt::Debug for SourceProtectionObservation{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.debug_struct("SourceProtectionObservation").field("counts",&self.counts).finish_non_exhaustive()}
}
impl ImportedSourcePackage{
    /// # Errors
    /// Uses the original native-form sensitive-name predicate and original HP lock/TC/SZ guard.
    /// One scan of already admitted XML, one temporary local-guard vector per part; no ZIP/import replay.
    /// A missing signal remains unknown; this result never constructs ProtectionState::Unprotected.
    pub fn observe_protection_signals(&self)->Result<SourceProtectionObservation,SourceProtectionObservationError>{
        let mut counts=SourceProtectionSignalCounts{parts:0,xml_parts:0,xml_elements:0,protection_element_visits:0,
            local_blocked_elements:0,document_signal_parts:0,document_xml_signal_elements:0,signature_parts:0,encryption_parts:0,rights_parts:0};
        for part in self.parts(){
            add(&mut counts.parts,1)?;let path=part.path().as_str();
            let signature=path.eq_ignore_ascii_case("META-INF/signatures.xml");
            let encryption=path.eq_ignore_ascii_case("META-INF/encryption.xml");
            let rights=path.eq_ignore_ascii_case("META-INF/rights.xml");
            add(&mut counts.signature_parts,usize::from(signature))?;add(&mut counts.encryption_parts,usize::from(encryption))?;
            add(&mut counts.rights_parts,usize::from(rights))?;
            let sensitive_part=signature||encryption||rights;
            // Exactly the original conservative native-form metadata scopes, not text-value guessing.
            let global=sensitive_part||path.eq_ignore_ascii_case("settings.xml")||path=="Contents/header.xml";
            let mut document_signal=sensitive_part;
            if let Some(xml)=part.xml(){
                add(&mut counts.xml_parts,1)?;add(&mut counts.xml_elements,xml.elements().len())?;
                let local=super::structure::caption_text_batch::observed_protection(xml).map_err(|_|SourceProtectionObservationError::Traversal)?;
                add(&mut counts.protection_element_visits,xml.elements().len().checked_mul(2).ok_or(SourceProtectionObservationError::Limit)?)?;
                add(&mut counts.local_blocked_elements,local.into_iter().filter(|blocked|*blocked).count())?;
                if global{
                    add(&mut counts.protection_element_visits,xml.elements().len())?;
                    for node in xml.elements(){
                        if crate::native_form_package::sensitive(node.name().local_name())||node.attributes().iter().any(|a|
                            !a.is_namespace_declaration()&&crate::native_form_package::sensitive(a.name().local_name())){
                            document_signal=true;add(&mut counts.document_xml_signal_elements,1)?;
                        }
                    }
                }
            }
            add(&mut counts.document_signal_parts,usize::from(document_signal))?;
        }
        if counts.parts!=self.receipt().parts||counts.xml_parts!=self.receipt().xml_parts||counts.xml_elements!=self.receipt().xml_elements{
            return Err(SourceProtectionObservationError::Binding);
        }
        Ok(SourceProtectionObservation{profile:SOURCE_PROTECTION_OBSERVATION_PROFILE,document_id:self.document_id().clone(),
            source_package_sha256:self.receipt().source_package_sha256,source_provenance_sha256:self.receipt().provenance_sha256,counts,
            native_protection_verified:false,cryptographic_signature_verified:false,execution_authority:false})
    }
}
impl SourceProtectionObservation{
    #[must_use]pub const fn counts(&self)->SourceProtectionSignalCounts{self.counts}
    #[must_use]pub const fn source_package_sha256(&self)->[u8;32]{self.source_package_sha256}
    /// # Errors
    /// Sealed source identity only. Fresh service/ACL/head checks still belong to the original provider.
    pub fn verify_binding(&self,source:&ImportedSourcePackage)->Result<(),SourceProtectionObservationError>{
        let receipt=source.receipt();
        if &self.document_id!=source.document_id()||self.source_package_sha256!=receipt.source_package_sha256
            ||self.source_provenance_sha256!=receipt.provenance_sha256||self.counts.parts!=receipt.parts
            ||self.counts.xml_parts!=receipt.xml_parts||self.counts.xml_elements!=receipt.xml_elements{
            return Err(SourceProtectionObservationError::Binding);
        }Ok(())
    }
    /// # Errors
    /// Denies observed document-wide signals even if a caller supplies Unprotected routing context.
    /// Local lock counts alone do not block unrelated edits; original selection guards remain authoritative.
    /// Success means only no document signal observed in this partial profile, never native unprotection.
    pub fn require_no_observed_document_signals(&self)->Result<(),SourceProtectionObservationError>{
        if self.counts.document_signal_parts!=0{return Err(SourceProtectionObservationError::ObservedDocumentSignal);}Ok(())
    }
}
fn add(value:&mut usize,n:usize)->Result<(),SourceProtectionObservationError>{
    *value=value.checked_add(n).ok_or(SourceProtectionObservationError::Limit)?;Ok(())
}
#[derive(Clone,Copy,Debug,Eq,Error,PartialEq)]
pub enum SourceProtectionObservationError{
    #[error("source_protection_observation_binding_rejected")]Binding,
    #[error("source_protection_observation_original_guard_rejected")]Traversal,
    #[error("source_protection_observation_limit")]Limit,
    #[error("source_protection_observed_document_security_signal")]ObservedDocumentSignal,
}
