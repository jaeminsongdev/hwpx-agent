//! Exact-profile identity rebinding for the fixed P05-07 Hangul 2020 fixture.
//!
//! This is deliberately narrower than a cross-backend normalizer. It cannot rewrite a package,
//! publish a revision, accept a changed semantic value, or treat an empty backend ID as a key.

use std::collections::HashSet;
use std::error::Error;
use std::ffi::OsString;
use std::path::Path;

use hwpx_package::{
    ColumnDefinition, ColumnLayout, ColumnLineType, ColumnLineWidth, ColumnSizing, ColumnType,
    PageGutterType, PageOrientation,
};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

const PDF_LIMIT: u64 = 64 * 1024 * 1024;
const JSON_LIMIT: u64 = 262_144;
const PNG_LIMIT: u64 = 16 * 1024 * 1024;
const EXPECTED_RENDERER: &str = "3f2440140fef98ddd1ef0772a10d8e58dc3564a9b15a14b4611b5bbd5bdcd37f";
const EXPECTED_PYTHON_RUNTIME: &str =
    "dc7ecf75280678175b4f931ce05f1ef9c10d48984399ca7de6beee69d71bcb1b";
const EXPECTED_VERIFIER: &str = "2dd4855b1911a5966828517c2b5953e94792abeb27a6b0c4c214917679553b89";
const LOGICAL_IDS: [&str; 2] = [
    "p05-07-section-column-logical-01",
    "p05-07-section-column-logical-02",
];
const USAGE: &str = concat!(
    "usage: rebind-identity <source.hwpx> <saved.hwpx> <trace.json> <trace-sha256> ",
    "<render.pdf> <pdf-verification.json> <pdf-verification-sha256> ",
    "<expectation.json> <expectation-sha256> <page-1.png> <page-2.png>"
);

pub(super) fn run(arguments: impl Iterator<Item = OsString>) -> Result<(), Box<dyn Error>> {
    let arguments: Vec<_> = arguments.take(12).collect();
    if arguments.len() != 11 {
        return Err(USAGE.into());
    }
    let source = super::read_bounded(Path::new(&arguments[0]), crate::MAX_TARGET_FIXTURE_BYTES)?;
    let saved = super::read_bounded(Path::new(&arguments[1]), crate::MAX_TARGET_FIXTURE_BYTES)?;
    let trace = super::read_bounded(Path::new(&arguments[2]), super::TRACE_LIMIT)?;
    let trace_sha256 = arguments[3].to_str().ok_or(USAGE)?;
    let pdf = super::read_bounded(Path::new(&arguments[4]), PDF_LIMIT)?;
    let pdf_verification = super::read_bounded(Path::new(&arguments[5]), JSON_LIMIT)?;
    let pdf_verification_sha256 = arguments[6].to_str().ok_or(USAGE)?;
    let expectation = super::read_bounded(Path::new(&arguments[7]), JSON_LIMIT)?;
    let expectation_sha256 = arguments[8].to_str().ok_or(USAGE)?;
    let pngs = [
        super::read_bounded(Path::new(&arguments[9]), PNG_LIMIT)?,
        super::read_bounded(Path::new(&arguments[10]), PNG_LIMIT)?,
    ];
    let receipt = issue_receipt(
        &source,
        &saved,
        &trace,
        trace_sha256,
        &pdf,
        &pdf_verification,
        pdf_verification_sha256,
        &expectation,
        expectation_sha256,
        [&pngs[0], &pngs[1]],
    )?;
    println!("{}", serde_json::to_string_pretty(&receipt)?);
    Ok(())
}

#[derive(Serialize)]
#[expect(
    clippy::struct_excessive_bools,
    reason = "Independent preservation, binding, render and publication claims remain explicit"
)]
struct RebindingReceipt {
    schema_version: &'static str,
    state: &'static str,
    scope: &'static str,
    mode: &'static str,
    decision_id: &'static str,
    target_build: &'static str,
    source_sha256: String,
    saved_sha256: String,
    execution_trace_sha256: String,
    pdf_sha256: String,
    pdf_verification_sha256: String,
    expectation_sha256: String,
    rendered_png_sha256: Vec<String>,
    exact_semantic_context_verified: bool,
    identity_binding_verified: bool,
    logical_identity_rebinding_verified: bool,
    backend_identifiers_preserved: bool,
    saved_backend_identifier_absence_admitted: bool,
    render_evidence_bound: bool,
    actual_execution_independently_attested: bool,
    visual_layout_semantics_independently_attested: bool,
    revision_publication_authorized: bool,
    p05_07_identity_subgate: &'static str,
    overall_product_acceptance: &'static str,
    bindings: Vec<IdentityBinding>,
    normalization_events: Vec<NormalizationEvent>,
    raw_document_text_or_backend_ids_present: bool,
}

