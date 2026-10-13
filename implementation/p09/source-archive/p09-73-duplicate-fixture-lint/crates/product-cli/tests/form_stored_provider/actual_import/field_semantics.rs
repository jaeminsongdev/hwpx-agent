use super::*;
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use hwpx_agent_cli::form_stored_provider::actual_import::field_ranges::{
    StoredFieldRangeImportError, semantics::StoredFieldSemanticImportError,
};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{FIELD_SEMANTICS_PROFILE, FIELD_SEMANTICS_SCOPE, ImportedDocumentFieldSemantics},
};
#[path = "../../../../hwpx-package/tests/support/document_import_field_fixture.rs"]
mod fixture;

#[test]
fn actual_captured_source_meaning_matches_direct_import_without_ingest_or_head_write() -> TestResult
{
    let bytes = fixture::captured()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let ranges = source.import_field_ranges(&provider, 5)?;
    let meaning = ranges.import_semantics(&provider, 6)?;
    let direct_forms = fixture::forms(&bytes, "actual-form-document")?;
    let direct_ranges = ImportedDocumentFields::import(&direct_forms)?;
    let direct = ImportedDocumentFieldSemantics::import(&direct_ranges)?;
    assert_eq!(meaning.graph(), direct.graph());
    assert_eq!(meaning.observations(), direct.observations());
    assert_eq!(meaning.receipt().semantics, *direct.receipt());
    assert_eq!(meaning.receipt().semantics.https_targets, 1);
    assert_eq!(meaning.verify(&provider, 7)?, *meaning.receipt());
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    assert_eq!(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.ingested")
            .count(),
        2
    );
    let metadata = format!("{meaning:?}{}", serde_json::to_string(meaning.receipt())?);
    assert!(!metadata.contains("https://") && !metadata.contains("Command"));
    Ok(())
}
#[test]
fn revoked_acl_denies_new_meaning_import_and_cached_meaning_verify() -> TestResult {
    let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let ranges = source.import_field_ranges(&provider, 5)?;
    let meaning = ranges.import_semantics(&provider, 6)?;
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        7,
    )?;
    for denied in [
        ranges
            .import_semantics(&provider, 8)
            .map(|v| v.receipt().clone()),
        meaning.verify(&provider, 8),
    ] {
        assert!(matches!(
            denied,
            Err(StoredFieldSemanticImportError::Source(
                StoredFieldRangeImportError::Source(StoredActualFormImportError::Source(
                    StoredFormError::Artifact
                ))
            ))
        ));
    }
    Ok(())
}
#[test]
fn actual_aead_tamper_denies_meaning_before_supported_tuple_parsing() -> TestResult {
    let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let ranges = source.import_field_ranges(&provider, 5)?;
    let meaning = ranges.import_semantics(&provider, 6)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(matches!(
        meaning.verify(&provider, 7),
        Err(StoredFieldSemanticImportError::Source(
            StoredFieldRangeImportError::Source(StoredActualFormImportError::Source(
                StoredFormError::Artifact
            ))
        ))
    ));
    assert!(ranges.import_semantics(&provider, 7).is_err());
    Ok(())
}
#[test]
fn head_advance_invalidates_meanings_even_when_result_bytes_are_same() -> TestResult {
    let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let ranges = source.import_field_ranges(&provider, 5)?;
    let meaning = ranges.import_semantics(&provider, 6)?;
    stored.advance()?;
    assert!(matches!(
        meaning.verify(&provider, 7),
        Err(StoredFieldSemanticImportError::Source(
            StoredFieldRangeImportError::Source(StoredActualFormImportError::Source(
                StoredFormError::Head
            ))
        ))
    ));
    assert!(ranges.import_semantics(&provider, 7).is_err());
    Ok(())
}
#[test]
fn all_scope5_substitutions_reject_fresh_and_cached_meaning_models() -> TestResult {
    let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let ranges = source.import_field_ranges(&provider, 5)?;
    let meaning = ranges.import_semantics(&provider, 6)?;
    for variant in 0..5 {
        let tenant = if variant == 4 {
            TenantId::new(uuid::Uuid::from_u128(702))?
        } else {
            stored.reader.tenant_id()
        };
        let subject = if variant == 3 {
            stored.owner.subject()
        } else {
            stored.reader.subject()
        };
        let actor = RequestContext::new(tenant, subject, [AuthScope::DocumentRead]);
        let revision_actor = revision_service::RevisionRequestContext::new(tenant, subject);
        let project = if variant == 2 {
            revision_service::ProjectId::parse("prj_70000000000000000000000000000002")?
        } else {
            stored.project
        };
        let branch = if variant == 1 {
            revision_service::BranchId::parse("brn_70000000000000000000000000000002")?
        } else {
            stored.branch
        };
        let document = if variant == 0 {
            "different-document"
        } else {
            "actual-form-document"
        };
        let other = StoredFormProvider::bind(
            &stored.artifacts,
            &stored.revisions,
            &actor,
            &revision_actor,
            project,
            branch,
            DocumentId::parse(document)?,
        )?;
        for denied in [
            ranges
                .import_semantics(&other, 7)
                .map(|v| v.receipt().clone()),
            meaning.verify(&other, 7),
        ] {
            assert!(matches!(
                denied,
                Err(StoredFieldSemanticImportError::Source(
                    StoredFieldRangeImportError::Source(StoredActualFormImportError::Binding)
                ))
            ));
        }
    }
    Ok(())
}
#[test]
fn semantic_partial_markers_each_deny_full_context_without_predecessor_markers() -> TestResult {
    let bytes = fixture::package("<hp:p id='1'><hp:run><hp:t>plain</hp:t></hp:run></hp:p>")?;
    let forms = fixture::forms(&bytes, "actual-form-document")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    for (key, value) in [
        ("field_semantics_import_profile", FIELD_SEMANTICS_PROFILE),
        ("field_semantics_import_scope", FIELD_SEMANTICS_SCOPE),
    ] {
        let mut draft = meanings.graph().clone().into_draft();
        draft.source_profile = None;
        draft.metadata = Properties::new();
        draft
            .metadata
            .insert(key, PropertyValue::Text(value.into()));
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                *ContentDigest::of(&bytes).as_bytes(),
                RevisionId::parse("field-meaning-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
