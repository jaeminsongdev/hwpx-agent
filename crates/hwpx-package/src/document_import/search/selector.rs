//! Original graph section/node selection and fingerprinted NFC-index ranges, not live UI flow.
pub mod inventory;
pub(in crate::document_import::search) mod control_geometry;
use super::*;
use domain_ir::{Flow,LogicalId,Node};
use std::collections::BTreeMap;
use serde::Deserialize;
pub const SOURCE_SELECTOR_SCOPE_PROFILE:&str="hwpx-agent.source-index-scope-selector/v1";
#[derive(Clone,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceIndexBoundary {pub paragraph_handle:LogicalId,pub block_index:usize,pub normalized_scalar:usize}
#[derive(Clone,Copy,Debug)]
pub enum SourceIndexScopeSelector<'a> {
    Document,Section(&'a [LogicalId]),NodeSet(&'a [LogicalId]),
    Selection {index_sha256:[u8;32],start:&'a SourceIndexBoundary,end:&'a SourceIndexBoundary},
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceIndexScopeReceipt {
    pub profile:&'static str,pub kind:&'static str,pub scope_sha256:[u8;32],pub index_sha256:[u8;32],
    pub selected_sections:usize,pub selected_nodes:usize,pub selected_paragraphs:usize,pub selected_blocks:usize,
    pub selected_normalized_scalars:usize,pub coordinate_space:&'static str,pub block_order:&'static str,
    pub whole_document_visibility_native_flow_or_revision_authority:bool,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceSelectorSearchResult {profile:&'static str,scope:SourceIndexScopeReceipt,request_sha256:[u8;32],result:SourceSearchResult}
impl SourceSelectorSearchResult {
    /// # Errors
    /// Binds this exact retained selector result; never searches or widens its windows.
    pub fn navigate(&self,request:&navigation::SourceSearchNavigationRequest,context:[u8;32])->Result<navigation::SourceSearchNavigationResult,E> {
        navigation::navigate(self,navigation::Occurrences::Text(self.result.matches(),None),self.result.output_limit,request,context)
    }
    #[must_use] pub const fn scope_receipt(&self)->&SourceIndexScopeReceipt {&self.scope}
    #[must_use] pub const fn result(&self)->&SourceSearchResult {&self.result}
    #[must_use] pub const fn request_sha256(&self)->[u8;32] {self.request_sha256}
    /// # Errors
    /// The finite response includes the selector wrapper; no truncation or authority.
    pub fn canonical_json(&self)->Result<Vec<u8>,E> {
        let mut output=Output {bytes:Some(Vec::new()),length:0,maximum:self.result.output_limit};
        serde_json::to_writer(&mut output,self).map_err(|_|E::Output)?;output.bytes.ok_or(E::Output)
    }
}
type Windows=BTreeMap<usize,(usize,usize)>;
pub(in crate::document_import::search) type SupplementalNodes=BTreeMap<LogicalId,SourceAnchorHandle>;
type NodeIntervals=BTreeMap<LogicalId,(String,usize,usize)>;
impl SourceTextIndex<'_> {
    /// # Errors
    /// Original section/node identities and exact index-bound selection are checked before query matching.
    /// The file/index coordinate profile does not attest current revision, visibility or native flow.
    pub fn find_selector(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>)->Result<SourceSelectorSearchResult,E> {
        let (scope,windows)=self.resolve_index_selector(selector)?;
        let result=self.find_windowed(query,None,None,Some(&windows))?;
        let mut hash=ScopeHash::new(self.limits.0.result_bytes);
        serde_json::to_writer(&mut hash,&(SOURCE_SELECTOR_SCOPE_PROFILE,scope.scope_sha256,result.query_sha256())).map_err(|_|E::Output)?;
        let result=SourceSelectorSearchResult {profile:SOURCE_SELECTOR_SCOPE_PROFILE,scope,request_sha256:hash.finish(),result};
        let mut count=Output {bytes:None,length:0,maximum:self.limits.0.result_bytes};serde_json::to_writer(&mut count,&result).map_err(|_|E::Output)?;Ok(result)
    }
    fn resolve_index_selector(&self,selector:SourceIndexScopeSelector<'_>)->Result<(SourceIndexScopeReceipt,Windows),E> {
        self.resolve_index_selector_with_nodes(selector,None)
    }
    pub(in crate::document_import::search) fn resolve_index_selector_with_nodes(&self,selector:SourceIndexScopeSelector<'_>,supplemental:Option<&SupplementalNodes>)->Result<(SourceIndexScopeReceipt,Windows),E> {
        self.resolve_index_selector_with_geometry(selector,supplemental,None)
    }
    pub(in crate::document_import::search) fn resolve_index_selector_with_geometry(&self,selector:SourceIndexScopeSelector<'_>,supplemental:Option<&SupplementalNodes>,mut geometry:Option<&mut control_geometry::ControlGeometry>)->Result<(SourceIndexScopeReceipt,Windows),E> {
        let mut windows=Windows::new();let mut ids=BTreeSet::new();let mut sections=0;let mut nodes=0;
        let (kind,boundaries)=match selector {
            SourceIndexScopeSelector::Document=>{for (i,b) in self.blocks.iter().enumerate(){windows.insert(i,(0,b.units.len()));}("document",None)},
            SourceIndexScopeSelector::Section(requested)=>{
                ids=unique(requested,self.limits.0.paragraphs)?;sections=ids.len();
                let mut actual=self.original.graph().sections().iter();let mut parts=BTreeSet::new();let mut available=BTreeSet::new();
                for path in self.original.source().spine() {
                    let part=self.original.source().parts().iter().find(|p|p.path()==path).ok_or(E::Source)?;
                    let xml=part.xml().ok_or(E::Source)?;let root=&xml.elements()[xml.root_element()];
                    if root.name().namespace()!=Some("http://www.hancom.co.kr/hwpml/2011/section")||root.name().local_name()!="sec"{continue;}
                    let section=actual.next().ok_or(E::Mapping)?;available.insert(&section.section_id);
                    if ids.contains(&section.section_id){parts.insert(path);}
                }
                if actual.next().is_some()||!ids.iter().all(|id|available.contains(id)){return Err(E::Scope);}
                if let Some(g)=geometry.as_deref_mut(){*g=control_geometry::ControlGeometry::Parts(parts.iter().map(|p|p.as_str().to_owned()).collect());}
                for (i,b) in self.blocks.iter().enumerate() {
                    let original=self.original.source().resolve_anchor(&b.paragraph).map_err(|_|E::Source)?;
                    if parts.contains(original.part().path()){windows.insert(i,(0,b.units.len()));}
                }("section",None)
            },
            SourceIndexScopeSelector::NodeSet(requested)=>{
                ids=unique(requested,self.limits.0.paragraphs)?;nodes=ids.len();let mut catalog=NodeIntervals::new();
                for section in self.original.graph().sections(){self.node_intervals(&section.body,&mut catalog,0)?;}
                for note in self.original.graph().notes(){self.node_intervals(&note.body,&mut catalog,0)?;}
                if let Some(extra)=supplemental {for (id,anchor) in extra {
                    if catalog.len()>=self.limits.0.blocks{return Err(E::Limit);}
                    let resolved=self.original.source().resolve_anchor(anchor).map_err(|_|E::Source)?;let element=resolved.element().ok_or(E::Mapping)?;
                    let xml=resolved.part().xml().ok_or(E::Source)?;let stop=xml.tokens()[element.end_token().unwrap_or(element.start_token())].span().end();
                    if catalog.insert(id.clone(),(resolved.part().path().as_str().to_owned(),element.start_tag_span().start(),stop)).is_some(){return Err(E::Mapping);}
                }}
                let mut selected:BTreeMap<&str,Vec<(usize,usize)>>=BTreeMap::new();
                for id in &ids {let(path,a,b)=catalog.get(id).ok_or(E::Scope)?;selected.entry(path).or_default().push((*a,*b));}
                for ranges in selected.values_mut() {ranges.sort_unstable();let mut merged:Vec<(usize,usize)>=Vec::new();
                    for &(a,b) in ranges.iter(){if let Some(last)=merged.last_mut()&&a<=last.1 {last.1=last.1.max(b);}else{merged.push((a,b));}}*ranges=merged;}
                if let Some(g)=geometry.as_deref_mut(){*g=control_geometry::ControlGeometry::Nodes(selected.iter().map(|(p,r)|(p.to_string(),r.clone())).collect());}
                for (i,b) in self.blocks.iter().enumerate() {
                    let resolved=self.original.source().resolve_anchor(&b.paragraph).map_err(|_|E::Source)?;
                    let position=resolved.element().ok_or(E::Mapping)?.start_tag_span().start();
                    if let Some(ranges)=selected.get(resolved.part().path().as_str()) {
                        let n=ranges.partition_point(|(a,_)|*a<=position);
                        if n>0&&position<ranges[n-1].1 {windows.insert(i,(0,b.units.len()));}
                    }
                }("node_set",None)
            },
            SourceIndexScopeSelector::Selection {index_sha256,start,end}=>{
                if index_sha256!=self.receipt.index_sha256{return Err(E::Scope);}
                self.selector_boundary(start)?;self.selector_boundary(end)?;
                if (start.block_index,start.normalized_scalar)>(end.block_index,end.normalized_scalar){return Err(E::Scope);}
                if let Some(g)=geometry.as_deref_mut(){*g=control_geometry::ControlGeometry::selection(self,start,end)?;}
                for i in start.block_index..=end.block_index {let block=&self.blocks[i];
                    windows.insert(i,(if i==start.block_index{start.normalized_scalar}else{0},if i==end.block_index{end.normalized_scalar}else{block.units.len()}));
                }("selection",Some((start,end)))
            },
        };
        let paragraphs:BTreeSet<_>=windows.keys().map(|i|&self.blocks[*i].paragraph.opaque_handle).collect();
        let selected_normalized_scalars=windows.values().try_fold(0usize,|sum,(a,b)|sum.checked_add(b-a).ok_or(E::Limit))?;
        let mut hash=ScopeHash::new(self.limits.0.result_bytes);
        serde_json::to_writer(&mut hash,&(SOURCE_SELECTOR_SCOPE_PROFILE,self.receipt.index_sha256,kind,&ids,boundaries,&windows)).map_err(|_|E::Output)?;
        Ok((SourceIndexScopeReceipt {profile:SOURCE_SELECTOR_SCOPE_PROFILE,kind,scope_sha256:hash.finish(),index_sha256:self.receipt.index_sha256,
            selected_sections:sections,selected_nodes:nodes,selected_paragraphs:paragraphs.len(),selected_blocks:windows.len(),selected_normalized_scalars,
            coordinate_space:"index_nfc_unicode_scalars",block_order:"source_index_blocks_not_native_document_flow",
            whole_document_visibility_native_flow_or_revision_authority:false},windows))
    }
    fn selector_boundary(&self,boundary:&SourceIndexBoundary)->Result<(),E> {
        let block=self.blocks.get(boundary.block_index).ok_or(E::Scope)?;let cut=boundary.normalized_scalar;
        if boundary.paragraph_handle!=block.paragraph.opaque_handle||cut>block.units.len(){return Err(E::Scope);}
        // A boundary cannot split multiple normalized contributions of one original scalar.
        for unit in &block.units[..cut] {for origin in &unit.origins {if self.usage[*origin].1>=cut{return Err(E::Scope);}}}Ok(())
    }
    fn node_intervals(&self,flow:&Flow,catalog:&mut NodeIntervals,depth:usize)->Result<(),E> {
        if depth>128{return Err(E::Limit);}
        for node in &flow.children {
            if catalog.len()>=self.limits.0.blocks{return Err(E::Limit);}
            let common=node.common();let anchor=common.source_anchor.as_ref().ok_or(E::Source)?;
            let resolved=self.original.source().resolve_anchor(anchor).map_err(|_|E::Source)?;let element=resolved.element().ok_or(E::Mapping)?;
            let xml=resolved.part().xml().ok_or(E::Source)?;
            let stop=xml.tokens()[element.end_token().unwrap_or(element.start_token())].span().end();
            if catalog.insert(common.node_id.clone(),(resolved.part().path().as_str().to_owned(),element.start_tag_span().start(),stop)).is_some(){return Err(E::Mapping);}
            match node {Node::Table(t)=>for cell in &t.cells {self.node_intervals(&cell.body,catalog,depth+1)?;},
                Node::Drawing(d)=>self.node_intervals(&d.children,catalog,depth+1)?,_=>{}}
        }Ok(())
    }
}
fn unique(ids:&[LogicalId],maximum:usize)->Result<BTreeSet<LogicalId>,E> {
    if ids.is_empty()||ids.len()>maximum{return Err(E::Scope);}let set:BTreeSet<_>=ids.iter().cloned().collect();
    if set.len()!=ids.len(){return Err(E::Scope);}Ok(set)
}
struct ScopeHash {hash:Sha256,length:usize,maximum:usize}
impl ScopeHash {fn new(maximum:usize)->Self {Self {hash:Sha256::new(),length:0,maximum}}fn finish(self)->[u8;32] {self.hash.finalize().into()}}
impl io::Write for ScopeHash {
    fn write(&mut self,bytes:&[u8])->io::Result<usize> {
        self.length=self.length.checked_add(bytes.len()).filter(|n|*n<=self.maximum).ok_or_else(||io::Error::other("selector scope binding bound"))?;
        self.hash.update(bytes);Ok(bytes.len())
    }
    fn flush(&mut self)->io::Result<()> {Ok(())}
}
