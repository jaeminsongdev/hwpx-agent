//! Complete-package campaign preparation only: never creates a COM session.
#[allow(dead_code)]
#[path = "p08_19_support/common.rs"]
mod archive;

use std::collections::BTreeMap;
use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{
    FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldCacheStatus, FieldCachedResult, FieldDefinition,
    FieldDocumentState, FieldDocumentStateDraft, FieldEngineBuilder, FieldEngineLimitConfig,
    FieldEngineLimits, FieldIdentity, FieldNumberFormat, FieldOperation, FieldRequest,
    FieldRequestDraft, FieldState, FieldUpdatePolicy, LogicalId, ObjectNumberKind,
};
use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    BoundedZipReader, FieldAutoNumberHwpxLimitConfig, FieldAutoNumberHwpxLimits,
    FieldObjectCaptionHwpxBuilder, FieldObjectCaptionHwpxContext, FieldObjectCaptionHwpxLowerer,
    FieldObjectCaptionHwpxReader, FieldObjectCaptionHwpxTarget, PackageGraph, PackageGraphLimits,
    PackageLimits, PreservingXmlDocument, XmlElementToken,
};
use serde::Serialize;

type AnyError = Box<dyn Error>;
const PARA_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CACHED_NUMBER: i64 = 19;
const MAX_FILE: u64 = 32 * 1024 * 1024;
const CAPTION_SEED: &str = "fixtures/target-build/p08-19-object-target-complete-20260914-02/output/obj-019-margin-caption.hwpx";
const CAPTION_SEED_SHA256: &str =
    "659b31bc1f5f86ee46756ea683258e03ba75515179af2f5377a953a108eafbf7";

#[derive(Clone, Copy)]
struct Seed {
    case_id: &'static str,
    relative: &'static str,
    sha256: &'static str,
    tag: &'static str,
    kind: ObjectNumberKind,
    native_id: u32,
    file: &'static str,
}

const SEEDS: [Seed; 4] = [
    Seed {
        case_id: "P09-19-C01",
        relative: CAPTION_SEED,
        sha256: CAPTION_SEED_SHA256,
        tag: "rect",
        kind: ObjectNumberKind::Picture,
        native_id: 8101,
        file: "p09-19-c01-rectangle-caption-number.hwpx",
    },
    Seed {
        case_id: "P09-19-C02",
        relative: "fixtures/target-build/p08-18-object-insert-target-20260914-02/output/obj-002-image-insert.hwpx",
        sha256: "e7a202dd4ff75e0cda74681e99d8aec4c490a68189f8c0d658a2b2ea764d857c",
        tag: "pic",
        kind: ObjectNumberKind::Picture,
        native_id: 8102,
        file: "p09-19-c02-picture-caption-number.hwpx",
    },
    Seed {
        case_id: "P09-19-C03",
        relative: "fixtures/target-build/p06-09-table-create-target-20260913-06/table-001-create-3x4-nonuniform.hwpx",
        sha256: "b6d000efb0076f3b63ea7247601e8efc366f215f91c5d35927ca92de5c7b8021",
        tag: "tbl",
        kind: ObjectNumberKind::Table,
        native_id: 1_188_510_574,
        file: "p09-19-c03-table-caption-number.hwpx",
    },
    Seed {
        case_id: "P09-19-C04",
        relative: "implementation/p07/evidence/private/p07-09-20260912-attempt14/after.hwpx",
        sha256: "a774bf918c5bd57a1b86531e34ea6bc6f62d4b41d74213090358b657a38f224d",
        tag: "equation",
        kind: ObjectNumberKind::Equation,
        native_id: 1_192_022_476,
        file: "p09-19-c04-equation-caption-number.hwpx",
    },
];

