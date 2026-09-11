use std::env;
use std::error::Error;
use std::fmt::Write as _;
use std::io::{Cursor, Read, Write};
use std::path::{Path, PathBuf};

use domain_ir::MathAstDraft;
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditParseRequestDraft,
};
use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    AtomicPackagePublisher, BoundedZipReader, EQUATION_HWPX_PROFILE_ID,
    EQUATION_HWPX_SCHEMA_VERSION, EquationExtent, EquationExtentSource, EquationHwpxBuilder,
    EquationHwpxLimits, EquationHwpxLowerer, EquationHwpxRequest, EquationHwpxRequestDraft,
    EquationLayout, EquationStyle, Hancom2020Vs0Builder, IdIndexLimits, PackageGraph,
    PackageGraphLimits, PackageLimits, PreservingWriter, WriterLimits,
};
use serde_json::json;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{DateTime, ZipArchive, ZipWriter};

const SECTION_PATH: &str = "Contents/section0.xml";
const OUTPUT_RELATIVE: &str = "p07-05-native-equation-before.hwpx";
const VISIBLE_TEXT: &str = "P07-05 NATIVE EQUATION";
const OBJECT_ID: u32 = 2_200_000_001;
const SCRIPT: &str = "sum _{i=1} ^{32} {i^2} + int _0 ^1 {x^4 + 3x^2 + 1} dx = 10416";
const MAX_BASE_BYTES: usize = 2 * 1024 * 1024;
const MAX_PART_BYTES: usize = 1024 * 1024;
const MAX_PARTS: usize = 32;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let workspace_root = PathBuf::from(arguments.next().ok_or("workspace root is required")?);
    if arguments.next().is_some() {
        return Err("too many arguments".into());
    }

    let source_bytes = build_source()?;
    let mut reader = BoundedZipReader::open(
        Cursor::new(source_bytes.as_slice()),
        PackageLimits::default(),
    )?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let limits = EquationHwpxLimits::default();
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        1,
        0,
        EquationLayout::Display,
        limits,
    )?;
    let before_flow = digest_label(b"p07-05-target-flow-before");
    let after_flow = digest_label(b"p07-05-target-flow-after");
    let parsed = EqEditEngine::new(limits.eqedit, limits.math)?.parse(EqEditParseRequestDraft {
        schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
        profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
        source: SCRIPT.to_owned(),
    })?;
    let math_ast: MathAstDraft =
        serde_json::from_slice(&parsed.ast().canonical_json(limits.math)?)?;
    let request = EquationHwpxRequest::from_draft(
        EquationHwpxRequestDraft {
            schema_version: EQUATION_HWPX_SCHEMA_VERSION.to_owned(),
            profile_id: EQUATION_HWPX_PROFILE_ID.to_owned(),
            section_part: source.section_part().to_owned(),
            paragraph_ordinal: 1,
            run_ordinal: 0,
            expected_package_state_sha256: source.package_state_sha256().to_owned(),
            expected_section_sha256: source.section_sha256().to_owned(),
            expected_paragraph_sha256: source.paragraph_sha256().to_owned(),
            expected_run_sha256: source.run_sha256().to_owned(),
            expected_object_ids_sha256: source.object_ids_sha256().to_owned(),
            expected_document_flow_sha256: before_flow.clone(),
            target_document_flow_sha256: after_flow,
            object_id: OBJECT_ID,
            layout: EquationLayout::Display,
            style: EquationStyle::default(),
            extent: EquationExtent {
                width_hwpunit: 17_000,
                height_hwpunit: 6_000,
                source: EquationExtentSource::Provisional,
                source_evidence_sha256: None,
                render_required: true,
            },
            math_ast,
        },
        &source,
        &before_flow,
        limits,
    )?;
    let lowered = EquationHwpxLowerer::lower(&mut reader, &graph, &request, &before_flow, limits)?;
    let lowering_json = lowered.receipt().canonical_json(limits)?;
    let artifact = PreservingWriter::build(
        lowered.patch(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    let workspace = SecureWorkspace::create(&workspace_root)?;
    let publication = AtomicPackagePublisher::publish(
        &artifact,
        &workspace,
        Path::new("p07-05/native-equation-before.hwpx"),
        Path::new(OUTPUT_RELATIVE),
    )?;
    let result = json!({
        "schema_version": "hwpx-agent.p07-05-equation-target-fixture/v1",
        "state": "pass",
        "output_relative": publication.output_relative().to_string_lossy(),
        "output_sha256": hex(publication.sha256()),
        "output_bytes": publication.size_bytes(),
        "visible_text_sha256": digest_label(VISIBLE_TEXT.as_bytes()),
        "object_id": OBJECT_ID,
        "semantic_sha256": request.semantic_sha256(),
        "lowering_receipt": serde_json::from_slice::<serde_json::Value>(&lowering_json)?,
        "actual_hangul_2020": false,
        "save_reopen": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run"
    });
    println!("{}", serde_json::to_string(&result)?);
    Ok(())
}

fn build_source() -> Result<Vec<u8>, Box<dyn Error>> {
    let base = Hancom2020Vs0Builder::build(VISIBLE_TEXT)?;
    let bytes = base.with_verified_bytes(<[u8]>::to_vec)?;
    if bytes.len() > MAX_BASE_BYTES {
        return Err("base artifact exceeds target-fixture limit".into());
    }
    let mut archive = ZipArchive::new(Cursor::new(bytes))?;
    if archive.is_empty() || archive.len() > MAX_PARTS {
        return Err("base artifact part count is invalid".into());
    }
    let mut parts = Vec::with_capacity(archive.len());
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        if entry.size() > MAX_PART_BYTES as u64 || entry.name().contains('\\') {
            return Err("base artifact part is outside fixture policy".into());
        }
        let mut part = Vec::new();
        entry.read_to_end(&mut part)?;
        let method = entry.compression();
        let name = entry.name().to_owned();
        if name == SECTION_PATH {
            part = insert_empty_equation_paragraph(&part)?;
        }
        parts.push((name, part, method));
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, part, method) in parts {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default());
        writer.start_file(name, options)?;
        writer.write_all(&part)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn insert_empty_equation_paragraph(section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(section)?;
    let closing = source
        .rfind("</hs:sec>")
        .ok_or("section closing tag is missing")?;
    if source.contains("<hp:equation ") || source.contains("<hp:p id=\"2\"") {
        return Err("base section already owns the target identity".into());
    }
    let paragraph = concat!(
        "<hp:p id=\"2\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" ",
        "columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\"><hp:t/>",
        "</hp:run></hp:p>"
    );
    let mut output = String::with_capacity(source.len() + paragraph.len());
    output.push_str(&source[..closing]);
    output.push_str(paragraph);
    output.push_str(&source[closing..]);
    Ok(output.into_bytes())
}

fn digest_label(value: &[u8]) -> String {
    hex(Sha256::digest(value).into())
}

fn hex(value: [u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in value {
        let _ = write!(output, "{byte:02x}");
    }
    output
}
