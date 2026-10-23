//! Original language-local font definitions, never installed-font selection or activated embedding.
//! Source integration is unverified until the external003 execution boundary permits local validation.
pub mod output;
use super::*;
use crate::{CharacterStyleCatalog,FontFace,FontTypeInfo,SubstituteFont,LanguageSlot,LanguageValues};
use crate::document_import::fields::semantics::catalog::fonts::names::declared_matcher;
use regex::Regex;

macro_rules! choices {
    ($name:ident,$native:ident,[$($value:ident),+])=>{
        #[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
        #[serde(rename_all="snake_case")]
        pub enum $name {$($value),+}
        impl $name {fn native(self)->crate::$native {match self {$(Self::$value=>crate::$native::$value),+}}}
    }
}
choices!(DefinitionFontType,FontType,[Representative,TrueType,HancomFont]);
choices!(DefinitionFontFamily,FontFamily,[Unknown,Myungjo,Gothic,SansSerif,BrushScript,Decorative,NonRectMyungjo,NonRectGothic]);

#[derive(Clone,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct DeclaredFontNameQuery {pub query:String,pub regex:bool,pub case_sensitive:bool,pub whole_word:bool}
impl fmt::Debug for DeclaredFontNameQuery {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.debug_struct("DeclaredFontNameQuery").field("query_bytes",&self.query.len())
        .field("regex",&self.regex).field("case_sensitive",&self.case_sensitive).field("whole_word",&self.whole_word).finish()}
}
impl DeclaredFontNameQuery {
    fn compile(&self,limits:(usize,usize,usize))->Result<Regex,E> {
        let matcher=declared_matcher(&self.query,self.regex,self.case_sensitive,self.whole_word,limits.0,limits.1,limits.2)
            .map_err(|error|match error {crate::document_import::fields::semantics::catalog::fonts::names::FontNameResolutionError::Limit=>E::Limit,_=>E::Filter})?;
        if matcher.is_match(""){return Err(E::Filter);}Ok(matcher)
    }
}
fn name_matches(matcher:Option<&Regex>,value:&str)->Result<bool,E> {
    let Some(matcher)=matcher else{return Ok(true)};
    match matcher.find(value) {Some(hit)if hit.is_empty()=>Err(E::Filter),Some(_)=>Ok(true),None=>Ok(false)}
}

/// Absence and an exact declared string are different from no predicate; values never appear in Debug.
#[derive(Clone,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum OptionalFontTextFilter {Absent {},Present {value:String}}
impl fmt::Debug for OptionalFontTextFilter {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {match self {Self::Absent {}=>f.write_str("OptionalFontTextFilter(Absent)"),
        Self::Present {value}=>f.debug_struct("OptionalFontTextFilter(Present)").field("value_bytes",&value.len()).finish()}}
}
impl OptionalFontTextFilter {
    fn validate(&self)->Result<(),E> {if let Self::Present {value}=self {
        if value.is_empty()||value.len()>4096||value.chars().any(char::is_control){return Err(E::Filter);}
    }Ok(())}
    fn matches(&self,value:Option<&str>)->bool {match self {Self::Absent {}=>value.is_none(),Self::Present {value:query}=>value==Some(query.as_str())}}
}

