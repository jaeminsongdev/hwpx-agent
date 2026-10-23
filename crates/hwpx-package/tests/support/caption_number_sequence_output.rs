use super::*;
use hwpx_package::document_import::{structure::{caption_numbering_sequence::*,caption_edit_batch::CaptionLayoutReplacement as Layout,
    caption_style_batch::CaptionStyleReplacement as Style,caption_layout::CaptionLayout},reference_targets::numbering::{NativeNumberCategory as Category,NativeNumberControlKind as Kind}};
use hwpx_package::{NumberFormat,WriterLimitConfig};
use domain_ir::NativeCaptionSide;
fn package_for(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
    rewrite(&with_begin(body)?,|name,data|Ok(if name=="Contents/header.xml"{String::from_utf8(data)?.replace("<hh:charPr id='4'/>","<hh:charPr id='4'/><hh:charPr id='5'/>").into_bytes()}else{data}))
}
fn snapshot_events<'a>(state:&'a ImportedCaptionSourceState<'_>)->Result<Vec<NativeNumberEventReplacement<'a>>,Box<dyn Error>> {
    state.context().ordered_controls().iter().map(|ordered|{
        if let Some(c)=state.numbering().controls().iter().find(|c|c.logical_control_id==ordered.logical_control_id) {
            let values=match c.kind {Kind::AutoNumber=>NativeNumberEventValues::AutoNumber {category:c.category,stored_number:c.stored_number,format:NativeNumberFormatReplacement::Preserve},
                Kind::Restart=>NativeNumberEventValues::Restart {category:c.category,stored_number:c.stored_number,format:NativeNumberFormatReplacement::Preserve}};
            return Ok(NativeNumberEventReplacement {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,values});
        }
        let c=state.numbering().section_starts().iter().find(|c|c.logical_control_id==ordered.logical_control_id).ok_or("source start")?;
        let page_starts_on=match c.page_starts_on {"BOTH"=>NativePageStartsOn::Both,"EVEN"=>NativePageStartsOn::Even,"ODD"=>NativePageStartsOn::Odd,_=>return Err("source enum".into())};
        Ok(NativeNumberEventReplacement {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,
            values:NativeNumberEventValues::SectionStart {page_starts_on,page:c.page,picture:c.picture,table:c.table,equation:c.equation}})
    }).collect()
}
fn snapshot_begin<'a>(state:&'a ImportedCaptionSourceState<'_>)->Option<NativeDocumentStartReplacement<'a>> {
    state.context().document_start().map(|c|NativeDocumentStartReplacement {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,
        values:NativeDocumentStartValues {page:c.page,footnote:c.footnote,endnote:c.endnote,picture:c.picture,table:c.table,equation:c.equation}})
}
fn sequence<'a>(state:&ImportedCaptionSourceState<'_>,events:&'a[NativeNumberEventReplacement<'a>],document_start:Option<NativeDocumentStartReplacement<'a>>)->NativeNumberSequenceReplacement<'a> {
    NativeNumberSequenceReplacement {expected_joined_state_sha256:state.receipt().joined_state_sha256,events,document_start}
}
fn changed(event:NativeNumberEventReplacement<'_>,number:i32)->NativeNumberEventReplacement<'_> {
    NativeNumberEventReplacement {values:match event.values {
        NativeNumberEventValues::AutoNumber {category,format,..}=>NativeNumberEventValues::AutoNumber {category,stored_number:number,format},
        NativeNumberEventValues::Restart {category,format,..}=>NativeNumberEventValues::Restart {category,stored_number:number,format},
        value=>value,
    },..event}
}
#[test]
fn number_sequence_complete_document_section_restart_auto_and_caption_content_share_one_output() -> TestResult {
    let body=format!("<hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='0' tbl='3' equation='4'/></hp:secPr><hp:ctrl><hp:newNum num='5' numType='PICTURE'/></hp:ctrl>{}{}",
        object(0,"<hp:t>private old</hp:t><hp:ctrl><hp:newNum num='2' numType='PICTURE'/></hp:ctrl>"),object(1,"<hp:t>unchanged</hp:t>"));
    let bytes=package_for(&body)?;let source=structure(&bytes,"number-sequence")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let mut events=snapshot_events(&state)?;
    for (i,event) in events.iter_mut().enumerate(){*event=changed(*event,30+i as i32);}
    events[0].values=NativeNumberEventValues::SectionStart {page_starts_on:NativePageStartsOn::Even,page:0,picture:7,table:8,equation:9};
    let mut begin=snapshot_begin(&state).ok_or("begin")?;begin.values=NativeDocumentStartValues {page:0,footnote:11,endnote:12,picture:13,table:14,equation:15};
    let request=sequence(&state,&events,Some(begin));let frame=&state.frames().frames()[0];
    let text=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"private new & <x>"}];
    let styles=[Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.runs[0].logical_run_id,family:hwpx_package::document_import::reference_targets::caption_frames::CaptionStyleFamily::Character,declaration_id:5}];
    let layouts=[Layout {caption_id:&frame.logical_caption_id,layout:CaptionLayout {side:NativeCaptionSide::Left,full_size:true,width_hwpunit:80,gap_hwpunit:12,last_width_hwpunit:40}}];
    let result=state.lower_sequence_batch_candidate(&bytes,&text,&layouts,&styles,&request,limits()?,WriterLimits::default())?;
    let r=result.receipt();assert_eq!(r.number_sequence.requested_events,events.len());assert!(r.number_sequence.document_start_bound&&r.number_sequence.complete_original_control_order_checked&&r.number_sequence.all_requested_values_read_back);
    assert!(!r.number_sequence.native_counter_interpretation_and_recalculation_qualified&&!r.execution_publication_authority);
    assert_eq!((r.content.output.changed_parts,r.content.output.text_changes.len(),r.content.output.layout_changes.len(),r.content.style_changes.len()),(2,1,1,1));
    let output=result.with_verified_bytes(<[u8]>::to_vec)?;let rebuilt=structure(&output,"number-sequence")?;let after=ImportedCaptionSourceState::import(&rebuilt,limits()?)?;
    assert_eq!(after.context().document_start().ok_or("begin")?.table,14);assert_eq!(after.numbering().section_starts()[0].picture,7);
    assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[31,32,33,34]);
    assert_eq!(after.frames().plain_text(&after.frames().frames()[0].segments[0].logical_source_id),Some(text[0].replacement));
    let after_parts=parts(&output)?;for (path,old) in parts(&bytes)?{if !matches!(path.as_str(),"Contents/header.xml"|"Contents/section0.xml"){assert_eq!(after_parts[&path],old);}}
    assert_eq!(state.verify_source(&bytes)?,*state.receipt());assert!(!format!("{request:?}{result:?}{}",serde_json::to_string(r)?).contains("private new"));Ok(())
}
#[test]
fn number_sequence_omission_duplicate_reordering_kind_fingerprint_join_and_document_presence_reject() -> TestResult {
    let bytes=package_for(&format!("<hp:ctrl><hp:newNum num='5' numType='PICTURE'/></hp:ctrl>{}",object(0,"<hp:t>oldA</hp:t>")))?;
    let source=structure(&bytes,"sequence-coverage")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let events=snapshot_events(&state)?;let begin=snapshot_begin(&state);
    let mut reverse=events.clone();reverse.reverse();let mut duplicate=events.clone();duplicate[1]=duplicate[0];
    let mut kind=events.clone();kind[0].values=NativeNumberEventValues::AutoNumber {category:Category::Picture,stored_number:7,format:NativeNumberFormatReplacement::Preserve};
    let foreign=LogicalId::parse("foreign-number-control")?;let mut foreign_events=events.clone();foreign_events[0].source_control_id=&foreign;
    let mut stale=events.clone();stale[0].source_fingerprint_sha256[0]^=1;
    for bad in [events[..1].to_vec(),reverse,duplicate,kind,foreign_events,stale] {
        let request=sequence(&state,&bad,begin);assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Selection)));
    }
    let missing=sequence(&state,&events,None);assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&missing,limits()?,WriterLimits::default()),Err(E::Selection)));
    let mut wrong=sequence(&state,&events,begin);wrong.expected_joined_state_sha256[0]^=1;
    assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&wrong,limits()?,WriterLimits::default()),Err(E::Source)));
    let request=sequence(&state,&events,begin);assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::NoChange)));
    let mut bad_format=events.clone();bad_format[0].values=NativeNumberEventValues::Restart {category:Category::Picture,stored_number:7,format:NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:"",suffix:"",superscript:false}};
    let request=sequence(&state,&bad_format,begin);assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Selection)));Ok(())
}
#[test]
fn number_sequence_all22_formats_categories_and_attribute_whitespace_roundtrip_without_plaintext_receipts() -> TestResult {
    let body=object(0,"<hp:t>oldA</hp:t>").replace("prefixChar=''","prefixChar=\"\"").replace("<hp:autoNumFormat ","<hp:autoNumFormat u:flag='KEEP' ");
    let bytes=package_for(&body)?;let source=structure(&bytes,"sequence-formats")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let formats=[NumberFormat::Digit,NumberFormat::CircledDigit,NumberFormat::RomanCapital,NumberFormat::RomanSmall,NumberFormat::LatinCapital,NumberFormat::LatinSmall,
        NumberFormat::CircledLatinCapital,NumberFormat::CircledLatinSmall,NumberFormat::HangulSyllable,NumberFormat::CircledHangulSyllable,NumberFormat::HangulJamo,
        NumberFormat::CircledHangulJamo,NumberFormat::HangulPhonetic,NumberFormat::Ideograph,NumberFormat::CircledIdeograph,NumberFormat::DecagonCircle,
        NumberFormat::DecagonCircleHanja,NumberFormat::Symbol,NumberFormat::UserChar,NumberFormat::Symbol2,NumberFormat::Image,NumberFormat::TwoDigit];
    let categories=[Category::Page,Category::Footnote,Category::Endnote,Category::Picture,Category::Table,Category::Equation,Category::TotalPage];
    let prefix="private prefix & <\"'>\t\r\n";let suffix="private suffix\n\t\r";
    for (i,format) in formats.into_iter().enumerate() {
        let mut events=snapshot_events(&state)?;events[0].values=NativeNumberEventValues::AutoNumber {category:categories[i%7],stored_number:if i==0{i32::MIN}else{i as i32},
            format:NativeNumberFormatReplacement::Replace {format,user_character:"★",prefix,suffix,superscript:true}};
        let request=sequence(&state,&events,snapshot_begin(&state));let result=state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default())?;
        let output=result.with_verified_bytes(<[u8]>::to_vec)?;let rebuilt=structure(&output,"sequence-formats")?;let after=ImportedCaptionNumbering::import(&rebuilt,limits()?)?;
        let found=after.controls()[0].format.as_ref().ok_or("format")?;
        assert_eq!(found.prefix_sha256,<[u8;32]>::from(Sha256::digest(prefix.as_bytes())));assert_eq!(found.suffix_sha256,<[u8;32]>::from(Sha256::digest(suffix.as_bytes())));
        assert_eq!(found.user_character_sha256,<[u8;32]>::from(Sha256::digest("★".as_bytes())));assert!(found.superscript);
        let xml=String::from_utf8(parts(&output)?["Contents/section0.xml"].clone())?;
        for value in ["&#9;","&#10;","&#13;","u:flag='KEEP'"]{assert!(xml.contains(value));}
        assert!(!format!("{request:?}{result:?}{}",serde_json::to_string(result.receipt())?).contains("private prefix"));
    }Ok(())
}
#[test]
fn number_sequence_preserves_numeric_noop_lexical_source_and_observed_ancestor_subtree_header_protection() -> TestResult {
    let body=object(0,"<hp:t>oldA</hp:t>").replace("num='19'","num='00019'");let bytes=package_for(&body)?;
    let source=structure(&bytes,"sequence-noop")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let events=snapshot_events(&state)?;
    let request=sequence(&state,&events,snapshot_begin(&state));let frame=&state.frames().frames()[0];
    let text=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"changed"}];
    let result=state.lower_sequence_batch_candidate(&bytes,&text,&[],&[],&request,limits()?,WriterLimits::default())?;
    assert!(result.receipt().number_sequence.nodes.iter().all(|n|n.changed_attributes==0));
    assert!(String::from_utf8(parts(&result.with_verified_bytes(<[u8]>::to_vec)?)?["Contents/section0.xml"].clone())?.contains("num='00019'"));
    for locked in [body.replace("lock='0'","lock='1'"),body.replace("<hp:caption ","<hp:caption lock='unknown' "),body.replace("<hp:run charPrIDRef='4'>","<hp:run charPrIDRef='4' lock='1'>"),
        body.replace("<hp:autoNum ","<hp:autoNum lock='1' "),body.replace("<hp:autoNumFormat ","<hp:autoNumFormat lock='1' "),fixture::table(&body).replace("lock=\"0\"","lock=\"1\"")] {
        let bytes=package_for(&locked)?;let source=structure(&bytes,"sequence-locked")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let mut events=snapshot_events(&state)?;
        events[0]=changed(events[0],7);let request=sequence(&state,&events,snapshot_begin(&state));
        assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Protection)));
    }
    let locked=rewrite(&bytes,|name,data|Ok(if name=="Contents/header.xml"{String::from_utf8(data)?.replace("<hh:head ","<hh:head lock='1' ").into_bytes()}else{data}))?;
    let source=structure(&locked,"sequence-header-lock")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let events=snapshot_events(&state)?;
    let mut begin=snapshot_begin(&state).ok_or("begin")?;begin.values.picture=4;let request=sequence(&state,&events,Some(begin));
    assert!(matches!(state.lower_sequence_batch_candidate(&locked,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Protection)));Ok(())
}
#[test]
fn number_sequence_multiple_parts_missing_document_start_and_exact_whole_form_proof_bindings() -> TestResult {
    let bytes=rewrite(&fixture::two_sections()?,|name,data|{
        if name=="Contents/header.xml"{return Ok(HEADER.as_bytes().to_vec());}
        if name.starts_with("Contents/section"){let i=usize::from(name.ends_with("section1.xml"));let text=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&object(i,"<hp:t>oldA</hp:t>"));
            return Ok(if i==1{text.replacen("<hp:p id='1'>","<hp:p id='2'>",1)}else{text}.into_bytes());}Ok(data)
    })?;
    let forms=base::forms(&bytes,"sequence-parts")?;let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;let mut events=snapshot_events(&state)?;
    assert!(snapshot_begin(&state).is_none());for (i,event) in events.iter_mut().enumerate(){*event=changed(*event,100+i as i32);}
    let request=sequence(&state,&events,None);let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let result=proof.lower_caption_state_sequence_batch_candidate(&forms,&state,&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default())?;
    assert_eq!(result.receipt().content.output.changed_parts,2);let output=result.with_verified_bytes(<[u8]>::to_vec)?;let rebuilt=structure(&output,"sequence-parts")?;
    let after=ImportedCaptionSourceState::import(&rebuilt,limits()?)?;
    let values=after.context().ordered_controls().iter().map(|o|after.numbering().controls().iter().find(|c|c.logical_control_id==o.logical_control_id).map(|c|c.stored_number).ok_or("ordered control")).collect::<Result<Vec<_>,_>>()?;
    assert_eq!(values,[100,101]);
    assert!(after.context().document_start().is_none());
    let other=base::forms(&bytes,"sequence-parts")?;let other_state=ImportedCaptionSourceState::import(other.body_structure(),limits()?)?;
    assert!(matches!(proof.lower_caption_state_sequence_batch_candidate(&forms,&other_state,&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Source)));
    assert!(matches!(proof.lower_caption_state_sequence_batch_candidate(&other,&state,&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Source)));
    let mut drift=bytes.clone();drift[0]^=1;
    assert!(matches!(state.lower_sequence_batch_candidate(&drift,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Source)));
    assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?),Err(E::Writer)));Ok(())
}
#[test]
fn number_sequence_many_events_reuse_part_guards_with_styles_and_reject_invalid_or_over_budget_formats() -> TestResult {
    let bytes=package_for(&(0..64).map(|i|format!("<hp:ctrl><hp:newNum num='{i}' numType='PICTURE'/></hp:ctrl>{}",object(i,"<hp:t>oldA</hp:t>"))).collect::<String>())?;
    let source=structure(&bytes,"sequence-many")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let mut events=snapshot_events(&state)?;
    assert_eq!(events.len(),128);for event in &mut events {let old=match event.values {NativeNumberEventValues::AutoNumber {stored_number,..}|NativeNumberEventValues::Restart {stored_number,..}=>stored_number,_=>return Err("unexpected start".into())};*event=changed(*event,old+1);}
    let request=sequence(&state,&events,snapshot_begin(&state));let frames=state.frames().frames();
    let texts=frames.iter().map(|f|Request {caption_id:&f.logical_caption_id,text_id:&f.segments[0].logical_source_id,replacement:"new"}).collect::<Vec<_>>();
    let styles=frames.iter().map(|f|Style {caption_id:&f.logical_caption_id,source_node_id:&f.runs[0].logical_run_id,family:hwpx_package::document_import::reference_targets::caption_frames::CaptionStyleFamily::Character,declaration_id:5}).collect::<Vec<_>>();
    let result=state.lower_sequence_batch_candidate(&bytes,&texts,&[],&styles,&request,limits()?,WriterLimits::default())?;
    let xml=source.source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").and_then(|p|p.xml()).ok_or("xml")?;
    assert_eq!(result.receipt().content.output.observed_protection_element_visits,4*xml.elements().len());assert_eq!(result.receipt().number_sequence.nodes.len(),129);
    assert_eq!(result.receipt().number_sequence.nodes.iter().filter(|n|n.changed_attributes>0).count(),128);
    let mut invalid=events.clone();invalid[1].values=NativeNumberEventValues::AutoNumber {category:Category::Picture,stored_number:4,format:NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:"bad\0",suffix:"",superscript:false}};
    let bad=sequence(&state,&invalid,snapshot_begin(&state));assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&bad,limits()?,WriterLimits::default()),Err(E::Value)));
    let oversized="X".repeat(limits()?.config().text_bytes+1);invalid[1].values=NativeNumberEventValues::AutoNumber {category:Category::Picture,stored_number:4,format:NativeNumberFormatReplacement::Replace {format:NumberFormat::Digit,user_character:"",prefix:&oversized,suffix:"",superscript:false}};
    let bad=sequence(&state,&invalid,snapshot_begin(&state));assert!(matches!(state.lower_sequence_batch_candidate(&bytes,&[],&[],&[],&bad,limits()?,WriterLimits::default()),Err(E::Limit)));Ok(())
}
