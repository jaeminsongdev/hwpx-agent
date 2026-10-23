//! Original paragraph-style names -> simultaneous paragraph reference changes, including empty bodies.
pub mod filtered;
use super::*;
use crate::document_import::fields::semantics::{ImportedDocumentFieldSemantics,catalog::{ImportedDocumentCatalog,ImportedCatalogKind}};
use domain_ir::PropertyValue;
pub const NAMED_PARAGRAPH_STYLE_PROFILE:&str="hwpx-agent.source-named-paragraph-style-replacement/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize,Deserialize)]
#[serde(rename_all="snake_case")]
pub enum SourceStyleNameAxis{NativeName,EnglishName}
impl SourceStyleNameAxis{fn attribute(self)->&'static str{match self{Self::NativeName=>"name",Self::EnglishName=>"engName"}}}
#[derive(Clone,Copy,Serialize)]
pub struct SourceNamedParagraphStyleQuery<'a>{pub query:&'a str,pub replacement:&'a str,pub regex:bool,pub case_sensitive:bool,pub whole_word:bool,pub name_axis:SourceStyleNameAxis}
impl fmt::Debug for SourceNamedParagraphStyleQuery<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceNamedParagraphStyleQuery(<redacted>)")}}
#[derive(Debug,Error)]
pub enum SourceNamedParagraphStyleError{
    #[error("NAMED_PARAGRAPH_STYLE_SOURCE_REJECTED")]Source,
    #[error("NAMED_PARAGRAPH_STYLE_PATTERN_REJECTED")]Pattern,
    #[error("NAMED_PARAGRAPH_STYLE_LIMIT")]Limit,
    #[error("NAMED_PARAGRAPH_STYLE_TARGET_MISSING")]MissingTarget,
    #[error("NAMED_PARAGRAPH_STYLE_TARGET_AMBIGUOUS")]AmbiguousTarget,
    #[error("NAMED_PARAGRAPH_STYLE_NO_MATCHES")]NoMatches,
    #[error("NAMED_PARAGRAPH_STYLE_NO_CHANGE")]NoChange,
    #[error("NAMED_PARAGRAPH_STYLE_SEARCH_REJECTED:{0}")]Search(#[from]SourceSearchError),
    #[error("NAMED_PARAGRAPH_STYLE_PARAGRAPH_REJECTED:{0}")]Paragraph(#[from]SourceParagraphStyleReplacementError),
    #[error("NAMED_PARAGRAPH_STYLE_COMPILE_REJECTED:{0}")]Compile(#[from]E),
}
type N=SourceNamedParagraphStyleError;
impl SourceNamedParagraphStyleQuery<'_>{
    /// # Errors
    /// Nonempty bounded names/pattern, no control characters or inferred name axis.
    pub fn validate(self)->Result<(),N>{
        if self.query.len()>4096||self.replacement.len()>4096{return Err(N::Limit);}
        if self.query.is_empty()||self.replacement.is_empty()||self.query.chars().chain(self.replacement.chars()).any(char::is_control){return Err(N::Pattern);}Ok(())
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceNamedParagraphStyleReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_catalog_sha256:[u8;32],pub source_index_sha256:[u8;32],
    pub selector:SourceIndexScopeReceipt,pub body_policy:SourceReviewTextPolicy,pub name_axis:SourceStyleNameAxis,pub query_sha256:[u8;32],pub request_sha256:[u8;32],
    pub matched_declarations:usize,pub from_style_ids:Vec<u32>,pub target_style_id:u32,pub target_declaration:SourceAnchorHandle,
    pub matched_paragraphs:usize,pub changes:Vec<SourceParagraphStyleChange>,pub changed_parts:usize,pub compiled_attribute_bytes:usize,
    pub source_review_import:ReviewBodyImportReceipt,pub output_review_import:ReviewBodyImportReceipt,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub original_declarations_and_nonselected_references_preserved:bool,pub original_text_controls_run_and_text_references_preserved:bool,
    pub full_style_filter_character_style_native_or_execution_qualified:bool,
}
pub struct SourceNamedParagraphStyleCandidate{artifact:PackageArtifact,receipt:SourceNamedParagraphStyleReceipt}
impl fmt::Debug for SourceNamedParagraphStyleCandidate{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceNamedParagraphStyleCandidate(<redacted>; not_native_or_authority)")}}
impl SourceNamedParagraphStyleCandidate{
    #[must_use]pub const fn receipt(&self)->&SourceNamedParagraphStyleReceipt{&self.receipt}
    /// # Errors
    /// Writer integrity only. No current-service, commit or execution authority.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(consume)}
}
impl ImportedDocumentForms{
    /// # Errors
    /// Fresh whole source and explicit paragraph-style-name matching; no synthetic text matches.
    pub fn lower_named_paragraph_style_candidate(&self,fresh:&[u8],query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceNamedParagraphStyleCandidate,N>{
        query.validate()?;check_budget(query,limits)?;
        self.reconstruct_source_for_verification(fresh).map_err(|_|N::Source)?
            .lower_named_paragraph_style_candidate(self,query,selector,policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_>{
    /// # Errors
    /// One source proof/catalog/index/output. Whole original paragraphs only; names are not body text.
    pub fn lower_named_paragraph_style_candidate(&self,original:&ImportedDocumentForms,query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceNamedParagraphStyleCandidate,N>{
        self.lower_named_paragraph_style_candidate_checked(original,query,selector,policy,None,limits,writer).map(|(candidate,_)|candidate)
    }
    fn lower_named_paragraph_style_candidate_checked(&self,original:&ImportedDocumentForms,query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,filter:Option<SourceReviewStyleFilter>,limits:SourceSearchLimits,writer:WriterLimits)->Result<(SourceNamedParagraphStyleCandidate,Option<filtered::SourceNamedParagraphFilterReceipt>),N>{
        if let Some(filter)=filter{filter.validate()?;}
        query.validate()?;check_budget(query,limits)?;let rebuilt=self.for_original(original).map_err(|_|N::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|N::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|N::Source)?;
        let meanings=ImportedDocumentFieldSemantics::import(&fields).map_err(|_|N::Source)?;let catalog=ImportedDocumentCatalog::import(&meanings).map_err(|_|N::Source)?;
        let names=resolve(&catalog,query,limits)?;let scope=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let(selector,windows,_,_)=scope.transformation_windows(selector,policy)?;let index=scope.source_index();let source=original.source();
        if selector.kind=="selection"&&selector.selected_normalized_scalars==0{return Err(R::IncompleteParagraphScope.into());}
        let filtered=filter.map(|filter|filtered::select(index,&windows,filter)).transpose()?;
        source.observe_protection_signals().and_then(|o|o.require_no_observed_document_signals()).map_err(|_|E::Protection)?;
        let mut full=BTreeMap::new();let mut selected=BTreeMap::new();
        for(i,block)in index.blocks.iter().enumerate(){*full.entry(&block.paragraph.opaque_handle).or_insert(true)&=windows.get(&i)==Some(&(0,block.units.len()));
            if windows.contains_key(&i){selected.insert(&block.paragraph.opaque_handle,&block.paragraph);}}
        let mut matched:BTreeMap<PackagePath,BTreeMap<usize,SourceAnchorHandle>>=BTreeMap::new();let mut count=0usize;
        for(id,anchor)in selected{
            let at=source.resolve_anchor(anchor).map_err(|_|E::Selection)?;let node=at.element().ok_or(E::Selection)?;
            if !paragraph(node){return Err(E::Selection.into());}
            let Some(old)=super::super::render::reference(node,"styleIDRef")? else{continue};
            if !names.from.contains(&old){continue;}
            if full.get(id)!=Some(&true){return Err(R::IncompleteParagraphScope.into());}
            if filtered.as_ref().is_some_and(|(allowed,_)|!allowed.contains(id)){continue;}
            if count>=limits.0.matches{return Err(N::Limit);}count+=1;
            matched.entry(at.part().path().clone()).or_default().insert(at.element_index().ok_or(E::Selection)?,(*anchor).clone());
        }
        if count==0{return Err(N::NoMatches);}
        let target=SourceParagraphStyleTarget::ParagraphStyle(names.target);let context=review::ReviewWriteContext::new(source,&fields,&review,policy)?;
        let plan=compile_matched(index,&fields,&context,matched,target)?;
        let parts=plan.edits.keys().map(|p|(p,())).collect();
        let artifact=super::super::text::output::build(source,rebuilt.source().original.as_ref(),&plan.intents,&parts,writer)?;
        let output_review=verify::output(index,&plan,target,&artifact,&context)?;
        let query_sha256=hash(&query,limits.0.result_bytes)?;
        let request_sha256=hash(&(NAMED_PARAGRAPH_STYLE_PROFILE,catalog.receipt(),&selector,policy,query_sha256,&names.from,names.target,&names.declaration,&plan.changes),limits.0.result_bytes)?;
        let receipt=SourceNamedParagraphStyleReceipt{profile:NAMED_PARAGRAPH_STYLE_PROFILE,source_package_sha256:source.receipt().source_package_sha256,
            source_catalog_sha256:catalog.receipt().graph_sha256,source_index_sha256:index.receipt.index_sha256,selector,body_policy:policy,name_axis:query.name_axis,
            query_sha256,request_sha256,matched_declarations:names.matched,from_style_ids:names.from.into_iter().collect(),target_style_id:names.target,target_declaration:names.declaration,
            matched_paragraphs:plan.matched_paragraphs,changes:plan.changes,changed_parts:plan.edits.len(),compiled_attribute_bytes:plan.bytes,
            source_review_import:review.receipt().clone(),output_review_import:output_review,observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),original_declarations_and_nonselected_references_preserved:true,
            original_text_controls_run_and_text_references_preserved:true,full_style_filter_character_style_native_or_execution_qualified:false};
        let mut count=Output{bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|N::Limit)?;
        Ok((SourceNamedParagraphStyleCandidate{artifact,receipt},filtered.map(|(_,receipt)|receipt)))
    }
}
fn check_budget(query:SourceNamedParagraphStyleQuery<'_>,limits:SourceSearchLimits)->Result<(),N>{
    if query.query.len()>limits.0.query_bytes||query.replacement.len()>limits.0.query_bytes{return Err(N::Limit);}Ok(())
}
struct Names{from:BTreeSet<u32>,target:u32,declaration:SourceAnchorHandle,matched:usize}
fn resolve(catalog:&ImportedDocumentCatalog<'_, '_, '_>,query:SourceNamedParagraphStyleQuery<'_>,limits:SourceSearchLimits)->Result<Names,N>{
    let pattern=if query.regex{query.query.to_owned()}else{::regex::escape(query.query)};
    let pattern=if query.whole_word{format!(r"\b(?:{pattern})\b")}else{pattern};
    let matcher=::regex::RegexBuilder::new(&pattern).case_insensitive(!query.case_sensitive).size_limit(limits.0.pattern_bytes.min(1024*1024))
        .dfa_size_limit(limits.0.dfa_bytes.min(1024*1024)).build().map_err(|_|N::Pattern)?;
    let(mut from,mut targets)=(BTreeSet::new(),Vec::new());let mut matched=0usize;
    for definition in catalog.definitions().iter().filter(|d|d.kind==ImportedCatalogKind::NamedStyle){
        let value=|name:&str|definition.native_attributes.iter().find_map(|(key,value)|if key==name{if let PropertyValue::Text(text)=value{Some(text.as_str())}else{None}}else{None});
        if value("type")!=Some("PARA"){continue;}
        let name=value(query.name_axis.attribute()).ok_or(N::Source)?;
        if name==query.replacement{targets.push((definition.native_id,definition.source_anchor.clone()));}
        if let Some(hit)=matcher.find(name){if hit.is_empty(){return Err(N::Pattern);}matched+=1;if from.len()>=128{return Err(N::Limit);}from.insert(definition.native_id);}
    }
    if matched==0{return Err(N::NoMatches);}let(target,declaration)=match targets.as_slice(){[]=>return Err(N::MissingTarget),[one]=>one.clone(),_=>return Err(N::AmbiguousTarget)};
    from.remove(&target);if from.is_empty(){return Err(N::NoChange);}Ok(Names{from,target,declaration,matched})
}
fn hash(value:&impl Serialize,maximum:usize)->Result<[u8;32],N>{
    let mut out=Output{bytes:Some(Vec::new()),length:0,maximum};serde_json::to_writer(&mut out,value).map_err(|_|N::Limit)?;Ok(Sha256::digest(out.bytes.ok_or(N::Limit)?).into())
}
