//! Fixed captured outputs only. Cache hashes/equality are not Native evaluation.
use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation as Product,
    source_field_semantics::ReferenceSourceMeaningKind,
};
#[cfg(test)]
use hwpx_package::document_import::fields::cached_source::SourceFieldCachedInlines;
use hwpx_package::document_import::{
    SourceImportLimits, fields::cached_source::FieldCacheSnapshot,
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
type Result<T = ()> = std::result::Result<T, Box<dyn Error>>;
const DOC: &str = "p09-field-cache619";
const CORPUS: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
);
fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn require(ok: bool) -> Result {
    if !ok {
        return Err("P619_CACHE_OBSERVATION_REJECTED".into());
    }
    Ok(())
}
fn assess(
    bytes: &[u8],
) -> Result<hwpx_agent_cli::reference_validation_product::source::ReferenceSourceAssessment> {
    Ok(Product::assess_package_source(
        bytes,
        DocumentId::parse(DOC)?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
        limits()?,
    )?)
}
fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("pin")?;
    require(
        name.starts_with("implementation/p09/evidence/private/")
            && !name.contains('\\')
            && !name.split('/').any(|v| v == ".." || v.is_empty()),
    )?;
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("root")?;
    let path = root.join(name);
    for ancestor in path.ancestors().collect::<Vec<_>>().into_iter().rev() {
        let m = ancestor.symlink_metadata()?;
        require(!m.file_type().is_symlink())?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            require(m.file_attributes() & 0x400 == 0)?;
        }
    }
    let size = pin["bytes"].as_u64().ok_or("size")?;
    require(size > 0 && size <= 4194304 && path.is_file() && path.metadata()?.len() == size)?;
    std::thread::sleep(Duration::from_millis(50));
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file = options.open(path)?;
    let mut bytes = Vec::new();
    let mut buffer = [0; 65536];
    let watch = Instant::now();
    loop {
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        require(bytes.len() + n <= 4194304)?;
        bytes.try_reserve(n)?;
        bytes.extend_from_slice(&buffer[..n]);
        if let Some(delay) =
            Duration::from_secs_f64(bytes.len() as f64 / 2097152.).checked_sub(watch.elapsed())
        {
            std::thread::sleep(delay);
        }
    }
    require(
        bytes.len() as u64 == size
            && hex::encode(Sha256::digest(&bytes)) == pin["sha256"].as_str().ok_or("sha")?,
    )?;
    Ok(bytes)
}
fn fixed_captured() -> Result<Value> {
    require(
        hex::encode(Sha256::digest(CORPUS.as_bytes()))
            == "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f",
    )?;
    let corpus: Value = serde_json::from_str(CORPUS)?;
    let cases = corpus["cases"].as_array().ok_or("cases")?;
    require(cases.len() == 8)?;
    let mut observations = Vec::new();
    let mut comparisons = Vec::new();
    for case in cases {
        let mut saved = None;
        let mut reopened = None;
        for stage in ["opened", "saved", "reopened"] {
            let pin = &case["artifacts"][stage];
            let bytes = read_pin(pin)?;
            let report = assess(&bytes)?;
            let caches = report.field_cached_source();
            require(caches.field_import() == report.field_range_receipt())?;
            require(caches.observations().len() == report.field_meanings().receipt().ranges)?;
            let metadata: Value = serde_json::from_slice(&caches.canonical_json(limits()?)?)?;
            for key in [
                "native_display_or_evaluation_qualified",
                "cache_currentness_qualified",
                "complete_reference_validation_qualified",
            ] {
                require(metadata[key] == false)?;
            }
            let selected: Vec<_> = report
                .field_meanings()
                .selections()
                .iter()
                .filter(|v| v.kind == ReferenceSourceMeaningKind::BookmarkCrossReference)
                .collect();
            require(selected.len() == usize::from(stage != "opened"))?;
            let snapshot = if let Some(field) = selected.first() {
                Some(
                    caches
                        .observations()
                        .iter()
                        .find(|v| v.field_reference_id == field.reference_id)
                        .ok_or("cache join")?
                        .cache
                        .clone(),
                )
            } else {
                None
            };
            let mut name_match = None;
            if stage != "opened" && case["display"] == "bookmark_name" {
                let bindings = Product::read_source_bookmark_crossrefs(
                    &bytes,
                    DocumentId::parse(DOC)?,
                    Sha256::digest(&bytes).into(),
                    SourceImportLimits::default(),
                    limits()?,
                )?;
                require(bindings.bindings().len() == 1)?;
                if let Some(FieldCacheSnapshot::DecodedTextNotEvaluated {
                    decoded_text_sha256,
                    ..
                }) = &snapshot
                {
                    name_match = Some(
                        *decoded_text_sha256 == bindings.bindings()[0].exact_target_name_sha256,
                    );
                }
            }
            if stage == "saved" {
                saved = snapshot.clone();
            }
            if stage == "reopened" {
                reopened = snapshot.clone();
            }
            observations.push(json!({"case_index":case["case_index"],"stage":stage,"source_sha256":pin["sha256"],
                "all_field_cache_records":caches.observations().len(),"selected_crossref_cache":snapshot,
                "bookmark_name_cache_matches_decoded_command_target":name_match,"cache_currentness_qualified":false}));
            require(read_pin(pin)? == bytes)?;
        }
        comparisons.push(json!({"case_index":case["case_index"],"saved_reopened_selected_cache_equal":saved==reopened}));
    }
    Ok(
        json!({"state":"source_field_cache619_observed_not_native_or_currentness","observations":observations,
        "saved_reopened_comparisons":comparisons,"actual_native_started":false,"native_display_or_evaluation_qualified":false,
        "cache_currentness_qualified":false,"P09_complete":false}),
    )
}
fn main() {
    let result = (|| -> Result {
        require(std::env::args().skip(1).collect::<Vec<_>>() == ["--fixed-captured-readonly"])?;
        let bytes = serde_json::to_vec(&fixed_captured()?)?;
        require(bytes.len() <= 32768)?;
        println!("{}", String::from_utf8(bytes)?);
        Ok(())
    })();
    if result.is_err() {
        eprintln!("P619_FIXED_CACHE_SOURCE_FAILED");
        std::process::exit(2);
    }
}
#[cfg(test)]
#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[cfg(test)]
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
#[cfg(test)]
mod tests {
    use super::*;
    use domain_ir::ReferenceAuxiliaryLimitConfig;
    use hwpx_package::document_import::fields::{
        ImportedDocumentFields, cached_source::FieldCachedSourceError,
    };
    fn field(id: u32, cache: &str) -> String {
        format!(
            "<hp:ctrl><hp:fieldBegin id='{id}' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='Command'>?private-target;6;1;0;0</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl>{cache}<hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>"
        )
    }
    fn package(body: &str) -> Result<Vec<u8>> {
        base::package(&fixture::paragraph(body))
    }
    fn cache(bytes: &[u8], budget: ReferenceAuxiliaryLimits) -> Result<SourceFieldCachedInlines> {
        let forms = base::forms(bytes, DOC)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let before = fields.graph().canonical_sha256()?;
        let result = SourceFieldCachedInlines::import(&fields, budget)?;
        require(fields.graph().canonical_sha256()? == before)?;
        Ok(result)
    }
    fn digest(text: &str) -> [u8; 32] {
        Sha256::digest(text.as_bytes()).into()
    }
    #[test]
    fn exact_decoded_text_tabs_breaks_entities_and_spaces_are_not_normalized() -> Result {
        let body = format!(
            "<hp:t>outside-before</hp:t>{}<hp:t>outside-after</hp:t>",
            field(
                1,
                "<hp:t>  A&amp;한<hp:tab width='1' leader='0' type='0'/>B<hp:lineBreak/>C  </hp:t>"
            )
        );
        let result = cache(&package(&body)?, limits()?)?;
        assert_eq!(result.observations().len(), 1);
        let FieldCacheSnapshot::DecodedTextNotEvaluated {
            decoded_text_sha256,
            utf8_bytes,
            tabs,
            line_breaks,
            ..
        } = &result.observations()[0].cache
        else {
            return Err("decoded cache".into());
        };
        assert_eq!(*decoded_text_sha256, digest("  A&한\tB\nC  "));
        assert_eq!(*utf8_bytes, "  A&한\tB\nC  ".len());
        assert_eq!((*tabs, *line_breaks), (1, 1));
        Ok(())
    }
    #[test]
    fn empty_cache_is_an_observed_empty_snapshot_not_an_absent_field_or_current_value() -> Result {
        let result = cache(&package(&field(1, ""))?, limits()?)?;
        assert!(
            matches!(&result.observations()[0].cache,FieldCacheSnapshot::DecodedTextNotEvaluated{decoded_text_sha256,utf8_bytes:0,text_atoms:0,..}if *decoded_text_sha256==digest(""))
        );
        let value: Value = serde_json::from_slice(&result.canonical_json(limits()?)?)?;
        assert_eq!(value["cache_currentness_qualified"], false);
        Ok(())
    }
    #[test]
    fn nested_field_parent_is_structured_and_child_text_is_not_flattened_into_it() -> Result {
        let child = "<hp:ctrl><hp:fieldBegin id='2' type='DATE'/></hp:ctrl><hp:t>child</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='2'/></hp:ctrl>";
        let result = cache(
            &package(&field(1, &format!("<hp:t>A</hp:t>{child}<hp:t>B</hp:t>")))?,
            limits()?,
        )?;
        assert_eq!(result.observations().len(), 2);
        assert!(matches!(
            result.observations()[0].cache,
            FieldCacheSnapshot::StructuredUnqualified {
                unsupported_inline_items: 2,
                ..
            }
        ));
        assert!(
            matches!(&result.observations()[1].cache,FieldCacheSnapshot::DecodedTextNotEvaluated{decoded_text_sha256,..}if *decoded_text_sha256==digest("child"))
        );
        Ok(())
    }
    #[test]
    fn bookmark_controls_inside_cache_remain_structured_not_empty_or_ignored() -> Result {
        let result = cache(
            &package(&field(
                1,
                &format!("<hp:t>A</hp:t>{}<hp:t>B</hp:t>", fixture::marker("inside")),
            ))?,
            limits()?,
        )?;
        assert!(matches!(
            result.observations()[0].cache,
            FieldCacheSnapshot::StructuredUnqualified {
                unsupported_inline_items: 2,
                inline_items: 4,
            }
        ));
        Ok(())
    }
    #[test]
    fn cross_run_note_and_table_ranges_preserve_original_field_order_and_owner() -> Result {
        let crossing = "<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>A</hp:t></hp:run><hp:run><hp:t>B</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>";
        let bytes = base::package(crossing)?;
        assert!(
            matches!(&cache(&bytes,limits()?)?.observations()[0].cache,FieldCacheSnapshot::DecodedTextNotEvaluated{decoded_text_sha256,..}if *decoded_text_sha256==digest("AB"))
        );
        for body in [
            fixture::note(&field(1, "<hp:t>N</hp:t>")),
            fixture::table(&field(1, "<hp:t>T</hp:t>")),
        ] {
            let bytes = package(&body)?;
            assert_eq!(cache(&bytes, limits()?)?.observations().len(), 1);
        }
        Ok(())
    }
    #[test]
    fn cache_changes_are_not_reinterpreted_as_a_new_command_or_native_currentness() -> Result {
        let mut commands = Vec::new();
        let mut snapshots = Vec::new();
        for text in ["old cache", "changed cache"] {
            let bytes = package(&format!(
                "{}{}",
                fixture::marker("private-target"),
                field(1, &format!("<hp:t>{text}</hp:t>"))
            ))?;
            let bindings = Product::read_source_bookmark_crossrefs(
                &bytes,
                DocumentId::parse(DOC)?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                limits()?,
            )?;
            commands.push(bindings.bindings()[0].command_sha256);
            snapshots.push(cache(&bytes, limits()?)?.observations()[0].cache.clone());
        }
        assert_eq!(commands[0], commands[1]);
        assert_ne!(snapshots[0], snapshots[1]);
        Ok(())
    }
    #[test]
    fn output_text_item_and_aggregate_hash_budgets_fail_without_partial_results() -> Result {
        let bytes = package(&format!(
            "{}{}",
            field(1, "<hp:t>abc</hp:t>"),
            field(2, "<hp:t>def</hp:t>")
        ))?;
        let forms = base::forms(&bytes, DOC)?;
        let fields = ImportedDocumentFields::import(&forms)?;
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
            ReferenceAuxiliaryLimitConfig {
                input_bytes: 5,
                ..Default::default()
            },
            ReferenceAuxiliaryLimitConfig {
                items_per_kind: 1,
                ..Default::default()
            },
        ] {
            assert!(matches!(
                SourceFieldCachedInlines::import(&fields, ReferenceAuxiliaryLimits::new(config)?),
                Err(FieldCachedSourceError::Limit)
            ));
        }
        let result = cache(&bytes, limits()?)?;
        let n = result.canonical_json(limits()?)?.len();
        let exact = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
            input_bytes: n,
            output_bytes: n,
            ..Default::default()
        })?;
        assert_eq!(result.canonical_json(exact)?.len(), n);
        assert!(matches!(
            result.canonical_json(ReferenceAuxiliaryLimits::new(
                ReferenceAuxiliaryLimitConfig {
                    input_bytes: n - 1,
                    output_bytes: n - 1,
                    ..Default::default()
                }
            )?),
            Err(FieldCachedSourceError::Limit)
        ));
        Ok(())
    }
    #[test]
    fn many_fields_have_linear_prefix_work_and_no_additional_document_graph_clone() -> Result {
        let mut body = String::new();
        for id in 1..=128 {
            body.push_str(&field(id, "<hp:t>x</hp:t>"));
        }
        let result = cache(&package(&body)?, limits()?)?;
        let value: Value = serde_json::from_slice(&result.canonical_json(limits()?)?)?;
        assert_eq!(result.observations().len(), 128);
        assert_eq!(value["prefix_events"], 256);
        assert_eq!(value["hashed_text_bytes"], 128);
        assert!(value["scanned_inline_items"].as_u64().ok_or("work")? <= 384);
        assert_eq!(value["additional_document_graph_clones"], 0);
        Ok(())
    }
    #[test]
    fn source_v15_cache_join_is_separate_from_meaning_and_never_exposes_private_text() -> Result {
        let bytes = package(&format!(
            "{}{}",
            fixture::marker("private-target"),
            field(1, "<hp:t>private cached value</hp:t>")
        ))?;
        let result = assess(&bytes)?;
        assert_eq!(
            result.field_cached_source().field_import(),
            result.field_range_receipt()
        );
        assert_eq!(
            result.field_cached_source().observations()[0].field_reference_id,
            result.field_meanings().selections()[0].reference_id
        );
        let value: Value = serde_json::from_slice(&result.canonical_json(limits()?)?)?;
        assert_eq!(
            value["schema_version"],
            "hwpx-agent.product.reference-source-assessment/v15"
        );
        assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(), 4);
        assert!(value["validation_report"].is_null());
        assert_eq!(value["status"], "incomplete");
        for text in [
            String::from_utf8(result.canonical_json(limits()?)?)?,
            format!("{result:?}"),
        ] {
            for private in ["private-target", "private cached value", "?private-target;"] {
                assert!(!text.contains(private));
            }
        }
        Ok(())
    }
    #[test]
    fn exact_captured_twenty_four_outputs_use_main_source_cache_path_without_native_execution()
    -> Result {
        let value = fixed_captured()?;
        require(
            value["observations"]
                .as_array()
                .is_some_and(|v| v.len() == 24),
        )?;
        require(value["cache_currentness_qualified"] == false)?;
        Ok(())
    }
}