#[derive(Serialize)]
struct CaseManifest {
    case_id: &'static str,
    feature_ids: [&'static str; 2],
    file: &'static str,
    source_relative: &'static str,
    source_package_sha256: &'static str,
    source_section_sha256: String,
    prepared_caption_section_sha256: String,
    fixture_caption_attached_from_seed: bool,
    fixture_none_numbering_type_assigned: bool,
    object_tag: &'static str,
    native_object_id: u32,
    numbering_type: &'static str,
    object_counts: BTreeMap<String, usize>,
    input_cached_number: i64,
    expected_saved_number: i64,
    expectation_basis: &'static str,
    output_package_sha256: String,
    output_package_bytes: usize,
    output_section_sha256: String,
    composition_plan_sha256: String,
    inner_plan_sha256: String,
    caption_sha256: String,
    unrelated_parts_sha256: BTreeMap<String, String>,
    non_field_section_restores_to_seed: bool,
    retry_checks: RetryChecks,
}

#[derive(Serialize)]
struct RetryChecks {
    stale_source_rejected: bool,
    deterministic_retry: bool,
}

#[derive(Serialize)]
struct StaticEvidence {
    complete_package_graph: bool,
    original_object_payloads_and_resources_preserved: bool,
    cached_result_is_not_target_recalculation_proof: bool,
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    task: &'static str,
    caption_seed_relative: &'static str,
    caption_seed_package_sha256: &'static str,
    cases: Vec<CaseManifest>,
    static_evidence: StaticEvidence,
    fixture_caption_attachment_is_not_product_caption_creation: bool,
    actual_hangul: bool,
    semantic_save_reopen: &'static str,
    render: &'static str,
    differential: &'static str,
    green_rows: usize,
    product_complete: bool,
}

fn main() -> Result<(), AnyError> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?;
    let output = output_argument(&root)?;
    let caption_package = read_seed(&root, CAPTION_SEED, CAPTION_SEED_SHA256)?;
    let caption_section = archive::section_from_package(&caption_package)?;
    let caption = extracted_caption(&caption_section)?;
    let mut cases = Vec::new();
    let mut packages = Vec::new();
    for seed in SEEDS {
        let source = read_seed(&root, seed.relative, seed.sha256)?;
        let (package, case) = build_case(seed, &source, &caption)
            .map_err(|error| std::io::Error::other(format!("{}: {error}", seed.case_id)))?;
        let (retry, retry_case) = build_case(seed, &source, &caption)?;
        if retry != package || serde_json::to_vec(&case)? != serde_json::to_vec(&retry_case)? {
            return Err("fixture generation is not byte deterministic".into());
        }
        packages.push(package);
        cases.push(case);
    }
    let manifest = Manifest {
        schema_version: "hwpx-agent.p09-object-caption-number-target-fixture/v1",
        task: "P09-19",
        caption_seed_relative: CAPTION_SEED,
        caption_seed_package_sha256: CAPTION_SEED_SHA256,
        cases,
        static_evidence: StaticEvidence {
            complete_package_graph: true,
            original_object_payloads_and_resources_preserved: true,
            cached_result_is_not_target_recalculation_proof: true,
        },
        fixture_caption_attachment_is_not_product_caption_creation: true,
        actual_hangul: false,
        semantic_save_reopen: "not_run",
        render: "not_run",
        differential: "not_run",
        green_rows: 0,
        product_complete: false,
    };
    let manifest_bytes = serde_json::to_vec_pretty(&manifest)?;
    // Publish only after all source, retry, preservation and graph checks pass.
    let workspace = SecureWorkspace::create(&output)?;
    for (case, bytes) in manifest.cases.iter().zip(packages.iter()) {
        let staged = workspace.stage_bytes(&Path::new("p09-19").join(case.file), bytes)?;
        workspace.publish(&staged, Path::new(case.file))?;
    }
    let staged = workspace.stage_bytes(Path::new("p09-19/manifest.json"), &manifest_bytes)?;
    workspace.publish(&staged, Path::new("fixture-manifest.json"))?;
    println!(
        "{}",
        serde_json::json!({
            "state": "pass", "cases": manifest.cases.len(),
            "manifest_sha256": archive::sha256(&manifest_bytes), "output": output,
            "actual_hangul": false, "green_rows": 0
        })
    );
    Ok(())
}

