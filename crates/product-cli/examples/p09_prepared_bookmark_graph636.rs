//! Fixed current captures through real product readers and whole semantic graphs.
//! No Native, output mutation, arbitrary input CLI, old trial replay or Gate claim.
use domain_ir::{
    DocumentGraph, DocumentGraphLimits, DocumentId, ReferenceAuxiliaryLimitConfig,
    ReferenceAuxiliaryLimits,
};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation as Product,
    source_field_semantics::ReferenceSourceMeaningKind,
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        bookmark_crossref::{BookmarkCrossReferenceDisplay as Display, SourceBookmarkResolution},
        cached_source::{FieldCacheSnapshot, SourceFieldCachedInlines},
        semantics::{ImportedDocumentFieldSemantics, ImportedFieldMeaning},
    },
    forms::ImportedDocumentForms,
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{error::Error, fs::OpenOptions, io::Read, path::PathBuf, time::Duration};

type Result<T> = std::result::Result<T, Box<dyn Error>>;
const INPUT: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-prepared-bookmark636-product-inputs.v1.json"
);
fn require(ok: bool, code: &'static str) -> Result<()> {
    if !ok {
        return Err(code.into());
    }
    Ok(())
}
fn root() -> Result<PathBuf> {
    Ok(PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(std::path::Path::parent)
        .ok_or("P636_ROOT")?
        .to_owned())
}
fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("P636_PATH")?;
    require(
        name.starts_with("implementation/p09/evidence/")
            && !name.contains('\\')
            && !name.contains(':')
            && !name
                .split('/')
                .any(|v| v.is_empty() || v == "." || v == ".."),
        "P636_PATH_SCOPE",
    )?;
    let path = root()?.join(name);
    for component in path.ancestors() {
        let meta = component.symlink_metadata()?;
        require(!meta.file_type().is_symlink(), "P636_LINK")?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            require(meta.file_attributes() & 0x400 == 0, "P636_REPARSE")?;
        }
    }
    let expected = pin["bytes"].as_u64().ok_or("P636_SIZE")?;
    require(
        expected > 0
            && expected <= 4_194_304
            && path.metadata()?.is_file()
            && path.metadata()?.len() == expected,
        "P636_SIZE_LIMIT",
    )?;
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file = options.open(path)?;
    let mut out = Vec::new();
    let mut chunk = [0_u8; 65_536];
    loop {
        let n = file.read(&mut chunk)?;
        if n == 0 {
            break;
        }
        require(
            out.len()
                .checked_add(n)
                .is_some_and(|v| v <= expected as usize),
            "P636_GROWTH",
        )?;
        out.extend_from_slice(&chunk[..n]);
        std::thread::sleep(Duration::from_secs_f64(n as f64 / 2_097_152.));
    }
    require(
        out.len() as u64 == expected && hex::encode(Sha256::digest(&out)) == pin["sha256"],
        "P636_SHA",
    )?;
    Ok(out)
}
fn background(
    fields: &ImportedDocumentFields<'_>,
    semantics: &ImportedDocumentFieldSemantics<'_, '_>,
) -> Result<Value> {
    let limits = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default())?;
    let caches = SourceFieldCachedInlines::import(fields, limits)?;
    require(
        fields.fields().len() == semantics.observations().len()
            && fields.fields().len() == caches.observations().len(),
        "P636_WHOLE_BACKGROUND_COVERAGE",
    )?;
    let mut rows = Vec::new();
    for field in fields
        .fields()
        .iter()
        .filter(|v| v.native_kind != "CROSSREF")
    {
        let meaning = semantics
            .observations()
            .iter()
            .find(|v| v.reference_id == field.reference_id)
            .ok_or("P636_BACKGROUND_MEANING")?;
        let cache = caches
            .observations()
            .iter()
            .find(|v| v.field_reference_id == field.reference_id)
            .ok_or("P636_BACKGROUND_CACHE")?;
        let FieldCacheSnapshot::DecodedTextNotEvaluated {
            decoded_text_sha256,
            utf8_bytes,
            tabs,
            line_breaks,
            ..
        } = &cache.cache
        else {
            return Err("P636_BACKGROUND_STRUCTURED_CACHE_UNQUALIFIED".into());
        };
        rows.push(json!({"kind":field.native_kind,"native_id":field.native_begin_id,
            "parameters_sha256":field.parameter_anchor.as_ref().map(|v| hex::encode(v.fingerprint_sha256)),
            "meaning":meaning.meaning,"cache_sha256":hex::encode(decoded_text_sha256),
            "utf8_bytes":utf8_bytes,"tabs":tabs,"line_breaks":line_breaks}));
    }
    rows.sort_by_key(Value::to_string);
    // Values remain private in memory. Only the aggregate hash is published.
    Ok(Value::Array(rows))
}
fn inspect(
    bytes: &[u8],
    expected: &Value,
    display: Display,
    hyperlink: bool,
    target_name: &Value,
    original_background: &Value,
) -> Result<(Value, Value)> {
    let limits = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default())?;
    let document = DocumentId::parse("p09-prepared-bookmark-graph636")?;
    let sha = Sha256::digest(bytes).into();
    let bindings = Product::read_source_bookmark_crossrefs(
        bytes,
        document.clone(),
        sha,
        SourceImportLimits::default(),
        limits,
    )?;
    require(bindings.bindings().len() == 1, "P636_ONE_BINDING")?;
    let binding = &bindings.bindings()[0];
    require(
        binding.display == display
            && binding.hyperlink == hyperlink
            && hex::encode(binding.command_sha256) == expected["command_sha256"]
            && hex::encode(binding.exact_target_name_sha256) == *target_name,
        "P636_TYPED_BINDING",
    )?;
    let SourceBookmarkResolution::Bound {
        logical_target_id, ..
    } = &binding.target
    else {
        return Err("P636_TARGET_NOT_BOUND".into());
    };
    let assessment = Product::assess_package_source(
        bytes,
        document.clone(),
        sha,
        SourceImportLimits::default(),
        limits,
    )?;
    require(
        assessment.validation_report().is_none()
            && assessment.target_receipt().bookmark_targets == 1
            && assessment.field_range_receipt().field_ranges
                == original_background
                    .as_array()
                    .ok_or("P636_BACKGROUND_ARRAY")?
                    .len()
                    + 1
            && assessment.field_meanings().receipt().bookmark_crossrefs == 1
            && assessment.field_meanings().selections().len()
                == assessment.field_range_receipt().field_ranges,
        "P636_PRODUCT_COVERAGE",
    )?;
    let meaning = assessment
        .field_meanings()
        .selections()
        .iter()
        .find(|v| v.reference_id == binding.field_reference_id)
        .ok_or("P636_PRODUCT_MEANING_MISSING")?;
    require(
        meaning.kind == ReferenceSourceMeaningKind::BookmarkCrossReference
            && meaning.reference_id == binding.field_reference_id,
        "P636_PRODUCT_MEANING",
    )?;
    let cached = assessment.field_cached_source().observations();
    require(
        cached.len() == assessment.field_range_receipt().field_ranges,
        "P636_CACHE_FIELD",
    )?;
    let FieldCacheSnapshot::DecodedTextNotEvaluated {
        decoded_text_sha256,
        utf8_bytes,
        ..
    } = &cached
        .iter()
        .find(|v| v.field_reference_id == binding.field_reference_id)
        .ok_or("P636_CACHE_MISSING")?
        .cache
    else {
        return Err("P636_STRUCTURED_CACHE_UNQUALIFIED".into());
    };
    require(
        hex::encode(decoded_text_sha256) == expected["display_sha256"],
        "P636_INDEPENDENT_CACHE_READBACK",
    )?;
    let package =
        ImportedSourcePackage::import(bytes, document, sha, SourceImportLimits::default())?;
    let forms = ImportedDocumentForms::import(package)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let semantics = ImportedDocumentFieldSemantics::import(&fields)?;
    require(
        background(&fields, &semantics)? == *original_background,
        "P636_ORIGINAL_BACKGROUND_NOT_PRESERVED",
    )?;
    require(
        semantics.receipt().bookmark_crossrefs == 1
            && semantics.receipt().bound_bookmark_edges == 1
            && semantics.receipt().unsupported_meanings == 0
            && semantics.observations().len() == assessment.field_range_receipt().field_ranges,
        "P636_GRAPH_MEANINGS",
    )?;
    require(
        matches!(&semantics.observations().iter().find(|v| v.reference_id == binding.field_reference_id).ok_or("P636_GRAPH_MEANING_MISSING")?.meaning,
        ImportedFieldMeaning::BookmarkCrossReference { command } if command == binding),
        "P636_API_GRAPH_JOIN",
    )?;
    let target = forms
        .bookmarks()
        .iter()
        .find(|v| &v.reference_id == logical_target_id)
        .ok_or("P636_GRAPH_BOOKMARK")?;
    let graph_bytes = semantics.graph().canonical_json()?;
    let graph_value: Value = serde_json::from_slice(&graph_bytes)?;
    let edges = graph_value["references"]
        .as_array()
        .ok_or("P636_GRAPH_REFERENCES")?;
    let field_id = serde_json::to_value(&binding.field_reference_id)?;
    let wrapper_id = serde_json::to_value(&target.wrapper_node_id)?;
    require(
        edges
            .iter()
            .filter(|v| v["reference_id"] == field_id && v["target_node_id"] == wrapper_id)
            .count()
            == 1,
        "P636_EXACT_GRAPH_EDGE",
    )?;
    let reopened_graph = DocumentGraph::from_json(&graph_bytes, DocumentGraphLimits::default())?;
    require(
        &reopened_graph == semantics.graph() && reopened_graph.canonical_json()? == graph_bytes,
        "P636_GRAPH_SERIALIZATION_REOPEN",
    )?;
    require(
        semantics.verify_source(bytes)? == *semantics.receipt(),
        "P636_WHOLE_SOURCE_RECONSTRUCTION",
    )?;
    let projection = json!({"command_sha256":hex::encode(binding.command_sha256),
        "target_name_sha256":target_name,"display":display,"hyperlink":hyperlink,
        "cached_display_sha256":hex::encode(decoded_text_sha256),"cached_utf8_bytes":utf8_bytes});
    let report = json!({"product_source_bound":true,"exact_graph_target_edge":true,
        "semantic_graph_sha256":hex::encode(semantics.receipt().graph_sha256),
        "field_graph_sha256":hex::encode(fields.receipt().graph_sha256),
        "product_meaning_sha256":hex::encode(meaning.meaning_sha256),
        "whole_source_reconstruction":true,"graph_serialization_reopened":true,"original_background_preserved":true,
        "background_semantics_sha256":hex::encode(Sha256::digest(serde_json::to_vec(original_background)?))});
    Ok((projection, report))
}
fn run() -> Result<Value> {
    let input: Value = serde_json::from_str(INPUT)?;
    require(
        input["schema"] == "hwpx-agent.p09.prepared-capture-product-input636/v1"
            && input["native_execution_authorized"] == false
            && input["P09_complete"] == false,
        "P636_PROFILE",
    )?;
    let cases = input["cases"].as_array().ok_or("P636_CASES")?;
    require(cases.len() == 8, "P636_EIGHT")?;
    let source = read_pin(&input["source"])?;
    let source_package = ImportedSourcePackage::import(
        &source,
        DocumentId::parse("p09-prepared-bookmark-graph636")?,
        Sha256::digest(&source).into(),
        SourceImportLimits::default(),
    )?;
    let source_forms = ImportedDocumentForms::import(source_package)?;
    let source_fields = ImportedDocumentFields::import(&source_forms)?;
    let source_semantics = ImportedDocumentFieldSemantics::import(&source_fields)?;
    let original_background = background(&source_fields, &source_semantics)?;
    require(
        source_fields.fields().len() == 1
            && source_fields.fields()[0].native_kind == "HYPERLINK"
            && original_background.as_array().is_some_and(|v| v.len() == 1),
        "P636_ORIGINAL_HYPERLINK_CONTEXT",
    )?;
    require(
        Product::read_source_bookmark_crossrefs(
            &source,
            DocumentId::parse("p09-prepared-bookmark-graph636")?,
            Sha256::digest(&source).into(),
            SourceImportLimits::default(),
            ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default())?,
        )?
        .bindings()
        .is_empty(),
        "P636_ORIGINAL_HAS_NO_FIELD",
    )?;
    let mut rows = Vec::new();
    for (index, case) in cases.iter().enumerate() {
        let display = [
            Display::Page,
            Display::BookmarkName,
            Display::Content,
            Display::RelativePosition,
        ][index / 2];
        require(
            case["case_index"] == index + 1
                && case["hyperlink"] == (index % 2 == 1)
                && serde_json::to_value(display)? == case["display"],
            "P636_COMBINATION_ORDER",
        )?;
        let mut first = None;
        for stage in ["initial", "saved", "reopened"] {
            let expected = &case["stages"][stage];
            let bytes = read_pin(&expected["pin"])?;
            let (projection, report) = inspect(
                &bytes,
                expected,
                display,
                index % 2 == 1,
                &input["target_name_sha256"],
                &original_background,
            )?;
            if let Some(prior) = &first {
                require(
                    prior == &projection,
                    "P636_CROSS_STAGE_SEMANTIC_PRESERVATION",
                )?;
            } else {
                first = Some(projection.clone());
            }
            require(read_pin(&expected["pin"])? == bytes, "P636_FRESH_ARTIFACT")?;
            rows.push(json!({"case_index":index+1,"stage":stage,"source":expected["pin"],"projection":projection,"graph":report}));
        }
    }
    require(read_pin(&input["source"])? == source, "P636_FRESH_ORIGINAL")?;
    Ok(
        json!({"state":"PASS636_CURRENT24_SOURCE_PRODUCT_BINDINGS_CACHE_AND_SEMANTIC_GRAPH_NOT_FULL_F11",
        "observations":rows,"native_started":false,"old_trials_replayed":false,
        "render_qualified":false,"target_motion_rename_qualified":false,"full_F11_or_P09_qualified":false}),
    )
}
fn main() {
    let result = (|| -> Result<()> {
        require(
            std::env::args().skip(1).collect::<Vec<_>>() == ["--current-captured-graph-readonly"],
            "P636_CLOSED_ARGS",
        )?;
        let bytes = serde_json::to_vec(&run()?)?;
        require(bytes.len() <= 32_000, "P636_OUTPUT_LIMIT")?;
        println!("{}", String::from_utf8(bytes)?);
        Ok(())
    })();
    if let Err(error) = result {
        // All explicit codes are closed; never print arbitrary dependency errors.
        let message = error.to_string();
        if message.starts_with("P636_")
            && message.len() < 80
            && message
                .bytes()
                .all(|b| b.is_ascii_uppercase() || b.is_ascii_digit() || b == b'_')
        {
            eprintln!("{message}");
        } else {
            eprintln!("P636_PRODUCT_OR_GRAPH_REJECTED_NO_RAW_VALUES");
        }
        std::process::exit(2);
    }
}
