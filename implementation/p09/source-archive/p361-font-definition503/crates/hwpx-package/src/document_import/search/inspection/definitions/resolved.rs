//! Required-axis resolution coverage; absent/conflicting source semantics are not false matches.
use super::*;

pub const SOURCE_RESOLVED_STYLE_PROFILE:&str="hwpx-agent.source-resolved-direct-formatting/v1";

#[derive(Clone,Copy,Debug,Default,Eq,PartialEq,Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceResolvedStyleFilter {
    pub bold:Option<bool>,pub italic:Option<bool>,pub height_hwpunit:Option<u32>,
    pub text_rgb:Option<[u8;3]>,pub alignment:Option<DefinitionAlignment>,
    #[serde(skip_serializing_if="Option::is_none")]
    pub character_details:Option<details::SourceCharacterDetailFilter>,
    #[serde(skip_serializing_if="Option::is_none")]
    pub paragraph_details:Option<paragraph_details::SourceParagraphDetailFilter>,
}
impl SourceResolvedStyleFilter {
    fn characters(&self)->bool {self.bold.is_some()||self.italic.is_some()||self.height_hwpunit.is_some()||self.text_rgb.is_some()||self.character_details.is_some()}
    fn paragraphs(&self)->bool {self.alignment.is_some()||self.paragraph_details.is_some()}
    /// # Errors
    /// At least one supported property is required; false is a predicate, not absence.
    pub fn validate(&self)->Result<(),E> {if let Some(details)=&self.character_details {details.validate()?;}if let Some(details)=&self.paragraph_details {details.validate()?;}if !self.characters()&&!self.paragraphs(){Err(E::Filter)}else{Ok(())}}
    pub(in crate::document_import::search) fn explicit(&self)->SourceDefinitionStyleFilter {
        SourceDefinitionStyleFilter {character_source:self.characters().then_some(CharacterDefinitionSource::RunProperty),
            bold:self.bold,italic:self.italic,height_hwpunit:self.height_hwpunit,text_rgb:self.text_rgb,
            paragraph_source:self.paragraphs().then_some(ParagraphDefinitionSource::DirectProperty),alignment:self.alignment,character_details:self.character_details,
            paragraph_details:self.paragraph_details}
    }
}

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceResolvedStyleCoverage {
    pub profile:&'static str,pub definitions:SourceStyleDefinitionReceipt,pub selected_text_segments:usize,
    pub resolved_character_segments:usize,pub missing_run_segments:usize,pub unresolved_text_style_segments:usize,
    pub resolved_paragraph_segments:usize,pub missing_paragraph_segments:usize,pub observed_segment_visits:usize,
    pub requested_character_axis_complete:bool,pub requested_paragraph_axis_complete:bool,
    pub inferred_default_or_named_fallback:bool,pub native_effective_visibility_or_execution_authority:bool,
}
impl SourceResolvedStyleCoverage {
    #[must_use] pub const fn requested_axes_complete(&self)->bool {self.requested_character_axis_complete&&self.requested_paragraph_axis_complete}
}

impl SourceStyleDefinitionIndex<'_, '_,'_> {
    fn unresolved_control_contexts(&self,segments:&BTreeSet<usize>)->Result<BTreeSet<usize>,E> {
        if segments.is_empty(){return Ok(BTreeSet::new());}
        let source=self.inspection.text.original.source();
        let source_parts:BTreeMap<_,_>=source.parts().iter().map(|p|(p.path().as_str(),p)).collect();
        let mut parts:BTreeMap<&str,BTreeMap<usize,usize>>=BTreeMap::new();
        for &segment in segments {
            let anchor=self.inspection.text.segments.get(segment).ok_or(E::Mapping)?;
            let resolved=source.resolve_anchor(anchor).map_err(|_|E::Source)?;
            let element=resolved.element_index().ok_or(E::Mapping)?;
            if parts.entry(resolved.part().path().as_str()).or_default().insert(element,segment).is_some(){return Err(E::Mapping);}
        }
        let mut uncertain=BTreeSet::new();
        for (path,selected) in parts {
            let part=source_parts.get(path).ok_or(E::Source)?;let mut selected=selected.into_iter().peekable();
            let xml=part.xml().ok_or(E::Source)?;let mut inherited=Vec::with_capacity(xml.elements().len());
            for (i,node) in xml.elements().iter().enumerate() {
                let parent=match node.parent(){Some(p)=>*inherited.get(p).ok_or(E::Mapping)?,None=>false};
                let local=node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)&&node.name().local_name()=="ctrl"
                    &&node.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="charStyleIDRef");
                let unresolved=parent||local;inherited.push(unresolved);
                if selected.peek().is_some_and(|(element,_)|*element==i) {
                    let(_,segment)=selected.next().ok_or(E::Mapping)?;if unresolved{uncertain.insert(segment);}
                }
            }
            if selected.next().is_some(){return Err(E::Mapping);}
        }
        // Structural context is not a native inheritance rule. Without qualified precedence,
        // a descendant direct run cannot silently override an uninterpreted control style.
        Ok(uncertain)
    }
    /// The caller supplies segments from already resolved windows, never arbitrary public indexes.
    pub(in crate::document_import::search) fn assess_resolved_segments(&self,segments:&BTreeSet<usize>,filter:&SourceResolvedStyleFilter)->Result<SourceResolvedStyleCoverage,E> {
        filter.validate()?;let control_contexts=self.unresolved_control_contexts(segments)?;
        let mut coverage=SourceResolvedStyleCoverage {profile:SOURCE_RESOLVED_STYLE_PROFILE,definitions:self.receipt.clone(),selected_text_segments:segments.len(),
            resolved_character_segments:0,missing_run_segments:0,unresolved_text_style_segments:0,resolved_paragraph_segments:0,missing_paragraph_segments:0,
            observed_segment_visits:0,requested_character_axis_complete:true,requested_paragraph_axis_complete:true,
            inferred_default_or_named_fallback:false,native_effective_visibility_or_execution_authority:false};
        for &segment in segments {
            let refs=self.refs.get(segment).ok_or(E::Mapping)?;coverage.observed_segment_visits+=1;
            let uncertain=refs.text.is_some()||control_contexts.contains(&segment);
            if uncertain{coverage.unresolved_text_style_segments+=1;}
            if refs.run.is_none(){coverage.missing_run_segments+=1;}
            if refs.run.is_some()&&!uncertain{coverage.resolved_character_segments+=1;}
            if refs.paragraph.is_some(){coverage.resolved_paragraph_segments+=1;}else{coverage.missing_paragraph_segments+=1;}
        }
        // Direct p/run links have original typed values. No rule for text-style precedence or
        // missing-axis fallback is invented from attribute names, nextStyle or fixture output.
        coverage.requested_character_axis_complete=!filter.characters()||coverage.resolved_character_segments==segments.len();
        coverage.requested_paragraph_axis_complete=!filter.paragraphs()||coverage.resolved_paragraph_segments==segments.len();
        Ok(coverage)
    }
}
