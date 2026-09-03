use std::error::Error;

use hwpx_package::{
    DeduplicatedTabDefinitions, LineType2, ParagraphStyleCatalogReader, ParagraphStyleLimits,
    TAB_DEFINITION_PROFILE_ID, TabDefinition, TabDefinitionCatalog, TabDefinitionCatalogReader,
    TabDefinitionCatalogWriter, TabDefinitionError, TabDefinitionLimitConfig, TabDefinitionLimits,
    TabItem, TabPositionUnit, TabStop, TabStopAlignment,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");
const HEAD_NS: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const PARA_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HWPUNIT_CHAR_NS: &str = "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar";

fn fragment(contents: &str, count: usize) -> String {
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><hh:refList xmlns:hh=\"{HEAD_NS}\" \
         xmlns:hp=\"{PARA_NS}\"><hh:tabProperties itemCnt=\"{count}\">{contents}</hh:tabProperties></hh:refList>"
    )
}

fn read(source: &str) -> Result<TabDefinitionCatalog, TabDefinitionError> {
    TabDefinitionCatalogReader::read(source.as_bytes(), TabDefinitionLimits::default())
}

fn item(position: i32, alignment: TabStopAlignment, leader: LineType2) -> TabItem {
    TabItem {
        position,
        alignment,
        leader,
        unit: None,
    }
}

#[test]
fn exact_current_2020_header_lifts_three_automatic_tab_domains() -> TestResult {
    let catalog = TabDefinitionCatalogReader::read(HEADER, TabDefinitionLimits::default())?;
    assert_eq!(catalog.definitions.len(), 3);
    assert_eq!(
        catalog
            .definitions
            .iter()
            .map(|definition| (
                definition.id,
                definition.auto_tab_left,
                definition.auto_tab_right,
                definition.stops.len()
            ))
            .collect::<Vec<_>>(),
        vec![
            (0, false, false, 0),
            (1, true, false, 0),
            (2, false, true, 0)
        ]
    );
    Ok(())
}

#[test]
fn direct_custom_alignments_units_and_leaders_round_trip() -> TestResult {
    let catalog = TabDefinitionCatalog {
        definitions: vec![
            TabDefinition {
                id: 0,
                auto_tab_left: true,
                auto_tab_right: true,
                stops: vec![
                    TabStop::Direct(TabItem {
                        position: 100,
                        alignment: TabStopAlignment::Left,
                        leader: LineType2::None,
                        unit: None,
                    }),
                    TabStop::Direct(TabItem {
                        position: 200,
                        alignment: TabStopAlignment::Right,
                        leader: LineType2::Dot,
                        unit: Some(TabPositionUnit::HwpUnit),
                    }),
                    TabStop::Direct(item(
                        300,
                        TabStopAlignment::Decimal,
                        LineType2::SlimThickSlim,
                    )),
                ],
            },
            TabDefinition {
                id: 1,
                auto_tab_left: false,
                auto_tab_right: false,
                stops: vec![TabStop::Direct(TabItem {
                    position: 40,
                    alignment: TabStopAlignment::Center,
                    leader: LineType2::DashDot,
                    unit: Some(TabPositionUnit::Character),
                })],
            },
        ],
    };
    let (bytes, receipt) =
        TabDefinitionCatalogWriter::lower_with_receipt(&catalog, TabDefinitionLimits::default())?;
    assert_eq!(receipt.profile_id, TAB_DEFINITION_PROFILE_ID);
    assert_eq!(receipt.definition_count, 2);
    assert_eq!(receipt.stop_count, 4);
    assert_eq!(receipt.output_bytes, bytes.len());
    assert_eq!(receipt.sha256, <[u8; 32]>::from(Sha256::digest(&bytes)));
    assert_eq!(
        TabDefinitionCatalogReader::read(&bytes, TabDefinitionLimits::default())?,
        catalog
    );
    Ok(())
}

