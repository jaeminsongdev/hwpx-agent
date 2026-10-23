use super::field_ranges::fixture;
use super::*;
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use hwpx_agent_cli::form_stored_provider::actual_import::field_ranges::semantics::catalog::security::StoredActiveSecurityImportError;
use hwpx_package::{
    ActivationKind, ActiveContentError,
    document_import::fields::{
        ImportedDocumentFields,
        semantics::{ImportedDocumentFieldSemantics, catalog::{
            ImportedDocumentCatalog,
            security::{ActiveSecurityImportError, ImportedDocumentActiveSecurity,
                NativeSecurityQualification, SECURITY_IMPORT_PROFILE, SECURITY_IMPORT_SCOPE},
        }},
    },
};

fn actions() -> [ActivationKind; 6] {
    [
        ActivationKind::Ole,
        ActivationKind::Multimedia,
        ActivationKind::EmbeddedExecutable,
        ActivationKind::ScriptMacro,
        ActivationKind::FormCommand,
        ActivationKind::ExternalLink,
    ]
}

#[test]
fn authenticated_actual_security_matches_direct_whole_graph_and_denies_every_activation()
-> TestResult {
    let bytes = fixture::captured()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let security = catalog.import_active_security(&provider, 8)?;
    let forms = fixture::forms(&bytes, "actual-form-document")?;
    let direct_fields = ImportedDocumentFields::import(&forms)?;
    let direct_meanings = ImportedDocumentFieldSemantics::import(&direct_fields)?;
    let direct_catalog = ImportedDocumentCatalog::import(&direct_meanings)?;
    let direct = ImportedDocumentActiveSecurity::import(&direct_catalog)?;
    assert_eq!(security.graph(), direct.graph());
    assert_eq!(security.controls(), direct.controls());
    assert_eq!(security.resources(), direct.resources());
    assert_eq!(security.receipt().security, *direct.receipt());
    assert_eq!(security.verify(&provider, 9)?, *security.receipt());
    assert_eq!(
        security.receipt().security.native_security,
        NativeSecurityQualification::NotAssessedByActiveContentInventory
    );
    for action in actions() {
        assert!(matches!(security.require_activation(&provider, action, 10),
            Err(StoredActiveSecurityImportError::Security(ActiveSecurityImportError::Inventory(
                ActiveContentError::ActivationDenied { action: denied }))) if denied == action));
    }
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
        format!("{security:?}"),
        "StoredImportedActiveSecurity(<redacted>)"
    );
    Ok(())
}

#[test]
fn security_rechecks_aead_acl_and_head_before_cached_inspection_or_policy_denial() -> TestResult {
    for failure in 0..3 {
        let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let catalog = meanings.import_catalog(&provider, 7)?;
        let security = catalog.import_active_security(&provider, 8)?;
        match failure {
            0 => stored.blobs.tamper.store(true, Ordering::SeqCst),
            1 => {
                stored.artifacts.set_permissions(
                    &stored.owner,
                    stored.result,
                    stored.reader.subject(),
                    BTreeSet::new(),
                    9,
                )?;
            }
            _ => {
                stored.advance()?;
            }
        }
        assert!(security.verify(&provider, 10).is_err());
        assert!(catalog.import_active_security(&provider, 10).is_err());
        for action in actions() {
            assert!(matches!(
                security.require_activation(&provider, action, 10),
                Err(StoredActiveSecurityImportError::Source(_))
            ));
        }
    }
    Ok(())
}

#[test]
fn all_scope_substitutions_deny_existing_security_binding_and_recreation() -> TestResult {
    let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let security = catalog.import_active_security(&provider, 8)?;
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
        assert!(security.verify(&other, 9).is_err());
        assert!(catalog.import_active_security(&other, 9).is_err());
        assert!(matches!(
            security.require_activation(&other, ActivationKind::FormCommand, 9),
            Err(StoredActiveSecurityImportError::Source(_))
        ));
    }
    Ok(())
}

#[test]
fn each_security_partial_marker_independently_denies_full_document_context() -> TestResult {
    let forms = fixture::forms(&fixture::captured()?, "actual-form-document")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    for (key, value) in [
        ("active_security_import_profile", SECURITY_IMPORT_PROFILE),
        ("active_security_import_scope", SECURITY_IMPORT_SCOPE),
    ] {
        let mut draft = security.graph().clone().into_draft();
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
                catalog.receipt().source_package_sha256,
                RevisionId::parse("security-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}

#[test]
fn all_ten_actual_form_sources_and_results_have_source_bound_blocked_controls() -> TestResult {
    let (_, manifest) = fixture_manifest()?;
    let mut bindings = 0;
    let mut represented = 0;
    let mut native_inventory_gaps = 0;
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
            assert_eq!(security.verify(&provider, 9)?, *security.receipt());
            assert!(!security.receipt().security.activation_allowed);
            bindings += security.controls().len();
            represented += security.receipt().security.represented_control_bindings;
            assert_eq!(
                security.native_forms().len(),
                source.imported().forms().len()
            );
            native_inventory_gaps += security
                .receipt()
                .security
                .native_forms_not_in_original_inventory;
        }
    }
    assert!(bindings > 0);
    assert_eq!(bindings, represented);
    assert!(native_inventory_gaps > 0);
    Ok(())
}