fn build_case(
    seed: Seed,
    source: &[u8],
    caption: &[u8],
) -> Result<(Vec<u8>, CaseManifest), AnyError> {
    let section = archive::section_from_package(source)?;
    let (numbered, assigned) = prepare_numbering_type(&section, seed)?;
    let (prepared, attached) = prepare_caption(&numbered, seed, caption)?;
    let counts = object_counts(&section)?;
    assert_first_numbered_object(&section, seed)?;
    let target = FieldObjectCaptionHwpxTarget {
        logical_object_id: LogicalId::parse(seed.case_id)?,
        native_object_id: seed.native_id,
        object_kind: seed.kind,
    };
    let (field_section, plan_hash, inner_hash, caption_hash, stale_rejected) =
        insert_number(&prepared, &target, source)?;
    let mut restored = remove_fixture_changes(&field_section, &prepared, attached)?;
    if assigned {
        restored = replace_numbering_type(&restored, seed, "NONE")?;
    }
    if restored != section {
        return Err("non-field bytes do not restore exactly to the original seed".into());
    }
    let package = archive::package_with_section(source, &field_section)?;
    let source_parts = package_inventory(source)?;
    let output_parts = package_inventory(&package)?;
    if source_parts != output_parts {
        return Err("unrelated package parts differ".into());
    }
    let case = CaseManifest {
        case_id: seed.case_id,
        feature_ids: ["REF-008", "REF-009"],
        file: seed.file,
        source_relative: seed.relative,
        source_package_sha256: seed.sha256,
        source_section_sha256: archive::sha256(&section),
        prepared_caption_section_sha256: archive::sha256(&prepared),
        fixture_caption_attached_from_seed: attached,
        fixture_none_numbering_type_assigned: assigned,
        object_tag: seed.tag,
        native_object_id: seed.native_id,
        numbering_type: kind_name(seed.kind),
        object_counts: counts,
        input_cached_number: CACHED_NUMBER,
        expected_saved_number: 1,
        expectation_basis: "first_object_of_its_category_in_isolated_seed_model_hypothesis_target_unqualified",
        output_package_sha256: archive::sha256(&package),
        output_package_bytes: package.len(),
        output_section_sha256: archive::sha256(&field_section),
        composition_plan_sha256: plan_hash,
        inner_plan_sha256: inner_hash,
        caption_sha256: caption_hash,
        unrelated_parts_sha256: source_parts,
        non_field_section_restores_to_seed: true,
        retry_checks: RetryChecks {
            stale_source_rejected: stale_rejected,
            deterministic_retry: true,
        },
    };
    Ok((package, case))
}

