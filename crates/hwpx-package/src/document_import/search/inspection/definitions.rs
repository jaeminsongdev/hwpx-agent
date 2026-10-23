//! Original typed definitions, explicitly chosen source axes, never an inferred cascade.
pub mod resolved;
pub mod details;
pub mod paragraph_details;
pub mod border_details;
pub mod font_details;
pub mod tab_details;
mod last_predicate;
use super::*;
use std::collections::BTreeMap;
use crate::{BinaryProperty,CharacterStyleCatalog,ParagraphStyleCatalog,Color,HorizontalAlignment,
    document_import::fields::semantics::catalog::{source_style_catalogs_for_search,ImportedCatalogKind as CatalogKind}};
use domain_ir::PropertyValue;
pub const SOURCE_DEFINITION_STYLE_PROFILE:&str="hwpx-agent.source-definition-style-search/v1";

#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="axis",content="declaration_id",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceParagraphStyleTarget {ParagraphProperty(u32),ParagraphStyle(u32)}
impl SourceParagraphStyleTarget {
    #[must_use] pub const fn declaration_id(self)->u32 {match self {Self::ParagraphProperty(id)|Self::ParagraphStyle(id)=>id}}
    #[must_use] pub const fn attribute(self)->&'static str {match self {Self::ParagraphProperty(_)=>"paraPrIDRef",Self::ParagraphStyle(_)=>"styleIDRef"}}
}

#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum CharacterDefinitionSource {RunProperty,TextStyle,NamedStyle}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum ParagraphDefinitionSource {DirectProperty,NamedStyle}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum DefinitionAlignment {Justify,Left,Right,Center,Distribute,DistributeSpace}
impl DefinitionAlignment {fn native(self)->HorizontalAlignment {match self {
    Self::Justify=>HorizontalAlignment::Justify,Self::Left=>HorizontalAlignment::Left,Self::Right=>HorizontalAlignment::Right,
    Self::Center=>HorizontalAlignment::Center,Self::Distribute=>HorizontalAlignment::Distribute,Self::DistributeSpace=>HorizontalAlignment::DistributeSpace}}}
