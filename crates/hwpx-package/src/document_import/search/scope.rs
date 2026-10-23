//! Explicit mapped-source scope; never a complete-document visibility claim.
use super::*;
use domain_ir::LogicalId;
use super::super::forms::{ImportedDocumentForms,VerifiedFormReconstruction};

pub const SCOPED_SOURCE_SEARCH_PROFILE:&str="hwpx-agent.scoped-source-text-search/v1";
#[derive(Clone,Copy,Debug)]
pub enum SourceSearchScope<'a> {MappedDocument,Paragraphs(&'a [LogicalId])}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSearchScopeReceipt {
    pub kind:&'static str,pub scope_sha256:[u8;32],pub selected_paragraphs:usize,pub selected_blocks:usize,
    pub whole_document_visibility_qualified:bool,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ScopedSourceSearchResult {
    profile:&'static str,scope:SourceSearchScopeReceipt,result:SourceSearchResult,
}
impl ScopedSourceSearchResult {
    /// # Errors
    /// Scope and full original result identity are retained in each cursor.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::Text(self.result.matches(),None),self.result.output_limit,request,context)
    }
    #[must_use] pub const fn scope_receipt(&self)->&SourceSearchScopeReceipt {&self.scope}
    #[must_use] pub const fn result(&self)->&SourceSearchResult {&self.result}
    /// # Errors
    /// Rejects the whole response on output overflow, without truncation.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {
        let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.result.output_limit};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)
    }
}
impl SourceTextIndex<'_> {
    /// Resolve only original paragraph handles before searching, including zero matches.
    /// # Errors
    /// Rejects empty, duplicate, foreign or over-limit paragraph selections.
    pub fn find_scoped(&self,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>)->Result<ScopedSourceSearchResult,E> {
        let(receipt,selected)=self.resolve_search_scope(scope)?;
        let result=self.find_selected(query,Some(&selected))?;
        let scoped=ScopedSourceSearchResult {profile:SCOPED_SOURCE_SEARCH_PROFILE,scope:receipt,result};
        let mut count=Output {bytes:None,length:0,maximum:self.limits.0.result_bytes};
        serde_json::to_writer(&mut count,&scoped).map_err(|_|E::Output)?;Ok(scoped)
    }
    pub(super) fn resolve_search_scope(&self,scope:SourceSearchScope<'_>)->Result<(SourceSearchScopeReceipt,BTreeSet<LogicalId>),E> {
        let available:BTreeSet<LogicalId>=self.blocks.iter().map(|b|b.paragraph.opaque_handle.clone()).collect();
        let (kind,selected)=match scope {
            SourceSearchScope::MappedDocument=>("mapped_document",available),
            SourceSearchScope::Paragraphs(handles)=>{
                if handles.is_empty()||handles.len()>self.limits.0.paragraphs{return Err(E::Scope);}
                let selected:BTreeSet<_>=handles.iter().cloned().collect();
                if selected.len()!=handles.len()||!selected.is_subset(&available){return Err(E::Scope);}
                ("paragraphs",selected)
            }
        };
        let selected_blocks=self.blocks.iter().filter(|b|selected.contains(&b.paragraph.opaque_handle)).count();
        let binding=serde_json::to_vec(&(SCOPED_SOURCE_SEARCH_PROFILE,self.receipt.index_sha256,kind,&selected)).map_err(|_|E::Mapping)?;
        Ok((SourceSearchScopeReceipt {kind,scope_sha256:Sha256::digest(binding).into(),selected_paragraphs:selected.len(),selected_blocks,
                whole_document_visibility_qualified:false},selected))
    }
}
impl VerifiedFormReconstruction<'_> {
    /// Reuse one complete reconstruction of this exact original, never a caller proof.
    /// # Errors
    /// Rejects a foreign model and all ordinary index limits; no service authority.
    pub fn source_text_index<'a>(&self,original:&'a ImportedDocumentForms,limits:SourceSearchLimits)->Result<SourceTextIndex<'a>,E> {
        self.for_original(original).map_err(|_|E::Source)?;
        extract::build(original.body_structure(),limits)
    }
}
