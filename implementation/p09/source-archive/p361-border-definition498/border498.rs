//! Predicates on the exact border definition referenced by the selected character/paragraph axis.
//! No render winner, inferred absent border, gradient/image support, or service authority.
use super::*;
use details::{DefinitionColor,DefinitionLine};
use crate::{BorderFill,BorderLine,Slash,WindowBrush};

macro_rules! choices {
    ($name:ident,$native:ident,[$($value:ident),+])=>{
        #[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
        #[serde(rename_all="snake_case")]
        pub enum $name {$($value),+}
        impl $name {fn native(self)->crate::$native {match self {$(Self::$value=>crate::$native::$value),+}}}
    }
}
choices!(DefinitionBorderWidth,BorderWidth,[Mm0_1,Mm0_12,Mm0_15,Mm0_2,Mm0_25,Mm0_3,Mm0_4,Mm0_5,Mm0_6,Mm0_7,Mm1_0,Mm1_5,Mm2_0,Mm3_0,Mm4_0,Mm5_0]);
choices!(DefinitionCenterLine,CenterLine,[None,Vertical,Horizontal,Cross]);
choices!(DefinitionSlashType,SlashType,[None,Center,CenterBelow,CenterAbove,All]);
choices!(DefinitionHatchStyle,HatchStyle,[Horizontal,Vertical,BackSlash,Slash,Cross,CrossDiagonal]);

#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceBorderLineFilter {pub line_type:Option<DefinitionLine>,pub width:Option<DefinitionBorderWidth>,pub rgb:Option<[u8;3]>}
impl SourceBorderLineFilter {
    fn valid(&self)->bool {*self!=Self::default()}
    fn matches(&self,value:&BorderLine)->bool {
        self.line_type.is_none_or(|v|v.native()==value.line_type)&&self.width.is_none_or(|v|v.native()==value.width)
            &&self.rgb.is_none_or(|[r,g,b]|value.color==Color::Rgb(r,g,b))
    }
}
#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceSlashFilter {pub slash_type:Option<DefinitionSlashType>,pub crooked:Option<bool>,pub is_counter:Option<bool>}
impl SourceSlashFilter {
    fn valid(&self)->bool {*self!=Self::default()}
    fn matches(&self,value:&Slash)->bool {
        self.slash_type.is_none_or(|v|v.native()==value.slash_type)&&self.crooked.is_none_or(|v|v==value.crooked)
            &&self.is_counter.is_none_or(|v|v==value.is_counter)
    }
}
/// Absent attribute, present `none` color and no predicate are three distinct states.
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceHatchColorFilter {Absent,Present {color:DefinitionColor}}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceHatchStyleFilter {Absent,Present {style:DefinitionHatchStyle}}
#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceWindowBrushFilter {
    pub face_color:Option<DefinitionColor>,pub hatch_color:Option<SourceHatchColorFilter>,
    pub hatch_style:Option<SourceHatchStyleFilter>,pub alpha:Option<u8>,
}
impl SourceWindowBrushFilter {
    fn valid(&self)->bool {*self!=Self::default()}
    fn matches(&self,value:&WindowBrush)->bool {
        self.face_color.is_none_or(|v|v.native()==value.face_color)&&self.alpha.is_none_or(|v|v==value.alpha)
            &&self.hatch_color.is_none_or(|query|match query {SourceHatchColorFilter::Absent=>value.hatch_color.is_none(),
                SourceHatchColorFilter::Present {color}=>value.hatch_color==Some(color.native())})
            &&self.hatch_style.is_none_or(|query|match query {SourceHatchStyleFilter::Absent=>value.hatch_style.is_none(),
                SourceHatchStyleFilter::Present {style}=>value.hatch_style==Some(style.native())})
    }
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceFillBrushFilter {Absent,Window {filter:SourceWindowBrushFilter}}

/// Every requested property is conjunctive. Border references are not definition identities.
#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceBorderDefinitionFilter {
    pub three_d:Option<bool>,pub shadow:Option<bool>,pub center_line:Option<DefinitionCenterLine>,pub break_cell_separate_line:Option<bool>,
    pub slash:Option<SourceSlashFilter>,pub back_slash:Option<SourceSlashFilter>,
    pub left:Option<SourceBorderLineFilter>,pub right:Option<SourceBorderLineFilter>,pub top:Option<SourceBorderLineFilter>,
    pub bottom:Option<SourceBorderLineFilter>,pub diagonal:Option<SourceBorderLineFilter>,pub fill_brush:Option<SourceFillBrushFilter>,
}
impl SourceBorderDefinitionFilter {
    /// # Errors
    /// Rejects an empty border or nested predicate before any original source access.
    pub fn validate(&self)->Result<(),E> {
        if *self==Self::default()||[self.slash,self.back_slash].iter().flatten().any(|q|!q.valid())
            ||[self.left,self.right,self.top,self.bottom,self.diagonal].iter().flatten().any(|q|!q.valid())
            ||matches!(self.fill_brush,Some(SourceFillBrushFilter::Window {filter})if !filter.valid()) {return Err(E::Filter);}Ok(())
    }
    pub(super) fn matches(&self,value:&BorderFill)->bool {
        self.three_d.is_none_or(|v|v==value.three_d)&&self.shadow.is_none_or(|v|v==value.shadow)
            &&self.center_line.is_none_or(|v|v.native()==value.center_line)&&self.break_cell_separate_line.is_none_or(|v|v==value.break_cell_separate_line)
            &&self.slash.as_ref().is_none_or(|v|v.matches(&value.slash))&&self.back_slash.as_ref().is_none_or(|v|v.matches(&value.back_slash))
            &&self.left.as_ref().is_none_or(|v|v.matches(&value.left))&&self.right.as_ref().is_none_or(|v|v.matches(&value.right))
            &&self.top.as_ref().is_none_or(|v|v.matches(&value.top))&&self.bottom.as_ref().is_none_or(|v|v.matches(&value.bottom))
            &&self.diagonal.as_ref().is_none_or(|v|v.matches(&value.diagonal))
            &&self.fill_brush.as_ref().is_none_or(|query|match query {SourceFillBrushFilter::Absent=>value.fill_brush.is_none(),
                SourceFillBrushFilter::Window {filter}=>value.fill_brush.as_ref().is_some_and(|fill|filter.matches(&fill.window))})
    }
}
