//! Current point-target authoring rules; no Native/SQL/publication or old suite replay.
use super::*;
use hwpx_agent_cli::{
    form_stored_provider::actual_import::bookmark_command_output::StoredBookmarkCommandError,
    reference_validation_product::ReferenceValidationProductOperation as Product,
};
use hwpx_package::{
    cross_reference_sdk::{SdkCrossReferenceCandidate, SdkCrossReferenceTarget},
    document_import::{
        SourceImportLimits,
        fields::{
            bookmark_insertion::SourceBookmarkInsertionError as InsertionError,
            semantics::source_index::{
                SourceFieldMeaningIndex,
                bookmark_updates::{
                    SourceBookmarkCommandChange as Change,
                    SourceBookmarkCommandError as CommandError,
                },
            },
        },
        reference_targets::sdk::authoring_display::{
            PointBookmarkAuthoringDisplay, PointBookmarkDisplayError,
        },
    },
};

fn selected(bytes: &[u8]) -> Result<(SourceAnchorHandle, LogicalId)> {
    let s = StoredFixture::new(bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    selection(&p.import_actual_forms(s.head, 4)?)
}
fn direct_insert(bytes: &[u8], display: Display, hyperlink: bool)
-> Result<hwpx_package::document_import::fields::bookmark_insertion::generated::SourceBookmarkCreationCandidate, InsertionError>{
    let (run, target) = selected(bytes).map_err(|_| InsertionError::Selection)?;
    Product::prepare_source_bookmark_reference_insertion(
        bytes,
        DocumentId::parse(DOC).map_err(|_| InsertionError::Source)?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
        limits().map_err(|_| InsertionError::Limit)?,
        Request {
            run: &run,
            target_id: &target,
            display,
            hyperlink,
        },
        WriterLimits::default(),
    )
}
fn existing() -> Result<Vec<u8>> {
    Ok(direct_insert(&sample()?, Display::Page, false)?.with_verified_bytes(|v| v.to_vec())?)
}
struct Edit {
    id: LogicalId,
    field: [u8; 32],
    meaning: [u8; 32],
    target: LogicalId,
}
impl Edit {
    fn request(&self, display: Display, hyperlink: bool) -> Change<'_> {
        Change {
            reference_id: &self.id,
            expected_source_field_sha256: self.field,
            expected_meaning_sha256: self.meaning,
            target_id: &self.target,
            display,
            hyperlink,
        }
    }
}
fn edit(fields: &ImportedDocumentFields<'_>) -> Result<Edit> {
    let index = SourceFieldMeaningIndex::import(fields, limits()?)?;
    let (i, field) = fields
        .fields()
        .iter()
        .enumerate()
        .find(|(_, f)| f.native_kind == "CROSSREF")
        .ok_or("field")?;
    let hwpx_package::document_import::fields::semantics::ImportedFieldMeaning::BookmarkCrossReference {command} = &index.observations()[i].meaning else {return Err("meaning".into());};
    let hwpx_package::document_import::fields::bookmark_crossref::SourceBookmarkResolution::Bound {
        logical_target_id,
        ..
    } = &command.target
    else {
        return Err("target".into());
    };
    Ok(Edit {
        id: field.reference_id.clone(),
        field: field.begin_anchor.fingerprint_sha256,
        meaning: index.meaning_sha256(i)?,
        target: logical_target_id.clone(),
    })
}

