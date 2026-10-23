use super::*;
use domain_ir::SourceAnchorHandle;
use hwpx_package::{ElementSplicePosition as Position,NumberFormat,WriterLimitConfig};
use hwpx_package::document_import::{structure::{caption_number_topology::*,caption_numbering_sequence::{NativeDocumentStartValues,NativePageStartsOn},
    caption_edit_batch::CaptionLayoutReplacement as Layout,caption_layout::CaptionLayout,caption_style_batch::CaptionStyleReplacement as Style},
    reference_targets::{numbering::NativeNumberCategory as Category,caption_frames::CaptionStyleFamily}};
fn target(source:&ImportedDocumentStructure,path:&str,name:&str,nth:usize)->Result<SourceAnchorHandle,Box<dyn Error>> {
    let part=source.source().parts().iter().find(|p|p.path().as_str()==path).ok_or("part")?;
    let i=part.xml().ok_or("xml")?.elements().iter().enumerate().filter(|(_,e)|e.name().local_name()==name).nth(nth).ok_or("element")?.0;
    Ok(part.element_anchor(i).ok_or("anchor")?.clone())
}
fn run_target(source:&ImportedDocumentStructure)->Result<SourceAnchorHandle,Box<dyn Error>>{target(source,"Contents/section0.xml","run",1)}
fn restart(value:i32)->NativeInsertedNumberControl<'static>{NativeInsertedNumberControl::Restart {category:Category::Picture,stored_number:value,format:None}}
fn topology<'a>(state:&ImportedCaptionSourceState<'_>,deletions:&'a[NativeNumberDeletion<'a>],insertions:&'a[NativeNumberInsertion<'a>])->NativeNumberTopologyRequest<'a> {
    NativeNumberTopologyRequest {expected_joined_state_sha256:state.receipt().joined_state_sha256,deletions,insertions}
}
fn deletion<'a>(state:&'a ImportedCaptionSourceState<'_>,index:usize,remove:bool)->NativeNumberDeletion<'a>{
    let c=&state.numbering().controls()[index];NativeNumberDeletion {source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,remove_owned_empty_wrapper:remove}
}
fn output_state(bytes:&[u8],name:&str)->Result<Vec<i32>,Box<dyn Error>> {
    let source=structure(bytes,name)?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    Ok(state.numbering().controls().iter().map(|c|c.stored_number).collect())
}
fn package_for(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
    rewrite(&with_begin(body)?,|name,data|Ok(if name=="Contents/header.xml"{String::from_utf8(data)?.replace("<hh:charPr id='4'/>","<hh:charPr id='4'/><hh:charPr id='5'/>").into_bytes()}else{data}))
}
#[test]
fn number_topology_mixed_content_rebinds_shifted_text_and_preserves_all_other_parts() -> TestResult {
    let bytes=package_for(&format!("{}{}",object(0,"<hp:t>oldA</hp:t>"),object(1,"<hp:t>untouched</hp:t>")))?;
    let source=structure(&bytes,"topology-mixed")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let anchor=run_target(&source)?;let local=LogicalId::parse("insert-before-original-text")?;let controls=[restart(-7),restart(0)];
    let insertions=[NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::FirstChild,controls:&controls}];
    let deletions=[deletion(&state,0,true)];let request=topology(&state,&deletions,&insertions);let frame=&state.frames().frames()[0];
    let texts=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"private new & <본문>"},
        Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[2].logical_source_id,replacement:"last text"}];
    let styles=[Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.runs[0].logical_run_id,family:CaptionStyleFamily::Character,declaration_id:5}];
    let layouts=[Layout {caption_id:&frame.logical_caption_id,layout:CaptionLayout {side:domain_ir::NativeCaptionSide::Left,full_size:true,width_hwpunit:80,gap_hwpunit:12,last_width_hwpunit:40}}];
    let candidate=state.lower_topology_batch_candidate(&bytes,&texts,&layouts,&styles,&request,limits()?,WriterLimits::default())?;
    let r=candidate.receipt();let t=&r.number_topology;
    assert_eq!((t.original_controls,t.retained_controls,t.output_controls,t.inserted.len(),t.deleted.len()),(3,2,4,2,1));
    assert!(t.deleted[0].owned_empty_wrapper_removed&&t.complete_original_and_inserted_inventory_read_back);
    assert_eq!(t.caller_request_sha256,request.canonical_sha256(limits()?)?);
    assert!(!t.native_counter_recalculation_qualified&&!r.execution_publication_authority);
    assert_eq!((r.content.output.text_changes.len(),r.content.style_changes.len(),r.content.output.layout_changes.len()),(2,1,1));
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(output_state(&output,"topology-mixed")?,[-7,0,19]);
    let before=parts(&bytes)?;let after=parts(&output)?;for (name,old) in &before {if name!="Contents/section0.xml"{assert_eq!(&after[name],old);}}
    let xml=String::from_utf8(after["Contents/section0.xml"].clone())?;assert!(xml.contains("private new &amp; &lt;본문&gt;")&&xml.contains("last text")&&xml.contains("untouched"));
    assert!(r.content.output.outside_selected_edits_exact);
    assert!(!format!("{request:?}{candidate:?}{}",serde_json::to_string(r)?).contains("private new"));Ok(())
}
#[test]
fn number_topology_all22_formats_categories_and_affixes_are_one_bounded_forest() -> TestResult {
    let bytes=with_begin(&object(0,"<hp:t>oldA</hp:t>"))?;let source=structure(&bytes,"topology-formats")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let formats=[NumberFormat::Digit,NumberFormat::CircledDigit,NumberFormat::RomanCapital,NumberFormat::RomanSmall,NumberFormat::LatinCapital,NumberFormat::LatinSmall,
        NumberFormat::CircledLatinCapital,NumberFormat::CircledLatinSmall,NumberFormat::HangulSyllable,NumberFormat::CircledHangulSyllable,NumberFormat::HangulJamo,
        NumberFormat::CircledHangulJamo,NumberFormat::HangulPhonetic,NumberFormat::Ideograph,NumberFormat::CircledIdeograph,NumberFormat::DecagonCircle,
        NumberFormat::DecagonCircleHanja,NumberFormat::Symbol,NumberFormat::UserChar,NumberFormat::Symbol2,NumberFormat::Image,NumberFormat::TwoDigit];
    let categories=[Category::Page,Category::Footnote,Category::Endnote,Category::Picture,Category::Table,Category::Equation,Category::TotalPage];let prefix="private prefix & <\"'>\t\r\n";
    let controls=formats.into_iter().enumerate().map(|(i,format)|NativeInsertedNumberControl::AutoNumber {category:categories[i%7],stored_number:if i==0{i32::MIN}else{i as i32},
        format:NativeInsertedNumberFormat {format,user_character:"★",prefix,suffix:"\n\t\r",superscript:true}}).collect::<Vec<_>>();
    let anchor=run_target(&source)?;let local=LogicalId::parse("formats")?;
    let insertions=[NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::FirstChild,controls:&controls}];let request=topology(&state,&[],&insertions);
    let candidate=state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default())?;
    assert_eq!(candidate.receipt().number_topology.inserted.len(),22);let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;let after=structure(&output,"topology-formats")?;
    let after=ImportedCaptionSourceState::import(&after,limits()?)?;
    for (i,c) in after.numbering().controls()[..22].iter().enumerate(){let f=c.format.as_ref().ok_or("format")?;assert_eq!(c.category,categories[i%7]);
        assert_eq!(f.prefix_sha256,<[u8;32]>::from(Sha256::digest(prefix.as_bytes())));assert!(f.superscript);}
    let xml=String::from_utf8(parts(&output)?["Contents/section0.xml"].clone())?;for escaped in ["&#9;","&#10;","&#13;","&amp;","&quot;"]{assert!(xml.contains(escaped));}
    assert!(!serde_json::to_string(candidate.receipt())?.contains("private prefix"));Ok(())
}
#[test]
fn number_topology_empty_parents_grouped_insertions_and_explicit_document_section_starts() -> TestResult {
    for empty in ["<hp:run/>","<hp:run><hp:ctrl/></hp:run>","<hp:run><hp:secPr/></hp:run>"] {
        let bytes=package(&fixture::paragraph("").replace("<hp:run></hp:run>",empty))?;
        let source=structure(&bytes,"topology-empty")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
        let name=if empty.contains("ctrl"){"ctrl"}else if empty.contains("secPr"){"secPr"}else{"run"};
        let anchor=target(&source,"Contents/section0.xml",name,0)?;let header=target(&source,"Contents/header.xml","head",0)?;
        let local=LogicalId::parse("empty-first")?;let local2=LogicalId::parse("empty-second")?;let local3=LogicalId::parse("document")?;
        let controls=if name=="secPr"{vec![NativeInsertedNumberControl::SectionStart {page_starts_on:NativePageStartsOn::Odd,page:0,picture:7,table:8,equation:9}]}else{vec![restart(3)]};
        let begin=[NativeInsertedNumberControl::DocumentStart(NativeDocumentStartValues {page:0,footnote:1,endnote:2,picture:3,table:4,equation:5})];
        let mut insertions=vec![NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::FirstChild,controls:&controls},NativeNumberInsertion {local_id:&local3,target:&header,position:Position::FirstChild,controls:&begin}];
        if name!="secPr"{insertions.push(NativeNumberInsertion {local_id:&local2,target:&anchor,position:Position::LastChild,controls:&controls});}
        let request=topology(&state,&[],&insertions);let candidate=state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default())?;
        let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;let after=structure(&output,"topology-empty")?;let after=ImportedCaptionSourceState::import(&after,limits()?)?;
        assert_eq!(after.context().document_start().ok_or("begin")?.page,0);
        if name=="secPr"{assert_eq!(after.numbering().section_starts()[0].page_starts_on,"ODD");}else{assert_eq!(after.numbering().controls().len(),2);}
    }
    // Missing document starts stay missing unless explicitly requested.
    let bytes=package(&fixture::paragraph("<hp:ctrl/>"))?;let source=structure(&bytes,"topology-no-default")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let anchor=target(&source,"Contents/section0.xml","ctrl",0)?;let local=LogicalId::parse("no-default")?;let controls=[restart(0)];let insertions=[NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::LastChild,controls:&controls}];
    let candidate=state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&topology(&state,&[],&insertions),limits()?,WriterLimits::default())?;
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;let after=structure(&output,"topology-no-default")?;assert!(ImportedCaptionSourceState::import(&after,limits()?)?.context().document_start().is_none());Ok(())
}
#[test]
fn number_topology_deletion_preserves_unknown_wrapper_content_and_boundary_replacement_is_atomic() -> TestResult {
    for (extra,remove) in [("",true),(" u:flag='KEEP'",false)] {
        let body=object(0,"<hp:t>oldA</hp:t>").replace("<hp:ctrl>",&format!("<hp:ctrl{extra}>"));let bytes=with_begin(&body)?;
        let source=structure(&bytes,"topology-delete")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let deletions=[deletion(&state,0,true)];
        let result=state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&topology(&state,&deletions,&[]),limits()?,WriterLimits::default())?;
        assert_eq!(result.receipt().number_topology.deleted[0].owned_empty_wrapper_removed,remove);
        let xml=String::from_utf8(parts(&result.with_verified_bytes(<[u8]>::to_vec)?)?["Contents/section0.xml"].clone())?;
        assert_eq!(xml.contains("<hp:ctrl"),!remove);if !remove{assert!(xml.contains("u:flag='KEEP'"));}
    }
    let body=object(0,"<hp:t>oldA</hp:t>").replace("<hp:ctrl>","<hp:ctrl><!--keep--><hp:newNum num='2' numType='PICTURE'/>");
    let bytes=with_begin(&body)?;let source=structure(&bytes,"topology-replace")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let deletions=[deletion(&state,1,true)];let anchor=target(&source,"Contents/section0.xml","autoNum",0)?;let local=LogicalId::parse("replacement")?;let controls=[restart(4),restart(5)];
    let insertions=[NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::Before,controls:&controls}];
    let request=topology(&state,&deletions,&insertions);let result=state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default())?;
    let output=result.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(output_state(&output,"topology-replace")?,[2,4,5]);
    assert!(String::from_utf8(parts(&output)?["Contents/section0.xml"].clone())?.contains("<!--keep-->"));
    assert!(!result.receipt().number_topology.deleted[0].owned_empty_wrapper_removed);Ok(())
}
#[test]
fn number_topology_rejects_stale_duplicate_foreign_protected_slots_limits_and_no_partial_output() -> TestResult {
    let bytes=with_begin(&object(0,"<hp:t>oldA</hp:t>"))?;let source=structure(&bytes,"topology-reject")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let local=LogicalId::parse("request")?;let anchor=run_target(&source)?;let controls=[restart(4)];let insertions=[NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::FirstChild,controls:&controls}];
    let good=topology(&state,&[],&insertions);let mut stale=topology(&state,&[],&insertions);stale.expected_joined_state_sha256[0]^=1;
    assert!(matches!(state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&stale,limits()?,WriterLimits::default()),Err(E::Source)));
    let mut stale_anchor=anchor.clone();stale_anchor.fingerprint_sha256[0]^=1;let foreign=target(&source,"Contents/section0.xml","t",0)?;
    for (anchor,position) in [(&stale_anchor,Position::FirstChild),(&foreign,Position::FirstChild),(&anchor,Position::Subtree)] {
        let bad=[NativeNumberInsertion {local_id:&local,target:anchor,position,controls:&controls}];assert!(state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&topology(&state,&[],&bad),limits()?,WriterLimits::default()).is_err());
    }
    let d=deletion(&state,0,false);let duplicate=[d,d];assert!(matches!(state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&topology(&state,&duplicate,&[]),limits()?,WriterLimits::default()),Err(E::Selection)));
    let duplicate_insert=[NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::FirstChild,controls:&controls},NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::LastChild,controls:&controls}];
    assert!(matches!(state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&topology(&state,&[],&duplicate_insert),limits()?,WriterLimits::default()),Err(E::Selection)));
    let invalid=[NativeInsertedNumberControl::AutoNumber {category:Category::Page,stored_number:0,format:NativeInsertedNumberFormat {format:NumberFormat::Digit,user_character:"\0",prefix:"",suffix:"",superscript:false}}];
    let bad=[NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::FirstChild,controls:&invalid}];assert!(matches!(topology(&state,&[],&bad).canonical_sha256(limits()?),Err(E::Value)));
    let oversized="x".repeat(limits()?.config().text_bytes+1);let invalid=[NativeInsertedNumberControl::Restart {category:Category::Page,stored_number:0,format:Some(NativeInsertedNumberFormat {format:NumberFormat::Digit,user_character:&oversized,prefix:"",suffix:"",superscript:false})}];
    let bad=[NativeNumberInsertion {local_id:&local,target:&anchor,position:Position::FirstChild,controls:&invalid}];assert!(matches!(topology(&state,&[],&bad).canonical_sha256(limits()?),Err(E::Limit)));
    assert!(matches!(state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&good,limits()?,WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?),Err(E::Writer)));
    for locked in [object(0,"<hp:t>oldA</hp:t>").replace("lock='0'","lock='1'"),object(0,"<hp:t>oldA</hp:t>").replace("<hp:autoNumFormat ","<hp:autoNumFormat lock='1' ")] {
        let bytes=with_begin(&locked)?;let source=structure(&bytes,"topology-lock")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let deletions=[deletion(&state,0,true)];
        assert!(matches!(state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&topology(&state,&deletions,&[]),limits()?,WriterLimits::default()),Err(E::Protection)));
    }Ok(())
}
#[test]
fn number_topology128_edits_share_protection_maps_and_whole_proof_binds_exact_original() -> TestResult {
    let bytes=package_for(&(0..64).map(|i|object(i,"<hp:t>oldA</hp:t>")).collect::<String>())?;
    let forms=base::forms(&bytes,"topology-many")?;let source=forms.body_structure();let state=ImportedCaptionSourceState::import(source,limits()?)?;
    let anchors=state.frames().frames().iter().map(|f|{let r=&f.runs[0];Ok(SourceAnchorHandle {opaque_handle:LogicalId::parse(r.logical_run_id.as_str().strip_prefix("caption-run-").ok_or("run")?)?,fingerprint_sha256:r.source_fingerprint_sha256})}).collect::<Result<Vec<_>,Box<dyn Error>>>()?;
    let ids=(0..64).map(|i|LogicalId::parse(format!("local-{i}"))).collect::<Result<Vec<_>,_>>()?;let controls=[restart(3)];
    let insertions=anchors.iter().zip(&ids).map(|(target,local_id)|NativeNumberInsertion {local_id,target,position:Position::FirstChild,controls:&controls}).collect::<Vec<_>>();
    let deletions=(0..64).map(|i|deletion(&state,i,true)).collect::<Vec<_>>();let request=topology(&state,&deletions,&insertions);
    let frames=state.frames().frames();let texts=frames.iter().map(|f|Request {caption_id:&f.logical_caption_id,text_id:&f.segments[0].logical_source_id,replacement:"changed"}).collect::<Vec<_>>();
    let styles=frames.iter().map(|f|Style {caption_id:&f.logical_caption_id,source_node_id:&f.runs[0].logical_run_id,family:CaptionStyleFamily::Character,declaration_id:5}).collect::<Vec<_>>();
    let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let result=proof.lower_caption_state_topology_batch_candidate(&forms,&state,&bytes,&texts,&[],&styles,&request,limits()?,WriterLimits::default())?;
    let n=source.source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").and_then(|p|p.xml()).ok_or("xml")?.elements().len();
    assert_eq!(result.receipt().content.output.observed_protection_element_visits,4*n);assert_eq!(result.receipt().number_topology.inserted.len(),64);
    assert_eq!(output_state(&result.with_verified_bytes(<[u8]>::to_vec)?,"topology-many")?,vec![3;64]);
    let other=base::forms(&bytes,"topology-many")?;let foreign=ImportedCaptionSourceState::import(other.body_structure(),limits()?)?;
    assert!(matches!(proof.lower_caption_state_topology_batch_candidate(&forms,&foreign,&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Source)));
    assert!(matches!(proof.lower_caption_state_topology_batch_candidate(&other,&state,&bytes,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Source)));
    let mut stale=bytes.clone();stale[0]^=1;assert!(matches!(state.lower_topology_batch_candidate(&stale,&[],&[],&[],&request,limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
}
#[test]
fn number_topology_document_and_section_deletion_replacement_and_multi_part_inventory() -> TestResult {
    let bytes=rewrite(&fixture::two_sections()?,|name,data| {
        if name=="Contents/header.xml"{return Ok(HEADER.replace("<hh:refList>",&format!("{BEGIN}<hh:refList>")).into_bytes());}
        if name.starts_with("Contents/section") {let i=usize::from(name.ends_with("section1.xml"));let text=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&format!("<hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='1' tbl='2' equation='3'/></hp:secPr>{}",object(i,"<hp:t>oldA</hp:t>")));
            return Ok(if i==1{text.replacen("<hp:p id='1'>","<hp:p id='2'>",1)}else{text}.into_bytes());}Ok(data)
    })?;
    let source=structure(&bytes,"topology-parts")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let begin=state.context().document_start().ok_or("begin")?;let section=&state.numbering().section_starts()[0];
    let deletions=[NativeNumberDeletion {source_control_id:&begin.logical_control_id,source_fingerprint_sha256:begin.source_fingerprint_sha256,remove_owned_empty_wrapper:false},
        NativeNumberDeletion {source_control_id:&section.logical_control_id,source_fingerprint_sha256:section.source_fingerprint_sha256,remove_owned_empty_wrapper:false}];
    let removed=state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&topology(&state,&deletions,&[]),limits()?,WriterLimits::default())?;
    let output=removed.with_verified_bytes(<[u8]>::to_vec)?;let after=structure(&output,"topology-parts")?;let after=ImportedCaptionSourceState::import(&after,limits()?)?;
    assert!(after.context().document_start().is_none());assert_eq!(after.numbering().section_starts().len(),1);assert_eq!(after.numbering().controls().len(),2);
    let a=target(&source,"Contents/header.xml","beginNum",0)?;let b=target(&source,"Contents/section0.xml","startNum",0)?;
    let c=target(&source,"Contents/section1.xml","autoNum",0)?;
    let ids=[LogicalId::parse("document-replace")?,LogicalId::parse("section-replace")?,LogicalId::parse("other-part")?];
    let document=[NativeInsertedNumberControl::DocumentStart(NativeDocumentStartValues {page:0,footnote:2,endnote:3,picture:4,table:5,equation:6})];
    let start=[NativeInsertedNumberControl::SectionStart {page_starts_on:NativePageStartsOn::Even,page:0,picture:8,table:9,equation:10}];let other=[restart(4)];
    let insertions=[NativeNumberInsertion {local_id:&ids[0],target:&a,position:Position::Before,controls:&document},NativeNumberInsertion {local_id:&ids[1],target:&b,position:Position::After,controls:&start},NativeNumberInsertion {local_id:&ids[2],target:&c,position:Position::After,controls:&other}];
    let result=state.lower_topology_batch_candidate(&bytes,&[],&[],&[],&topology(&state,&deletions,&insertions),limits()?,WriterLimits::default())?;
    assert_eq!(result.receipt().content.output.changed_parts,3);assert_eq!((result.receipt().number_topology.original_controls,result.receipt().number_topology.retained_controls,result.receipt().number_topology.output_controls),(5,3,6));
    let output=result.with_verified_bytes(<[u8]>::to_vec)?;let after=structure(&output,"topology-parts")?;let after=ImportedCaptionSourceState::import(&after,limits()?)?;
    assert_eq!(after.context().document_start().ok_or("begin")?.picture,4);assert_eq!(after.numbering().section_starts()[0].page_starts_on,"EVEN");assert_eq!(after.numbering().section_starts()[1].page_starts_on,"BOTH");
    assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[19,19,4]);Ok(())
}
