use super::field_ranges::fixture;
use super::*;
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        catalog::{
            ImportedDocumentCatalog,
            security::{
                ImportedDocumentActiveSecurity,
                settings::{
                    ImportedDocumentSectionSettings, SETTINGS_IMPORT_PROFILE, SETTINGS_IMPORT_SCOPE,
                },
            },
        },
    },
};

#[test]
fn actual_stored_settings_match_direct_whole_graph_without_ingest_or_head_write() -> TestResult {
    let bytes = fixture::captured()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let security = catalog.import_active_security(&provider, 8)?;
    let settings = security.import_section_settings(&provider, 9)?;
    let forms = fixture::forms(&bytes, "actual-form-document")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let direct_security = ImportedDocumentActiveSecurity::import(&catalog)?;
    let direct = ImportedDocumentSectionSettings::import(&direct_security)?;
    assert_eq!(settings.graph(), direct.graph());
    assert_eq!(settings.settings(), direct.settings());
    assert_eq!(settings.receipt().settings, *direct.receipt());
    assert_eq!(settings.verify(&provider, 10)?, *settings.receipt());
    assert_eq!(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.ingested")
            .count(),
        2
    );
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    assert_eq!(
        format!("{settings:?}"),
        "StoredImportedSectionSettings(<redacted>)"
    );
    Ok(())
}
#[test]
fn creation_and_cached_settings_recheck_original_aead_acl_and_head() -> TestResult {
    for failure in 0..3 {
        let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let catalog = meanings.import_catalog(&provider, 7)?;
        let security = catalog.import_active_security(&provider, 8)?;
        let settings = security.import_section_settings(&provider, 9)?;
        match failure {
            0 => stored.blobs.tamper.store(true, Ordering::SeqCst),
            1 => {
                stored.artifacts.set_permissions(
                    &stored.owner,
                    stored.result,
                    stored.reader.subject(),
                    BTreeSet::new(),
                    10,
                )?;
            }
            _ => {
                stored.advance()?;
            }
        }
        assert!(settings.verify(&provider, 11).is_err());
        assert!(security.import_section_settings(&provider, 11).is_err());
    }
    Ok(())
}
#[test]
fn settings_bindings_reject_all_five_authentication_scope_substitutions() -> TestResult {
    let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let security = catalog.import_active_security(&provider, 8)?;
    let settings = security.import_section_settings(&provider, 9)?;
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
        assert!(settings.verify(&other, 10).is_err());
        assert!(security.import_section_settings(&other, 10).is_err());
    }
    Ok(())
}
#[test]
fn each_settings_partial_qualifier_denies_full_context_independently() -> TestResult {
    let forms = fixture::forms(&fixture::captured()?, "actual-form-document")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    let settings = ImportedDocumentSectionSettings::import(&security)?;
    for (key, value) in [
        ("section_settings_import_profile", SETTINGS_IMPORT_PROFILE),
        ("section_settings_import_scope", SETTINGS_IMPORT_SCOPE),
    ] {
        let mut draft = settings.graph().clone().into_draft();
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
                settings.receipt().source_package_sha256,
                RevisionId::parse("settings-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
#[test]
fn all_ten_actual_form_sources_and_results_retain_security_with_real_settings() -> TestResult {
    let (_, manifest) = fixture_manifest()?;
    let mut count = 0;
    for row in manifest["cases"].as_array().ok_or("cases")? {
        for kind in ["source", "output"] {
            let bytes = fixture_bytes(row["case"].as_str().ok_or("case")?, kind)?;
            let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
            let provider = stored.provider()?;
            let source = provider.import_actual_forms(stored.head, 4)?;
            let fields = source.import_field_ranges(&provider, 5)?;
            let meanings = fields.import_semantics(&provider, 6)?;
            let catalog = meanings.import_catalog(&provider, 7)?;
            let security = catalog.import_active_security(&provider, 8)?;
            let settings = security.import_section_settings(&provider, 9)?;
            assert_eq!(settings.verify(&provider, 10)?, *settings.receipt());
            assert_eq!(
                settings.graph().clone().into_draft().security_state,
                security.graph().clone().into_draft().security_state
            );
            count += 1;
        }
    }
    assert_eq!(count, 10);
    Ok(())
}
