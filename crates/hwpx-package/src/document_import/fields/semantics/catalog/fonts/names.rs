//! Bounded name matching over original declarations; no platform lookup or implicit fallback.
use super::{ImportedDocumentFonts, ImportedFontLanguage as L, replacement::FontReferenceMapping};
mod matcher;
pub(in crate::document_import) use matcher::declared_matcher;
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::BTreeSet,fmt};
use thiserror::Error;
pub const FONT_NAME_RESOLUTION_PROFILE:&str="hwpx-agent.source-font-name-resolution/v1";
#[derive(Clone,Copy,Serialize)]
pub struct FontNameReplacementQuery<'a> {
    pub query:&'a str,pub replacement:&'a str,pub regex:bool,pub case_sensitive:bool,pub whole_word:bool,
    pub languages:&'a [L],
}
impl fmt::Debug for FontNameReplacementQuery<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("FontNameReplacementQuery(<redacted>)")}}
#[derive(Clone,Copy,Debug,Eq,Error,PartialEq)]
pub enum FontNameResolutionError {
    #[error("FONT_NAME_PATTERN_REJECTED")] Pattern,
    #[error("FONT_NAME_LANGUAGE_REJECTED")] Language,
    #[error("FONT_NAME_LIMIT")] Limit,
    #[error("FONT_NAME_NO_MATCHES")] NoMatches,
    #[error("FONT_NAME_NO_CHANGE")] NoChange,
    #[error("FONT_NAME_TARGET_MISSING")] MissingTarget,
    #[error("FONT_NAME_TARGET_AMBIGUOUS")] AmbiguousTarget,
}
type E=FontNameResolutionError;
impl FontNameReplacementQuery<'_> {
    /// # Errors
    /// Explicit language set, nonempty names/pattern and finite bytes; no inferred default axes.
    pub fn validate(self,maximum_mappings:usize)->Result<(),E>{
        if maximum_mappings==0||maximum_mappings>128||self.query.len()>4096||self.replacement.len()>4096{return Err(E::Limit);}
        if self.query.is_empty()||self.replacement.is_empty()||self.query.chars().chain(self.replacement.chars()).any(char::is_control){return Err(E::Pattern);}
        if self.languages.is_empty()||self.languages.len()>7||self.languages.iter().collect::<BTreeSet<_>>().len()!=self.languages.len(){return Err(E::Language);}Ok(())
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct FontNameResolutionReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_font_graph_sha256:[u8;32],
    pub request_sha256:[u8;32],pub matched_declarations:usize,pub changed_mappings:usize,
    pub platform_fallback_availability_or_execution_qualified:bool,
}
pub struct FontNameResolution {receipt:FontNameResolutionReceipt,mappings:Vec<FontReferenceMapping>}
impl fmt::Debug for FontNameResolution{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("FontNameResolution(<redacted>; original_declarations_only)")}}
impl FontNameResolution {
    #[must_use]pub const fn receipt(&self)->&FontNameResolutionReceipt{&self.receipt}
    #[must_use]pub fn mappings(&self)->&[FontReferenceMapping]{&self.mappings}
}
impl ImportedDocumentFonts<'_, '_, '_, '_> {
    /// Literal substring or bounded Rust Unicode regex matches declared faces, not body text.
    /// Replacement is an exact, unique already declared face in each matched language.
    /// # Errors
    /// No zero-width match, truncated result, arbitrary first duplicate, file lookup or fallback.
    pub fn resolve_name_replacements(&self,query:FontNameReplacementQuery<'_>,maximum_mappings:usize)->Result<FontNameResolution,E>{
        self.resolve_name_replacements_with_budget(query,maximum_mappings,4096,1024*1024,1024*1024)
    }
    pub(in crate::document_import) fn resolve_name_replacements_with_budget(&self,query:FontNameReplacementQuery<'_>,maximum_mappings:usize,
        query_bytes:usize,pattern_bytes:usize,dfa_bytes:usize)->Result<FontNameResolution,E>{
        query.validate(maximum_mappings)?;
        if query_bytes==0||pattern_bytes==0||dfa_bytes==0||query.query.len()>query_bytes||query.replacement.len()>query_bytes{return Err(E::Limit);}
        let matcher=declared_matcher(query.query,query.regex,query.case_sensitive,query.whole_word,query_bytes,pattern_bytes,dfa_bytes)?;
        let languages:BTreeSet<_>=query.languages.iter().copied().collect();let mut mappings=Vec::new();let mut matched=0usize;
        for &language in &languages {
            let mut sources=Vec::new();let mut targets=Vec::new();
            for d in self.definitions().iter().filter(|d|d.language==language){
                if d.declared.face==query.replacement{targets.push(d.declared.id);}
                if let Some(hit)=matcher.find(&d.declared.face){
                    if hit.is_empty(){return Err(E::Pattern);}matched=matched.checked_add(1).ok_or(E::Limit)?;
                    sources.push(d.declared.id);
                    if sources.len()>128{return Err(E::Limit);}
                }
            }
            if sources.is_empty(){continue;}
            let target=match targets.as_slice(){[]=>return Err(E::MissingTarget),[one]=>*one,_=>return Err(E::AmbiguousTarget)};
            for from_native_id in sources {if from_native_id!=target{
                if mappings.len()>=maximum_mappings{return Err(E::Limit);}
                mappings.push(FontReferenceMapping{language,from_native_id,to_native_id:target});
            }}
        }
        if matched==0{return Err(E::NoMatches);}if mappings.is_empty(){return Err(E::NoChange);}mappings.sort_unstable();
        let languages:Vec<_>=languages.into_iter().collect();
        let canonical=FontNameReplacementQuery{languages:&languages,..query};
        let bytes=serde_json::to_vec(&(FONT_NAME_RESOLUTION_PROFILE,self.receipt(),canonical,&mappings,maximum_mappings)).map_err(|_|E::Limit)?;
        Ok(FontNameResolution{receipt:FontNameResolutionReceipt{profile:FONT_NAME_RESOLUTION_PROFILE,
            source_package_sha256:self.receipt().source_package_sha256,source_font_graph_sha256:self.receipt().graph_sha256,
            request_sha256:Sha256::digest(bytes).into(),matched_declarations:matched,changed_mappings:mappings.len(),
            platform_fallback_availability_or_execution_qualified:false},mappings})
    }
}
