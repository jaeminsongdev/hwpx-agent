//! Synthetic native-format style output through original catalog/patch/writer, NOT native meaning.
use domain_ir::{CommentLineType, CommentLineWidth, CommentMemoType, DocumentId};
use hwpx_package::{
    BoundedZipReader, IdIndex, IdIndexLimits, IdKind, IdRuleProfile, PackageGraph,
    PackageGraphLimits, PackageLimits, PreservingXmlDocument, WriterLimitConfig, WriterLimits,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        fields::{
            ImportedDocumentFields,
            semantics::{
                ImportedDocumentFieldSemantics,
                catalog::{
                    ImportedCatalogKind, ImportedDocumentCatalog,
                    memo_style::{MemoStyleColor, MemoStyleLoweringError, MemoStyleValues},
                },
            },
        },
        forms::ImportedDocumentForms,
    },
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, io::Cursor};
#[path = "support/document_import_memo_catalog_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;
fn values() -> MemoStyleValues {
    MemoStyleValues {
        width_native_units: 77,
        line_width: CommentLineWidth::Mm0_3,
        line_type: CommentLineType::Wave,
        line_color: MemoStyleColor::Rgb(0xAABBCC),
        fill_color: MemoStyleColor::None,
        active_color: MemoStyleColor::Rgb(0x112233),
        memo_type: CommentMemoType::UserUpdate,
    }
}
fn with_catalog(
    bytes: &[u8],
    action: impl FnOnce(&ImportedDocumentCatalog<'_, '_, '_>) -> TestResult,
) -> TestResult {
    let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(
        bytes,
        DocumentId::parse("memo-style")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    action(&catalog)
}
fn parts(bytes: &[u8]) -> Result<Vec<(String, Vec<u8>)>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let names: Vec<_> = reader
        .entries()
        .iter()
        .map(|e| e.path.as_str().to_owned())
        .collect();
    names
        .into_iter()
        .enumerate()
        .map(|(i, name)| Ok((name, reader.read_entry(i)?)))
        .collect()
}
fn index(bytes: &[u8]) -> Result<IdIndex, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok(IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )?)
}
#[test]
fn original_writer_reopens_surgical_seven_attribute_output_and_all_other_bytes_stay_exact()
-> TestResult {
    let bytes = fixture::package(
        &fixture::table(&format!("{}{}", fixture::style(12), fixture::style(13)), 2),
        Some("12"),
    )?;
    with_catalog(&bytes, |catalog| {
        let selected = catalog
            .definitions()
            .iter()
            .find(|d| d.kind == ImportedCatalogKind::MemoProperty && d.native_id == 12)
            .ok_or("style")?;
        let output = catalog.lower_memo_style(
            &bytes,
            &selected.source_anchor,
            &values(),
            WriterLimits::default(),
        )?;
        assert_eq!(output.receipt().changed_attributes, 7);
        assert_eq!(output.receipt().changed_parts, 1);
        assert!(output.receipt().unrelated_expanded_parts_exact);
        assert!(!output.receipt().native_author_time_state_binding_verified);
        assert!(!output.receipt().execution_publication_authority);
        let after = output.with_verified_bytes(<[u8]>::to_vec)?;
        let original_parts = parts(&bytes)?;
        let after_parts = parts(&after)?;
        assert_eq!(original_parts.len(), after_parts.len());
        for ((name, before), (other, next)) in original_parts.iter().zip(&after_parts) {
            assert_eq!(name, other);
            if name != "Contents/header.xml" {
                assert_eq!(before, next);
                continue;
            }
            let old_fragment = fixture::style(12);
            let new_fragment = old_fragment
                .replace("width='55'", "width='77'")
                .replace("lineWidth='1'", "lineWidth='5'")
                .replace("lineType='SOLID'", "lineType='WAVE'")
                .replace("lineColor='#010203'", "lineColor='#AABBCC'")
                .replace("fillColor='#CCFF99'", "fillColor='none'")
                .replace("activeColor='none'", "activeColor='#112233'")
                .replace("memoType='NOMAL'", "memoType='USER_UPDATE'");
            assert_eq!(
                std::str::from_utf8(next)?,
                std::str::from_utf8(before)?.replacen(&old_fragment, &new_fragment, 1)
            );
            assert!(std::str::from_utf8(next)?.contains("PRIVATE-MEMO-STYLE"));
        }
        assert_eq!(
            Sha256::digest(&after).as_slice(),
            output.receipt().output_package_sha256
        );
        assert!(
            index(&after)?
                .declarations()
                .iter()
                .any(|d| d.kind() == IdKind::MemoShape)
        );
        assert!(
            !format!("{output:?} {:?} {:?}", output.receipt(), values()).contains("PRIVATE-MEMO")
        );
        Ok(())
    })
}
#[test]
fn official_memoPr_declarations_resolve_without_disabling_duplicate_or_dangling_checks()
-> TestResult {
    let good = fixture::package(&fixture::table(&fixture::style(12), 1), Some("12"))?;
    let read = index(&good)?;
    assert_eq!(
        read.declarations()
            .iter()
            .filter(|d| d.kind() == IdKind::MemoShape)
            .count(),
        1
    );
    for (styles, count, reference) in [
        (fixture::style(12), 1, "99"),
        (
            format!("{}{}", fixture::style(12), fixture::style(12)),
            2,
            "12",
        ),
        ("<x:memoPr xmlns:x='urn:foreign' id='12'/>".into(), 1, "12"),
        (
            format!("{}<hh:memoShape id='12'/>", fixture::style(12)),
            2,
            "12",
        ),
    ] {
        assert!(
            index(&fixture::package(
                &fixture::table(&styles, count),
                Some(reference)
            )?)
            .is_err()
        );
    }
    let legacy = fixture::package(&fixture::table("<hh:memoShape id='12'/>", 1), Some("12"))?;
    assert!(
        index(&legacy).is_ok(),
        "existing legacy declaration support is retained"
    );
    Ok(())
}
#[test]
fn foreign_anchor_fresh_source_changes_noop_invalid_values_and_small_writer_limit_never_output()
-> TestResult {
    let bytes = fixture::package(&fixture::table(&fixture::style(12), 1), Some("12"))?;
    let changed = fixture::package(&fixture::table(&fixture::style(13), 1), Some("13"))?;
    with_catalog(&bytes, |catalog| {
        let selected = catalog
            .definitions()
            .iter()
            .find(|d| d.kind == ImportedCatalogKind::MemoProperty)
            .ok_or("style")?;
        assert!(
            catalog
                .lower_memo_style(
                    &changed,
                    &selected.source_anchor,
                    &values(),
                    WriterLimits::default()
                )
                .is_err()
        );
        let foreign = catalog
            .definitions()
            .iter()
            .find(|d| d.kind != ImportedCatalogKind::MemoProperty)
            .ok_or("non-memo")?;
        assert_eq!(
            catalog
                .lower_memo_style(
                    &bytes,
                    &foreign.source_anchor,
                    &values(),
                    WriterLimits::default()
                )
                .err(),
            Some(MemoStyleLoweringError::Selection)
        );
        let mut invalid = values();
        invalid.width_native_units = 0;
        assert_eq!(
            catalog
                .lower_memo_style(
                    &bytes,
                    &selected.source_anchor,
                    &invalid,
                    WriterLimits::default()
                )
                .err(),
            Some(MemoStyleLoweringError::Values)
        );
        invalid.width_native_units = 55;
        invalid.active_color = MemoStyleColor::Rgb(u32::MAX);
        assert_eq!(
            catalog
                .lower_memo_style(
                    &bytes,
                    &selected.source_anchor,
                    &invalid,
                    WriterLimits::default()
                )
                .err(),
            Some(MemoStyleLoweringError::Values)
        );
        let noop = MemoStyleValues {
            width_native_units: 55,
            line_width: CommentLineWidth::Mm0_12,
            line_type: CommentLineType::Solid,
            line_color: MemoStyleColor::Rgb(0x010203),
            fill_color: MemoStyleColor::Rgb(0xCCFF99),
            active_color: MemoStyleColor::None,
            memo_type: CommentMemoType::Normal,
        };
        assert_eq!(
            catalog
                .lower_memo_style(
                    &bytes,
                    &selected.source_anchor,
                    &noop,
                    WriterLimits::default()
                )
                .err(),
            Some(MemoStyleLoweringError::NoChange)
        );
        let small = WriterLimits::new(WriterLimitConfig {
            max_output_bytes: 1,
            ..Default::default()
        })?;
        assert!(
            catalog
                .lower_memo_style(&bytes, &selected.source_anchor, &values(), small)
                .is_err()
        );
        Ok(())
    })
}
#[test]
fn all_original_native_enum_values_reopen_through_original_catalog() -> TestResult {
    let bytes = fixture::package(&fixture::table(&fixture::style(12), 1), Some("12"))?;
    let widths = [
        CommentLineWidth::Mm0_1,
        CommentLineWidth::Mm0_12,
        CommentLineWidth::Mm0_15,
        CommentLineWidth::Mm0_2,
        CommentLineWidth::Mm0_25,
        CommentLineWidth::Mm0_3,
        CommentLineWidth::Mm0_4,
        CommentLineWidth::Mm0_5,
        CommentLineWidth::Mm0_6,
        CommentLineWidth::Mm0_7,
        CommentLineWidth::Mm1_0,
        CommentLineWidth::Mm1_5,
        CommentLineWidth::Mm2_0,
        CommentLineWidth::Mm3_0,
        CommentLineWidth::Mm4_0,
        CommentLineWidth::Mm5_0,
    ];
    let lines = [
        CommentLineType::None,
        CommentLineType::Solid,
        CommentLineType::Dot,
        CommentLineType::Dash,
        CommentLineType::DashDot,
        CommentLineType::DashDotDot,
        CommentLineType::LongDash,
        CommentLineType::Circle,
        CommentLineType::DoubleSlim,
        CommentLineType::SlimThick,
        CommentLineType::ThickSlim,
        CommentLineType::SlimThickSlim,
        CommentLineType::Wave,
        CommentLineType::DoubleWave,
        CommentLineType::Thick3d,
        CommentLineType::ThickReverse3d,
        CommentLineType::ThreeDimensional,
        CommentLineType::Reverse3d,
    ];
    with_catalog(&bytes, |catalog| {
        let selected = catalog
            .definitions()
            .iter()
            .find(|d| d.kind == ImportedCatalogKind::MemoProperty)
            .ok_or("style")?;
        for width in widths {
            let mut v = values();
            v.line_width = width;
            catalog.lower_memo_style(
                &bytes,
                &selected.source_anchor,
                &v,
                WriterLimits::default(),
            )?;
        }
        for line in lines {
            let mut v = values();
            v.line_type = line;
            catalog.lower_memo_style(
                &bytes,
                &selected.source_anchor,
                &v,
                WriterLimits::default(),
            )?;
        }
        for memo in [
            CommentMemoType::Normal,
            CommentMemoType::UserInsert,
            CommentMemoType::UserDelete,
            CommentMemoType::UserUpdate,
        ] {
            let mut v = values();
            v.memo_type = memo;
            catalog.lower_memo_style(
                &bytes,
                &selected.source_anchor,
                &v,
                WriterLimits::default(),
            )?;
        }
        Ok(())
    })
}
