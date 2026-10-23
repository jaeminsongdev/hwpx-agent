//! Complete note packages through the existing production preserving adapter; no COM.
#[allow(dead_code)]
#[path = "p08_19_support/common.rs"]
mod archive;

use domain_ir::{
    LogicalId, NOTE_ENGINE_SCHEMA_VERSION, NoteAnchor, NoteAutoNumberFormat, NoteBuilder,
    NoteDocumentState, NoteDocumentStateDraft, NoteEntry, NoteIdentity, NoteKind, NoteLimitConfig,
    NoteLimits, NoteLineStyle, NoteLineType, NoteLineWidth, NoteMarkerProperties, NoteNativeTag,
    NoteNumberFormat, NoteNumberingRestart, NoteOperation, NotePlacement, NoteRequest,
    NoteRequestDraft, NoteSectionState, NoteSpacing, NoteStyle,
};
use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    BoundedZipReader, Hancom2020Vs0Builder, NoteHwpxBuilder, NoteHwpxLimitConfig, NoteHwpxLimits,
    NoteHwpxLowerer, NoteHwpxLoweringReceipt, NoteHwpxReader, PackageGraph, PackageGraphLimits,
    PackageLimits,
};
use quick_xml::escape::escape;
use serde::Serialize;
use std::{collections::BTreeMap, env, error::Error, fs, io::Cursor, path::PathBuf};

type AnyError = Box<dyn Error>;
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const EMPTY: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const SEED_TEXT: &str = "P09-24 note insertion target & preserved main text";

#[derive(Clone, Serialize)]
struct OperationEvidence {
    capability_id: String,
    native_inst_id: u32,
    kind: &'static str,
    run_ordinal: u32,
    inline_ordinal: u32,
    input_marker_number: u16,
    body_graph_sha256: String,
    plain_text_sha256: Option<String>,
    body_style_sha256: String,
    marker_style_sha256: String,
    source_section_sha256: String,
    output_section_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    plan_sha256: String,
    stale_source_rejected: bool,
    stale_payload_rejected: bool,
}

#[derive(Serialize)]
struct FixtureCase {
    case_id: &'static str,
    feature_ids: Vec<&'static str>,
    file: &'static str,
    package_sha256: String,
    package_bytes: usize,
    section_sha256: String,
    note_count: usize,
    operations: Vec<OperationEvidence>,
    expanded_non_section_parts_sha256: BTreeMap<String, String>,
    deterministic_retry: bool,
}

struct BuildProgress {
    section: Vec<u8>,
    state: NoteDocumentState,
    operations: Vec<OperationEvidence>,
}