#[test]
fn point_display_rule_does_not_rewrite_or_disable_inert_sdk_discovery() -> Result {
    require(matches!(
        PointBookmarkAuthoringDisplay::try_from(Display::Content),
        Err(PointBookmarkDisplayError::ContentRequiresBlockBookmark)
    ))?;
    require(matches!(
        PointBookmarkAuthoringDisplay::try_from(Display::ObjectNumber),
        Err(PointBookmarkDisplayError::Unsupported)
    ))?;
    for display in [
        Display::Page,
        Display::BookmarkName,
        Display::RelativePosition,
    ] {
        require(PointBookmarkAuthoringDisplay::try_from(display).is_ok())?;
    }
    let raw = SdkCrossReferenceCandidate::build(
        SdkCrossReferenceTarget::Bookmark {
            exact_source_name: "private-target",
        },
        Display::Content,
        false,
    )?;
    require(
        raw.requires_native_target_qualification() && raw.command_for_discovery().contains(";6;2;"),
    )
}
#[test]
fn direct_content_insert_rejects_before_any_candidate_for_both_link_options() -> Result {
    let bytes = sample()?;
    let before = bytes.clone();
    for link in [false, true] {
        require(matches!(
            direct_insert(&bytes, Display::Content, link),
            Err(InsertionError::ContentRequiresBlockBookmark)
        ))?;
    }
    require(bytes == before)
}
#[test]
fn stored_content_insert_denies_without_head_or_metadata_mutation() -> Result {
    let bytes = sample()?;
    for hyperlink in [false, true] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let ctx = write_context(&s);
        let p = provider(&s, &ctx)?;
        let before = s.metadata.find(s.owner.tenant_id(), s.result)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let (run, target) = selection(&source)?;
        require(matches!(
            source.into_bookmark_insertion_candidate(
                &p,
                Request {
                    run: &run,
                    target_id: &target,
                    display: Display::Content,
                    hyperlink
                },
                limits()?,
                WriterLimits::default(),
                5
            ),
            Err(E::Output(InsertionError::ContentRequiresBlockBookmark))
        ))?;
        require(
            s.revisions.head(&s.revision_context, s.project, s.branch)? == s.head
                && s.metadata.find(s.owner.tenant_id(), s.result)? == before,
        )?;
    }
    Ok(())
}
#[test]
fn direct_existing_command_content_rejects_without_output_or_cache_update() -> Result {
    let bytes = existing()?;
    let before = bytes.clone();
    let forms = base::forms(&bytes, DOC)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let selected = edit(&fields)?;
    for link in [false, true] {
        require(matches!(
            Product::prepare_source_bookmark_command_changes(
                &bytes,
                DocumentId::parse(DOC)?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                limits()?,
                &[selected.request(Display::Content, link)],
                WriterLimits::default()
            ),
            Err(CommandError::ContentRequiresBlockBookmark)
        ))?;
    }
    require(bytes == before)
}
#[test]
fn stored_existing_command_content_denies_without_current_state_mutation() -> Result {
    let bytes = existing()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let fields = ImportedDocumentFields::import(source.imported())?;
    let selected = edit(&fields)?;
    let before = s.metadata.find(s.owner.tenant_id(), s.result)?;
    for link in [false, true] {
        require(matches!(
            source.prepare_bookmark_command_candidate(
                &p,
                &[selected.request(Display::Content, link)],
                limits()?,
                WriterLimits::default(),
                5
            ),
            Err(StoredBookmarkCommandError::Output(
                CommandError::ContentRequiresBlockBookmark
            ))
        ))?;
    }
    require(
        s.revisions.head(&s.revision_context, s.project, s.branch)? == s.head
            && s.metadata.find(s.owner.tenant_id(), s.result)? == before,
    )
}
#[test]
fn write_permission_and_source_drift_still_precede_display_denial() -> Result {
    let bytes = existing()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let p = provider(&s, &s.reader)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let fields = ImportedDocumentFields::import(source.imported())?;
    let selected = edit(&fields)?;
    require(matches!(
        source.prepare_bookmark_command_candidate(
            &p,
            &[selected.request(Display::Content, false)],
            limits()?,
            WriterLimits::default(),
            5
        ),
        Err(StoredBookmarkCommandError::Permission)
    ))?;
    let insertion_bytes = sample()?;
    let insertion_fixture = StoredFixture::new(&insertion_bytes, ArtifactKind::Result, false)?;
    let insertion_provider = provider(&insertion_fixture, &insertion_fixture.reader)?;
    let insertion_source = insertion_provider.import_actual_forms(insertion_fixture.head, 4)?;
    let (run, target) = selection(&insertion_source)?;
    require(matches!(
        insertion_source.into_bookmark_insertion_candidate(
            &insertion_provider,
            Request {
                run: &run,
                target_id: &target,
                display: Display::Content,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default(),
            5
        ),
        Err(E::Permission)
    ))?;
    require(matches!(
        Product::prepare_source_bookmark_command_changes(
            &bytes,
            DocumentId::parse(DOC)?,
            [0; 32],
            SourceImportLimits::default(),
            limits()?,
            &[selected.request(Display::Content, false)],
            WriterLimits::default()
        ),
        Err(CommandError::Source)
    ))?;
    require(matches!(
        Product::prepare_source_bookmark_reference_insertion(
            &insertion_bytes,
            DocumentId::parse(DOC)?,
            [0; 32],
            SourceImportLimits::default(),
            limits()?,
            Request {
                run: &run,
                target_id: &target,
                display: Display::Content,
                hyperlink: false
            },
            WriterLimits::default()
        ),
        Err(InsertionError::Source)
    ))
}
#[test]
fn actual_current_source_keeps_six_expected_outputs_and_denies_two_point_content_cases() -> Result {
    let expected: Value = serde_json::from_str(EXPECTED)?;
    let bytes = read_pin(&expected["source"])?;
    let mut allowed = 0;
    let mut denied = 0;
    for case in expected["cases"].as_array().ok_or("cases")? {
        let display = match case["display"].as_str() {
            Some("page") => Display::Page,
            Some("bookmark_name") => Display::BookmarkName,
            Some("relative_position") => Display::RelativePosition,
            Some("content") => Display::Content,
            _ => return Err("display".into()),
        };
        let candidate = direct_insert(&bytes, display, case["hyperlink"].as_bool().ok_or("link")?);
        if display == Display::Content {
            require(matches!(
                candidate,
                Err(InsertionError::ContentRequiresBlockBookmark)
            ))?;
            denied += 1;
        } else {
            let candidate = candidate?;
            require(
                hex::encode(candidate.receipt().output_package_sha256) == case["output_sha256"],
            )?;
            require(
                !candidate
                    .receipt()
                    .native_currentness_execution_or_publication_qualified,
            )?;
            allowed += 1;
        }
    }
    require(allowed == 6 && denied == 2)
}
#[test]
fn stored_six_valid_point_variants_remain_owned_candidates_not_write_grants() -> Result {
    let bytes = sample()?;
    for display in [
        Display::Page,
        Display::BookmarkName,
        Display::RelativePosition,
    ] {
        for link in [false, true] {
            let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
            let ctx = write_context(&s);
            let p = provider(&s, &ctx)?;
            let candidate = prepare(p.import_actual_forms(s.head, 4)?, &p, display, link)?;
            require(
                !candidate.receipt().execution_or_publication_authority
                    && candidate.receipt().output.inserted_fields == 1,
            )?;
            require(s.revisions.head(&s.revision_context, s.project, s.branch)? == s.head)?;
        }
    }
    Ok(())
}
#[test]
fn valid_command_edit_bytes_match_original_lowerer_and_never_refresh_cache() -> Result {
    let bytes = existing()?;
    let forms = base::forms(&bytes, DOC)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let selected = edit(&fields)?;
    let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
    let proof = forms.reconstruct_source_for_verification(&bytes)?;
    for display in [
        Display::Page,
        Display::BookmarkName,
        Display::RelativePosition,
    ] {
        let requests = [selected.request(display, true)];
        let raw =
            index.lower_bookmark_command_changes(&proof, &requests, WriterLimits::default())?;
        let product = Product::prepare_source_bookmark_command_changes(
            &bytes,
            DocumentId::parse(DOC)?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
            limits()?,
            &requests,
            WriterLimits::default(),
        )?;
        require(
            raw.with_verified_bytes(|v| v.to_vec())?
                == product.with_verified_bytes(|v| v.to_vec())?
                && product.receipt().cached_values_preserved_not_refreshed,
        )?;
    }
    Ok(())
}

#[test]
fn stored_valid_command_edits_keep_current_authorization_and_do_not_commit() -> Result {
    let bytes = existing()?;
    for display in [
        Display::Page,
        Display::BookmarkName,
        Display::RelativePosition,
    ] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let ctx = write_context(&s);
        let p = provider(&s, &ctx)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let fields = ImportedDocumentFields::import(source.imported())?;
        let selected = edit(&fields)?;
        let candidate = source.prepare_bookmark_command_candidate(
            &p,
            &[selected.request(display, true)],
            limits()?,
            WriterLimits::default(),
            5,
        )?;
        let output = candidate.with_verified_bytes(&p, 6, |v| v.to_vec())?;
        require(
            !output.is_empty()
                && s.revisions.head(&s.revision_context, s.project, s.branch)? == s.head,
        )?;
    }
    Ok(())
}
