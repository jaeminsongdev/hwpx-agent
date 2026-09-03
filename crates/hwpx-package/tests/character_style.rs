use std::error::Error;
use std::io::{Cursor, Read};

use hwpx_package::{
    BinaryProperty, CHARACTER_STYLE_PROFILE_ID, CharacterStyleCatalog, CharacterStyleCatalogReader,
    CharacterStyleCatalogWriter, CharacterStyleError, CharacterStyleLimitConfig,
    CharacterStyleLimits, Color, EmphasisMark, FontType, Hancom2020Vs0Builder, LanguageSlot,
    LineType1, LineType2, ParagraphChild, ShadowType, SubstituteFont, TextFlowLimits,
    TextFlowReader, TextRunItem, UnderlinePosition,
};
use sha2::{Digest as _, Sha256};
use zip::ZipArchive;

type TestResult = Result<(), Box<dyn Error>>;

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");

#[test]
fn exact_current_2020_header_lifts_all_language_slots_and_styles() -> TestResult {
    let catalog = CharacterStyleCatalogReader::read(HEADER, CharacterStyleLimits::default())?;
    assert_eq!(catalog.font_faces.len(), 7);
    assert_eq!(
        catalog
            .font_faces
            .iter()
            .map(|group| group.fonts.len())
            .sum::<usize>(),
        14
    );
    assert_eq!(catalog.styles.len(), 7);
    assert_eq!(
        catalog
            .font_faces
            .iter()
            .map(|group| group.language)
            .collect::<Vec<_>>(),
        [
            LanguageSlot::Hangul,
            LanguageSlot::Latin,
            LanguageSlot::Hanja,
            LanguageSlot::Japanese,
            LanguageSlot::Other,
            LanguageSlot::Symbol,
            LanguageSlot::User,
        ]
    );
    assert_eq!(catalog.styles[4].spacing.hangul, -5);
    assert_eq!(catalog.styles[5].text_color, Color::Rgb(0x2E, 0x74, 0xB5));
    Ok(())
}

#[test]
fn lower_is_deterministic_and_exactly_readable() -> TestResult {
    let catalog = CharacterStyleCatalogReader::read(HEADER, CharacterStyleLimits::default())?;
    let (first, first_receipt) =
        CharacterStyleCatalogWriter::lower_with_receipt(&catalog, CharacterStyleLimits::default())?;
    let (second, second_receipt) =
        CharacterStyleCatalogWriter::lower_with_receipt(&catalog, CharacterStyleLimits::default())?;
    assert_eq!(first, second);
    assert_eq!(first_receipt, second_receipt);
    assert_eq!(first_receipt.profile_id, CHARACTER_STYLE_PROFILE_ID);
    assert_eq!(first_receipt.output_bytes, first.len());
    assert_eq!(first_receipt.font_count, 14);
    assert_eq!(first_receipt.style_count, 7);
    assert_eq!(
        CharacterStyleCatalogReader::read(&first, CharacterStyleLimits::default())?,
        catalog
    );
    let xml = std::str::from_utf8(&first)?;
    assert!(xml.starts_with("<?xml version=\"1.0\" encoding=\"UTF-8\"?><hh:refList"));
    assert!(xml.contains("<hh:fontfaces itemCnt=\"7\">"));
    assert!(xml.contains("<hh:charProperties itemCnt=\"7\">"));
    Ok(())
}

