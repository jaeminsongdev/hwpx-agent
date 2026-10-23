use super::*;
use hwpx_package::document_import::{structure::{caption_topology::*,caption_number_topology::{NativeInsertedNumberControl as Number,NativeInsertedNumberFormat as NumberStyle},
    caption_edit_batch::CaptionLayoutReplacement as Layout,caption_style_batch::CaptionStyleReplacement as Style,caption_layout::CaptionLayout},reference_targets::numbering::NativeNumberCategory as Category};
use hwpx_package::NumberFormat;
const ITEMS1:&[CaptionContent<'static>]=&[CaptionContent::Text("private new label & <x>\r\n"),CaptionContent::Number(Number::AutoNumber {category:Category::Picture,stored_number:9,format:NumberStyle {format:NumberFormat::RomanCapital,user_character:"★",prefix:"[",suffix:"]",superscript:true}}),CaptionContent::Text("private body")];
const ITEMS2:&[CaptionContent<'static>]=&[CaptionContent::Text("private continuation"),CaptionContent::Number(Number::Restart {category:Category::Picture,stored_number:2,format:None})];
const RUN1:&[CaptionRun<'static>]=&[CaptionRun {character_style:4,content:ITEMS1}];
const RUN2:&[CaptionRun<'static>]=&[CaptionRun {character_style:4,content:ITEMS2}];
const PARAGRAPHS:&[CaptionParagraph<'static>]=&[CaptionParagraph {paragraph_style:6,named_style:8,runs:RUN1},CaptionParagraph {paragraph_style:6,named_style:8,runs:RUN2}];
const HEADER_FULL:&str="<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head'><hh:beginNum page='0' footnote='1' endnote='1' pic='0' tbl='0' equation='0'/><hh:refList><hh:charProperties><hh:charPr id='4'/><hh:charPr id='5'/></hh:charProperties><hh:paraProperties><hh:paraPr id='6'/><hh:paraPr id='7'/></hh:paraProperties><hh:styles><hh:style id='8'/><hh:style id='9'/></hh:styles><hh:borderFills><hh:borderFill id='1'/></hh:borderFills></hh:refList></hh:head>";
fn package_for(body:&str)->Result<Vec<u8>,Box<dyn Error>> {rewrite(&package(&fixture::paragraph(body))?,|name,data|Ok(if name=="Contents/header.xml"{HEADER_FULL.as_bytes().to_vec()}else{data}))}
fn bare(i:usize)->String{format!("<hp:rect id='{}' lock='0' u:keep='yes' />",500+i)}
fn layout()->CaptionLayout {CaptionLayout {side:domain_ir::NativeCaptionSide::Bottom,full_size:false,width_hwpunit:1000,gap_hwpunit:20,last_width_hwpunit:900}}
fn creation<'a>(owner:&'a hwpx_package::document_import::reference_targets::numbering::context::NativeNumberingOwnerObservation,local:&'a LogicalId)->CaptionCreation<'a>{
    CaptionCreation {local_id:local,object_id:&owner.logical_object_id,object_fingerprint_sha256:owner.source_fingerprint_sha256,layout:layout(),paragraphs:PARAGRAPHS}
}
fn deletion<'a>(frame:&'a hwpx_package::document_import::reference_targets::caption_frames::CaptionSourceFrame)->CaptionDeletion<'a>{CaptionDeletion {caption_id:&frame.logical_caption_id,caption_fingerprint_sha256:frame.source_fingerprint_sha256}}
fn request<'a>(state:&ImportedCaptionSourceState<'_>,deletions:&'a[CaptionDeletion<'a>],creations:&'a[CaptionCreation<'a>])->SourceCaptionTopologyRequest<'a>{SourceCaptionTopologyRequest {expected_joined_state_sha256:state.receipt().joined_state_sha256,deletions,creations}}
fn caption_owner_profile_boundaries() -> TestResult {
    use hwpx_package::{BoundedZipReader,IdIndex,IdIndexLimits,IdIssueKind,IdRuleProfile,PackageGraph,PackageGraphLimits,PackageLimits};
    let check=|body:&str,profile|->Result<Result<IdIndex,hwpx_package::IdIndexError>,Box<dyn Error>>{
        let bytes=package_for(body)?;let mut reader=BoundedZipReader::open(Cursor::new(bytes),PackageLimits::default())?;
        let graph=PackageGraph::build(&mut reader,PackageGraphLimits::default())?;
        Ok(IdIndex::build(&mut reader,&graph,profile,IdIndexLimits::default()))
    };
    let v6=IdRuleProfile::hwpml_2011_shape_v6();let v7=IdRuleProfile::hwpml_2016_ooxml_chart_v7();let v8=IdRuleProfile::hwpml_2011_caption_owner_v8();
    assert_eq!(v6.version(),"hwpml-2011-shape-static/v6");assert_eq!(v7.version(),"hwpml-2016-ooxml-chart/v7");assert_eq!(v8.version(),"hwpml-2011-caption-owner-static/v8");
    assert!(check("<hp:rect id='500' instid='600'/>",v6)?.is_ok());assert!(check("<hp:chart id='500'/>",v7)?.is_ok());
    let extended="<hp:arc id='500' instid='600'/><hp:connectLine id='501' instid='601'/>";
    for profile in [v6,v7]{let error=check(extended,profile)?.err().ok_or("legacy profile unexpectedly extended")?;
        assert!(error.validation().ok_or("missing validation")?.issues().iter().any(|i|i.kind()==IdIssueKind::UnknownIdLikeAttribute));}
    assert!(check(extended,v8)?.is_ok());
    for (body,expected) in [
        ("<hp:rect id='500'/><hp:arc id='500'/>",IdIssueKind::DuplicateDeclaration),
        ("<hp:arc id='500' instid='600'/><hp:connectLine id='501' instid='600'/>",IdIssueKind::DuplicateDeclaration),
        ("<hp:arc id='500' unknownIDRef='600'/>",IdIssueKind::UnknownIdLikeAttribute),
        ("<hp:connectLine id='500'><hp:startPt subjectIDRef='600'/></hp:connectLine>",IdIssueKind::UnknownIdLikeAttribute),
        ("<hp:chart id='500'/>",IdIssueKind::UnknownIdLikeAttribute),
        ("<hp:arc u:id='500'/>",IdIssueKind::UnknownIdLikeAttribute),
    ] {let error=check(body,v8)?.err().ok_or("invalid profile fixture admitted")?;
        assert!(error.validation().ok_or("missing validation")?.issues().iter().any(|i|i.kind()==expected));}
    let opaque=check("<u:arc id='500'/>",v8)?;
    assert!(opaque?.declarations().iter().all(|d|!matches!(d.kind(),hwpx_package::IdKind::Shape|hwpx_package::IdKind::ShapeInstance)));
    Ok(())
}
#[test]
fn caption_structure_mixed_creation_deletion_rebinds_retained_text_layout_and_three_styles() -> TestResult {
    let bytes=package_for(&format!("{}{}{}{}",bare(0),bare(1),object(2,"<hp:t>oldA</hp:t>"),object(3,"<hp:t>retained</hp:t>")))?;
    let source=structure(&bytes,"caption-structure")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let frames=state.frames().frames();let owners=state.context().owners();
    let ids=[LogicalId::parse("private first caption")?,LogicalId::parse("private second caption")?];let creations=[creation(&owners[0],&ids[0]),creation(&owners[1],&ids[1])];let deletions=[deletion(&frames[0])];
    let topology=request(&state,&deletions,&creations);let texts=[Request {caption_id:&frames[1].logical_caption_id,text_id:&frames[1].segments[0].logical_source_id,replacement:"private retained update"}];
    let layouts=[Layout {caption_id:&frames[1].logical_caption_id,layout:CaptionLayout {side:domain_ir::NativeCaptionSide::Left,..layout()}}];
    let styles=[Style {caption_id:&frames[1].logical_caption_id,source_node_id:&frames[1].runs[0].logical_run_id,family:hwpx_package::document_import::reference_targets::caption_frames::CaptionStyleFamily::Character,declaration_id:5},
        Style {caption_id:&frames[1].logical_caption_id,source_node_id:&frames[1].paragraphs[0].logical_paragraph_id,family:hwpx_package::document_import::reference_targets::caption_frames::CaptionStyleFamily::Paragraph,declaration_id:7},
        Style {caption_id:&frames[1].logical_caption_id,source_node_id:&frames[1].paragraphs[0].logical_paragraph_id,family:hwpx_package::document_import::reference_targets::caption_frames::CaptionStyleFamily::Named,declaration_id:9}];
    let candidate=state.lower_caption_structure_candidate(&bytes,&topology,&texts,&layouts,&styles,limits()?,WriterLimits::default())?;let r=candidate.receipt();let t=&r.caption_topology;
    assert_eq!((t.original_captions,t.output_captions,t.created.len(),t.deleted.len(),t.retained_native_controls,t.created_native_controls),(2,3,2,1,2,4));
    assert!(t.complete_owner_caption_and_native_control_inventory_read_back&&!t.native_counter_recalculation_qualified&&!r.execution_publication_authority);
    assert_eq!(t.caller_request_sha256,topology.canonical_sha256(limits()?)?);assert_eq!(t.created.iter().flat_map(|c|c.allocated_paragraph_ids.iter().copied()).collect::<Vec<_>>(),[103,104,105,106]);
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;let rebuilt=structure(&output,"caption-structure")?;let after=ImportedCaptionSourceState::import(&rebuilt,limits()?)?;
    assert_eq!(after.frames().frames().len(),3);let retained=&after.frames().frames()[2];assert_eq!(after.frames().plain_text(&retained.segments[0].logical_source_id),Some("private retained update"));
    assert_eq!((retained.runs[0].character_style.reference_id,retained.paragraphs[0].paragraph_style.reference_id,retained.paragraphs[0].named_style.reference_id),(Some(5),Some(7),Some(9)));
    assert_eq!(after.numbering().caption_import().envelopes()[2].native_envelope().side,domain_ir::NativeCaptionSide::Left);
    assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[9,2,9,2,19]);assert_eq!(after.context().document_start().ok_or("begin")?.page,0);
    let before=parts(&bytes)?;let after_parts=parts(&output)?;for (path,old) in before{if path!="Contents/section0.xml"{assert_eq!(after_parts[&path],old);}}
    assert!(String::from_utf8(after_parts["Contents/section0.xml"].clone())?.contains("u:keep='yes'"));
    let safe=format!("{topology:?}{candidate:?}{}",serde_json::to_string(r)?);for value in ["private new label","private first caption","private retained update"]{assert!(!safe.contains(value));}Ok(())
}
#[test]
fn caption_structure_whole_deletion_and_explicit_replacement_preserve_other_source_bytes() -> TestResult {
    let body=object(0,"<hp:t>oldA</hp:t>").replace("<hp:caption ","<hp:caption u:future='unknown' ").replace("</hp:subList>","<!--private retained until deletion--></hp:subList>");
    let bytes=package_for(&body)?;let source=structure(&bytes,"caption-structure")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let deletions=[deletion(&state.frames().frames()[0])];let removed=state.lower_caption_structure_candidate(&bytes,&request(&state,&deletions,&[]),&[],&[],&[],limits()?,WriterLimits::default())?;
    let output=removed.with_verified_bytes(<[u8]>::to_vec)?;let after=structure(&output,"caption-structure")?;let after=ImportedCaptionSourceState::import(&after,limits()?)?;
    assert!(after.frames().frames().is_empty()&&after.numbering().controls().is_empty()&&after.context().owners()[0].logical_caption_id.is_none());assert_eq!(removed.receipt().caption_topology.retained_native_controls,1);
    let local=LogicalId::parse("replacement")?;let creations=[creation(&state.context().owners()[0],&local)];let replacement=state.lower_caption_structure_candidate(&bytes,&request(&state,&deletions,&creations),&[],&[],&[],limits()?,WriterLimits::default())?;
    let output=replacement.with_verified_bytes(<[u8]>::to_vec)?;let after=structure(&output,"caption-structure")?;let after=ImportedCaptionSourceState::import(&after,limits()?)?;assert_eq!(after.frames().frames().len(),1);
    assert_eq!(after.numbering().controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[9,2]);assert_eq!(replacement.receipt().caption_topology.created[0].allocated_paragraph_ids,[100,101]);
    let before=parts(&bytes)?;let old=String::from_utf8(before["Contents/section0.xml"].clone())?;let new=String::from_utf8(parts(&output)?["Contents/section0.xml"].clone())?;
    let start=old.find("<hp:caption ").ok_or("old")?;let end=old.find("</hp:caption>").ok_or("end")?+"</hp:caption>".len();let new_start=new.find("<hp:caption ").ok_or("new")?;let new_end=new.find("</hp:caption>").ok_or("end")?+"</hp:caption>".len();
    assert_eq!(&old[..start],&new[..new_start]);assert_eq!(&old[end..],&new[new_end..]);Ok(())
}
#[test]
fn caption_structure_all_ten_owner_kinds_and_two_parts_use_one_id_scan_per_part() -> TestResult {
    caption_owner_profile_boundaries()?;
    let mut body=String::new();for (i,name) in ["pic","rect","ellipse","line","arc","polygon","curve","connectLine","equation"].iter().enumerate(){body.push_str(&format!("<hp:{name} id='{}' lock='0'/>",500+i));}
    body.push_str(&fixture::table("<hp:t>cell</hp:t>").replace("<hp:p id='1'>","<hp:p id='700'>"));
    let bytes=rewrite(&fixture::two_sections()?,|name,data|{if name=="Contents/header.xml"{return Ok(HEADER_FULL.as_bytes().to_vec());}if name.starts_with("Contents/section") {let second=name.ends_with("section1.xml");let replacement=if second{bare(100)}else{body.clone()};let text=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&replacement);return Ok(if second{text.replacen("<hp:p id='1'>","<hp:p id='2'>",1)}else{text}.into_bytes());}Ok(data)})?;
    let source=structure(&bytes,"caption-structure")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;assert_eq!(state.context().owners().len(),11);assert!(state.frames().frames().is_empty());
    let ids=(0..11).map(|i|LogicalId::parse(format!("create-{i}"))).collect::<Result<Vec<_>,_>>()?;let creations=state.context().owners().iter().zip(&ids).map(|(owner,id)|creation(owner,id)).collect::<Vec<_>>();
    let result=state.lower_caption_structure_candidate(&bytes,&request(&state,&[],&creations),&[],&[],&[],limits()?,WriterLimits::default())?;let output=result.with_verified_bytes(<[u8]>::to_vec)?;
    let after=structure(&output,"caption-structure")?;let after=ImportedCaptionSourceState::import(&after,limits()?)?;assert_eq!(after.frames().frames().len(),11);assert_eq!(after.numbering().controls().len(),22);assert_eq!(result.receipt().content.output.changed_parts,2);
    assert_eq!(result.receipt().content.output.id_rule_profile,"hwpml-2011-caption-owner-static/v8");
    let scanned=source.source().parts().iter().filter(|p|p.path().as_str().starts_with("Contents/section")).map(|p|p.xml().unwrap().elements().len()).sum::<usize>();assert_eq!(result.receipt().caption_topology.paragraph_id_elements_scanned,scanned);
    assert_eq!(result.receipt().caption_topology.created[0].allocated_paragraph_ids,[701,702]);assert_eq!(result.receipt().caption_topology.created[10].allocated_paragraph_ids,[3,4]);Ok(())
}
#[test]
fn caption_structure_invalid_stale_duplicate_style_scope_and_deleted_noop_selections_reject() -> TestResult {
    let bytes=package_for(&format!("{}{}",bare(0),object(0,"<hp:t>oldA</hp:t>")))?;let source=structure(&bytes,"caption-structure")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let owner=&state.context().owners()[0];let frame=&state.frames().frames()[0];let local=LogicalId::parse("new")?;
    let good=creation(owner,&local);let deletions=[deletion(frame)];
    let bad_creation=[creation(&state.context().owners()[1],&local)];assert!(matches!(state.lower_caption_structure_candidate(&bytes,&request(&state,&[],&bad_creation),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Selection)));
    let duplicate=[creation(owner,&local),creation(owner,&local)];assert!(matches!(state.lower_caption_structure_candidate(&bytes,&request(&state,&[],&duplicate),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Selection)));
    let mut stale=creation(owner,&local);stale.object_fingerprint_sha256[0]^=1;assert!(matches!(state.lower_caption_structure_candidate(&bytes,&request(&state,&[],&[stale]),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Selection)));
    let mut stale=deletions[0];stale.caption_fingerprint_sha256[0]^=1;for bad in [vec![stale],vec![deletions[0],deletions[0]],vec![CaptionDeletion {caption_id:&local,..deletions[0]}]]{assert!(matches!(state.lower_caption_structure_candidate(&bytes,&request(&state,&bad,&[]),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Selection)));}
    let bad_runs=[CaptionRun {character_style:987,content:ITEMS1}];let bad_body=[CaptionParagraph {paragraph_style:6,named_style:8,runs:&bad_runs}];let bad=[CaptionCreation {paragraphs:&bad_body,..creation(owner,&local)}];assert!(matches!(state.lower_caption_structure_candidate(&bytes,&request(&state,&[],&bad),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Selection)));
    let bad=[CaptionCreation {paragraphs:&[],..good}];assert!(matches!(request(&state,&[],&bad).canonical_sha256(limits()?),Err(E::Value)));
    let text=[Request {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement:"oldA"}];let topology=request(&state,&deletions,&[]);
    assert!(matches!(state.lower_caption_structure_candidate(&bytes,&topology,&text,&[],&[],limits()?,WriterLimits::default()),Err(E::Selection)));
    let layout_request=[Layout {caption_id:&frame.logical_caption_id,layout:layout()}];assert!(matches!(state.lower_caption_structure_candidate(&bytes,&topology,&[],&layout_request,&[],limits()?,WriterLimits::default()),Err(E::Selection)));
    let style=[Style {caption_id:&frame.logical_caption_id,source_node_id:&frame.runs[0].logical_run_id,family:hwpx_package::document_import::reference_targets::caption_frames::CaptionStyleFamily::Character,declaration_id:4}];assert!(matches!(state.lower_caption_structure_candidate(&bytes,&topology,&[],&[],&style,limits()?,WriterLimits::default()),Err(E::Selection)));
    let creates=[creation(owner,&local)];let mut stale=request(&state,&[],&creates);stale.expected_joined_state_sha256[0]^=1;assert!(matches!(state.lower_caption_structure_candidate(&bytes,&stale,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
}
#[test]
fn caption_structure_whole_proof_source_writer_limits_id_exhaustion_and_protection_hold() -> TestResult {
    let bytes=package_for(&bare(0))?;let forms=base::forms(&bytes,"caption-structure")?;let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;let local=LogicalId::parse("new")?;let creates=[creation(&state.context().owners()[0],&local)];let topology=request(&state,&[],&creates);let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let result=proof.lower_caption_state_structure_candidate(&forms,&state,&bytes,&topology,&[],&[],&[],limits()?,WriterLimits::default())?;assert_eq!(result.receipt().caption_topology.created[0].allocated_paragraph_ids,[2,3]);
    let other=base::forms(&bytes,"caption-structure")?;let foreign=ImportedCaptionSourceState::import(other.body_structure(),limits()?)?;
    assert!(matches!(proof.lower_caption_state_structure_candidate(&forms,&foreign,&bytes,&topology,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Source)));assert!(matches!(proof.lower_caption_state_structure_candidate(&other,&state,&bytes,&topology,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Source)));
    let mut drift=bytes.clone();drift[0]^=1;assert!(matches!(state.lower_caption_structure_candidate(&drift,&topology,&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Source)));
    assert!(matches!(state.lower_caption_structure_candidate(&bytes,&topology,&[],&[],&[],limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?),Err(E::Writer)));
    let overflowing=rewrite(&bytes,|name,data|Ok(if name=="Contents/section0.xml"{String::from_utf8(data)?.replacen("<hp:p id='1'>","<hp:p id='4294967295'>",1).into_bytes()}else{data}))?;
    let source=structure(&overflowing,"caption-structure")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let creates=[creation(&state.context().owners()[0],&local)];assert!(matches!(state.lower_caption_structure_candidate(&overflowing,&request(&state,&[],&creates),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Limit)));
    for body in [bare(0).replace("lock='0'","lock='1'"),fixture::table("<hp:t>cell</hp:t>").replace("<hp:p id='1'>","<hp:p id='700'>").replace("lock=\"0\"","lock=\"1\"")] {
        let bytes=package_for(&body)?;let source=structure(&bytes,"caption-structure")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;let creates=[creation(&state.context().owners()[0],&local)];assert!(matches!(state.lower_caption_structure_candidate(&bytes,&request(&state,&[],&creates),&[],&[],&[],limits()?,WriterLimits::default()),Err(E::Protection)));
    }Ok(())
}
#[test]
fn caption_structure64_creations_deletions_share_guard_maps_and_allocate_without_reusing_removed_ids() -> TestResult {
    let body=(0..64).map(bare).chain((0..64).map(|i|object(i,"<hp:t>oldA</hp:t>"))).collect::<String>();let bytes=package_for(&body)?;let source=structure(&bytes,"caption-structure")?;let state=ImportedCaptionSourceState::import(&source,limits()?)?;
    let ids=(0..64).map(|i|LogicalId::parse(format!("new-{i}"))).collect::<Result<Vec<_>,_>>()?;let creates=state.context().owners()[..64].iter().zip(&ids).map(|(owner,id)|creation(owner,id)).collect::<Vec<_>>();let deletions=state.frames().frames().iter().map(deletion).collect::<Vec<_>>();
    let result=state.lower_caption_structure_candidate(&bytes,&request(&state,&deletions,&creates),&[],&[],&[],limits()?,WriterLimits::default())?;let receipt=result.receipt();assert_eq!((receipt.caption_topology.output_captions,receipt.caption_topology.retained_native_controls,receipt.caption_topology.created_native_controls),(64,1,128));
    let n=source.source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").and_then(|p|p.xml()).ok_or("xml")?.elements().len();assert_eq!(receipt.caption_topology.paragraph_id_elements_scanned,n);assert_eq!(receipt.content.output.observed_protection_element_visits,4*n);
    let allocated=receipt.caption_topology.created.iter().flat_map(|c|c.allocated_paragraph_ids.iter().copied()).collect::<Vec<_>>();assert_eq!(allocated,(163..=290).collect::<Vec<_>>());
    let output=result.with_verified_bytes(<[u8]>::to_vec)?;let after=structure(&output,"caption-structure")?;let after=ImportedCaptionSourceState::import(&after,limits()?)?;assert_eq!(after.frames().frames().len(),64);assert_eq!(after.numbering().controls().len(),128);Ok(())
}