#[derive(Clone,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceSubstituteFontFilter {
    pub face:Option<DeclaredFontNameQuery>,pub font_type:Option<DefinitionFontType>,pub binary_item_id_ref:Option<OptionalFontTextFilter>,
}
impl SourceSubstituteFontFilter {
    fn validate_shape(&self)->Result<(),E> {if self==&Self::default(){return Err(E::Filter);}
        if let Some(query)=&self.binary_item_id_ref{query.validate()?;}Ok(())}
    fn matches(&self,face:Option<&Regex>,value:&SubstituteFont)->Result<bool,E> {
        let matched=name_matches(face,&value.face)?;
        Ok(matched&&self.font_type.is_none_or(|v|v.native()==value.font_type)
            &&self.binary_item_id_ref.as_ref().is_none_or(|v|v.matches(value.binary_item_id_ref.as_deref())))
    }
}
#[derive(Clone,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceFontTypeInfoFilter {
    pub family:Option<DefinitionFontFamily>,pub serif_style:Option<OptionalFontTextFilter>,
    pub weight:Option<i32>,pub proportion:Option<i32>,pub contrast:Option<i32>,pub stroke_variation:Option<i32>,
    pub arm_style:Option<bool>,pub letterform:Option<bool>,pub midline:Option<bool>,pub x_height:Option<bool>,
}
impl SourceFontTypeInfoFilter {
    fn validate(&self)->Result<(),E> {if self==&Self::default(){return Err(E::Filter);}if let Some(query)=&self.serif_style{query.validate()?;}Ok(())}
    fn matches(&self,value:&FontTypeInfo)->bool {
        self.family.is_none_or(|v|v.native()==value.family)&&self.serif_style.as_ref().is_none_or(|v|v.matches(value.serif_style.as_deref()))
            &&self.weight.is_none_or(|v|v==value.weight)&&self.proportion.is_none_or(|v|v==value.proportion)
            &&self.contrast.is_none_or(|v|v==value.contrast)&&self.stroke_variation.is_none_or(|v|v==value.stroke_variation)
            &&self.arm_style.is_none_or(|v|v==matches!(value.arm_style,BinaryProperty::On))
            &&self.letterform.is_none_or(|v|v==matches!(value.letterform,BinaryProperty::On))
            &&self.midline.is_none_or(|v|v==matches!(value.midline,BinaryProperty::On))
            &&self.x_height.is_none_or(|v|v==matches!(value.x_height,BinaryProperty::On))
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceSubstituteFontPredicate {
    Absent {},Present {#[serde(skip_serializing_if="Option::is_none")] filter:Option<SourceSubstituteFontFilter>},
}
#[derive(Clone,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceFontTypeInfoPredicate {
    Absent {},Present {#[serde(skip_serializing_if="Option::is_none")] filter:Option<SourceFontTypeInfoFilter>},
}

/// These are declaration facts. `is_embedded`/binary IDs do not prove a file is present or activated.
#[derive(Clone,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceFontDefinitionFilter {
    pub face:Option<DeclaredFontNameQuery>,pub font_type:Option<DefinitionFontType>,pub is_embedded:Option<bool>,
    pub binary_item_id_ref:Option<OptionalFontTextFilter>,pub substitute:Option<SourceSubstituteFontPredicate>,pub type_info:Option<SourceFontTypeInfoPredicate>,
}
impl fmt::Debug for SourceFontDefinitionFilter {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.debug_struct("SourceFontDefinitionFilter(<redacted>)")
        .field("face",&self.face.is_some()).field("font_type",&self.font_type).field("is_embedded",&self.is_embedded)
        .field("binary_reference_predicate",&self.binary_item_id_ref.is_some()).field("substitute_predicate",&self.substitute.is_some())
        .field("type_info_predicate",&self.type_info.is_some()).finish()}
}
struct CompiledDefinition<'a> {query:&'a SourceFontDefinitionFilter,face:Option<Regex>,substitute_face:Option<Regex>}
impl<'a> CompiledDefinition<'a> {
    fn new(query:&'a SourceFontDefinitionFilter,limits:(usize,usize,usize))->Result<Self,E> {
        if query==&SourceFontDefinitionFilter::default(){return Err(E::Filter);}
        if let Some(value)=&query.binary_item_id_ref{value.validate()?;}
        if let Some(SourceFontTypeInfoPredicate::Present {filter:Some(filter)})=&query.type_info{filter.validate()?;}
        let face=query.face.as_ref().map(|q|q.compile(limits)).transpose()?;
        let substitute_face=if let Some(SourceSubstituteFontPredicate::Present {filter:Some(filter)})=&query.substitute {
            filter.validate_shape()?;filter.face.as_ref().map(|q|q.compile(limits)).transpose()?
        }else{None};
        Ok(Self {query,face,substitute_face})
    }
    fn matches(&self,value:&FontFace)->Result<bool,E> {
        // Observe any actual zero-width name hit even if another metadata predicate would be false.
        let face=name_matches(self.face.as_ref(),&value.face)?;
        let substitute=match &self.query.substitute {
            None=>true,Some(SourceSubstituteFontPredicate::Absent {})=>value.substitute.is_none(),
            Some(SourceSubstituteFontPredicate::Present {filter})=>match &value.substitute {None=>false,Some(value)=>match filter {
                None=>true,Some(filter)=>filter.matches(self.substitute_face.as_ref(),value)?}},
        };
        let type_info=match &self.query.type_info {
            None=>true,Some(SourceFontTypeInfoPredicate::Absent {})=>value.type_info.is_none(),
            Some(SourceFontTypeInfoPredicate::Present {filter})=>value.type_info.as_ref().is_some_and(|value|filter.as_ref().is_none_or(|query|query.matches(value))),
        };
        Ok(face&&substitute&&type_info&&self.query.font_type.is_none_or(|v|v.native()==value.font_type)
            &&self.query.is_embedded.is_none_or(|v|v==value.is_embedded)
            &&self.query.binary_item_id_ref.as_ref().is_none_or(|v|v.matches(value.binary_item_id_ref.as_deref())))
    }
}

