//! Predicates on the existing typed source character declaration, not font substitution or rendering.
use super::*;
use crate::{CharacterStyle,LanguageValues};

macro_rules! choices {
    ($name:ident,$native:ident,[$($value:ident),+])=>{
        #[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
        #[serde(rename_all="snake_case")]
        pub enum $name {$($value),+}
        impl $name {pub(super) fn native(self)->crate::$native {match self {$(Self::$value=>crate::$native::$value),+}}}
    }
}
choices!(DefinitionUnderline,UnderlinePosition,[None,Bottom,Center,Top]);
choices!(DefinitionLine,LineType2,[None,Solid,Dot,Dash,DashDot,DashDotDot,LongDash,Circle,DoubleSlim,SlimThick,ThickSlim,SlimThickSlim]);
choices!(DefinitionOutline,LineType1,[None,Solid,Dot,Thick,Dash,DashDot,DashDotDot]);
choices!(DefinitionShadow,ShadowType,[None,Drop,Continuous]);
choices!(DefinitionEmphasis,EmphasisMark,[None,DotAbove,RingAbove,Tilde,Caron,Side,Colon,GraveAccent,AcuteAccent,Circumflex,Macron,HookAbove,DotBelow]);

#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",content="rgb",rename_all="snake_case",deny_unknown_fields)]
pub enum DefinitionColor {None,Rgb([u8;3])}
impl DefinitionColor {pub(super) fn native(self)->Color {match self {Self::None=>Color::None,Self::Rgb([r,g,b])=>Color::Rgb(r,g,b)}}}

/// An explicit absent declaration is different from no predicate.
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",content="id",rename_all="snake_case",deny_unknown_fields)]
pub enum DefinitionBorderFill {Absent,Reference(u32)}
impl DefinitionBorderFill {fn native(self)->Option<u32> {match self {Self::Absent=>None,Self::Reference(id)=>Some(id)}}}

#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceLanguagePredicates<T> {
    pub hangul:Option<T>,pub latin:Option<T>,pub hanja:Option<T>,pub japanese:Option<T>,
    pub other:Option<T>,pub symbol:Option<T>,pub user:Option<T>,
}
impl<T:Copy+Eq> SourceLanguagePredicates<T> {
    fn empty(&self)->bool {[self.hangul,self.latin,self.hanja,self.japanese,self.other,self.symbol,self.user].iter().all(Option::is_none)}
    fn matches(&self,values:&LanguageValues<T>)->bool {
        [(self.hangul,values.hangul),(self.latin,values.latin),(self.hanja,values.hanja),(self.japanese,values.japanese),
            (self.other,values.other),(self.symbol,values.symbol),(self.user,values.user)].into_iter().all(|(query,value)|query.is_none_or(|q|q==value))
    }
}

/// Every predicate is conjunctive. Explicit false, zero, absent and no-color are values.
/// Font IDs are original language-local declarations, never installed-font identity.
#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceCharacterDetailFilter {
    pub shade_color:Option<DefinitionColor>,pub use_font_space:Option<bool>,pub use_kerning:Option<bool>,
    pub emphasis:Option<DefinitionEmphasis>,pub border_fill:Option<DefinitionBorderFill>,
    pub underline_position:Option<DefinitionUnderline>,pub underline_shape:Option<DefinitionLine>,pub underline_color:Option<DefinitionColor>,
    pub strikeout_shape:Option<DefinitionLine>,pub strikeout_color:Option<DefinitionColor>,pub outline:Option<DefinitionOutline>,
    pub shadow_type:Option<DefinitionShadow>,pub shadow_color:Option<DefinitionColor>,pub shadow_offset_x:Option<i16>,pub shadow_offset_y:Option<i16>,
    pub emboss:Option<bool>,pub engrave:Option<bool>,pub superscript:Option<bool>,pub subscript:Option<bool>,
    pub font_refs:Option<SourceLanguagePredicates<u32>>,pub ratios:Option<SourceLanguagePredicates<u16>>,
    pub spacing:Option<SourceLanguagePredicates<i16>>,pub relative_sizes:Option<SourceLanguagePredicates<u16>>,pub offsets:Option<SourceLanguagePredicates<i16>>,
    #[serde(skip_serializing_if="Option::is_none")]
    pub border_definition:Option<border_details::SourceBorderDefinitionFilter>,
}
impl SourceCharacterDetailFilter {
    /// # Errors
    /// Empty objects, including any empty nested language selection, are not predicates.
    pub fn validate(self)->Result<(),E> {
        if let Some(filter)=self.border_definition {filter.validate()?;}
        if self==Self::default()||self.font_refs.is_some_and(|v|v.empty())||self.ratios.is_some_and(|v|v.empty())
            ||self.spacing.is_some_and(|v|v.empty())||self.relative_sizes.is_some_and(|v|v.empty())||self.offsets.is_some_and(|v|v.empty()) {
            return Err(E::Filter);
        }Ok(())
    }
    pub(super) fn matches(&self,style:&CharacterStyle,border:Option<&crate::BorderFill>)->bool {
        let e=&style.effects;
        !self.shade_color.is_some_and(|v|v.native()!=style.shade_color)
            &&!self.use_font_space.is_some_and(|v|v!=style.use_font_space)&&!self.use_kerning.is_some_and(|v|v!=style.use_kerning)
            &&!self.emphasis.is_some_and(|v|v.native()!=style.emphasis_mark)&&!self.border_fill.is_some_and(|v|v.native()!=style.border_fill_id_ref)
            &&!self.underline_position.is_some_and(|v|v.native()!=e.underline.position)&&!self.underline_shape.is_some_and(|v|v.native()!=e.underline.shape)
            &&!self.underline_color.is_some_and(|v|v.native()!=e.underline.color)&&!self.strikeout_shape.is_some_and(|v|v.native()!=e.strikeout.shape)
            &&!self.strikeout_color.is_some_and(|v|v.native()!=e.strikeout.color)&&!self.outline.is_some_and(|v|v.native()!=e.outline)
            &&!self.shadow_type.is_some_and(|v|v.native()!=e.shadow.shadow_type)&&!self.shadow_color.is_some_and(|v|v.native()!=e.shadow.color)
            &&!self.shadow_offset_x.is_some_and(|v|v!=e.shadow.offset_x)&&!self.shadow_offset_y.is_some_and(|v|v!=e.shadow.offset_y)
            &&!self.emboss.is_some_and(|v|v!=matches!(e.emboss,BinaryProperty::On))&& !self.engrave.is_some_and(|v|v!=matches!(e.engrave,BinaryProperty::On))
            &&!self.superscript.is_some_and(|v|v!=matches!(e.superscript,BinaryProperty::On))&& !self.subscript.is_some_and(|v|v!=matches!(e.subscript,BinaryProperty::On))
            &&!self.font_refs.is_some_and(|v|!v.matches(&style.font_refs))&& !self.ratios.is_some_and(|v|!v.matches(&style.ratios))
            &&!self.spacing.is_some_and(|v|!v.matches(&style.spacing))&& !self.relative_sizes.is_some_and(|v|!v.matches(&style.relative_sizes))
            &&!self.offsets.is_some_and(|v|!v.matches(&style.offsets))
            &&self.border_definition.as_ref().is_none_or(|query|border.is_some_and(|value|query.matches(value)))
    }
}