#[derive(Serialize)]
struct IdentityBinding {
    section_ordinal: usize,
    logical_id: &'static str,
    structural_context_sha256: String,
    source_backend_identifier_sha256: String,
    source_backend_identifier_present: bool,
    saved_backend_identifier_state: &'static str,
    backend_identifier_preserved: bool,
    logical_binding_unique: bool,
}

#[derive(Serialize)]
struct NormalizationEvent {
    section_ordinal: usize,
    logical_id: &'static str,
    event: &'static str,
    source_backend_identifier_sha256: String,
    saved_backend_identifier_state: &'static str,
    structural_context_sha256: String,
    reason: &'static str,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RenderExpectation {
    schema_version: String,
    expected_page_count: usize,
    geometry_tolerance_milli_mm: u32,
    pages: Vec<ExpectedPage>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ExpectedPage {
    index: usize,
    width_milli_mm: u32,
    height_milli_mm: u32,
    rotation: u16,
    required_text: Vec<String>,
    forbidden_text: Vec<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
#[expect(
    clippy::struct_excessive_bools,
    reason = "Exact closed PDF-verifier wire shape; each safety claim is checked independently"
)]
struct PdfVerification {
    schema_version: String,
    state: String,
    error_code: Value,
    pdf_sha256: String,
    pdf_bytes: u64,
    pdf_signature_valid: bool,
    expectation_sha256: String,
    page_count: usize,
    geometry_tolerance_milli_mm: u32,
    render_dpi: u32,
    renderer_sha256: String,
    python_runtime_sha256: String,
    verifier_sha256: String,
    pypdf_version: String,
    pillow_version: String,
    pages: Vec<VerifiedPage>,
    raw_document_text_present: bool,
    user_document_scanned: bool,
    external_network_invoked: bool,
    pdf_modified: bool,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct VerifiedPage {
    index: usize,
    width_milli_mm: u32,
    height_milli_mm: u32,
    rotation: u16,
    extracted_text_sha256: String,
    extracted_text_utf8_bytes: usize,
    required_text_sha256: Vec<String>,
    forbidden_text_sha256: Vec<String>,
    png_sha256: String,
    png_bytes: u64,
    png_width: u32,
    png_height: u32,
}

#[expect(
    clippy::too_many_arguments,
    reason = "Every evidence artifact and caller-supplied digest is an independent binding"
)]
fn issue_receipt(
    source: &[u8],
    saved: &[u8],
    trace_bytes: &[u8],
    trace_sha256: &str,
    pdf: &[u8],
    pdf_verification_bytes: &[u8],
    pdf_verification_sha256: &str,
    expectation_bytes: &[u8],
    expectation_sha256: &str,
    pngs: [&[u8]; 2],
) -> Result<RebindingReceipt, Box<dyn Error>> {
    require_digest(trace_sha256)?;
    require_digest(pdf_verification_sha256)?;
    require_digest(expectation_sha256)?;
    if super::digest(pdf_verification_bytes) != pdf_verification_sha256
        || super::digest(expectation_bytes) != expectation_sha256
    {
        return Err("P05_07_REBIND_EVIDENCE_DIGEST_MISMATCH".into());
    }

    let diagnostic = super::diagnose(source, saved, trace_bytes, trace_sha256)?;
    let trace: super::Trace =
        serde_json::from_slice(trace_bytes).map_err(|_| "P05_07_REBIND_TRACE_SHAPE_INVALID")?;
    let expectation: RenderExpectation = serde_json::from_slice(expectation_bytes)
        .map_err(|_| "P05_07_REBIND_EXPECTATION_SHAPE_INVALID")?;
    let verification: PdfVerification = serde_json::from_slice(pdf_verification_bytes)
        .map_err(|_| "P05_07_REBIND_PDF_EVIDENCE_SHAPE_INVALID")?;
    validate_render_evidence(
        &trace,
        pdf,
        &expectation,
        expectation_sha256,
        &verification,
        pngs,
    )?;

    let (bindings, normalization_events) = build_identity_bindings(source, saved, &diagnostic)?;

    let all_preserved = normalization_events.is_empty();
    Ok(RebindingReceipt {
        schema_version: "hwpx-agent.p05-07-identity-rebinding-receipt/v1",
        state: "pass",
        scope: "fixed_synthetic_fixture_current_hangul_2020_build_only",
        mode: "native_automation_bounded_normalization",
        decision_id: "P05-07-H2020-COLPR-ID-ABSENCE-V1",
        target_build: super::BUILD,
        source_sha256: super::digest(source),
        saved_sha256: super::digest(saved),
        execution_trace_sha256: super::digest(trace_bytes),
        pdf_sha256: super::digest(pdf),
        pdf_verification_sha256: super::digest(pdf_verification_bytes),
        expectation_sha256: super::digest(expectation_bytes),
        rendered_png_sha256: pngs.iter().map(|png| super::digest(png)).collect(),
        exact_semantic_context_verified: true,
        identity_binding_verified: true,
        logical_identity_rebinding_verified: !all_preserved,
        backend_identifiers_preserved: all_preserved,
        saved_backend_identifier_absence_admitted: !all_preserved,
        render_evidence_bound: true,
        actual_execution_independently_attested: false,
        visual_layout_semantics_independently_attested: false,
        revision_publication_authorized: false,
        p05_07_identity_subgate: "pass_for_exact_fixture_and_build",
        overall_product_acceptance: "not_granted_remaining_p05_gates",
        bindings,
        normalization_events,
        raw_document_text_or_backend_ids_present: false,
    })
}

