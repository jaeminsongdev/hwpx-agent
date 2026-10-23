use super::*;
use domain_ir::caption_sequence_program::{CaptionSequenceMember as Member,resolve_caption_sequence_numbers as resolve};
fn members(d:&ReferenceAuxiliaryDocumentStateDraft)->Vec<Member<'_>> {
    d.captions.iter().map(|c|{let object=d.caption_objects.iter().find(|o|o.logical_object_id==c.logical_object_id).unwrap();Member {
        logical_caption_id:&c.logical_caption_id,logical_object_id:&c.logical_object_id,logical_sequence_id:&c.logical_sequence_id,section_id:&object.section_id,
        object_kind:object.object_kind,document_order:c.document_order}}).collect()
}
#[test]
fn caption_program_original_full_state_numbers_match_without_fabricating_complete_state() {
    let d=draft();let result=resolve(&d.caption_sequences,&members(&d),limits()).unwrap();
    for value in result {let expected=d.captions.iter().find(|c|c.logical_caption_id==value.logical_caption_id).unwrap();assert_eq!(value.resolved_number,expected.cache.resolved_number);}
    ReferenceAuxiliaryDocumentState::from_draft(d,limits()).unwrap();
}
#[test]
fn caption_program_explicit_order_independent_sequences_and_per_section_resets_are_deterministic() {
    let sequences=[sequence("private a",CaptionObjectKind::Picture,CaptionRestartPolicy::Continuous,4),sequence("private b",CaptionObjectKind::Picture,CaptionRestartPolicy::PerSection,8)];
    let captions=[id("c0"),id("c1"),id("c2"),id("c3")];let objects=[id("o0"),id("o1"),id("o2"),id("o3")];let sections=[id("s0"),id("s1")];
    let members=(0..4).map(|i|Member {logical_caption_id:&captions[i],logical_object_id:&objects[i],logical_sequence_id:&sequences[usize::from(i>=2)].logical_sequence_id,
        section_id:&sections[usize::from(i==3)],object_kind:CaptionObjectKind::Picture,document_order:[9,1,2,3][i]}).collect::<Vec<_>>();
    let output=resolve(&sequences,&members,limits()).unwrap();assert_eq!(output.iter().map(|v|v.resolved_number).collect::<Vec<_>>(),[4,8,8,5]);
    assert_eq!(output.iter().map(|v|v.document_order).collect::<Vec<_>>(),[1,2,3,9]);
    assert!(!format!("{:?}{output:?}",members[0]).contains("private"));
}
#[test]
fn caption_program_duplicate_identity_object_order_missing_definition_and_kind_are_rejected() {
    let d=draft();let mut data=members(&d);let missing=id("missing");
    for mode in 0..5 {let mut bad=members(&d);match mode {0=>bad[1].logical_caption_id=bad[0].logical_caption_id,1=>bad[1].logical_object_id=bad[0].logical_object_id,
        2=>bad[1].document_order=bad[0].document_order,3=>bad[0].logical_sequence_id=&missing,_=>bad[0].object_kind=CaptionObjectKind::Table};
        assert!(resolve(&d.caption_sequences,&bad,limits()).is_err());
    }
    let mut duplicate=d.caption_sequences.clone();duplicate.push(duplicate[0].clone());assert!(resolve(&duplicate,&data,limits()).is_err());data.clear();assert!(resolve(&d.caption_sequences,&data,limits()).unwrap().is_empty());
}
#[test]
fn caption_program_invalid_definition_text_digests_opaque_metadata_and_zero_start_are_rejected() {
    let d=draft();let data=members(&d);
    for mode in 0..6 {let mut bad=d.caption_sequences.clone();match mode {0=>bad[0].label.clear(),1=>bad[0].separator="\n".into(),2=>bad[0].number_style_sha256="invalid".into(),
        3=>bad[0].start_at=0,4=>bad[0].label="bad\0".into(),_=>bad[0].opaque_properties.push(domain_ir::OpaqueLinkProperty {namespace:"bad value".into(),name:"flag".into(),value_sha256:D.into()})};
        assert!(resolve(&bad,&data,limits()).is_err());
    }
}
#[test]
fn caption_program_finite_counts_sections_text_and_last_item_overflow_preserve_existing_rules() {
    let d=draft();let data=members(&d);let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()}).unwrap();
    assert_eq!(resolve(&d.caption_sequences,&data,tiny),Err(ReferenceAuxiliaryError::InputLimit));
    let mut definitions=d.caption_sequences.clone();definitions[0].start_at=u32::MAX;assert_eq!(resolve(&definitions,&data[..1],limits()),Err(ReferenceAuxiliaryError::InvalidCaption));
    definitions[0].start_at=u32::MAX-1;assert_eq!(resolve(&definitions,&data[..1],limits()).unwrap()[0].resolved_number,u32::MAX-1);
    assert_eq!(resolve(&definitions,&data,limits()),Err(ReferenceAuxiliaryError::InvalidCaption));
    let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {text_bytes:1,..Default::default()}).unwrap();assert!(resolve(&d.caption_sequences,&data,tiny).is_err());
}
#[test]
fn caption_program512_members_match_independent_counter_oracle_without_per_member_whole_scans() {
    use std::collections::BTreeMap;
    let sequences=[sequence("continuous",CaptionObjectKind::Picture,CaptionRestartPolicy::Continuous,4),sequence("section",CaptionObjectKind::Picture,CaptionRestartPolicy::PerSection,6)];
    let captions=(0..512).map(|i|id(&format!("c{i}"))).collect::<Vec<_>>();let objects=(0..512).map(|i|id(&format!("o{i}"))).collect::<Vec<_>>();let sections=(0..4).map(|i|id(&format!("s{i}"))).collect::<Vec<_>>();
    let members=(0..512).map(|i|Member {logical_caption_id:&captions[i],logical_object_id:&objects[i],logical_sequence_id:&sequences[i%2].logical_sequence_id,
        section_id:&sections[i%4],object_kind:CaptionObjectKind::Picture,document_order:511-i as u64}).collect::<Vec<_>>();
    let result=resolve(&sequences,&members,limits()).unwrap();let mut counters=BTreeMap::<(usize,Option<usize>),u32>::new();
    for (position,item) in result.iter().enumerate(){let i=511-position;let key=(i%2,if i%2==1{Some(i%4)}else{None});let expected=counters.entry(key).or_insert(if i%2==0{4}else{6});
        assert_eq!(item.logical_caption_id,captions[i]);assert_eq!(item.resolved_number,*expected);*expected+=1;
    }
}
