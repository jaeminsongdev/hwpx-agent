//! Current-source cursor destinations; no stale cache/position or Native cursor command.
use super::*;
use super::super::bookmark_crossref::{BookmarkCrossReferenceDisplay as D,SourceBookmarkCrossReferenceBindings,SourceBookmarkResolution};
use domain_ir::SourceAnchorHandle;
use std::io;
const HP:&str=crate::HANCOM_2020_PARAGRAPH_NAMESPACE;

#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum BookmarkNavigationError{
    #[error("BOOKMARK_NAVIGATION_SOURCE_REJECTED")]Source,
    #[error("BOOKMARK_NAVIGATION_SELECTION_REJECTED")]Selection,
    #[error("BOOKMARK_NAVIGATION_PARAMETER_REJECTED")]Parameters,
    #[error("BOOKMARK_NAVIGATION_TARGET_REJECTED")]Target,
    #[error("BOOKMARK_NAVIGATION_LIMIT")]Limit,
}
type E=BookmarkNavigationError;
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum BookmarkNavigationStatus{SourceDestinationResolved,HyperlinkDisabled,MissingTarget,AmbiguousTarget}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct BookmarkNavigationReceipt{
    pub profile:&'static str,pub field_id_sha256:[u8;32],pub target_name_sha256:[u8;32],pub command_sha256:[u8;32],
    pub status:BookmarkNavigationStatus,pub family:Option<SourceBookmarkFamily>,pub command_refpath_agree:bool,
    pub source_destination_resolved:bool,pub cached_display_used_for_destination:bool,pub native_cursor_or_execution_authority:bool,
}
/// Exact current source tokens, not a native API argument or application cursor.
pub struct BookmarkSourceDestination{family:SourceBookmarkFamily,start:SourceAnchorHandle,end:Option<SourceAnchorHandle>}
impl fmt::Debug for BookmarkSourceDestination{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("BookmarkSourceDestination(<redacted>; source_only)")}}
impl BookmarkSourceDestination{
    #[must_use]pub const fn family(&self)->SourceBookmarkFamily{self.family}
    #[must_use]pub const fn start(&self)->&SourceAnchorHandle{&self.start}
    #[must_use]pub fn end(&self)->Option<&SourceAnchorHandle>{self.end.as_ref()}
}
pub struct BookmarkNavigationResult{receipt:BookmarkNavigationReceipt,destination:Option<BookmarkSourceDestination>}
impl fmt::Debug for BookmarkNavigationResult{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("BookmarkNavigationResult(<redacted>)")}}
impl BookmarkNavigationResult{
    #[must_use]pub const fn receipt(&self)->&BookmarkNavigationReceipt{&self.receipt}
    #[must_use]pub fn destination(&self)->Option<&BookmarkSourceDestination>{self.destination.as_ref()}
}
pub struct PreparedBookmarkNavigation{source_sha256:[u8;32],source_bytes:usize,rows:Vec<BookmarkNavigationResult>,limit:usize}
impl fmt::Debug for PreparedBookmarkNavigation{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedBookmarkNavigation(<redacted>; no_native_cursor_authority)")}}
impl PreparedBookmarkNavigation{
    /// # Errors
    /// A complete fresh-byte identity check precedes the entire batch. Source
    /// destinations must still be resolved by a host against its current source.
    pub fn with_current_results<T>(&self,fresh:&[u8],consume:impl FnOnce(&[BookmarkNavigationResult])->T)->Result<T,E>{
        if fresh.len()!=self.source_bytes||<[u8;32]>::from(Sha256::digest(fresh))!=self.source_sha256{return Err(E::Source);}
        Ok(consume(&self.rows))
    }
    /// # Errors
    /// Hash-only bounded metadata. Neither XML selectors, raw commands, names nor cache text are exported.
    pub fn canonical_receipts_json(&self)->Result<Vec<u8>,E>{
        struct Limited{bytes:Vec<u8>,limit:usize}
        impl io::Write for Limited{
            fn write(&mut self,b:&[u8])->io::Result<usize>{
                if self.bytes.len().checked_add(b.len()).is_none_or(|n|n>self.limit){return Err(io::Error::other("BOOKMARK_NAVIGATION_LIMIT"));}
                self.bytes.try_reserve(b.len()).map_err(|_|io::Error::other("BOOKMARK_NAVIGATION_LIMIT"))?;
                self.bytes.extend_from_slice(b);Ok(b.len())
            }
            fn flush(&mut self)->io::Result<()>{Ok(())}
        }
        #[derive(Serialize)]struct Metadata<'a>{schema_version:&'static str,source_package_sha256:[u8;32],rows:Vec<&'a BookmarkNavigationReceipt>,native_cursor_moved:bool}
        let value=Metadata{schema_version:"hwpx-agent.source-bookmark-navigation/v1",source_package_sha256:self.source_sha256,
            rows:self.rows.iter().map(|r|&r.receipt).collect(),native_cursor_moved:false};
        let mut out=Limited{bytes:Vec::new(),limit:self.limit};serde_json::to_writer(&mut out,&value).map_err(|_|E::Limit)?;Ok(out.bytes)
    }
}
fn parameters(fields:&ImportedDocumentFields<'_>,field:&super::super::ImportedFieldRange,limits:ReferenceAuxiliaryLimits,work:&mut usize)->Result<[u8;32],E>{
    let source=fields.forms.source();let p=source.resolve_anchor(field.parameter_anchor.as_ref().ok_or(E::Parameters)?).map_err(|_|E::Source)?;
    let xml=p.part().xml().ok_or(E::Source)?;let node=p.element().ok_or(E::Source)?;
    let mut values=[None,None];let mut at=node.first_child();
    while let Some(i)=at{let n=xml.elements().get(i).ok_or(E::Source)?;at=n.next_sibling();
        *work=work.checked_add(1).filter(|n|*n<=1_000_000).ok_or(E::Limit)?;
        let Some(key)=n.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()=="name").map(|a|a.semantic_value())else{continue};
        let slot=match key{"Command"=>0,"RefPath"=>1,_=>continue};
        if values[slot].is_some()||n.name().namespace()!=Some(HP)||n.name().local_name()!="stringParam"||n.first_child().is_some(){return Err(E::Parameters);}
        let raw=xml.source_text(n.content_span().ok_or(E::Parameters)?).map_err(|_|E::Source)?;
        if raw.len()>limits.config().text_bytes{return Err(E::Limit);}
        values[slot]=Some(quick_xml::escape::unescape(raw).map_err(|_|E::Parameters)?);
    }
    let command=values[0].as_deref().ok_or(E::Parameters)?;let path=values[1].as_deref().ok_or(E::Parameters)?;
    let prefix=command.split_once(';').ok_or(E::Parameters)?.0;
    if !path.ends_with(';')||path.strip_suffix(';')!=Some(prefix){return Err(E::Parameters);}
    Ok(Sha256::digest(command.as_bytes()).into())
}
impl SourceBookmarkAuthoringContext<'_>{
    /// # Errors
    /// Reconstructs the whole source once, imports bindings once, then indexes
    /// selected fields/targets. No cache or caller destination participates.
    pub fn prepare_navigation(&self,fresh:&[u8],selected:&[LogicalId])->Result<PreparedBookmarkNavigation,E>{
        let limits=self.limits;let cfg=limits.config();
        if selected.is_empty()||selected.len()>cfg.items_per_kind{return Err(E::Selection);}
        if selected.len().checked_mul(std::mem::size_of::<BookmarkNavigationResult>()).is_none_or(|n|n>cfg.output_bytes){return Err(E::Limit);}
        let mut unique=BTreeSet::new();for id in selected{if !unique.insert(id){return Err(E::Selection);}}
        self.verify_source(fresh).map_err(|_|E::Source)?;
        let bound=SourceBookmarkCrossReferenceBindings::import(self.fields,limits).map_err(|e|match e{
            super::super::bookmark_crossref::BookmarkCrossReferenceError::Limit=>E::Limit,_=>E::Parameters})?;
        let bindings:BTreeMap<_,_>=bound.bindings().iter().map(|b|(&b.field_reference_id,b)).collect();
        let ranges:BTreeMap<_,_>=self.fields.fields().iter().map(|f|(&f.reference_id,f)).collect();
        let points:BTreeMap<_,_>=self.fields.forms.body_structure().bookmarks().iter().map(|b|(&b.reference_id,&b.source_anchor)).collect();
        let source=self.fields.forms.source();let mut rows=Vec::new();rows.try_reserve_exact(selected.len()).map_err(|_|E::Limit)?;
        let mut parameter_work=0usize;
        for id in selected{
            let b=bindings.get(id).ok_or(E::Selection)?;let field=ranges.get(id).ok_or(E::Selection)?;
            if parameters(self.fields,field,limits,&mut parameter_work)?!=b.command_sha256{return Err(E::Parameters);}
            let mut destination=None;
            let status=if !b.hyperlink{BookmarkNavigationStatus::HyperlinkDisabled}else{match &b.target{
                SourceBookmarkResolution::Missing=>BookmarkNavigationStatus::MissingTarget,
                SourceBookmarkResolution::Ambiguous=>BookmarkNavigationStatus::AmbiguousTarget,
                SourceBookmarkResolution::Bound{logical_target_id,target_state_sha256}=>{
                    let display=match b.display{D::Page=>SdkCrossReferenceDisplay::Page,D::BookmarkName=>SdkCrossReferenceDisplay::BookmarkName,
                        D::Content=>SdkCrossReferenceDisplay::Content,D::RelativePosition=>SdkCrossReferenceDisplay::RelativePosition};
                    let target=self.prepare(logical_target_id,display,true).map_err(|_|E::Target)?;
                    if target.receipt().command_sha256!=b.command_sha256||&target.receipt().target_state_sha256!=target_state_sha256{return Err(E::Target);}
                    let (family,start,end)=if let Some(i)=self.block_ids.get(logical_target_id){
                        let row=&self.blocks.as_ref().ok_or(E::Target)?.observations()[*i];
                        (SourceBookmarkFamily::Block,row.begin_anchor().clone(),Some(row.end_anchor().clone()))
                    }else{let anchor=points.get(logical_target_id).ok_or(E::Target)?;
                        (SourceBookmarkFamily::Point,(**anchor).clone(),None)};
                    let start_node=source.resolve_anchor(&start).map_err(|_|E::Target)?;
                    if let Some(ref tail)=end{let end_node=source.resolve_anchor(tail).map_err(|_|E::Target)?;
                        if start_node.part().path()!=end_node.part().path()||start_node.element_index().zip(end_node.element_index()).is_none_or(|(a,b)|a>=b){return Err(E::Target);}}
                    destination=Some(BookmarkSourceDestination{family,start,end});BookmarkNavigationStatus::SourceDestinationResolved
                }
            }};
            let receipt=BookmarkNavigationReceipt{profile:"hwpx-agent.source-bookmark-navigation/v1",field_id_sha256:Sha256::digest(id.as_str().as_bytes()).into(),
                target_name_sha256:b.exact_target_name_sha256,command_sha256:b.command_sha256,status,family:destination.as_ref().map(|v|v.family),
                command_refpath_agree:true,source_destination_resolved:destination.is_some(),cached_display_used_for_destination:false,native_cursor_or_execution_authority:false};
            rows.push(BookmarkNavigationResult{receipt,destination});
        }
        let out=PreparedBookmarkNavigation{source_sha256:self.fields.receipt().source_package_sha256,source_bytes:fresh.len(),rows,limit:cfg.output_bytes};
        out.canonical_receipts_json()?;Ok(out)
    }
}
