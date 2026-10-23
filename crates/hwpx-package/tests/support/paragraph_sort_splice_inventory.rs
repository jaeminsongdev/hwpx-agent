use super::*;
#[test]
fn inventory_contains_only_moved_destination_slots_with_actual_source_ranges()->TestResult {
    let raw=fixture::package(&(p(1,"Z")+&p(2,"B")+&p(3,"A-LONG")))?;let f=fixture::forms(&raw,"sort-inventory")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;let r=out.receipt();let inv=out.splice_inventory();assert_eq!(r.source_order,vec![2,1,0]);assert_eq!(inv.splices().len(),2);
    for (splice,destination)in inv.splices().iter().zip([0,2]) {
        assert_eq!(splice.source_anchor(),&r.entries[destination].paragraph_anchor);
        let at=f.source().resolve_anchor(splice.source_anchor())?;let span=at.element().ok_or("element")?.outer_span().ok_or("span")?;
        assert_eq!((splice.source_start(),splice.source_end()),(span.start(),span.end()));
        let moved=&r.entries[r.source_order[destination]];assert_eq!(splice.replacement_sha256(),moved.subtree_sha256);assert_eq!(splice.replacement_bytes(),moved.subtree_bytes);
    }Ok(())
}
#[test]
fn inventory_replacement_hash_and_size_match_actual_unequal_output_subtrees()->TestResult {
    let a=p(1,"Z");let b="<hp:p id='2'><hp:run><hp:t>A</hp:t></hp:run><hp:run><hp:t>MORE</hp:t></hp:run></hp:p>";
    let raw=fixture::package(&(a+b))?;let f=fixture::forms(&raw,"sort-inventory-bytes")?;let out=sort(&f,&raw,Scope::Document,spec())?;
    let text=section(&bytes(&out)?)?;let xml=hwpx_package::PreservingXmlDocument::parse(text.as_bytes())?;
    let paragraphs:Vec<_>=xml.elements().iter().filter(|n|n.name().local_name()=="p").collect();
    for (splice,node)in out.splice_inventory().splices().iter().zip(paragraphs){let span=node.outer_span().ok_or("span")?;
        let data=&text.as_bytes()[span.start()..span.end()];assert_eq!(splice.replacement_sha256(),<[u8;32]>::from(Sha256::digest(data)));assert_eq!(splice.replacement_bytes(),data.len());}Ok(())
}
#[test]
fn inventory_is_bound_to_unchanged_legacy_receipt_source_and_output_hashes()->TestResult {
    let raw=fixture::package(&(p(1,"Z")+&p(2,"A")))?;let f=fixture::forms(&raw,"sort-inventory-binding")?;let out=sort(&f,&raw,Scope::Document,spec())?;
    let inv=out.splice_inventory();assert_eq!(inv.source_package_sha256(),out.receipt().source_package_sha256);assert_eq!(inv.output_package_sha256(),out.receipt().output_package_sha256);
    assert_eq!(inv.legacy_receipt_sha256(),<[u8;32]>::from(Sha256::digest(serde_json::to_vec(out.receipt())?)));
    assert_eq!(inv.canonical_sha256(),<[u8;32]>::from(Sha256::digest(serde_json::to_vec(inv)?)));Ok(())
}
#[test]
fn inventory_equal_nfc_keys_preserve_original_stable_source_identity()->TestResult {
    let raw=fixture::package(&(p(1,"가")+&p(2,"Z")+&p(3,"가")))?;let f=fixture::forms(&raw,"sort-inventory-stable")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;assert_eq!(out.receipt().source_order,vec![1,0,2]);assert_eq!(out.splice_inventory().splices().len(),2);
    assert!(out.splice_inventory().splices().iter().all(|s|s.source_anchor()!=&out.receipt().entries[2].paragraph_anchor));Ok(())
}
#[test]
fn inventory_redacts_text_and_is_not_serialized_as_part_of_original_receipt()->TestResult {
    let raw=fixture::package(&(p(1,"Z-PRIVATE-KEY")+&p(2,"A-PRIVATE-KEY")))?;let f=fixture::forms(&raw,"sort-inventory-private")?;let out=sort(&f,&raw,Scope::Document,spec())?;
    let inv=out.splice_inventory();for text in[format!("{inv:?}{:?}",inv.splices()),serde_json::to_string(inv)?]{assert!(!text.contains("PRIVATE-KEY"));}
    let receipt=serde_json::to_value(out.receipt())?;assert!(receipt.get("splices").is_none());assert!(!out.receipt().locale_native_full_protection_or_execution_authority);Ok(())
}
#[test]
fn inventory_128_actual_moves_are_deterministic_without_text_or_fragment_copies()->TestResult {
    let body=(0..128).rev().map(|i|p(i+1,&format!("K-{i:03}"))).collect::<String>();let raw=fixture::package(&body)?;let f=fixture::forms(&raw,"sort-inventory-128")?;
    let a=sort(&f,&raw,Scope::Document,spec())?;let b=sort(&f,&raw,Scope::Document,spec())?;
    assert_eq!(a.splice_inventory(),b.splice_inventory());assert_eq!(a.splice_inventory().splices().len(),128);
    assert_eq!(a.splice_inventory().splices().iter().map(|s|s.replacement_bytes()).sum::<usize>(),body.len());Ok(())
}
