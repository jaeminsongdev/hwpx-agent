//! Explicit independent sibling groups in one immutable-source transaction, never sequential sorts.
mod readback;
use super::*;

pub const SOURCE_PARAGRAPH_SORT_GROUPS_PROFILE:&str="hwpx-agent.source-paragraph-sort-groups-candidate/v1";
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceParagraphSortGroup {
    #[serde(serialize_with="serialize_path")]
    pub part:PackagePath,pub parent_element:usize,pub entries:Vec<SourceParagraphSortEntry>,
    pub source_order:Vec<usize>,pub comparison_bytes:usize,pub moved_paragraphs:usize,
}
impl fmt::Debug for SourceParagraphSortGroup {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceParagraphSortGroup(<redacted>)")}
}
fn serialize_path<S:serde::Serializer>(path:&PackagePath,serializer:S)->Result<S::Ok,S::Error>{serializer.serialize_str(path.as_str())}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceParagraphSortGroupsReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],
    pub scope:SourceIndexScopeReceipt,pub body_policy:SourceReviewTextPolicy,pub spec:SourceParagraphSortSpec,
    pub request_sha256:[u8;32],pub groups:Vec<SourceParagraphSortGroup>,pub selected_paragraphs:usize,
    pub moved_paragraphs:usize,pub changed_groups:usize,pub changed_parts:usize,pub comparison_bytes:usize,
    pub excluded_hidden_paragraphs:usize,pub excluded_memo_paragraphs:usize,pub observed_protection_element_visits:usize,
    pub normalization_unicode_version:(u8,u8,u8),pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub whole_paragraph_scope_verified:bool,pub exact_subtrees_and_positional_gaps_read_back:bool,pub stable_equal_keys:bool,
    pub locale_native_full_protection_or_execution_authority:bool,
}
pub struct SourceParagraphSortGroupsCandidate {artifact:PackageArtifact,receipt:SourceParagraphSortGroupsReceipt,splices:intents::SourceParagraphSortSpliceInventory}
impl fmt::Debug for SourceParagraphSortGroupsCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceParagraphSortGroupsCandidate(<redacted>; not_service_or_execution_authority)")}
}
impl SourceParagraphSortGroupsCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceParagraphSortGroupsReceipt {&self.receipt}
    #[must_use] pub const fn splice_inventory(&self)->&intents::SourceParagraphSortSpliceInventory {&self.splices}
    /// # Errors
    /// Checks immutable artifact bytes only, not current service access or a revision commit.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
struct Row {element:usize,block:usize,start:usize,end:usize,entry:SourceParagraphSortEntry}
struct PlannedGroup<'a> {path:&'a PackagePath,parent:usize,xml:&'a PreservingXmlDocument,rows:Vec<Row>,order:Vec<usize>,work:usize,moved:usize}

