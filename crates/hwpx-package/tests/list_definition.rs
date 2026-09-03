use std::error::Error;

use hwpx_package::{
    BulletDefinition, CompatibleHeading, Heading, HeadingType, LIST_DEFINITION_PROFILE_ID,
    ListAlignment, ListBinding, ListDefinitionCatalog, ListDefinitionCatalogReader,
    ListDefinitionCatalogWriter, ListDefinitionError, ListDefinitionLimitConfig,
    ListDefinitionLimits, ListSequenceEngine, ListSequenceItem, ListSequenceKind, NumberFormat,
    NumberingDefinition, NumberingLevel, OutlineDefinitionBindingReader, ParagraphHeadStyle,
    ParagraphStyleCatalogReader, ParagraphStyleLimits, TextOffsetUnit,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");

fn head(format: NumberFormat, template: &str) -> ParagraphHeadStyle {
    ParagraphHeadStyle {
        alignment: ListAlignment::Left,
        use_instance_width: true,
        auto_indent: true,
        width_adjust: 0,
        text_offset_unit: TextOffsetUnit::Percent,
        text_offset: 50,
        number_format: format,
        character_style_id_ref: None,
        checkable: false,
        template: template.to_owned(),
    }
}

fn numbering(id: u32) -> NumberingDefinition {
    let formats = [
        NumberFormat::Digit,
        NumberFormat::HangulSyllable,
        NumberFormat::Digit,
        NumberFormat::HangulSyllable,
        NumberFormat::Digit,
        NumberFormat::HangulSyllable,
        NumberFormat::CircledDigit,
        NumberFormat::CircledHangulSyllable,
        NumberFormat::HangulJamo,
        NumberFormat::RomanSmall,
    ];
    NumberingDefinition {
        id,
        start: 0,
        levels: (1_u8..=10)
            .zip(formats)
            .map(|(level, format)| NumberingLevel {
                level,
                start: 1,
                head: head(format, if level <= 8 { "^1." } else { "" }),
            })
            .collect(),
    }
}

fn bullet(id: u32, checked: bool) -> BulletDefinition {
    let mut bullet_head = head(NumberFormat::Digit, "");
    bullet_head.checkable = checked;
    BulletDefinition {
        id,
        mark: '•',
        checked_mark: checked.then_some('✓'),
        head: bullet_head,
    }
}

fn catalog_with_bullet() -> ListDefinitionCatalog {
    ListDefinitionCatalog {
        numberings: vec![numbering(1)],
        bullets: vec![bullet(1, true)],
    }
}

#[test]
fn exact_current_2020_header_lifts_numbering_and_no_bullets() -> TestResult {
    let catalog = ListDefinitionCatalogReader::read(HEADER, ListDefinitionLimits::default())?;
    assert_eq!(catalog.numberings.len(), 1);
    assert!(catalog.bullets.is_empty());
    let numbering = &catalog.numberings[0];
    assert_eq!(numbering.id, 1);
    assert_eq!(numbering.start, 0);
    assert_eq!(numbering.levels.len(), 10);
    assert_eq!(numbering.levels[0].level, 1);
    assert_eq!(numbering.levels[0].head.template, "^1.");
    assert_eq!(
        numbering.levels[1].head.number_format,
        NumberFormat::HangulSyllable
    );
    assert!(numbering.levels[6].head.checkable);
    assert_eq!(
        numbering.levels[9].head.number_format,
        NumberFormat::RomanSmall
    );
    assert_eq!(numbering.levels[9].head.template, "");
    let paragraphs = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    catalog.validate_paragraph_references(
        &paragraphs,
        1,
        &[0, 1, 2, 3, 4, 5, 6],
        ListDefinitionLimits::default(),
    )?;
    assert_eq!(
        catalog.validate_paragraph_references(
            &paragraphs,
            2,
            &[0, 1, 2, 3, 4, 5, 6],
            ListDefinitionLimits::default(),
        ),
        Err(ListDefinitionError::DanglingReference)
    );
    Ok(())
}

#[test]
fn section_outline_binding_is_typed_and_closed_against_numberings() -> TestResult {
    let catalog = ListDefinitionCatalogReader::read(HEADER, ListDefinitionLimits::default())?;
    let section = br#"<?xml version="1.0" encoding="UTF-8"?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p><hp:run><hp:secPr outlineShapeIDRef="1"/></hp:run></hp:p></hs:sec>"#;
    assert_eq!(
        OutlineDefinitionBindingReader::read(
            section,
            &catalog,
            &[0, 1, 2, 3, 4, 5, 6],
            ListDefinitionLimits::default(),
        )?
        .numbering_definition_id,
        1
    );
    let dangling =
        std::str::from_utf8(section)?.replace("outlineShapeIDRef=\"1\"", "outlineShapeIDRef=\"2\"");
    assert_eq!(
        OutlineDefinitionBindingReader::read(
            dangling.as_bytes(),
            &catalog,
            &[0, 1, 2, 3, 4, 5, 6],
            ListDefinitionLimits::default(),
        ),
        Err(ListDefinitionError::DanglingReference)
    );
    Ok(())
}

#[test]
fn lower_is_deterministic_escaped_and_exactly_readable() -> TestResult {
    let mut catalog = catalog_with_bullet();
    catalog.numberings[0].levels[0].head.character_style_id_ref = Some(0);
    catalog.numberings[0].levels[0].head.template = "^1 & 항목".to_owned();
    catalog.bullets[0].head.character_style_id_ref = Some(0);
    let (first, first_receipt) = ListDefinitionCatalogWriter::lower_with_receipt(
        &catalog,
        &[0],
        ListDefinitionLimits::default(),
    )?;
    let (second, second_receipt) = ListDefinitionCatalogWriter::lower_with_receipt(
        &catalog,
        &[0],
        ListDefinitionLimits::default(),
    )?;
    assert_eq!(first, second);
    assert_eq!(first_receipt, second_receipt);
    assert_eq!(first_receipt.profile_id, LIST_DEFINITION_PROFILE_ID);
    assert_eq!(first_receipt.numbering_count, 1);
    assert_eq!(first_receipt.bullet_count, 1);
    assert_eq!(first_receipt.level_count, 11);
    assert_eq!(
        ListDefinitionCatalogReader::read_with_character_style_domain(
            &first,
            &[0],
            ListDefinitionLimits::default()
        )?,
        catalog
    );
    let xml = std::str::from_utf8(&first)?;
    assert!(xml.contains("^1 &amp; 항목"));
    assert!(xml.contains("char=\"•\" checkedChar=\"✓\" useImage=\"0\""));
    Ok(())
}

#[test]
fn official_number_formats_are_typed_and_image_fails_without_binary_closure() -> TestResult {
    let formats = [
        NumberFormat::Digit,
        NumberFormat::CircledDigit,
        NumberFormat::RomanCapital,
        NumberFormat::RomanSmall,
        NumberFormat::LatinCapital,
        NumberFormat::LatinSmall,
        NumberFormat::CircledLatinCapital,
        NumberFormat::CircledLatinSmall,
        NumberFormat::HangulSyllable,
        NumberFormat::CircledHangulSyllable,
        NumberFormat::HangulJamo,
        NumberFormat::CircledHangulJamo,
        NumberFormat::HangulPhonetic,
        NumberFormat::Ideograph,
        NumberFormat::CircledIdeograph,
        NumberFormat::DecagonCircle,
        NumberFormat::DecagonCircleHanja,
        NumberFormat::Symbol,
        NumberFormat::UserChar,
        NumberFormat::Symbol2,
        NumberFormat::Image,
        NumberFormat::TwoDigit,
    ];
    for (case, format) in formats.into_iter().enumerate() {
        let mut catalog = ListDefinitionCatalog {
            numberings: vec![numbering(1)],
            bullets: Vec::new(),
        };
        catalog.numberings[0].levels[case % 10].head.number_format = format;
        if format == NumberFormat::Image {
            assert_eq!(
                ListDefinitionCatalogWriter::lower(&catalog, &[], ListDefinitionLimits::default()),
                Err(ListDefinitionError::UnsupportedShape)
            );
        } else {
            let bytes =
                ListDefinitionCatalogWriter::lower(&catalog, &[], ListDefinitionLimits::default())?;
            assert_eq!(
                ListDefinitionCatalogReader::read(&bytes, ListDefinitionLimits::default())?,
                catalog
            );
        }
    }
    Ok(())
}

#[test]
fn semantic_dedup_rewrites_number_bullet_and_outline_references_atomically() -> TestResult {
    let first_numbering = numbering(1);
    let mut second_numbering = first_numbering.clone();
    second_numbering.id = 2;
    let first_bullet = bullet(1, false);
    let mut second_bullet = first_bullet.clone();
    second_bullet.id = 2;
    let catalog = ListDefinitionCatalog {
        numberings: vec![first_numbering, second_numbering],
        bullets: vec![first_bullet, second_bullet],
    };
    let deduplicated = catalog.deduplicate(&[], ListDefinitionLimits::default())?;
    assert_eq!(deduplicated.numbering_old_to_new, [1, 1]);
    assert_eq!(deduplicated.bullet_old_to_new, [1, 1]);
    assert_eq!(deduplicated.catalog.numberings.len(), 1);
    assert_eq!(deduplicated.catalog.bullets.len(), 1);

    let mut paragraphs =
        ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    paragraphs.references.numbering_ids = vec![1, 2];
    paragraphs.references.bullet_ids = vec![1, 2];
    paragraphs.styles[0].heading = CompatibleHeading::Direct(Heading {
        heading_type: HeadingType::Number,
        id_ref: 2,
        level: 1,
    });
    paragraphs.styles[1].heading = CompatibleHeading::Direct(Heading {
        heading_type: HeadingType::Bullet,
        id_ref: 2,
        level: 0,
    });
    deduplicated.rewrite_paragraph_references(
        &mut paragraphs,
        &[0, 1, 2, 3, 4, 5, 6],
        ListDefinitionLimits::default(),
    )?;
    assert_eq!(paragraphs.references.numbering_ids, [1]);
    assert_eq!(paragraphs.references.bullet_ids, [1]);
    assert!(matches!(
        paragraphs.styles[0].heading,
        CompatibleHeading::Direct(Heading { id_ref: 1, .. })
    ));
    assert!(matches!(
        paragraphs.styles[1].heading,
        CompatibleHeading::Direct(Heading { id_ref: 1, .. })
    ));
    assert_eq!(deduplicated.remap_outline_definition_id(2)?, 1);
    Ok(())
}

#[test]
fn malformed_public_map_cannot_partially_rewrite_paragraphs() -> TestResult {
    let mut paragraphs =
        ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let original = paragraphs.clone();
    let malformed = hwpx_package::DeduplicatedListDefinitions {
        catalog: ListDefinitionCatalog {
            numberings: vec![numbering(1)],
            bullets: Vec::new(),
        },
        numbering_old_to_new: vec![2],
        bullet_old_to_new: Vec::new(),
    };
    assert_eq!(
        malformed.rewrite_paragraph_references(
            &mut paragraphs,
            &[0, 1, 2, 3, 4, 5, 6],
            ListDefinitionLimits::default(),
        ),
        Err(ListDefinitionError::InvalidId)
    );
    assert_eq!(paragraphs, original);
    Ok(())
}

#[test]
fn sequence_engine_tracks_nesting_continuity_restart_outline_and_checked_bullets() -> TestResult {
    let catalog = catalog_with_bullet();
    let items = [
        item(1, ListSequenceKind::Number, 0, None, false),
        item(1, ListSequenceKind::Number, 1, None, false),
        item(1, ListSequenceKind::Number, 1, None, false),
        item(1, ListSequenceKind::Number, 0, None, false),
        item(1, ListSequenceKind::Number, 1, Some(7), false),
        ListSequenceItem {
            sequence_id: 2,
            kind: ListSequenceKind::Outline,
            definition_id: 1,
            level: 0,
            restart: Some(3),
            checked: false,
        },
        item(3, ListSequenceKind::Bullet, 0, None, false),
        item(3, ListSequenceKind::Bullet, 1, None, true),
    ];
    let results =
        ListSequenceEngine::evaluate(&catalog, &[], &items, ListDefinitionLimits::default())?;
    assert_eq!(results[0].counters[0], Some(1));
    assert_eq!(&results[1].counters[..2], &[Some(1), Some(1)]);
    assert_eq!(&results[2].counters[..2], &[Some(1), Some(2)]);
    assert_eq!(results[3].counters[0], Some(2));
    assert_eq!(&results[4].counters[..2], &[Some(2), Some(7)]);
    assert!(results[4].restart_applied);
    assert_eq!(results[5].counters[0], Some(3));
    assert_eq!(results[6].bullet_mark, Some('•'));
    assert_eq!(results[7].bullet_mark, Some('✓'));
    assert_eq!(results[7].level, 1);
    Ok(())
}

fn item(
    sequence_id: u32,
    kind: ListSequenceKind,
    level: u8,
    restart: Option<u32>,
    checked: bool,
) -> ListSequenceItem {
    ListSequenceItem {
        sequence_id,
        kind,
        definition_id: 1,
        level,
        restart,
        checked,
    }
}

#[test]
fn sequence_engine_rejects_skips_conflicts_zero_restart_and_overflow() {
    let catalog = catalog_with_bullet();
    let limits = ListDefinitionLimits::default();
    assert_eq!(
        ListSequenceEngine::evaluate(
            &catalog,
            &[],
            &[item(1, ListSequenceKind::Number, 1, None, false)],
            limits
        ),
        Err(ListDefinitionError::InvalidSequence)
    );
    assert_eq!(
        ListSequenceEngine::evaluate(
            &catalog,
            &[],
            &[
                item(1, ListSequenceKind::Number, 0, None, false),
                item(1, ListSequenceKind::Number, 2, None, false),
            ],
            limits
        ),
        Err(ListDefinitionError::InvalidSequence)
    );
    assert_eq!(
        ListSequenceEngine::evaluate(
            &catalog,
            &[],
            &[
                item(1, ListSequenceKind::Number, 0, None, false),
                item(1, ListSequenceKind::Outline, 0, None, false),
            ],
            limits
        ),
        Err(ListDefinitionError::InvalidSequence)
    );
    assert_eq!(
        ListSequenceEngine::evaluate(
            &catalog,
            &[],
            &[item(1, ListSequenceKind::Number, 0, Some(0), false)],
            limits
        ),
        Err(ListDefinitionError::InvalidSequence)
    );
    let mut overflowing = catalog;
    overflowing.numberings[0].levels[0].start = u32::MAX;
    assert_eq!(
        ListSequenceEngine::evaluate(
            &overflowing,
            &[],
            &[
                item(1, ListSequenceKind::Number, 0, None, false),
                item(1, ListSequenceKind::Number, 0, None, false),
            ],
            limits
        ),
        Err(ListDefinitionError::CounterOverflow)
    );
}

#[test]
fn list_bindings_apply_remove_and_change_levels_without_raw_xml() -> TestResult {
    let number = ListBinding::Number {
        definition_id: 2,
        level: 0,
    };
    assert_eq!(ListBinding::from_heading(number.to_heading()?)?, number);
    assert_eq!(
        number
            .increase_level()?
            .increase_level()?
            .decrease_level()?,
        ListBinding::Number {
            definition_id: 2,
            level: 1
        }
    );
    assert_eq!(
        ListBinding::remove().to_heading()?.heading_type,
        HeadingType::None
    );
    assert_eq!(
        ListBinding::Outline { level: 9 }.increase_level(),
        Err(ListDefinitionError::InvalidSequence)
    );
    assert_eq!(
        ListBinding::Bullet {
            definition_id: 1,
            level: 0
        }
        .decrease_level(),
        Err(ListDefinitionError::InvalidSequence)
    );
    Ok(())
}

#[test]
fn malformed_xml_shapes_fail_closed() -> TestResult {
    let bytes = ListDefinitionCatalogWriter::lower(
        &catalog_with_bullet(),
        &[],
        ListDefinitionLimits::default(),
    )?;
    let source = std::str::from_utf8(&bytes)?;
    let cases = [
        (
            source.replacen("numberings itemCnt=\"1\"", "numberings itemCnt=\"2\"", 1),
            ListDefinitionError::CountMismatch,
        ),
        (
            source.replacen("numbering id=\"1\"", "numbering id=\"2\"", 1),
            ListDefinitionError::InvalidId,
        ),
        (
            source.replacen("level=\"1\"", "level=\"2\"", 1),
            ListDefinitionError::InvalidId,
        ),
        (
            source.replacen("useImage=\"0\"", "useImage=\"1\"", 1),
            ListDefinitionError::UnsupportedShape,
        ),
        (
            source.replacen("align=\"LEFT\"", "align=\"SIDEWAYS\"", 1),
            ListDefinitionError::InvalidEnum,
        ),
        (
            source.replacen("autoIndent=\"1\"", "autoIndent=\"maybe\"", 1),
            ListDefinitionError::InvalidBoolean,
        ),
        (
            source.replacen("start=\"1\"", "start=\"0\"", 1),
            ListDefinitionError::OutOfRange,
        ),
        (
            source.replacen("<hh:numbering ", "<hh:numbering extra=\"x\" ", 1),
            ListDefinitionError::UnsupportedShape,
        ),
    ];
    for (case, expected) in cases {
        assert_eq!(
            ListDefinitionCatalogReader::read(case.as_bytes(), ListDefinitionLimits::default()),
            Err(expected)
        );
    }
    Ok(())
}

#[test]
fn character_references_and_bullet_shapes_are_strict() {
    let mut catalog = catalog_with_bullet();
    catalog.numberings[0].levels[0].head.character_style_id_ref = Some(1);
    assert_eq!(
        ListDefinitionCatalogWriter::lower(&catalog, &[0], ListDefinitionLimits::default()),
        Err(ListDefinitionError::DanglingReference)
    );
    catalog.numberings[0].levels[0].head.character_style_id_ref = None;
    catalog.bullets[0].checked_mark = None;
    assert_eq!(
        ListDefinitionCatalogWriter::lower(&catalog, &[], ListDefinitionLimits::default()),
        Err(ListDefinitionError::UnsupportedShape)
    );
    catalog.bullets[0].head.checkable = false;
    catalog.bullets[0].mark = ' ';
    assert_eq!(
        ListDefinitionCatalogWriter::lower(&catalog, &[], ListDefinitionLimits::default()),
        Err(ListDefinitionError::InvalidText)
    );
}

#[test]
fn finite_limits_cover_input_output_definition_text_and_sequence_counts() -> TestResult {
    assert_eq!(
        ListDefinitionLimits::new(ListDefinitionLimitConfig {
            input_bytes: 0,
            ..ListDefinitionLimitConfig::default()
        }),
        Err(ListDefinitionError::InvalidLimit)
    );
    let tiny_input = ListDefinitionLimits::new(ListDefinitionLimitConfig {
        input_bytes: 64,
        ..ListDefinitionLimitConfig::default()
    })?;
    assert_eq!(
        ListDefinitionCatalogReader::read(HEADER, tiny_input),
        Err(ListDefinitionError::InputLimit)
    );
    assert_eq!(
        ListDefinitionCatalogWriter::lower(&catalog_with_bullet(), &[], tiny_input),
        Err(ListDefinitionError::OutputLimit)
    );
    let one_sequence = ListDefinitionLimits::new(ListDefinitionLimitConfig {
        sequence_items: 1,
        ..ListDefinitionLimitConfig::default()
    })?;
    assert_eq!(
        ListSequenceEngine::evaluate(
            &catalog_with_bullet(),
            &[],
            &[
                item(1, ListSequenceKind::Number, 0, None, false),
                item(1, ListSequenceKind::Number, 0, None, false),
            ],
            one_sequence
        ),
        Err(ListDefinitionError::SequenceLimit)
    );
    let tiny_text = ListDefinitionLimits::new(ListDefinitionLimitConfig {
        text_bytes: 1,
        ..ListDefinitionLimitConfig::default()
    })?;
    assert_eq!(
        ListDefinitionCatalogWriter::lower(&catalog_with_bullet(), &[], tiny_text),
        Err(ListDefinitionError::InvalidText)
    );
    let tiny_references = ListDefinitionLimits::new(ListDefinitionLimitConfig {
        reference_items: 1,
        ..ListDefinitionLimitConfig::default()
    })?;
    let exact_catalog = ListDefinitionCatalogReader::read(HEADER, ListDefinitionLimits::default())?;
    let exact_paragraphs =
        ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    assert_eq!(
        exact_catalog.validate_paragraph_references(
            &exact_paragraphs,
            1,
            &[0, 1, 2, 3, 4, 5, 6],
            tiny_references,
        ),
        Err(ListDefinitionError::ReferenceLimit)
    );
    Ok(())
}

#[test]
fn stable_error_codes_cover_every_failure_class() {
    let cases = [
        (
            ListDefinitionError::InvalidLimit,
            "list_definition_invalid_limit",
        ),
        (
            ListDefinitionError::InputLimit,
            "list_definition_input_limit",
        ),
        (ListDefinitionError::WrongRoot, "list_definition_wrong_root"),
        (
            ListDefinitionError::UnsupportedShape,
            "list_definition_unsupported_shape",
        ),
        (
            ListDefinitionError::CountMismatch,
            "list_definition_count_mismatch",
        ),
        (ListDefinitionError::InvalidId, "list_definition_invalid_id"),
        (
            ListDefinitionError::DanglingReference,
            "list_definition_dangling_reference",
        ),
        (
            ListDefinitionError::ReferenceLimit,
            "list_definition_reference_limit",
        ),
        (
            ListDefinitionError::InvalidNumber,
            "list_definition_invalid_number",
        ),
        (
            ListDefinitionError::InvalidBoolean,
            "list_definition_invalid_boolean",
        ),
        (
            ListDefinitionError::InvalidEnum,
            "list_definition_invalid_enum",
        ),
        (
            ListDefinitionError::InvalidText,
            "list_definition_invalid_text",
        ),
        (
            ListDefinitionError::OutOfRange,
            "list_definition_out_of_range",
        ),
        (
            ListDefinitionError::DefinitionLimit,
            "list_definition_definition_limit",
        ),
        (
            ListDefinitionError::LevelLimit,
            "list_definition_level_limit",
        ),
        (
            ListDefinitionError::ElementLimit,
            "list_definition_element_limit",
        ),
        (
            ListDefinitionError::InvalidSequence,
            "list_definition_invalid_sequence",
        ),
        (
            ListDefinitionError::SequenceLimit,
            "list_definition_sequence_limit",
        ),
        (
            ListDefinitionError::CounterOverflow,
            "list_definition_counter_overflow",
        ),
        (
            ListDefinitionError::OutputLimit,
            "list_definition_output_limit",
        ),
        (
            ListDefinitionError::AllocationFailed,
            "list_definition_allocation_failed",
        ),
        (
            ListDefinitionError::ReadbackMismatch,
            "list_definition_readback_mismatch",
        ),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}

#[test]
fn fixed_128_case_catalog_and_sequence_corpus_is_deterministic() -> TestResult {
    fn digest() -> Result<[u8; 32], Box<dyn Error>> {
        let mut aggregate = Sha256::new();
        for case in 0_u32..128 {
            let mut catalog = catalog_with_bullet();
            let level = usize::try_from(case % 10)?;
            catalog.numberings[0].start = case;
            catalog.numberings[0].levels[level].start = case + 1;
            catalog.numberings[0].levels[level].head.width_adjust = i32::try_from(case)? - 64;
            catalog.numberings[0].levels[level].head.text_offset = i32::try_from(case % 101)?;
            catalog.numberings[0].levels[level].head.alignment = match case % 3 {
                0 => ListAlignment::Left,
                1 => ListAlignment::Center,
                _ => ListAlignment::Right,
            };
            catalog.numberings[0].levels[level].head.template = format!("^{level}-case-{case}");
            let (bytes, receipt) = ListDefinitionCatalogWriter::lower_with_receipt(
                &catalog,
                &[],
                ListDefinitionLimits::default(),
            )?;
            let sequence = ListSequenceEngine::evaluate(
                &catalog,
                &[],
                &[
                    item(case + 1, ListSequenceKind::Number, 0, Some(case + 1), false),
                    item(case + 1, ListSequenceKind::Number, 0, None, false),
                ],
                ListDefinitionLimits::default(),
            )?;
            aggregate.update(case.to_le_bytes());
            aggregate.update(receipt.sha256);
            aggregate.update(Sha256::digest(bytes));
            aggregate.update(
                sequence[1].counters[0]
                    .ok_or("missing counter")?
                    .to_le_bytes(),
            );
        }
        Ok(aggregate.finalize().into())
    }
    let first = digest()?;
    let second = digest()?;
    assert_eq!(first, second);
    assert_eq!(
        hex::encode(first),
        "7798294a9b581ff434befcc80f201f28b93430cbd1c74581b9a9f20f3e97dbd1"
    );
    Ok(())
}