fn non_identity_checks_pass(section: &super::SectionComparison) -> bool {
    section.source_page_matches_target
        && section.saved_page_matches_target
        && section.page_values_equal
        && section.source_columns_admitted_at_actual_body_width
        && section.saved_columns_admitted_at_actual_body_width
        && section.source_columns_admitted_in_target_frame
        && section.saved_columns_admitted_in_target_frame
        && section.column_values_equal_excluding_ids
        && section.source_column_values_match_target
        && section.saved_column_values_match_target
        && section.source_control_id_matches_target
        && section.source_text_matches_target
        && section.saved_text_matches_target
        && section.text_values_equal
}

fn build_identity_bindings(
    source: &[u8],
    saved: &[u8],
    diagnostic: &super::DiagnosticReport,
) -> Result<(Vec<IdentityBinding>, Vec<NormalizationEvent>), Box<dyn Error>> {
    if diagnostic.sections.len() != 2
        || diagnostic
            .sections
            .iter()
            .any(|section| !non_identity_checks_pass(section))
    {
        return Err("P05_07_REBIND_SEMANTIC_CONTEXT_MISMATCH".into());
    }
    let source_snapshots =
        super::snapshot(source).map_err(|_| "P05_07_REBIND_SOURCE_STRUCTURE_INVALID")?;
    let saved_snapshots =
        super::snapshot(saved).map_err(|_| "P05_07_REBIND_SAVED_STRUCTURE_INVALID")?;
    let target_columns = [crate::section_one_columns(), crate::section_two_columns()];
    let mut fingerprints = HashSet::with_capacity(2);
    let mut identifier_hashes = HashSet::with_capacity(2);
    let mut bindings = Vec::with_capacity(2);
    let mut events = Vec::with_capacity(2);

    for ordinal in 0..2 {
        let source_column = super::one_column(&source_snapshots[ordinal])
            .ok_or("P05_07_REBIND_SOURCE_COLUMN_AMBIGUOUS")?;
        let saved_column = super::one_column(&saved_snapshots[ordinal])
            .ok_or("P05_07_REBIND_SAVED_COLUMN_AMBIGUOUS")?;
        if source_column != &target_columns[ordinal]
            || source_column.control_id.is_empty()
            || !super::equal_values(source_column, saved_column)
        {
            return Err("P05_07_REBIND_TARGET_OR_SEMANTIC_MISMATCH".into());
        }
        let source_fingerprint =
            structural_fingerprint(ordinal, &source_snapshots[ordinal], source_column)?;
        let saved_fingerprint =
            structural_fingerprint(ordinal, &saved_snapshots[ordinal], saved_column)?;
        if source_fingerprint != saved_fingerprint {
            return Err("P05_07_REBIND_CONTEXT_MISMATCH".into());
        }
        insert_unique(&mut fingerprints, source_fingerprint.clone())?;
        let source_id_sha256 = super::digest(source_column.control_id.as_bytes());
        insert_unique(&mut identifier_hashes, source_id_sha256.clone())?;
        let preserved = saved_column.control_id == source_column.control_id;
        let removed = saved_column.control_id.is_empty();
        if !preserved && !removed {
            return Err("P05_07_REBIND_UNSUPPORTED_ID_CHANGE".into());
        }
        bindings.push(IdentityBinding {
            section_ordinal: ordinal,
            logical_id: LOGICAL_IDS[ordinal],
            structural_context_sha256: source_fingerprint.clone(),
            source_backend_identifier_sha256: source_id_sha256.clone(),
            source_backend_identifier_present: true,
            saved_backend_identifier_state: if preserved {
                "preserved"
            } else {
                "absent_native_normalization"
            },
            backend_identifier_preserved: preserved,
            logical_binding_unique: true,
        });
        if removed {
            events.push(NormalizationEvent {
                section_ordinal: ordinal,
                logical_id: LOGICAL_IDS[ordinal],
                event: "removed_backend_identifier",
                source_backend_identifier_sha256: source_id_sha256,
                saved_backend_identifier_state: "absent",
                structural_context_sha256: source_fingerprint,
                reason: "hancom_2020_native_save_normalization",
            });
        }
    }
    Ok((bindings, events))
}