#[test]
fn hwpunit_char_switch_preserves_even_and_odd_fallback_positions() -> TestResult {
    let source = fragment(
        &format!(
            "<hh:tabPr id=\"0\" autoTabLeft=\"0\" autoTabRight=\"0\">\
             <hp:switch><hp:case hp:required-namespace=\"{HWPUNIT_CHAR_NS}\">\
             <hh:tabItem pos=\"50\" type=\"LEFT\" leader=\"NONE\" unit=\"HWPUNIT\"/>\
             </hp:case><hp:default><hh:tabItem pos=\"101\" type=\"LEFT\" leader=\"NONE\"/>\
             </hp:default></hp:switch>\
             <hp:switch><hp:case hp:required-namespace=\"{HWPUNIT_CHAR_NS}\">\
             <hh:tabItem pos=\"100\" type=\"DECIMAL\" leader=\"DOT\" unit=\"HWPUNIT\"/>\
             </hp:case><hp:default><hh:tabItem pos=\"200\" type=\"DECIMAL\" leader=\"DOT\"/>\
             </hp:default></hp:switch></hh:tabPr>"
        ),
        1,
    );
    let catalog = read(&source)?;
    assert_eq!(catalog.definitions[0].stops[0].effective_position(), 101);
    assert_eq!(catalog.definitions[0].stops[1].effective_position(), 200);
    let bytes = TabDefinitionCatalogWriter::lower(&catalog, TabDefinitionLimits::default())?;
    assert_eq!(read(std::str::from_utf8(&bytes)?)?, catalog);
    Ok(())
}

#[test]
fn all_appendix_f_line_type2_leaders_are_typed() -> TestResult {
    let leaders = [
        LineType2::None,
        LineType2::Solid,
        LineType2::Dot,
        LineType2::Dash,
        LineType2::DashDot,
        LineType2::DashDotDot,
        LineType2::LongDash,
        LineType2::Circle,
        LineType2::DoubleSlim,
        LineType2::SlimThick,
        LineType2::ThickSlim,
        LineType2::SlimThickSlim,
    ];
    let catalog = TabDefinitionCatalog {
        definitions: vec![TabDefinition {
            id: 0,
            auto_tab_left: false,
            auto_tab_right: false,
            stops: leaders
                .into_iter()
                .enumerate()
                .map(|(index, leader)| {
                    Ok(TabStop::Direct(item(
                        i32::try_from((index + 1) * 100)?,
                        TabStopAlignment::Left,
                        leader,
                    )))
                })
                .collect::<Result<Vec<_>, std::num::TryFromIntError>>()?,
        }],
    };
    let bytes = TabDefinitionCatalogWriter::lower(&catalog, TabDefinitionLimits::default())?;
    assert_eq!(
        TabDefinitionCatalogReader::read(&bytes, TabDefinitionLimits::default())?,
        catalog
    );
    Ok(())
}

#[test]
fn semantic_dedup_rewrites_only_typed_paragraph_tab_references() -> TestResult {
    let source = fragment(
        concat!(
            "<hh:tabPr id=\"0\" autoTabLeft=\"0\" autoTabRight=\"0\"/>",
            "<hh:tabPr id=\"1\" autoTabLeft=\"0\" autoTabRight=\"0\"/>",
            "<hh:tabPr id=\"2\" autoTabLeft=\"0\" autoTabRight=\"1\"/>"
        ),
        3,
    );
    let catalog = read(&source)?;
    let deduplicated = catalog.deduplicate(TabDefinitionLimits::default())?;
    assert_eq!(deduplicated.old_to_new, vec![0, 0, 1]);
    assert_eq!(deduplicated.definitions.len(), 2);

    let mut paragraphs =
        ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let before_ids = paragraphs
        .styles
        .iter()
        .map(|style| style.id)
        .collect::<Vec<_>>();
    deduplicated.rewrite_paragraph_styles(&mut paragraphs)?;
    assert_eq!(paragraphs.references.tab_property_ids, vec![0, 1]);
    assert_eq!(
        paragraphs
            .styles
            .iter()
            .map(|style| style.id)
            .collect::<Vec<_>>(),
        before_ids
    );
    assert!(
        paragraphs
            .styles
            .iter()
            .all(|style| style.tab_property_id_ref < 2)
    );
    TabDefinitionCatalog {
        definitions: deduplicated.definitions,
    }
    .validate_paragraph_references(&paragraphs, TabDefinitionLimits::default())?;
    Ok(())
}

#[test]
fn malformed_public_dedup_map_cannot_partially_rewrite() -> TestResult {
    let mut paragraphs =
        ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let original = paragraphs.clone();
    let malformed = DeduplicatedTabDefinitions {
        definitions: vec![TabDefinition {
            id: 0,
            auto_tab_left: false,
            auto_tab_right: false,
            stops: vec![],
        }],
        old_to_new: vec![0, 0, 9],
    };
    assert_eq!(
        malformed.rewrite_paragraph_styles(&mut paragraphs),
        Err(TabDefinitionError::InvalidId)
    );
    assert_eq!(paragraphs, original);
    Ok(())
}