fn insert_number(
    source: &[u8],
    target: &FieldObjectCaptionHwpxTarget,
    package: &[u8],
) -> Result<(Vec<u8>, String, String, String, bool), AnyError> {
    let limits = FieldEngineLimits::new(FieldEngineLimitConfig::default())?;
    let hwpx = FieldAutoNumberHwpxLimits::new(FieldAutoNumberHwpxLimitConfig::default())?;
    let source_flow = archive::sha256(source);
    let after_flow = archive::sha256(&[source, b"p09-19-number-insertion"].concat());
    let package_hash = archive::sha256(package);
    let empty_hash = archive::sha256(b"");
    let state = empty_state(&source_flow, &package_hash, limits)?;
    let (paragraph_style_sha256, character_style_sha256) =
        FieldObjectCaptionHwpxReader::style_sha256_at(source, target, 0, 0, hwpx)
            .map_err(|error| std::io::Error::other(format!("caption style: {error}")))?;
    let paragraph = LogicalId::parse("p09-19-caption-paragraph")?;
    let field = FieldState {
        identity: FieldIdentity {
            logical_field_id: LogicalId::parse("p09-19-caption-field")?,
            native_begin_id: 20_000,
            native_end_id: 20_001,
        },
        anchor: FieldAnchor {
            paragraph_id: paragraph.clone(),
            run_ordinal: 0,
            inline_ordinal: 0,
        },
        definition: FieldDefinition::ObjectNumber {
            object_kind: target.object_kind,
            format: FieldNumberFormat::Digit,
        },
        cached_result: FieldCachedResult::Number {
            value: CACHED_NUMBER,
            display: CACHED_NUMBER.to_string(),
        },
        update_policy: FieldUpdatePolicy::RecomputeDirect,
        cache_status: FieldCacheStatus::Current,
        locked: false,
        evaluation_context_sha256: None,
        paragraph_style_sha256,
        character_style_sha256,
        field_payload_sha256: empty_hash,
        opaque_properties: Vec::new(),
    };
    let request = FieldRequest::from_draft(
        FieldRequestDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p09-19-insert-request")?,
            expected_source_state_sha256: state.canonical_sha256(limits)?,
            expected_document_flow_sha256: source_flow.clone(),
            target_document_flow_sha256: after_flow,
            operation: FieldOperation::Insert {
                insertion_index: 0,
                field,
            },
        },
        &state,
        &source_flow,
        limits,
    )?;
    let domain = FieldEngineBuilder::plan(&state, &request, &source_flow, limits)?;
    let map = [paragraph];
    let context = FieldObjectCaptionHwpxContext {
        target,
        state: &state,
        document_flow_sha256: &source_flow,
        caption_paragraph_ids: &map,
        state_limits: limits,
        hwpx_limits: hwpx,
    };
    let plan = FieldObjectCaptionHwpxBuilder::plan(source, &context, &domain)
        .map_err(|error| std::io::Error::other(format!("caption plan: {error}")))?;
    let (output, receipt) =
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(source, &plan, &context)?;
    let retry =
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(source, &plan, &context)?.0;
    if retry != output {
        return Err("lowerer retry differs".into());
    }
    let readback = FieldObjectCaptionHwpxReader::read_section(
        &output,
        &FieldObjectCaptionHwpxContext {
            state: domain.target_state(),
            document_flow_sha256: domain.target_document_flow_sha256(),
            ..context
        },
    )?;
    if readback.auto_number_count != 1 {
        return Err("caption field count differs".into());
    }
    let mut drifted = source.to_vec();
    drifted.push(b' ');
    let rejected =
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(&drifted, &plan, &context)
            .is_err();
    if !rejected {
        return Err("stale source accepted".into());
    }
    Ok((
        output,
        receipt.plan_sha256,
        receipt.inner.plan_sha256,
        archive::hex(receipt.output_caption_sha256),
        rejected,
    ))
}

fn empty_state(
    flow: &str,
    package: &str,
    limits: FieldEngineLimits,
) -> Result<FieldDocumentState, AnyError> {
    Ok(FieldDocumentState::from_draft(
        FieldDocumentStateDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            fields: Vec::new(),
            non_field_content_sha256: flow.to_owned(),
            style_catalog_sha256: package.to_owned(),
            reference_inventory_sha256: archive::sha256(b""),
            resource_inventory_sha256: package.to_owned(),
            opaque_document_state_sha256: package.to_owned(),
        },
        limits,
    )?)
}

fn named(element: &XmlElementToken, name: &str) -> bool {
    element.name().namespace() == Some(PARA_NS) && element.name().local_name() == name
}

fn native_id(element: &XmlElementToken, source: &[u8]) -> Result<u32, AnyError> {
    let span = element
        .attributes()
        .iter()
        .find(|attribute| {
            attribute.name().namespace().is_none() && attribute.name().local_name() == "id"
        })
        .ok_or("native object ID missing")?
        .value_span();
    let id = std::str::from_utf8(&source[span.start()..span.end()])?;
    let value: u32 = id.parse()?;
    if value.to_string() != id {
        return Err("noncanonical native ID".into());
    }
    Ok(value)
}

fn prepare_numbering_type(source: &[u8], seed: Seed) -> Result<(Vec<u8>, bool), AnyError> {
    let span = numbering_span(source, seed)?;
    let current = std::str::from_utf8(&source[span.start()..span.end()])?;
    if current == kind_name(seed.kind) {
        return Ok((source.to_vec(), false));
    }
    if current != "NONE" {
        return Err("seed numbering type is not NONE or the expected kind".into());
    }
    Ok((
        replace_numbering_type(source, seed, kind_name(seed.kind))?,
        true,
    ))
}

