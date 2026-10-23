use super::*;
use domain_ir::{CaptionSequenceDefinition as Definition,CaptionNumberFormat as Format,CaptionObjectKind as ObjectKind,CaptionRestartPolicy as Restart};
use hwpx_package::document_import::{reference_targets::{caption_source_state::output::program::*,caption_frames::{CaptionStyleFamily,CaptionFrameSegmentKind}},
    structure::{caption_style_batch::CaptionStyleReplacement as Style,caption_edit_batch::CaptionLayoutReplacement as Layout,caption_layout::CaptionLayout}};
fn package_for(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
    rewrite(&with_begin(body)?,|name,data|Ok(if name=="Contents/header.xml"{String::from_utf8(data)?.replace("<hh:charPr id='4'/>","<hh:charPr id='4'/><hh:charPr id='5'/>").into_bytes()}else{data}))
}
fn definition(state:&ImportedCaptionSourceState<'_>,id:&str,style:u32,start:u32,restart:Restart)->Definition {
    Definition {logical_sequence_id:LogicalId::parse(id).unwrap(),object_kind:ObjectKind::Picture,label:"그림 & <label>".into(),separator:" ".into(),number_format:Format::Decimal,
        restart_policy:restart,start_at:start,number_style_sha256:hex::encode(state.frames().style_declaration(CaptionStyleFamily::Character,style).declaration_sha256.unwrap()),opaque_properties:vec![],locked:false}
}
fn assignments<'a>(state:&'a ImportedCaptionSourceState<'_>,sequence:&'a LogicalId)->Result<Vec<SourceCaptionSequenceAssignment<'a>>,Box<dyn Error>> {
    state.frames().frames().iter().enumerate().map(|(i,f)|Ok(SourceCaptionSequenceAssignment {caption_id:&f.logical_caption_id,object_id:&f.logical_object_id,sequence_id:sequence,
        label_text_id:&f.segments.iter().find(|s|s.kind==CaptionFrameSegmentKind::PlainText).ok_or("text")?.logical_source_id,
        number_control_id:f.segments.iter().find(|s|s.kind==CaptionFrameSegmentKind::AutoNumber).and_then(|s|s.number_control_id.as_ref()).ok_or("auto")?,document_order:i as u64})).collect()
}
fn request<'a>(state:&ImportedCaptionSourceState<'_>,sequences:&'a[Definition],assignments:&'a[SourceCaptionSequenceAssignment<'a>])->SourceCaptionSequenceRequest<'a> {
    SourceCaptionSequenceRequest {expected_joined_state_sha256:state.receipt().joined_state_sha256,sequences,assignments}
}
fn after_numbers(bytes:&[u8])->Result<Vec<i32>,Box<dyn Error>> {
    let source=structure(bytes,"program")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;Ok(state.numbering().controls().iter().map(|c|c.stored_number).collect())
}
#[test]
fn caption_program_complete_membership_explicit_order_content_style_and_native_snapshot_share_output() -> TestResult {
    let body=format!("<hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='0' tbl='3' equation='4'/></hp:secPr><hp:ctrl><hp:newNum num='5' numType='PICTURE'/></hp:ctrl>{}{}",object(0,"<hp:t>oldA</hp:t>"),object(1,"<hp:t>oldA</hp:t>"))
        .replace("prefixChar=''","prefixChar='private pre&#9;&amp;'");
    let bytes=package_for(&body)?;let source=structure(&bytes,"program")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let mut sequences=[definition(&state,"private logical sequence",5,3,Restart::Continuous)];sequences[0].number_format=Format::RomanUpper;
    let mut members=assignments(&state,&sequences[0].logical_sequence_id)?;members[0].document_order=20;members[1].document_order=10;
    let program=request(&state,&sequences,&members);let frames=state.frames().frames();
    let styles=frames.iter().map(|f|Style {caption_id:&f.logical_caption_id,source_node_id:&f.runs[0].logical_run_id,family:CaptionStyleFamily::Character,declaration_id:5}).collect::<Vec<_>>();
    let texts=[Request {caption_id:&frames[1].logical_caption_id,text_id:&frames[1].segments.last().ok_or("last")?.logical_source_id,replacement:"private new body"}];
    let layouts=[Layout {caption_id:&frames[0].logical_caption_id,layout:CaptionLayout {side:domain_ir::NativeCaptionSide::Left,full_size:true,width_hwpunit:80,gap_hwpunit:12,last_width_hwpunit:40}}];
    let candidate=state.lower_caption_program_candidate(&bytes,&program,&texts,&layouts,&styles,limits()?,WriterLimits::default())?;let r=candidate.receipt();
    assert_eq!(r.caller_request_sha256,program.canonical_sha256(limits()?)?);assert_eq!(r.bindings.iter().map(|b|b.resolved_number).collect::<Vec<_>>(),[4,3]);
    assert!(r.complete_original_caption_membership_checked&&r.labels_stored_numbers_and_declared_styles_read_back&&r.caller_order_not_native_counter_order);
    assert!(!r.native_counter_recalculation_qualified&&!r.execution_publication_authority);
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(after_numbers(&output)?,[5,4,3]);
    let after=structure(&output,"program")?;let after=ImportedCaptionSourceState::import(&after,limits()?)?;
    assert_eq!(after.context().document_start().ok_or("begin")?.page,0);assert_eq!(after.numbering().section_starts()[0].table,3);
    for f in after.frames().frames(){assert_eq!(after.frames().plain_text(&f.segments[0].logical_source_id),Some("그림 & <label> "));assert_eq!(f.runs[0].character_style.reference_id,Some(5));}
    for c in &after.numbering().controls()[1..] {let format=c.format.as_ref().ok_or("format")?;assert_eq!(format.native_type,"ROMAN_CAPITAL");assert_eq!(format.prefix_sha256,<[u8;32]>::from(Sha256::digest("private pre\t&".as_bytes())));}
    let before=parts(&bytes)?;let after=parts(&output)?;for (path,old) in before {if path!="Contents/section0.xml"{assert_eq!(after[&path],old);}}
    let safe=format!("{program:?}{candidate:?}{}",serde_json::to_string(r)?);for raw in ["private logical sequence","private pre","private new body","그림 & <label>"]{assert!(!safe.contains(raw));}Ok(())
}
#[test]
fn caption_program_per_section_and_independent_sequences_preserve_actual_spine_binding() -> TestResult {
    let bytes=rewrite(&fixture::two_sections()?,|name,data|{
        if name=="Contents/header.xml"{return Ok(HEADER.as_bytes().to_vec());}
        if name.starts_with("Contents/section"){let offset=if name.ends_with("section1.xml"){2}else{0};let text=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&format!("{}{}",object(offset,"<hp:t>oldA</hp:t>"),object(offset+1,"<hp:t>oldA</hp:t>")));
            return Ok(if offset==2{text.replacen("<hp:p id='1'>","<hp:p id='2'>",1)}else{text}.into_bytes());}Ok(data)
    })?;
    let source=structure(&bytes,"program")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let sequences=[definition(&state,"per-section",4,2,Restart::PerSection),definition(&state,"continuous",4,7,Restart::Continuous)];let mut members=assignments(&state,&sequences[0].logical_sequence_id)?;
    for (i,m) in members.iter_mut().enumerate(){m.sequence_id=&sequences[i%2].logical_sequence_id;}members.reverse();
    let program=request(&state,&sequences,&members);let output=state.lower_caption_program_candidate(&bytes,&program,&[],&[],&[],limits()?,WriterLimits::default())?;
    assert_eq!(output.receipt().output.content.output.changed_parts,2);assert_eq!(after_numbers(&output.with_verified_bytes(<[u8]>::to_vec)?)?,[2,7,2,8]);Ok(())
}
#[test]
fn caption_program_all_seven_formats_and_noops_keep_original_affixes_and_lexical_values() -> TestResult {
    let bytes=package_for(&(0..7).map(|i|object(i,"<hp:t>oldA</hp:t>")).collect::<String>())?;let source=structure(&bytes,"program")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let formats=[Format::Decimal,Format::CircledDecimal,Format::RomanUpper,Format::RomanLower,Format::LatinUpper,Format::LatinLower,Format::HangulSyllable];
    let sequences=formats.iter().enumerate().map(|(i,f)|{let mut s=definition(&state,&format!("sequence-{i}"),4,11+i as u32,Restart::Continuous);s.number_format=*f;s}).collect::<Vec<_>>();
    let mut members=assignments(&state,&sequences[0].logical_sequence_id)?;for (i,m) in members.iter_mut().enumerate(){m.sequence_id=&sequences[i].logical_sequence_id;}
    let result=state.lower_caption_program_candidate(&bytes,&request(&state,&sequences,&members),&[],&[],&[],limits()?,WriterLimits::default())?;
    let output=result.with_verified_bytes(<[u8]>::to_vec)?;let rebuilt=structure(&output,"program")?;let after=ImportedCaptionSourceState::import(&rebuilt,limits()?)?;
    assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[11,12,13,14,15,16,17]);
    assert_eq!(after.numbering().controls().iter().map(|c|c.format.as_ref().and_then(|f|f.typed_format)).collect::<Vec<_>>(),formats.into_iter().map(Some).collect::<Vec<_>>());
    let bytes=package_for(&object(0,"<hp:t>oldA</hp:t>").replace("num='19'","num='00019'"))?;let source=structure(&bytes,"program")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let mut sequences=[definition(&state,"noop",4,19,Restart::Continuous)];sequences[0].label="oldA".into();sequences[0].separator.clear();let members=assignments(&state,&sequences[0].logical_sequence_id)?;
    assert!(matches!(state.lower_caption_program_candidate(&bytes,&request(&state,&sequences,&members),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::NoChange)));
    let f=&state.frames().frames()[0];let texts=[Request {caption_id:&f.logical_caption_id,text_id:&f.segments.last().ok_or("last")?.logical_source_id,replacement:"new body"}];
    let result=state.lower_caption_program_candidate(&bytes,&request(&state,&sequences,&members),&texts,&[],&[],limits()?,WriterLimits::default())?;
    assert!(String::from_utf8(parts(&result.with_verified_bytes(<[u8]>::to_vec)?)?["Contents/section0.xml"].clone())?.contains("num='00019'"));Ok(())
}
#[test]
fn caption_program_rejects_omitted_duplicate_foreign_opaque_kind_style_metadata_and_overflow() -> TestResult {
    let bytes=package_for(&format!("{}{}",object(0,"<hp:t>oldA</hp:t>"),object(1,"<hp:t>oldA</hp:t>")))?;let source=structure(&bytes,"program")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let sequences=[definition(&state,"sequence",4,1,Restart::Continuous)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;
    let omitted=request(&state,&sequences,&members[..1]);assert!(matches!(state.lower_caption_program_candidate(&bytes,&omitted,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Selection)));
    for mode in 0..7 {let mut bad=assignments(&state,&sequences[0].logical_sequence_id)?;
        match mode {0=>bad[1].caption_id=bad[0].caption_id,1=>bad[1].object_id=bad[0].object_id,2=>bad[1].number_control_id=bad[0].number_control_id,
            3=>bad[1].label_text_id=&state.frames().frames()[1].segments[1].logical_source_id,4=>bad[1].document_order=bad[0].document_order,
            5=>bad[1].sequence_id=&state.frames().frames()[0].logical_caption_id,_=>bad[1].label_text_id=bad[0].label_text_id}
        assert!(state.lower_caption_program_candidate(&bytes,&request(&state,&sequences,&bad),&[],&[],&[],limits()?,WriterLimits::default()).is_err());
    }
    for mode in 0..7 {let mut bad=sequences.clone();match mode {0=>bad[0].object_kind=ObjectKind::Table,1=>bad[0].number_style_sha256="a".repeat(64),2=>bad[0].locked=true,
        3=>bad[0].start_at=0,4=>bad[0].start_at=i32::MAX as u32+1,5=>bad[0].label="bad\0".into(),_=>bad[0].opaque_properties.push(domain_ir::OpaqueLinkProperty {namespace:"future".into(),name:"flag".into(),value_sha256:"a".repeat(64)})};
        assert!(state.lower_caption_program_candidate(&bytes,&request(&state,&bad,&members),&[],&[],&[],limits()?,WriterLimits::default()).is_err());
    }
    let f=&state.frames().frames()[0];let duplicate=[Request {caption_id:&f.logical_caption_id,text_id:members[0].label_text_id,replacement:"other label"}];
    assert!(matches!(state.lower_caption_program_candidate(&bytes,&request(&state,&sequences,&members),&duplicate,&[],&[],limits()?,WriterLimits::default()),Err(E::Selection)));Ok(())
}
#[test]
fn caption_program_whole_form_source_limits_and_observed_protection_remain_fail_closed() -> TestResult {
    let bytes=package_for(&object(0,"<hp:t>oldA</hp:t>"))?;let forms=base::forms(&bytes,"program")?;let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;
    let sequences=[definition(&state,"sequence",4,1,Restart::Continuous)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;let program=request(&state,&sequences,&members);
    let proof=forms.reconstruct_source_for_verification(&bytes)?;let result=proof.lower_caption_state_program_candidate(&forms,&state,&bytes,&program,&[],&[],&[],limits()?,WriterLimits::default())?;
    assert_eq!(after_numbers(&result.with_verified_bytes(<[u8]>::to_vec)?)?,[1]);
    let other=base::forms(&bytes,"program")?;let foreign=ImportedCaptionSourceState::import(other.body_structure(),limits()?)?;
    assert!(matches!(proof.lower_caption_state_program_candidate(&forms,&foreign,&bytes,&program,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Source)));
    assert!(matches!(proof.lower_caption_state_program_candidate(&other,&state,&bytes,&program,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Source)));
    let mut stale=bytes.clone();stale[0]^=1;assert!(matches!(state.lower_caption_program_candidate(&stale,&program,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Source)));
    let mut wrong=request(&state,&sequences,&members);wrong.expected_joined_state_sha256[0]^=1;assert!(matches!(state.lower_caption_program_candidate(&bytes,&wrong,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Source)));
    let tighter=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {text_bytes:1,..Default::default()})?;
    assert!(matches!(state.lower_caption_program_candidate(&bytes,&program,&[],&[],&[],tighter,WriterLimits::default()),Err(E::Limit)));
    assert!(matches!(state.lower_caption_program_candidate(&bytes,&program,&[],&[],&[],limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?),Err(E::Writer)));
    let bytes=package_for(&object(0,"<hp:t>oldA</hp:t>").replace("lock='0'","lock='1'"))?;let source=structure(&bytes,"program")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let sequences=[definition(&state,"sequence",4,1,Restart::Continuous)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;
    assert!(matches!(state.lower_caption_program_candidate(&bytes,&request(&state,&sequences,&members),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Protection)));Ok(())
}
#[test]
fn caption_program64_members_share_part_guards_and_bind_noop_order_and_definition_identity() -> TestResult {
    let bytes=package_for(&(0..64).map(|i|object(i,"<hp:t>oldA</hp:t>")).collect::<String>())?;let source=structure(&bytes,"program")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let sequences=[definition(&state,"private sequence identity",4,1,Restart::Continuous)];let members=assignments(&state,&sequences[0].logical_sequence_id)?;let program=request(&state,&sequences,&members);
    let result=state.lower_caption_program_candidate(&bytes,&program,&[],&[],&[],limits()?,WriterLimits::default())?;assert_eq!(result.receipt().bindings.len(),64);
    let n=source.source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").and_then(|p|p.xml()).ok_or("xml")?.elements().len();
    assert_eq!(result.receipt().output.content.output.observed_protection_element_visits,4*n);assert_eq!(after_numbers(&result.with_verified_bytes(<[u8]>::to_vec)?)?,(1..=64).collect::<Vec<_>>());
    let baseline=program.canonical_sha256(limits()?)?;let mut reversed=assignments(&state,&sequences[0].logical_sequence_id)?;reversed.reverse();assert_ne!(request(&state,&sequences,&reversed).canonical_sha256(limits()?)?,baseline);
    for mode in 0..5 {let mut variant=sequences.clone();match mode {0=>variant[0].start_at+=1,1=>variant[0].separator="_".into(),2=>variant[0].label="other".into(),3=>variant[0].number_format=Format::RomanLower,_=>variant[0].restart_policy=Restart::PerSection};
        assert_ne!(request(&state,&variant,&members).canonical_sha256(limits()?)?,baseline);
    }Ok(())
}