#[test]
fn wrong_namespace_malformed_xml_and_unknown_shape_fail_closed() {
    let wrong = "<hh:refList xmlns:hh=\"urn:wrong\"><hh:tabProperties itemCnt=\"0\"/></hh:refList>";
    assert_eq!(read(wrong), Err(TabDefinitionError::WrongRoot));

    let malformed = "<!DOCTYPE x [<!ENTITY e 'x'>]><hh:refList xmlns:hh=\"http://www.hancom.co.kr/hwpml/2011/head\"><hh:tabProperties itemCnt=\"0\"/></hh:refList>";
    assert!(matches!(
        read(malformed),
        Err(TabDefinitionError::Preserving(_))
    ));

    let unknown = fragment("<hh:tabPr id=\"0\"><hh:unknown/></hh:tabPr>", 1);
    assert_eq!(read(&unknown), Err(TabDefinitionError::UnsupportedShape));
}

#[test]
fn malformed_counts_ids_numbers_booleans_and_enums_are_distinct() {
    let mismatch = fragment("<hh:tabPr id=\"0\"/>", 2);
    assert_eq!(read(&mismatch), Err(TabDefinitionError::CountMismatch));

    let bad_id = fragment("<hh:tabPr id=\"1\"/>", 1);
    assert_eq!(read(&bad_id), Err(TabDefinitionError::InvalidId));

    let bad_number = fragment("<hh:tabPr id=\"+0\"/>", 1);
    assert_eq!(read(&bad_number), Err(TabDefinitionError::InvalidNumber));

    let bad_bool = fragment("<hh:tabPr id=\"0\" autoTabLeft=\"yes\"/>", 1);
    assert_eq!(read(&bad_bool), Err(TabDefinitionError::InvalidBoolean));

    for bad in [
        "<hh:tabPr id=\"0\"><hh:tabItem pos=\"1\" type=\"VERTBAR\" leader=\"NONE\"/></hh:tabPr>",
        "<hh:tabPr id=\"0\"><hh:tabItem pos=\"1\" type=\"LEFT\" leader=\"WAVE\"/></hh:tabPr>",
        "<hh:tabPr id=\"0\"><hh:tabItem pos=\"1\" type=\"LEFT\" leader=\"NONE\" unit=\"PT\"/></hh:tabPr>",
    ] {
        assert_eq!(
            read(&fragment(bad, 1)),
            Err(TabDefinitionError::InvalidEnum)
        );
    }
}

#[test]
fn negative_unordered_and_inconsistent_compatibility_positions_reject() {
    let negative = fragment(
        "<hh:tabPr id=\"0\"><hh:tabItem pos=\"-1\" type=\"LEFT\" leader=\"NONE\"/></hh:tabPr>",
        1,
    );
    assert_eq!(read(&negative), Err(TabDefinitionError::OutOfRange));

    let unordered = fragment(
        concat!(
            "<hh:tabPr id=\"0\">",
            "<hh:tabItem pos=\"100\" type=\"LEFT\" leader=\"NONE\"/>",
            "<hh:tabItem pos=\"100\" type=\"RIGHT\" leader=\"DOT\"/>",
            "</hh:tabPr>"
        ),
        1,
    );
    assert_eq!(read(&unordered), Err(TabDefinitionError::InvalidOrder));

    let mixed_units = fragment(
        concat!(
            "<hh:tabPr id=\"0\">",
            "<hh:tabItem pos=\"10\" type=\"LEFT\" leader=\"NONE\" unit=\"CHAR\"/>",
            "<hh:tabItem pos=\"20\" type=\"RIGHT\" leader=\"NONE\" unit=\"HWPUNIT\"/>",
            "</hh:tabPr>"
        ),
        1,
    );
    assert_eq!(read(&mixed_units), Err(TabDefinitionError::MixedUnits));

    for pair in [
        (
            "<hh:tabItem pos=\"50\" type=\"LEFT\" leader=\"NONE\" unit=\"HWPUNIT\"/>",
            "<hh:tabItem pos=\"102\" type=\"LEFT\" leader=\"NONE\"/>",
        ),
        (
            "<hh:tabItem pos=\"50\" type=\"LEFT\" leader=\"NONE\"/>",
            "<hh:tabItem pos=\"100\" type=\"LEFT\" leader=\"NONE\"/>",
        ),
        (
            "<hh:tabItem pos=\"50\" type=\"LEFT\" leader=\"NONE\" unit=\"HWPUNIT\"/>",
            "<hh:tabItem pos=\"100\" type=\"RIGHT\" leader=\"NONE\"/>",
        ),
    ] {
        let body = format!(
            "<hh:tabPr id=\"0\"><hp:switch><hp:case hp:required-namespace=\"{HWPUNIT_CHAR_NS}\">{}\
             </hp:case><hp:default>{}</hp:default></hp:switch></hh:tabPr>",
            pair.0, pair.1
        );
        assert_eq!(
            read(&fragment(&body, 1)),
            Err(TabDefinitionError::UnsupportedShape)
        );
    }
}