fn require_digest(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("P05_07_REBIND_DIGEST_INVALID".into());
    }
    Ok(())
}

fn insert_unique(set: &mut HashSet<String>, value: String) -> Result<(), Box<dyn Error>> {
    if !set.insert(value) {
        return Err("P05_07_REBIND_VALUE_NOT_UNIQUE".into());
    }
    Ok(())
}

fn validate_render_evidence(
    trace: &super::Trace,
    pdf: &[u8],
    expectation: &RenderExpectation,
    expectation_sha256: &str,
    verification: &PdfVerification,
    pngs: [&[u8]; 2],
) -> Result<(), Box<dyn Error>> {
    if !pdf.starts_with(b"%PDF-")
        || !pdf[pdf.len().saturating_sub(1024)..]
            .windows(5)
            .any(|value| value == b"%%EOF")
        || trace.render_pdf_sha256 != super::digest(pdf)
        || trace.render_pdf_bytes != pdf.len() as u64
    {
        return Err("P05_07_REBIND_PDF_BINDING_INVALID".into());
    }
    validate_expectation(expectation)?;
    if verification.schema_version != "hwpx-agent.p05-hancom-pdf-verification/v1"
        || verification.state != "pass"
        || !verification.error_code.is_null()
        || verification.pdf_sha256 != super::digest(pdf)
        || verification.pdf_bytes != pdf.len() as u64
        || !verification.pdf_signature_valid
        || verification.expectation_sha256 != expectation_sha256
        || verification.page_count != 2
        || verification.geometry_tolerance_milli_mm != expectation.geometry_tolerance_milli_mm
        || verification.render_dpi != 144
        || verification.renderer_sha256 != EXPECTED_RENDERER
        || verification.python_runtime_sha256 != EXPECTED_PYTHON_RUNTIME
        || verification.verifier_sha256 != EXPECTED_VERIFIER
        || verification.pypdf_version != "6.13.3"
        || verification.pillow_version != "12.2.0"
        || verification.raw_document_text_present
        || verification.user_document_scanned
        || verification.external_network_invoked
        || verification.pdf_modified
        || verification.pages.len() != 2
    {
        return Err("P05_07_REBIND_PDF_EVIDENCE_INVALID".into());
    }
    for (ordinal, png) in pngs.iter().enumerate() {
        validate_verified_page(
            &verification.pages[ordinal],
            &expectation.pages[ordinal],
            png,
        )?;
    }
    Ok(())
}

fn validate_expectation(expectation: &RenderExpectation) -> Result<(), Box<dyn Error>> {
    let required = [crate::SECTION_ONE_TEXT, crate::SECTION_TWO_TEXT];
    let forbidden = [crate::SECTION_TWO_TEXT, crate::SECTION_ONE_TEXT];
    if expectation.schema_version != "hwpx-agent.p05-render-expectation/v1"
        || expectation.expected_page_count != 2
        || expectation.geometry_tolerance_milli_mm != 500
        || expectation.pages.len() != 2
    {
        return Err("P05_07_REBIND_EXPECTATION_INVALID".into());
    }
    for ordinal in 0..2 {
        let page = &expectation.pages[ordinal];
        if page.index != ordinal + 1
            || page.width_milli_mm != 310_000
            || page.height_milli_mm != 230_000
            || page.rotation != 0
            || page.required_text.as_slice() != [required[ordinal]]
            || page.forbidden_text.as_slice() != [forbidden[ordinal]]
        {
            return Err("P05_07_REBIND_EXPECTATION_TARGET_MISMATCH".into());
        }
    }
    Ok(())
}

