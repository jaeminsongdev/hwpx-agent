//! Conditions on the exact paragraph-referenced tab declaration, not layout or rendered stops.
use super::*;
use crate::{TabDefinition,TabDefinitionCatalogReader,TabItem,TabStop,TabStopAlignment,TabPositionUnit};
use details::DefinitionLine;
use crate::document_import::ImportedSourcePackage;

#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum DefinitionTabAlignment {Left,Right,Center,Decimal}
impl DefinitionTabAlignment {
    fn native(self)->TabStopAlignment {match self {Self::Left=>TabStopAlignment::Left,Self::Right=>TabStopAlignment::Right,
        Self::Center=>TabStopAlignment::Center,Self::Decimal=>TabStopAlignment::Decimal}}
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum DefinitionTabUnit {Character,HwpUnit}
impl DefinitionTabUnit {fn native(self)->TabPositionUnit {match self {Self::Character=>TabPositionUnit::Character,Self::HwpUnit=>TabPositionUnit::HwpUnit}}}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceTabUnitFilter {Absent {},Present {unit:DefinitionTabUnit}}

#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceTabItemFilter {
    pub position:Option<i32>,pub alignment:Option<DefinitionTabAlignment>,pub leader:Option<DefinitionLine>,pub unit:Option<SourceTabUnitFilter>,
}
impl SourceTabItemFilter {
    fn valid(&self)->bool {*self!=Self::default()&&self.position.is_none_or(|v|v>=0)}
    fn matches(&self,item:&TabItem)->bool {
        self.position.is_none_or(|v|v==item.position)&&self.alignment.is_none_or(|v|v.native()==item.alignment)
            &&self.leader.is_none_or(|v|v.native()==item.leader)&&self.unit.is_none_or(|q|match q {
                SourceTabUnitFilter::Absent {}=>item.unit.is_none(),SourceTabUnitFilter::Present {unit}=>item.unit==Some(unit.native())})
    }
}
/// A branch is mandatory. Neither current nor fallback is selected as the rendered winner.
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceTabStopFilter {
    Direct {item:SourceTabItemFilter},
    HwpUnitChar {current:Option<SourceTabItemFilter>,fallback:Option<SourceTabItemFilter>},
}
impl SourceTabStopFilter {
    fn valid(&self)->bool {match self {Self::Direct {item}=>item.valid(),Self::HwpUnitChar {current,fallback}=>
        (current.is_some()||fallback.is_some())&&current.as_ref().is_none_or(SourceTabItemFilter::valid)&&fallback.as_ref().is_none_or(SourceTabItemFilter::valid)}}
    fn matches(&self,stop:&TabStop)->bool {match (self,stop) {
        (Self::Direct {item},TabStop::Direct(value))=>item.matches(value),
        (Self::HwpUnitChar {current,fallback},TabStop::HwpUnitChar {current:c,fallback:f})=>
            current.as_ref().is_none_or(|q|q.matches(c))&&fallback.as_ref().is_none_or(|q|q.matches(f)),_=>false}}
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceIndexedTabStopFilter {pub index:u32,pub stop:SourceTabStopFilter}

/// All requested settings and indexed stops are conjunctive. Explicit stop_count=0 is meaningful.
#[derive(Clone,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceTabDefinitionFilter {
    pub auto_tab_left:Option<bool>,pub auto_tab_right:Option<bool>,pub stop_count:Option<u32>,
    #[serde(default,skip_serializing_if="Vec::is_empty")]
    pub stops:Vec<SourceIndexedTabStopFilter>,
}
impl SourceTabDefinitionFilter {
    /// # Errors
    /// Bound both requested work and source-supported stop ordinals before original access.
    pub fn validate(&self)->Result<(),E> {
        const MAX:usize=crate::TabDefinitionLimits::HARD_MAX_STOPS;
        if self==&Self::default()||self.stops.len()>MAX||self.stop_count.is_some_and(|v|v as usize>MAX){return Err(E::Filter);}
        let mut previous=None;
        for filter in &self.stops {
            if filter.index as usize>=MAX||self.stop_count.is_some_and(|count|filter.index>=count)
                ||previous.is_some_and(|i|filter.index<=i)||!filter.stop.valid(){return Err(E::Filter);}
            previous=Some(filter.index);
        }Ok(())
    }
    fn matches(&self,value:&TabDefinition)->bool {
        self.auto_tab_left.is_none_or(|v|v==value.auto_tab_left)&&self.auto_tab_right.is_none_or(|v|v==value.auto_tab_right)
            &&self.stop_count.is_none_or(|v|v as usize==value.stops.len())
            &&self.stops.iter().all(|q|value.stops.get(q.index as usize).is_some_and(|stop|q.stop.matches(stop)))
    }
    pub(super) fn prepare(&self,source:&ImportedSourcePackage,paragraphs:&ParagraphStyleCatalog)->Result<PreparedTabDefinitions,E> {
        self.validate()?;
        let xml=source.parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").and_then(|p|p.xml()).ok_or(E::Definition)?;
        let catalog=xml.with_source_bytes(|bytes|TabDefinitionCatalogReader::read(bytes,Default::default())).map_err(|_|E::Definition)?;
        // Dense zero-based IDs and finite stop work are validated by the unchanged typed reader.
        if paragraphs.references.tab_property_ids.len()!=catalog.definitions.len()
            ||paragraphs.references.tab_property_ids.iter().zip(&catalog.definitions).any(|(id,value)|*id!=value.id){return Err(E::Definition);}
        let mut matches=Vec::new();matches.try_reserve_exact(catalog.definitions.len()).map_err(|_|E::Limit)?;
        matches.extend(catalog.definitions.iter().map(|value|self.matches(value)));Ok(PreparedTabDefinitions {matches})
    }
}
pub(super) struct PreparedTabDefinitions {matches:Vec<bool>}
impl PreparedTabDefinitions {
    pub(super) fn matches(&self,id:u32)->bool {self.matches.get(id as usize).copied().unwrap_or(false)}
}