#[test]
fn finite_input_element_definition_stop_and_output_limits_are_enforced() -> TestResult {
    assert_eq!(
        TabDefinitionLimits::new(TabDefinitionLimitConfig {
            input_bytes: 0,
            ..TabDefinitionLimitConfig::default()
        }),
        Err(TabDefinitionError::InvalidLimit)
    );
    let tiny_input = TabDefinitionLimits::new(TabDefinitionLimitConfig {
        input_bytes: 16,
        ..TabDefinitionLimitConfig::default()
    })?;
    assert_eq!(
        TabDefinitionCatalogReader::read(HEADER, tiny_input),
        Err(TabDefinitionError::InputLimit)
    );

    let tiny_elements = TabDefinitionLimits::new(TabDefinitionLimitConfig {
        elements: 1,
        ..TabDefinitionLimitConfig::default()
    })?;
    assert_eq!(
        TabDefinitionCatalogReader::read(HEADER, tiny_elements),
        Err(TabDefinitionError::ElementLimit)
    );

    let one_definition = TabDefinitionLimits::new(TabDefinitionLimitConfig {
        definitions: 1,
        ..TabDefinitionLimitConfig::default()
    })?;
    assert_eq!(
        TabDefinitionCatalogReader::read(HEADER, one_definition),
        Err(TabDefinitionError::DefinitionLimit)
    );

    let two_stops = fragment(
        concat!(
            "<hh:tabPr id=\"0\">",
            "<hh:tabItem pos=\"1\" type=\"LEFT\" leader=\"NONE\"/>",
            "<hh:tabItem pos=\"2\" type=\"RIGHT\" leader=\"NONE\"/>",
            "</hh:tabPr>"
        ),
        1,
    );
    let one_stop = TabDefinitionLimits::new(TabDefinitionLimitConfig {
        stops: 1,
        ..TabDefinitionLimitConfig::default()
    })?;
    assert_eq!(
        TabDefinitionCatalogReader::read(two_stops.as_bytes(), one_stop),
        Err(TabDefinitionError::StopLimit)
    );

    let catalog = TabDefinitionCatalogReader::read(HEADER, TabDefinitionLimits::default())?;
    let small_output = TabDefinitionLimits::new(TabDefinitionLimitConfig {
        input_bytes: 64,
        ..TabDefinitionLimitConfig::default()
    })?;
    assert_eq!(
        TabDefinitionCatalogWriter::lower(&catalog, small_output),
        Err(TabDefinitionError::OutputLimit)
    );
    Ok(())
}

