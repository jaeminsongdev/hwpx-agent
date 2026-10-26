//! Source-derived initial result oracle, distinct from cache observation or Native authority.
pub mod single_page731;
use super::*;
use super::super::{bookmark_crossref::{BookmarkCrossReferenceDisplay,SourceBookmarkCrossReferenceBindings,SourceBookmarkResolution},
    cached_source::{FieldCacheSnapshot,SourceFieldCachedInlines}};

#[derive(Clone)]
pub struct BookmarkResultSelection { pub target_id:LogicalId,pub display:SdkCrossReferenceDisplay,pub hyperlink:bool }
impl fmt::Debug for BookmarkResultSelection {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("BookmarkResultSelection(<redacted>)")}
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum BookmarkResultStatus { SourceTextMatches,SourceTextMismatch,NeedsDocumentFlow,UnqualifiedTargetContent,UnqualifiedCachedResult }
#[derive(Clone,Copy,Debug,Eq,PartialEq)]
struct TextIdentity { sha256:[u8;32],bytes:usize }
#[derive(Clone,Eq,PartialEq)]
struct TargetSignature { family:SourceBookmarkFamily,name:TextIdentity,content:Option<TextIdentity> }
fn text(cache:&FieldCacheSnapshot)->Option<TextIdentity>{
    match cache {FieldCacheSnapshot::DecodedTextNotEvaluated{decoded_text_sha256,utf8_bytes,..}=>Some(TextIdentity{sha256:*decoded_text_sha256,bytes:*utf8_bytes}),
        FieldCacheSnapshot::StructuredUnqualified{..}=>None}
}
fn signature(context:&SourceBookmarkAuthoringContext<'_>,target:&LogicalId)->Result<TargetSignature,BookmarkResultError>{
    if let Some(index)=context.block_ids.get(target){
        let row=context.blocks.as_ref().and_then(|b|b.observations().get(*index)).ok_or(BookmarkResultError::Target)?;
        Ok(TargetSignature{family:SourceBookmarkFamily::Block,name:TextIdentity{sha256:Sha256::digest(row.name().as_bytes()).into(),bytes:row.name().len()},content:text(row.selected_source())})
    }else{
        let name=context.point_ids.get(target).ok_or(BookmarkResultError::Target)?;
        Ok(TargetSignature{family:SourceBookmarkFamily::Point,name:TextIdentity{sha256:Sha256::digest(name.as_bytes()).into(),bytes:name.len()},content:None})
    }
}
fn display(value:SdkCrossReferenceDisplay)->Result<BookmarkCrossReferenceDisplay,BookmarkResultError>{
    Ok(match value {SdkCrossReferenceDisplay::Page=>BookmarkCrossReferenceDisplay::Page,
        SdkCrossReferenceDisplay::BookmarkName=>BookmarkCrossReferenceDisplay::BookmarkName,
        SdkCrossReferenceDisplay::Content=>BookmarkCrossReferenceDisplay::Content,
        SdkCrossReferenceDisplay::RelativePosition=>BookmarkCrossReferenceDisplay::RelativePosition,
        SdkCrossReferenceDisplay::ObjectNumber=>return Err(BookmarkResultError::Selection)})
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum BookmarkResultError {
    #[error("BOOKMARK_RESULT_SOURCE_BINDING_REJECTED")]Source,
    #[error("BOOKMARK_RESULT_SELECTION_REJECTED")]Selection,
    #[error("BOOKMARK_RESULT_TARGET_REJECTED")]Target,
    #[error("BOOKMARK_RESULT_TARGET_DRIFT_REJECTED")]TargetDrift,
    #[error("BOOKMARK_RESULT_EXACT_COMMAND_REJECTED")]Command,
    #[error("BOOKMARK_RESULT_AMBIGUOUS_FIELD_REJECTED")]Ambiguous,
    #[error("BOOKMARK_RESULT_LIMIT")]Limit,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct BookmarkResultAssessment {
    pub profile:&'static str,pub status:BookmarkResultStatus,pub source_package_sha256:[u8;32],pub observed_package_sha256:[u8;32],
    pub command_sha256:[u8;32],pub display:BookmarkCrossReferenceDisplay,pub hyperlink:bool,pub target_name_sha256:[u8;32],
    pub expected_text_sha256:Option<[u8;32]>,pub expected_utf8_bytes:Option<usize>,pub observed_text_sha256:Option<[u8;32]>,pub observed_utf8_bytes:Option<usize>,
    pub source_target_text_signature_preserved:bool,pub whole_source_bindings_checked:bool,
    pub native_execution_or_layout_attested:bool,pub publication_revision_or_complete_reference_authority:bool,
}
/// Private immutable source oracle. No Deserialize or caller-supplied expected text/hash.
pub struct PreparedBookmarkResultExpectation {
    source_sha256:[u8;32],source_bytes:usize,target:TargetSignature,command_sha256:[u8;32],
    display:BookmarkCrossReferenceDisplay,sdk_display:SdkCrossReferenceDisplay,hyperlink:bool,limits:ReferenceAuxiliaryLimits,
}
impl fmt::Debug for PreparedBookmarkResultExpectation{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedBookmarkResultExpectation(<redacted>; source_oracle_only)")}
}
impl SourceBookmarkAuthoringContext<'_>{
    /// One original whole-source reconstruction for the complete bounded batch.
    /// # Errors
    /// Rejects stale/foreign source, empty/duplicate selections, ambiguous names and all original target/display guards.
    pub fn prepare_result_expectations(&self,fresh:&[u8],selections:&[BookmarkResultSelection])
        ->Result<Vec<PreparedBookmarkResultExpectation>,BookmarkResultError>{
        if selections.is_empty()||selections.len()>self.limits.config().items_per_kind
            || selections.len().checked_mul(std::mem::size_of::<PreparedBookmarkResultExpectation>())
                .is_none_or(|bytes|bytes>self.limits.config().output_bytes){return Err(BookmarkResultError::Limit);}
        self.verify_source(fresh).map_err(|_|BookmarkResultError::Source)?;
        let mut seen=BTreeSet::new();let mut out=Vec::new();
        out.try_reserve_exact(selections.len()).map_err(|_|BookmarkResultError::Limit)?;
        for s in selections{
            let target=self.prepare(&s.target_id,s.display,s.hyperlink).map_err(|_|BookmarkResultError::Target)?;
            let command_sha256=target.receipt().command_sha256;
            if !seen.insert(command_sha256){return Err(BookmarkResultError::Selection);}
            out.push(PreparedBookmarkResultExpectation{source_sha256:self.fields.receipt().source_package_sha256,source_bytes:fresh.len(),
                target:signature(self,&s.target_id)?,command_sha256,display:display(s.display)?,sdk_display:s.display,hyperlink:s.hyperlink,limits:self.limits});
        }Ok(out)
    }
}
impl PreparedBookmarkResultExpectation{
    /// # Errors
    /// Rehashes every original byte; no original import/graph clone/reconstruction per captured case.
    pub fn verify_original(&self,fresh:&[u8])->Result<(),BookmarkResultError>{
        if fresh.len()!=self.source_bytes||<[u8;32]>::from(Sha256::digest(fresh))!=self.source_sha256{return Err(BookmarkResultError::Source);}Ok(())
    }
    /// # Errors
    /// Fresh actual source reconstruction, exact typed Command/target and privately derived expected text.
    /// Page and relative location never use cached text as their own layout oracle.
    pub fn assess(&self,original_fresh:&[u8],actual:&ImportedDocumentFields<'_>,actual_fresh:&[u8])
        ->Result<BookmarkResultAssessment,BookmarkResultError>{
        self.verify_original(original_fresh)?;actual.verify_source(actual_fresh).map_err(|_|BookmarkResultError::Source)?;
        let commands=SourceBookmarkCrossReferenceBindings::import(actual,self.limits).map_err(|_|BookmarkResultError::Command)?;
        let mut matches=commands.bindings().iter().filter(|v|v.command_sha256==self.command_sha256);
        let row=matches.next().ok_or(BookmarkResultError::Command)?;
        if matches.next().is_some(){return Err(BookmarkResultError::Ambiguous);}
        if row.display!=self.display||row.hyperlink!=self.hyperlink||row.exact_target_name_sha256!=self.target.name.sha256{return Err(BookmarkResultError::Command);}
        let SourceBookmarkResolution::Bound{logical_target_id,target_state_sha256}=&row.target else{return Err(BookmarkResultError::Target)};
        let current=SourceBookmarkAuthoringContext::import(actual,self.limits).map_err(|_|BookmarkResultError::Target)?;
        let rebound=current.prepare(logical_target_id,self.sdk_display,self.hyperlink).map_err(|_|BookmarkResultError::Target)?;
        if &rebound.receipt().target_state_sha256!=target_state_sha256{return Err(BookmarkResultError::Target);}
        if signature(&current,logical_target_id)?!=self.target{return Err(BookmarkResultError::TargetDrift);}
        let caches=SourceFieldCachedInlines::import(actual,self.limits).map_err(|_|BookmarkResultError::Source)?;
        let cache=caches.observations().iter().find(|v|v.field_reference_id==row.field_reference_id).ok_or(BookmarkResultError::Source)?;
        let observed=text(&cache.cache);
        let expected=match self.display {BookmarkCrossReferenceDisplay::BookmarkName=>Some(self.target.name),BookmarkCrossReferenceDisplay::Content=>self.target.content,_=>None};
        let status=if matches!(self.display,BookmarkCrossReferenceDisplay::Page|BookmarkCrossReferenceDisplay::RelativePosition){BookmarkResultStatus::NeedsDocumentFlow}
            else if expected.is_none(){BookmarkResultStatus::UnqualifiedTargetContent}
            else if observed.is_none(){BookmarkResultStatus::UnqualifiedCachedResult}
            else if expected==observed{BookmarkResultStatus::SourceTextMatches}else{BookmarkResultStatus::SourceTextMismatch};
        let receipt=BookmarkResultAssessment{profile:"hwpx-agent.source-bookmark-initial-result-oracle/v1",status,source_package_sha256:self.source_sha256,
            observed_package_sha256:actual.receipt().source_package_sha256,command_sha256:self.command_sha256,display:self.display,hyperlink:self.hyperlink,
            target_name_sha256:self.target.name.sha256,expected_text_sha256:expected.map(|v|v.sha256),expected_utf8_bytes:expected.map(|v|v.bytes),
            observed_text_sha256:observed.map(|v|v.sha256),observed_utf8_bytes:observed.map(|v|v.bytes),
            source_target_text_signature_preserved:self.target.family==SourceBookmarkFamily::Point||self.target.content.is_some(),whole_source_bindings_checked:true,
            native_execution_or_layout_attested:false,publication_revision_or_complete_reference_authority:false};
        if serde_json::to_vec(&receipt).map_err(|_|BookmarkResultError::Limit)?.len()>self.limits.config().output_bytes{return Err(BookmarkResultError::Limit);}
        Ok(receipt)
    }
}
