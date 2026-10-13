//! Actual immutable source selection + the unchanged native template validators.
//! All packages are synthetic in-memory fixtures, NOT Hangul save/reopen acceptance.
#[path = "support/document_import_review_assembly_fixture.rs"]
mod assembly;
#[path = "table_create_hwpx.rs"]
mod native;
use domain_ir::{DocumentId, Node, SourceAnchorHandle};
use hwpx_package::{
    BoundedZipReader, PackageLimits, TABLE_CREATE_HWPX_PROFILE_ID, TableCreateHwpxLimits,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        forms::ImportedDocumentForms,
        structure::review::{
            ImportedDocumentReviewBodies,
            table_create_context::{ReviewTableContextError, ReviewTableTemplate},
        },
    },
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, io::Cursor};
type TestResult<T = ()> = Result<T, Box<dyn Error>>;
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
pub(super) fn forms(bytes: &[u8], document: &str) -> TestResult<ImportedDocumentForms> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse(document)?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
fn source_section() -> String {
    let markers = assembly::markers("").replace("<hp:t>HIDDEN-REVIEW</hp:t>", "<hp:t/>");
    format!(
        "<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='{HP}'><hp:p id='10' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'>{markers}</hp:run></hp:p>{}</hs:sec>",
        native::empty_paragraph(11)
    )
}
pub(super) fn source() -> TestResult<Vec<u8>> {
    native::package(
        &native::header()?,
        source_section().as_bytes(),
        b"OPAQUE-SOURCE-PRIVATE",
    )
}
pub(super) fn template(nonempty: bool) -> TestResult<Vec<u8>> {
    native::package(
        &native::header()?,
        &native::template_section(nonempty),
        b"OPAQUE-TEMPLATE-PRIVATE",
    )
}
pub(super) fn anchor(
    forms: &ImportedDocumentForms,
    bytes: &[u8],
    local: &str,
    id: &str,
) -> TestResult<SourceAnchorHandle> {
    forms.source().verify_source(bytes)?;
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let entry = reader
        .entries()
        .iter()
        .position(|e| e.path.as_str() == "Contents/section0.xml")
        .ok_or("entry")?;
    let raw = reader.read_entry(entry)?;
    let part = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/section0.xml")
        .ok_or("section")?;
    let xml = part.xml().ok_or("xml")?;
    let (i, _) = xml
        .elements()
        .iter()
        .enumerate()
        .find(|(_, e)| {
            e.name().namespace() == Some(HP)
                && e.name().local_name() == local
                && e.attributes().iter().any(|a| {
                    a.name().namespace().is_none()
                        && a.name().local_name() == "id"
                        && raw[a.value_span().start()..a.value_span().end()] == *id.as_bytes()
                })
        })
        .ok_or("anchor")?;
    Ok(part.element_anchor(i).ok_or("identity")?.clone())
}
#[test]
fn memo_and_hidden_prepare_original_native_template_with_actual_tracks_and_ids() -> TestResult {
    let bytes = source()?;
    let tbytes = template(false)?;
    let source = forms(&bytes, "review-table-context")?;
    let template = forms(&tbytes, "native-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = anchor(&template, &tbytes, "tbl", "700")?;
    let actual = template
        .graph()
        .sections()
        .iter()
        .flat_map(|s| &s.body.children)
        .find_map(|n| {
            if let Node::Table(t) = n {
                Some(t)
            } else {
                None
            }
        })
        .ok_or("table graph")?;
    let mut context_hashes = Vec::new();
    for (observation, id) in [(0, "101"), (1, "102")] {
        let paragraph = anchor(&source, &bytes, "p", id)?;
        let result = review.prepare_table_creation(
            &bytes,
            &review.observations()[observation].marker_anchor,
            &paragraph,
            ReviewTableTemplate {
                forms: &template,
                fresh: &tbytes,
                table: &table,
            },
            TableCreateHwpxLimits::default(),
        )?;
        result.verify_source(&bytes, &tbytes)?;
        let native = result.native_context();
        assert_ne!(native.profile_id, TABLE_CREATE_HWPX_PROFILE_ID);
        assert_eq!(native.template.grid.rows(), 2);
        assert_eq!(native.template.grid.columns(), 2);
        assert_eq!(
            native.template.state.row_boundaries_hwpunit(),
            &[0, 500, 1100]
        );
        assert_eq!(
            native.template.state.column_boundaries_hwpunit(),
            &[0, 800, 2000]
        );
        assert_eq!(native.template.payload_block_count, 0);
        assert_eq!(native.template.formula_count, 0);
        assert_eq!(native.source_table_count, 0);
        assert_eq!(
            native
                .template
                .grid
                .master_cells()
                .iter()
                .map(|c| &c.master_cell_id)
                .collect::<Vec<_>>(),
            actual.cells.iter().map(|c| &c.cell_id).collect::<Vec<_>>()
        );
        assert_eq!(result.receipt().header_binding,
            hwpx_package::document_import::structure::review::table_create_context::ReviewTableHeaderBinding::ExactSharedOriginalHeader);
        assert!(!result.receipt().new_table_inserted);
        assert!(!result.receipt().full_document_flow_bound);
        assert!(!result.receipt().full_comment_product_acceptance);
        assert!(!format!("{result:?}").contains("PRIVATE"));
        context_hashes.push(native.insertion_context_sha256.clone());
    }
    assert_ne!(context_hashes[0], context_hashes[1]);
    source.source().verify_source(&bytes)?;
    template.source().verify_source(&tbytes)?;
    Ok(())
}
#[test]
fn foreign_other_review_main_nonparagraph_and_template_selections_reject() -> TestResult {
    let bytes = source()?;
    let tbytes = template(false)?;
    let source = forms(&bytes, "selection-owner")?;
    let foreign = forms(&bytes, "foreign-owner")?;
    let template = forms(&tbytes, "selection-template")?;
    let other_template = forms(&tbytes, "foreign-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let marker = &review.observations()[0].marker_anchor;
    let table = anchor(&template, &tbytes, "tbl", "700")?;
    for selected in [
        anchor(&foreign, &bytes, "p", "101")?,
        anchor(&source, &bytes, "p", "102")?,
        anchor(&source, &bytes, "p", "10")?,
        anchor(&source, &bytes, "p", "11")?,
        marker.clone(),
    ] {
        assert!(
            review
                .prepare_table_creation(
                    &bytes,
                    marker,
                    &selected,
                    ReviewTableTemplate {
                        forms: &template,
                        fresh: &tbytes,
                        table: &table
                    },
                    TableCreateHwpxLimits::default()
                )
                .is_err()
        );
    }
    let paragraph = anchor(&source, &bytes, "p", "101")?;
    for wrong in [
        anchor(&other_template, &tbytes, "tbl", "700")?,
        anchor(&template, &tbytes, "p", "900")?,
    ] {
        assert!(matches!(
            review.prepare_table_creation(
                &bytes,
                marker,
                &paragraph,
                ReviewTableTemplate {
                    forms: &template,
                    fresh: &tbytes,
                    table: &wrong
                },
                TableCreateHwpxLimits::default()
            ),
            Err(ReviewTableContextError::Template)
        ));
    }
    assert!(matches!(
        review.prepare_table_creation(
            &bytes,
            &foreign.source().parts()[0].anchor().clone(),
            &paragraph,
            ReviewTableTemplate {
                forms: &template,
                fresh: &tbytes,
                table: &table
            },
            TableCreateHwpxLimits::default()
        ),
        Err(ReviewTableContextError::Selection)
    ));
    Ok(())
}
#[test]
fn fresh_replay_binds_both_entire_archives_including_opaque_parts() -> TestResult {
    let bytes = source()?;
    let tbytes = template(false)?;
    let source = forms(&bytes, "fresh-owner")?;
    let template = forms(&tbytes, "fresh-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = anchor(&template, &tbytes, "tbl", "700")?;
    let paragraph = anchor(&source, &bytes, "p", "101")?;
    let context = review.prepare_table_creation(
        &bytes,
        &review.observations()[0].marker_anchor,
        &paragraph,
        ReviewTableTemplate {
            forms: &template,
            fresh: &tbytes,
            table: &table,
        },
        TableCreateHwpxLimits::default(),
    )?;
    let changed_source = native::package(
        &native::header()?,
        source_section().as_bytes(),
        b"DIFFERENT-OPAQUE",
    )?;
    let changed_template = native::package(
        &native::header()?,
        &native::template_section(false),
        b"DIFFERENT-OPAQUE",
    )?;
    assert!(matches!(
        context.verify_source(&changed_source, &tbytes),
        Err(ReviewTableContextError::Source)
    ));
    assert!(matches!(
        context.verify_source(&bytes, &changed_template),
        Err(ReviewTableContextError::Source)
    ));
    assert!(matches!(
        review.prepare_table_creation(
            &bytes,
            &review.observations()[0].marker_anchor,
            &paragraph,
            ReviewTableTemplate {
                forms: &template,
                fresh: &changed_template,
                table: &table
            },
            TableCreateHwpxLimits::default()
        ),
        Err(ReviewTableContextError::Source)
    ));
    Ok(())
}
#[test]
fn nonempty_placeholder_and_native_table_collision_reject() -> TestResult {
    let tbytes = template(false)?;
    let template = forms(&tbytes, "collision-template")?;
    let table = anchor(&template, &tbytes, "tbl", "700")?;
    let cases = [
        source_section().replace("<hp:t></hp:t>", "<hp:t>PRIVATE-NONEMPTY</hp:t>"),
        source_section().replace(
            "</hs:sec>",
            &format!(
                "{}</hs:sec>",
                std::str::from_utf8(&native::template_section(false))?
                    .split_once('>')
                    .ok_or("root")?
                    .1
                    .rsplit_once("</hs:sec>")
                    .ok_or("end")?
                    .0
            ),
        ),
    ];
    for (i, section) in cases.into_iter().enumerate() {
        let bytes = native::package(&native::header()?, section.as_bytes(), b"OPAQUE")?;
        let source = forms(&bytes, "reject-context")?;
        let review = ImportedDocumentReviewBodies::import(&source)?;
        let paragraph = anchor(&source, &bytes, "p", "101")?;
        let error = review
            .prepare_table_creation(
                &bytes,
                &review.observations()[0].marker_anchor,
                &paragraph,
                ReviewTableTemplate {
                    forms: &template,
                    fresh: &tbytes,
                    table: &table,
                },
                TableCreateHwpxLimits::default(),
            )
            .err()
            .ok_or("accepted invalid context")?;
        assert!(
            matches!(error, ReviewTableContextError::Native(_)),
            "case {i}"
        );
    }
    Ok(())
}
#[test]
fn original_nonblank_nonuniform_repeat_and_header_guards_remain() -> TestResult {
    let bytes = source()?;
    let source = forms(&bytes, "template-guard-source")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let paragraph = anchor(&source, &bytes, "p", "101")?;
    let marker = &review.observations()[0].marker_anchor;
    let original = String::from_utf8(native::template_section(false))?;
    for section in [
        String::from_utf8(native::template_section(true))?,
        original.replacen(
            "width=\"800\" height=\"600\"",
            "width=\"900\" height=\"600\"",
            1,
        ),
        original.replacen("repeatHeader=\"0\"", "repeatHeader=\"1\"", 1),
    ] {
        let tbytes = native::package(&native::header()?, section.as_bytes(), b"OPAQUE")?;
        let template = forms(&tbytes, "bad-template")?;
        let table = anchor(&template, &tbytes, "tbl", "700")?;
        assert!(
            review
                .prepare_table_creation(
                    &bytes,
                    marker,
                    &paragraph,
                    ReviewTableTemplate {
                        forms: &template,
                        fresh: &tbytes,
                        table: &table
                    },
                    TableCreateHwpxLimits::default()
                )
                .is_err()
        );
    }
    let mut different_header = native::header()?;
    different_header.extend_from_slice(b" ");
    let tbytes = native::package(&different_header, original.as_bytes(), b"OPAQUE")?;
    let template = forms(&tbytes, "different-header")?;
    let table = anchor(&template, &tbytes, "tbl", "700")?;
    assert!(matches!(
        review.prepare_table_creation(
            &bytes,
            marker,
            &paragraph,
            ReviewTableTemplate {
                forms: &template,
                fresh: &tbytes,
                table: &table
            },
            TableCreateHwpxLimits::default()
        ),
        Err(ReviewTableContextError::Header)
    ));
    Ok(())
}

#[test]
fn original_builder_header_is_not_assumed_compatible_with_native_template() -> TestResult {
    let bytes = assembly::package(&assembly::markers(""))?;
    let source = forms(&bytes, "original-builder-source")?;
    let tbytes = template(false)?;
    let template = forms(&tbytes, "original-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let paragraph = anchor(&source, &bytes, "p", "101")?;
    let table = anchor(&template, &tbytes, "tbl", "700")?;
    assert!(matches!(
        review.prepare_table_creation(
            &bytes,
            &review.observations()[0].marker_anchor,
            &paragraph,
            ReviewTableTemplate {
                forms: &template,
                fresh: &tbytes,
                table: &table
            },
            TableCreateHwpxLimits::default(),
        ),
        Err(ReviewTableContextError::Header)
    ));
    Ok(())
}

#[test]
fn existing_review_cell_context_retains_all_ancestor_protection_checks_and_finite_bounds()
-> TestResult {
    let tbytes = template(false)?;
    let template = forms(&tbytes, "protected-context-template")?;
    let table = anchor(&template, &tbytes, "tbl", "700")?;
    let original = String::from_utf8(native::template_section(false))?;
    let inner = original
        .split_once('>')
        .ok_or("root")?
        .1
        .rsplit_once("</hs:sec>")
        .ok_or("end")?
        .0
        .replace("id=\"700\"", "id=\"701\"");
    for (i, wrapper) in [
        inner.clone(),
        inner.replacen("lock=\"0\"", "lock=\"1\"", 1),
        inner.replacen("protect=\"0\"", "protect=\"1\"", 1),
        inner.replacen("protect=\"0\"", "protect=\"UNKNOWN\"", 1),
        inner.replacen("protect=\"0\" editable", "protect=\"1\" editable", 1),
    ]
    .into_iter()
    .enumerate()
    {
        let section = source_section().replace(
            "</hp:subList></hp:fieldBegin>",
            &format!("{wrapper}</hp:subList></hp:fieldBegin>"),
        );
        let bytes = native::package(&native::header()?, section.as_bytes(), b"OPAQUE")?;
        let source = forms(&bytes, "protected-context-source")?;
        if i == 3 {
            assert!(matches!(ImportedDocumentReviewBodies::import(&source),
                Err(hwpx_package::document_import::structure::review::ReviewBodyImportError::Structure(
                    hwpx_package::document_import::structure::StructureImportError::Table {
                        code: "table_layout_hwpx_invalid_boolean"
                    }
                ))));
            continue;
        }
        let review = ImportedDocumentReviewBodies::import(&source)?;
        // The first repeated numeric p=0 here is explicitly the first actual table cell.
        // Production only receives the source-derived identity, not this fixture numeric locator.
        let paragraph = anchor(&source, &bytes, "p", "0")?;
        let result = review.prepare_table_creation(
            &bytes,
            &review.observations()[0].marker_anchor,
            &paragraph,
            ReviewTableTemplate {
                forms: &template,
                fresh: &tbytes,
                table: &table,
            },
            TableCreateHwpxLimits::default(),
        );
        if i == 0 {
            let context = result?;
            context.verify_source(&bytes, &tbytes)?;
            assert_eq!(context.native_context().source_table_count, 1);
            let tight = TableCreateHwpxLimits {
                pagination: hwpx_package::TablePaginationHwpxLimits::new(
                    hwpx_package::TablePaginationHwpxLimitConfig {
                        input_bytes: 1,
                        ..hwpx_package::TablePaginationHwpxLimitConfig::default()
                    },
                )?,
                ..TableCreateHwpxLimits::default()
            };
            assert!(matches!(
                review.prepare_table_creation(
                    &bytes,
                    &review.observations()[0].marker_anchor,
                    &paragraph,
                    ReviewTableTemplate {
                        forms: &template,
                        fresh: &tbytes,
                        table: &table
                    },
                    tight,
                ),
                Err(ReviewTableContextError::Native(_))
            ));
        } else {
            assert!(
                matches!(result, Err(ReviewTableContextError::Selection)),
                "case {i}"
            );
        }
    }
    Ok(())
}
