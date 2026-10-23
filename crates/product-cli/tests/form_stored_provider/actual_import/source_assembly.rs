use super::formula_evaluation::fixture::inputs;
use super::*;
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        catalog::{
            ImportedDocumentCatalog,
            assembly::{
                DOCUMENT_ASSEMBLY_PROFILE, DOCUMENT_ASSEMBLY_SCOPE, ImportedDocumentAssembly,
            },
        },
    },
};
fn direct_forms(bytes: &[u8]) -> Result<ImportedDocumentForms, Box<dyn std::error::Error>> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse("actual-form-document")?,
            *ContentDigest::of(bytes).as_bytes(),
            SourceImportLimits::default(),
        )?,
    )?)
}
#[test]
fn actual36_stored_whole_assembly_and_sidecars_match_direct_without_writes() -> TestResult {
    let mut count = 0;
    for bytes in inputs::actual_corpus()? {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let catalog = meanings.import_catalog(&provider, 7)?;
        let assembly = catalog.import_document_assembly(&provider, 8)?;
        let forms = direct_forms(&bytes)?;
        let direct_fields = ImportedDocumentFields::import(&forms)?;
        let direct_meanings = ImportedDocumentFieldSemantics::import(&direct_fields)?;
        let direct_catalog = ImportedDocumentCatalog::import(&direct_meanings)?;
        let direct = ImportedDocumentAssembly::import(&direct_catalog)?;
        let a = assembly.imported();
        assert_eq!(a.graph(), direct.graph());
        assert_eq!(a.font_definitions(), direct.font_definitions());
        assert_eq!(a.font_links(), direct.font_links());
        assert_eq!(a.section_settings(), direct.section_settings());
        assert_eq!(a.inventory(), direct.inventory());
        assert_eq!(a.active_controls(), direct.active_controls());
        assert_eq!(a.active_resources(), direct.active_resources());
        assert_eq!(a.native_forms(), direct.native_forms());
        assert_eq!(a.formula_values(), direct.formula_values());
        assert_eq!(
            a.formula_source_bindings(),
            direct.formula_source_bindings()
        );
        assert_eq!(assembly.receipt().assembly, *direct.receipt());
        assert_eq!(assembly.verify(&provider, 9)?, *assembly.receipt());
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
                assembly.graph(),
                assembly.graph().canonical_sha256()?,
                *ContentDigest::of(&bytes).as_bytes(),
                RevisionId::parse("assembly-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
        assert_eq!(
            format!("{assembly:?}"),
            "StoredImportedDocumentAssembly(<redacted>)"
        );
        count += 1;
    }
    assert_eq!(count, 36);
    Ok(())
}
#[test]
fn assembly_creation_and_cached_verify_reject_acl_aead_head_and_quarantine() -> TestResult {
    let bytes = inputs::actual_corpus()?.remove(0);
    for failure in 0..4 {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let catalog = meanings.import_catalog(&provider, 7)?;
        let assembly = catalog.import_document_assembly(&provider, 8)?;
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
            2 => {
                stored.advance()?;
            }
            _ => {
                stored.artifacts.quarantine(
                    &stored.owner,
                    stored.result,
                    artifact_service::QuarantineReason::parse("P81_TEST_QUARANTINE")?,
                    9,
                )?;
            }
        }
        assert!(catalog.import_document_assembly(&provider, 10).is_err());
        assert!(assembly.verify(&provider, 10).is_err());
    }
    Ok(())
}
#[test]
fn assembly_rejects_all_five_authenticated_scope_substitutions() -> TestResult {
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
    let assembly = catalog.import_document_assembly(&provider, 8)?;
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
            "other-document"
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
        assert!(catalog.import_document_assembly(&other, 9).is_err());
        assert!(assembly.verify(&other, 9).is_err());
    }
    Ok(())
}
#[test]
fn assembly_profile_and_scope_individually_deny_full_context() -> TestResult {
    let bytes = inputs::actual_corpus()?.remove(0);
    let forms = direct_forms(&bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let assembly = ImportedDocumentAssembly::import(&catalog)?;
    for (key, value) in [
        ("document_assembly_profile", DOCUMENT_ASSEMBLY_PROFILE),
        ("document_assembly_scope", DOCUMENT_ASSEMBLY_SCOPE),
    ] {
        let mut draft = assembly.graph().clone().into_draft();
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
                RevisionId::parse("assembly-partial-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