fn validate_verified_page(
    page: &VerifiedPage,
    expected: &ExpectedPage,
    png: &[u8],
) -> Result<(), Box<dyn Error>> {
    let required_sha = super::digest(expected.required_text[0].as_bytes());
    let forbidden_sha = super::digest(expected.forbidden_text[0].as_bytes());
    let width_delta = page.width_milli_mm.abs_diff(expected.width_milli_mm);
    let height_delta = page.height_milli_mm.abs_diff(expected.height_milli_mm);
    let (png_width, png_height) = png_dimensions(png)?;
    if page.index != expected.index
        || width_delta > 500
        || height_delta > 500
        || page.rotation != expected.rotation
        || page.extracted_text_sha256 != required_sha
        || page.extracted_text_utf8_bytes != expected.required_text[0].len()
        || page.required_text_sha256.as_slice() != [required_sha]
        || page.forbidden_text_sha256.as_slice() != [forbidden_sha]
        || page.png_sha256 != super::digest(png)
        || page.png_bytes != png.len() as u64
        || page.png_width != png_width
        || page.png_height != png_height
        || page.png_width != 1756
        || page.png_height != 1302
    {
        return Err("P05_07_REBIND_RENDERED_PAGE_INVALID".into());
    }
    Ok(())
}

fn png_dimensions(bytes: &[u8]) -> Result<(u32, u32), Box<dyn Error>> {
    const SIGNATURE: &[u8; 8] = b"\x89PNG\r\n\x1a\n";
    if bytes.len() < 24 || &bytes[..8] != SIGNATURE || &bytes[12..16] != b"IHDR" {
        return Err("P05_07_REBIND_PNG_INVALID".into());
    }
    let width = u32::from_be_bytes(bytes[16..20].try_into()?);
    let height = u32::from_be_bytes(bytes[20..24].try_into()?);
    if width == 0 || height == 0 {
        return Err("P05_07_REBIND_PNG_DIMENSION_INVALID".into());
    }
    Ok((width, height))
}

fn structural_fingerprint(
    ordinal: usize,
    snapshot: &super::SectionSnapshot,
    column: &ColumnDefinition,
) -> Result<String, Box<dyn Error>> {
    let page = snapshot
        .page
        .as_ref()
        .ok_or("P05_07_REBIND_PAGE_AMBIGUOUS")?;
    let sizing = match &column.sizing {
        ColumnSizing::Equal { count, gap } => json!({
            "kind": "equal", "count": count, "gap": gap
        }),
        ColumnSizing::Custom(columns) => json!({
            "kind": "custom",
            "columns": columns.iter().map(|value| json!({
                "width": value.width, "gap": value.gap
            })).collect::<Vec<_>>()
        }),
    };
    let separator = column.separator.map(|value| {
        json!({
            "line_type": line_type(value.line_type),
            "width": line_width(value.width),
            "color": value.color,
        })
    });
    let canonical = json!({
        "schema": "hwpx-agent.p05-07-structural-context/v1",
        "section_ordinal": ordinal,
        "page": {
            "orientation": match page.orientation { PageOrientation::Landscape => "landscape", PageOrientation::Portrait => "portrait" },
            "width": page.dimensions.width,
            "height": page.dimensions.height,
            "gutter_type": match page.gutter_type { PageGutterType::LeftOnly => "left_only", PageGutterType::LeftRight => "left_right", PageGutterType::TopBottom => "top_bottom" },
            "margins": {
                "header": page.margins.header, "footer": page.margins.footer,
                "gutter": page.margins.gutter, "left": page.margins.left,
                "right": page.margins.right, "top": page.margins.top,
                "bottom": page.margins.bottom,
            }
        },
        "column": {
            "type": match column.column_type { ColumnType::Newspaper => "newspaper", ColumnType::BalancedNewspaper => "balanced_newspaper", ColumnType::Parallel => "parallel" },
            "layout": match column.layout { ColumnLayout::Left => "left", ColumnLayout::Right => "right", ColumnLayout::Mirror => "mirror" },
            "sizing": sizing,
            "separator": separator,
        },
        "text_sha256": super::digest(snapshot.text.as_bytes()),
    });
    Ok(super::digest(&serde_json::to_vec(&canonical)?))
}

