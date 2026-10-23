//! One source-bound HTTPS target transaction; no URL access, field/cache update or service authority.
use super::*;
use domain_ir::{ExternalLinkPolicy,HyperlinkTarget,LinkReferenceLimits,LogicalId};
use crate::{BoundedZipReader,IdIndexLimits,IdRuleProfile,PackageArtifact,PackageGraphLimits,PackagePath,
    PatchIntent,PatchLimits,PatchText,PreservationRuleProfile,PreservingPatchEngine,PreservingWriter,WriterError,WriterLimits,
    XmlElementSelector};
use crate::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms};
use std::{collections::{BTreeMap,BTreeSet},io::Cursor};

pub struct SourceHttpsTargetChange<'a>{pub reference_id:&'a LogicalId,pub expected_source_field_sha256:[u8;32],
    pub expected_meaning_sha256:[u8;32],pub target:&'a HyperlinkTarget}
impl fmt::Debug for SourceHttpsTargetChange<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceHttpsTargetChange(<redacted>)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceHttpsTargetChangeReceipt{pub source_reference_id:LogicalId,pub source_field_sha256:[u8;32],pub source_meaning_sha256:[u8;32],
    pub output_target_sha256:String}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceHttpsTargetReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub source_meaning_inventory_sha256:[u8;32],pub policy_sha256:[u8;32],pub request_sha256:[u8;32],
    pub changes:Vec<SourceHttpsTargetChangeReceipt>,pub changed_parts:usize,pub changed_parameter_leaves:usize,
    pub id_rule_profile:&'static str,pub outside_selected_parameter_contents_exact:bool,
    pub unselected_meanings_and_cached_text_bytes_preserved:bool,pub native_protection_issuer_update_or_execution_qualified:bool,
}
pub struct SourceHttpsTargetCandidate{artifact:PackageArtifact,receipt:SourceHttpsTargetReceipt}
impl fmt::Debug for SourceHttpsTargetCandidate{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceHttpsTargetCandidate(<redacted>; no_execution_authority)")}}
impl SourceHttpsTargetCandidate{
    #[must_use]pub const fn receipt(&self)->&SourceHttpsTargetReceipt{&self.receipt}
    /// Writer integrity only. Caller still needs current service/route/policy checks before storage or execution.
    /// # Errors
    /// Refuses an invalid owned artifact before exposing its bytes.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(consume)}
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceHttpsTargetError{
    #[error("SOURCE_HTTPS_TARGET_SOURCE_REJECTED")]Source,
    #[error("SOURCE_HTTPS_TARGET_SELECTION_REJECTED")]Selection,
    #[error("SOURCE_HTTPS_TARGET_POLICY_REJECTED")]Policy,
    #[error("SOURCE_HTTPS_TARGET_PROTECTION_REJECTED")]Protection,
    #[error("SOURCE_HTTPS_TARGET_UNQUALIFIED_KIND")]Unsupported,
    #[error("SOURCE_HTTPS_TARGET_NO_CHANGE")]NoChange,
    #[error("SOURCE_HTTPS_TARGET_LIMIT")]Limit,
    #[error("SOURCE_HTTPS_TARGET_PATCH_REJECTED")]Patch,
    #[error("SOURCE_HTTPS_TARGET_WRITER_REJECTED")]Writer,
    #[error("SOURCE_HTTPS_TARGET_PRESERVATION_REJECTED")]Preservation,
    #[error("SOURCE_HTTPS_TARGET_READBACK_REJECTED")]Readback,
}
type E=SourceHttpsTargetError;
struct Leaf{element:usize,value:String}

impl SourceFieldMeaningIndex<'_,'_>{
    /// All-or-nothing selection of exact source HTTPS fields and policy-approved new HTTPS targets.
    /// # Errors
    /// Rejects a foreign fresh proof, stale/duplicate/unsupported/no-op selections, observed protection,
    /// missing destination approval and any writer, whole output or preservation inconsistency.
    pub fn lower_https_target_candidates(&self,proof:&VerifiedFormReconstruction<'_>,requests:&[SourceHttpsTargetChange<'_>],
        policy:&ExternalLinkPolicy,target_limits:LinkReferenceLimits,writer:WriterLimits)->Result<SourceHttpsTargetCandidate,E>{
        if requests.is_empty()||requests.len()>self.limits.config().items_per_kind||requests.len()>target_limits.config().hyperlinks
            ||requests.len().checked_mul(2).is_none_or(|n|n>PatchLimits::default().config().max_intents){return Err(E::Limit);}
        let target_policy=policy.validated_external_targets(target_limits).map_err(|_|E::Policy)?;
        let policy_sha256=bounded_digest(policy,self.limits.config().output_bytes).map_err(|_|E::Limit)?;
        let rebuilt=proof.for_original(self.fields.forms).map_err(|_|E::Source)?;
        let source=self.fields.forms.source();let fresh=rebuilt.source().original.as_ref();
        let protection=source.observe_protection_signals().map_err(|_|E::Protection)?;
        protection.require_no_observed_document_signals().map_err(|_|E::Protection)?;
        let mut field_counts=[0usize;2];
        for part in source.parts(){if let Some(xml)=part.xml(){for node in xml.elements(){
            if node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE){let i=match node.name().local_name(){"fieldBegin"=>0,"fieldEnd"=>1,_=>continue};
                field_counts[i]=field_counts[i].checked_add(1).filter(|n|*n<=self.limits.config().items_per_kind).ok_or(E::Limit)?;}
        }}}
        if field_counts!=[self.fields.fields().len();2]{return Err(E::Source);}
        let by_id:BTreeMap<_,_>=self.fields.fields().iter().enumerate().map(|(i,f)|(&f.reference_id,i)).collect();
        let mut selected=BTreeMap::new();let mut plans:BTreeMap<&PackagePath,Vec<Leaf>>=BTreeMap::new();
        let mut guards:BTreeMap<&PackagePath,Vec<usize>>=BTreeMap::new();let mut intents=Vec::new();let mut changes=Vec::new();
        let mut seen=BTreeSet::new();
        for request in requests{
            if !matches!(request.target,HyperlinkTarget::Https{..}){return Err(E::Unsupported);}
            target_policy.require_external_target(request.target).map_err(|_|E::Policy)?;
            if !seen.insert(request.reference_id){return Err(E::Selection);}
            let i=*by_id.get(request.reference_id).ok_or(E::Selection)?;let range=&self.fields.fields()[i];
            if range.begin_anchor.fingerprint_sha256!=request.expected_source_field_sha256
                ||self.meaning_sha256(i).map_err(|_|E::Limit)?!=request.expected_meaning_sha256{return Err(E::Selection);}
            let ImportedFieldMeaning::HttpsTarget{target:old}=&self.observations[i].meaning else{return Err(E::Unsupported)};
            if old==request.target{return Err(E::NoChange);}
            let HyperlinkTarget::Https{uri}=request.target else{return Err(E::Unsupported)};
            if uri.len()>self.limits.config().text_bytes{return Err(E::Limit);}
            let begin=source.resolve_anchor(&range.begin_anchor).map_err(|_|E::Source)?;
            let end=source.resolve_anchor(&range.end_anchor).map_err(|_|E::Source)?;
            let param=source.resolve_anchor(range.parameter_anchor.as_ref().ok_or(E::Selection)?).map_err(|_|E::Source)?;
            if begin.part().path()!=end.part().path()||param.part().path()!=begin.part().path(){return Err(E::Source);}
            let part=begin.part();let xml=part.xml().ok_or(E::Source)?;
            let start=begin.element_index().ok_or(E::Source)?;
            let stop=end.element_index().and_then(|n|n.checked_add(1)).ok_or(E::Source)?;
            if start>=stop{return Err(E::Source);}
            if !guards.contains_key(part.path()){
                let flags=crate::document_import::search::replacement::atoms::unicode::plan::guard(xml).map_err(|_|E::Protection)?;
                let mut prefix=Vec::new();prefix.try_reserve_exact(flags.len()+1).map_err(|_|E::Limit)?;prefix.push(0usize);
                for flag in flags{let next=prefix.last().copied().ok_or(E::Protection)?.checked_add(usize::from(flag)).ok_or(E::Limit)?;prefix.push(next);}
                guards.insert(part.path(),prefix);
            }
            let prefix=guards.get(part.path()).ok_or(E::Protection)?;
            if prefix.get(stop).zip(prefix.get(start)).is_none_or(|(a,b)|a!=b){return Err(E::Protection);}
            let leaves=crate::hyperlink_hwpx::imported_https_target_leaves(xml,param.element_index().ok_or(E::Source)?,request.target).map_err(|_|E::Source)?;
            for(element,value)in leaves{
                if element<start||element>=stop{return Err(E::Protection);}
                let target=XmlElementSelector::bind(part.path(),xml,element).map_err(|_|E::Selection)?;
                let text=PatchText::new(&value).map_err(|_|E::Limit)?;
                intents.push(PatchIntent::ReplaceLeafText{target,value:text});plans.entry(part.path()).or_default().push(Leaf{element,value});
            }
            selected.insert(i,request.target);
            changes.push(SourceHttpsTargetChangeReceipt{source_reference_id:range.reference_id.clone(),source_field_sha256:range.begin_anchor.fingerprint_sha256,
                source_meaning_sha256:request.expected_meaning_sha256,output_target_sha256:request.target.external_approval_sha256(target_limits).map_err(|_|E::Policy)?});
        }
        for leaves in plans.values_mut(){leaves.sort_by_key(|p|p.element);if leaves.windows(2).any(|p|p[0].element==p[1].element){return Err(E::Selection);}}
        let zip=source.limits.zip().map_err(|_|E::Source)?;let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;
        let profile=crate::document_import::search::replacement::font_profile::select(source,IdRuleProfile::hwpml_2011_shape_v6());
        let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,PackageGraphLimits::default(),profile,
            IdIndexLimits::default(),PatchLimits::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&intents).map_err(|_|E::Patch)?;
        if patch.added_parts()!=0||patch.changed_parts()!=plans.len()||patch.parts().iter().any(|p|!plans.contains_key(p.path())&&p.source_sha256()!=Some(p.output_sha256())){return Err(E::Preservation);}
        let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer).map_err(|_|E::Writer)?;
        artifact.with_verified_bytes(|bytes|->Result<(),E>{
            let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
            let forms=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;
            let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Readback)?;
            let meanings=SourceFieldMeaningIndex::import(&fields,self.limits).map_err(|_|E::Readback)?;
            if meanings.observations.len()!=self.observations.len(){return Err(E::Readback);}
            for(i,(old,new))in self.observations.iter().zip(&meanings.observations).enumerate(){
                if let Some(target)=selected.get(&i){if !matches!(&new.meaning,ImportedFieldMeaning::HttpsTarget{target:actual}if actual==*target){return Err(E::Readback);}}
                else if old.meaning!=new.meaning{return Err(E::Readback);}
                let a=&self.fields.fields()[i];let b=&fields.fields()[i];
                if a.native_kind!=b.native_kind||a.native_begin_id!=b.native_begin_id||a.inline_start!=b.inline_start||a.inline_end!=b.inline_end{return Err(E::Readback);}
                let x=source.resolve_anchor(&a.begin_anchor).map_err(|_|E::Readback)?;let y=forms.source().resolve_anchor(&b.begin_anchor).map_err(|_|E::Readback)?;
                if x.part().path()!=y.part().path()||x.element_index()!=y.element_index(){return Err(E::Readback);}
            }
            for(path,leaves)in &plans{
                let old=source.parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
                let new=forms.source().parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
                if old.elements().len()!=new.elements().len(){return Err(E::Readback);}
                let(mut before,mut after)=(0,0);
                for leaf in leaves{
                    let a=old.elements()[leaf.element].content_span().ok_or(E::Readback)?;let b=new.elements()[leaf.element].content_span().ok_or(E::Readback)?;
                    if !old.with_source_bytes(|x|new.with_source_bytes(|y|x.get(before..a.start())==y.get(after..b.start()))){return Err(E::Preservation);}
                    let node=new.elements().get(leaf.element).ok_or(E::Readback)?;
                    if node.first_child().is_some(){return Err(E::Readback);}
                    let value=new.source_text(b).map_err(|_|E::Readback)?;
                    if quick_xml::escape::unescape(value).map_err(|_|E::Readback)?.as_ref()!=leaf.value{return Err(E::Readback);}
                    before=a.end();after=b.end();
                }
                if !old.with_source_bytes(|a|new.with_source_bytes(|b|a.get(before..)==b.get(after..))){return Err(E::Preservation);}
            }Ok(())
        }).map_err(|_|E::Writer)??;
        let request_sha256=bounded_digest(&("source-https-targets/v1",self.receipt.meaning_inventory_sha256,policy_sha256,&changes),self.limits.config().output_bytes).map_err(|_|E::Limit)?;
        let receipt=SourceHttpsTargetReceipt{profile:"hwpx-agent.source-https-target-changes/v1",source_package_sha256:source.receipt().source_package_sha256,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),source_meaning_inventory_sha256:self.receipt.meaning_inventory_sha256,
            policy_sha256,request_sha256,changed_parts:plans.len(),changed_parameter_leaves:intents.len(),changes,id_rule_profile:profile.version(),
            outside_selected_parameter_contents_exact:true,unselected_meanings_and_cached_text_bytes_preserved:true,native_protection_issuer_update_or_execution_qualified:false};
        let _=bounded_digest(&receipt,self.limits.config().output_bytes).map_err(|_|E::Limit)?;
        Ok(SourceHttpsTargetCandidate{artifact,receipt})
    }
}
