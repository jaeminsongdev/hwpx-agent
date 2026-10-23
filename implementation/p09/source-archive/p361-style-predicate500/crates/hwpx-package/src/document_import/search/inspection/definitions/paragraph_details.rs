//! Predicates on the existing typed paragraph declaration. Neither branch is native precedence.
use super::*;
use crate::{CompatibleHeading,Heading,ParagraphLayout,ParagraphStyle};

macro_rules! choices {
    ($name:ident,$native:ident,[$($value:ident),+])=>{
        #[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
        #[serde(rename_all="snake_case")]
        pub enum $name {$($value),+}
        impl $name {fn native(self)->crate::$native {match self {$(Self::$value=>crate::$native::$value),+}}}
    }
}
choices!(DefinitionVerticalAlignment,VerticalAlignment,[Baseline,Top,Center,Bottom]);
choices!(DefinitionWordBreak,WordBreak,[KeepWord,BreakWord,Hyphenation]);
choices!(DefinitionLineWrap,LineWrap,[Break,Squeeze,Keep]);
choices!(DefinitionMeasurementUnit,MeasurementUnit,[Character,HwpUnit]);
choices!(DefinitionLineSpacingType,LineSpacingType,[Percent,Fixed,BetweenLines,AtLeast]);
choices!(DefinitionHeadingType,HeadingType,[None,Outline,Number,Bullet]);

#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum DefinitionTextDirection {Absent,LeftToRight,RightToLeft}
impl DefinitionTextDirection {
    fn native(self)->Option<crate::TextDirection> {match self {Self::Absent=>None,
        Self::LeftToRight=>Some(crate::TextDirection::LeftToRight),Self::RightToLeft=>Some(crate::TextDirection::RightToLeft)}}
}

#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct DefinitionMeasurement {pub value:i32,pub unit:DefinitionMeasurementUnit}
impl DefinitionMeasurement {fn native(self)->crate::HwpValue {crate::HwpValue {value:self.value,unit:self.unit.native()}}}

#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct DefinitionLineSpacing {pub spacing_type:DefinitionLineSpacingType,pub value:i32,pub unit:DefinitionMeasurementUnit}
impl DefinitionLineSpacing {
    fn valid(self)->bool {self.spacing_type!=DefinitionLineSpacingType::Percent||(0..=500).contains(&self.value)}
    fn native(self)->crate::LineSpacing {crate::LineSpacing {spacing_type:self.spacing_type.native(),value:self.value,unit:self.unit.native()}}
}

#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceParagraphLayoutFilter {
    pub indent:Option<DefinitionMeasurement>,pub left:Option<DefinitionMeasurement>,pub right:Option<DefinitionMeasurement>,
    pub previous:Option<DefinitionMeasurement>,pub next:Option<DefinitionMeasurement>,pub line_spacing:Option<DefinitionLineSpacing>,
}
impl SourceParagraphLayoutFilter {
    fn valid(self)->bool {self!=Self::default()&&self.line_spacing.is_none_or(DefinitionLineSpacing::valid)}
    fn matches(&self,layout:&ParagraphLayout)->bool {
        [(self.indent,layout.margin.intent),(self.left,layout.margin.left),(self.right,layout.margin.right),
            (self.previous,layout.margin.previous),(self.next,layout.margin.next)].into_iter().all(|(q,v)|q.is_none_or(|q|q.native()==v))
            &&self.line_spacing.is_none_or(|q|q.native()==layout.line_spacing)
    }
}

