use domain_ir::{ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    block_bookmarks::{BlockBookmarkImportError as E, ImportedBlockBookmarks},
    cached_source::FieldCacheSnapshot,
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, path::PathBuf};
#[path = "support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;

fn limits() -> ReferenceAuxiliaryLimits {
    ReferenceAuxiliaryLimits::default()
}
fn block(id: u32, name: &str, prop: &str, body: &str) -> String {
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='BOOKMARK' name='{name}' fieldid='777'><hp:parameters cnt='1' name=''><hp:integerParam name='Prop'>{prop}</hp:integerParam></hp:parameters></hp:fieldBegin></hp:ctrl>{body}<hp:ctrl><hp:fieldEnd beginIDRef='{id}' fieldid='777'/></hp:ctrl>"
    )
}
fn package(body: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    fixture::package(&format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>"))
}

#[test]
fn actual_native670_created_and_reopened_have_eight_source_bound_block_ranges() -> TestResult {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let targets = [
        "B643_ALPHA",
        "two words",
        "한글내용",
        "A&B<C>",
        "0123456789",
        "Mixed_한글_123",
        "RANGE",
        "끝",
    ];
    for (name, size, sha) in [
        (
            "created.hwpx",
            17331,
            "aa0ae8f3042a0b3be43733deb0196488bdd1bac14e6025f7785915cca5660076",
        ),
        (
            "reopened.hwpx",
            17269,
            "783ee3372fe44d8c9b6f6f6e65b5088226ea11ac920f97c76915b4c1181b6699",
        ),
    ] {
        let path = root
            .join(
                "implementation/p09/evidence/private/p09-361-block-bookmark670-source-document001",
            )
            .join(name);
        let meta = std::fs::symlink_metadata(&path)?;
        assert!(meta.is_file() && !meta.file_type().is_symlink());
        assert_eq!(meta.len(), size);
        let bytes = std::fs::read(path)?;
        assert_eq!(hex::encode(Sha256::digest(&bytes)), sha);
        let forms = fixture::forms(&bytes, "actual-block670")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
        assert_eq!(blocks.observations().len(), 8);
        assert_eq!(forms.body_structure().bookmarks().len(), 0);
        for (i, text) in targets.iter().enumerate() {
            let name = format!("p09_block643_{:02}", i + 1);
            let row = blocks.by_exact_source_name(&name)?;
            assert_ne!(row.begin_anchor(), row.end_anchor());
            let FieldCacheSnapshot::DecodedTextNotEvaluated {
                decoded_text_sha256,
                utf8_bytes,
                ..
            } = row.selected_source()
            else {
                return Err("plain block expected".into());
            };
            assert_eq!(
                *decoded_text_sha256,
                <[u8; 32]>::from(Sha256::digest(text.as_bytes()))
            );
            assert_eq!(*utf8_bytes, text.len());
        }
        assert_eq!(
            blocks.verify_source(&fields, &bytes, limits())?,
            *blocks.receipt()
        );
        assert!(
            !blocks
                .receipt()
                .native_or_cross_reference_execution_qualified
        );
    }
    Ok(())
}

#[test]
fn shared_fieldid_is_not_a_unique_identity_and_exact_names_remain_distinct() -> TestResult {
    let bytes =
        package(&(block(1, "a", "2", "<hp:t>A</hp:t>") + &block(2, "b", "2", "<hp:t>B</hp:t>")))?;
    let forms = fixture::forms(&bytes, "shared-fieldid")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
    assert_ne!(
        blocks.by_exact_source_name("a")?.field_reference_id(),
        blocks.by_exact_source_name("b")?.field_reference_id()
    );
    assert_eq!(blocks.by_exact_source_name("A").unwrap_err(), E::Missing);
    Ok(())
}

#[test]
fn duplicate_names_stay_ambiguous_without_selecting_first_or_last() -> TestResult {
    let bytes = package(
        &(block(1, "same", "2", "<hp:t>A</hp:t>") + &block(2, "same", "2", "<hp:t>B</hp:t>")),
    )?;
    let forms = fixture::forms(&bytes, "duplicates")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
    assert_eq!(blocks.observations().len(), 2);
    assert_eq!(
        blocks.by_exact_source_name("same").unwrap_err(),
        E::Ambiguous
    );
    Ok(())
}

#[test]
fn nonobserved_prop_profiles_are_rejected_without_point_fallback() -> TestResult {
    for prop in ["0", "1", "3", "", " 2 "] {
        let bytes = package(&block(1, "name", prop, "<hp:t>text</hp:t>"))?;
        let forms = fixture::forms(&bytes, "wrong-prop")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        assert_eq!(
            ImportedBlockBookmarks::import(&fields, limits()).unwrap_err(),
            E::Unsupported
        );
    }
    Ok(())
}

#[test]
fn malformed_or_missing_parameter_envelope_does_not_invent_a_block() -> TestResult {
    for raw in [block(1,"name","2","<hp:t>text</hp:t>").replace("cnt='1'","cnt='2'"),
        block(1,"name","2","<hp:t>text</hp:t>").replace("<hp:parameters cnt='1' name=''><hp:integerParam name='Prop'>2</hp:integerParam></hp:parameters>","")] {
        let bytes=package(&raw)?;let forms=fixture::forms(&bytes,"parameter-drift")?;
        match ImportedDocumentFields::import(&forms) {
            Err(_)=>{},Ok(fields)=>assert!(ImportedBlockBookmarks::import(&fields,limits()).is_err()),
        }
    }
    Ok(())
}

#[test]
fn point_bookmark_marker_is_not_promoted_to_a_block_target() -> TestResult {
    let bytes = package("<hp:ctrl><hp:bookmark name='point'/></hp:ctrl><hp:t>text</hp:t>")?;
    let forms = fixture::forms(&bytes, "point-family")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    assert_eq!(forms.body_structure().bookmarks().len(), 1);
    assert!(
        ImportedBlockBookmarks::import(&fields, limits())?
            .observations()
            .is_empty()
    );
    Ok(())
}

#[test]
fn wrong_end_id_rejects_at_the_original_field_importer() -> TestResult {
    let raw =
        block(1, "name", "2", "<hp:t>text</hp:t>").replace("beginIDRef='1'", "beginIDRef='777'");
    let bytes = package(&raw)?;
    match fixture::forms(&bytes, "bad-end") {
        Err(_) => {}
        Ok(forms) => assert!(ImportedDocumentFields::import(&forms).is_err()),
    }
    Ok(())
}

#[test]
fn structured_selected_content_is_retained_as_unqualified_not_plain_text() -> TestResult {
    let bytes = package(&block(1, "name", "2", "<hp:ctrl><hp:unknown/></hp:ctrl>"))?;
    let forms = fixture::forms(&bytes, "structured")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    assert_eq!(
        ImportedBlockBookmarks::import(&fields, limits()).unwrap_err(),
        E::Unsupported
    );
    Ok(())
}

#[test]
fn changed_bytes_or_foreign_field_model_cannot_reuse_the_import() -> TestResult {
    let bytes = package(&block(1, "name", "2", "<hp:t>text</hp:t>"))?;
    let forms = fixture::forms(&bytes, "fresh-boundary")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
    let changed = package(&block(1, "other", "2", "<hp:t>text</hp:t>"))?;
    assert_eq!(
        blocks
            .verify_source(&fields, &changed, limits())
            .unwrap_err(),
        E::Binding
    );
    let other_forms = fixture::forms(&changed, "foreign")?;
    let other = ImportedDocumentFields::import(&other_forms)?;
    assert_eq!(
        blocks
            .verify_source(&other, &changed, limits())
            .unwrap_err(),
        E::Binding
    );
    Ok(())
}

#[test]
fn diagnostics_redact_original_names_and_selected_text() -> TestResult {
    let bytes = package(&block(1, "PRIVATE_NAME", "2", "<hp:t>PRIVATE_TEXT</hp:t>"))?;
    let forms = fixture::forms(&bytes, "redaction")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
    let debug = format!(
        "{blocks:?} {:?} {:?}",
        blocks.observations(),
        blocks.receipt()
    );
    assert!(!debug.contains("PRIVATE_"));
    assert!(!serde_json::to_string(blocks.receipt())?.contains("PRIVATE_"));
    Ok(())
}

#[test]
fn finite_name_or_count_limits_reject_instead_of_clamping() -> TestResult {
    let bytes = package(
        &(block(1, "lengthy", "2", "<hp:t>A</hp:t>") + &block(2, "b", "2", "<hp:t>B</hp:t>")),
    )?;
    let forms = fixture::forms(&bytes, "budgets")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    for config in [
        ReferenceAuxiliaryLimitConfig {
            text_bytes: 3,
            ..Default::default()
        },
        ReferenceAuxiliaryLimitConfig {
            items_per_kind: 1,
            ..Default::default()
        },
    ] {
        assert_eq!(
            ImportedBlockBookmarks::import(&fields, ReferenceAuxiliaryLimits::new(config)?)
                .unwrap_err(),
            E::Limit
        );
    }
    Ok(())
}

