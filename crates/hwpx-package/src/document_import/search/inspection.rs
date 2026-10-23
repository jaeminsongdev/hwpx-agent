//! Declared style references and closed structural control tags, not effective formatting.
pub mod definitions;
use super::*;
use super::scope::{SourceSearchScope,SourceSearchScopeReceipt};
use crate::{XmlElementToken,document_import::ImportedSourcePart};
use serde::Deserialize;
const HP:&str=crate::HANCOM_2020_PARAGRAPH_NAMESPACE;
pub const SOURCE_SEARCH_INSPECTION_PROFILE:&str="hwpx-agent.source-search-inspection/v1";

#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceDeclaredStyleFilter {
    pub paragraph_property:Option<u32>,pub paragraph_style:Option<u32>,
    pub run_character_property:Option<u32>,pub text_character_style:Option<u32>,
}
impl SourceDeclaredStyleFilter {
    #[must_use] pub fn is_empty(self)->bool {self==Self::default()}
    fn matches(self,actual:Self)->bool {[(self.paragraph_property,actual.paragraph_property),(self.paragraph_style,actual.paragraph_style),
        (self.run_character_property,actual.run_character_property),(self.text_character_style,actual.text_character_style)]
        .iter().all(|(q,v)|q.is_none()||q==v)}
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceControlKind {FieldBegin,FieldEnd,Footnote,Endnote,Bookmark,Table,Picture,Equation,Rectangle,Ellipse,
    Line,Arc,Polygon,Curve,Connector,AutoNumber,NewNumber,SectionProperties,TitleMark,IndexMark,Tab,LineBreak,
    Ole,Container,TextArt,Compose,Dutmal,Button,RadioButton,CheckBox,ComboBox,ListBox,Edit,ScrollBar,Video,
    MarkpenBegin,MarkpenEnd,Chart,UnknownObject,ColumnProperties,Header,Footer,PageNumberControl,PageHiding,PageNumber,
    HiddenComment,Hyphen,NonbreakingSpace,FullwidthSpace,CharacterValue,InsertBegin,InsertEnd,DeleteBegin,DeleteEnd,UnknownCharacter}
#[derive(Clone,Copy)]
enum Site {Run,Control,Text}
fn kind(node:&XmlElementToken,site:Site)->Option<SourceControlKind> {
    use SourceControlKind as K;
    if node.name().namespace()!=Some(HP){return None;}
    Some(match (site,node.name().local_name()) {
        (Site::Control,"fieldBegin")=>K::FieldBegin,(Site::Control,"fieldEnd")=>K::FieldEnd,(Site::Control,"footNote")=>K::Footnote,
        (Site::Control,"endNote")=>K::Endnote,(Site::Control,"bookmark")=>K::Bookmark,(Site::Control,"autoNum")=>K::AutoNumber,
        (Site::Control,"newNum")=>K::NewNumber,(Site::Control,"indexmark")=>K::IndexMark,(Site::Control,"colPr")=>K::ColumnProperties,
        (Site::Control,"header")=>K::Header,(Site::Control,"footer")=>K::Footer,(Site::Control,"pageNumCtrl")=>K::PageNumberControl,
        (Site::Control,"pageHiding")=>K::PageHiding,(Site::Control,"pageNum")=>K::PageNumber,(Site::Control,"hiddenComment")=>K::HiddenComment,
        (Site::Run,"tbl")=>K::Table,(Site::Run,"pic")=>K::Picture,(Site::Run,"equation")=>K::Equation,(Site::Run,"rect")=>K::Rectangle,
        (Site::Run,"ellipse")=>K::Ellipse,(Site::Run,"line")=>K::Line,(Site::Run,"arc")=>K::Arc,(Site::Run,"polygon")=>K::Polygon,
        (Site::Run,"curve")=>K::Curve,(Site::Run,"connectLine")=>K::Connector,(Site::Run,"secPr")=>K::SectionProperties,
        (Site::Run,"ole")=>K::Ole,(Site::Run,"container")=>K::Container,(Site::Run,"textart")=>K::TextArt,(Site::Run,"compose")=>K::Compose,
        (Site::Run,"dutmal")=>K::Dutmal,(Site::Run,"btn")=>K::Button,(Site::Run,"radioBtn")=>K::RadioButton,(Site::Run,"checkBtn")=>K::CheckBox,
        (Site::Run,"comboBox")=>K::ComboBox,(Site::Run,"listBox")=>K::ListBox,(Site::Run,"edit")=>K::Edit,(Site::Run,"scrollBar")=>K::ScrollBar,
        (Site::Run,"video")=>K::Video,(Site::Run,"chart")=>K::Chart,(Site::Run,"unknownObj")=>K::UnknownObject,
        (Site::Run|Site::Text,"markpenBegin")=>K::MarkpenBegin,(Site::Run|Site::Text,"markpenEnd")=>K::MarkpenEnd,
        (Site::Text,"titleMark")=>K::TitleMark,(Site::Text,"tab")=>K::Tab,(Site::Text,"lineBreak")=>K::LineBreak,
        (Site::Text,"hypen")=>K::Hyphen,(Site::Text,"nbSpace")=>K::NonbreakingSpace,(Site::Text,"fwSpace")=>K::FullwidthSpace,
        (Site::Text,"chval")=>K::CharacterValue,(Site::Text,"insertBegin")=>K::InsertBegin,(Site::Text,"insertEnd")=>K::InsertEnd,
        (Site::Text,"deleteBegin")=>K::DeleteBegin,(Site::Text,"deleteEnd")=>K::DeleteEnd,(Site::Text,"unknownch")=>K::UnknownCharacter,
        _=>return None})
}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceControlMatch {pub kind:SourceControlKind,pub paragraph_anchor:SourceAnchorHandle,pub control_anchor:SourceAnchorHandle}
impl fmt::Debug for SourceControlMatch {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceControlMatch(<redacted>)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceInspectionReceipt {
    pub profile:&'static str,pub source_index_sha256:[u8;32],pub inspection_sha256:[u8;32],
    pub text_segments:usize,pub structural_controls:usize,pub skipped_opaque_items:usize,
    pub style_definitions_resolved:bool,pub effective_style_or_hidden_visibility_qualified:bool,
    pub control_parameter_or_execution_semantics_qualified:bool,
}
pub struct SourceInspectionIndex<'a,'source> {text:&'a SourceTextIndex<'source>,styles:Vec<SourceDeclaredStyleFilter>,
    controls:Vec<SourceControlMatch>,receipt:SourceInspectionReceipt}
impl fmt::Debug for SourceInspectionIndex<'_, '_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceInspectionIndex(<redacted>; declared_source_only)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceInspectionResult {
    profile:&'static str,index:SourceSearchIndexReceipt,inspection:SourceInspectionReceipt,scope:SourceSearchScopeReceipt,
    request_sha256:[u8;32],text_matches:Option<SourceSearchResult>,control_matches:Vec<SourceControlMatch>,
    complete_within_declared_source_inventory:bool,full_search_or_execution_authority:bool,
    #[serde(skip)] output_limit:usize,
}
impl SourceInspectionResult {
    /// # Errors
    /// Navigates the retained style or control inventory without searching again.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        let occurrences=match &self.text_matches {Some(m)=>navigation::Occurrences::Text(m.matches(),None),None=>navigation::Occurrences::Control(&self.control_matches)};
        navigation::navigate(self,occurrences,self.output_limit,request,context)
    }
    #[must_use] pub const fn index_receipt(&self)->&SourceSearchIndexReceipt {&self.index}
    #[must_use] pub const fn scope_receipt(&self)->&SourceSearchScopeReceipt {&self.scope}
    #[must_use] pub const fn request_sha256(&self)->[u8;32] {self.request_sha256}
    #[must_use] pub const fn text_result(&self)->Option<&SourceSearchResult> {self.text_matches.as_ref()}
    #[must_use] pub fn controls(&self)->&[SourceControlMatch] {&self.control_matches}
    /// # Errors
    /// Bounds the whole response, not just the match payload.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {
        let mut out=Output {bytes:Some(Vec::new()),length:0,maximum:self.output_limit};
        serde_json::to_writer(&mut out,self).map_err(|_|E::Output)?;out.bytes.ok_or(E::Output)
    }
}
impl<'source> SourceTextIndex<'source> {
    /// # Errors
    /// Builds from existing anchored XML only, with bounded metadata and no invented defaults.
    pub fn inspection(&self)->Result<SourceInspectionIndex<'_,'source>,E> {
        let mut styles=Vec::new();let source=self.original.source();
        for anchor in &self.segments {
            let resolved=source.resolve_anchor(anchor).map_err(|_|E::Source)?;
            let xml=resolved.part().xml().ok_or(E::Source)?;let t=resolved.element().ok_or(E::Mapping)?;
            let run=xml.elements().get(t.parent().ok_or(E::Mapping)?).ok_or(E::Mapping)?;
            let paragraph=xml.elements().get(run.parent().ok_or(E::Mapping)?).ok_or(E::Mapping)?;
            if !named(t,"t")||!named(run,"run")||!named(paragraph,"p"){return Err(E::Mapping);}
            styles.push(SourceDeclaredStyleFilter {paragraph_property:reference(paragraph,"paraPrIDRef")?,paragraph_style:reference(paragraph,"styleIDRef")?,
                run_character_property:reference(run,"charPrIDRef")?,text_character_style:reference(t,"charStyleIDRef")?});
        }
        let paragraphs:BTreeSet<_>=self.blocks.iter().map(|b|b.paragraph.opaque_handle.clone()).collect();
        let mut controls=Vec::new();let mut skipped=0;
        for path in source.spine() {
            let part=source.parts().iter().find(|p|p.path()==path).ok_or(E::Source)?;
            let xml=part.xml().ok_or(E::Source)?;
            for (i,p) in xml.elements().iter().enumerate().filter(|(_,p)|named(p,"p")) {
                let anchor=part.element_anchor(i).ok_or(E::Mapping)?;
                if !paragraphs.contains(&anchor.opaque_handle){continue;}
                let mut run=p.first_child();
                while let Some(ri)=run {
                    let r=&xml.elements()[ri];run=r.next_sibling();
                    if !named(r,"run"){skipped+=1;continue;}
                    let mut item=r.first_child();
                    while let Some(ti)=item {
                        let t=&xml.elements()[ti];item=t.next_sibling();
                        if named(t,"ctrl") {
                            let mut child=t.first_child();
                            while let Some(ci)=child {child=xml.elements()[ci].next_sibling();push_control(part,ci,anchor,Site::Control,&mut controls,&mut skipped,self.limits.0.segments)?;}
                        }else if named(t,"t") {
                            let mut child=t.first_child();
                            while let Some(ci)=child {child=xml.elements()[ci].next_sibling();
                                push_control(part,ci,anchor,Site::Text,&mut controls,&mut skipped,self.limits.0.segments)?;
                            }
                        }else{push_control(part,ti,anchor,Site::Run,&mut controls,&mut skipped,self.limits.0.segments)?;}
                    }
                }
            }
        }
        let mut digest=DigestOutput {bound:Output {bytes:None,length:0,maximum:self.limits.0.result_bytes},hash:Sha256::new()};
        serde_json::to_writer(&mut digest,&(SOURCE_SEARCH_INSPECTION_PROFILE,self.receipt.index_sha256,&styles,&controls,skipped)).map_err(|_|E::Output)?;
        let receipt=SourceInspectionReceipt {profile:SOURCE_SEARCH_INSPECTION_PROFILE,source_index_sha256:self.receipt.index_sha256,
            inspection_sha256:digest.hash.finalize().into(),text_segments:styles.len(),structural_controls:controls.len(),
            skipped_opaque_items:skipped,style_definitions_resolved:false,effective_style_or_hidden_visibility_qualified:false,
            control_parameter_or_execution_semantics_qualified:false};
        Ok(SourceInspectionIndex {text:self,styles,controls,receipt})
    }
}
impl SourceInspectionIndex<'_, '_> {
    pub(in crate::document_import::search) fn observed_controls(&self)->&[SourceControlMatch] {&self.controls}
    pub(in crate::document_import::search) fn accepts_declared_points(&self,points:&BTreeSet<usize>,filter:SourceDeclaredStyleFilter)->bool {
        !points.is_empty()&&points.iter().all(|p|filter.matches(self.styles[self.text.points[*p].segment]))
    }
    #[must_use] pub const fn receipt(&self)->&SourceInspectionReceipt {&self.receipt}
    /// # Errors
    /// All original contributing scalars must satisfy the declared-reference filter.
    /// Empty matches have no source scalars and are not style matches.
    pub fn find_style(&self,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,filter:SourceDeclaredStyleFilter)->Result<SourceInspectionResult,E> {
        if filter.is_empty(){return Err(E::Filter);}
        let(receipt,selected)=self.text.resolve_search_scope(scope)?;
        let accept=|points:&BTreeSet<usize>|self.accepts_declared_points(points,filter);
        let result=self.text.find_filtered(query,Some(&selected),Some(&accept))?;
        let binding=serde_json::to_vec(&(SOURCE_SEARCH_INSPECTION_PROFILE,"declared_style",self.receipt.inspection_sha256,
            receipt.scope_sha256,query,filter)).map_err(|_|E::Mapping)?;
        self.result(receipt,Sha256::digest(binding).into(),Some(result),Vec::new())
    }
    /// # Errors
    /// Searches the closed observed tag kind, never opaque descendants or raw XML names.
    pub fn find_control(&self,scope:SourceSearchScope<'_>,kind:SourceControlKind,max_results:usize)->Result<SourceInspectionResult,E> {
        if max_results==0||max_results>self.text.limits.0.matches{return Err(E::Limit);}
        let(receipt,selected)=self.text.resolve_search_scope(scope)?;let mut found=Vec::new();
        for control in &self.controls {
            if control.kind==kind&&selected.contains(&control.paragraph_anchor.opaque_handle) {
                if found.len()>=max_results{return Err(E::Limit);}found.push(control.clone());
            }
        }
        let binding=serde_json::to_vec(&(SOURCE_SEARCH_INSPECTION_PROFILE,"structural_control",self.receipt.inspection_sha256,
            receipt.scope_sha256,kind,max_results)).map_err(|_|E::Mapping)?;
        self.result(receipt,Sha256::digest(binding).into(),None,found)
    }
    fn result(&self,scope:SourceSearchScopeReceipt,request_sha256:[u8;32],text_matches:Option<SourceSearchResult>,control_matches:Vec<SourceControlMatch>)->Result<SourceInspectionResult,E> {
        let result=SourceInspectionResult {profile:SOURCE_SEARCH_INSPECTION_PROFILE,index:self.text.receipt.clone(),inspection:self.receipt.clone(),scope,
            request_sha256,text_matches,control_matches,complete_within_declared_source_inventory:true,full_search_or_execution_authority:false,
            output_limit:self.text.limits.0.result_bytes};
        let mut count=Output {bytes:None,length:0,maximum:result.output_limit};serde_json::to_writer(&mut count,&result).map_err(|_|E::Output)?;Ok(result)
    }
}
fn named(node:&XmlElementToken,name:&str)->bool {node.name().namespace()==Some(HP)&&node.name().local_name()==name}
fn reference(node:&XmlElementToken,name:&str)->Result<Option<u32>,E> {
    node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name)
        .map(|a|a.semantic_value().parse::<u32>().map_err(|_|E::Mapping)).transpose()
}
fn push_control(part:&ImportedSourcePart,i:usize,paragraph:&SourceAnchorHandle,site:Site,out:&mut Vec<SourceControlMatch>,skipped:&mut usize,maximum:usize)->Result<(),E> {
    let node=&part.xml().ok_or(E::Source)?.elements()[i];
    if let Some(kind)=kind(node,site) {if out.len()>=maximum{return Err(E::Limit);}
        out.push(SourceControlMatch {kind,paragraph_anchor:paragraph.clone(),control_anchor:part.element_anchor(i).ok_or(E::Mapping)?.clone()});
    }else{*skipped+=1;}Ok(())
}
struct DigestOutput {bound:Output,hash:Sha256}
impl io::Write for DigestOutput {
    fn write(&mut self,bytes:&[u8])->io::Result<usize> {let n=io::Write::write(&mut self.bound,bytes)?;self.hash.update(bytes);Ok(n)}
    fn flush(&mut self)->io::Result<()> {Ok(())}
}