#[derive(Clone,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceFontDetailsFilter {
    pub hangul:Option<SourceFontDefinitionFilter>,pub latin:Option<SourceFontDefinitionFilter>,pub hanja:Option<SourceFontDefinitionFilter>,
    pub japanese:Option<SourceFontDefinitionFilter>,pub other:Option<SourceFontDefinitionFilter>,pub symbol:Option<SourceFontDefinitionFilter>,pub user:Option<SourceFontDefinitionFilter>,
}
impl SourceFontDetailsFilter {
    fn slots(&self)->[(LanguageSlot,&Option<SourceFontDefinitionFilter>);7] {use LanguageSlot as L;
        [(L::Hangul,&self.hangul),(L::Latin,&self.latin),(L::Hanja,&self.hanja),(L::Japanese,&self.japanese),(L::Other,&self.other),(L::Symbol,&self.symbol),(L::User,&self.user)]}
    /// # Errors
    /// An explicit language selection and nonempty closed predicates are required before source reads.
    pub fn validate(&self)->Result<(),E> {
        if self==&Self::default(){return Err(E::Filter);}
        for(_,query)in self.slots(){if let Some(query)=query{CompiledDefinition::new(query,(4096,1024*1024,1024*1024))?;}}Ok(())
    }
    pub(super) fn prepare(&self,catalog:&CharacterStyleCatalog,query_bytes:usize,pattern_bytes:usize,dfa_bytes:usize)->Result<PreparedFontDetails,E> {
        if self==&Self::default(){return Err(E::Filter);}
        if query_bytes==0||pattern_bytes==0||dfa_bytes==0{return Err(E::Limit);}let mut result=PreparedFontDetails::default();
        result.languages.try_reserve_exact(7).map_err(|_|E::Limit)?;
        for(language,query)in self.slots(){let Some(query)=query else{continue};
            let group=catalog.font_faces.iter().find(|g|g.language==language).ok_or(E::Definition)?;
            if group.fonts.len()>crate::CharacterStyleLimits::HARD_MAX_FONTS_PER_LANGUAGE{return Err(E::Limit);}
            let compiled=CompiledDefinition::new(query,(query_bytes,pattern_bytes,dfa_bytes))?;
            let mut accepted=Vec::new();accepted.try_reserve_exact(group.fonts.len()).map_err(|_|E::Limit)?;
            for(index,value)in group.fonts.iter().enumerate(){if value.id as usize!=index{return Err(E::Definition);}accepted.push(compiled.matches(value)?);}
            result.languages.push((language,accepted)); // Regexes drop here, never retained in a scalar loop.
        }Ok(result)
    }
}
#[derive(Default)]
pub(super) struct PreparedFontDetails {languages:Vec<(LanguageSlot,Vec<bool>)>}
impl PreparedFontDetails {
    pub(super) fn matches(&self,refs:&LanguageValues<u32>)->bool {
        self.languages.iter().all(|(language,accepted)|{use LanguageSlot as L;
            let id=match language {L::Hangul=>refs.hangul,L::Latin=>refs.latin,L::Hanja=>refs.hanja,L::Japanese=>refs.japanese,
                L::Other=>refs.other,L::Symbol=>refs.symbol,L::User=>refs.user};
            accepted.get(id as usize)==Some(&true)
        })
    }
}
