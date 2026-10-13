//! Bounded synthetic package composition; NOT native/SQL/full comment acceptance.
#[path = "review_table_create_context.rs"]
mod previous;
use hwpx_package::{
    BoundedZipReader, PackageLimits, PreservingXmlDocument, TableCreateHwpxLimits, TextFlow,
    TextFlowLimits, TextFlowReader, TextFlowWriter, WriterLimitConfig, WriterLimits,
    document_import::structure::review::{
        ImportedDocumentReviewBodies,
        table_create_context::{
            ReviewTableTemplate,
            filled_output::{ReviewFilledTableError, ReviewNewTableCell, ReviewNewTableCells},
            output::ReviewTableDimensions,
        },
    },
};
use sha2::{Digest as _, Sha256};
use std::{
    collections::BTreeMap,
    error::Error,
    io::{Cursor, Write},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
type TestResult<T = ()> = Result<T, Box<dyn Error>>;
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
fn flow(id: u32) -> TestResult<TextFlow> {
    Ok(TextFlowReader::read(format!("<hp:p xmlns:hp='{HP}' id='{id}' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>PRIVATE-TEXT &amp; 한글<hp:tab width='8000' leader='0' type='0'/><hp:lineBreak/>끝</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>SECOND RUN</hp:t></hp:run></hp:p>").as_bytes(), TextFlowLimits::default())?)
}
fn cell(row: u32, column: u32, ids: &[u32]) -> TestResult<ReviewNewTableCell> {
    Ok(ReviewNewTableCell {
        row,
        column,
        paragraphs: ids.iter().map(|id| flow(*id)).collect::<TestResult<_>>()?,
    })
}
fn dims() -> TestResult<ReviewTableDimensions> {
    Ok(ReviewTableDimensions::new(
        vec![400, 800],
        vec![500, 900, 600],
    )?)
}
fn parts(bytes: &[u8]) -> TestResult<BTreeMap<String, Vec<u8>>> {
    let mut zip = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    zip.entries()
        .to_vec()
        .into_iter()
        .map(|e| Ok((e.path.as_str().to_owned(), zip.read_entry(e.index)?)))
        .collect()
}
fn package(parts: &BTreeMap<String, Vec<u8>>) -> TestResult<Vec<u8>> {
    let mut zip = ZipWriter::new(Cursor::new(Vec::new()));
    let options = SimpleFileOptions::default().compression_method(CompressionMethod::Stored);
    zip.start_file("mimetype", options)?;
    zip.write_all(parts.get("mimetype").ok_or("mimetype")?)?;
    for (path, bytes) in parts {
        if path != "mimetype" {
            zip.start_file(path, options)?;
            zip.write_all(bytes)?;
        }
    }
    Ok(zip.finish()?.into_inner())
}
fn attr<'a>(e: &'a hwpx_package::XmlElementToken, local: &str) -> Option<&'a str> {
    e.attributes()
        .iter()
        .find(|a| a.name().namespace().is_none() && a.name().local_name() == local)
        .map(hwpx_package::XmlAttributeToken::semantic_value)
}
fn named(e: &hwpx_package::XmlElementToken, local: &str) -> bool {
    e.name().namespace() == Some(HP) && e.name().local_name() == local
}
// Fixture-only numeric locating. Production never receives a caller-selected native ID.
fn contents(
    xml: &PreservingXmlDocument,
) -> TestResult<BTreeMap<(u32, u32), hwpx_package::XmlSpan>> {
    let (table, _) = xml
        .elements()
        .iter()
        .enumerate()
        .find(|(_, e)| named(e, "tbl") && attr(e, "id") == Some("700"))
        .ok_or("new table")?;
    let mut result = BTreeMap::new();
    for (i, c) in xml.elements().iter().enumerate().filter(|(_, e)| {
        named(e, "tc") && e.parent().and_then(|r| xml.elements()[r].parent()) == Some(table)
    }) {
        let addr = xml
            .elements()
            .iter()
            .find(|a| a.parent() == Some(i) && named(a, "cellAddr"))
            .ok_or("address")?;
        let body = xml
            .elements()
            .iter()
            .find(|a| a.parent() == Some(i) && named(a, "subList"))
            .ok_or("body")?;
        assert!(
            result
                .insert(
                    (
                        attr(addr, "rowAddr").ok_or("row")?.parse()?,
                        attr(addr, "colAddr").ok_or("column")?.parse()?
                    ),
                    body.content_span().ok_or("span")?
                )
                .is_none()
        );
        let _ = c;
    }
    Ok(result)
}
fn lower_root(p: &TextFlow) -> TestResult<Vec<u8>> {
    let raw = TextFlowWriter::lower(p, TextFlowLimits::default())?;
    let xml = PreservingXmlDocument::parse(&raw)?;
    let span = xml.elements()[xml.root_element()]
        .outer_span()
        .ok_or("root")?;
    Ok(raw[span.start()..span.end()].to_vec())
}
#[test]
fn memo_hidden_fill_multiple_paragraphs_exact_other_cells_geometry_parts_and_receipt() -> TestResult
{
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "filled-source")?;
    let template = previous::forms(&tbytes, "filled-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
    for (ordinal, id) in [(0, "101"), (1, "102")] {
        let paragraph = previous::anchor(&source, &bytes, "p", id)?;
        let ctx = review.prepare_table_creation(
            &bytes,
            &review.observations()[ordinal].marker_anchor,
            &paragraph,
            ReviewTableTemplate {
                forms: &template,
                fresh: &tbytes,
                table: &table,
            },
            TableCreateHwpxLimits::default(),
        )?;
        let requests = vec![cell(0, 0, &[801, 802])?, cell(1, 2, &[803])?];
        let cells = ReviewNewTableCells::new(vec![cell(0, 0, &[801, 802])?, cell(1, 2, &[803])?])?;
        let blank = ctx.lower_table(&bytes, &tbytes, &dims()?, WriterLimits::default())?;
        let mut expected = parts(&blank.with_verified_bytes(<[u8]>::to_vec)?)?;
        let section = expected.get_mut("Contents/section0.xml").ok_or("section")?;
        let spans = contents(&PreservingXmlDocument::parse(section)?)?;
        assert_eq!(spans.len(), 6);
        let mut changes = requests
            .iter()
            .map(|c| {
                let span = spans.get(&(c.row, c.column)).ok_or("cell")?;
                let mut value = Vec::new();
                for p in &c.paragraphs {
                    value.extend(lower_root(p)?);
                }
                Ok((*span, value))
            })
            .collect::<TestResult<Vec<_>>>()?;
        changes.sort_by_key(|(span, _)| std::cmp::Reverse(span.start()));
        for (span, replacement) in changes {
            section.splice(span.start()..span.end(), replacement);
        }
        let output =
            ctx.lower_table_with_cells(&bytes, &tbytes, &dims()?, &cells, WriterLimits::default())?;
        let actual = output.with_verified_bytes(<[u8]>::to_vec)?;
        assert_eq!(parts(&actual)?, expected);
        let receipt = output.receipt();
        assert_eq!(receipt.blank_creation, *blank.receipt());
        assert_eq!(
            receipt.final_package_sha256,
            <[u8; 32]>::from(Sha256::digest(&actual))
        );
        assert_ne!(
            receipt.final_package_sha256,
            receipt.blank_creation.output_package_sha256
        );
        assert_eq!(
            (
                receipt.populated_cells,
                receipt.populated_paragraphs,
                receipt.final_bytes
            ),
            (2, 3, actual.len())
        );
        assert!(receipt.geometry_and_unselected_content_exact);
        assert!(!receipt.full_document_flow_bound && !receipt.full_comment_product_acceptance);
        assert!(!format!("{output:?}{cells:?}{receipt:?}").contains("PRIVATE-TEXT"));
        let after_forms = previous::forms(&actual, "filled-source")?;
        let after = ImportedDocumentReviewBodies::import(&after_forms)?;
        assert_eq!(after.observations().len(), review.observations().len());
        assert_eq!(
            after.observations()[ordinal].native_attributes,
            review.observations()[ordinal].native_attributes
        );
        assert!(after_forms.source().resolve_anchor(&paragraph).is_err());
        ctx.verify_source(&bytes, &tbytes)?;
    }
    Ok(())
}
#[test]
fn canonical_edit_order_repeat_all_cells_and_single_cell_boundary() -> TestResult {
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "order-source")?;
    let template = previous::forms(&tbytes, "order-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
    let p = previous::anchor(&source, &bytes, "p", "101")?;
    let ctx = review.prepare_table_creation(
        &bytes,
        &review.observations()[0].marker_anchor,
        &p,
        ReviewTableTemplate {
            forms: &template,
            fresh: &tbytes,
            table: &table,
        },
        TableCreateHwpxLimits::default(),
    )?;
    let make = || {
        (0..2)
            .flat_map(|r| (0..3).map(move |c| (r, c)))
            .map(|(r, c)| cell(r, c, &[810 + r * 3 + c]))
            .collect::<TestResult<Vec<_>>>()
    };
    let forward = ReviewNewTableCells::new(make()?)?;
    let mut reverse = make()?;
    reverse.reverse();
    let reverse = ReviewNewTableCells::new(reverse)?;
    let one =
        ctx.lower_table_with_cells(&bytes, &tbytes, &dims()?, &forward, WriterLimits::default())?;
    let two =
        ctx.lower_table_with_cells(&bytes, &tbytes, &dims()?, &reverse, WriterLimits::default())?;
    assert_eq!(one.receipt(), two.receipt());
    assert_eq!(
        one.with_verified_bytes(<[u8]>::to_vec)?,
        two.with_verified_bytes(<[u8]>::to_vec)?
    );
    assert_eq!(one.receipt().populated_cells, 6);
    let single = ctx.lower_table_with_cells(
        &bytes,
        &tbytes,
        &ReviewTableDimensions::new(vec![300], vec![500])?,
        &ReviewNewTableCells::new(vec![cell(0, 0, &[850])?])?,
        WriterLimits::default(),
    )?;
    assert_eq!(
        (
            single.receipt().blank_creation.created_cells,
            single.receipt().populated_cells
        ),
        (1, 1)
    );
    Ok(())
}
#[test]
fn bounded_constructor_rejects_empty_duplicate_cell_and_aggregate_limits() -> TestResult {
    assert!(matches!(
        ReviewNewTableCells::new(vec![]),
        Err(ReviewFilledTableError::Values)
    ));
    assert!(ReviewNewTableCells::new(vec![cell(0, 0, &[])?]).is_err());
    assert!(ReviewNewTableCells::new(vec![cell(0, 0, &[801])?, cell(0, 0, &[802])?]).is_err());
    assert!(
        ReviewNewTableCells::new(
            (0..129)
                .map(|r| cell(r, 0, &[801]))
                .collect::<TestResult<_>>()?
        )
        .is_err()
    );
    assert!(
        ReviewNewTableCells::new(vec![ReviewNewTableCell {
            row: 0,
            column: 0,
            paragraphs: vec![flow(801)?; 513]
        }])
        .is_err()
    );
    let large = TextFlowReader::read(
        format!(
            "<hp:p xmlns:hp='{HP}' id='801'><hp:run><hp:t>{}</hp:t></hp:run></hp:p>",
            "a".repeat(1_000_000)
        )
        .as_bytes(),
        TextFlowLimits::default(),
    )?;
    assert!(
        ReviewNewTableCells::new(vec![ReviewNewTableCell {
            row: 0,
            column: 0,
            paragraphs: vec![large; 9]
        }])
        .is_err()
    );
    Ok(())
}
#[test]
fn actual_geometry_rejects_out_of_bounds_and_overflow_coordinates() -> TestResult {
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "bounds-source")?;
    let template = previous::forms(&tbytes, "bounds-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
    let p = previous::anchor(&source, &bytes, "p", "101")?;
    let ctx = review.prepare_table_creation(
        &bytes,
        &review.observations()[0].marker_anchor,
        &p,
        ReviewTableTemplate {
            forms: &template,
            fresh: &tbytes,
            table: &table,
        },
        TableCreateHwpxLimits::default(),
    )?;
    for (r, c) in [(2, 0), (0, 3), (u32::MAX, 0), (0, u32::MAX)] {
        assert!(matches!(
            ctx.lower_table_with_cells(
                &bytes,
                &tbytes,
                &dims()?,
                &ReviewNewTableCells::new(vec![cell(r, c, &[801])?])?,
                WriterLimits::default()
            ),
            Err(ReviewFilledTableError::Values)
        ));
    }
    Ok(())
}
#[test]
fn fresh_source_and_template_whole_bytes_remain_required() -> TestResult {
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "fresh-source")?;
    let template = previous::forms(&tbytes, "fresh-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
    let p = previous::anchor(&source, &bytes, "p", "101")?;
    let ctx = review.prepare_table_creation(
        &bytes,
        &review.observations()[0].marker_anchor,
        &p,
        ReviewTableTemplate {
            forms: &template,
            fresh: &tbytes,
            table: &table,
        },
        TableCreateHwpxLimits::default(),
    )?;
    let cells = ReviewNewTableCells::new(vec![cell(0, 0, &[801])?])?;
    let mut changed = bytes.clone();
    changed.push(0);
    let mut changed_template = tbytes.clone();
    changed_template.push(0);
    for (s, t) in [(&changed, &tbytes), (&bytes, &changed_template)] {
        assert!(matches!(
            ctx.lower_table_with_cells(s, t, &dims()?, &cells, WriterLimits::default()),
            Err(ReviewFilledTableError::Creation(_))
        ));
    }
    Ok(())
}
#[test]
fn unsafe_opaque_field_dangling_styles_and_original_writer_limits_reject() -> TestResult {
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "unsafe-source")?;
    let template = previous::forms(&tbytes, "unsafe-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
    let p = previous::anchor(&source, &bytes, "p", "101")?;
    let ctx = review.prepare_table_creation(
        &bytes,
        &review.observations()[0].marker_anchor,
        &p,
        ReviewTableTemplate {
            forms: &template,
            fresh: &tbytes,
            table: &table,
        },
        TableCreateHwpxLimits::default(),
    )?;
    let opaque = TextFlowReader::read(format!("<hp:p xmlns:hp='{HP}' xmlns:u='urn:future' id='801'><hp:run><hp:t>TEXT</hp:t></hp:run><u:opaque/></hp:p>").as_bytes(),TextFlowLimits::default())?;
    let field = TextFlowReader::read(format!("<hp:p xmlns:hp='{HP}' id='801'><hp:run><hp:ctrl><hp:fieldBegin id='19' type='DATE'/></hp:ctrl><hp:ctrl><hp:fieldEnd beginIDRef='19'/></hp:ctrl></hp:run></hp:p>").as_bytes(),TextFlowLimits::default())?;
    let mut bad_style = flow(801)?;
    bad_style.paragraph.style_id_ref = Some(999_999);
    for paragraph in [opaque, field, bad_style] {
        let request = ReviewNewTableCells::new(vec![ReviewNewTableCell {
            row: 0,
            column: 0,
            paragraphs: vec![paragraph],
        }]);
        if let Ok(cells) = request {
            assert!(
                ctx.lower_table_with_cells(
                    &bytes,
                    &tbytes,
                    &dims()?,
                    &cells,
                    WriterLimits::default()
                )
                .is_err()
            );
        }
    }
    let tiny = WriterLimits::new(WriterLimitConfig {
        max_output_bytes: 1,
    })?;
    assert!(
        ctx.lower_table_with_cells(
            &bytes,
            &tbytes,
            &dims()?,
            &ReviewNewTableCells::new(vec![cell(0, 0, &[801])?])?,
            tiny
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn original_package_id_guard_rejects_existing_and_cross_cell_duplicates() -> TestResult {
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "id-source")?;
    let template = previous::forms(&tbytes, "id-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
    let p = previous::anchor(&source, &bytes, "p", "101")?;
    let ctx = review.prepare_table_creation(
        &bytes,
        &review.observations()[0].marker_anchor,
        &p,
        ReviewTableTemplate {
            forms: &template,
            fresh: &tbytes,
            table: &table,
        },
        TableCreateHwpxLimits::default(),
    )?;
    for requests in [
        vec![cell(0, 0, &[10])?],
        vec![cell(0, 0, &[801])?, cell(1, 2, &[801])?],
        vec![cell(0, 0, &[801, 801])?],
    ] {
        assert!(
            ctx.lower_table_with_cells(
                &bytes,
                &tbytes,
                &dims()?,
                &ReviewNewTableCells::new(requests)?,
                WriterLimits::default()
            )
            .is_err()
        );
    }
    Ok(())
}
#[test]
fn nested_new_table_fills_only_new_cell_and_retains_outer_protection_rejection() -> TestResult {
    let tbytes = previous::template(false)?;
    let template = previous::forms(&tbytes, "nested-template")?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
    let original = previous::source()?;
    let outer = String::from_utf8(
        parts(&tbytes)?
            .remove("Contents/section0.xml")
            .ok_or("section")?,
    )?;
    let inner = outer
        .split_once('>')
        .ok_or("root")?
        .1
        .rsplit_once("</hs:sec>")
        .ok_or("end")?
        .0
        .replace("id=\"700\"", "id=\"701\"");
    for locked in [false, true] {
        let mut source_parts = parts(&original)?;
        let section = String::from_utf8(
            source_parts
                .remove("Contents/section0.xml")
                .ok_or("section")?,
        )?;
        let wrapper = if locked {
            inner.replacen("lock=\"0\"", "lock=\"1\"", 1)
        } else {
            inner.clone()
        };
        source_parts.insert(
            "Contents/section0.xml".to_owned(),
            section
                .replacen(
                    "</hp:subList></hp:fieldBegin>",
                    &format!("{wrapper}</hp:subList></hp:fieldBegin>"),
                    1,
                )
                .into_bytes(),
        );
        let bytes = package(&source_parts)?;
        let source = previous::forms(&bytes, "nested-source")?;
        let review = ImportedDocumentReviewBodies::import(&source)?;
        let p = previous::anchor(&source, &bytes, "p", "0")?;
        let result = review.prepare_table_creation(
            &bytes,
            &review.observations()[0].marker_anchor,
            &p,
            ReviewTableTemplate {
                forms: &template,
                fresh: &tbytes,
                table: &table,
            },
            TableCreateHwpxLimits::default(),
        );
        if locked {
            assert!(result.is_err());
            continue;
        }
        let ctx = result?;
        let blank = ctx
            .lower_table(&bytes, &tbytes, &dims()?, WriterLimits::default())?
            .with_verified_bytes(<[u8]>::to_vec)?;
        let filled = ctx
            .lower_table_with_cells(
                &bytes,
                &tbytes,
                &dims()?,
                &ReviewNewTableCells::new(vec![cell(1, 2, &[801])?])?,
                WriterLimits::default(),
            )?
            .with_verified_bytes(<[u8]>::to_vec)?;
        let mut expected = parts(&blank)?;
        let section = expected.get_mut("Contents/section0.xml").ok_or("section")?;
        let span = contents(&PreservingXmlDocument::parse(section)?)?
            .remove(&(1, 2))
            .ok_or("cell")?;
        section.splice(span.start()..span.end(), lower_root(&flow(801)?)?);
        assert_eq!(parts(&filled)?, expected);
        let after = previous::forms(&filled, "nested-source")?;
        ImportedDocumentReviewBodies::import(&after)?.verify_source(&filled)?;
    }
    Ok(())
}
