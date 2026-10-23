//! Whole synthetic catalogs plus the exact read-only local installation config, never private-user INI or Native.
use super::*;
use hwpx_package::document_import::search::{SourceSearchError,personal_info::catalog::{SourcePersonalInfoCatalog as Catalog,PersonalInfoCatalogFamily as F,PersonalInfoCatalogError as CE},
    navigation::{SourceSearchNavigationRequest as Next,SourceSearchDirection as Direction}};
const NAMES:[&str;11]=["TELEPHONE","RESIDENT","FOREIGNER","EMAIL","ACCOUNT","LICENSE","PASSPORT","CREDIT","IPADDRESS","BIRTHDAY","USERDEF"];
const FAMILIES:[F;11]=[F::Telephone,F::ResidentRegistration,F::ForeignRegistration,F::Email,F::Account,F::DriverLicense,F::Passport,F::CreditCard,F::IpAddress,F::BirthDate,F::UserDefined];
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
const INSTALLED:&str=r"C:\Program Files (x86)\HNC\Office 2020\HOffice110\Bin\PrivateInfo.ini";
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
const INSTALLED_SHA:&str="fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434";
fn encoded(text:&str)->Vec<u8>{let mut out=vec![0xff,0xfe];for u in text.encode_utf16(){out.extend_from_slice(&u.to_le_bytes());}out}
fn parsed(raw:&[u8])->Result<Catalog,CE>{Catalog::parse_utf16le(raw,Sha256::digest(raw).into())}
fn ini(family:usize,patterns:&[String])->String{NAMES.iter().enumerate().map(|(i,n)|format!("[{n}]\r\n{}",if i==family{patterns.iter().enumerate().map(|(p,q)|format!("pattern{p}={q}\r\n")).collect::<String>()}else if i==10{String::new()}else{format!("pattern0=UNMATCHED{i}\r\n")})).collect()}
fn catalog(pattern:&str)->Result<Catalog,CE>{parsed(&encoded(&ini(0,&[pattern.into()])))}
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
fn installed()->Result<Vec<u8>,Box<dyn Error>>{let p=std::env::var("P09_INSTALLED_FORMAT_CATALOG")?;assert_eq!(p,INSTALLED);assert!(std::fs::metadata(&p)?.len()<=64*1024);let bytes=std::fs::read(p)?;
    assert_eq!(hex_digest(&bytes),INSTALLED_SHA);Ok(bytes)}
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
fn hex_digest(raw:&[u8])->String{Sha256::digest(raw).iter().map(|b|format!("{b:02x}")).collect()}
fn find(raw:&[u8],pattern:&str)->Result<hwpx_package::document_import::search::personal_info::catalog::PersonalInfoCatalogResult,Box<dyn Error>>{
    let f=forms(raw)?;let index=f.source_review_scope_index(raw,Default::default())?;Ok(index.find_personal_info_catalog(&catalog(pattern)?.prepare(&[F::Telephone],Default::default())?,Scope::Document,all())?)}
