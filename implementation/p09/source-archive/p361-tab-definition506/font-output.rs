//! Result-only projection. Input/canonical Serialize remains lossless; text predicates leave results as a binding.
//! These serializers grant no access, execution, embedding or native authority.
use super::*;
use super::super::{SourceDefinitionStyleFilter,resolved::SourceResolvedStyleFilter};
use crate::document_import::search::reviews::selector::styles::SourceReviewStyleFilter;
use serde::{Serialize,Serializer,ser::{SerializeStruct,Error as _}};
use sha2::{Digest as _,Sha256};
use std::io::Write;

#[derive(Serialize)]
struct FontBinding {profile:&'static str,request_sha256:[u8;32],languages:Vec<&'static str>}
fn binding(query:&SourceFontDetailsFilter)->Result<FontBinding,&'static str> {
    struct Hash {sha:Sha256,bytes:usize}
    impl Write for Hash {
        fn write(&mut self,value:&[u8])->std::io::Result<usize> {
            let size=self.bytes.checked_add(value.len()).filter(|n|*n<=256*1024).ok_or_else(||std::io::Error::other("font_binding_limit"))?;
            self.bytes=size;self.sha.update(value);Ok(value.len())
        }
        fn flush(&mut self)->std::io::Result<()> {Ok(())}
    }
    let mut out=Hash {sha:Sha256::new(),bytes:0};serde_json::to_writer(&mut out,query).map_err(|_|"font_binding_rejected")?;
    let languages=query.slots().into_iter().filter_map(|(language,filter)|filter.as_ref().map(|_|match language {LanguageSlot::Hangul=>"hangul",
        LanguageSlot::Latin=>"latin",LanguageSlot::Hanja=>"hanja",LanguageSlot::Japanese=>"japanese",LanguageSlot::Other=>"other",
        LanguageSlot::Symbol=>"symbol",LanguageSlot::User=>"user"})).collect();
    Ok(FontBinding {profile:"hwpx-agent.source-font-definition-filter-binding/v1",request_sha256:out.sha.finalize().into(),languages})
}
struct DefinitionView<'a>(&'a SourceDefinitionStyleFilter);
impl Serialize for DefinitionView<'_> {
    fn serialize<S:Serializer>(&self,serializer:S)->Result<S::Ok,S::Error> {
        let filter=self.0;if filter.font_details.is_none(){return filter.serialize(serializer);}
        let mut value=serializer.serialize_struct("SourceDefinitionStyleFilterResult",8+usize::from(filter.character_details.is_some())+usize::from(filter.paragraph_details.is_some()))?;
        value.serialize_field("character_source",&filter.character_source)?;value.serialize_field("bold",&filter.bold)?;
        value.serialize_field("italic",&filter.italic)?;value.serialize_field("height_hwpunit",&filter.height_hwpunit)?;
        value.serialize_field("text_rgb",&filter.text_rgb)?;value.serialize_field("paragraph_source",&filter.paragraph_source)?;value.serialize_field("alignment",&filter.alignment)?;
        if let Some(details)=&filter.character_details{value.serialize_field("character_details",details)?;}
        if let Some(details)=&filter.paragraph_details{value.serialize_field("paragraph_details",details)?;}
        value.serialize_field("font_details",&binding(filter.font_details.as_ref().ok_or_else(||S::Error::custom("font_filter_binding"))?).map_err(S::Error::custom)?)?;
        value.end()
    }
}
/// # Errors
/// Only result wrappers should call this; requests keep their ordinary lossless Serialize.
pub fn review<S:Serializer>(filter:&SourceReviewStyleFilter,serializer:S)->Result<S::Ok,S::Error> {
    match filter {
        SourceReviewStyleFilter::Declared(_)=>filter.serialize(serializer),
        SourceReviewStyleFilter::Definition(filter)=>{
            let mut value=serializer.serialize_struct("SourceReviewStyleFilter",2)?;value.serialize_field("kind","definition")?;
            value.serialize_field("filter",&DefinitionView(filter))?;value.end()
        }
    }
}
struct ReviewView<'a>(&'a SourceReviewStyleFilter);
impl Serialize for ReviewView<'_> {fn serialize<S:Serializer>(&self,serializer:S)->Result<S::Ok,S::Error>{review(self.0,serializer)}}
/// # Errors
/// An absent optional predicate remains JSON null; a present predicate keeps its original tag.
pub fn optional_review<S:Serializer>(filter:&Option<SourceReviewStyleFilter>,serializer:S)->Result<S::Ok,S::Error> {
    match filter {None=>serializer.serialize_none(),Some(filter)=>serializer.serialize_some(&ReviewView(filter))}
}
/// # Errors
/// Source names/binary query strings are replaced by their complete, bounded input binding in result JSON.
pub fn resolved<S:Serializer>(filter:&SourceResolvedStyleFilter,serializer:S)->Result<S::Ok,S::Error> {
    if filter.font_details.is_none(){return filter.serialize(serializer);}
    let mut value=serializer.serialize_struct("SourceResolvedStyleFilterResult",6+usize::from(filter.character_details.is_some())+usize::from(filter.paragraph_details.is_some()))?;
    value.serialize_field("bold",&filter.bold)?;value.serialize_field("italic",&filter.italic)?;
    value.serialize_field("height_hwpunit",&filter.height_hwpunit)?;value.serialize_field("text_rgb",&filter.text_rgb)?;value.serialize_field("alignment",&filter.alignment)?;
    if let Some(details)=&filter.character_details{value.serialize_field("character_details",details)?;}
    if let Some(details)=&filter.paragraph_details{value.serialize_field("paragraph_details",details)?;}
    value.serialize_field("font_details",&binding(filter.font_details.as_ref().ok_or_else(||S::Error::custom("font_filter_binding"))?).map_err(S::Error::custom)?)?;value.end()
}
