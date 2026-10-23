//! Explicit NFC scalar ordering of complete selected sibling paragraphs, not locale or Native order.
mod order;
mod verify;
pub mod intents;
pub mod groups;
use super::*;
use crate::document_import::{ImportedSourcePackage,structure::review::ImportedDocumentReviewBodies};
use crate::document_import::search::{reviews::{SourceReviewTextPolicy,selector::SourceReviewScopeIndex},selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt}};
use serde::Deserialize;

pub const SOURCE_PARAGRAPH_SORT_PROFILE:&str="hwpx-agent.source-sibling-paragraph-sort-candidate/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceParagraphSortDirection {Ascending,Descending}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceParagraphSortComparison {NfcUnicodeScalarLexicographic}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceParagraphSortSpec {
    pub direction:SourceParagraphSortDirection,pub comparison:SourceParagraphSortComparison,pub max_comparison_bytes:usize,
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceParagraphSortError {
    #[error("SOURCE_PARAGRAPH_SORT_COMPILE:{0}")] Compile(#[from] SourceLiteralReplacementError),
    #[error("SOURCE_PARAGRAPH_SORT_SEARCH:{0}")] Search(#[from] SourceSearchError),
    #[error("SOURCE_PARAGRAPH_SORT_INCOMPLETE_PARAGRAPH_SCOPE")] IncompleteParagraphScope,
    #[error("SOURCE_PARAGRAPH_SORT_MULTIPLE_PARENT_GROUPS_UNQUALIFIED")] ParentScope,
    #[error("SOURCE_PARAGRAPH_SORT_STRUCTURED_PARAGRAPH_KEY_UNQUALIFIED")] StructuredKey,
    #[error("SOURCE_PARAGRAPH_SORT_COMPARISON_WORK_LIMIT")] ComparisonLimit,
}
type R=SourceParagraphSortError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceParagraphSortEntry {pub paragraph_anchor:SourceAnchorHandle,pub normalized_key_sha256:[u8;32],pub subtree_sha256:[u8;32],pub subtree_bytes:usize}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceParagraphSortReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub scope:SourceIndexScopeReceipt,
    pub body_policy:SourceReviewTextPolicy,pub spec:SourceParagraphSortSpec,pub request_sha256:[u8;32],
    pub entries:Vec<SourceParagraphSortEntry>,pub source_order:Vec<usize>,pub comparison_bytes:usize,pub moved_paragraphs:usize,
    pub excluded_hidden_paragraphs:usize,pub excluded_memo_paragraphs:usize,pub observed_protection_element_visits:usize,
    pub normalization_unicode_version:(u8,u8,u8),pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub whole_paragraph_scope_verified:bool,pub exact_subtrees_and_positional_gaps_read_back:bool,pub stable_equal_keys:bool,
    pub locale_native_full_protection_or_execution_authority:bool,
}
pub struct SourceParagraphSortCandidate {artifact:PackageArtifact,receipt:SourceParagraphSortReceipt,splices:intents::SourceParagraphSortSpliceInventory}
impl fmt::Debug for SourceParagraphSortCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceParagraphSortCandidate(<redacted>; explicit_single_sibling_group_not_native_or_service_authority)")}}
impl SourceParagraphSortCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceParagraphSortReceipt {&self.receipt}
    #[must_use] pub const fn splice_inventory(&self)->&intents::SourceParagraphSortSpliceInventory {&self.splices}
    /// # Errors
    /// Verifies immutable output bytes, never current service access or a revision commit.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Sorts all complete paragraphs selected from one sibling group; never widens or skips invalid selections.
    pub fn lower_selector_paragraph_sort_candidate(&self,fresh:&[u8],selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        spec:SourceParagraphSortSpec,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceParagraphSortCandidate,R> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_selector_paragraph_sort_candidate(self,selector,policy,spec,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One current whole Form proof, field/review admission, one preserving transaction and one output import.
    pub fn lower_selector_paragraph_sort_candidate(&self,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        spec:SourceParagraphSortSpec,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceParagraphSortCandidate,R> {
        if spec.max_comparison_bytes==0||spec.max_comparison_bytes>32*1024*1024{return Err(R::ComparisonLimit);}
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let(scope,windows,hidden,memo)=index.transformation_windows(selector,policy)?;let text=index.source_index();
        let mut by_paragraph:BTreeMap<&domain_ir::LogicalId,Vec<usize>>=BTreeMap::new();
        for(i,b)in text.blocks.iter().enumerate(){by_paragraph.entry(&b.paragraph.opaque_handle).or_default().push(i);}
        let mut selected=Vec::new();
        for blocks in by_paragraph.values() {
            if !blocks.iter().any(|i|windows.contains_key(i)){continue;}
            if blocks.iter().any(|i|windows.get(i)!=Some(&(0,text.blocks[*i].units.len()))){return Err(R::IncompleteParagraphScope);}
            if blocks.len()!=1{return Err(R::StructuredKey);}
            selected.push(blocks[0]);
        }
        if selected.len()<2{return Err(E::NoMatches.into());}
        if selected.len()>PatchLimits::default().config().max_intents{return Err(E::Limit.into());}
        let source=text.original.source();let first=source.resolve_anchor(&text.blocks[selected[0]].paragraph).map_err(|_|E::Source)?;
        let path=first.part().path();let xml=first.part().xml().ok_or(E::Source)?;let parent=first.element().ok_or(E::Selection)?.parent().ok_or(E::Selection)?;
        let context=review::ReviewWriteContext::new(source,&fields,&review,policy)?;let intervals=context.field_intervals(source,&fields)?;
        let guard=guard(xml)?;let mut rows=Vec::new();
        rows.try_reserve_exact(selected.len()).map_err(|_|E::Limit)?;
        for block in selected {
            let b=&text.blocks[block];let resolved=source.resolve_anchor(&b.paragraph).map_err(|_|E::Source)?;
            let i=resolved.element_index().ok_or(E::Selection)?;let node=resolved.element().ok_or(E::Selection)?;
            if resolved.part().path()!=path||node.parent()!=Some(parent){return Err(R::ParentScope);}
            if node.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)||node.name().local_name()!="p"{return Err(E::Selection.into());}
            let span=node.outer_span().ok_or(E::Selection)?;
            let stop=xml.elements().partition_point(|n|n.start_tag_span().start()<span.end());
            if guard[stop]!=guard[i]{return Err(E::Protection.into());}
            if let Some(ranges)=intervals.get(path){let j=ranges.partition_point(|(_,b)|*b<=span.start());
                if ranges.get(j).is_some_and(|(a,_)|*a<span.end()){return Err(E::FieldContent.into());}}
            let flow=crate::TextFlowReader::read_preserving_xml_context(xml,i,crate::TextFlowLimits::default()).map_err(|_|E::Source)?;
            if flow.children.iter().any(|child|match child {crate::ParagraphChild::Run(run)=>run.items.iter().any(|item|!matches!(item,crate::TextRunItem::Text(_))),_=>true}){return Err(R::StructuredKey);}
            let sha=xml.with_source_bytes(|raw|Sha256::digest(&raw[span.start()..span.end()]).into());
            rows.push((i,block,span.start(),span.end(),SourceParagraphSortEntry {paragraph_anchor:b.paragraph.clone(),normalized_key_sha256:Sha256::digest(b.text.as_bytes()).into(),subtree_sha256:sha,subtree_bytes:span.end()-span.start()}));
        }
        rows.sort_unstable_by_key(|r|r.0);
        let keys:Vec<_>=rows.iter().map(|r|text.blocks[r.1].text.as_str()).collect();
        let(order,work)=order::sort(&keys,spec)?;let moved=order.iter().enumerate().filter(|(i,j)|*i!=**j).count();
        if moved==0{return Err(E::NoChange.into());}
        let targets=rows.iter().map(|r|XmlElementSelector::bind(path,xml,r.0).map_err(|_|E::Selection)).collect::<Result<Vec<_>,_>>()?;
        let intent=PatchIntent::PermuteSiblingElements {targets,source_order:order.clone()};
        let parts=BTreeMap::from([(path,())]);
        let artifact=styles::text::output::build(source,rebuilt.source().original.as_ref(),&[intent],&parts,writer)?;
        let spans:Vec<_>=rows.iter().map(|r|(r.2,r.3)).collect();
        verify::output(source,path,xml,&spans,&order,&artifact,&context)?;
        let entries:Vec<_>=rows.into_iter().map(|r|r.4).collect();
        let mut binding=Output {bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_PARAGRAPH_SORT_PROFILE,text.receipt.index_sha256,&scope,policy,spec,&entries,&order)).map_err(|_|E::Limit)?;
        let receipt=SourceParagraphSortReceipt {profile:SOURCE_PARAGRAPH_SORT_PROFILE,source_package_sha256:source.receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,scope,body_policy:policy,spec,request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),
            entries,source_order:order,comparison_bytes:work,moved_paragraphs:moved,excluded_hidden_paragraphs:hidden,excluded_memo_paragraphs:memo,
            observed_protection_element_visits:xml.elements().len().checked_mul(3).ok_or(E::Limit)?,normalization_unicode_version:text.receipt.normalization_unicode_version,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),whole_paragraph_scope_verified:true,
            exact_subtrees_and_positional_gaps_read_back:true,stable_equal_keys:true,locale_native_full_protection_or_execution_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        let splices=intents::build(&receipt,&spans,limits.0.result_bytes)?;
        Ok(SourceParagraphSortCandidate {artifact,receipt,splices})
    }
}
fn guard(xml:&PreservingXmlDocument)->Result<Vec<usize>,E> {
    let protected=crate::document_import::structure::caption_text_batch::observed_protection(xml).map_err(|_|E::Protection)?;
    let mut tracked=Vec::<bool>::new();let mut prefix=vec![0usize];
    for(i,node)in xml.elements().iter().enumerate(){
        let own=node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)
            &&(matches!(node.name().local_name(),"insertBegin"|"insertEnd"|"deleteBegin"|"deleteEnd")
                ||node.attributes().iter().any(|a|a.name().namespace().is_none()&&matches!(a.name().local_name(),"paraTcId"|"charTcId")));
        let inherited=match node.parent(){Some(p)if p<i=>tracked[p],Some(_)=>return Err(E::Source),None=>false};
        let flag=own||inherited;tracked.push(flag);prefix.push(prefix.last().copied().ok_or(E::Source)?.checked_add(usize::from(flag||protected[i])).ok_or(E::Limit)?);
    }Ok(prefix)
}
