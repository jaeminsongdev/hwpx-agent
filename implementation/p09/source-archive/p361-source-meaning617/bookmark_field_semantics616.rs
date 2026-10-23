//! Source meaning integration, not Native display/evaluation/approval evidence.
use domain_ir::{DocumentId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation as Product,
    source::{ReferenceSourceError, ReferenceSourceStatus},
    source_field_semantics::ReferenceSourceMeaningKind,
};
use hwpx_package::document_import::{
    SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        bookmark_crossref::{BookmarkCrossReferenceDisplay as Display, SourceBookmarkResolution},
        semantics::{
            ImportedDocumentFieldSemantics, ImportedFieldMeaning,
            source_index::SourceFieldMeaningIndex,
        },
    },
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    fs::OpenOptions,
    io::Read,
    path::Path,
    time::{Duration, Instant},
};
#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type Result<T = ()> = std::result::Result<T, Box<dyn Error>>;
const DOCUMENT: &str = "p09-bookmark-semantics616";
const CORPUS: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
);
fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn field(id: u32, kind: &str, children: Option<&str>) -> String {
    let parameters = children
        .map(|v| format!("<hp:parameters cnt='1'>{v}</hp:parameters>"))
        .unwrap_or_default();
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='{kind}'>{parameters}</hp:fieldBegin></hp:ctrl><hp:t>untrusted cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>"
    )
}
fn command(value: &str) -> String {
    format!(
        "<hp:stringParam name='Command'>{}</hp:stringParam>",
        value.replace('&', "&amp;").replace('<', "&lt;")
    )
}
fn package(body: &str) -> Result<Vec<u8>> {
    base::package(&fixture::paragraph(body))
}
fn assess(bytes: &[u8]) -> Result<hwpx_agent_cli::reference_validation_product::source_field_semantics::ReferenceSourceFieldMeaningAssessment>{
    Ok(Product::assess_package_field_semantics(
        bytes,
        DocumentId::parse(DOCUMENT)?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
        limits()?,
    )?)
}
#[test]
fn all_eight_options_are_meanings_and_graph_properties_without_native_evaluation() -> Result {
    for display in 0..4 {
        for hyperlink in 0..2 {
            let bytes = package(&format!(
                "{}{}",
                fixture::marker("private-target"),
                field(
                    1,
                    "CROSSREF",
                    Some(&command(&format!(
                        "?private-target;6;{display};{hyperlink};0"
                    )))
                )
            ))?;
            let forms = base::forms(&bytes, DOCUMENT)?;
            let fields = ImportedDocumentFields::import(&forms)?;
            let original = fields.graph().canonical_sha256()?;
            let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
            let graph = ImportedDocumentFieldSemantics::import(&fields)?;
            assert_eq!(index.observations(), graph.observations());
            assert_eq!(index.receipt().bookmark_crossrefs, 1);
            assert_eq!(graph.receipt().bookmark_crossrefs, 1);
            assert_eq!(index.receipt().unsupported_meanings, 0);
            assert_eq!(index.receipt().additional_document_graph_clones, 0);
            assert!(
                !index
                    .receipt()
                    .complete_reference_state_or_external_approval
            );
            let ImportedFieldMeaning::BookmarkCrossReference { command } =
                &index.observations()[0].meaning
            else {
                return Err("typed meaning required".into());
            };
            assert_eq!(
                command.field_reference_id,
                index.observations()[0].reference_id
            );
            assert_eq!(
                command.display,
                [
                    Display::Page,
                    Display::BookmarkName,
                    Display::Content,
                    Display::RelativePosition
                ][display]
            );
            assert_eq!(command.hyperlink, hyperlink == 1);
            assert!(matches!(
                command.target,
                SourceBookmarkResolution::Bound { .. }
            ));
            let graph_json = String::from_utf8(graph.graph().canonical_json()?)?;
            assert!(
                graph_json.contains("source_derived_meaning")
                    && graph_json.contains("bookmark_cross_reference")
            );
            assert_eq!(fields.graph().canonical_sha256()?, original);
            let public = assess(&bytes)?;
            assert_eq!(public.receipt(), index.receipt());
            assert_eq!(
                public.selections()[0].kind,
                ReferenceSourceMeaningKind::BookmarkCrossReference
            );
            assert_eq!(
                public.selections()[0].meaning_sha256,
                index.meaning_sha256(0)?
            );
            let result: Value = serde_json::from_slice(&public.canonical_json(limits()?)?)?;
            assert_eq!(
                result["schema_version"],
                "hwpx-agent.product.reference-source-field-meanings/v2"
            );
            assert_eq!(result["status"], "incomplete");
            assert_eq!(result["reference_validation_or_external_approval"], false);
        }
    }
    Ok(())
}
#[test]
fn mixed_foreign_kinds_and_unkeyed_parameters_remain_explicit_unsupported() -> Result {
    let mut body = fixture::marker("private-target");
    body.push_str(&field(
        1,
        "CROSSREF",
        Some(&command("?private-target;6;0;0;0")),
    ));
    for id in 2..8 {
        body.push_str(&field(
            id,
            "CROSSREF",
            Some(&command(&format!("?foreign;{};0;0;0", id - 2))),
        ));
    }
    body.push_str(&field(8, "CROSSREF", None));
    body.push_str(&field(
        9,
        "CROSSREF",
        Some("<hp:stringParam name='Other'>?private-target;6;0;0;0</hp:stringParam>"),
    ));
    body.push_str(&field(10, "DATE", None));
    let bytes = package(&body)?;
    let public = assess(&bytes)?;
    assert_eq!(public.selections().len(), 10);
    assert_eq!(public.receipt().bookmark_crossrefs, 1);
    assert_eq!(public.receipt().unsupported_meanings, 9);
    assert!(
        public.selections()[1..]
            .iter()
            .all(|v| v.kind == ReferenceSourceMeaningKind::Unsupported)
    );
    // The original strict all-bookmark API must not silently return this subset.
    assert!(
        Product::read_source_bookmark_crossrefs(
            &bytes,
            DocumentId::parse(DOCUMENT)?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
            limits()?
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn missing_and_duplicate_bookmarks_have_typed_unresolved_meanings() -> Result {
    for (markers, ambiguous) in [
        (String::new(), false),
        (
            format!(
                "{}{}",
                fixture::marker("private-target"),
                fixture::marker("private-target")
            ),
            true,
        ),
    ] {
        let bytes = package(&format!(
            "{markers}{}",
            field(1, "CROSSREF", Some(&command("?private-target;6;0;0;0")))
        ))?;
        let forms = base::forms(&bytes, DOCUMENT)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
        let ImportedFieldMeaning::BookmarkCrossReference { command } =
            &index.observations()[0].meaning
        else {
            return Err("meaning required".into());
        };
        assert_eq!(
            command.target,
            if ambiguous {
                SourceBookmarkResolution::Ambiguous
            } else {
                SourceBookmarkResolution::Missing
            }
        );
        assert_eq!(assess(&bytes)?.receipt().bookmark_crossrefs, 1);
    }
    Ok(())
}
#[test]
fn malformed_supported_command_is_rejected_not_unsupported_success() -> Result {
    for child in [
        command("?private-target;6;4;0;0"),
        command("?private-target;6;0;0;0;"),
        "<hp:integerParam name='Command'>1</hp:integerParam>".into(),
        "<hp:stringParam name='Command'><!--x-->?private-target;6;0;0;0</hp:stringParam>".into(),
    ] {
        let bytes = package(&field(1, "CROSSREF", Some(&child)))?;
        assert!(matches!(
            Product::assess_package_field_semantics(
                &bytes,
                DocumentId::parse(DOCUMENT)?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                limits()?
            ),
            Err(ReferenceSourceError::FieldRanges)
        ));
    }
    Ok(())
}
#[test]
fn source_and_target_changes_invalidate_fresh_reconstruction_and_meaning_hash() -> Result {
    let make = |name: &str, display: u8| {
        package(&format!(
            "{}{}",
            fixture::marker(name),
            field(
                1,
                "CROSSREF",
                Some(&command(&format!("?private-target;6;{display};0;0")))
            )
        ))
    };
    let bytes = make("private-target", 0)?;
    let forms = base::forms(&bytes, DOCUMENT)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
    let graph = ImportedDocumentFieldSemantics::import(&fields)?;
    let proof = forms.reconstruct_source_for_verification(&bytes)?;
    assert_eq!(index.verify_reconstruction(&proof)?, *index.receipt());
    assert_eq!(graph.verify_reconstruction(&proof)?, *graph.receipt());
    let foreign = base::forms(&bytes, DOCUMENT)?;
    let foreign_proof = foreign.reconstruct_source_for_verification(&bytes)?;
    assert!(index.verify_reconstruction(&foreign_proof).is_err());
    assert!(graph.verify_reconstruction(&foreign_proof).is_err());
    for changed in [make("other-target", 0)?, make("private-target", 1)?] {
        assert!(forms.reconstruct_source_for_verification(&changed).is_err());
        assert_ne!(
            assess(&bytes)?.selections()[0].meaning_sha256,
            assess(&changed)?.selections()[0].meaning_sha256
        );
    }
    Ok(())
}
#[test]
fn finite_meaning_budgets_and_wrong_package_sha_fail_closed() -> Result {
    let bytes = package(&format!(
        "{}{}",
        fixture::marker("private-target"),
        field(1, "CROSSREF", Some(&command("?private-target;6;0;0;0")))
    ))?;
    for config in [
        ReferenceAuxiliaryLimitConfig {
            input_bytes: 128,
            output_bytes: 128,
            ..Default::default()
        },
        ReferenceAuxiliaryLimitConfig {
            text_bytes: 1,
            ..Default::default()
        },
    ] {
        assert!(matches!(
            Product::assess_package_field_semantics(
                &bytes,
                DocumentId::parse(DOCUMENT)?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                ReferenceAuxiliaryLimits::new(config)?
            ),
            Err(ReferenceSourceError::InputLimit)
        ));
    }
    assert!(matches!(
        Product::assess_package_field_semantics(
            &bytes,
            DocumentId::parse(DOCUMENT)?,
            [0; 32],
            SourceImportLimits::default(),
            limits()?
        ),
        Err(ReferenceSourceError::Binding)
    ));
    Ok(())
}
#[test]
fn public_selection_and_debug_never_expose_command_target_or_cache_text() -> Result {
    let bytes = package(&format!(
        "{}{}",
        fixture::marker("private-target"),
        field(1, "CROSSREF", Some(&command("?private-target;6;0;0;0")))
    ))?;
    let result = assess(&bytes)?;
    for text in [
        String::from_utf8(result.canonical_json(limits()?)?)?,
        format!("{result:?}"),
    ] {
        for secret in [
            "private-target",
            "?private-target;",
            "untrusted cache",
            "<hp:",
        ] {
            assert!(!text.contains(secret));
        }
    }
    Ok(())
}
fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("pin")?;
    if !name.starts_with("implementation/p09/evidence/private/")
        || name.contains('\\')
        || name.split('/').any(|v| v == ".." || v.is_empty())
    {
        return Err("path rejected".into());
    }
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("root")?;
    let path = root.join(name);
    for parent in path.ancestors() {
        let m = parent.symlink_metadata()?;
        if m.file_type().is_symlink() {
            return Err("link".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("reparse".into());
            }
        }
    }
    let size = pin["bytes"].as_u64().ok_or("size")?;
    if size == 0 || size > 4194304 || !path.is_file() {
        return Err("file limit".into());
    }
    std::thread::sleep(Duration::from_millis(50));
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file = options.open(&path)?;
    let mut bytes = Vec::new();
    let mut buffer = [0; 65536];
    let clock = Instant::now();
    loop {
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        if bytes.len() + n > 4194304 {
            return Err("read limit".into());
        }
        bytes.try_reserve(n)?;
        bytes.extend_from_slice(&buffer[..n]);
        if let Some(delay) =
            Duration::from_secs_f64(bytes.len() as f64 / 2097152.).checked_sub(clock.elapsed())
        {
            std::thread::sleep(delay);
        }
    }
    assert_eq!(bytes.len() as u64, size);
    assert_eq!(
        hex::encode(Sha256::digest(&bytes)),
        pin["sha256"].as_str().ok_or("sha")?
    );
    Ok(bytes)
}
#[test]
fn actual010_twenty_four_saved_outputs_use_integrated_public_meaning_api() -> Result {
    assert_eq!(
        hex::encode(Sha256::digest(CORPUS.as_bytes())),
        "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f"
    );
    let corpus: Value = serde_json::from_str(CORPUS)?;
    let mut count = 0;
    for case in corpus["cases"].as_array().ok_or("cases")? {
        for stage in ["opened", "saved", "reopened"] {
            let pin = &case["artifacts"][stage];
            let bytes = read_pin(pin)?;
            let result = assess(&bytes)?;
            let expected = usize::from(stage != "opened");
            assert_eq!(result.receipt().bookmark_crossrefs, expected);
            assert_eq!(result.receipt().unsupported_meanings, 0);
            let forms = base::forms(&bytes, DOCUMENT)?;
            let fields = ImportedDocumentFields::import(&forms)?;
            let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
            assert_eq!(result.receipt(), index.receipt());
            assert_eq!(result.selections().len(), fields.fields().len());
            assert_eq!(
                result
                    .selections()
                    .iter()
                    .filter(|item| item.kind == ReferenceSourceMeaningKind::BookmarkCrossReference)
                    .count(),
                expected
            );
            assert_eq!(
                result.receipt().ranges,
                result.receipt().https_targets
                    + result.receipt().table_formula_asts
                    + result.receipt().bookmark_crossrefs
                    + result.receipt().unsupported_meanings
            );
            if expected == 1 {
                let ImportedFieldMeaning::BookmarkCrossReference { command } = &index
                    .observations()
                    .iter()
                    .find(|item| {
                        matches!(
                            item.meaning,
                            ImportedFieldMeaning::BookmarkCrossReference { .. }
                        )
                    })
                    .ok_or("bookmark meaning")?
                    .meaning
                else {
                    return Err("meaning".into());
                };
                assert_eq!(hex::encode(command.command_sha256), case["command_sha256"]);
                assert!(matches!(
                    command.target,
                    SourceBookmarkResolution::Bound { .. }
                ));
                let selection = result
                    .selections()
                    .iter()
                    .find(|item| item.reference_id == command.field_reference_id)
                    .ok_or("bookmark selection")?;
                assert_eq!(
                    selection.kind,
                    ReferenceSourceMeaningKind::BookmarkCrossReference
                );
            }
            let json: Value = serde_json::from_slice(&result.canonical_json(limits()?)?)?;
            assert_eq!(json["status"], "incomplete");
            assert_eq!(json["reference_validation_or_external_approval"], false);
            assert_eq!(read_pin(pin)?, bytes);
            count += 1;
        }
    }
    assert_eq!(count, 24);
    Ok(())
}
#[test]
fn main_source_v13_still_reports_all_unresolved_stages() -> Result {
    let bytes = package(&format!(
        "{}{}",
        fixture::marker("private-target"),
        field(1, "CROSSREF", Some(&command("?private-target;6;0;0;0")))
    ))?;
    let result = Product::assess_package_source(
        &bytes,
        DocumentId::parse(DOCUMENT)?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    let value: Value = serde_json::from_slice(&result.canonical_json(limits()?)?)?;
    assert_eq!(
        value["schema_version"],
        "hwpx-agent.product.reference-source-assessment/v13"
    );
    assert_eq!(value["status"], json!(ReferenceSourceStatus::Incomplete));
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(), 4);
    Ok(())
}