#[test]
fn complete_ten_family_catalog_keeps_order_counts_and_false_native_authority()->R{
    let raw=encoded(&ini(4,&["ONE".into(),"TWO".into()]));let c=parsed(&raw)?;assert_eq!(c.receipt().total_patterns,11);assert_eq!(c.receipt().source_section_order.len(),11);
    for(i,s)in c.receipt().source_section_order.iter().enumerate(){assert_eq!(s.family,FAMILIES[i]);assert_eq!(s.patterns,if i==4{2}else if i==10{0}else{1});}
    assert!(c.receipt().original_pattern_text_preserved&&!c.receipt().installed_vendor_authenticity_or_native_semantics_qualified);c.verify_source(&raw)?;Ok(())
}
#[test]
fn encoding_bom_even_length_surrogate_and_nul_errors_never_become_partial_catalogs()->R{
    let good=encoded(&ini(0,&["MARK".into()]));for raw in [good[2..].to_vec(),{let mut v=good.clone();v.push(0);v},vec![0xff,0xfe,0,0xd8],{let mut v=good.clone();v.extend_from_slice(&[0,0]);v}]{assert!(matches!(parsed(&raw),Err(CE::Encoding)));}
    assert!(Catalog::parse_utf16le(&good,[0;32]).is_err());Ok(())
}
#[test]
fn missing_duplicate_unknown_sections_and_noncanonical_pattern_indices_fail_closed()->R{
    let good=ini(0,&["MARK".into()]);for text in [good.replace("[TELEPHONE]\r\npattern0=MARK\r\n",""),good.replace("[TELEPHONE]","[ADDRESS]"),format!("{good}[TELEPHONE]\r\npattern0=X\r\n"),
        good.replacen("pattern0=MARK","pattern1=MARK",1),good.replacen("pattern0=MARK","pattern00=MARK",1),good.replacen("pattern0=MARK","pattern0=MARK\r\npattern0=X",1),format!("pattern0=X\r\n{good}")]{assert!(parsed(&encoded(&text)).is_err());}Ok(())
}
#[test]
fn empty_sections_unknown_keys_bare_cr_and_quoted_section_names_are_not_silently_ignored()->R{
    let good=ini(0,&["MARK".into()]);for text in [good.replacen("pattern0=MARK\r\n","",1),good.replacen("pattern0=MARK","other=MARK",1),good.replacen("pattern0=MARK","pattern0=",1),good.replacen("MARK","MA\rRK",1),good.replace("[TELEPHONE]","[\"TELEPHONE\"]")]{assert!(parsed(&encoded(&text)).is_err());}Ok(())
}
#[test]
fn original_pattern_spaces_and_case_are_preserved_not_trimmed_or_normalized()->R{
    let raw=fixture::package(&para(1,"X MARK Y mark Z"))?;let found=find(&raw," MARK ")?;assert_eq!(found.matches().len(),1);let m=&found.search().result().matches()[0];assert_eq!((m.start_normalized_scalar,m.end_normalized_scalar),(1,7));Ok(())
}
#[test]
fn malformed_empty_and_conflicting_capture_patterns_reject_the_entire_selected_policy()->R{
    for pattern in ["(","A*",r"(?P<p09cat0>MARK)"]{assert!(matches!(catalog(pattern)?.prepare(&[F::Telephone],Default::default()),Err(CE::Pattern)));}
    let c=parsed(&encoded(&ini(0,&["MARK".into(),"(".into()])))?;assert!(c.prepare(&[F::Telephone],Default::default()).is_err());Ok(())
}
#[test]
fn family_selection_is_a_unique_set_but_matching_precedence_is_original_file_order()->R{
    let c=parsed(&encoded(&ini(0,&["UNMATCHED1".into()])))?;let a=c.prepare(&[F::Telephone,F::ResidentRegistration],Default::default())?;let b=c.prepare(&[F::ResidentRegistration,F::Telephone],Default::default())?;assert_eq!(a.request_sha256(),b.request_sha256());
    let raw=fixture::package(&para(1,"UNMATCHED1"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=index.find_personal_info_catalog(&b,Scope::Document,all())?;assert_eq!(found.matches()[0].family,F::Telephone);
    assert!(c.prepare(&[],Default::default()).is_err());assert!(c.prepare(&[F::Telephone,F::Telephone],Default::default()).is_err());assert!(serde_json::from_str::<F>("\"address\"").is_err());Ok(())
}
#[test]
fn all_thirty_five_account_patterns_survive_the_legacy_sixteen_rule_and_four_kib_boundary()->R{
    let pad="(?:[A-Z]{0})".repeat(12);let patterns:Vec<_>=(0..35).map(|i|format!("MARK{i:02}{pad}")).collect();let c=parsed(&encoded(&ini(4,&patterns)))?;
    let policy=c.prepare(&[F::Account],Default::default())?;assert_eq!(policy.selected_pattern_count(),35);
    let raw=fixture::package(&para(1,"MARK34"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=index.find_personal_info_catalog(&policy,Scope::Document,all())?;
    assert_eq!(found.matches().len(),1);assert_eq!(found.matches()[0].source_pattern_index,34);let v:serde_json::Value=serde_json::from_slice(&found.canonical_json()?)?;assert!(v["selected_pattern_bytes"].as_u64().ok_or("bytes")?>4096);Ok(())
}
#[test]
fn catalog_size_pattern_count_and_per_pattern_byte_bounds_are_enforced()->R{
    assert!(matches!(parsed(&vec![0;65538]),Err(CE::Limit)));assert!(parsed(&encoded(&ini(0,&["X".repeat(4097)]))).is_err());
    let patterns:Vec<_>=(0..120).map(|i|format!("MARK{i}")).collect();assert!(matches!(parsed(&encoded(&ini(0,&patterns))),Err(CE::Limit)));Ok(())
}
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
#[test]
fn full_installed_catalog_has_exact_ten_families_sixty_four_patterns_and_no_address_assumption()->R{
    let raw=installed()?;let c=parsed(&raw)?;assert_eq!(c.receipt().source_bytes,17020);assert_eq!(c.receipt().total_patterns,64);
    let counts=[8,1,1,6,35,1,2,1,1,8,0];assert_eq!(c.receipt().source_section_order.len(),11);for(i,s)in c.receipt().source_section_order.iter().enumerate(){assert_eq!(s.family,FAMILIES[i]);assert_eq!(s.patterns,counts[i]);}
    assert_eq!(c.prepare(&FAMILIES,Default::default())?.selected_pattern_count(),64);assert_eq!(c.prepare(&[F::Account],Default::default())?.selected_pattern_count(),35);c.verify_source(&raw)?;Ok(())
}
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
#[test]
fn installed_telephone_patterns_find_ascii_fullwidth_and_cross_run_source_without_changing_it()->R{
    let config=installed()?;let c=parsed(&config)?;let policy=c.prepare(&[F::Telephone],Default::default())?;
    let body="<hp:p id='1'><hp:run><hp:t>010-000-</hp:t></hp:run><hp:run><hp:t>0000 ０１０－０００－００００</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=index.find_personal_info_catalog(&policy,Scope::Document,all())?;
    assert_eq!(found.matches().len(),2);assert_eq!(found.search().result().matches()[0].pieces.len(),2);assert!(found.matches().iter().all(|m|m.family==F::Telephone));c.verify_source(&config)?;assert_eq!(section(&raw)?,section(&fixture::package(body)?)?);Ok(())
}
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
#[test]
fn installed_unparenthesized_ip_alternation_is_not_silently_fixed_or_claimed_validated()->R{
    let config=installed()?;let c=parsed(&config)?;let text=String::from_utf16(&config[2..].chunks_exact(2).map(|b|u16::from_le_bytes([b[0],b[1]])).collect::<Vec<_>>())?;
    let block=text.split("[IPADDRESS]\r\n").nth(1).ok_or("section")?;let original=block.lines().find_map(|s|s.strip_prefix("pattern0=")).ok_or("pattern")?;let expression=regex::Regex::new(original)?;
    let content="IP 999.888.777.666";let expected:Vec<_>=expression.find_iter(content).map(|m|(m.start(),m.end())).collect();assert!(expected.len()>1);
    let raw=fixture::package(&para(1,content))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=index.find_personal_info_catalog(&c.prepare(&[F::IpAddress],Default::default())?,Scope::Document,all())?;
    let actual:Vec<_>=found.search().result().matches().iter().map(|m|(m.start_normalized_scalar,m.end_normalized_scalar)).collect();assert_eq!(actual,expected);
    let v:serde_json::Value=serde_json::from_slice(&found.canonical_json()?)?;assert_eq!(v["native_defaults_identity_or_execution_qualified"],false);Ok(())
}
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
#[test]
fn identical_resident_and_foreigner_patterns_keep_distinct_source_families_and_indices()->R{
    let config=installed()?;let c=parsed(&config)?;let raw=fixture::package(&para(1,"000000-0000000"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    for family in [F::ResidentRegistration,F::ForeignRegistration]{let found=index.find_personal_info_catalog(&c.prepare(&[family],Default::default())?,Scope::Document,all())?;
        assert_eq!(found.matches().len(),1);assert_eq!(found.matches()[0].family,family);assert_eq!(found.matches()[0].source_pattern_index,0);}Ok(())
}
#[test]
fn driver_license_and_passport_are_not_relabelled_custom_or_discarded()->R{
    let c=parsed(&encoded(&ini(5,&["LICENSE-MARK".into()])))?;let raw=fixture::package(&para(1,"LICENSE-MARK UNMATCHED6"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let found=index.find_personal_info_catalog(&c.prepare(&[F::DriverLicense,F::Passport],Default::default())?,Scope::Document,all())?;
    assert_eq!(found.matches().len(),2);assert_eq!(found.matches()[0].family,F::DriverLicense);assert_eq!(found.matches()[1].family,F::Passport);Ok(())
}
#[test]
fn exact_catalog_selection_feeds_existing_protected_mask_and_preserves_outside_text()->R{
    let raw=fixture::package(&para(1,"KEEP MARK TAIL"))?;let found=find(&raw,"MARK")?;let selected=found.selection(0)?;let f=forms(&raw)?;
    let c=mask(&f,&raw,selected.scope(),all(),Mask::ThreeAsterisksPerTextGroup)?;exact(&raw,&c,"KEEP MARK TAIL","KEEP *** TAIL")?;Ok(())
}
#[test]
fn partial_nfc_contribution_is_reported_but_never_exported_as_an_exact_selection()->R{
    let raw=fixture::package(&para(1,"\u{344}"))?;let found=find(&raw,"\u{308}")?;assert_eq!(found.matches().len(),1);assert!(!found.search().result().matches()[0].source_scalar_selection_exact);assert!(matches!(found.selection(0),Err(CE::Selection)));Ok(())
}
#[test]
fn tab_linebreak_and_paragraph_boundaries_are_not_joined_for_catalog_matching()->R{
    let text="MA<hp:tab width='1' leader='0' type='0'/>RK MA<hp:lineBreak/>RK";let raw=fixture::package(&(para(1,text)+&para(2,"MA")+&para(3,"RK")))?;
    assert!(find(&raw,"MARK")?.matches().is_empty());Ok(())
}
#[test]
fn document_section_node_and_exact_selection_reuse_original_revision_index_windows()->R{
    let raw=fixture::package(&(para(1,"MARK MARK")+&para(2,"MARK")))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let id=inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone();let nodes=[id];let start=boundary(b,5);let end=boundary(b,9);let p=catalog("MARK")?.prepare(&[F::Telephone],Default::default())?;
    for(scope,n)in [(Scope::Document,3),(Scope::Section(&inv.inventory.section_ids),3),(Scope::NodeSet(&nodes),2),(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{assert_eq!(index.find_personal_info_catalog(&p,scope,all())?.matches().len(),n);}Ok(())
}
#[test]
fn review_regions_are_excluded_before_matching_and_keep_explicit_region_labels()->R{
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let p=catalog("K")?.prepare(&[F::Telephone],Default::default())?;
    for(h,m,n)in [(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{let found=index.find_personal_info_catalog(&p,Scope::Document,Policy{include_hidden_explanations:h,include_memo_bodies:m})?;assert_eq!(found.matches().len(),n);assert_eq!(found.search().match_regions().len(),n);}Ok(())
}
#[test]
fn stale_source_index_and_foreign_nodes_never_widen_scope()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;assert!(f.source_review_scope_index(&fixture::package(&para(1,"CHANGED"))?,Default::default()).is_err());
    let index=f.source_review_scope_index(&raw,Default::default())?;let p=catalog("MARK")?.prepare(&[F::Telephone],Default::default())?;
    assert!(index.find_personal_info_catalog(&p,Scope::NodeSet(&[LogicalId::parse("foreign-node")?]),all()).is_err());let inv=index.scope_inventory()?;let a=boundary(&inv.inventory.blocks[0],0);let b=boundary(&inv.inventory.blocks[0],4);
    assert!(index.find_personal_info_catalog(&p,Scope::Selection{index_sha256:[0;32],start:&a,end:&b},all()).is_err());Ok(())
}
#[test]
fn retained_navigation_binds_configuration_bytes_family_selection_and_context()->R{
    let raw=fixture::package(&para(1,"MARK MARK"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let c=catalog("MARK")?;let p=c.prepare(&[F::Telephone],Default::default())?;let found=index.find_personal_info_catalog(&p,Scope::Document,all())?;
    let first=found.navigate(&Next{direction:Direction::Forward,wrap:false,cursor:None},[1;32])?;let req=Next{direction:Direction::Forward,wrap:false,cursor:first.cursor().cloned()};assert_eq!(found.navigate(&req,[1;32])?.match_index(),Some(1));
    assert!(found.navigate(&req,[2;32]).is_err());let changed=parsed(&encoded(&(ini(0,&["MARK".into()])+";source comment\r\n")))?;
    let other=index.find_personal_info_catalog(&changed.prepare(&[F::Telephone],Default::default())?,Scope::Document,all())?;assert!(other.navigate(&req,[1;32]).is_err());Ok(())
}
#[test]
fn compiler_and_index_budgets_are_not_bypassed_by_prepared_regex_objects()->R{
    let c=catalog("M[AR]+K")?;assert!(c.prepare(&[F::Telephone],SourceSearchLimits::new(Config{pattern_bytes:1,..Default::default()})?).is_err());
    let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;let limits=SourceSearchLimits::new(Config{pattern_bytes:1024,..Default::default()})?;let index=f.source_review_scope_index(&raw,limits)?;
    assert!(matches!(index.find_personal_info_catalog(&c.prepare(&[F::Telephone],Default::default())?,Scope::Document,all()),Err(CE::Limit)));Ok(())
}
#[test]
fn exact_entire_catalog_response_limit_and_one_byte_less_are_distinct()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;let c=catalog("MARK")?;let p=c.prepare(&[F::Telephone],Default::default())?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let expected=index.find_personal_info_catalog(&p,Scope::Document,all())?.canonical_json()?;let n=expected.len();let index=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config{result_bytes:n,..Default::default()})?)?;
    assert_eq!(index.find_personal_info_catalog(&p,Scope::Document,all())?.canonical_json()?,expected);let short=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config{result_bytes:n-1,..Default::default()})?)?;assert!(short.find_personal_info_catalog(&p,Scope::Document,all()).is_err());Ok(())
}
#[test]
fn match_and_reported_original_point_limits_fail_without_partial_catalog_results()->R{
    let raw=fixture::package(&para(1,"MARK MARK"))?;let f=forms(&raw)?;let c=catalog("MARK")?;
    for config in [Config{matches:1,..Default::default()},Config{reported_points:1,..Default::default()}]{let index=f.source_review_scope_index(&raw,SourceSearchLimits::new(config)?)?;assert!(matches!(index.find_personal_info_catalog(&c.prepare(&[F::Telephone],Default::default())?,Scope::Document,all()),Err(CE::Search(SourceSearchError::Limit))));}Ok(())
}
#[test]
fn catalog_result_debug_and_selection_never_return_raw_patterns_or_matched_values()->R{
    let c=catalog("PRIVATE-CATALOG-MARK")?;let p=c.prepare(&[F::Telephone],Default::default())?;let raw=fixture::package(&para(1,"PRIVATE-CATALOG-MARK"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let found=index.find_personal_info_catalog(&p,Scope::Document,all())?;let selected=found.selection(0)?;
    for text in [String::from_utf8(c.canonical_json()?)?,String::from_utf8(found.canonical_json()?)?,format!("{c:?}{p:?}{found:?}{selected:?}"),serde_json::to_string(&selected)?]{assert!(!text.contains("PRIVATE-")&&!text.contains("\"query\":")&&!text.contains("matched_value_sha256"));}Ok(())
}
#[test]
fn empty_catalog_match_set_has_no_selection_and_no_native_or_package_sanitization_claim()->R{
    let raw=fixture::package(&para(1,"OTHER"))?;let found=find(&raw,"MARK")?;assert!(found.matches().is_empty());assert!(found.selection(0).is_err());
    let v:serde_json::Value=serde_json::from_slice(&found.canonical_json()?)?;assert_eq!(v["whole_package_personal_data_removed"],false);assert_eq!(v["native_defaults_identity_or_execution_qualified"],false);Ok(())
}
#[test]
fn empty_user_defined_section_is_retained_and_selected_without_inventing_an_empty_regex()->R{
    let c=catalog("MARK")?;assert_eq!(c.receipt().source_section_order.last().ok_or("section")?.family,F::UserDefined);
    let p=c.prepare(&[F::UserDefined],Default::default())?;assert_eq!(p.selected_pattern_count(),0);let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let found=index.find_personal_info_catalog(&p,Scope::Document,all())?;assert!(found.matches().is_empty());assert!(found.selection(0).is_err());assert!(!found.canonical_json()?.is_empty());
    let mut text=ini(0,&["MARK".into()]);text=text.replace("[USERDEF]\r\n","");assert!(parsed(&encoded(&text))?.prepare(&[F::UserDefined],Default::default()).is_err());Ok(())
}