#[test]
fn typed_variations_effects_and_attribute_escaping_round_trip() -> TestResult {
    let mut catalog = CharacterStyleCatalogReader::read(HEADER, CharacterStyleLimits::default())?;
    let font = &mut catalog.font_faces[0].fonts[0];
    font.face = "A&B\"C".to_owned();
    font.is_embedded = true;
    font.binary_item_id_ref = Some("BIN&1".to_owned());
    font.substitute = Some(SubstituteFont {
        face: "대체<글꼴".to_owned(),
        font_type: FontType::Representative,
        binary_item_id_ref: Some("SUB\"1".to_owned()),
    });
    if let Some(type_info) = &mut font.type_info {
        type_info.serif_style = Some("SERIF_STYLE".to_owned());
    }
    let style = &mut catalog.styles[0];
    style.ratios.latin = 150;
    style.spacing.hanja = -25;
    style.relative_sizes.japanese = 80;
    style.offsets.hangul = 75;
    style.offsets.user = 50;
    style.use_font_space = true;
    style.use_kerning = true;
    style.emphasis_mark = EmphasisMark::DotAbove;
    style.shade_color = Color::Rgb(0x10, 0x20, 0x30);
    style.effects.italic = BinaryProperty::On;
    style.effects.bold = BinaryProperty::On;
    style.effects.underline.position = UnderlinePosition::Bottom;
    style.effects.underline.shape = LineType2::DashDot;
    style.effects.underline.color = Color::Rgb(1, 2, 3);
    style.effects.strikeout.shape = LineType2::LongDash;
    style.effects.outline = LineType1::Thick;
    style.effects.shadow.shadow_type = ShadowType::Drop;
    style.effects.shadow.offset_x = -100;
    style.effects.shadow.offset_y = 100;
    style.effects.emboss = BinaryProperty::On;
    style.effects.engrave = BinaryProperty::On;
    style.effects.superscript = BinaryProperty::On;

    let bytes = CharacterStyleCatalogWriter::lower(&catalog, CharacterStyleLimits::default())?;
    assert!(std::str::from_utf8(&bytes)?.contains("face=\"A&amp;B&quot;C\""));
    assert!(std::str::from_utf8(&bytes)?.contains("binaryItemIDRef=\"BIN&amp;1\""));
    assert!(std::str::from_utf8(&bytes)?.contains("face=\"대체&lt;글꼴\""));
    assert_eq!(
        CharacterStyleCatalogReader::read(&bytes, CharacterStyleLimits::default())?,
        catalog
    );
    Ok(())
}

#[test]
fn semantic_dedup_uses_first_occurrence_and_dense_ids() -> TestResult {
    let mut catalog = CharacterStyleCatalogReader::read(HEADER, CharacterStyleLimits::default())?;
    let mut duplicate = catalog.styles[0].clone();
    duplicate.id = u32::try_from(catalog.styles.len())?;
    catalog.styles.push(duplicate);

    let result = catalog.deduplicate(CharacterStyleLimits::default())?;
    assert_eq!(result.old_to_new.len(), 8);
    assert_eq!(result.old_to_new[7], result.old_to_new[0]);
    assert!(result.styles.len() < catalog.styles.len());
    for (position, style) in result.styles.iter().enumerate() {
        assert_eq!(style.id, u32::try_from(position)?);
    }
    let paragraph = br#"<hp:p xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" id="0"><hp:run charPrIDRef="7"><hp:t charStyleIDRef="7">x</hp:t></hp:run></hp:p>"#;
    let mut flow = TextFlowReader::read(paragraph, TextFlowLimits::default())?;
    result.rewrite_text_flow(&mut flow)?;
    let ParagraphChild::Run(run) = &flow.children[0] else {
        return Err("typed run missing".into());
    };
    assert_eq!(run.character_property_id_ref, Some(0));
    let TextRunItem::Text(span) = &run.items[0] else {
        return Err("typed text missing".into());
    };
    assert_eq!(span.character_style_id_ref, Some(0));

    let mut invalid_flow = flow.clone();
    let ParagraphChild::Run(run) = &mut invalid_flow.children[0] else {
        return Err("typed run missing".into());
    };
    run.character_property_id_ref = Some(99);
    let unchanged = invalid_flow.clone();
    assert_eq!(
        result.rewrite_text_flow(&mut invalid_flow),
        Err(CharacterStyleError::DanglingReference)
    );
    assert_eq!(invalid_flow, unchanged);

    let deduplicated = CharacterStyleCatalog {
        font_faces: catalog.font_faces,
        styles: result.styles,
    };
    let first = CharacterStyleCatalogWriter::lower(&deduplicated, CharacterStyleLimits::default())?;
    let second =
        CharacterStyleCatalogWriter::lower(&deduplicated, CharacterStyleLimits::default())?;
    assert_eq!(first, second);
    Ok(())
}

