use domain_ir::{NoteKind, NoteLineType as L, NoteLineWidth as W, NoteNumberFormat as N,
    NoteNumberingRestart as R, NotePlacement as P};
use hwpx_package::{BoundedZipReader, NoteHwpxLimitConfig, NoteHwpxLimits, PackageLimits,
    PreservingXmlDocument, WriterLimitConfig, WriterLimits,
    document_import::structure::note_style::{ImportedNoteStyle, NoteStyleError as E, NoteStyleReplacement, NoteStyleValues}};
use std::{collections::BTreeMap, error::Error, io::{Cursor, Write}};
#[allow(dead_code)]
#[path = "support/document_import_field_fixture.rs"] mod fixture;
#[path = "support/document_import_note_fixture.rs"] mod historical;
type TestResult = Result<(), Box<dyn Error>>;
fn limits() -> NoteHwpxLimits { NoteHwpxLimits::new(NoteHwpxLimitConfig::default()).expect("default") }
fn style(kind: &str, placement: &str) -> String {
    format!("<hp:{kind} u:future='KEEP-STYLE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar=')' supscript='false'/><hp:noteLine length='-1' type='SOLID' width='0.12 mm' color='#aBcDeF'/><hp:noteSpacing betweenNotes='283' belowLine='567' aboveLine='850'/><hp:numbering type='CONTINUOUS' newNum='1'/><hp:placement place='{placement}' beneathText='false'/><u:extension secret='KEEP-OPAQUE'/></hp:{kind}>")
}
fn body(styles: &str) -> String {
    format!("<hp:p id='1'><hp:run><hp:secPr>{styles}</hp:secPr><hp:t>KEEP-BODY</hp:t><hp:ctrl><hp:footNote instId='101' number='1'><hp:subList><hp:p id='10'><hp:run><hp:t>KEEP-NOTE</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>")
}
fn source() -> Result<Vec<u8>, Box<dyn Error>> {
    fixture::package(&body(&(style("footNotePr", "EACH_COLUMN") + &style("endNotePr", "END_OF_DOCUMENT"))))
}
fn expanded(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    (0..reader.entries().len()).map(|i| Ok((reader.entries()[i].path.as_str().to_owned(), reader.read_entry(i)?))).collect()
}
fn request<'a>(style: &'a ImportedNoteStyle, values: &'a NoteStyleValues) -> NoteStyleReplacement<'a> {
    NoteStyleReplacement { style_id: style.style_id(), source_style_sha256: style.source_anchor().fingerprint_sha256, values }
}
#[test]
fn source_values_are_observed_without_defaults_protection_grants_or_private_debug() -> TestResult {
    let bytes = source()?; let forms = fixture::forms(&bytes, "styles")?;
    let styles = forms.body_structure().import_note_styles(limits())?;
    assert_eq!(styles.len(), 2);
    assert_eq!((styles[0].kind(), styles[1].kind()), (NoteKind::Footnote, NoteKind::Endnote));
    assert_eq!(styles[0].values().note_line.length_hwp_units, -1);
    assert_eq!(styles[0].values().note_line.color_rgb, 0xabcdef);
    assert_eq!(styles[1].values().placement, P::EndOfDocument);
    assert_eq!(styles[0].values().auto_number_format.suffix_character, ")");
    let value = serde_json::to_value(&styles[0])?;
    assert!(value.get("locked").is_none() && value.get("opaque_style_sha256").is_none());
    for debug in [format!("{:?}", styles[0]), format!("{:?}", styles[0].values())] {
        assert!(!debug.contains("KEEP") && !debug.contains(styles[0].style_id().as_str()));
    }
    let absent = fixture::package("<hp:p id='1'><hp:run><hp:t>NO STYLE</hp:t></hp:run></hp:p>")?;
    assert!(fixture::forms(&absent, "absent")?.body_structure().import_note_styles(limits())?.is_empty());
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}
#[test]
fn batch_changes_all_sixteen_values_with_exact_opaque_body_and_other_part_preservation() -> TestResult {
    let bytes = source()?; let forms = fixture::forms(&bytes, "styles")?;
    let styles = forms.body_structure().import_note_styles(limits())?;
    let mut values = styles[0].values().clone();
    values.auto_number_format.format = N::UserChar;
    values.auto_number_format.user_character = "별&<'\"\t\n\r".into();
    values.auto_number_format.prefix_character = "앞".into(); values.auto_number_format.suffix_character = "뒤".into();
    values.auto_number_format.superscript = true;
    values.note_line.length_hwp_units = i32::MAX; values.note_line.line_type = L::Reverse3d;
    values.note_line.width = W::Mm5_0; values.note_line.color_rgb = 0x123456;
    values.spacing.between_notes_hwp_units = 1; values.spacing.below_line_hwp_units = 2; values.spacing.above_line_hwp_units = 3;
    values.numbering_restart = R::PerPage; values.new_number = 42; values.placement = P::RightMostColumn; values.beneath_text = true;
    let mut end = values.clone(); end.numbering_restart = R::PerSection; end.placement = P::EndOfSection;
    let candidate = forms.body_structure().lower_note_style_batch_candidate(&bytes, &[request(&styles[0], &values), request(&styles[1], &end)], limits(), WriterLimits::default())?;
    let output = candidate.with_verified_bytes(<[u8]>::to_vec)?;
    let next = fixture::forms(&output, "styles")?;
    let actual = next.body_structure().import_note_styles(limits())?;
    assert_eq!(actual[0].values(), &values); assert_eq!(actual[1].values(), &end);
    let mut expected = expanded(&bytes)?;
    let old_section = expected.get_mut("Contents/section0.xml").ok_or("section")?;
    let text = String::from_utf8(old_section.clone())?
        .replace("type='DIGIT'", "type='USER_CHAR'").replace("userChar=''", "userChar='별&amp;&lt;&apos;\"&#9;&#10;&#13;'")
        .replace("prefixChar=''", "prefixChar='앞'").replace("suffixChar=')'", "suffixChar='뒤'")
        .replace("supscript='false'", "supscript='1'").replace("length='-1'", "length='2147483647'")
        .replace("type='SOLID'", "type='REV3D'").replace("width='0.12 mm'", "width='5.0 mm'")
        .replace("color='#aBcDeF'", "color='#123456'").replace("betweenNotes='283'", "betweenNotes='1'")
        .replace("belowLine='567'", "belowLine='2'").replace("aboveLine='850'", "aboveLine='3'")
        .replacen("type='CONTINUOUS'", "type='ON_PAGE'", 1).replace("type='CONTINUOUS'", "type='ON_SECTION'")
        .replace("newNum='1'", "newNum='42'").replace("place='EACH_COLUMN'", "place='RIGHT_MOST_COLUMN'")
        .replace("place='END_OF_DOCUMENT'", "place='END_OF_SECTION'").replace("beneathText='false'", "beneathText='1'");
    *old_section = text.into_bytes(); assert_eq!(expanded(&output)?, expected);
    let receipt = candidate.receipt();
    assert_eq!((receipt.replaced_styles, receipt.total_styles_read_back, receipt.changed_attributes, receipt.changed_parts), (2, 2, 32, 1));
    assert!(receipt.only_selected_attribute_values_changed && receipt.opaque_xml_note_bodies_and_other_parts_preserved);
    assert!(!receipt.complete_protection_qualified && !receipt.native_layout_and_numbering_qualified && !receipt.execution_publication_authority);
    let xml = PreservingXmlDocument::parse(expected.get("Contents/section0.xml").ok_or("section")?)?;
    assert_eq!(receipt.protection_element_visits, xml.elements().len() * 4);
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    assert!(!format!("{candidate:?}").contains("KEEP"));
    Ok(())
}
#[test]
fn independent_closed_catalogs_and_family_placements_roundtrip_without_spelling_guesses() -> TestResult {
    let numbers = [(N::Digit,"DIGIT"),(N::CircledDigit,"CIRCLED_DIGIT"),(N::RomanCapital,"ROMAN_CAPITAL"),(N::RomanSmall,"ROMAN_SMALL"),
        (N::LatinCapital,"LATIN_CAPITAL"),(N::LatinSmall,"LATIN_SMALL"),(N::CircledLatinCapital,"CIRCLED_LATIN_CAPITAL"),(N::CircledLatinSmall,"CIRCLED_LATIN_SMALL"),
        (N::HangulSyllable,"HANGUL_SYLLABLE"),(N::CircledHangulSyllable,"CIRCLED_HANGUL_SYLLABLE"),(N::HangulJamo,"HANGUL_JAMO"),(N::CircledHangulJamo,"CIRCLED_HANGUL_JAMO"),
        (N::HangulPhonetic,"HANGUL_PHONETIC"),(N::Ideograph,"IDEOGRAPH"),(N::CircledIdeograph,"CIRCLED_IDEOGRAPH"),(N::DecagonCircle,"DECAGON_CIRCLE"),
        (N::DecagonCircleHanja,"DECAGON_CIRCLE_HANJA"),(N::Symbol,"SYMBOL"),(N::UserChar,"USER_CHAR"),(N::Symbol2,"SYMBOL2"),(N::Image,"IMAGE"),(N::TwoDigit,"2DIGIT")];
    let lines = [(L::None,"NONE"),(L::Solid,"SOLID"),(L::Dot,"DOT"),(L::Dash,"DASH"),(L::DashDot,"DASH_DOT"),(L::DashDotDot,"DASH_DOT_DOT"),
        (L::LongDash,"LONG_DASH"),(L::Circle,"CIRCLE"),(L::DoubleSlim,"DOUBLE_SLIM"),(L::SlimThick,"SLIM_THICK"),(L::ThickSlim,"THICK_SLIM"),
        (L::SlimThickSlim,"SLIM_THICK_SLIM"),(L::Wave,"WAVE"),(L::DoubleWave,"DOUBLEWAVE"),(L::Thick3d,"THICK3D"),(L::ThickReverse3d,"THICKREV3D"),(L::ThreeDimensional,"3D"),(L::Reverse3d,"REV3D")];
    let widths = [(W::Mm0_1,"0.1 mm"),(W::Mm0_12,"0.12 mm"),(W::Mm0_15,"0.15 mm"),(W::Mm0_2,"0.2 mm"),(W::Mm0_25,"0.25 mm"),
        (W::Mm0_3,"0.3 mm"),(W::Mm0_4,"0.4 mm"),(W::Mm0_5,"0.5 mm"),(W::Mm0_6,"0.6 mm"),(W::Mm0_7,"0.7 mm"),
        (W::Mm1_0,"1.0 mm"),(W::Mm1_5,"1.5 mm"),(W::Mm2_0,"2.0 mm"),(W::Mm3_0,"3.0 mm"),(W::Mm4_0,"4.0 mm"),(W::Mm5_0,"5.0 mm")];
    let bytes = source()?; let forms = fixture::forms(&bytes, "catalog")?; let structure = forms.body_structure();
    let styles = structure.import_note_styles(limits())?;
    for (i, &(number, number_spelling)) in numbers.iter().enumerate() {
        let (line, line_spelling) = lines[i % lines.len()]; let (width, width_spelling) = widths[i % widths.len()];
        let mut v = styles[0].values().clone(); v.auto_number_format.format = number; v.auto_number_format.user_character = "*".into();
        v.note_line.line_type = line; v.note_line.width = width; v.new_number = u32::try_from(i)? + 2;
        let candidate = structure.lower_note_style_batch_candidate(&bytes, &[request(&styles[0], &v)], limits(), WriterLimits::default())?;
        let output = candidate.with_verified_bytes(<[u8]>::to_vec)?;
        let after = fixture::forms(&output, "catalog")?.body_structure().import_note_styles(limits())?;
        assert_eq!(after[0].values(), &v);
        let raw = expanded(&output)?.remove("Contents/section0.xml").ok_or("section")?;
        let text = String::from_utf8(raw)?;
        for expected in [format!("type='{number_spelling}'"), format!("type='{line_spelling}'"), format!("width='{width_spelling}'")] { assert!(text.contains(&expected)); }
        assert!(text.contains("color='#aBcDeF'") && text.contains("supscript='false'"), "unchanged lexical values retained");
    }
    for (slot, placement, restart) in [(0,P::EachColumn,R::Continuous),(0,P::MergedColumn,R::PerSection),(0,P::RightMostColumn,R::PerPage),
        (1,P::EndOfDocument,R::Continuous),(1,P::EndOfSection,R::PerSection)] {
        let mut v = styles[slot].values().clone(); v.placement = placement; v.numbering_restart = restart; v.new_number = 7;
        let output = structure.lower_note_style_batch_candidate(&bytes, &[request(&styles[slot], &v)], limits(), WriterLimits::default())?.with_verified_bytes(<[u8]>::to_vec)?;
        assert_eq!(fixture::forms(&output,"catalog")?.body_structure().import_note_styles(limits())?[slot].values(), &v);
    }
    Ok(())
}
#[test]
fn missing_duplicate_nested_unknown_and_incompatible_source_values_never_get_defaults() -> TestResult {
    let valid = style("footNotePr", "EACH_COLUMN");
    let bad = [valid.replace(" userChar=''", ""), valid.replace(" newNum='1'", ""), valid.replace(" beneathText='false'", ""),
        valid.replace("<hp:noteLine", "<hp:noteSpacing betweenNotes='1' belowLine='2' aboveLine='3'/><hp:noteLine"),
        valid.replace("type='DIGIT'", "type='FUTURE'"), valid.replace("type='SOLID'", "type='DOUBLE_WAVE'"),
        valid.replace("width='0.12 mm'", "width='0.12'"), valid.replace("color='#aBcDeF'", "color='#1234567'"),
        valid.replace("newNum='1'", "newNum='4294967296'"), valid.replace("length='-1'", "length='2147483648'"),
        valid.replace("betweenNotes='283'", "betweenNotes='-1'"), valid.replace("supscript='false'", "supscript='unknown'"),
        valid.replace("type='DIGIT'", "type='USER_CHAR'"), valid.replace("place='EACH_COLUMN'", "place='END_OF_SECTION'"),
        valid.replace("<hp:noteLine", "<u:hidden><hp:noteLine").replace("<hp:noteSpacing", "</u:hidden><hp:noteSpacing"),
        valid.replace("<hp:autoNumFormat", "<hp:autoNumFormat").replace("supscript='false'/>", "supscript='false'><u:child/></hp:autoNumFormat>"),
        style("endNotePr", "END_OF_DOCUMENT").replace("type='CONTINUOUS'", "type='ON_PAGE'")];
    for style in bad { let bytes = fixture::package(&body(&style))?; let f = fixture::forms(&bytes,"invalid")?; assert!(f.body_structure().import_note_styles(limits()).is_err()); }
    for b in [body(&(valid.clone() + &valid)), body(&format!("<u:hidden>{valid}</u:hidden>")),
        body(&valid).replace("</hp:secPr>", "</hp:secPr><hp:secPr/>"),
        format!("<hp:p id='1'><hp:run>{valid}</hp:run></hp:p>")] {
        let bytes = fixture::package(&b)?; assert!(matches!(fixture::forms(&bytes,"invalid")?.body_structure().import_note_styles(limits()), Err(E::Shape)));
    }
    Ok(())
}
#[test]
fn foreign_stale_empty_duplicate_noop_and_fresh_source_drift_reject_whole_batch() -> TestResult {
    let bytes = source()?; let f = fixture::forms(&bytes,"owner")?; let s = f.body_structure(); let styles = s.import_note_styles(limits())?;
    let foreign = fixture::forms(&bytes,"foreign")?.body_structure().import_note_styles(limits())?;
    let mut v = styles[0].values().clone(); v.new_number = 2;
    let lower = |r: &[NoteStyleReplacement<'_>]| s.lower_note_style_batch_candidate(&bytes,r,limits(),WriterLimits::default());
    assert!(matches!(lower(&[]),Err(E::Selection)));
    assert!(matches!(lower(&[request(&styles[0],&v),request(&styles[0],&v)]),Err(E::Selection)));
    assert!(matches!(lower(&[request(&foreign[0],&v)]),Err(E::Selection)));
    assert!(matches!(lower(&[NoteStyleReplacement { source_style_sha256: [0;32], ..request(&styles[0],&v) }]),Err(E::Selection)));
    assert!(matches!(lower(&[request(&styles[0],&v),request(&styles[1],styles[1].values())]),Err(E::NoChange)));
    let changed = fixture::package(&body(&style("footNotePr","MERGED_COLUMN")))?;
    assert!(matches!(s.lower_note_style_batch_candidate(&changed,&[request(&styles[0],&v)],limits(),WriterLimits::default()),Err(E::Source)));
    for (slot, placement, restart) in [(0,P::EndOfDocument,R::Continuous),(1,P::EachColumn,R::Continuous),(1,P::EndOfSection,R::PerPage)] {
        let mut v = styles[slot].values().clone(); v.placement = placement; v.numbering_restart = restart;
        assert!(matches!(lower(&[request(&styles[slot],&v)]),Err(E::Value)));
    }
    Ok(())
}
#[test]
fn observed_locks_in_ancestors_known_children_or_opaque_subtrees_deny_changes() -> TestResult {
    for locked in [body(&style("footNotePr","EACH_COLUMN")).replace("<hp:secPr>","<hp:secPr lock='1'>"),
        body(&style("footNotePr","EACH_COLUMN")).replace("<hp:noteLine ","<hp:noteLine lock='true' "),
        body(&style("footNotePr","EACH_COLUMN")).replace("<u:extension", "<hp:future lock='unknown'/><u:extension")] {
        let bytes = fixture::package(&locked)?; let f = fixture::forms(&bytes,"protected")?;
        let styles = f.body_structure().import_note_styles(limits())?;
        let mut v = styles[0].values().clone(); v.new_number = 2;
        assert!(matches!(f.body_structure().lower_note_style_batch_candidate(&bytes,&[request(&styles[0],&v)],limits(),WriterLimits::default()),Err(E::Protection)));
    }
    Ok(())
}
#[test]
fn source_request_plan_output_and_writer_limits_are_finite_and_not_silently_clamped() -> TestResult {
    let bytes = source()?; let f = fixture::forms(&bytes,"limits")?; let s = f.body_structure(); let styles = s.import_note_styles(limits())?;
    for config in [NoteHwpxLimitConfig { notes:1,..NoteHwpxLimitConfig::default() },NoteHwpxLimitConfig { elements:1,..NoteHwpxLimitConfig::default() },
        NoteHwpxLimitConfig { section_bytes:1,..NoteHwpxLimitConfig::default() },NoteHwpxLimitConfig { text_bytes:1,..NoteHwpxLimitConfig::default() }] {
        assert!(matches!(s.import_note_styles(NoteHwpxLimits::new(config)?),Err(E::Limit)));
    }
    let mut v = styles[0].values().clone(); v.new_number = 2; v.auto_number_format.prefix_character = "&&&&&&".into();
    assert!(matches!(s.lower_note_style_batch_candidate(&bytes,&[request(&styles[0],&v)],NoteHwpxLimits::new(NoteHwpxLimitConfig { plan_bytes:1,..NoteHwpxLimitConfig::default() })?,WriterLimits::default()),Err(E::Limit)));
    assert!(matches!(s.lower_note_style_batch_candidate(&bytes,&[request(&styles[0],&v)],limits(),WriterLimits::new(WriterLimitConfig { max_output_bytes:1 })?),Err(E::Writer)));
    v.auto_number_format.prefix_character = "\0".into();
    assert!(matches!(s.lower_note_style_batch_candidate(&bytes,&[request(&styles[0],&v)],limits(),WriterLimits::default()),Err(E::Value)));
    let requests: Vec<_> = (0..257).map(|_| request(&styles[0], &v)).collect();
    assert!(matches!(s.lower_note_style_batch_candidate(&bytes,&requests,limits(),WriterLimits::default()),Err(E::Limit)));
    Ok(())
}
#[test]
fn original_nine_generated_saved_reopened_styles_are_observed_without_relabelling_native_failure() -> TestResult {
    let mut lanes = BTreeMap::new();
    for input in historical::actual_inputs()? {
        let forms = fixture::forms(&input.bytes,"historical-styles")?;
        let styles = forms.body_structure().import_note_styles(limits())?;
        assert_eq!(styles.len(),2); assert_eq!(forms.notes().len(),input.expected_notes);
        assert_eq!((styles[0].kind(),styles[1].kind()),(NoteKind::Footnote,NoteKind::Endnote));
        *lanes.entry(input.lane).or_insert(0usize) += 1;
        assert_eq!(forms.verify_source(&input.bytes)?,*forms.receipt());
    }
    assert_eq!(lanes,BTreeMap::from([("generated",3),("reopened",3),("saved",3)]));
    Ok(())
}
#[test]
fn same_local_styles_in_two_sections_are_distinct_and_one_transaction_preserves_both_parts() -> TestResult {
    let bytes = source()?; let mut entries = expanded(&bytes)?;
    let section = entries.get("Contents/section0.xml").ok_or("section")?.clone();
    entries.insert("Contents/section1.xml".into(),section);
    let opf = entries.get_mut("Contents/content.hpf").ok_or("opf")?;
    *opf = String::from_utf8(opf.clone())?.replace("</o:manifest>","<o:item id='s1' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>")
        .replace("</o:spine>","<o:itemref idref='s1'/></o:spine>").into_bytes();
    let mut zip = zip::ZipWriter::new(Cursor::new(Vec::new()));
    zip.start_file("mimetype",zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;
    zip.write_all(entries.get("mimetype").ok_or("mimetype")?)?;
    for (name,data) in entries.iter().filter(|(name,_)| name.as_str() != "mimetype") { zip.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;zip.write_all(data)?; }
    let bytes = zip.finish()?.into_inner(); let f = fixture::forms(&bytes,"two-sections")?;
    let s = f.body_structure(); let styles = s.import_note_styles(limits())?;
    assert_eq!(styles.len(),4); assert_ne!(styles[0].style_id(),styles[2].style_id());
    let mut a = styles[0].values().clone(); a.new_number = 20;
    let mut b = styles[3].values().clone(); b.new_number = 30;
    let output = s.lower_note_style_batch_candidate(&bytes,&[request(&styles[3],&b),request(&styles[0],&a)],limits(),WriterLimits::default())?;
    assert_eq!((output.receipt().changed_parts,output.receipt().total_styles_read_back),(2,4));
    let actual = output.with_verified_bytes(|bytes| fixture::forms(bytes,"two-sections"))??.body_structure().import_note_styles(limits())?;
    assert_eq!(actual[0].values(),&a); assert_eq!(actual[3].values(),&b);
    assert_eq!(actual[1].values(),styles[1].values()); assert_eq!(actual[2].values(),styles[2].values());
    Ok(())
}

#[test]
fn operation_local_whole_form_proof_matches_direct_output_and_rejects_foreign_original_or_bytes() -> TestResult {
    let bytes = source()?; let original = fixture::forms(&bytes,"proof-owner")?;
    let foreign = fixture::forms(&bytes,"proof-owner")?;
    let styles = original.body_structure().import_note_styles(limits())?;
    let mut v = styles[0].values().clone(); v.new_number = 20;
    let requests = [request(&styles[0],&v)];
    let proof = original.reconstruct_source_for_verification(&bytes)?;
    let direct = original.body_structure().lower_note_style_batch_candidate(&bytes,&requests,limits(),WriterLimits::default())?;
    let joined = proof.lower_note_style_batch_candidate(&original,&bytes,&requests,limits(),WriterLimits::default())?;
    assert_eq!(joined.receipt(),direct.receipt());
    assert_eq!(joined.with_verified_bytes(<[u8]>::to_vec)?,direct.with_verified_bytes(<[u8]>::to_vec)?);
    assert!(matches!(proof.lower_note_style_batch_candidate(&foreign,&bytes,&requests,limits(),WriterLimits::default()),Err(E::Source)));
    let drift = fixture::package(&body(&style("footNotePr","MERGED_COLUMN")))?;
    assert!(matches!(proof.lower_note_style_batch_candidate(&original,&drift,&requests,limits(),WriterLimits::default()),Err(E::Source)));
    Ok(())
}

#[test]
fn shared_request_digest_keeps_original_v1_order_and_binds_every_sixteen_values() -> TestResult {
    use hwpx_package::document_import::structure::note_style::note_style_request_sha256 as hash;
    use sha2::{Digest as _,Sha256};
    let bytes = source()?; let original = fixture::forms(&bytes,"digest-owner")?;
    let styles = original.body_structure().import_note_styles(limits())?;
    let values = styles[0].values().clone(); let selected = [request(&styles[0],&values)];
    let source_sha: [u8;32] = Sha256::digest(&bytes).into();
    let mut old = Sha256::new(); old.update(b"hwpx-agent.source-note-style-replacement/v1\0"); old.update(source_sha);old.update(1u64.to_le_bytes());
    old.update(Sha256::digest(styles[0].style_id().as_str().as_bytes()));old.update(styles[0].source_anchor().fingerprint_sha256);
    for value in ["DIGIT","","",")","0","-1","SOLID","0.12 mm","#ABCDEF","283","567","850","CONTINUOUS","1","EACH_COLUMN","0"] {
        old.update((value.len() as u64).to_le_bytes());old.update(value.as_bytes());
    }
    let expected: [u8;32] = old.finalize().into(); assert_eq!(hash(source_sha,&selected,limits())?,expected);
    for i in 0..16 {
        let mut v = values.clone();
        match i {
            0 => v.auto_number_format.format=N::RomanSmall, 1 => v.auto_number_format.user_character="*".into(),
            2 => v.auto_number_format.prefix_character="prefix".into(), 3 => v.auto_number_format.suffix_character="suffix".into(),
            4 => v.auto_number_format.superscript=true, 5 => v.note_line.length_hwp_units=100,
            6 => v.note_line.line_type=L::Dot, 7 => v.note_line.width=W::Mm1_0, 8 => v.note_line.color_rgb=0,
            9 => v.spacing.between_notes_hwp_units=1,10 => v.spacing.below_line_hwp_units=1,11 => v.spacing.above_line_hwp_units=1,
            12 => v.numbering_restart=R::PerSection,13 => v.new_number=2,14 => v.placement=P::MergedColumn,15 => v.beneath_text=true,
            _ => unreachable!(),
        }
        assert_ne!(hash(source_sha,&[request(&styles[0],&v)],limits())?,expected);
    }
    assert_ne!(hash([0;32],&selected,limits())?,expected);
    let foreign = domain_ir::LogicalId::parse("foreign-style")?;
    assert_ne!(hash(source_sha,&[NoteStyleReplacement { style_id:&foreign,..request(&styles[0],&values) }],limits())?,expected);
    assert_ne!(hash(source_sha,&[NoteStyleReplacement { source_style_sha256:[0;32],..request(&styles[0],&values) }],limits())?,expected);
    assert_ne!(hash(source_sha,&[request(&styles[0],&values),request(&styles[1],styles[1].values())],limits())?,
        hash(source_sha,&[request(&styles[1],styles[1].values()),request(&styles[0],&values)],limits())?);
    assert!(matches!(hash(source_sha,&[],limits()),Err(E::Selection)));
    assert_eq!(hash(source_sha,&selected,NoteHwpxLimits::new(NoteHwpxLimitConfig { text_bytes:1,..NoteHwpxLimitConfig::default() })?)?,expected);
    let mut oversized=values.clone();oversized.auto_number_format.prefix_character="xx".into();
    assert!(matches!(hash(source_sha,&[request(&styles[0],&oversized)],NoteHwpxLimits::new(NoteHwpxLimitConfig { text_bytes:1,..NoteHwpxLimitConfig::default() })?),Err(E::Limit)));
    Ok(())
}

#[test]
fn native_uint_zero_is_exact_readback_and_preservation_not_a_new_or_reinterpreted_start_number() -> TestResult {
    let raw=style("footNotePr","EACH_COLUMN").replace("newNum='1'","newNum='0'");
    let bytes=fixture::package(&body(&raw))?;let forms=fixture::forms(&bytes,"zero-source")?;
    let structure=forms.body_structure();let styles=structure.import_note_styles(limits())?;
    assert_eq!(styles[0].values().new_number,0);
    let mut v=styles[0].values().clone();v.note_line.color_rgb=0x123456;
    let request=[request(&styles[0],&v)];
    let direct=structure.lower_note_style_batch_candidate(&bytes,&request,limits(),WriterLimits::default())?;
    let proof=forms.reconstruct_source_for_verification(&bytes)?;
    let joined=proof.lower_note_style_batch_candidate(&forms,&bytes,&request,limits(),WriterLimits::default())?;
    assert_eq!(direct.receipt(),joined.receipt());
    let output=direct.with_verified_bytes(<[u8]>::to_vec)?;
    let mut expected=expanded(&bytes)?;let section=expected.get_mut("Contents/section0.xml").ok_or("section")?;
    *section=String::from_utf8(section.clone())?.replace("color='#aBcDeF'","color='#123456'").into_bytes();
    assert_eq!(expanded(&output)?,expected);
    assert_eq!(fixture::forms(&output,"zero-source")?.body_structure().import_note_styles(limits())?[0].values().new_number,0);
    let mut reinterpreted=v.clone();reinterpreted.numbering_restart=R::PerSection;
    assert!(matches!(structure.lower_note_style_batch_candidate(&bytes,&[NoteStyleReplacement {values:&reinterpreted,..request[0]}],limits(),WriterLimits::default()),Err(E::Value)));
    let positive=source()?;let f=fixture::forms(&positive,"positive-source")?;let observed=f.body_structure().import_note_styles(limits())?;
    assert!(matches!(f.body_structure().lower_note_style_batch_candidate(&positive,&[NoteStyleReplacement {style_id:observed[0].style_id(),source_style_sha256:observed[0].source_anchor().fingerprint_sha256,values:&v}],limits(),WriterLimits::default()),Err(E::Value)));
    let captured=fixture::captured()?;let captured_forms=fixture::forms(&captured,"captured-zero")?;
    let real=captured_forms.body_structure().import_note_styles(limits())?;
    assert_eq!(real.len(),2);assert!(real.iter().all(|s|s.values().new_number==0));
    assert!(!direct.receipt().native_layout_and_numbering_qualified && !direct.receipt().complete_protection_qualified);
    Ok(())
}
