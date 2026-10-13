use super::*;
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        catalog::{
            ImportedDocumentCatalog,
            fonts::{FONT_IMPORT_PROFILE, FONT_IMPORT_SCOPE, ImportedDocumentFonts},
        },
    },
};
#[path = "../../../../hwpx-package/tests/support/document_import_fonts_fixture.rs"]
mod fixture;
#[path = "../../../../hwpx-package/tests/support/document_import_settings_inputs.rs"]
mod inputs;
#[test]
fn actual36_stored_fonts_match_direct_without_ingest_head_write_or_full_admission() -> TestResult {
    let mut count = 0;
    for bytes in inputs::actual_corpus()? {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let catalog = meanings.import_catalog(&provider, 7)?;
        let before = catalog.graph().clone();
        let fonts = catalog.import_fonts(&provider, 8)?;
        let forms = fixture::forms(&bytes, "actual-form-document")?;
        let direct_fields = ImportedDocumentFields::import(&forms)?;
        let direct_meanings = ImportedDocumentFieldSemantics::import(&direct_fields)?;
        let direct_catalog = ImportedDocumentCatalog::import(&direct_meanings)?;
        let direct = ImportedDocumentFonts::import(&direct_catalog)?;
        fixture::verify_whole(&forms, &direct_catalog, &direct)?;
        assert_eq!(fonts.graph(), direct.graph());
        assert_eq!(fonts.definitions(), direct.definitions());
        assert_eq!(fonts.links(), direct.links());
        assert_eq!(fonts.receipt().fonts, *direct.receipt());
        assert_eq!(fonts.verify(&provider, 9)?, *fonts.receipt());
        assert_eq!(catalog.graph(), &before);
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
                .filter(|e| e.event == "artifact.ingested")
                .count(),
            2
        );
        assert!(matches!(
            FullDocumentFormContext::bind(
                fonts.graph(),
                fonts.graph().canonical_sha256()?,
                fonts.receipt().fonts.source_package_sha256,
                RevisionId::parse("font-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
        assert_eq!(format!("{fonts:?}"), "StoredImportedFonts(<redacted>)");
        count += 1;
    }
    assert_eq!(count, 36);
    Ok(())
}
#[test]
fn creation_and_cached_fonts_reject_aead_acl_head_and_quarantine() -> TestResult {
    let bytes = inputs::actual_corpus()?.remove(0);
    for failure in 0..4 {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let catalog = meanings.import_catalog(&provider, 7)?;
        let fonts = catalog.import_fonts(&provider, 8)?;
        match failure {
            0 => stored.blobs.tamper.store(true, Ordering::SeqCst),
            1 => stored.artifacts.set_permissions(
                &stored.owner,
                stored.result,
                stored.reader.subject(),
                BTreeSet::new(),
                9,
            )?,
            2 => {
                stored.advance()?;
            }
            _ => stored.artifacts.quarantine(
                &stored.owner,
                stored.result,
                artifact_service::QuarantineReason::parse("P80_FIXTURE_QUARANTINE")?,
                9,
            )?,
        }
        assert!(catalog.import_fonts(&provider, 10).is_err());
        assert!(fonts.verify(&provider, 10).is_err());
    }
    Ok(())
}
#[test]
fn fonts_reject_all_five_scope_substitutions_on_new_and_cached_models() -> TestResult {
    let stored = StoredFixture::new(
        &inputs::actual_corpus()?.remove(0),
        ArtifactKind::Result,
        false,
    )?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let fonts = catalog.import_fonts(&provider, 8)?;
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
        assert!(catalog.import_fonts(&other, 9).is_err());
        assert!(fonts.verify(&other, 9).is_err());
    }
    Ok(())
}
#[test]
fn font_profile_and_scope_each_independently_reject_full_context() -> TestResult {
    let forms = fixture::forms(&inputs::actual_corpus()?.remove(0), "font-partial")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let fonts = ImportedDocumentFonts::import(&catalog)?;
    for (key, value) in [
        ("font_catalog_import_profile", FONT_IMPORT_PROFILE),
        ("font_catalog_import_scope", FONT_IMPORT_SCOPE),
    ] {
        let mut draft = fonts.graph().clone().into_draft();
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
                fonts.receipt().source_package_sha256,
                RevisionId::parse("font-partial-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
#[test]
fn missing_read_scope_rejects_provider_before_font_reuse() -> TestResult {
    let stored = StoredFixture::new(
        &inputs::actual_corpus()?.remove(0),
        ArtifactKind::Result,
        false,
    )?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let fonts = catalog.import_fonts(&provider, 8)?;
    let actor = RequestContext::new(stored.reader.tenant_id(), stored.reader.subject(), []);
    assert!(matches!(
        StoredFormProvider::bind(
            &stored.artifacts,
            &stored.revisions,
            &actor,
            &stored.revision_context,
            stored.project,
            stored.branch,
            DocumentId::parse("actual-form-document")?
        ),
        Err(StoredFormError::Scope)
    ));
    assert_eq!(fonts.verify(&provider, 9)?, *fonts.receipt());
    Ok(())
}
