//! Named PARA/CHAR declarations and their exact typed resources, not body occurrence/application semantics.
use super::{ImportedDocumentCatalog,ImportedCatalogDefinition,ImportedCatalogKind};
use domain_ir::{LogicalId,PropertyValue,SourceAnchorHandle};
use serde::{Deserialize,Serialize};
use sha2::{Digest as _,Sha256};
use std::{collections::BTreeMap,fmt,io::Write};
use thiserror::Error;
pub const NAMED_STYLE_NAME_RESOLUTION_PROFILE:&str="hwpx-agent.source-named-style-declaration-resolution/v1";
// The request hash also consumes private names/catalog metadata not emitted in the response.
// Keep this finite fixed ceiling separate from the server's smaller public response byte budget.
const MAX_BINDING_BYTES:usize=4*1024*1024;
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceNamedStyleKind{Paragraph,Character}
impl SourceNamedStyleKind{fn native(self)->&'static str{match self{Self::Paragraph=>"PARA",Self::Character=>"CHAR"}}}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceNamedStyleNameAxis{NativeName,EnglishName}
impl SourceNamedStyleNameAxis{fn attribute(self)->&'static str{match self{Self::NativeName=>"name",Self::EnglishName=>"engName"}}}
#[derive(Clone,Copy,Serialize)]
pub struct SourceNamedStyleNameQuery<'a>{pub query:&'a str,pub replacement:&'a str,pub regex:bool,pub case_sensitive:bool,pub whole_word:bool,
    pub kind:SourceNamedStyleKind,pub name_axis:SourceNamedStyleNameAxis}
impl fmt::Debug for SourceNamedStyleNameQuery<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceNamedStyleNameQuery(<redacted>)")}}
#[derive(Clone,Copy,Debug)]
pub struct SourceNamedStyleNameLimits{maximum_mappings:usize,query_bytes:usize,regex_bytes:usize,result_bytes:usize}
impl Default for SourceNamedStyleNameLimits{fn default()->Self{Self{maximum_mappings:128,query_bytes:4096,regex_bytes:1024*1024,result_bytes:4*1024*1024}}}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceNamedStyleNameError{
    #[error("NAMED_STYLE_NAME_PATTERN_REJECTED")]Pattern,#[error("NAMED_STYLE_NAME_LIMIT")]Limit,
    #[error("NAMED_STYLE_NAME_NO_MATCHES")]NoMatches,#[error("NAMED_STYLE_NAME_NO_CHANGE")]NoChange,
    #[error("NAMED_STYLE_NAME_TARGET_MISSING")]MissingTarget,#[error("NAMED_STYLE_NAME_TARGET_AMBIGUOUS")]AmbiguousTarget,
    #[error("NAMED_STYLE_NAME_ORIGINAL_BINDING_REJECTED")]Binding,
}
type E=SourceNamedStyleNameError;
impl SourceNamedStyleNameLimits{
    #[must_use]pub const fn maximum_result_bytes(self)->usize{self.result_bytes}
    /// # Errors
    /// Positive server limits can only restrict the fixed128/4096/1MiB/4MiB ceilings.
    pub fn new(maximum_mappings:usize,query_bytes:usize,regex_bytes:usize,result_bytes:usize)->Result<Self,E>{
        if maximum_mappings==0||maximum_mappings>128||query_bytes==0||query_bytes>4096||regex_bytes==0||regex_bytes>1024*1024||result_bytes==0||result_bytes>4*1024*1024{return Err(E::Limit);}
        Ok(Self{maximum_mappings,query_bytes,regex_bytes,result_bytes})
    }
}
impl SourceNamedStyleNameQuery<'_>{
    /// # Errors
    /// Names/pattern are nonempty, bounded, free of control characters and explicitly typed.
    pub fn validate(self,limits:SourceNamedStyleNameLimits)->Result<(),E>{
        if self.query.len()>limits.query_bytes||self.replacement.len()>limits.query_bytes{return Err(E::Limit);}
        if self.query.is_empty()||self.replacement.is_empty()||self.query.chars().chain(self.replacement.chars()).any(char::is_control){return Err(E::Pattern);}Ok(())
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceNamedStyleResourceReference{pub native_id:u32,pub source_anchor:SourceAnchorHandle}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceNamedStyleDeclaration{
    pub native_style_id:u32,pub kind:SourceNamedStyleKind,pub source_anchor:SourceAnchorHandle,
    pub character_property:SourceNamedStyleResourceReference,pub paragraph_property:SourceNamedStyleResourceReference,
    pub next_named_style:SourceNamedStyleResourceReference,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceNamedStyleNameResolutionReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_catalog_sha256:[u8;32],pub request_sha256:[u8;32],
    pub kind:SourceNamedStyleKind,pub name_axis:SourceNamedStyleNameAxis,pub matched_declarations:usize,pub changed_mappings:usize,
    pub all_original_declaration_resources_bound:bool,pub body_occurrences_or_target_semantics_qualified:bool,
    pub current_access_execution_or_publication_authority:bool,
}
#[derive(Serialize)]
pub struct SourceNamedStyleNameResolution{receipt:SourceNamedStyleNameResolutionReceipt,from:Vec<SourceNamedStyleDeclaration>,target:SourceNamedStyleDeclaration,#[serde(skip)]maximum_bytes:usize}
impl fmt::Debug for SourceNamedStyleNameResolution{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceNamedStyleNameResolution(<redacted>; declarations_not_body_semantics)")}}
impl SourceNamedStyleNameResolution{
    #[must_use]pub const fn receipt(&self)->&SourceNamedStyleNameResolutionReceipt{&self.receipt}
    #[must_use]pub fn from_declarations(&self)->&[SourceNamedStyleDeclaration]{&self.from}
    #[must_use]pub const fn target_declaration(&self)->&SourceNamedStyleDeclaration{&self.target}
    /// # Errors
    /// Bounded declaration metadata only. This cannot reconstruct or execute a document mutation.
    pub fn canonical_json(&self)->Result<Vec<u8>,E>{let mut out=Bound{hash:Sha256::new(),bytes:Some(Vec::new()),length:0,maximum:self.maximum_bytes};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Limit)?;out.bytes.ok_or(E::Limit)}
}
impl ImportedDocumentCatalog<'_, '_, '_>{
    /// # Errors
    /// Resolve original named declarations/resources. Never identify body uses by equal charPr/style IDs.
    pub fn resolve_named_style_replacements(&self,query:SourceNamedStyleNameQuery<'_>,limits:SourceNamedStyleNameLimits)->Result<SourceNamedStyleNameResolution,E>{
        query.validate(limits)?;
        let pattern=if query.regex{query.query.to_owned()}else{regex::escape(query.query)};
        let pattern=if query.whole_word{format!(r"\b(?:{pattern})\b")}else{pattern};
        let matcher=regex::RegexBuilder::new(&pattern).case_insensitive(!query.case_sensitive).size_limit(limits.regex_bytes).dfa_size_limit(limits.regex_bytes).build().map_err(|_|E::Pattern)?;
        // One map for all typed relationships. No per-declaration whole catalog scan or header reparse.
        let mut by_id=BTreeMap::new();for definition in self.definitions(){if by_id.insert(&definition.catalog_id,definition).is_some(){return Err(E::Binding);}}
        let(mut sources,mut target)=(BTreeMap::new(),None);let(mut matched,mut target_count)=(0usize,0usize);
        for definition in self.definitions().iter().filter(|d|d.kind==ImportedCatalogKind::NamedStyle){
            if text(definition,"type")?!=query.kind.native(){continue;}let name=text(definition,query.name_axis.attribute())?;
            if name==query.replacement{target_count+=1;if target_count==1{target=Some(definition);}}
            if let Some(found)=matcher.find(name){if found.is_empty(){return Err(E::Pattern);}if matched>=limits.maximum_mappings{return Err(E::Limit);}matched+=1;
                if sources.insert(definition.native_id,definition).is_some(){return Err(E::Binding);}}
        }
        if matched==0{return Err(E::NoMatches);}let target=match target_count{0=>return Err(E::MissingTarget),1=>target.ok_or(E::Binding)?,_=>return Err(E::AmbiguousTarget)};
        sources.remove(&target.native_id);if sources.is_empty(){return Err(E::NoChange);}
        let from=sources.into_values().map(|d|declaration(d,query.kind,&by_id)).collect::<Result<Vec<_>,E>>()?;
        let target=declaration(target,query.kind,&by_id)?;
        let request_sha256=hash(&(NAMED_STYLE_NAME_RESOLUTION_PROFILE,self.receipt(),query,&from,&target),MAX_BINDING_BYTES)?;
        let receipt=SourceNamedStyleNameResolutionReceipt{profile:NAMED_STYLE_NAME_RESOLUTION_PROFILE,source_package_sha256:self.receipt().source_package_sha256,
            source_catalog_sha256:self.receipt().graph_sha256,request_sha256,kind:query.kind,name_axis:query.name_axis,matched_declarations:matched,changed_mappings:from.len(),
            all_original_declaration_resources_bound:true,body_occurrences_or_target_semantics_qualified:false,current_access_execution_or_publication_authority:false};
        let out=SourceNamedStyleNameResolution{receipt,from,target,maximum_bytes:limits.result_bytes};let _=hash(&out,limits.result_bytes)?;Ok(out)
    }
}
fn text<'a>(definition:&'a ImportedCatalogDefinition,key:&str)->Result<&'a str,E>{match definition.native_attributes.iter().find_map(|(k,v)|(k==key).then_some(v)){Some(PropertyValue::Text(v))=>Ok(v),_=>Err(E::Binding)}}
fn resource(definition:&ImportedCatalogDefinition,key:&str,kind:ImportedCatalogKind,index:&BTreeMap<&LogicalId,&ImportedCatalogDefinition>)->Result<SourceNamedStyleResourceReference,E>{
    let Some(PropertyValue::Id(id))=definition.relationships.iter().find_map(|(k,v)|(k==key).then_some(v))else{return Err(E::Binding)};
    let actual=index.get(id).filter(|d|d.kind==kind).ok_or(E::Binding)?;
    Ok(SourceNamedStyleResourceReference{native_id:actual.native_id,source_anchor:actual.source_anchor.clone()})
}
fn declaration(d:&ImportedCatalogDefinition,kind:SourceNamedStyleKind,index:&BTreeMap<&LogicalId,&ImportedCatalogDefinition>)->Result<SourceNamedStyleDeclaration,E>{
    if d.kind!=ImportedCatalogKind::NamedStyle||text(d,"type")?!=kind.native(){return Err(E::Binding);}
    Ok(SourceNamedStyleDeclaration{native_style_id:d.native_id,kind,source_anchor:d.source_anchor.clone(),
        character_property:resource(d,"charPrIDRef",ImportedCatalogKind::CharacterProperty,index)?,paragraph_property:resource(d,"paraPrIDRef",ImportedCatalogKind::ParagraphProperty,index)?,
        next_named_style:resource(d,"nextStyleIDRef",ImportedCatalogKind::NamedStyle,index)?})
}
struct Bound{hash:Sha256,bytes:Option<Vec<u8>>,length:usize,maximum:usize}
impl Write for Bound{
    fn write(&mut self,b:&[u8])->std::io::Result<usize>{let n=self.length.checked_add(b.len()).filter(|n|*n<=self.maximum).ok_or_else(||std::io::Error::other("named_style_resolution_limit"))?;
        self.hash.update(b);if let Some(bytes)=&mut self.bytes{bytes.extend_from_slice(b);}self.length=n;Ok(b.len())}
    fn flush(&mut self)->std::io::Result<()>{Ok(())}
}
fn hash(value:&impl Serialize,maximum:usize)->Result<[u8;32],E>{let mut out=Bound{hash:Sha256::new(),bytes:None,length:0,maximum};serde_json::to_writer(&mut out,value).map_err(|_|E::Limit)?;Ok(out.hash.finalize().into())}