#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct DefinitionHeading {pub heading_type:DefinitionHeadingType,pub id_ref:u32,pub level:u8}
impl DefinitionHeading {
    fn valid(self)->bool {self.level<=9&&match self.heading_type {
        DefinitionHeadingType::None=>self.id_ref==0&&self.level==0,DefinitionHeadingType::Outline=>self.id_ref==0,
        DefinitionHeadingType::Number|DefinitionHeadingType::Bullet=>self.id_ref>0}}
    fn native(self)->Heading {Heading {heading_type:self.heading_type.native(),id_ref:self.id_ref,level:self.level}}
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceParagraphHeadingFilter {
    Direct {heading:DefinitionHeading},
    MetaTag {current:Option<DefinitionHeading>,fallback:Option<DefinitionHeading>},
}
impl SourceParagraphHeadingFilter {
    fn valid(self)->bool {match self {Self::Direct {heading}=>heading.valid(),Self::MetaTag {current,fallback}=>
        (current.is_some()||fallback.is_some())&&current.is_none_or(DefinitionHeading::valid)&&fallback.is_none_or(DefinitionHeading::valid)}}
    fn matches(self,heading:CompatibleHeading)->bool {match(self,heading) {
        (Self::Direct {heading:query},CompatibleHeading::Direct(value))=>query.native()==value,
        (Self::MetaTag {current:query,fallback:qf},CompatibleHeading::MetaTag {current,fallback})=>
            query.is_none_or(|q|q.native()==current)&&qf.is_none_or(|q|q.native()==fallback),_=>false}}
}

/// All predicates are AND. False, zero, absent text direction and signed offsets remain values.
/// Layout/heading branches are explicit source declarations, never a chosen rendering branch.
#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceParagraphDetailFilter {
    pub tab_property_id_ref:Option<u32>,pub condense:Option<u8>,pub font_line_height:Option<bool>,pub snap_to_grid:Option<bool>,
    pub suppress_line_numbers:Option<bool>,pub checked:Option<bool>,pub text_direction:Option<DefinitionTextDirection>,
    pub vertical_alignment:Option<DefinitionVerticalAlignment>,pub heading:Option<SourceParagraphHeadingFilter>,
    pub latin_word:Option<DefinitionWordBreak>,pub non_latin_word:Option<DefinitionWordBreak>,pub widow_orphan:Option<bool>,
    pub keep_with_next:Option<bool>,pub keep_lines:Option<bool>,pub page_break_before:Option<bool>,pub line_wrap:Option<DefinitionLineWrap>,
    pub auto_spacing_english:Option<bool>,pub auto_spacing_number:Option<bool>,
    pub current_layout:Option<SourceParagraphLayoutFilter>,pub fallback_layout:Option<SourceParagraphLayoutFilter>,
    pub border_fill_id_ref:Option<u32>,pub border_offset_left:Option<i32>,pub border_offset_right:Option<i32>,
    pub border_offset_top:Option<i32>,pub border_offset_bottom:Option<i32>,pub border_connect:Option<bool>,pub border_ignore_margin:Option<bool>,
    #[serde(skip_serializing_if="Option::is_none")]
    pub border_definition:Option<border_details::SourceBorderDefinitionFilter>,
}
impl SourceParagraphDetailFilter {
    /// # Errors
    /// Rejects empty predicates/branches and values the original typed model cannot admit.
    pub fn validate(self)->Result<(),E> {
        if let Some(filter)=self.border_definition {filter.validate()?;}
        if self==Self::default()||self.condense.is_some_and(|v|v>75)||self.non_latin_word==Some(DefinitionWordBreak::Hyphenation)
            ||self.current_layout.is_some_and(|v|!v.valid())||self.fallback_layout.is_some_and(|v|!v.valid())||self.heading.is_some_and(|v|!v.valid()) {
            return Err(E::Filter);
        }Ok(())
    }
    pub(super) fn matches(&self,style:&ParagraphStyle,border:Option<&crate::BorderFill>)->bool {
        let b=style.break_settings;
        !self.tab_property_id_ref.is_some_and(|v|v!=style.tab_property_id_ref)&&!self.condense.is_some_and(|v|v!=style.condense)
            &&!self.font_line_height.is_some_and(|v|v!=style.font_line_height)&&!self.snap_to_grid.is_some_and(|v|v!=style.snap_to_grid)
            &&!self.suppress_line_numbers.is_some_and(|v|v!=style.suppress_line_numbers)&&!self.checked.is_some_and(|v|v!=style.checked)
            &&!self.text_direction.is_some_and(|v|v.native()!=style.text_direction)&&!self.vertical_alignment.is_some_and(|v|v.native()!=style.vertical_alignment)
            &&!self.heading.is_some_and(|v|!v.matches(style.heading))
            &&!self.latin_word.is_some_and(|v|v.native()!=b.latin_word)&&!self.non_latin_word.is_some_and(|v|v.native()!=b.non_latin_word)
            &&!self.widow_orphan.is_some_and(|v|v!=b.widow_orphan)&&!self.keep_with_next.is_some_and(|v|v!=b.keep_with_next)
            &&!self.keep_lines.is_some_and(|v|v!=b.keep_lines)&&!self.page_break_before.is_some_and(|v|v!=b.page_break_before)
            &&!self.line_wrap.is_some_and(|v|v.native()!=b.line_wrap)
            &&!self.auto_spacing_english.is_some_and(|v|v!=style.auto_spacing.e_asian_english)&&!self.auto_spacing_number.is_some_and(|v|v!=style.auto_spacing.e_asian_number)
            &&!self.current_layout.as_ref().is_some_and(|v|!v.matches(&style.layout.current))&&!self.fallback_layout.as_ref().is_some_and(|v|!v.matches(&style.layout.fallback))
            &&!self.border_fill_id_ref.is_some_and(|v|v!=style.border.border_fill_id_ref)
            &&!self.border_offset_left.is_some_and(|v|v!=style.border.offset_left)&&!self.border_offset_right.is_some_and(|v|v!=style.border.offset_right)
            &&!self.border_offset_top.is_some_and(|v|v!=style.border.offset_top)&&!self.border_offset_bottom.is_some_and(|v|v!=style.border.offset_bottom)
            &&!self.border_connect.is_some_and(|v|v!=style.border.connect)&&!self.border_ignore_margin.is_some_and(|v|v!=style.border.ignore_margin)
            &&self.border_definition.as_ref().is_none_or(|query|border.is_some_and(|value|query.matches(value)))
    }
}
