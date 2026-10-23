//! Immutable mapped-source search, not complete-document visibility, edits or authority.
mod normalization;
mod extract;
mod captures;
pub mod scope;
pub mod selector;
pub mod inspection;
pub mod reviews;
pub mod navigation;
pub mod replacement;
pub mod personal_info;
use super::structure::ImportedDocumentStructure;
use domain_ir::SourceAnchorHandle;
use regex::RegexBuilder;
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::BTreeSet,fmt,io};
use thiserror::Error;

pub const SOURCE_SEARCH_PROFILE:&str="hwpx-agent.source-text-search/nfc-map-v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub struct SourceSearchLimitConfig {
    pub paragraphs:usize,pub blocks:usize,pub segments:usize,pub scalars:usize,
    pub decomposed_scalars:usize,pub query_bytes:usize,pub matches:usize,
    pub reported_points:usize,pub pattern_bytes:usize,pub dfa_bytes:usize,pub result_bytes:usize,
}
impl Default for SourceSearchLimitConfig {
    fn default()->Self {Self {paragraphs:50_000,blocks:50_000,segments:100_000,scalars:250_000,
        decomposed_scalars:1_000_000,query_bytes:4096,matches:10_000,reported_points:250_000,
        pattern_bytes:2*1024*1024,dfa_bytes:2*1024*1024,result_bytes:4*1024*1024}}
}
#[derive(Clone,Copy,Debug,Default,Eq,PartialEq)]
pub struct SourceSearchLimits(SourceSearchLimitConfig);
impl SourceSearchLimits {
    /// # Errors
    /// Explicitly intersects a request maximum with the already validated server budget.
    pub fn restrict_match_limit(self,maximum:usize)->Result<Self,E>{
        if maximum==0||maximum>SourceSearchLimitConfig::default().matches{return Err(E::Limit);}
        Self::new(SourceSearchLimitConfig{matches:self.0.matches.min(maximum),..self.0})
    }
    #[must_use] pub const fn maximum_query_bytes(self)->usize{self.0.query_bytes}
    #[must_use] pub const fn maximum_result_bytes(self)->usize{self.0.result_bytes}
    /// # Errors
    /// Rejects zero/over-ceiling limits; never silently clamps a request.
    pub fn new(config:SourceSearchLimitConfig)->Result<Self,E> {
        let ceiling=SourceSearchLimitConfig::default();
        for (n,max) in [(config.paragraphs,ceiling.paragraphs),(config.blocks,ceiling.blocks),(config.segments,ceiling.segments),
            (config.scalars,ceiling.scalars),(config.decomposed_scalars,ceiling.decomposed_scalars),(config.query_bytes,ceiling.query_bytes),
            (config.matches,ceiling.matches),(config.reported_points,ceiling.reported_points),(config.pattern_bytes,ceiling.pattern_bytes),
            (config.dfa_bytes,ceiling.dfa_bytes),(config.result_bytes,ceiling.result_bytes)] {if n==0||n>max{return Err(E::Limit);}}
        Ok(Self(config))
    }
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceSearchMode {Literal,Regex}
#[derive(Clone,Copy,Serialize)]
pub struct SourceSearchQuery<'a> {pub query:&'a str,pub mode:SourceSearchMode,pub case_sensitive:bool,pub whole_word:bool,pub max_results:usize}
impl fmt::Debug for SourceSearchQuery<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceSearchQuery(<redacted>)")}}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceSearchError {
    #[error("SOURCE_SEARCH_LIMIT_EXCEEDED")] Limit,
    #[error("SOURCE_SEARCH_SOURCE_REJECTED")] Source,
    #[error("SEARCH_PATTERN_INVALID_OR_COMPILED_LIMIT")] Pattern,
    #[error("SOURCE_SEARCH_MAPPING_REJECTED")] Mapping,
    #[error("SEARCH_SCOPE_INVALID")] Scope,
    #[error("SOURCE_SEARCH_FILTER_INVALID")] Filter,
    #[error("SOURCE_SEARCH_STYLE_DEFINITION_REJECTED")] Definition,
    #[error("SOURCE_SEARCH_REVIEW_BODY_REJECTED")] Review,
    #[error("SOURCE_SEARCH_CURSOR_STALE_OR_INVALID")] Cursor,
    #[error("SOURCE_SEARCH_OUTPUT_LIMIT")] Output,
}
type E=SourceSearchError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSearchIndexReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub graph_sha256:[u8;32],pub index_sha256:[u8;32],
    pub normalization_unicode_version:(u8,u8,u8),pub paragraphs:usize,pub blocks:usize,pub text_elements:usize,
    pub original_scalars:usize,pub normalized_scalars:usize,pub decomposed_scalars:usize,pub control_or_opaque_barriers:usize,
    pub skipped_unmapped_source_paragraphs:usize,pub source_opaque_nodes:usize,
    pub whole_document_visibility_and_search_qualified:bool,pub edit_or_service_access_authority:bool,
}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceSearchPiece {pub text_anchor:SourceAnchorHandle,pub atom_index:u32,pub start_scalar:u32,pub end_scalar:u32}
impl fmt::Debug for SourceSearchPiece {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceSearchPiece(<redacted>)")}}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceSearchMatch {
    pub paragraph_anchor:SourceAnchorHandle,pub block_index:usize,pub start_normalized_scalar:usize,pub end_normalized_scalar:usize,
    pub pieces:Vec<SourceSearchPiece>,pub zero_width:bool,pub source_scalar_selection_exact:bool,
}
impl fmt::Debug for SourceSearchMatch {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceSearchMatch(<redacted>)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSearchResult {
    profile:&'static str,index:SourceSearchIndexReceipt,query_sha256:[u8;32],matches:Vec<SourceSearchMatch>,
    complete_within_indexed_blocks:bool,edit_or_execution_authority:bool,
    #[serde(skip)] output_limit:usize,
}
impl SourceSearchResult {
    /// # Errors
    /// Moves within this complete bounded match set, not a fresh search or service grant.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::Text(self.matches(),None),self.output_limit,request,context)
    }
    #[must_use] pub fn matches(&self)->&[SourceSearchMatch] {&self.matches}
    #[must_use] pub const fn index_receipt(&self)->&SourceSearchIndexReceipt {&self.index}
    #[must_use] pub const fn query_sha256(&self)->[u8;32] {self.query_sha256}
    /// # Errors
    /// Rejects excessive response size, never returns a truncated match set.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {
        let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.output_limit};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)
    }
}
#[derive(Clone,Copy)]
struct Point {segment:usize,atom:u32,scalar:u32}
struct Unit {ch:char,origins:Vec<usize>}
struct Block {paragraph:SourceAnchorHandle,text:String,offsets:Vec<usize>,units:Vec<Unit>}
pub struct SourceTextIndex<'a> {
    original:&'a ImportedDocumentStructure,limits:SourceSearchLimits,receipt:SourceSearchIndexReceipt,
    segments:Vec<SourceAnchorHandle>,points:Vec<Point>,usage:Vec<(usize,usize)>,blocks:Vec<Block>,
}
impl fmt::Debug for SourceTextIndex<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceTextIndex(<redacted>; mapped_source_only)")}}
impl ImportedDocumentStructure {
    /// Fresh whole source reconstruction, then reuse existing source XML trees.
    /// # Errors
    /// Rejects stale source, invalid maps and finite limits; no partial index.
    pub fn source_text_index(&self,fresh:&[u8],limits:SourceSearchLimits)->Result<SourceTextIndex<'_>,E> {
        self.verify_source(fresh).map_err(|_|E::Source)?;extract::build(self,limits)
    }
}
impl SourceTextIndex<'_> {
    #[must_use] pub const fn receipt(&self)->&SourceSearchIndexReceipt {&self.receipt}
    /// # Errors
    /// Checks current supplied bytes against the original whole source, not an ACL grant.
    pub fn verify_source(&self,fresh:&[u8])->Result<(),E> {self.original.verify_source(fresh).map(|_|()).map_err(|_|E::Source)}
    /// Search NFC indexed blocks. Literal queries are NFC; regex syntax is kept
    /// exactly as supplied. Unicode simple casefold/word boundaries use regex.
    /// Results are leftmost non-overlapping, including bounded zero-width matches.
    /// # Errors
    /// No truncation: query/compiler/result/provenance overflow rejects the result.
    pub fn find(&self,query:SourceSearchQuery<'_>)->Result<SourceSearchResult,E> {
        self.find_selected(query,None)
    }
    fn find_selected(&self,query:SourceSearchQuery<'_>,selected:Option<&BTreeSet<domain_ir::LogicalId>>)->Result<SourceSearchResult,E> {
        self.find_filtered(query,selected,None)
    }
    fn find_filtered(&self,query:SourceSearchQuery<'_>,selected:Option<&BTreeSet<domain_ir::LogicalId>>,accept:Option<&dyn Fn(&BTreeSet<usize>)->bool>)->Result<SourceSearchResult,E> {
        self.find_windowed(query,selected,accept,None)
    }
    fn find_windowed(&self,query:SourceSearchQuery<'_>,selected:Option<&BTreeSet<domain_ir::LogicalId>>,accept:Option<&dyn Fn(&BTreeSet<usize>)->bool>,
        windows:Option<&std::collections::BTreeMap<usize,(usize,usize)>>)->Result<SourceSearchResult,E> {
        self.find_windowed_captured(query,selected,accept,windows,None)
    }
    fn find_windowed_captured(&self,query:SourceSearchQuery<'_>,selected:Option<&BTreeSet<domain_ir::LogicalId>>,accept:Option<&dyn Fn(&BTreeSet<usize>)->bool>,
        windows:Option<&std::collections::BTreeMap<usize,(usize,usize)>>,mut capture:Option<&mut dyn captures::CaptureSink>)->Result<SourceSearchResult,E> {
        use unicode_normalization::UnicodeNormalization as _;
        let limits=self.limits.0;
        if query.query.is_empty()||query.query.len()>limits.query_bytes||query.max_results==0||query.max_results>limits.matches{return Err(E::Limit);}
        let pattern=match query.mode {SourceSearchMode::Literal=>regex::escape(&query.query.nfc().collect::<String>()),SourceSearchMode::Regex=>query.query.to_owned()};
        let pattern=if query.whole_word {format!(r"\b(?:{pattern})\b")}else{pattern};
        let expression=RegexBuilder::new(&pattern).unicode(true).case_insensitive(!query.case_sensitive)
            .size_limit(limits.pattern_bytes).dfa_size_limit(limits.dfa_bytes).nest_limit(128).build().map_err(|_|E::Pattern)?;
        if let Some(sink)=capture.as_deref_mut(){sink.compiled(&expression)?;}
        let request=serde_json::to_vec(&(self.receipt.profile,query)).map_err(|_|E::Mapping)?;
        self.scan_compiled_windowed(&expression,Sha256::digest(request).into(),query.max_results,selected,accept,windows,capture)
    }
    // Shared finite scanner. Only validated internal callers can supply compiled expressions.
    fn scan_compiled_windowed(&self,expression:&regex::Regex,query_sha256:[u8;32],max_results:usize,selected:Option<&BTreeSet<domain_ir::LogicalId>>,
        accept:Option<&dyn Fn(&BTreeSet<usize>)->bool>,windows:Option<&std::collections::BTreeMap<usize,(usize,usize)>>,
        mut capture:Option<&mut dyn captures::CaptureSink>)->Result<SourceSearchResult,E>{
        let limits=self.limits.0;if max_results==0||max_results>limits.matches{return Err(E::Limit);}
        let mut matches=Vec::new();let mut reported=0usize;
        for (block_index,block) in self.blocks.iter().enumerate() {
            if selected.is_some_and(|set|!set.contains(&block.paragraph.opaque_handle)){continue;}
            let (offset,window)=if let Some(windows)=windows {
                let Some(&(a,b))=windows.get(&block_index)else{continue};
                let start=*block.offsets.get(a).ok_or(E::Mapping)?;let end=*block.offsets.get(b).ok_or(E::Mapping)?;
                if start>end{return Err(E::Mapping);}(start,block.text.get(start..end).ok_or(E::Mapping)?)
            }else{(0,block.text.as_str())};
            for scanned in captures::scan(expression,window,capture.is_some()) {
                let found=scanned.whole().ok_or(E::Mapping)?;
                let start=block.offsets.binary_search(&(offset+found.start())).map_err(|_|E::Mapping)?;
                let end=block.offsets.binary_search(&(offset+found.end())).map_err(|_|E::Mapping)?;
                let mut origins=BTreeSet::new();
                for unit in &block.units[start..end] {for &origin in &unit.origins {origins.insert(origin);}}
                if accept.is_some_and(|predicate|!predicate(&origins)){continue;}
                if matches.len()>=max_results{return Err(E::Limit);}
                reported=reported.checked_add(origins.len()).filter(|n|*n<=limits.reported_points).ok_or(E::Limit)?;
                let mut pieces:Vec<SourceSearchPiece>=Vec::new();let mut exact=start!=end;
                for origin in origins {
                    let (first,last)=self.usage[origin];if first<start||last>=end {exact=false;}
                    let point=self.points[origin];let anchor=self.segments.get(point.segment).ok_or(E::Mapping)?;
                    if let Some(last)=pieces.last_mut() {if &last.text_anchor==anchor&&last.atom_index==point.atom&&last.end_scalar==point.scalar {last.end_scalar+=1;continue;}}
                    pieces.push(SourceSearchPiece {text_anchor:anchor.clone(),atom_index:point.atom,start_scalar:point.scalar,end_scalar:point.scalar+1});
                }
                matches.push(SourceSearchMatch {paragraph_anchor:block.paragraph.clone(),block_index,start_normalized_scalar:start,end_normalized_scalar:end,
                    pieces,zero_width:start==end,source_scalar_selection_exact:exact});
                if let Some(sink)=capture.as_deref_mut(){sink.matched(scanned.captures().ok_or(E::Mapping)?)?;}
            }
        }
        let result=SourceSearchResult {profile:self.receipt.profile,index:self.receipt.clone(),query_sha256,matches,
            complete_within_indexed_blocks:true,edit_or_execution_authority:false,output_limit:limits.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:limits.result_bytes};serde_json::to_writer(&mut count,&result).map_err(|_|E::Output)?;Ok(result)
    }
}
struct Output {bytes:Option<Vec<u8>>,length:usize,maximum:usize}
impl io::Write for Output {
    fn write(&mut self,bytes:&[u8])->io::Result<usize> {
        self.length=self.length.checked_add(bytes.len()).filter(|n|*n<=self.maximum).ok_or_else(||io::Error::other("source search output bound"))?;
        if let Some(out)=&mut self.bytes {out.try_reserve(bytes.len()).map_err(|_|io::Error::other("source search allocation bound"))?;out.extend_from_slice(bytes);}Ok(bytes.len())
    }
    fn flush(&mut self)->io::Result<()> {Ok(())}
}