#[test]
fn diagnostics_redact_font_names_and_binary_references() -> TestResult {
    let mut catalog = CharacterStyleCatalogReader::read(HEADER, CharacterStyleLimits::default())?;
    catalog.font_faces[0].fonts[0].binary_item_id_ref = Some("SECRET_BINARY_ID".to_owned());
    let diagnostic = format!("{catalog:?}");
    assert!(!diagnostic.contains("함초롬"));
    assert!(!diagnostic.contains("SECRET_BINARY_ID"));
    assert!(diagnostic.contains("face_bytes"));
    assert!(diagnostic.contains("binary_item_id_ref_present"));
    Ok(())
}

#[test]
fn malformed_counts_ids_references_ranges_and_effects_fail_closed() -> TestResult {
    let source = std::str::from_utf8(HEADER)?;
    let cases = [
        (
            source.replacen(
                "<hh:fontfaces itemCnt=\"7\"",
                "<hh:fontfaces itemCnt=\"6\"",
                1,
            ),
            CharacterStyleError::CountMismatch,
        ),
        (
            source.replacen("<hh:font id=\"0\"", "<hh:font id=\"9\"", 1),
            CharacterStyleError::InvalidId,
        ),
        (
            source.replacen("<hh:fontRef hangul=\"1\"", "<hh:fontRef hangul=\"99\"", 1),
            CharacterStyleError::DanglingReference,
        ),
        (
            source.replacen("<hh:ratio hangul=\"100\"", "<hh:ratio hangul=\"201\"", 1),
            CharacterStyleError::OutOfRange,
        ),
        (
            source.replacen("<hh:underline", "<hh:bold/><hh:bold/><hh:underline", 1),
            CharacterStyleError::UnsupportedShape,
        ),
    ];
    for (bytes, expected) in cases {
        let Err(error) =
            CharacterStyleCatalogReader::read(bytes.as_bytes(), CharacterStyleLimits::default())
        else {
            return Err("invalid catalog was admitted".into());
        };
        assert_eq!(error, expected);
    }
    Ok(())
}

#[test]
fn wrong_namespace_and_malformed_xml_are_not_admitted() -> TestResult {
    let source = std::str::from_utf8(HEADER)?;
    let wrong_namespace = source.replacen(
        "http://www.hancom.co.kr/hwpml/2011/head",
        "urn:not-hancom-head",
        1,
    );
    assert_eq!(
        CharacterStyleCatalogReader::read(
            wrong_namespace.as_bytes(),
            CharacterStyleLimits::default()
        ),
        Err(CharacterStyleError::WrongRoot)
    );
    assert!(matches!(
        CharacterStyleCatalogReader::read(b"<hh:head", CharacterStyleLimits::default()),
        Err(CharacterStyleError::Preserving(_))
    ));
    Ok(())
}

#[test]
fn finite_input_output_and_model_limits_are_enforced() -> TestResult {
    let tiny = CharacterStyleLimits::new(CharacterStyleLimitConfig {
        input_bytes: 1,
        ..CharacterStyleLimitConfig::default()
    })?;
    assert_eq!(
        CharacterStyleCatalogReader::read(HEADER, tiny),
        Err(CharacterStyleError::InputLimit)
    );

    let catalog = CharacterStyleCatalogReader::read(HEADER, CharacterStyleLimits::default())?;
    let output_limited = CharacterStyleLimits::new(CharacterStyleLimitConfig {
        input_bytes: 4_096,
        ..CharacterStyleLimitConfig::default()
    })?;
    assert_eq!(
        CharacterStyleCatalogWriter::lower(&catalog, output_limited),
        Err(CharacterStyleError::OutputLimit)
    );

    let mut invalid = catalog;
    invalid.styles[0].spacing.user = 51;
    assert_eq!(
        CharacterStyleCatalogWriter::lower(&invalid, CharacterStyleLimits::default()),
        Err(CharacterStyleError::OutOfRange)
    );
    Ok(())
}