fn numbering_span(source: &[u8], seed: Seed) -> Result<hwpx_package::XmlByteSpan, AnyError> {
    let document = PreservingXmlDocument::parse(source)?;
    let candidates: Vec<_> = document
        .elements()
        .iter()
        .filter(|element| {
            named(element, seed.tag) && native_id(element, source).ok() == Some(seed.native_id)
        })
        .collect();
    let [object] = candidates.as_slice() else {
        return Err("numbering target is not unique".into());
    };
    let attribute = object
        .attributes()
        .iter()
        .find(|attribute| {
            attribute.name().namespace().is_none()
                && attribute.name().local_name() == "numberingType"
        })
        .ok_or("numbering type missing")?;
    Ok(attribute.value_span())
}

fn replace_numbering_type(source: &[u8], seed: Seed, value: &str) -> Result<Vec<u8>, AnyError> {
    if value != "NONE" && value != kind_name(seed.kind) {
        return Err("unqualified numbering type".into());
    }
    let span = numbering_span(source, seed)?;
    let mut output = source[..span.start()].to_vec();
    output.extend_from_slice(value.as_bytes());
    output.extend_from_slice(&source[span.end()..]);
    Ok(output)
}

fn extracted_caption(source: &[u8]) -> Result<Vec<u8>, AnyError> {
    let document = PreservingXmlDocument::parse(source)?;
    let captions: Vec<_> = document
        .elements()
        .iter()
        .filter(|element| named(element, "caption"))
        .collect();
    let [caption] = captions.as_slice() else {
        return Err("caption seed not unique".into());
    };
    let span = caption.outer_span().ok_or("caption span missing")?;
    Ok(source[span.start()..span.end()].to_vec())
}

fn prepare_caption(source: &[u8], seed: Seed, caption: &[u8]) -> Result<(Vec<u8>, bool), AnyError> {
    let document = PreservingXmlDocument::parse(source)?;
    let candidates: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, element)| named(element, seed.tag))
        .filter_map(|(index, element)| {
            (native_id(element, source).ok() == Some(seed.native_id)).then_some((index, element))
        })
        .collect();
    let [(index, object)] = candidates.as_slice() else {
        return Err("selected object not unique".into());
    };
    if object.name().prefix() != Some("hp") {
        return Err("fixture seed prefix is not qualified".into());
    }
    let existing: Vec<_> = document
        .elements()
        .iter()
        .filter(|element| element.parent() == Some(*index) && named(element, "caption"))
        .collect();
    if existing.len() == 1 {
        return Ok((source.to_vec(), false));
    }
    if !existing.is_empty() {
        return Err("caption is ambiguous".into());
    }
    let insertion = object
        .end_tag_span()
        .ok_or("object end tag missing")?
        .start();
    let mut output = source[..insertion].to_vec();
    output.extend_from_slice(caption);
    output.extend_from_slice(&source[insertion..]);
    PreservingXmlDocument::parse(&output)?.verify_untouched_round_trip()?;
    Ok((output, true))
}

fn remove_fixture_changes(
    source: &[u8],
    prepared: &[u8],
    attached: bool,
) -> Result<Vec<u8>, AnyError> {
    let document = PreservingXmlDocument::parse(source)?;
    let fields: Vec<_> = document
        .elements()
        .iter()
        .filter(|element| named(element, "autoNum"))
        .collect();
    let [field] = fields.as_slice() else {
        return Err("number control not unique".into());
    };
    let parent = document
        .elements()
        .get(field.parent().ok_or("field parent missing")?)
        .ok_or("field parent invalid")?;
    if !named(parent, "ctrl") {
        return Err("field wrapper not qualified".into());
    }
    let span = parent.outer_span().ok_or("field wrapper span missing")?;
    let mut restored = source.to_vec();
    restored.drain(span.start()..span.end());
    if restored != prepared {
        return Err("field insert reversal differs".into());
    }
    if attached {
        let caption = extracted_caption(&restored)?;
        let position = restored
            .windows(caption.len())
            .position(|value| value == caption)
            .ok_or("caption not found")?;
        restored.drain(position..position + caption.len());
    }
    Ok(restored)
}

