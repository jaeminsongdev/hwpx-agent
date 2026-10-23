//! Independent real saved/reopened parameter oracle; no Native execution.
use domain_ir::{
    LogicalId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits, SourceAnchorHandle,
};
use hwpx_package::{
    PreservingXmlDocument, WriterLimits,
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        fields::{
            ImportedDocumentFields,
            bookmark_insertion::{
                SourceBookmarkInsertion as Request, SourceBookmarkInsertionError as E,
                generated::{PARAMETER_PROFILE, SourceBookmarkCreationCandidate as Candidate},
            },
        },
        forms::ImportedDocumentForms,
    },
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    io::{Cursor, Read},
    path::Path,
};
#[path = "support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
pub type Result<T = ()> = std::result::Result<T, Box<dyn Error>>;
pub const DOC: &str = "p09-source-bookmark-first-insertion627";
const CORPUS: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
);
pub fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
pub fn require(ok: bool) -> Result {
    if ok {
        Ok(())
    } else {
        Err("P627_OBSERVATION_REJECTED_NO_RAW_VALUES".into())
    }
}
fn sample(name: &str, extra: &str) -> Result<Vec<u8>> {
    let escaped = quick_xml::escape::escape(name);
    base::package(&format!(
        "<hp:p id='1'><hp:run>{}</hp:run></hp:p><hp:p id='2'><hp:run><hp:t>private-placeholder&amp;原文</hp:t></hp:run>{extra}</hp:p>",
        fixture::marker(&escaped)
    ))
}
pub fn selection(forms: &ImportedDocumentForms) -> Result<(SourceAnchorHandle, LogicalId)> {
    let fields = ImportedDocumentFields::import(forms)?;
    let source = forms.source();
    let mut chosen = None;
    for p in source.parts() {
        if let Some(xml) = p.xml() {
            let intervals: Vec<_> = fields
                .fields()
                .iter()
                .filter_map(|f| {
                    let a = source.resolve_anchor(&f.begin_anchor).ok()?;
                    let b = source.resolve_anchor(&f.end_anchor).ok()?;
                    (a.part().path() == p.path()).then_some((
                        a.element()?.outer_span()?.start(),
                        b.element()?.outer_span()?.end(),
                    ))
                })
                .collect();
            for (i, n) in xml.elements().iter().enumerate() {
                if n.name().local_name() != "run"
                    || !n.first_child().is_some_and(|j| {
                        xml.elements()[j].name().local_name() == "t"
                            && xml.elements()[j].first_child().is_none()
                            && xml.elements()[j].next_sibling().is_none()
                    })
                {
                    continue;
                }
                let s = n.outer_span().ok_or("P627_RUN_SPAN")?;
                if intervals
                    .iter()
                    .any(|(a, b)| *a < s.end() && s.start() < *b)
                {
                    continue;
                }
                chosen = p.element_anchor(i).cloned();
                break;
            }
            if chosen.is_some() {
                break;
            }
        }
    }
    Ok((
        chosen.ok_or("P627_PLAIN_OUTSIDE_RUN_MISSING")?,
        forms
            .body_structure()
            .bookmarks()
            .first()
            .ok_or("P627_TARGET_MISSING")?
            .reference_id
            .clone(),
    ))
}
fn core(
    bytes: &[u8],
    run: &SourceAnchorHandle,
    target: &LogicalId,
    display: Display,
    hyperlink: bool,
) -> Result<Candidate> {
    let forms = base::forms(bytes, DOC)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let proof = forms.reconstruct_source_for_verification(bytes)?;
    Ok(fields.create_bookmark_reference(
        &proof,
        Request {
            run,
            target_id: target,
            display,
            hyperlink,
        },
        limits()?,
        WriterLimits::default(),
    )?)
}
fn display(value: &str) -> Result<Display> {
    Ok(match value {
        "page" => Display::Page,
        "bookmark_name" => Display::BookmarkName,
        "content" => Display::Content,
        "relative_position" => Display::RelativePosition,
        _ => return Err("P627_DISPLAY_REJECTED".into()),
    })
}
pub fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("P627_PIN_PATH")?;
    require(
        name.starts_with("implementation/p09/evidence/private/")
            && !name.contains('\\')
            && !name.split('/').any(|s| s == ".." || s.is_empty()),
    )?;
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(name);
    for p in path.ancestors() {
        let m = p.symlink_metadata()?;
        require(!m.file_type().is_symlink())?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            require(m.file_attributes() & 0x400 == 0)?;
        }
    }
    let m = path.metadata()?;
    require(m.is_file() && m.len() <= 4194304 && Some(m.len()) == pin["bytes"].as_u64())?;
    let bytes = std::fs::read(path)?;
    require(Some(hex::encode(Sha256::digest(&bytes)).as_str()) == pin["sha256"].as_str())?;
    Ok(bytes)
}
// This independent reader returns private data only to in-process comparisons.
// It is NEVER serialized or included in assertion/panic/debug text.
fn raw_parameters(bytes: &[u8]) -> Result<Vec<(String, String, String)>> {
    let mut archive = zip::ZipArchive::new(Cursor::new(bytes))?;
    let mut p = archive.by_name("Contents/section0.xml")?;
    require(p.size() <= 4194304)?;
    let mut bytes = Vec::new();
    p.read_to_end(&mut bytes)?;
    let xml = PreservingXmlDocument::parse(&bytes)?;
    let hp = Some("http://www.hancom.co.kr/hwpml/2011/paragraph");
    let (_, begin) = xml
        .elements()
        .iter()
        .enumerate()
        .find(|(_, n)| {
            n.name().namespace() == hp
                && n.name().local_name() == "fieldBegin"
                && n.attributes()
                    .iter()
                    .any(|a| a.name().local_name() == "type" && a.semantic_value() == "CROSSREF")
        })
        .ok_or("P627_CROSSREF_MISSING")?;
    let par = &xml.elements()[begin.first_child().ok_or("P627_PARAMETERS_MISSING")?];
    require(par.name().local_name() == "parameters")?;
    let mut child = par.first_child();
    let mut rows = Vec::new();
    while let Some(i) = child {
        require(rows.len() < 8)?;
        let n = &xml.elements()[i];
        require(n.name().namespace() == hp && n.first_child().is_none())?;
        let name = n
            .attributes()
            .iter()
            .find(|a| a.name().namespace().is_none() && a.name().local_name() == "name")
            .ok_or("P627_KEY_MISSING")?
            .semantic_value();
        let s = n.content_span().ok_or("P627_VALUE_MISSING")?;
        let value = quick_xml::escape::unescape(std::str::from_utf8(
            bytes.get(s.start()..s.end()).ok_or("P627_SPAN")?,
        )?)?;
        rows.push((
            n.name().local_name().to_owned(),
            name.to_owned(),
            value.into_owned(),
        ));
        child = n.next_sibling();
    }
    require(rows.len() == 8)?;
    Ok(rows)
}
pub fn fixed_observations(
    prepare: impl Fn(&[u8], &SourceAnchorHandle, &LogicalId, Display, bool) -> Result<Candidate>,
) -> Result<Value> {
    let corpus: Value = serde_json::from_str(CORPUS)?;
    let source = read_pin(&corpus["source"])?;
    let forms = base::forms(&source, DOC)?;
    let (run, target) = selection(&forms)?;
    require(
        !ImportedDocumentFields::import(&forms)?
            .fields()
            .iter()
            .any(|f| f.native_kind == "CROSSREF"),
    )?;
    let mut rows = Vec::new();
    for case in corpus["cases"].as_array().ok_or("P627_CASES")? {
        let candidate = prepare(
            &source,
            &run,
            &target,
            display(case["display"].as_str().ok_or("display")?)?,
            case["hyperlink"].as_bool().ok_or("hyperlink")?,
        )?;
        let output = candidate.with_verified_bytes(|b| b.to_vec())?;
        let generated = raw_parameters(&output)?;
        for stage in ["saved", "reopened"] {
            let original = read_pin(&case["artifacts"][stage])?;
            require(raw_parameters(&original)? == generated)?;
        }
        let receipt = candidate.receipt();
        require(
            receipt.inserted_fields == 1
                && !receipt.requires_existing_crossref_envelope
                && receipt.inserted_parameter_envelope_readback_verified
                && receipt.outside_insertions_exact
                && receipt.original_selected_run_exact
                && receipt.existing_display_text_is_not_evaluated_or_refreshed
                && !receipt.native_currentness_execution_or_publication_qualified
                && receipt.parameter_profile == PARAMETER_PROFILE,
        )?;
        rows.push(json!({"case_index":case["case_index"],"receipt":receipt,"original_saved_and_reopened_parameter_equality":true}));
    }
    require(rows.len() == 8 && read_pin(&corpus["source"])? == source)?;
    Ok(
        json!({"state":"bookmark_creation627_first_insert8_captured_parameter16_not_native_or_route","observations":rows,
        "actual_native_started":false,"source_overwritten":false,"P09_complete":false,"cache_currentness_qualified":false,"product_route_qualified":false}),
    )
}
#[test]
fn first_crossref_creation_needs_no_existing_envelope() -> Result {
    for name in ["private-target", "한글&자료<값>\"'"] {
        let bytes = sample(name, "")?;
        let forms = base::forms(&bytes, DOC)?;
        let (run, target) = selection(&forms)?;
        require(ImportedDocumentFields::import(&forms)?.fields().is_empty())?;
        for d in [
            Display::Page,
            Display::BookmarkName,
            Display::Content,
            Display::RelativePosition,
        ] {
            for h in [false, true] {
                let candidate = core(&bytes, &run, &target, d, h)?;
                require(
                    candidate.receipt().original_fields == 0
                        && candidate.receipt().inserted_fields == 1,
                )?;
            }
        }
    }
    Ok(())
}
#[test]
fn first_creation_original_source_matches_all_sixteen_native_envelopes() -> Result {
    let _ = fixed_observations(core)?;
    Ok(())
}
#[test]
fn unsupported_target_display_and_ambiguous_names_reject() -> Result {
    let bytes = sample("private-target", "")?;
    let forms = base::forms(&bytes, DOC)?;
    let (run, target) = selection(&forms)?;
    require(
        core(&bytes, &run, &target, Display::ObjectNumber, false)
            .err()
            .is_some_and(|e| matches!(e.downcast_ref::<E>(), Some(E::Target))),
    )?;
    require(
        core(
            &bytes,
            &run,
            &LogicalId::parse("absent")?,
            Display::Page,
            false,
        )
        .err()
        .is_some_and(|e| matches!(e.downcast_ref::<E>(), Some(E::Target))),
    )?;
    let bytes = sample(
        "private-target",
        &format!("<hp:run>{}</hp:run>", fixture::marker("private-target")),
    )?;
    let forms = base::forms(&bytes, DOC)?;
    let (run, target) = selection(&forms)?;
    require(
        core(&bytes, &run, &target, Display::Page, false)
            .err()
            .is_some_and(|e| matches!(e.downcast_ref::<E>(), Some(E::Target))),
    )
}
#[test]
fn source_envelope_entry_remains_closed_without_template() -> Result {
    let bytes = sample("private-target", "")?;
    let forms = base::forms(&bytes, DOC)?;
    let (run, target) = selection(&forms)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let proof = forms.reconstruct_source_for_verification(&bytes)?;
    require(matches!(
        fields.insert_bookmark_reference_from_source_envelope(
            &proof,
            Request {
                run: &run,
                target_id: &target,
                display: Display::Page,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default()
        ),
        Err(E::EnvelopeUnavailable)
    ))
}
#[test]
fn generated_envelope_cannot_escape_xml_or_leak_into_receipt() -> Result {
    let bytes = sample("private-secret&\"'", "")?;
    let forms = base::forms(&bytes, DOC)?;
    let (run, target) = selection(&forms)?;
    let a = core(&bytes, &run, &target, Display::Content, true)?;
    let b = core(&bytes, &run, &target, Display::Content, true)?;
    require(
        a.receipt() == b.receipt()
            && !serde_json::to_string(a.receipt())?.contains("private-secret")
            && !format!("{a:?}").contains("private-secret"),
    )
}
#[test]
fn generated_parameter_budget_and_foreign_proof_are_not_bypassed() -> Result {
    let bytes = sample("private-target", "")?;
    let forms = base::forms(&bytes, DOC)?;
    let other = base::forms(&bytes, DOC)?;
    let (run, target) = selection(&forms)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let foreign = other.reconstruct_source_for_verification(&bytes)?;
    require(matches!(
        fields.create_bookmark_reference(
            &foreign,
            Request {
                run: &run,
                target_id: &target,
                display: Display::Page,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default()
        ),
        Err(E::Source)
    ))?;
    let proof = forms.reconstruct_source_for_verification(&bytes)?;
    let limits = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        text_bytes: 64,
        ..Default::default()
    })?;
    require(matches!(
        fields.create_bookmark_reference(
            &proof,
            Request {
                run: &run,
                target_id: &target,
                display: Display::Page,
                hyperlink: false
            },
            limits,
            WriterLimits::default()
        ),
        Err(E::Limit)
    ))
}
#[test]
fn existing_unrelated_field_and_bookmark_are_preserved() -> Result {
    let bytes = sample(
        "private-target",
        &format!("<hp:run>{}</hp:run>", fixture::field()),
    )?;
    let forms = base::forms(&bytes, DOC)?;
    let (run, target) = selection(&forms)?;
    let a = core(&bytes, &run, &target, Display::Page, false)?;
    require(a.receipt().original_fields == 1 && a.receipt().outside_insertions_exact)
}