impl ImportedDocumentForms {
    /// # Errors
    /// Explicitly partitions complete selected paragraphs by their original part and immediate parent.
    /// Every selected paragraph is checked; structured/overlapping selections fail as a whole.
    pub fn lower_selector_paragraph_sort_groups_candidate(&self,fresh:&[u8],selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        spec:SourceParagraphSortSpec,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceParagraphSortGroupsCandidate,R> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_selector_paragraph_sort_groups_candidate(self,selector,policy,spec,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One whole-original proof and source index, one preserving transaction, one output admission.
    pub fn lower_selector_paragraph_sort_groups_candidate(&self,original:&ImportedDocumentForms,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        spec:SourceParagraphSortSpec,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceParagraphSortGroupsCandidate,R> {
        if spec.max_comparison_bytes==0||spec.max_comparison_bytes>32*1024*1024{return Err(R::ComparisonLimit);}
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let(scope,windows,hidden,memo)=index.transformation_windows(selector,policy)?;let text=index.source_index();
        let mut by_paragraph:BTreeMap<&domain_ir::LogicalId,Vec<usize>>=BTreeMap::new();
        for(i,b)in text.blocks.iter().enumerate(){by_paragraph.entry(&b.paragraph.opaque_handle).or_default().push(i);}
        let mut selected=Vec::new();
        for blocks in by_paragraph.values(){
            if !blocks.iter().any(|i|windows.contains_key(i)){continue;}
            if blocks.iter().any(|i|windows.get(i)!=Some(&(0,text.blocks[*i].units.len()))){return Err(R::IncompleteParagraphScope);}
            if blocks.len()!=1{return Err(R::StructuredKey);}selected.push(blocks[0]);
        }
        if selected.len()<2{return Err(E::NoMatches.into());}
        if selected.len()>PatchLimits::default().config().max_intents{return Err(E::Limit.into());}
        let selected_paragraphs=selected.len();let source=text.original.source();
        let context=review::ReviewWriteContext::new(source,&fields,&review,policy)?;
        let intervals=context.field_intervals(source,&fields)?;
        let mut guards=BTreeMap::new();let mut groups:BTreeMap<(&PackagePath,usize),PlannedGroup<'_>>=BTreeMap::new();
        let mut visits=0usize;
        for block in selected {
            let b=&text.blocks[block];let resolved=source.resolve_anchor(&b.paragraph).map_err(|_|E::Source)?;
            let path=resolved.part().path();let xml=resolved.part().xml().ok_or(E::Source)?;
            let i=resolved.element_index().ok_or(E::Selection)?;let node=resolved.element().ok_or(E::Selection)?;
            let parent=node.parent().ok_or(E::Selection)?;
            if node.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)||node.name().local_name()!="p"{return Err(E::Selection.into());}
            let span=node.outer_span().ok_or(E::Selection)?;
            if !guards.contains_key(path){
                visits=visits.checked_add(xml.elements().len().checked_mul(3).ok_or(E::Limit)?).ok_or(E::Limit)?;
                guards.insert(path,guard(xml)?);
            }
            let protection=guards.get(path).ok_or(E::Source)?;
            let stop=xml.elements().partition_point(|n|n.start_tag_span().start()<span.end());
            if protection[stop]!=protection[i]{return Err(E::Protection.into());}
            if let Some(ranges)=intervals.get(path){let j=ranges.partition_point(|(_,b)|*b<=span.start());
                if ranges.get(j).is_some_and(|(a,_)|*a<span.end()){return Err(E::FieldContent.into());}}
            let flow=crate::TextFlowReader::read_preserving_xml_context(xml,i,crate::TextFlowLimits::default()).map_err(|_|E::Source)?;
            if flow.children.iter().any(|child|match child {crate::ParagraphChild::Run(run)=>run.items.iter().any(|item|!matches!(item,crate::TextRunItem::Text(_))),_=>true}){return Err(R::StructuredKey);}
            let sha=xml.with_source_bytes(|raw|Sha256::digest(&raw[span.start()..span.end()]).into());
            let group=groups.entry((path,parent)).or_insert_with(||PlannedGroup{path,parent,xml,rows:Vec::new(),order:Vec::new(),work:0,moved:0});
            group.rows.try_reserve(1).map_err(|_|E::Limit)?;
            group.rows.push(Row {element:i,block,start:span.start(),end:span.end(),entry:SourceParagraphSortEntry{
                paragraph_anchor:b.paragraph.clone(),normalized_key_sha256:Sha256::digest(b.text.as_bytes()).into(),subtree_sha256:sha,subtree_bytes:span.end()-span.start()}});
        }
        let(mut work,mut moved,mut changed_groups)=(0usize,0usize,0usize);let mut intents=Vec::new();let mut parts=BTreeMap::new();
        for group in groups.values_mut(){
            group.rows.sort_unstable_by_key(|r|r.element);
            let keys:Vec<_>=group.rows.iter().map(|r|text.blocks[r.block].text.as_str()).collect();
            let remaining=spec.max_comparison_bytes.checked_sub(work).ok_or(R::ComparisonLimit)?;
            let(order,used)=order::sort(&keys,SourceParagraphSortSpec{max_comparison_bytes:remaining,..spec})?;
            work=work.checked_add(used).filter(|n|*n<=spec.max_comparison_bytes).ok_or(R::ComparisonLimit)?;
            group.moved=order.iter().enumerate().filter(|(i,j)|*i!=**j).count();group.work=used;group.order=order;
            moved=moved.checked_add(group.moved).ok_or(E::Limit)?;
            if group.moved==0{continue;}
            changed_groups=changed_groups.checked_add(1).ok_or(E::Limit)?;
            let targets=group.rows.iter().map(|r|XmlElementSelector::bind(group.path,group.xml,r.element).map_err(|_|E::Selection)).collect::<Result<Vec<_>,_>>()?;
            intents.push(PatchIntent::PermuteSiblingElements{targets,source_order:group.order.clone()});parts.insert(group.path,());
        }
        if groups.values().all(|g|g.rows.len()<2){return Err(E::NoMatches.into());}
        if moved==0{return Err(E::NoChange.into());}
        let grouped:Vec<_>=groups.into_values().collect();
        // Disjoint original spans, including identity slots, are verified before any artifact build.
        let slots=readback::slots(&grouped)?;
        let artifact=styles::text::output::build(source,rebuilt.source().original.as_ref(),&intents,&parts,writer)?;
        readback::output(source,&slots,&artifact,&context)?;
        let splices=intents::groups::prepare(slots.iter().flat_map(|(path,rows)|rows.iter().map(move |(destination,moved)|
            (*path,&destination.entry,&moved.entry,destination.start,destination.end))),selected_paragraphs,moved)?;
        let groups:Vec<_>=grouped.into_iter().map(|g|SourceParagraphSortGroup{part:g.path.clone(),parent_element:g.parent,
            entries:g.rows.into_iter().map(|r|r.entry).collect(),source_order:g.order,comparison_bytes:g.work,moved_paragraphs:g.moved}).collect();
        let request_sha256=intents::hash(&(SOURCE_PARAGRAPH_SORT_GROUPS_PROFILE,text.receipt.index_sha256,&scope,policy,spec,&groups),limits.0.result_bytes)?;
        let receipt=SourceParagraphSortGroupsReceipt{profile:SOURCE_PARAGRAPH_SORT_GROUPS_PROFILE,source_package_sha256:source.receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,scope,body_policy:policy,spec,request_sha256,groups,selected_paragraphs,
            moved_paragraphs:moved,changed_groups,changed_parts:parts.len(),comparison_bytes:work,excluded_hidden_paragraphs:hidden,excluded_memo_paragraphs:memo,
            observed_protection_element_visits:visits,normalization_unicode_version:text.receipt.normalization_unicode_version,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),whole_paragraph_scope_verified:true,
            exact_subtrees_and_positional_gaps_read_back:true,stable_equal_keys:true,locale_native_full_protection_or_execution_authority:false};
        let mut count=Output{bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        let splices=intents::groups::bind(&receipt,splices,limits.0.result_bytes)?;
        Ok(SourceParagraphSortGroupsCandidate{artifact,receipt,splices})
    }
}
