//! New field count/output proof, not Native display/currentness acceptance.
use domain_ir::{
    LogicalId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits, SourceAnchorHandle,
};
use hwpx_package::{
    WriterLimits,
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        fields::{
            ImportedDocumentFields,
            bookmark_insertion::{
                SourceBookmarkInsertion as Request, SourceBookmarkInsertionError as E,
            },
        },
        forms::ImportedDocumentForms,
    },
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, path::Path};
#[path = "support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type Result<T = ()> = std::result::Result<T, Box<dyn Error>>;
fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn require(ok: bool) -> Result {
    if ok {
        Ok(())
    } else {
        Err("P626_INSERTION_ASSERTION_NO_RAW_VALUES".into())
    }
}
fn sample(extra: &str) -> Result<Vec<u8>> {
    base::package(&format!(
        "<hp:p id='1'><hp:run>{}</hp:run><hp:run><hp:ctrl><hp:fieldBegin id='7' fieldid='17' dirty='0' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='Command'>?private-target;6;1;0;0</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>private-existing-cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='7' fieldid='17'/></hp:ctrl></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>private-new-display&amp;原文</hp:t></hp:run>{extra}</hp:p>",
        fixture::marker("private-target")
    ))
}
fn selection(forms: &ImportedDocumentForms) -> Result<(SourceAnchorHandle, LogicalId)> {
    let source = forms.source();
    let mut chosen = None;
    for p in source.parts() {
        if let Some(xml) = p.xml() {
            for (i, n) in xml.elements().iter().enumerate() {
                if n.name().local_name() == "run"
                    && n.first_child().is_some_and(|j| {
                        xml.elements()[j].name().local_name() == "t"
                            && xml.elements()[j].next_sibling().is_none()
                    })
                {
                    chosen = p.element_anchor(i).cloned();
                }
            }
        }
    }
    Ok((
        chosen.ok_or("P626_RUN_ABSENT")?,
        forms
            .body_structure()
            .bookmarks()
            .first()
            .ok_or("P626_TARGET_ABSENT")?
            .reference_id
            .clone(),
    ))
}
#[test]
fn new_field_is_inserted_not_an_existing_command_edit() -> Result {
    let bytes = sample("")?;
    let forms = base::forms(&bytes, "p626")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let proof = forms.reconstruct_source_for_verification(&bytes)?;
    let (run, target) = selection(&forms)?;
    let out = fields.insert_bookmark_reference_from_source_envelope(
        &proof,
        Request {
            run: &run,
            target_id: &target,
            display: Display::BookmarkName,
            hyperlink: false,
        },
        limits()?,
        WriterLimits::default(),
    )?;
    let r = out.receipt();
    require(
        r.inserted_fields == 1
            && r.original_fields == 1
            && r.outside_insertions_exact
            && r.original_selected_run_exact
            && r.same_command_source_envelope_only
            && r.existing_display_text_is_not_evaluated_or_refreshed
            && !r.native_currentness_execution_or_publication_qualified
            && r.source_package_sha256 != r.output_package_sha256,
    )?;
    out.with_verified_bytes(|b| -> Result {
        let f = base::forms(b, "p626")?;
        let fields = ImportedDocumentFields::import(&f)?;
        require(
            fields.fields().len() == 2 && fields.fields().iter().any(|f| f.native_begin_id == 8),
        )
    })??;
    Ok(())
}
#[test]
fn missing_envelope_target_display_and_hyperlink_fail_closed() -> Result {
    let bytes = sample("")?;
    let forms = base::forms(&bytes, "p626")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let proof = forms.reconstruct_source_for_verification(&bytes)?;
    let (run, target) = selection(&forms)?;
    for (display, hyperlink) in [(Display::Page, false), (Display::BookmarkName, true)] {
        require(matches!(
            fields.insert_bookmark_reference_from_source_envelope(
                &proof,
                Request {
                    run: &run,
                    target_id: &target,
                    display,
                    hyperlink
                },
                limits()?,
                WriterLimits::default()
            ),
            Err(E::EnvelopeUnavailable)
        ))?;
    }
    require(matches!(
        fields.insert_bookmark_reference_from_source_envelope(
            &proof,
            Request {
                run: &run,
                target_id: &LogicalId::parse("absent")?,
                display: Display::BookmarkName,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default()
        ),
        Err(E::Target)
    ))
}
#[test]
fn foreign_proof_and_run_anchor_are_rejected() -> Result {
    let bytes = sample("")?;
    let a = base::forms(&bytes, "p626")?;
    let b = base::forms(&bytes, "p626")?;
    let fields = ImportedDocumentFields::import(&a)?;
    let foreign = b.reconstruct_source_for_verification(&bytes)?;
    let (run, target) = selection(&a)?;
    require(matches!(
        fields.insert_bookmark_reference_from_source_envelope(
            &foreign,
            Request {
                run: &run,
                target_id: &target,
                display: Display::BookmarkName,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default()
        ),
        Err(E::Source)
    ))?;
    let foreign = base::forms(&bytes, "other-document")?;
    let (other, _) = selection(&foreign)?;
    let proof = a.reconstruct_source_for_verification(&bytes)?;
    require(matches!(
        fields.insert_bookmark_reference_from_source_envelope(
            &proof,
            Request {
                run: &other,
                target_id: &target,
                display: Display::BookmarkName,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default()
        ),
        Err(E::Selection)
    ))
}
#[test]
fn existing_field_contents_and_non_plain_selection_are_not_wrapped() -> Result {
    let bytes = sample("")?;
    let forms = base::forms(&bytes, "p626")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let proof = forms.reconstruct_source_for_verification(&bytes)?;
    let (_, target) = selection(&forms)?;
    let field = &fields.fields()[0];
    let selected = forms.source().resolve_anchor(&field.begin_anchor)?;
    let xml = selected.part().xml().ok_or("xml")?;
    let begin = selected.element_index().ok_or("index")?;
    let ctrl = xml.elements()[begin].parent().ok_or("ctrl")?;
    let run = xml.elements()[ctrl].parent().ok_or("run")?;
    let anchor = selected.part().element_anchor(run).ok_or("anchor")?;
    require(matches!(
        fields.insert_bookmark_reference_from_source_envelope(
            &proof,
            Request {
                run: anchor,
                target_id: &target,
                display: Display::BookmarkName,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default()
        ),
        Err(E::Selection)
    ))
}
#[test]
fn locks_and_tracked_change_streams_reject_without_mutation() -> Result {
    for extra in [
        "<hp:run lock='1'><hp:t>x</hp:t></hp:run>",
        "<hp:run><hp:ctrl><hp:insertBegin id='3'/></hp:ctrl></hp:run>",
        "<hp:run charTcId='4'><hp:t>x</hp:t></hp:run>",
    ] {
        let bytes = sample(extra)?;
        let forms = base::forms(&bytes, "p626")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let proof = forms.reconstruct_source_for_verification(&bytes)?;
        let (run, target) = selection(&forms)?;
        // A lock-bearing non-plain run may be rejected as selection earlier.
        require(matches!(
            fields.insert_bookmark_reference_from_source_envelope(
                &proof,
                Request {
                    run: &run,
                    target_id: &target,
                    display: Display::BookmarkName,
                    hyperlink: false
                },
                limits()?,
                WriterLimits::default()
            ),
            Err(E::Protection | E::Selection)
        ))?;
    }
    Ok(())
}
#[test]
fn deterministic_identity_limit_and_redacted_receipt() -> Result {
    let bytes = sample("")?;
    let forms = base::forms(&bytes, "p626")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let proof = forms.reconstruct_source_for_verification(&bytes)?;
    let (run, target) = selection(&forms)?;
    let prepare = || {
        fields.insert_bookmark_reference_from_source_envelope(
            &proof,
            Request {
                run: &run,
                target_id: &target,
                display: Display::BookmarkName,
                hyperlink: false,
            },
            limits().map_err(|_| E::Limit)?,
            WriterLimits::default(),
        )
    };
    let a = prepare()?;
    let b = prepare()?;
    require(a.receipt() == b.receipt())?;
    let raw = serde_json::to_string(a.receipt())?;
    require(!raw.contains("private-") && !format!("{a:?}").contains("private-"))?;
    let bounded = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        items_per_kind: 1,
        ..Default::default()
    })?;
    require(matches!(
        fields.insert_bookmark_reference_from_source_envelope(
            &proof,
            Request {
                run: &run,
                target_id: &target,
                display: Display::BookmarkName,
                hyperlink: false
            },
            bounded,
            WriterLimits::default()
        ),
        Err(E::Limit)
    ))
}
#[test]
fn actual_eight_saved_envelopes_produce_new_fields_without_native_execution() -> Result {
    let corpus: serde_json::Value = serde_json::from_str(include_str!(
        "../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
    ))?;
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    for case in corpus["cases"].as_array().ok_or("cases")? {
        let pin = &case["artifacts"]["saved"];
        let name = pin["path"].as_str().ok_or("path")?;
        require(
            name.starts_with("implementation/p09/evidence/private/")
                && !name.contains('\\')
                && !name.split('/').any(|s| s == ".." || s.is_empty()),
        )?;
        let path = root.join(name);
        for p in path.ancestors() {
            let m = p.symlink_metadata()?;
            require(!m.file_type().is_symlink())?;
            #[cfg(windows)]
            {
                use std::os::windows::fs::MetadataExt as _;
                require(m.file_attributes() & 0x400 == 0)?;
            }
        }
        let meta = path.metadata()?;
        require(
            meta.is_file() && meta.len() <= 4194304 && Some(meta.len()) == pin["bytes"].as_u64(),
        )?;
        let bytes = std::fs::read(path)?;
        require(Some(hex::encode(Sha256::digest(&bytes)).as_str()) == pin["sha256"].as_str())?;
        let forms = base::forms(&bytes, "p626-actual")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let proof = forms.reconstruct_source_for_verification(&bytes)?;
        let target = &forms
            .body_structure()
            .bookmarks()
            .first()
            .ok_or("bookmark")?
            .reference_id;
        let display = match case["display"].as_str() {
            Some("page") => Display::Page,
            Some("bookmark_name") => Display::BookmarkName,
            Some("content") => Display::Content,
            Some("relative_position") => Display::RelativePosition,
            _ => return Err("P626_DISPLAY_REJECTED".into()),
        };
        let mut output = None;
        // Try only original, outside-field plain runs; no guessed offset or XML.
        for part in forms.source().parts() {
            if let Some(xml) = part.xml() {
                for (i, n) in xml.elements().iter().enumerate() {
                    if n.name().local_name() != "run" {
                        continue;
                    }
                    let Some(anchor) = part.element_anchor(i) else {
                        continue;
                    };
                    match fields.insert_bookmark_reference_from_source_envelope(
                        &proof,
                        Request {
                            run: anchor,
                            target_id: target,
                            display,
                            hyperlink: case["hyperlink"].as_bool().ok_or("hyperlink")?,
                        },
                        limits()?,
                        WriterLimits::default(),
                    ) {
                        Ok(candidate) => {
                            output = Some(candidate);
                            break;
                        }
                        Err(E::Selection) => {}
                        Err(_) => return Err("P626_ACTUAL_INSERTION_REJECTED_NO_RAW_VALUES".into()),
                    }
                }
                if output.is_some() {
                    break;
                }
            }
        }
        let out = output.ok_or("P626_NO_QUALIFIED_PLAIN_RUN")?;
        require(
            out.receipt().inserted_fields == 1
                && out.receipt().outside_insertions_exact
                && !out
                    .receipt()
                    .native_currentness_execution_or_publication_qualified,
        )?;
    }
    Ok(())
}