fn id(value: &str) -> Result<LogicalId, AnyError> {
    Ok(LogicalId::parse(value)?)
}
fn state_limits() -> Result<NoteLimits, AnyError> {
    Ok(NoteLimits::new(NoteLimitConfig::default())?)
}
fn hwpx_limits() -> Result<NoteHwpxLimits, AnyError> {
    Ok(NoteHwpxLimits::new(NoteHwpxLimitConfig::default())?)
}
fn style(kind: NoteKind, binding: &str) -> NoteStyle {
    let foot = kind == NoteKind::Footnote;
    NoteStyle {
        kind,
        auto_number_format: NoteAutoNumberFormat {
            format: NoteNumberFormat::Digit,
            user_character: String::new(),
            prefix_character: String::new(),
            suffix_character: ")".into(),
            superscript: false,
        },
        note_line: NoteLineStyle {
            length_hwp_units: if foot { -1 } else { 14_692_344 },
            line_type: NoteLineType::Solid,
            width: NoteLineWidth::Mm0_12,
            color_rgb: 0,
        },
        spacing: NoteSpacing {
            between_notes_hwp_units: if foot { 283 } else { 0 },
            below_line_hwp_units: 567,
            above_line_hwp_units: 850,
        },
        numbering_restart: NoteNumberingRestart::Continuous,
        new_number: 1,
        placement: if foot {
            NotePlacement::EachColumn
        } else {
            NotePlacement::EndOfDocument
        },
        beneath_text: false,
        opaque_style_sha256: binding.into(),
        locked: false,
    }
}
fn initial_state(
    section: &[u8],
    parts: &BTreeMap<String, String>,
) -> Result<NoteDocumentState, AnyError> {
    let binding = archive::sha256(section);
    let inventory = archive::sha256(&serde_json::to_vec(parts)?);
    Ok(NoteDocumentState::from_draft(
        NoteDocumentStateDraft {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION.into(),
            sections: vec![NoteSectionState {
                section_id: id("section-1")?,
                footnote_style: style(NoteKind::Footnote, &binding),
                endnote_style: style(NoteKind::Endnote, &binding),
                opaque_section_state_sha256: binding.clone(),
                locked: false,
            }],
            notes: Vec::new(),
            non_note_content_sha256: binding.clone(),
            style_catalog_sha256: parts
                .get("Contents/header.xml")
                .ok_or("missing header")?
                .clone(),
            numbering_inventory_sha256: binding.clone(),
            reference_inventory_sha256: binding.clone(),
            resource_inventory_sha256: inventory.clone(),
            document_protection_sha256: parts
                .get("settings.xml")
                .ok_or("missing settings")?
                .clone(),
            opaque_document_state_sha256: inventory,
            document_locked: false,
        },
        state_limits()?,
    )?)
}
fn body(kind: NoteKind, paragraph_ids: &[u32]) -> Vec<u8> {
    let (style_id, text) = if kind == NoteKind::Footnote {
        (14, "P09 footnote & <body> 한글 🚀")
    } else {
        (15, "P09 endnote & <body> 한글")
    };
    format!(concat!(
        "<hp:subList xmlns:hp=\"{}\" id=\"\" textDirection=\"HORIZONTAL\" lineWrap=\"BREAK\" ",
        "vertAlign=\"TOP\" linkListIDRef=\"0\" linkListNextIDRef=\"0\" textWidth=\"0\" textHeight=\"0\" hasTextRef=\"0\" hasNumRef=\"0\">",
        "<hp:p id=\"{}\" paraPrIDRef=\"10\" styleIDRef=\"{}\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\">",
        "<hp:run charPrIDRef=\"3\"><hp:t>{}</hp:t></hp:run><hp:run charPrIDRef=\"0\"><hp:t> continuation</hp:t></hp:run></hp:p>",
        "<hp:p id=\"{}\" paraPrIDRef=\"10\" styleIDRef=\"{}\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\">",
        "<hp:run charPrIDRef=\"3\"><hp:t>second paragraph</hp:t></hp:run></hp:p></hp:subList>"
    ), HP, paragraph_ids[0], style_id, escape(text), paragraph_ids[1], style_id).into_bytes()
}
fn note_entry(
    progress: &BuildProgress,
    kind: NoteKind,
    native_id: u32,
    inline: u32,
    payload: &[u8],
) -> Result<NoteEntry, AnyError> {
    let digests = NoteHwpxReader::inspect_payload(payload, hwpx_limits()?)?;
    let marker_style =
        NoteHwpxReader::marker_style_sha256_at(&progress.section, 0, 1, hwpx_limits()?)?;
    Ok(NoteEntry {
        identity: NoteIdentity {
            logical_note_id: id(&format!("note-{native_id}"))?,
            native_instance_id: native_id,
        },
        anchor: NoteAnchor {
            section_id: id("section-1")?,
            paragraph_id: id("paragraph-1")?,
            run_ordinal: 1,
            inline_ordinal: inline,
        },
        kind,
        native_tag: if kind == NoteKind::Footnote {
            NoteNativeTag::FootNote
        } else {
            NoteNativeTag::EndNote
        },
        marker: NoteMarkerProperties {
            flags: 0,
            number: 1,
            user_character: None,
            prefix_character: None,
            suffix_character: None,
        },
        body_graph_sha256: digests.body_graph_sha256.clone(),
        plain_text_sha256: digests.plain_text_sha256.clone(),
        marker_style_sha256: marker_style.clone(),
        body_style_sha256: digests.body_style_sha256.clone(),
        opaque_native_payload_sha256: EMPTY.into(),
        opaque_properties: Vec::new(),
        locked: false,
    })
}
fn operation_evidence(
    note: &NoteEntry,
    receipt: &NoteHwpxLoweringReceipt,
    source_flow: &str,
    target_flow: &str,
    stale_source: bool,
    stale_payload: bool,
) -> OperationEvidence {
    OperationEvidence {
        capability_id: receipt.capability_id.into(),
        native_inst_id: note.identity.native_instance_id,
        kind: if note.kind == NoteKind::Footnote {
            "footNote"
        } else {
            "endNote"
        },
        run_ordinal: note.anchor.run_ordinal,
        inline_ordinal: note.anchor.inline_ordinal,
        input_marker_number: note.marker.number,
        body_graph_sha256: note.body_graph_sha256.clone(),
        plain_text_sha256: note.plain_text_sha256.clone(),
        body_style_sha256: note.body_style_sha256.clone(),
        marker_style_sha256: note.marker_style_sha256.clone(),
        source_section_sha256: source_flow.into(),
        output_section_sha256: target_flow.into(),
        source_state_sha256: receipt.source_state_sha256.clone(),
        target_state_sha256: receipt.target_state_sha256.clone(),
        plan_sha256: receipt.plan_sha256.clone(),
        stale_source_rejected: stale_source,
        stale_payload_rejected: stale_payload,
    }
}
fn rejects_stale_inputs(
    progress: &BuildProgress,
    payload: &[u8],
    plan: &hwpx_package::NoteHwpxPlan,
    source_flow: &str,
) -> Result<(bool, bool), AnyError> {
    let drift = [progress.section.as_slice(), b" "].concat();
    let wrong_payload = [payload, b" "].concat();
    Ok((
        NoteHwpxLowerer::lower_section(
            &drift,
            payload,
            plan,
            &progress.state,
            source_flow,
            state_limits()?,
            hwpx_limits()?,
        )
        .is_err(),
        NoteHwpxLowerer::lower_section(
            &progress.section,
            &wrong_payload,
            plan,
            &progress.state,
            source_flow,
            state_limits()?,
            hwpx_limits()?,
        )
        .is_err(),
    ))
}
fn insert(
    progress: &mut BuildProgress,
    kind: NoteKind,
    native_id: u32,
    inline: u32,
) -> Result<(), AnyError> {
    let paragraph_ids = NoteHwpxReader::allocate_paragraph_ids(&progress.section, 2, hwpx_limits()?)?;
    let payload = body(kind, &paragraph_ids);
    let note = note_entry(progress, kind, native_id, inline, &payload)?;
    let source_flow = archive::sha256(&progress.section);
    let map = [id("paragraph-1")?];
    // First derive the prospective bytes, then seal the final plan to their actual digest.
    let mut target_flow = archive::sha256(b"prospective-note-flow-not-target-evidence");
    let mut prospective = Vec::new();
    for pass in 0..2 {
        let request = NoteRequest::from_draft(
            NoteRequestDraft {
                schema_version: NOTE_ENGINE_SCHEMA_VERSION.into(),
                request_id: id(&format!("insert-{native_id}"))?,
                expected_source_state_sha256: progress.state.canonical_sha256(state_limits()?)?,
                expected_document_flow_sha256: source_flow.clone(),
                target_document_flow_sha256: target_flow.clone(),
                operation: NoteOperation::Insert {
                    insertion_index: progress.state.notes().len(),
                    note: note.clone(),
                },
            },
            &progress.state,
            &source_flow,
            state_limits()?,
        )?;
        let domain = NoteBuilder::plan(&progress.state, &request, &source_flow, state_limits()?)?;
        let built = NoteBuilder::build(&domain, &progress.state, &source_flow, state_limits()?)?;
        let plan = NoteHwpxBuilder::plan(
            &progress.section,
            &progress.state,
            &domain,
            &source_flow,
            &map,
            &payload,
            state_limits()?,
            hwpx_limits()?,
        )?;
        let (output, receipt) = NoteHwpxLowerer::lower_section_with_receipt(
            &progress.section,
            &payload,
            &plan,
            &progress.state,
            &source_flow,
            state_limits()?,
            hwpx_limits()?,
        )?;
        if pass == 0 {
            target_flow = archive::sha256(&output);
            prospective = output;
            continue;
        }
        if output != prospective || archive::sha256(&output) != target_flow {
            return Err("final note flow did not reproduce prospective bytes".into());
        }
        let (stale_source, stale_payload) =
            rejects_stale_inputs(progress, &payload, &plan, &source_flow)?;
        if !stale_source || !stale_payload || receipt.inserted_notes != 1 {
            return Err("note negative or insertion receipt failed".into());
        }
        let readback = NoteHwpxReader::read_section(
            &output,
            &built.state,
            &map,
            state_limits()?,
            hwpx_limits()?,
        )?;
        if readback.note_count != progress.state.notes().len() + 1 {
            return Err("note inventory did not grow by one".into());
        }
        progress.operations.push(operation_evidence(
            &note,
            &receipt,
            &source_flow,
            &target_flow,
            stale_source,
            stale_payload,
        ));
        progress.section = output;
        progress.state = built.state;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generated_note_packages_pass_original_id_index_and_complete_kind_conversion() -> Result<(), AnyError> {
        use hwpx_package::{IdIndex, IdIndexLimits, IdRuleProfile, WriterLimits};
        use hwpx_package::document_import::{ImportedSourcePackage, SourceImportLimits, structure::{ImportedDocumentStructure, note_conversion::NoteKindConversion}};
        use sha2::{Digest as _, Sha256};
        let base = Hancom2020Vs0Builder::build(SEED_TEXT)?.with_verified_bytes(<[u8]>::to_vec)?;
        for kinds in [vec![NoteKind::Footnote], vec![NoteKind::Endnote], vec![NoteKind::Footnote, NoteKind::Endnote]] {
            let (bytes, _) = build_case(&base, &kinds)?;
            let mut reader = BoundedZipReader::open(Cursor::new(&bytes), PackageLimits::default())?;
            let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
            IdIndex::build_with_graph_limits(&mut reader, &graph, PackageGraphLimits::default(), IdRuleProfile::hwpml_2011_shape_v6(), IdIndexLimits::default())?;
            let source = ImportedDocumentStructure::import(ImportedSourcePackage::import(&bytes, domain_ir::DocumentId::parse("note-id-regression")?, Sha256::digest(&bytes).into(), SourceImportLimits::default())?)?;
            let requests: Vec<_> = source.notes().iter().map(|n| NoteKindConversion { note_id: &n.note_id, source_note_sha256: n.source_anchor.fingerprint_sha256,
                target_kind: if n.native_kind == "footNote" { NoteKind::Endnote } else { NoteKind::Footnote } }).collect();
            let output = source.lower_note_kind_batch_candidate(&bytes, &requests, hwpx_limits()?, WriterLimits::default())?;
            assert_eq!(output.receipt().converted_notes, kinds.len());
            assert!(output.receipt().only_selected_note_names_changed);
            assert!(!output.receipt().native_number_recalculation_qualified);
            source.verify_source(&bytes)?;
        }
        Ok(())
    }

    #[test]
    fn complete_packages_repeat_and_preserve_all_other_parts() -> Result<(), AnyError> {
        let base = Hancom2020Vs0Builder::build(SEED_TEXT)?.with_verified_bytes(<[u8]>::to_vec)?;
        for kinds in [
            vec![NoteKind::Footnote],
            vec![NoteKind::Endnote],
            vec![NoteKind::Footnote, NoteKind::Endnote],
        ] {
            let (first, built) = build_case(&base, &kinds)?;
            let (retry, _) = build_case(&base, &kinds)?;
            assert_eq!(first, retry);
            assert_eq!(inventory(&base)?, inventory(&first)?);
            assert_eq!(built.state.notes().len(), kinds.len());
            assert!(
                built
                    .operations
                    .iter()
                    .all(|op| op.stale_source_rejected && op.stale_payload_rejected)
            );
        }
        Ok(())
    }

    #[test]
    fn combined_case_seals_real_flow_and_preserves_first_note() -> Result<(), AnyError> {
        let base = Hancom2020Vs0Builder::build(SEED_TEXT)?.with_verified_bytes(<[u8]>::to_vec)?;
        let (_, foot) = build_case(&base, &[NoteKind::Footnote])?;
        let (_, combined) = build_case(&base, &[NoteKind::Footnote, NoteKind::Endnote])?;
        assert_eq!(
            combined.operations[0].output_section_sha256,
            combined.operations[1].source_section_sha256
        );
        assert_eq!(
            combined.operations[0].target_state_sha256,
            combined.operations[1].source_state_sha256
        );
        assert_eq!(
            combined.operations[1].output_section_sha256,
            archive::sha256(&combined.section)
        );
        let text = std::str::from_utf8(&combined.section)?;
        let start = text.find("<hp:ctrl><hp:endNote").ok_or("endnote absent")?;
        let finish = start
            + text[start..]
                .find("</hp:endNote></hp:ctrl>")
                .ok_or("endnote close absent")?
            + "</hp:endNote></hp:ctrl>".len();
        let restored = [&combined.section[..start], &combined.section[finish..]].concat();
        assert_eq!(restored, foot.section);
        Ok(())
    }

    #[test]
    fn duplicate_anchor_is_rejected_without_partial_progress() -> Result<(), AnyError> {
        let base = Hancom2020Vs0Builder::build(SEED_TEXT)?.with_verified_bytes(<[u8]>::to_vec)?;
        let (_, mut built) = build_case(&base, &[NoteKind::Footnote])?;
        let before = built.section.clone();
        let state = built.state.canonical_json(state_limits()?)?;
        let operations = serde_json::to_vec(&built.operations)?;
        assert!(insert(&mut built, NoteKind::Footnote, 24_003, 0).is_err());
        assert_eq!(built.section, before);
        assert_eq!(built.state.canonical_json(state_limits()?)?, state);
        assert_eq!(serde_json::to_vec(&built.operations)?, operations);
        Ok(())
    }
}
fn inventory(bytes: &[u8]) -> Result<BTreeMap<String, String>, AnyError> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
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
fn build_case(base: &[u8], kinds: &[NoteKind]) -> Result<(Vec<u8>, BuildProgress), AnyError> {
    let parts = inventory(base)?;
    let section = archive::section_from_package(base)?;
    let mut progress = BuildProgress {
        state: initial_state(&section, &parts)?,
        section,
        operations: Vec::new(),
    };
    for kind in kinds {
        let foot = *kind == NoteKind::Footnote;
        insert(
            &mut progress,
            *kind,
            if foot { 24_001 } else { 24_002 },
            u32::from(!foot),
        )?;
    }
    let package = archive::package_with_section(base, &progress.section)?;
    if inventory(&package)? != parts {
        return Err("unrelated note package parts changed".into());
    }
    Ok((package, progress))
}
fn output_argument() -> Result<PathBuf, AnyError> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?;
    let mut args = env::args_os().skip(1);
    let output = PathBuf::from(args.next().ok_or("new output required")?);
    if args.next().is_some() || !output.is_absolute() || output.exists() {
        return Err("new absolute output required".into());
    }
    let parent = output.parent().ok_or("missing parent")?;
    for ancestor in parent.ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("linked output rejected".into());
            }
        }
        if metadata.file_type().is_symlink() {
            return Err("linked output rejected".into());
        }
    }
    if parent.canonicalize()? != root.join("fixtures/target-build").canonicalize()? {
        return Err("output boundary rejected".into());
    }
    Ok(parent.join(output.file_name().ok_or("missing output name")?))
}
fn main() -> Result<(), AnyError> {
    let destination = output_argument()?;
    let base = Hancom2020Vs0Builder::build(SEED_TEXT)?.with_verified_bytes(<[u8]>::to_vec)?;
    let parts = inventory(&base)?;
    let configs: [(_, _, &[NoteKind]); 3] = [
        (
            "P09-24-C01",
            "p09-24-c01-footnote.hwpx",
            &[NoteKind::Footnote],
        ),
        (
            "P09-24-C02",
            "p09-24-c02-endnote.hwpx",
            &[NoteKind::Endnote],
        ),
        (
            "P09-24-C03",
            "p09-24-c03-footnote-endnote.hwpx",
            &[NoteKind::Footnote, NoteKind::Endnote],
        ),
    ];
    let mut cases = Vec::new();
    let mut packages = Vec::new();
    for (case, file, kinds) in configs {
        let (bytes, built) = build_case(&base, kinds)?;
        let (retry, repeated) = build_case(&base, kinds)?;
        if bytes != retry
            || serde_json::to_vec(&built.operations)? != serde_json::to_vec(&repeated.operations)?
        {
            return Err("note package retry was not deterministic".into());
        }
        cases.push(FixtureCase {
            case_id: case,
            feature_ids: kinds
                .iter()
                .map(|k| {
                    if *k == NoteKind::Footnote {
                        "REF-021"
                    } else {
                        "REF-022"
                    }
                })
                .collect(),
            file,
            package_sha256: archive::sha256(&bytes),
            package_bytes: bytes.len(),
            section_sha256: archive::sha256(&built.section),
            note_count: kinds.len(),
            operations: built.operations,
            expanded_non_section_parts_sha256: parts.clone(),
            deterministic_retry: true,
        });
        packages.push(bytes);
    }
    let manifest = serde_json::json!({"schema_version":"hwpx-agent.p09-note-complete-target-fixture/v1", "task":"P09-24",
        "seed_file":"p09-24-note-seed.hwpx", "seed_package_sha256":archive::sha256(&base), "seed_package_bytes":base.len(),
        "seed_section_sha256":archive::sha256(&archive::section_from_package(&base)?), "cases":cases,
        "complete_package_graph":true,"actual_hangul":false,"save_reopen":"not_run","render":"not_run","automation":"not_run",
        "differential":"not_run","marker_expectation":"input_preservation_model_hypothesis_target_unqualified",
        "green_rows":0,"p09_complete":false,"product_complete":false});
    let raw = serde_json::to_vec_pretty(&manifest)?;
    let workspace = SecureWorkspace::create(&destination)?;
    for (name, bytes) in std::iter::once(("p09-24-note-seed.hwpx", &base))
        .chain(cases.iter().zip(&packages).map(|(c, p)| (c.file, p)))
    {
        let staged = workspace.stage_bytes(&PathBuf::from("p09-24").join(name), bytes)?;
        workspace.publish(&staged, std::path::Path::new(name))?;
    }
    let staged =
        workspace.stage_bytes(std::path::Path::new("p09-24/fixture-manifest.json"), &raw)?;
    workspace.publish(&staged, std::path::Path::new("fixture-manifest.json"))?;
    println!(
        "{}",
        serde_json::json!({"state":"pass","cases":cases.len(),"manifest_sha256":archive::sha256(&raw),"actual_hangul":false,"green_rows":0})
    );
    Ok(())
}