#[test]
fn current_2020_vs0_text_references_resolve_to_lifted_styles() -> TestResult {
    let artifact = Hancom2020Vs0Builder::build("문자 모양 참조 검증")?;
    let bytes = artifact.with_verified_bytes(ToOwned::to_owned)?;
    let mut archive = ZipArchive::new(Cursor::new(bytes))?;
    let mut header = Vec::new();
    archive
        .by_name("Contents/header.xml")?
        .read_to_end(&mut header)?;
    let catalog = CharacterStyleCatalogReader::read(&header, CharacterStyleLimits::default())?;

    let mut section = String::new();
    archive
        .by_name("Contents/section0.xml")?
        .read_to_string(&mut section)?;
    let start = section.find("<hp:p ").ok_or("paragraph start missing")?;
    let end = section.find("</hp:p>").ok_or("paragraph end missing")? + "</hp:p>".len();
    let fragment = section[start..end].replacen(
        "<hp:p ",
        "<hp:p xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" ",
        1,
    );
    let flow = TextFlowReader::read(fragment.as_bytes(), TextFlowLimits::default())?;
    for child in &flow.children {
        let ParagraphChild::Run(run) = child else {
            continue;
        };
        if let Some(reference) = run.character_property_id_ref {
            assert!(usize::try_from(reference)? < catalog.styles.len());
        }
        for item in &run.items {
            if let TextRunItem::Text(span) = item
                && let Some(reference) = span.character_style_id_ref
            {
                assert!(usize::try_from(reference)? < catalog.styles.len());
            }
        }
    }
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    assert_eq!(
        CharacterStyleError::DanglingReference.code(),
        "character_style_dangling_reference"
    );
    assert_eq!(
        CharacterStyleError::ReadbackMismatch.code(),
        "character_style_readback_mismatch"
    );
    assert_eq!(
        CharacterStyleLimits::new(CharacterStyleLimitConfig {
            input_bytes: 0,
            ..CharacterStyleLimitConfig::default()
        }),
        Err(CharacterStyleError::InvalidLimit)
    );
}

#[test]
fn fixed_128_style_variation_corpus_is_deterministic() -> TestResult {
    let base = CharacterStyleCatalogReader::read(HEADER, CharacterStyleLimits::default())?;
    let mut aggregate = Sha256::new();
    for index in 0..128_u16 {
        let mut catalog = base.clone();
        let style_index = usize::from(index % 7);
        let style = &mut catalog.styles[style_index];
        style.ratios.hangul = 50 + (index % 151);
        style.spacing.latin = -50 + i16::try_from(index % 101)?;
        style.relative_sizes.hanja = 10 + (index % 241);
        style.offsets.hangul = -100 + i16::try_from(index % 201)?;
        style.offsets.japanese = -100 + i16::try_from(index % 151)?;
        style.text_color = Color::Rgb(
            u8::try_from(index)?,
            u8::try_from(index.wrapping_mul(3) % 256)?,
            u8::try_from(index.wrapping_mul(7) % 256)?,
        );
        style.effects.bold = if index & 1 == 0 {
            BinaryProperty::Off
        } else {
            BinaryProperty::On
        };
        style.effects.italic = if index & 2 == 0 {
            BinaryProperty::Off
        } else {
            BinaryProperty::On
        };
        style.effects.superscript = if index % 3 == 0 {
            BinaryProperty::On
        } else {
            BinaryProperty::Off
        };
        style.effects.subscript = BinaryProperty::Off;

        let (first, first_receipt) = CharacterStyleCatalogWriter::lower_with_receipt(
            &catalog,
            CharacterStyleLimits::default(),
        )?;
        let (second, second_receipt) = CharacterStyleCatalogWriter::lower_with_receipt(
            &catalog,
            CharacterStyleLimits::default(),
        )?;
        assert_eq!(first, second);
        assert_eq!(first_receipt, second_receipt);
        aggregate.update(first_receipt.sha256);
    }
    assert_eq!(
        hex::encode(aggregate.finalize()),
        "5d2a03a19961f26ce46babf6e2d12eac28b23916aff35769fe5a8e0f0dc91e6d"
    );
    Ok(())
}