const fn line_type(value: ColumnLineType) -> &'static str {
    match value {
        ColumnLineType::None => "none",
        ColumnLineType::Solid => "solid",
        ColumnLineType::Dot => "dot",
        ColumnLineType::Dash => "dash",
        ColumnLineType::DashDot => "dash_dot",
        ColumnLineType::DashDotDot => "dash_dot_dot",
        ColumnLineType::LongDash => "long_dash",
        ColumnLineType::Circle => "circle",
        ColumnLineType::DoubleSlim => "double_slim",
        ColumnLineType::SlimThick => "slim_thick",
        ColumnLineType::ThickSlim => "thick_slim",
        ColumnLineType::SlimThickSlim => "slim_thick_slim",
        ColumnLineType::Wave => "wave",
        ColumnLineType::DoubleWave => "double_wave",
        ColumnLineType::Thick3d => "thick_3d",
        ColumnLineType::ThickReverse3d => "thick_reverse_3d",
        ColumnLineType::ThreeD => "3d",
        ColumnLineType::Reverse3d => "reverse_3d",
    }
}

const fn line_width(value: ColumnLineWidth) -> &'static str {
    match value {
        ColumnLineWidth::Mm0_1 => "0.1_mm",
        ColumnLineWidth::Mm0_12 => "0.12_mm",
        ColumnLineWidth::Mm0_15 => "0.15_mm",
        ColumnLineWidth::Mm0_2 => "0.2_mm",
        ColumnLineWidth::Mm0_25 => "0.25_mm",
        ColumnLineWidth::Mm0_3 => "0.3_mm",
        ColumnLineWidth::Mm0_4 => "0.4_mm",
        ColumnLineWidth::Mm0_5 => "0.5_mm",
        ColumnLineWidth::Mm0_6 => "0.6_mm",
        ColumnLineWidth::Mm0_7 => "0.7_mm",
        ColumnLineWidth::Mm1_0 => "1.0_mm",
        ColumnLineWidth::Mm1_5 => "1.5_mm",
        ColumnLineWidth::Mm2_0 => "2.0_mm",
        ColumnLineWidth::Mm3_0 => "3.0_mm",
        ColumnLineWidth::Mm4_0 => "4.0_mm",
        ColumnLineWidth::Mm5_0 => "5.0_mm",
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::diagnostics::tests::{fixture, rewrite, trace_value};

    fn png(width: u32, height: u32) -> Vec<u8> {
        let mut bytes = b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR".to_vec();
        bytes.extend_from_slice(&width.to_be_bytes());
        bytes.extend_from_slice(&height.to_be_bytes());
        bytes.extend_from_slice(&[8, 2, 0, 0, 0, 0, 0, 0, 0]);
        bytes
    }

    fn evidence(
        source: &[u8],
        saved: &[u8],
    ) -> Result<(Vec<u8>, Vec<u8>, Vec<u8>, [Vec<u8>; 2]), Box<dyn Error>> {
        let mut pdf = vec![b' '; 100];
        pdf[..9].copy_from_slice(b"%PDF-1.7\n");
        pdf[94..99].copy_from_slice(b"%%EOF");
        let pngs = [png(1756, 1302), png(1756, 1302)];
        let expectation_value = json!({
            "schema_version": "hwpx-agent.p05-render-expectation/v1",
            "expected_page_count": 2,
            "geometry_tolerance_milli_mm": 500,
            "pages": [
                {"index":1,"width_milli_mm":310000,"height_milli_mm":230000,"rotation":0,"required_text":[crate::SECTION_ONE_TEXT],"forbidden_text":[crate::SECTION_TWO_TEXT]},
                {"index":2,"width_milli_mm":310000,"height_milli_mm":230000,"rotation":0,"required_text":[crate::SECTION_TWO_TEXT],"forbidden_text":[crate::SECTION_ONE_TEXT]}
            ]
        });
        let expectation = serde_json::to_vec(&expectation_value)?;
        let page = |index: usize, text: &str, forbidden: &str, png: &[u8]| {
            json!({
                "index": index, "width_milli_mm": 309739, "height_milli_mm": 229658,
                "rotation": 0, "extracted_text_sha256": super::super::digest(text.as_bytes()),
                "extracted_text_utf8_bytes": text.len(), "required_text_sha256": [super::super::digest(text.as_bytes())],
                "forbidden_text_sha256": [super::super::digest(forbidden.as_bytes())],
                "png_sha256": super::super::digest(png), "png_bytes": png.len(), "png_width": 1756, "png_height": 1302
            })
        };
        let pdf_verification = serde_json::to_vec(&json!({
            "schema_version":"hwpx-agent.p05-hancom-pdf-verification/v1","state":"pass","error_code":null,
            "pdf_sha256":super::super::digest(&pdf),"pdf_bytes":pdf.len(),"pdf_signature_valid":true,
            "expectation_sha256":super::super::digest(&expectation),"page_count":2,"geometry_tolerance_milli_mm":500,
            "render_dpi":144,"renderer_sha256":EXPECTED_RENDERER,"python_runtime_sha256":EXPECTED_PYTHON_RUNTIME,
            "verifier_sha256":EXPECTED_VERIFIER,"pypdf_version":"6.13.3","pillow_version":"12.2.0",
            "pages":[page(1,crate::SECTION_ONE_TEXT,crate::SECTION_TWO_TEXT,&pngs[0]),page(2,crate::SECTION_TWO_TEXT,crate::SECTION_ONE_TEXT,&pngs[1])],
            "raw_document_text_present":false,"user_document_scanned":false,"external_network_invoked":false,"pdf_modified":false
        }))?;
        let mut trace = trace_value(source, saved)?;
        trace["render_pdf_sha256"] = json!(super::super::digest(&pdf));
        trace["render_pdf_bytes"] = json!(pdf.len());
        Ok((serde_json::to_vec(&trace)?, pdf, pdf_verification, pngs))
    }

    fn checked(source: &[u8], saved: &[u8]) -> Result<RebindingReceipt, Box<dyn Error>> {
        let (trace, pdf, pdf_verification, pngs) = evidence(source, saved)?;
        let expectation = serde_json::to_vec(&json!({
            "schema_version": "hwpx-agent.p05-render-expectation/v1", "expected_page_count": 2,
            "geometry_tolerance_milli_mm": 500,
            "pages": [
                {"index":1,"width_milli_mm":310000,"height_milli_mm":230000,"rotation":0,"required_text":[crate::SECTION_ONE_TEXT],"forbidden_text":[crate::SECTION_TWO_TEXT]},
                {"index":2,"width_milli_mm":310000,"height_milli_mm":230000,"rotation":0,"required_text":[crate::SECTION_TWO_TEXT],"forbidden_text":[crate::SECTION_ONE_TEXT]}
            ]
        }))?;
        issue_receipt(
            source,
            saved,
            &trace,
            &super::super::digest(&trace),
            &pdf,
            &pdf_verification,
            &super::super::digest(&pdf_verification),
            &expectation,
            &super::super::digest(&expectation),
            [&pngs[0], &pngs[1]],
        )
    }

    #[test]
    fn identical_backend_ids_emit_no_normalization_event() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let receipt = checked(&source, &source)?;
        assert!(receipt.identity_binding_verified);
        assert!(!receipt.logical_identity_rebinding_verified);
        assert!(receipt.backend_identifiers_preserved);
        assert!(receipt.normalization_events.is_empty());
        Ok(())
    }

    #[test]
    fn two_absent_saved_ids_rebind_to_two_unique_logical_ids() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let saved = rewrite(
            &source,
            "Contents/section0.xml",
            "id=\"p05-07-equal\"",
            "id=\"\"",
        )?;
        let saved = rewrite(
            &saved,
            "Contents/section1.xml",
            "id=\"p05-07-custom\"",
            "id=\"\"",
        )?;
        let receipt = checked(&source, &saved)?;
        assert!(receipt.logical_identity_rebinding_verified);
        assert!(!receipt.backend_identifiers_preserved);
        assert!(receipt.saved_backend_identifier_absence_admitted);
        assert_eq!(receipt.normalization_events.len(), 2);
        assert_ne!(
            receipt.bindings[0].logical_id,
            receipt.bindings[1].logical_id
        );
        assert_ne!(
            receipt.bindings[0].structural_context_sha256,
            receipt.bindings[1].structural_context_sha256
        );
        let serialized = serde_json::to_string(&receipt)?;
        assert!(!serialized.contains("p05-07-equal"));
        assert!(!serialized.contains("p05-07-custom"));
        assert!(!serialized.contains(crate::SECTION_ONE_TEXT));
        Ok(())
    }

    #[test]
    fn semantic_change_reorder_and_foreign_id_fail_closed() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let semantic = rewrite(
            &source,
            "Contents/section0.xml",
            "sameGap=\"1700\"",
            "sameGap=\"1800\"",
        )?;
        assert!(checked(&source, &semantic).is_err());
        let reordered = rewrite(
            &source,
            "Contents/content.hpf",
            concat!(
                "<opf:itemref idref=\"section0\" linear=\"yes\"/>",
                "<opf:itemref idref=\"section1\" linear=\"yes\"/>"
            ),
            concat!(
                "<opf:itemref idref=\"section1\" linear=\"yes\"/>",
                "<opf:itemref idref=\"section0\" linear=\"yes\"/>"
            ),
        )?;
        assert!(checked(&source, &reordered).is_err());
        let foreign = rewrite(
            &source,
            "Contents/section0.xml",
            "id=\"p05-07-equal\"",
            "id=\"foreign\"",
        )?;
        assert!(checked(&source, &foreign).is_err());
        Ok(())
    }

    #[test]
    fn stale_trace_pdf_expectation_and_png_fail_closed() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let (trace, pdf, pdf_verification, pngs) = evidence(&source, &source)?;
        let mut expectation: Value = serde_json::from_slice(&serde_json::to_vec(&json!({
            "schema_version":"hwpx-agent.p05-render-expectation/v1","expected_page_count":2,"geometry_tolerance_milli_mm":500,
            "pages":[
                {"index":1,"width_milli_mm":310000,"height_milli_mm":230000,"rotation":0,"required_text":[crate::SECTION_ONE_TEXT],"forbidden_text":[crate::SECTION_TWO_TEXT]},
                {"index":2,"width_milli_mm":310000,"height_milli_mm":230000,"rotation":0,"required_text":[crate::SECTION_TWO_TEXT],"forbidden_text":[crate::SECTION_ONE_TEXT]}
            ]
        }))?)?;
        let expectation_bytes = serde_json::to_vec(&expectation)?;
        assert!(
            issue_receipt(
                &source,
                &source,
                &trace,
                &"0".repeat(64),
                &pdf,
                &pdf_verification,
                &super::super::digest(&pdf_verification),
                &expectation_bytes,
                &super::super::digest(&expectation_bytes),
                [&pngs[0], &pngs[1]]
            )
            .is_err()
        );
        let mut wrong_pdf = pdf.clone();
        wrong_pdf[20] ^= 1;
        assert!(
            issue_receipt(
                &source,
                &source,
                &trace,
                &super::super::digest(&trace),
                &wrong_pdf,
                &pdf_verification,
                &super::super::digest(&pdf_verification),
                &expectation_bytes,
                &super::super::digest(&expectation_bytes),
                [&pngs[0], &pngs[1]]
            )
            .is_err()
        );
        expectation["pages"][0]["width_milli_mm"] = json!(300000);
        let wrong_expectation = serde_json::to_vec(&expectation)?;
        assert!(
            issue_receipt(
                &source,
                &source,
                &trace,
                &super::super::digest(&trace),
                &pdf,
                &pdf_verification,
                &super::super::digest(&pdf_verification),
                &wrong_expectation,
                &super::super::digest(&wrong_expectation),
                [&pngs[0], &pngs[1]]
            )
            .is_err()
        );
        let mut wrong_png = pngs[0].clone();
        wrong_png[20] ^= 1;
        assert!(
            issue_receipt(
                &source,
                &source,
                &trace,
                &super::super::digest(&trace),
                &pdf,
                &pdf_verification,
                &super::super::digest(&pdf_verification),
                &expectation_bytes,
                &super::super::digest(&expectation_bytes),
                [&wrong_png, &pngs[1]]
            )
            .is_err()
        );
        Ok(())
    }

    #[test]
    fn duplicate_fingerprints_and_malformed_package_are_rejected() -> Result<(), Box<dyn Error>> {
        let mut set = HashSet::new();
        insert_unique(&mut set, "same".to_owned())?;
        assert!(insert_unique(&mut set, "same".to_owned()).is_err());
        assert!(checked(b"not a package", b"not a package").is_err());
        Ok(())
    }
}
