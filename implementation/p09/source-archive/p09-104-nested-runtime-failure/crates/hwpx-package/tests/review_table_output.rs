//! Actual package output over bounded synthetic native templates. No Hangul/SQL acceptance.
#[path = "review_table_create_context.rs"]
mod previous;
use domain_ir::Node;
use hwpx_package::{
    BoundedZipReader, PackageLimits, TableCreateHwpxLimits, WriterLimits,
    document_import::structure::review::{
        ImportedDocumentReviewBodies,
        table_create_context::{
            ReviewTableTemplate,
            output::{ReviewTableDimensions, ReviewTableOutputAuthority, ReviewTableOutputError},
        },
    },
};
use std::{
    collections::BTreeMap,
    error::Error,
    io::{Cursor, Write},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
type TestResult<T = ()> = Result<T, Box<dyn Error>>;
fn parts(bytes: &[u8]) -> TestResult<BTreeMap<String, Vec<u8>>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    entries
        .into_iter()
        .map(|e| Ok((e.path.as_str().to_owned(), reader.read_entry(e.index)?)))
        .collect()
}
fn package(parts: &BTreeMap<String, Vec<u8>>) -> TestResult<Vec<u8>> {
    let mut zip = ZipWriter::new(Cursor::new(Vec::new()));
    zip.start_file(
        "mimetype",
        SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
    )?;
    zip.write_all(parts.get("mimetype").ok_or("mimetype")?)?;
    for (path, bytes) in parts {
        if path == "mimetype" {
            continue;
        }
        zip.start_file(
            path,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        zip.write_all(bytes)?;
    }
    Ok(zip.finish()?.into_inner())
}
fn rows() -> TestResult<ReviewTableDimensions> {
    Ok(ReviewTableDimensions::new(
        vec![400, 800],
        vec![500, 900, 600],
    )?)
}
#[test]
fn actual_memo_and_hidden_table_outputs_reopen_with_exact_tracks_and_all_other_parts() -> TestResult
{
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "table-output-source")?;
    let template = previous::forms(&tbytes, "table-output-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
    for (observation, id) in [(0, "101"), (1, "102")] {
        let paragraph = previous::anchor(&source, &bytes, "p", id)?;
        let context = review.prepare_table_creation(
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
        let output = context.lower_table(&bytes, &tbytes, &rows()?, WriterLimits::default())?;
        let actual = output.with_verified_bytes(<[u8]>::to_vec)?;
        let repeated = context
            .lower_table(&bytes, &tbytes, &rows()?, WriterLimits::default())?
            .with_verified_bytes(<[u8]>::to_vec)?;
        assert_eq!(actual, repeated);
        let old_parts = parts(&bytes)?;
        let after_parts = parts(&actual)?;
        assert_eq!(old_parts.len(), after_parts.len());
        for (p, old) in &old_parts {
            if p != "Contents/header.xml" && p != "Contents/section0.xml" {
                assert_eq!(after_parts.get(p), Some(old));
            }
        }
        let resolved = source.source().resolve_anchor(&paragraph)?;
        let old = resolved
            .element()
            .ok_or("paragraph")?
            .outer_span()
            .ok_or("span")?;
        let new_forms = previous::forms(&actual, "table-output-source")?;
        let new_review = ImportedDocumentReviewBodies::import(&new_forms)?;
        assert_eq!(new_review.observations().len(), review.observations().len());
        assert_eq!(
            new_review.observations()[observation].native_attributes,
            review.observations()[observation].native_attributes
        );
        let mut native_tables = Vec::new();
        for node in &new_review.observations()[observation]
            .body
            .as_ref()
            .ok_or("body")?
            .children
        {
            if let Node::Table(t) = node {
                native_tables.push(t);
            }
        }
        assert_eq!(native_tables.len(), 1);
        let created = native_tables[0];
        assert_eq!(
            (created.rows, created.columns, created.cells.len()),
            (2, 3, 6)
        );
        assert!(
            created
                .cells
                .iter()
                .all(|c| c.row_span == 1 && c.column_span == 1)
        );
        assert_outside(&new_forms, created, old, &old_parts, &after_parts)?;
        let receipt = output.receipt();
        assert_eq!(
            (
                receipt.target_rows,
                receipt.target_columns,
                receipt.created_cells
            ),
            (2, 3, 6)
        );
        assert_eq!(
            (
                receipt.before_table_count_in_selected_part,
                receipt.after_table_count_in_selected_part
            ),
            (0, 1)
        );
        assert!(receipt.new_table_inserted);
        assert!(!receipt.full_document_flow_bound);
        assert!(!receipt.full_comment_product_acceptance);
        assert_eq!(
            receipt.authority,
            ReviewTableOutputAuthority::SourceArtifactIntegrityOnly
        );
        assert!(!format!("{output:?}").contains("PRIVATE"));
        assert!(context.verify_source(&actual, &tbytes).is_err());
    }
    Ok(())
}
#[test]
fn one_by_one_boundary_and_requested_tracks_change_only_native_candidate_not_source() -> TestResult
{
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "boundary-output")?;
    let template = previous::forms(&tbytes, "boundary-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let paragraph = previous::anchor(&source, &bytes, "p", "101")?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
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
    let one = context.lower_table(
        &bytes,
        &tbytes,
        &ReviewTableDimensions::new(vec![1000], vec![2300])?,
        WriterLimits::default(),
    )?;
    assert_eq!(
        (
            one.receipt().target_rows,
            one.receipt().target_columns,
            one.receipt().created_cells
        ),
        (1, 1, 1)
    );
    let six = context.lower_table(&bytes, &tbytes, &rows()?, WriterLimits::default())?;
    assert_ne!(
        one.receipt().output_package_sha256,
        six.receipt().output_package_sha256
    );
    source.source().verify_source(&bytes)?;
    template.source().verify_source(&tbytes)?;
    Ok(())
}
#[test]
fn geometry_source_template_and_writer_bounds_fail_without_partial_output() -> TestResult {
    for (r, c) in [
        (vec![], vec![500]),
        (vec![0], vec![500]),
        (vec![1], vec![]),
        (vec![u32::MAX, 1], vec![500]),
        (vec![1], vec![0]),
        (vec![1; 10001], vec![1]),
    ] {
        assert!(ReviewTableDimensions::new(r, c).is_err());
    }
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let source = previous::forms(&bytes, "bounded-output")?;
    let template = previous::forms(&tbytes, "bounded-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let paragraph = previous::anchor(&source, &bytes, "p", "101")?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
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
    let mut stale = bytes.clone();
    stale.push(0);
    assert!(matches!(
        context.lower_table(&stale, &tbytes, &rows()?, WriterLimits::default()),
        Err(ReviewTableOutputError::Context(_))
    ));
    let mut stale_template = tbytes.clone();
    stale_template.push(0);
    assert!(matches!(
        context.lower_table(&bytes, &stale_template, &rows()?, WriterLimits::default()),
        Err(ReviewTableOutputError::Context(_))
    ));
    assert!(
        context
            .lower_table(
                &bytes,
                &tbytes,
                &ReviewTableDimensions::new(vec![u32::MAX], vec![1])?,
                WriterLimits::default()
            )
            .is_err()
    );
    let config = hwpx_package::WriterLimitConfig {
        max_output_bytes: 1,
    };
    assert!(
        context
            .lower_table(&bytes, &tbytes, &rows()?, WriterLimits::new(config)?)
            .is_err()
    );
    Ok(())
}
#[test]
fn same_native_identity_in_another_source_section_cannot_be_inserted() -> TestResult {
    let bytes = previous::source()?;
    let tbytes = previous::template(false)?;
    let mut expanded = parts(&bytes)?;
    expanded.insert(
        "Contents/section1.xml".into(),
        parts(&tbytes)?
            .remove("Contents/section0.xml")
            .ok_or("template section")?,
    );
    let opf = String::from_utf8(expanded.remove("Contents/content.hpf").ok_or("opf")?)?
        .replace("</opf:manifest>", "<opf:item id='extra' href='section1.xml' media-type='application/xml'/></opf:manifest>")
        .replace("</opf:spine>", "<opf:itemref idref='extra'/></opf:spine>");
    // The original native builder uses an opf prefix; assert this derivative actually adds a spine part.
    assert!(opf.contains("id='extra'"));
    expanded.insert("Contents/content.hpf".into(), opf.into_bytes());
    let bytes = package(&expanded)?;
    let source = previous::forms(&bytes, "cross-section-output")?;
    let template = previous::forms(&tbytes, "cross-section-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let paragraph = previous::anchor(&source, &bytes, "p", "101")?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
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
    assert!(matches!(
        context.lower_table(&bytes, &tbytes, &rows()?, WriterLimits::default()),
        Err(ReviewTableOutputError::NativeIdentityCollision)
    ));
    Ok(())
}

fn assert_outside(
    new_forms: &hwpx_package::document_import::forms::ImportedDocumentForms,
    created: &domain_ir::TableNode,
    old: hwpx_package::XmlByteSpan,
    old_parts: &BTreeMap<String, Vec<u8>>,
    after_parts: &BTreeMap<String, Vec<u8>>,
) -> TestResult {
    let selected = new_forms.source().resolve_anchor(
        created
            .common
            .source_anchor
            .as_ref()
            .ok_or("table anchor")?,
    )?;
    let xml = selected.part().xml().ok_or("xml")?;
    let table_index = selected.element_index().ok_or("table index")?;
    let run = xml.elements()[table_index].parent().ok_or("run")?;
    let new = xml.elements()[xml.elements()[run].parent().ok_or("p")?]
        .outer_span()
        .ok_or("new span")?;
    let before = old_parts
        .get("Contents/section0.xml")
        .ok_or("before section")?;
    let after = after_parts
        .get("Contents/section0.xml")
        .ok_or("after section")?;
    assert_eq!(before[..old.start()], after[..new.start()]);
    assert_eq!(before[old.end()..], after[new.end()..]);
    Ok(())
}

#[test]
fn table_inserted_in_existing_review_cell_preserves_outer_table_and_every_other_cell() -> TestResult
{
    let tbytes = previous::template(false)?;
    let original = previous::source()?;
    let bytes = nested_package(&original, &tbytes)?;
    let source = previous::forms(&bytes, "nested-table-output")?;
    let template = previous::forms(&tbytes, "nested-table-template")?;
    let review = ImportedDocumentReviewBodies::import(&source)?;
    let paragraph = previous::anchor(&source, &bytes, "p", "0")?;
    let table = previous::anchor(&template, &tbytes, "tbl", "700")?;
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
    let result = context.lower_table(
        &bytes,
        &tbytes,
        &ReviewTableDimensions::new(vec![100, 150], vec![150, 250])?,
        WriterLimits::default(),
    )?;
    let output = result.with_verified_bytes(<[u8]>::to_vec)?;
    assert_eq!(
        (
            result.receipt().before_table_count_in_selected_part,
            result.receipt().after_table_count_in_selected_part
        ),
        (1, 2)
    );
    let after_forms = previous::forms(&output, "nested-table-output")?;
    let after = ImportedDocumentReviewBodies::import(&after_forms)?;
    let old = source
        .source()
        .resolve_anchor(&paragraph)?
        .element()
        .ok_or("old p")?
        .outer_span()
        .ok_or("span")?;
    let outer = after.observations()[0]
        .body
        .as_ref()
        .ok_or("body")?
        .children
        .iter()
        .find_map(|n| {
            if let Node::Table(t) = n {
                Some(t)
            } else {
                None
            }
        })
        .ok_or("outer table")?;
    assert_eq!((outer.rows, outer.columns, outer.cells.len()), (2, 2, 4));
    let created = outer.cells[0]
        .body
        .children
        .iter()
        .find_map(|n| {
            if let Node::Table(t) = n {
                Some(t)
            } else {
                None
            }
        })
        .ok_or("created nested table")?;
    assert_eq!(
        (created.rows, created.columns, created.cells.len()),
        (2, 2, 4)
    );
    assert_outside(
        &after_forms,
        created,
        old,
        &parts(&bytes)?,
        &parts(&output)?,
    )?;
    assert!(!result.receipt().full_comment_product_acceptance);
    Ok(())
}

fn nested_package(original: &[u8], tbytes: &[u8]) -> TestResult<Vec<u8>> {
    let mut expanded = parts(original)?;
    let template_section = String::from_utf8(
        parts(tbytes)?
            .remove("Contents/section0.xml")
            .ok_or("template section")?,
    )?;
    let wrapper = template_section
        .split_once('>')
        .ok_or("root")?
        .1
        .rsplit_once("</hs:sec>")
        .ok_or("end")?
        .0
        .replace("id=\"700\"", "id=\"701\"");
    let section = String::from_utf8(expanded.remove("Contents/section0.xml").ok_or("section")?)?
        .replace(
            "</hp:subList></hp:fieldBegin>",
            &format!("{wrapper}</hp:subList></hp:fieldBegin>"),
        );
    expanded.insert("Contents/section0.xml".into(), section.into_bytes());
    package(&expanded)
}