#[test]
fn paragraph_reference_domain_drift_and_dangling_reference_reject() -> TestResult {
    let tabs = TabDefinitionCatalogReader::read(HEADER, TabDefinitionLimits::default())?;
    let mut paragraphs =
        ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    paragraphs.references.tab_property_ids = vec![0, 1];
    assert_eq!(
        tabs.validate_paragraph_references(&paragraphs, TabDefinitionLimits::default()),
        Err(TabDefinitionError::DanglingReference)
    );

    paragraphs.references.tab_property_ids = vec![0, 1, 2];
    paragraphs.styles[0].tab_property_id_ref = 99;
    assert_eq!(
        tabs.validate_paragraph_references(&paragraphs, TabDefinitionLimits::default()),
        Err(TabDefinitionError::DanglingReference)
    );

    let template = paragraphs.styles[0].clone();
    paragraphs.styles = vec![template; TabDefinitionLimits::HARD_MAX_DEFINITIONS + 1];
    assert_eq!(
        tabs.validate_paragraph_references(&paragraphs, TabDefinitionLimits::default()),
        Err(TabDefinitionError::ReferenceLimit)
    );
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (
            TabDefinitionError::InvalidLimit,
            "tab_definition_invalid_limit",
        ),
        (TabDefinitionError::InputLimit, "tab_definition_input_limit"),
        (TabDefinitionError::WrongRoot, "tab_definition_wrong_root"),
        (
            TabDefinitionError::UnsupportedShape,
            "tab_definition_unsupported_shape",
        ),
        (
            TabDefinitionError::CountMismatch,
            "tab_definition_count_mismatch",
        ),
        (TabDefinitionError::InvalidId, "tab_definition_invalid_id"),
        (
            TabDefinitionError::DanglingReference,
            "tab_definition_dangling_reference",
        ),
        (
            TabDefinitionError::ReferenceLimit,
            "tab_definition_reference_limit",
        ),
        (
            TabDefinitionError::InvalidNumber,
            "tab_definition_invalid_number",
        ),
        (
            TabDefinitionError::InvalidBoolean,
            "tab_definition_invalid_boolean",
        ),
        (
            TabDefinitionError::InvalidEnum,
            "tab_definition_invalid_enum",
        ),
        (
            TabDefinitionError::OutOfRange,
            "tab_definition_out_of_range",
        ),
        (
            TabDefinitionError::InvalidOrder,
            "tab_definition_invalid_order",
        ),
        (TabDefinitionError::MixedUnits, "tab_definition_mixed_units"),
        (
            TabDefinitionError::DefinitionLimit,
            "tab_definition_definition_limit",
        ),
        (TabDefinitionError::StopLimit, "tab_definition_stop_limit"),
        (
            TabDefinitionError::ElementLimit,
            "tab_definition_element_limit",
        ),
        (
            TabDefinitionError::OutputLimit,
            "tab_definition_output_limit",
        ),
        (
            TabDefinitionError::AllocationFailed,
            "tab_definition_allocation_failed",
        ),
        (
            TabDefinitionError::ReadbackMismatch,
            "tab_definition_readback_mismatch",
        ),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}

#[test]
fn deterministic_128_case_tab_corpus_has_locked_digest() -> TestResult {
    let leaders = [
        LineType2::None,
        LineType2::Solid,
        LineType2::Dot,
        LineType2::Dash,
        LineType2::DashDot,
        LineType2::DashDotDot,
        LineType2::LongDash,
        LineType2::Circle,
        LineType2::DoubleSlim,
        LineType2::SlimThick,
        LineType2::ThickSlim,
        LineType2::SlimThickSlim,
    ];
    let alignments = [
        TabStopAlignment::Left,
        TabStopAlignment::Right,
        TabStopAlignment::Center,
        TabStopAlignment::Decimal,
    ];
    let mut digest = Sha256::new();
    for case in 0_i32..128 {
        let direct = TabItem {
            position: 1000 + case * 3,
            alignment: alignments[usize::try_from(case)? % alignments.len()],
            leader: leaders[usize::try_from(case)? % leaders.len()],
            unit: if case % 3 == 0 {
                Some(TabPositionUnit::Character)
            } else if case % 3 == 1 {
                Some(TabPositionUnit::HwpUnit)
            } else {
                None
            },
        };
        let fallback_position = 3000 + case * 5;
        let current_position = fallback_position / 2;
        let current = TabItem {
            position: current_position,
            alignment: alignments[(usize::try_from(case)? + 1) % alignments.len()],
            leader: leaders[(usize::try_from(case)? + 5) % leaders.len()],
            unit: Some(TabPositionUnit::HwpUnit),
        };
        let fallback = TabItem {
            position: fallback_position,
            unit: None,
            ..current
        };
        let catalog = TabDefinitionCatalog {
            definitions: vec![
                TabDefinition {
                    id: 0,
                    auto_tab_left: case & 1 != 0,
                    auto_tab_right: case & 2 != 0,
                    stops: vec![TabStop::Direct(direct)],
                },
                TabDefinition {
                    id: 1,
                    auto_tab_left: case & 4 != 0,
                    auto_tab_right: case & 8 != 0,
                    stops: vec![TabStop::HwpUnitChar { current, fallback }],
                },
            ],
        };
        let bytes = TabDefinitionCatalogWriter::lower(&catalog, TabDefinitionLimits::default())?;
        digest.update(u64::try_from(bytes.len())?.to_le_bytes());
        digest.update(bytes);
    }
    assert_eq!(
        hex::encode(digest.finalize()),
        "f1f8d6822de68ca5824cef00cca89e753c61aac5b5956d9b7d5a4ccbdbdd0a92"
    );
    Ok(())
}
