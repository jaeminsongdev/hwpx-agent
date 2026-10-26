//! Conditional single-page snapshot interpretation. Caller metadata is NOT Native attestation.
//! A trusted capture consumer must independently bind the exact source/producer/page inventory.
use super::*;
use crate::{XmlElementToken,HANCOM_2020_PARAGRAPH_NAMESPACE as HP};
const HH:&str="http://www.hancom.co.kr/hwpml/2011/head";

/// Explicitly unattested metadata. No Deserialize and no execution/Native grant.
#[derive(Clone)]
pub struct SinglePageObservation { source_sha256:[u8;32] }
impl fmt::Debug for SinglePageObservation{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SinglePageObservation(<redacted>; unattested_metadata)")}
}
impl SinglePageObservation{
    /// # Errors
    /// Only one complete physical page is representable. An arbitrary caller can
    /// supply these numbers, so constructing this type does not attest a producer.
    pub fn from_unattested_metadata(source_sha256:[u8;32],page_count:u32,rendered_page_indices:&[u32])->Result<Self,BookmarkResultError>{
        if source_sha256==[0;32]||page_count!=1||rendered_page_indices!=[0]{return Err(BookmarkResultError::Selection);}
        Ok(Self{source_sha256})
    }
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SinglePageResultStatus { MatchesUnderObservation,MismatchUnderObservation,UnqualifiedLayout,UnqualifiedDirection }
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SinglePageResultAssessment{
    pub profile:&'static str,pub scope:&'static str,pub status:SinglePageResultStatus,
    pub base:BookmarkResultAssessment,pub expected_text_sha256:Option<[u8;32]>,
    pub target_line_y:Option<u32>,pub reference_line_y:Option<u32>,
    pub native_extent_or_locale_attested_by_api:bool,pub general_document_flow_qualified:bool,
    pub execution_publication_or_revision_authority:bool,
}
fn attr<'a>(node:&'a XmlElementToken,name:&str)->Option<&'a str>{
    node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name).map(|a|a.semantic_value())
}
fn named(node:&XmlElementToken,ns:&str,name:&str)->bool{node.name().namespace()==Some(ns)&&node.name().local_name()==name}
fn decimal_first_page_profile(actual:&ImportedDocumentFields<'_>)->bool{
    let source=actual.forms.source();
    let mut sections=source.parts().iter().filter(|p|p.path().as_str().starts_with("Contents/section")&&p.path().as_str().ends_with(".xml"));
    let Some(section)=sections.next()else{return false};if sections.next().is_some(){return false;}
    let Some(body)=section.xml()else{return false};
    if body.elements().iter().any(|n|n.name().namespace()==Some(HP)&&matches!(n.name().local_name(),
        "pageNumCtrl"|"pageNum"|"newNum"|"tbl"|"pic"|"ole"|"shapeContainer"|"footNote"|"endNote"|"header"|"footer")){return false;}
    let mut starts=body.elements().iter().filter(|n|named(n,HP,"startNum"));
    let Some(start)=starts.next()else{return false};if starts.next().is_some()||attr(start,"page")!=Some("0"){return false;}
    if !start.parent().and_then(|i|body.elements().get(i)).is_some_and(|n|named(n,HP,"secPr")){return false;}
    if body.elements().iter().any(|n|named(n,HP,"p")&&(attr(n,"pageBreak")!=Some("0")||attr(n,"columnBreak")!=Some("0"))){return false;}
    if body.elements().iter().any(|n|named(n,HP,"colPr")&&attr(n,"colCount")!=Some("1")){return false;}
    let Some(header)=source.parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").and_then(|p|p.xml())else{return false};
    let mut numbers=header.elements().iter().filter(|n|named(n,HH,"beginNum"));
    let Some(begin)=numbers.next()else{return false};numbers.next().is_none()&&attr(begin,"page")==Some("1")
        &&begin.parent().and_then(|i|header.elements().get(i)).is_some_and(|n|named(n,HH,"head"))
}
fn line_position(actual:&ImportedDocumentFields<'_>,id:&LogicalId,maximum:u32)->Option<(u32,u32)>{
    let field=actual.fields().iter().find(|f|&f.reference_id==id)?;
    let resolved=actual.forms.source().resolve_anchor(&field.begin_anchor).ok()?;let xml=resolved.part().xml()?;
    let mut at=resolved.element_index()?;let mut p=None;
    for _ in 0..32{let n=xml.elements().get(at)?;if named(n,HP,"p"){p=Some(at);break;}at=n.parent()?;}
    let p=p?;let paragraph=&xml.elements()[p];let parent=xml.elements().get(paragraph.parent()?)?;
    if parent.name().local_name()!="sec"||parent.name().namespace()!=Some("http://www.hancom.co.kr/hwpml/2011/section"){return None;}
    let mut arrays=xml.elements().iter().enumerate().filter(|(_,n)|n.parent()==Some(p)&&named(n,HP,"linesegarray"));
    let(index,_)=arrays.next()?;if arrays.next().is_some(){return None;}
    let mut lines=xml.elements().iter().filter(|n|n.parent()==Some(index)&&named(n,HP,"lineseg"));let line=lines.next()?;
    if lines.next().is_some()||attr(line,"textpos")!=Some("0"){return None;}
    let y:u32=attr(line,"vertpos")?.parse().ok()?;let height:u32=attr(line,"vertsize")?.parse().ok()?;
    if height==0||y.checked_add(height)?>maximum{return None;}Some((y,height))
}
impl PreparedBookmarkResultExpectation{
    /// # Errors
    /// Original/actual bytes and command/target checks precede conditional layout
    /// interpretation. This cannot turn arbitrary page-count metadata into Native authority.
    pub fn assess_single_page_observation(&self,original_fresh:&[u8],actual:&ImportedDocumentFields<'_>,actual_fresh:&[u8],
        observation:&SinglePageObservation)->Result<SinglePageResultAssessment,BookmarkResultError>{
        if observation.source_sha256!=actual.receipt().source_package_sha256{return Err(BookmarkResultError::Source);}
        let base=self.assess(original_fresh,actual,actual_fresh)?;
        if base.status!=BookmarkResultStatus::NeedsDocumentFlow{return Err(BookmarkResultError::Selection);}
        let mut receipt=SinglePageResultAssessment{profile:"hwpx-agent.source-single-page-bookmark-result/v1",
            scope:"conditional_decimal_first_page_korean_above_only_caller_extent_not_native_attestation",status:SinglePageResultStatus::UnqualifiedLayout,
            base,expected_text_sha256:None,target_line_y:None,reference_line_y:None,native_extent_or_locale_attested_by_api:false,
            general_document_flow_qualified:false,execution_publication_or_revision_authority:false};
        if !decimal_first_page_profile(actual){return Ok(receipt);}
        let commands=SourceBookmarkCrossReferenceBindings::import(actual,self.limits).map_err(|_|BookmarkResultError::Command)?;
        let row=commands.bindings().iter().find(|v|v.command_sha256==self.command_sha256).ok_or(BookmarkResultError::Command)?;
        let SourceBookmarkResolution::Bound{logical_target_id,..}=&row.target else{return Err(BookmarkResultError::Target)};
        let maximum=self.limits.config().extent_hwpunit;
        let(Some((target,height)),Some((reference,reference_height)))=(line_position(actual,logical_target_id,maximum),line_position(actual,&row.field_reference_id,maximum))else{return Ok(receipt)};
        receipt.target_line_y=Some(target);receipt.reference_line_y=Some(reference);
        let expected=match self.display{
            BookmarkCrossReferenceDisplay::Page=>Some("1"),
            BookmarkCrossReferenceDisplay::RelativePosition if target.checked_add(height).is_some_and(|v|v<=reference)=>Some("위"),
            BookmarkCrossReferenceDisplay::RelativePosition if reference.checked_add(reference_height).is_some_and(|v|v<=target)=>{
                receipt.status=SinglePageResultStatus::UnqualifiedDirection;None},
            _=>None,
        };
        if let Some(expected)=expected{
            let sha:[u8;32]=Sha256::digest(expected.as_bytes()).into();receipt.expected_text_sha256=Some(sha);
            receipt.status=if receipt.base.observed_text_sha256==Some(sha)&&receipt.base.observed_utf8_bytes==Some(expected.len()){
                SinglePageResultStatus::MatchesUnderObservation}else{SinglePageResultStatus::MismatchUnderObservation};
        }
        if serde_json::to_vec(&receipt).map_err(|_|BookmarkResultError::Limit)?.len()>self.limits.config().output_bytes{return Err(BookmarkResultError::Limit);}Ok(receipt)
    }
}
