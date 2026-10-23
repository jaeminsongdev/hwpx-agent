//! Complete disposable packages using the production preserving field-update adapter.
#[allow(dead_code)]
#[path = "p08_19_support/common.rs"]
mod archive;
use domain_ir::{
    FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldCacheStatus, FieldCachedResult, FieldDefinition,
    FieldDocumentState, FieldDocumentStateDraft, FieldEngineBuilder, FieldEngineLimitConfig,
    FieldEngineLimits, FieldIdentity, FieldOperation, FieldRequest, FieldRequestDraft, FieldState,
    FieldUpdatePolicy, LogicalId,
};
use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    BoundedZipReader, ClickHereHwpxBuilder, ClickHereHwpxLimits, ClickHereHwpxLowerer,
    ClickHereHwpxReader, PackageGraph, PackageGraphLimits, PackageLimits,
};
use serde::Serialize;
use std::{
    collections::BTreeMap,
    env,
    error::Error,
    fs,
    io::Cursor,
    path::{Path, PathBuf},
};
type AnyError = Box<dyn Error>;
const DIR: &str = "implementation/p09/evidence/private/p09-22-click-here-discovery-20261002-01";
const SEEDS: [(&str, &str, &str, &str, &str); 2] = [
    (
        "P09-22-C01",
        "empty.hwpx",
        "60a646f488941bad203d1c1d8bab43a36f2ae5c4712396eeeb3c1acb81d50747",
        "p09-22-c01-empty-field-update.hwpx",
        "P09 value & <text> 한글",
    ),
    (
        "P09-22-C02",
        "filled.hwpx",
        "ab6d2d2d8f9d4375c30b16b80e963a71c31c3b3ed6c7466f5bc3da872b00ebaf",
        "p09-22-c02-filled-field-update.hwpx",
        "P09 revised & <value> 한글 🚀",
    ),
];
#[derive(Serialize)]
struct FixtureRecord {
    case_id: &'static str,
    feature_ids: [&'static str; 1],
    file: &'static str,
    source_file: &'static str,
    source_package_sha256: &'static str,
    source_section_sha256: String,
    output_package_sha256: String,
    output_package_bytes: usize,
    output_section_sha256: String,
    expected_display_sha256: String,
    native_begin_id: u32,
    native_field_id: u32,
    parameters_sha256: String,
    plan_sha256: String,
    unrelated_parts_sha256: BTreeMap<String, String>,
    deterministic_retry: bool,
    stale_source_rejected: bool,
    outside_declared_edits_byte_exact: bool,
}
fn main() -> Result<(), AnyError> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?;
    let output = output_argument(&root)?;
    let mut cases = Vec::new();
    let mut packages = Vec::new();
    for (case, source_file, expected, file, display) in SEEDS {
        let source = read_seed(&root.join(DIR).join(source_file), expected)?;
        let section = archive::section_from_package(&source)?;
        let (lowered, plan_sha, stale) = lower(&section, display)?;
        let (retry, _, _) = lower(&section, display)?;
        if lowered != retry {
            return Err("non-deterministic lowering".into());
        }
        let bytes = archive::package_with_section(&source, &lowered)?;
        let repeated = archive::package_with_section(&source, &retry)?;
        if bytes != repeated || inventory(&source)? != inventory(&bytes)? {
            return Err("non-deterministic archive or changed unrelated part".into());
        }
        let native = ClickHereHwpxReader::inspect_section(
            &lowered,
            &[LogicalId::parse("paragraph-1")?],
            ClickHereHwpxLimits::default(),
        )?;
        if native.len() != 1 || native[0].display != display {
            return Err("native target projection mismatch".into());
        }
        cases.push(FixtureRecord {
            case_id: case,
            feature_ids: ["REF-009"],
            file,
            source_file,
            source_package_sha256: expected,
            source_section_sha256: archive::sha256(&section),
            output_package_sha256: archive::sha256(&bytes),
            output_package_bytes: bytes.len(),
            output_section_sha256: archive::sha256(&lowered),
            expected_display_sha256: archive::sha256(display.as_bytes()),
            native_begin_id: native[0].native_begin_id,
            native_field_id: native[0].native_field_id,
            parameters_sha256: native[0].parameters_sha256.clone(),
            plan_sha256: plan_sha,
            unrelated_parts_sha256: inventory(&source)?,
            deterministic_retry: true,
            stale_source_rejected: stale,
            outside_declared_edits_byte_exact: true,
        });
        packages.push(bytes);
    }
    let manifest = serde_json::json!({"schema_version":"hwpx-agent.p09-click-here-update-target-fixture/v1",
        "task":"P09-22","cases":cases,"complete_package_graph":true,"actual_hangul":false,
        "semantic_save_reopen":"not_run","render":"not_run","differential":"not_run",
        "green_rows":0,"p09_complete":false,"product_complete":false});
    let raw = serde_json::to_vec_pretty(&manifest)?;
    let workspace = SecureWorkspace::create(&output)?;
    for (case, bytes) in cases.iter().zip(&packages) {
        let staged = workspace.stage_bytes(&Path::new("p09-22").join(case.file), bytes)?;
        workspace.publish(&staged, Path::new(case.file))?;
    }
    let staged = workspace.stage_bytes(Path::new("p09-22/fixture-manifest.json"), &raw)?;
    workspace.publish(&staged, Path::new("fixture-manifest.json"))?;
    println!(
        "{}",
        serde_json::json!({"state":"pass","cases":cases.len(),"manifest_sha256":archive::sha256(&raw),
        "actual_hangul":false,"green_rows":0})
    );
    Ok(())
}
#[allow(clippy::too_many_lines)] // Explicit fixture binding fields are kept together for audit.
fn lower(source: &[u8], display: &str) -> Result<(Vec<u8>, String, bool), AnyError> {
    let map = [LogicalId::parse("paragraph-1")?];
    let state_limits = FieldEngineLimits::new(FieldEngineLimitConfig::default())?;
    let hwpx_limits = ClickHereHwpxLimits::default();
    let observed = ClickHereHwpxReader::inspect_section(source, &map, hwpx_limits)?;
    if observed.len() != 1 {
        return Err("source must contain one native field".into());
    }
    let p = &observed[0];
    let binding = archive::sha256(source);
    let state = FieldDocumentState::from_draft(
        FieldDocumentStateDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.into(),
            fields: vec![FieldState {
                identity: FieldIdentity {
                    logical_field_id: LogicalId::parse("field-1")?,
                    native_begin_id: 1,
                    native_end_id: 2,
                },
                anchor: FieldAnchor {
                    paragraph_id: map[0].clone(),
                    run_ordinal: p.run_ordinal,
                    inline_ordinal: p.inline_ordinal,
                },
                definition: FieldDefinition::ClickHere {
                    prompt: p.prompt.clone(),
                },
                cached_result: FieldCachedResult::Text {
                    display: p.display.clone(),
                },
                update_policy: FieldUpdatePolicy::RecomputeDirect,
                cache_status: FieldCacheStatus::Current,
                locked: false,
                evaluation_context_sha256: None,
                character_style_sha256: p.character_style_sha256.clone(),
                paragraph_style_sha256: p.paragraph_style_sha256.clone(),
                field_payload_sha256: p.parameters_sha256.clone(),
                opaque_properties: vec![],
            }],
            non_field_content_sha256: binding.clone(),
            style_catalog_sha256: binding.clone(),
            reference_inventory_sha256: binding.clone(),
            resource_inventory_sha256: binding.clone(),
            opaque_document_state_sha256: binding.clone(),
        },
        state_limits,
    )?;
    let target_flow = archive::sha256(display.as_bytes());
    let request = FieldRequest::from_draft(
        FieldRequestDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("request-1")?,
            expected_source_state_sha256: state.canonical_sha256(state_limits)?,
            expected_document_flow_sha256: binding.clone(),
            target_document_flow_sha256: target_flow.clone(),
            operation: FieldOperation::UpdateResult {
                target: state.fields()[0].identity.clone(),
                cached_result: FieldCachedResult::Text {
                    display: display.into(),
                },
                evaluation_context_sha256: target_flow,
            },
        },
        &state,
        &binding,
        state_limits,
    )?;
    let domain = FieldEngineBuilder::plan(&state, &request, &binding, state_limits)?;
    let plan = ClickHereHwpxBuilder::plan(
        source,
        &state,
        &domain,
        &binding,
        &map,
        state_limits,
        hwpx_limits,
    )?;
    let mut drift = source.to_vec();
    drift.push(b' ');
    let rejected_drift = ClickHereHwpxLowerer::lower_section_with_receipt(
        &drift,
        &plan,
        &state,
        &binding,
        &map,
        state_limits,
        hwpx_limits,
    )
    .is_err();
    if !rejected_drift {
        return Err("stale source admitted".into());
    }
    let (result, receipt) = ClickHereHwpxLowerer::lower_section_with_receipt(
        source,
        &plan,
        &state,
        &binding,
        &map,
        state_limits,
        hwpx_limits,
    )?;
    if !receipt.outside_declared_edits_byte_exact {
        return Err("preservation failed".into());
    }
    Ok((result, plan.plan_sha256().into(), rejected_drift))
}
fn inventory(package: &[u8]) -> Result<BTreeMap<String, String>, AnyError> {
    let mut reader = BoundedZipReader::open(Cursor::new(package), PackageLimits::default())?;
    PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let entries: Vec<_> = reader
        .entries()
        .iter()
        .map(|e| (e.index, e.path.as_str().to_owned()))
        .collect();
    let mut result = BTreeMap::new();
    for (index, name) in entries {
        if name != archive::SECTION_PATH {
            result.insert(name, archive::sha256(&reader.read_entry(index)?));
        }
    }
    Ok(result)
}
fn is_link(metadata: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt as _;
        metadata.file_attributes() & 0x400 != 0
    }
    #[cfg(not(windows))]
    {
        metadata.file_type().is_symlink()
    }
}
fn read_seed(path: &Path, expected: &str) -> Result<Vec<u8>, AnyError> {
    for ancestor in path.ancestors() {
        if is_link(&fs::symlink_metadata(ancestor)?) {
            return Err("linked seed rejected".into());
        }
    }
    let m = fs::metadata(path)?;
    if !m.is_file() || m.len() == 0 || m.len() > 4 * 1024 * 1024 {
        return Err("seed bound rejected".into());
    }
    let bytes = fs::read(path)?;
    if archive::sha256(&bytes) != expected {
        return Err("seed identity changed".into());
    }
    Ok(bytes)
}
fn output_argument(root: &Path) -> Result<PathBuf, AnyError> {
    let mut args = env::args_os().skip(1);
    let output = PathBuf::from(args.next().ok_or("new output required")?);
    if args.next().is_some() || !output.is_absolute() || output.exists() {
        return Err("new absolute output required".into());
    }
    let parent = output.parent().ok_or("missing parent")?;
    for ancestor in parent.ancestors() {
        if is_link(&fs::symlink_metadata(ancestor)?) {
            return Err("linked output rejected".into());
        }
    }
    if parent.canonicalize()? != root.join("fixtures/target-build").canonicalize()? {
        return Err("output must be a direct fixture child".into());
    }
    Ok(parent.join(output.file_name().ok_or("missing output name")?))
}