fn object_counts(source: &[u8]) -> Result<BTreeMap<String, usize>, AnyError> {
    let document = PreservingXmlDocument::parse(source)?;
    let mut counts = BTreeMap::new();
    for element in document.elements() {
        if ["rect", "pic", "tbl", "equation"]
            .iter()
            .any(|name| named(element, name))
        {
            *counts
                .entry(element.name().local_name().to_owned())
                .or_insert(0) += 1;
        }
    }
    Ok(counts)
}

fn assert_first_numbered_object(source: &[u8], seed: Seed) -> Result<(), AnyError> {
    let document = PreservingXmlDocument::parse(source)?;
    let first = document
        .elements()
        .iter()
        .find(|element| {
            element.name().namespace() == Some(PARA_NS)
                && match seed.kind {
                    ObjectNumberKind::Picture => matches!(
                        element.name().local_name(),
                        "pic"
                            | "rect"
                            | "ellipse"
                            | "line"
                            | "arc"
                            | "polygon"
                            | "curve"
                            | "connectLine"
                    ),
                    ObjectNumberKind::Table => named(element, "tbl"),
                    ObjectNumberKind::Equation => named(element, "equation"),
                }
        })
        .ok_or("numbered object missing")?;
    if native_id(first, source)? != seed.native_id {
        return Err("target is not the first object of its category".into());
    }
    Ok(())
}

fn kind_name(kind: ObjectNumberKind) -> &'static str {
    match kind {
        ObjectNumberKind::Picture => "PICTURE",
        ObjectNumberKind::Table => "TABLE",
        ObjectNumberKind::Equation => "EQUATION",
    }
}

fn package_inventory(package: &[u8]) -> Result<BTreeMap<String, String>, AnyError> {
    let mut reader = BoundedZipReader::open(Cursor::new(package), PackageLimits::default())?;
    PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let entries: Vec<_> = reader
        .entries()
        .iter()
        .map(|entry| (entry.index, entry.path.as_str().to_owned()))
        .collect();
    let mut parts = BTreeMap::new();
    for (index, name) in entries {
        if name == archive::SECTION_PATH {
            continue;
        }
        let bytes = reader.read_entry(index)?;
        if parts.insert(name, archive::sha256(&bytes)).is_some() {
            return Err("duplicate package part".into());
        }
    }
    Ok(parts)
}

fn read_seed(root: &Path, relative: &str, expected: &str) -> Result<Vec<u8>, AnyError> {
    let mut path = root.to_path_buf();
    for component in Path::new(relative).components() {
        if !matches!(component, std::path::Component::Normal(_)) {
            return Err("seed path outside root".into());
        }
        path.push(component);
        if is_link(&fs::symlink_metadata(&path)?) {
            return Err("linked seed path".into());
        }
    }
    let metadata = fs::metadata(&path)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > MAX_FILE {
        return Err("seed file exceeds bound".into());
    }
    let bytes = fs::read(&path)?;
    if u64::try_from(bytes.len())? > MAX_FILE || archive::sha256(&bytes) != expected {
        return Err("seed identity changed".into());
    }
    Ok(bytes)
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

fn output_argument(root: &Path) -> Result<PathBuf, AnyError> {
    let mut arguments = env::args_os().skip(1);
    let output = PathBuf::from(arguments.next().ok_or("new output directory required")?);
    if arguments.next().is_some() || !output.is_absolute() || output.exists() {
        return Err("output must be a new absolute directory".into());
    }
    let parent = output
        .parent()
        .ok_or("output parent missing")?
        .canonicalize()?;
    let allowed = root.join("fixtures/target-build").canonicalize()?;
    if parent != allowed {
        return Err("output must be a direct child of fixtures/target-build".into());
    }
    if output
        .components()
        .any(|part| matches!(part, std::path::Component::ParentDir))
    {
        return Err("output traversal rejected".into());
    }
    Ok(parent.join(output.file_name().ok_or("output name missing")?))
}
