use super::*;
#[test]
fn group_splices_only_moved_destinations_keep_per_part_ranges_and_identity_slots()->TestResult{
    let raw=two_parts(&(p(1,"Z")+&p(2,"B")+&p(3,"A")),&(p(1,"Y")+&p(2,"C")+&p(3,"B")))?;
    let f=fixture::forms(&raw,"group-splices")?;let out=sort(&f,&raw,Scope::Document,spec())?;let r=out.receipt();let inv=out.splice_inventory();
    assert_eq!(inv.profile(),"hwpx-agent.source-paragraph-sort-group-splices/v1");assert_eq!(inv.splices().len(),4);
    for(group,pair)in r.groups.iter().zip(inv.splices().chunks_exact(2)){
        for(destination,splice)in[0,2].into_iter().zip(pair){let at=f.source().resolve_anchor(splice.source_anchor())?;
            let span=at.element().ok_or("element")?.outer_span().ok_or("span")?;assert_eq!(at.part().path(),&group.part);
            assert_eq!((splice.source_start(),splice.source_end()),(span.start(),span.end()));assert_eq!(splice.source_anchor(),&group.entries[destination].paragraph_anchor);
            assert_ne!(splice.source_anchor(),&group.entries[1].paragraph_anchor);let moved=&group.entries[group.source_order[destination]];
            assert_eq!(splice.replacement_sha256(),moved.subtree_sha256);assert_eq!(splice.replacement_bytes(),moved.subtree_bytes);
        }}Ok(())
}
#[test]
fn group_splices_hashes_and_sizes_match_actual_unequal_subtrees_in_each_output_part()->TestResult{
    let raw=two_parts(&(p(1,"Z-LONG")+&p(2,"A")),&(p(1,"Y")+&p(2,"B-LONGER")))?;let f=fixture::forms(&raw,"group-splices-output")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;let next=bytes(&out)?;
    for(group,pair)in out.receipt().groups.iter().zip(out.splice_inventory().splices().chunks_exact(2)){
        let data=part(&next,group.part.as_str())?;let xml=hwpx_package::PreservingXmlDocument::parse(&data)?;
        let paragraphs:Vec<_>=xml.elements().iter().filter(|n|n.name().local_name()=="p").collect();
        for(splice,node)in pair.iter().zip(paragraphs){let span=node.outer_span().ok_or("span")?;let moved=&data[span.start()..span.end()];
            assert_eq!(splice.replacement_sha256(),<[u8;32]>::from(Sha256::digest(moved)));assert_eq!(splice.replacement_bytes(),moved.len());}
    }Ok(())
}
#[test]
fn group_splices_exclude_singleton_and_unchanged_groups_without_dropping_receipt_rows()->TestResult{
    for second in[p(1,"SINGLE"),p(1,"A")+&p(2,"B")]{let raw=two_parts(&(p(1,"Z")+&p(2,"A")),&second)?;let f=fixture::forms(&raw,"group-splices-noop")?;
        let out=sort(&f,&raw,Scope::Document,spec())?;assert_eq!(out.receipt().groups.len(),2);assert_eq!(out.splice_inventory().splices().len(),2);
        for splice in out.splice_inventory().splices(){assert_eq!(f.source().resolve_anchor(splice.source_anchor())?.part().path().as_str(),"Contents/section0.xml");}}
    Ok(())
}
#[test]
fn group_splices_discontinuous_cell_groups_have_original_xml_order_not_parent_iteration_order()->TestResult{
    let raw=cell_package(&["Z","KEEP-L","A"],&["Y","KEEP-R","B"])?;let f=fixture::forms(&raw,"group-splices-cells")?;let ids=cells(&f)?;
    let selected=[ids[1][2].clone(),ids[0][0].clone(),ids[1][0].clone(),ids[0][2].clone()];let out=sort(&f,&raw,Scope::NodeSet(&selected),spec())?;
    let inv=out.splice_inventory();assert_eq!(inv.splices().len(),4);assert!(inv.splices().windows(2).all(|p|p[0].source_end()<=p[1].source_start()));
    let next=String::from_utf8(part(&bytes(&out)?,"Contents/section0.xml")?)?;
    assert!(next.contains(&(table::paragraph(903,"A")+&table::paragraph(902,"KEEP-L")+&table::paragraph(901,"Z"))));Ok(())
}
#[test]
fn group_splices_bind_unchanged_receipt_source_output_and_redacted_metadata()->TestResult{
    let raw=two_parts(&(p(1,"Z-PRIVATE")+&p(2,"A")),&(p(1,"Y")+&p(2,"B")))?;let f=fixture::forms(&raw,"group-splices-hash")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;let inv=out.splice_inventory();assert_eq!(inv.source_package_sha256(),out.receipt().source_package_sha256);
    assert_eq!(inv.output_package_sha256(),out.receipt().output_package_sha256);assert_eq!(inv.legacy_receipt_sha256(),<[u8;32]>::from(Sha256::digest(serde_json::to_vec(out.receipt())?)));
    assert_eq!(inv.canonical_sha256(),<[u8;32]>::from(Sha256::digest(serde_json::to_vec(inv)?)));
    assert!(serde_json::to_value(out.receipt())?.get("splices").is_none());assert!(!out.receipt().locale_native_full_protection_or_execution_authority);
    assert!(!format!("{inv:?}{:?}{}",inv.splices(),serde_json::to_string(inv)?).contains("PRIVATE"));Ok(())
}
#[test]
fn group_splices_128_moves_are_deterministic_and_copy_budget_is_aggregate()->TestResult{
    let first=(0..64).rev().map(|i|p(i+1,&format!("L-{i:03}"))).collect::<String>();let second=(0..64).rev().map(|i|p(i+1,&format!("R-{i:03}"))).collect::<String>();
    let raw=two_parts(&first,&second)?;let f=fixture::forms(&raw,"group-splices-128")?;let a=sort(&f,&raw,Scope::Document,spec())?;let b=sort(&f,&raw,Scope::Document,spec())?;
    assert_eq!(a.splice_inventory(),b.splice_inventory());assert_eq!(a.splice_inventory().splices().len(),128);
    assert_eq!(a.splice_inventory().splices().iter().map(|s|s.replacement_bytes()).sum::<usize>(),first.len()+second.len());Ok(())
}
