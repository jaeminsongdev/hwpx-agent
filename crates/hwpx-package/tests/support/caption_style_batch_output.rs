use super::*;
use hwpx_package::{PatchIntent,PatchLimits,PatchLimitConfig,PatchError,PackageLimits,
    PackageGraph,PackageGraphLimits,IdRuleProfile,IdIndexLimits,PreservingPatchEngine,
    PreservationRuleProfile,PreservingXmlDocument,XmlElementSelector,BoundedZipReader};
use hwpx_package::document_import::{structure::{caption_style_batch::CaptionStyleReplacement as Style,
    caption_edit_batch::CaptionLayoutReplacement as Layout,caption_layout::CaptionLayout},
    reference_targets::caption_frames::{CaptionStyleFamily as Family,CaptionStyleReferenceStatus as Status}};
use domain_ir::NativeCaptionSide;
const EXTRA:&str="<hh:charPr id='5'/>";
const PARAS:&str="<hh:paraProperties><hh:paraPr id='6'/><hh:paraPr id='7'/></hh:paraProperties><hh:styles><hh:style id='8'/><hh:style id='9'/></hh:styles>";
fn styled(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
    rewrite(&with_begin(body)?,|name,data|Ok(if name=="Contents/header.xml" {
        String::from_utf8(data)?.replace("</hh:charProperties>",&format!("{EXTRA}</hh:charProperties>"))
            .replace("</hh:refList>",&format!("{PARAS}</hh:refList>")).into_bytes()
    }else{data}))
}
fn replacements(frame:&hwpx_package::document_import::reference_targets::caption_frames::CaptionSourceFrame)->[Style<'_>;3] {
    [Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.runs[0].logical_run_id,family:Family::Character,declaration_id:5},
     Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.paragraphs[0].logical_paragraph_id,family:Family::Paragraph,declaration_id:7},
     Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.paragraphs[0].logical_paragraph_id,family:Family::Named,declaration_id:9}]
}
#[test]
fn caption_style_compiler_atomic_text_layout_and_three_declared_references_preserve_other_bytes() -> TestResult {
    let bytes=styled(&object(0,"<hp:t>private old</hp:t>").replace("<hp:p id='99'>","<hp:p id='99' paraPrIDRef='6' styleIDRef='8'>"))?;
    let source=structure(&bytes,"caption-styles")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let frame=&state.frames().frames()[0];let styles=replacements(frame);
    let texts=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"private changed & <x>"}];
    let layouts=[Layout {caption_id:&frame.logical_caption_id,layout:CaptionLayout {side:NativeCaptionSide::Bottom,full_size:false,width_hwpunit:1000,gap_hwpunit:21,last_width_hwpunit:900}}];
    let result=state.lower_content_batch_candidate(&bytes,&texts,&layouts,&styles,limits()?,WriterLimits::default())?;
    let r=result.receipt();assert_eq!((r.requested_styles,r.style_changes.len(),r.output.text_changes.len(),r.output.layout_changes.len()),(3,3,1,1));
    assert!(r.style_changes.iter().all(|c|!c.inserted_attribute&&c.output_reference.status==Status::UniqueSourceDeclaration));
    assert!(r.output.outside_selected_edits_exact&&r.input_numbering_and_frames_reused);
    assert!(!r.effective_style_and_sequence_semantics_qualified&&!r.output.complete_auxiliary_state_and_protection_verified&&!r.execution_publication_authority);
    assert!(!format!("{result:?}{}",serde_json::to_string(r)?).contains("private changed"));
    let output=result.with_verified_bytes(<[u8]>::to_vec)?;let after=parts(&output)?;
    for (path,old) in parts(&bytes)? {
        let expected=if path=="Contents/section0.xml"{String::from_utf8(old)?.replace("charPrIDRef='4'","charPrIDRef='5'")
            .replace("paraPrIDRef='6'","paraPrIDRef='7'").replace("styleIDRef='8'","styleIDRef='9'")
            .replace("gap='20'","gap='21'").replace("private old","private changed &amp; &lt;x&gt;").into_bytes()}else{old};
        assert_eq!(after[&path],expected);
    }
    let rebuilt=structure(&output,"caption-styles")?;let after=ImportedCaptionSourceState::import(&rebuilt,limits()?)?;
    assert_eq!(after.numbering().controls()[0].stored_number,19);
    assert_eq!(after.frames().frames()[0].runs[0].character_style,state.frames().style_declaration(Family::Character,5));
    assert_eq!(state.verify_source(&bytes)?,*state.receipt());Ok(())
}
#[test]
fn caption_style_compiler_missing_attributes_grouped_insertions_self_closing_nodes_and_namespace_aliases() -> TestResult {
    let body=object(0,"<hp:t>oldA</hp:t>").replace("<hp:run charPrIDRef='4'>","<hp:run xmlns:ux='urn:private' ux:flag='111'>")
        .replace("</hp:p></hp:subList>","<hp:run/></hp:p><hp:p id='100'/></hp:subList>");
    let bytes=styled(&body)?;let source=structure(&bytes,"style-insert")?;
    let state=ImportedCaptionSourceState::import(&source,limits()?)?;let frame=&state.frames().frames()[0];
    let mut styles=replacements(frame).to_vec();
    styles.extend([Style {source_node_id:&frame.runs[1].logical_run_id,..styles[0]},
        Style {source_node_id:&frame.paragraphs[1].logical_paragraph_id,..styles[1]},
        Style {source_node_id:&frame.paragraphs[1].logical_paragraph_id,..styles[2]}]);
    let first=state.lower_content_batch_candidate(&bytes,&[],&[],&styles,limits()?,WriterLimits::default())?;
    styles.reverse();let second=state.lower_content_batch_candidate(&bytes,&[],&[],&styles,limits()?,WriterLimits::default())?;
    assert_eq!(first.receipt(),second.receipt());assert_eq!(first.receipt().style_changes.len(),6);
    assert!(first.receipt().style_changes.iter().all(|c|c.inserted_attribute&&c.source_reference.status==Status::MissingReference));
    let output=first.with_verified_bytes(<[u8]>::to_vec)?;let after=parts(&output)?;
    assert_eq!(after,parts(&second.with_verified_bytes(<[u8]>::to_vec)?)?);
    for (path,old) in parts(&bytes)? {
        let expected=if path=="Contents/section0.xml"{String::from_utf8(old)?
            .replace("<hp:p id='99'>","<hp:p id='99' paraPrIDRef=\"7\" styleIDRef=\"9\">")
            .replace("ux:flag='111'>","ux:flag='111' charPrIDRef=\"5\">")
            .replace("<hp:run/>","<hp:run charPrIDRef=\"5\"/>")
            .replace("<hp:p id='100'/>","<hp:p id='100' paraPrIDRef=\"7\" styleIDRef=\"9\"/>").into_bytes()}else{old};
        assert_eq!(after[&path],expected);
    }
    // An unknown ID-like namespaced attribute is not a usable style alias.
    // Keep the pre-existing ID-index rejection instead of weakening validation.
    let unknown=styled(&object(0,"<hp:t>oldA</hp:t>").replace("<hp:run charPrIDRef='4'>","<hp:run xmlns:ux='urn:private' ux:charPrIDRef='111'>"))?;
    let source=structure(&unknown,"style-unknown-id-attribute")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let styles=replacements(&state.frames().frames()[0]);
    assert!(matches!(state.lower_content_batch_candidate(&unknown,&[],&[],&styles,limits()?,WriterLimits::default()),Err(E::Patch("id_index_unknown_id_like_attribute"))));Ok(())
}
#[test]
fn caption_style_compiler_noops_keep_lexical_source_and_invalid_duplicate_family_owner_or_limits_fail() -> TestResult {
    let bytes=styled(&format!("{}{}",object(0,"<hp:t>oldA</hp:t>").replace("charPrIDRef='4'","charPrIDRef='0004'"),object(1,"<hp:t>other</hp:t>")))?;
    let source=structure(&bytes,"style-noops")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let f=&state.frames().frames()[0];let styles=replacements(f);let noop=Style {declaration_id:4,..styles[0]};
    assert!(matches!(state.lower_content_batch_candidate(&bytes,&[],&[],&[noop],limits()?,WriterLimits::default()),Err(E::NoChange)));
    let text=[Request {caption_id:&f.logical_caption_id,text_id:&f.segments[0].logical_source_id,replacement:"new"}];
    let result=state.lower_content_batch_candidate(&bytes,&text,&[],&[noop],limits()?,WriterLimits::default())?;
    assert!(result.receipt().style_changes.is_empty());assert_eq!(result.receipt().requested_styles,1);
    assert!(String::from_utf8(parts(&result.with_verified_bytes(<[u8]>::to_vec)?)?["Contents/section0.xml"].clone())?.contains("charPrIDRef='0004'"));
    for requests in [vec![noop,noop],vec![Style {family:Family::Paragraph,..styles[0]}],
        vec![Style {caption_id:&state.frames().frames()[1].logical_caption_id,..styles[0]}],vec![Style {declaration_id:123456,..styles[0]}]] {
        assert!(matches!(state.lower_content_batch_candidate(&bytes,&text,&[],&requests,limits()?,WriterLimits::default()),Err(E::Selection)));
    }
    let changed=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()})?;
    assert!(matches!(state.lower_content_batch_candidate(&bytes,&[],&[],&styles,changed,WriterLimits::default()),Err(E::Limit)));
    assert!(matches!(state.lower_content_batch_candidate(&bytes,&[],&[],&styles,limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?),Err(E::Writer)));
    let mut drift=bytes.clone();drift[0]^=1;
    assert!(matches!(state.lower_content_batch_candidate(&drift,&[],&[],&styles,limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
}
#[test]
fn caption_style_compiler_ambiguous_and_mislocated_declarations_cannot_be_targets() -> TestResult {
    for (replacement,status) in [("<hh:charPr id='5'/><hh:charPr id='5'/>",Status::AmbiguousDeclarations),
        ("<hh:wrapper><hh:charPr id='5'/></hh:wrapper>",Status::UnverifiedDeclarationLocation)] {
        let bytes=rewrite(&styled(&object(0,"<hp:t>oldA</hp:t>"))?,|name,data|Ok(if name=="Contents/header.xml" {String::from_utf8(data)?.replace(EXTRA,replacement).into_bytes()}else{data}))?;
        let source=structure(&bytes,"style-declaration")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
        assert_eq!(state.frames().style_declaration(Family::Character,5).status,status);
        let styles=replacements(&state.frames().frames()[0]);
        assert!(matches!(state.lower_content_batch_candidate(&bytes,&[],&[],&styles[..1],limits()?,WriterLimits::default()),Err(E::Selection)));
    }Ok(())
}
#[test]
fn caption_style_compiler_ancestor_and_descendant_observed_protection_is_not_bypassed() -> TestResult {
    let ordinary=object(0,"<hp:t>oldA</hp:t>");let table=fixture::table("<hp:t>inside</hp:t>");
    let mut protected=vec![ordinary.replace("lock='0'","lock='1'"),ordinary.replace("<hp:caption ","<hp:caption lock='unknown' "),
        ordinary.replace("<hp:t>","<hp:t lock='1'>"),ordinary.replace("<hp:run charPrIDRef='4'>","<hp:run charPrIDRef='4' lock='1'>")];
    for flag in ["lock=\"0\"","hasMargin=\"0\" protect=\"0\"","heightRelTo=\"ABSOLUTE\" protect=\"0\""] {
        let new=if flag.starts_with("lock"){"lock=\"1\"".to_owned()}else{flag.replace("protect=\"0\"","protect=\"1\"")};
        protected.push(fixture::table(&ordinary).replace(flag,&new));
    }
    for body in protected {
        let bytes=styled(&body)?;let source=structure(&bytes,"style-protection")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
        let styles=replacements(&state.frames().frames()[0]);
        for request in &styles {assert!(matches!(state.lower_content_batch_candidate(&bytes,&[],&[],&[*request],limits()?,WriterLimits::default()),Err(E::Protection)));}
    }
    // Nested objects inside an opaque caption are outside the joined owner's
    // current admission coverage; preserve that original fail-closed boundary.
    let unsupported=styled(&object(0,&format!("<hp:t>oldA</hp:t>{table}")))?;
    let source=structure(&unsupported,"style-unsupported-owner")?;
    assert!(matches!(ImportedCaptionSourceState::import(&source,limits()?),Err(StateError::Coverage)));Ok(())
}
#[test]
fn caption_style_compiler_whole_form_binding_many_requests_and_low_level_insertion_contracts() -> TestResult {
    let bytes=styled(&(0..32).map(|i|object(i,"<hp:t>oldA</hp:t>")).collect::<String>())?;
    let forms=base::forms(&bytes,"style-proof")?;let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;
    let styles=state.frames().frames().iter().flat_map(replacements).collect::<Vec<_>>();
    let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let result=proof.lower_caption_state_content_batch_candidate(&forms,&state,&bytes,&[],&[],&styles,limits()?,WriterLimits::default())?;
    assert_eq!((result.receipt().style_changes.len(),result.receipt().output.observed_protection_parts),(96,1));
    let part=forms.body_structure().source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").ok_or("part")?;
    let xml=part.xml().ok_or("xml")?;assert_eq!(result.receipt().output.observed_protection_element_visits,4*xml.elements().len());
    let other=base::forms(&bytes,"style-proof")?;let other_state=ImportedCaptionSourceState::import(other.body_structure(),limits()?)?;
    assert!(matches!(proof.lower_caption_state_content_batch_candidate(&forms,&other_state,&bytes,&[],&[],&styles,limits()?,WriterLimits::default()),Err(E::Source)));
    assert!(matches!(proof.lower_caption_state_content_batch_candidate(&other,&state,&bytes,&[],&[],&styles,limits()?,WriterLimits::default()),Err(E::Source)));
    let small=styled(&object(0,"<hp:t>oldA</hp:t>"))?;let mut reader=BoundedZipReader::open(Cursor::new(&small),PackageLimits::default())?;
    let graph=PackageGraph::build(&mut reader,PackageGraphLimits::default())?;
    let section=parts(&small)?.remove("Contents/section0.xml").ok_or("section")?;let doc=PreservingXmlDocument::parse(&section)?;
    let path=reader.entries().iter().find(|e|e.path.as_str()=="Contents/section0.xml").ok_or("path")?.path.clone();
    let i=doc.elements().iter().position(|e|e.name().local_name()=="caption").ok_or("caption")?;
    let selector=XmlElementSelector::bind(&path,&doc,i)?;
    let apply=|reader:&mut BoundedZipReader<_>,intents:&[PatchIntent],limits|PreservingPatchEngine::apply_with_limits_and_preservation_profile(reader,&graph,PackageGraphLimits::default(),IdRuleProfile::hwpml_2011_shape_v6(),IdIndexLimits::default(),limits,PreservationRuleProfile::Hangul2020PreviewTextV2,intents);
    for name in ["","xmlns","XMLNS","x:y","a b","1bad","bad\"=\"x","한글"] {
        let intent=PatchIntent::InsertUnsignedAttributes {target:selector.clone(),attributes:BTreeMap::from([(name.to_owned(),7)])};
        assert!(!format!("{intent:?}").contains(name)||name.is_empty());
        assert!(matches!(apply(&mut reader,&[intent],PatchLimits::default()),Err(PatchError::ValueInvalid)));
    }
    let make=|name:&str|PatchIntent::InsertUnsignedAttributes {target:selector.clone(),attributes:BTreeMap::from([(name.to_owned(),7)])};
    assert!(matches!(apply(&mut reader,&[make("gap")],PatchLimits::default()),Err(PatchError::Conflict)));
    assert!(matches!(apply(&mut reader,&[make("newValue"),make("otherValue")],PatchLimits::default()),Err(PatchError::Conflict)));
    assert!(matches!(apply(&mut reader,&[make("newValue")],PatchLimits::new(PatchLimitConfig {max_value_bytes:1,..Default::default()})?),Err(PatchError::LimitExceeded {..})));
    assert!(apply(&mut reader,&[make("newValue")],PatchLimits::default()).is_ok());Ok(())
}