#[derive(Clone,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceDefinitionStyleFilter {
    pub character_source:Option<CharacterDefinitionSource>,pub bold:Option<bool>,pub italic:Option<bool>,
    pub height_hwpunit:Option<u32>,pub text_rgb:Option<[u8;3]>,
    pub paragraph_source:Option<ParagraphDefinitionSource>,pub alignment:Option<DefinitionAlignment>,
    #[serde(skip_serializing_if="Option::is_none")]
    pub character_details:Option<details::SourceCharacterDetailFilter>,
    #[serde(skip_serializing_if="Option::is_none")]
    pub paragraph_details:Option<paragraph_details::SourceParagraphDetailFilter>,
    #[serde(skip_serializing_if="Option::is_none")]
    pub font_details:Option<font_details::SourceFontDetailsFilter>,
    #[serde(skip_serializing_if="Option::is_none")]
    pub tab_details:Option<tab_details::SourceTabDefinitionFilter>,
}
impl SourceDefinitionStyleFilter {
    /// # Errors
    /// Every requested value needs an explicit source axis; unused axes are rejected.
    pub fn validate(&self)->Result<(),E> {
        if let Some(details)=&self.character_details {details.validate()?;}
        if let Some(details)=&self.paragraph_details {details.validate()?;}
        if let Some(details)=&self.font_details {details.validate()?;}
        if let Some(details)=&self.tab_details {details.validate()?;}
        let characters=self.bold.is_some()||self.italic.is_some()||self.height_hwpunit.is_some()||self.text_rgb.is_some()||self.character_details.is_some()||self.font_details.is_some();
        let paragraphs=self.alignment.is_some()||self.paragraph_details.is_some()||self.tab_details.is_some();
        if self.character_source.is_some()!=characters||self.paragraph_source.is_some()!=paragraphs
            ||!characters&&!paragraphs{return Err(E::Filter);}Ok(())
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceStyleDefinitionReceipt {
    pub profile:&'static str,pub source_index_sha256:[u8;32],pub inspection_sha256:[u8;32],pub header_sha256:[u8;32],
    pub named_definitions:usize,pub character_definitions:usize,pub paragraph_definitions:usize,pub indexed_text_segments:usize,
    pub present_reference_bindings:usize,pub missing_run_references:usize,pub missing_text_references:usize,
    pub missing_paragraph_references:usize,pub missing_named_style_references:usize,
    pub all_present_indexed_references_resolved:bool,pub implicit_cascade_or_hidden_visibility_qualified:bool,
}
#[derive(Clone,Copy)]
struct BoundReferences {run:Option<usize>,text:Option<usize>,paragraph:Option<usize>,named_character:Option<usize>,named_paragraph:Option<usize>}
pub struct SourceStyleDefinitionIndex<'a,'text,'source> {
    inspection:&'a SourceInspectionIndex<'text,'source>,characters:CharacterStyleCatalog,paragraphs:ParagraphStyleCatalog,
    refs:Vec<BoundReferences>,receipt:SourceStyleDefinitionReceipt,
    character_declarations:BTreeMap<u32,SourceAnchorHandle>,
    paragraph_declarations:BTreeMap<(CatalogKind,u32),SourceAnchorHandle>,
}
impl fmt::Debug for SourceStyleDefinitionIndex<'_, '_,'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceStyleDefinitionIndex(<redacted>; explicit_axes_only)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceDefinitionStyleResult {
    profile:&'static str,index:SourceSearchIndexReceipt,scope:SourceSearchScopeReceipt,definitions:SourceStyleDefinitionReceipt,
    request_sha256:[u8;32],matches:SourceSearchResult,full_effective_style_search_or_execution_authority:bool,
    #[serde(skip)] output_limit:usize,
}
impl SourceDefinitionStyleResult {
    /// # Errors
    /// Definition predicates remain part of the retained result identity.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::Text(self.matches.matches(),None),self.output_limit,request,context)
    }
    #[must_use] pub const fn index_receipt(&self)->&SourceSearchIndexReceipt {&self.index}
    #[must_use] pub const fn scope_receipt(&self)->&SourceSearchScopeReceipt {&self.scope}
    #[must_use] pub const fn request_sha256(&self)->[u8;32] {self.request_sha256}
    #[must_use] pub const fn matches(&self)->&SourceSearchResult {&self.matches}
    /// # Errors
    /// The entire wrapper and result must fit without truncation.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.output_limit};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)}
}
impl<'text,'source> SourceInspectionIndex<'text,'source> {
    /// # Errors
    /// Uses the unchanged typed header readers, named links and dense ID checks.
    /// Missing explicit axes remain absent; dangling present refs reject the index.
    pub fn resolve_style_definitions(&self)->Result<SourceStyleDefinitionIndex<'_,'text,'source>,E> {
        let source=self.text.original.source();
        let(definitions,characters,paragraphs)=source_style_catalogs_for_search(source).map_err(|_|E::Definition)?;
        let ids:BTreeMap<_,_>=definitions.iter().map(|d|(&d.catalog_id,(d.kind,d.native_id))).collect();
        let mut named=BTreeMap::new();
        for definition in definitions.iter().filter(|d|d.kind==CatalogKind::NamedStyle) {
            let lookup=|name:&str,kind:CatalogKind|->Result<u32,E> {
                let target=definition.relationships.iter().find(|(key,_)|*key==name).map(|(_,v)|v).ok_or(E::Definition)?;
                let PropertyValue::Id(id)=target else{return Err(E::Definition)};
                let(actual,value)=ids.get(id).ok_or(E::Definition)?;
                if *actual!=kind{return Err(E::Definition);}Ok(*value)
            };
            if named.insert(definition.native_id,(lookup("charPrIDRef",CatalogKind::CharacterProperty)?,
                lookup("paraPrIDRef",CatalogKind::ParagraphProperty)?)).is_some(){return Err(E::Definition);}
        }
        let character=|id:u32|->Result<usize,E>{let index=id as usize;if !characters.styles.get(index).is_some_and(|s|s.id==id){return Err(E::Definition);}Ok(index)};
        let paragraph=|id:u32|->Result<usize,E>{let index=id as usize;if !paragraphs.styles.get(index).is_some_and(|s|s.id==id){return Err(E::Definition);}Ok(index)};
        let mut refs=Vec::new();let mut present=0;
        for style in &self.styles {
            present+=[style.run_character_property,style.text_character_style,style.paragraph_property,style.paragraph_style].iter().filter(|v|v.is_some()).count();
            let pair=style.paragraph_style.map(|id|named.get(&id).copied().ok_or(E::Definition)).transpose()?;
            refs.push(BoundReferences {run:style.run_character_property.map(character).transpose()?,text:style.text_character_style.map(character).transpose()?,
                paragraph:style.paragraph_property.map(paragraph).transpose()?,
                named_character:pair.map(|(c,_)|character(c)).transpose()?,named_paragraph:pair.map(|(_,p)|paragraph(p)).transpose()?});
        }
        let header=source.parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").ok_or(E::Definition)?;
        let receipt=SourceStyleDefinitionReceipt {profile:SOURCE_DEFINITION_STYLE_PROFILE,source_index_sha256:self.text.receipt.index_sha256,
            inspection_sha256:self.receipt.inspection_sha256,header_sha256:header.anchor().fingerprint_sha256,
            named_definitions:named.len(),character_definitions:characters.styles.len(),paragraph_definitions:paragraphs.styles.len(),indexed_text_segments:refs.len(),
            present_reference_bindings:present,missing_run_references:self.styles.iter().filter(|s|s.run_character_property.is_none()).count(),
            missing_text_references:self.styles.iter().filter(|s|s.text_character_style.is_none()).count(),
            missing_paragraph_references:self.styles.iter().filter(|s|s.paragraph_property.is_none()).count(),
            missing_named_style_references:self.styles.iter().filter(|s|s.paragraph_style.is_none()).count(),
            all_present_indexed_references_resolved:true,implicit_cascade_or_hidden_visibility_qualified:false};
        drop(ids);
        let mut character_declarations=BTreeMap::new();let mut paragraph_declarations=BTreeMap::new();
        for d in definitions {
            match d.kind {
                CatalogKind::CharacterProperty=>{character_declarations.insert(d.native_id,d.source_anchor);},
                CatalogKind::ParagraphProperty=>{paragraph_declarations.insert((d.kind,d.native_id),d.source_anchor);},
                CatalogKind::NamedStyle if d.native_attributes.iter().any(|(key,value)|key=="type"&&matches!(value,PropertyValue::Text(kind)if kind=="PARA"))=>{
                    paragraph_declarations.insert((d.kind,d.native_id),d.source_anchor);
                },_=>{}
            }
        }
        Ok(SourceStyleDefinitionIndex {inspection:self,characters,paragraphs,refs,receipt,character_declarations,paragraph_declarations})
    }
}
impl SourceStyleDefinitionIndex<'_, '_,'_> {
    pub(in crate::document_import::search) fn paragraph_declaration(&self,target:SourceParagraphStyleTarget)->Result<SourceAnchorHandle,E> {
        let kind=match target {SourceParagraphStyleTarget::ParagraphProperty(_)=>CatalogKind::ParagraphProperty,SourceParagraphStyleTarget::ParagraphStyle(_)=>CatalogKind::NamedStyle};
        self.paragraph_declarations.get(&(kind,target.declaration_id())).cloned().ok_or(E::Definition)
    }
    pub(in crate::document_import::search) fn character_declaration(&self,id:u32)->Result<SourceAnchorHandle,E> {
        if !self.characters.styles.get(id as usize).is_some_and(|s|s.id==id){return Err(E::Definition);}
        self.character_declarations.get(&id).cloned().ok_or(E::Definition)
    }
    pub(in crate::document_import::search) fn matcher<'a>(&'a self,filter:&'a SourceDefinitionStyleFilter)->Result<impl Fn(&BTreeSet<usize>)->bool+'a,E> {
        let limits=self.inspection.text.limits.0;
        let fonts=filter.font_details.as_ref().map(|query|query.prepare(&self.characters,limits.query_bytes,limits.pattern_bytes,limits.dfa_bytes)).transpose()?;
        let tabs=filter.tab_details.as_ref().map(|query|query.prepare(self.inspection.text.original.source(),&self.paragraphs)).transpose()?;
        let previous=last_predicate::LastPredicate::default();
        // The source index and one immutable filter are borrowed for this operation only.
        // Cache only the last selected pair: O(1) storage even for adversarial alternating styles.
        Ok(move |points:&BTreeSet<usize>|!points.is_empty()&&points.iter().all(|p| {
            let refs=self.refs[self.inspection.text.points[*p].segment];
            let character=match filter.character_source {Some(CharacterDefinitionSource::RunProperty)=>refs.run,
                Some(CharacterDefinitionSource::TextStyle)=>refs.text,Some(CharacterDefinitionSource::NamedStyle)=>refs.named_character,None=>None};
            let paragraph=match filter.paragraph_source {Some(ParagraphDefinitionSource::DirectProperty)=>refs.paragraph,
                Some(ParagraphDefinitionSource::NamedStyle)=>refs.named_paragraph,None=>None};
            previous.test((character,paragraph),||self.accepts((character,paragraph),filter,fonts.as_ref(),tabs.as_ref()))
        }))
    }
    #[must_use] pub const fn receipt(&self)->&SourceStyleDefinitionReceipt {&self.receipt}
    /// # Errors
    /// Every contributing source scalar must satisfy the explicitly selected definitions.
    pub fn find(&self,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,filter:SourceDefinitionStyleFilter)->Result<SourceDefinitionStyleResult,E> {
        filter.validate()?;let text=self.inspection.text;let(scope,selected)=text.resolve_search_scope(scope)?;
        let accept=self.matcher(&filter)?;
        let matches=text.find_filtered(query,Some(&selected),Some(&accept))?;
        drop(accept);
        let binding=serde_json::to_vec(&(SOURCE_DEFINITION_STYLE_PROFILE,&self.receipt,scope.scope_sha256,query,&filter)).map_err(|_|E::Mapping)?;
        let result=SourceDefinitionStyleResult {profile:SOURCE_DEFINITION_STYLE_PROFILE,index:text.receipt.clone(),scope,definitions:self.receipt.clone(),
            request_sha256:Sha256::digest(binding).into(),matches,full_effective_style_search_or_execution_authority:false,output_limit:text.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:result.output_limit};serde_json::to_writer(&mut count,&result).map_err(|_|E::Output)?;Ok(result)
    }
    fn accepts(&self,(character,paragraph):(Option<usize>,Option<usize>),filter:&SourceDefinitionStyleFilter,fonts:Option<&font_details::PreparedFontDetails>,tabs:Option<&tab_details::PreparedTabDefinitions>)->bool {
        if filter.character_source.is_some() {
            let Some(style)=character.and_then(|i|self.characters.styles.get(i))else{return false};
            if filter.bold.is_some_and(|v|v!=matches!(style.effects.bold,BinaryProperty::On))
                ||filter.italic.is_some_and(|v|v!=matches!(style.effects.italic,BinaryProperty::On))
                ||filter.height_hwpunit.is_some_and(|v|v!=style.height)
                ||filter.text_rgb.is_some_and(|[r,g,b]|style.text_color!=Color::Rgb(r,g,b))
                ||filter.character_details.as_ref().is_some_and(|details|!details.matches(style,self.border_definition(style.border_fill_id_ref)))
                ||fonts.is_some_and(|prepared|!prepared.matches(&style.font_refs)){return false;}
        }
        if filter.paragraph_source.is_some() {
            let Some(style)=paragraph.and_then(|i|self.paragraphs.styles.get(i))else{return false};
            if filter.alignment.is_some_and(|v|v.native()!=style.horizontal_alignment)
                ||filter.paragraph_details.as_ref().is_some_and(|details|!details.matches(style,self.border_definition(Some(style.border.border_fill_id_ref))))
                ||tabs.is_some_and(|prepared|!prepared.matches(style.tab_property_id_ref)){return false;}
        }true
    }
    fn border_definition(&self,id:Option<u32>)->Option<&crate::BorderFill> {
        // The unchanged typed reader validates dense one-based border IDs at index construction.
        let id=id?;self.paragraphs.border_fills.get(id.checked_sub(1)? as usize).filter(|value|value.id==id)
    }
}
