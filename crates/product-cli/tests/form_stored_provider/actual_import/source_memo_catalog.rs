use super::*;
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        catalog::{ImportedDocumentCatalog, assembly::ImportedDocumentAssembly},
    },
};
#[path = "../../../../hwpx-package/tests/support/document_import_memo_catalog_fixture.rs"]
pub(super) mod fixture;
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
fn stored_memo_catalog_and_section_style_relationship_match_direct_whole_assembly_without_publication()
-> TestResult {
    let bytes = fixture::package(&fixture::table(&fixture::style(12), 1), Some("12"))?;
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
    assert_eq!(assembly.imported().review_bodies(), direct.review_bodies());
    assert_eq!(
        assembly.imported().memo_catalog_uses(),
        direct.memo_catalog_uses()
    );
    assert_eq!(catalog.receipt().catalog.memo_properties, 1);
    assert_eq!(catalog.receipt().catalog.unresolved_memo_shape_uses, 0);
    assert_eq!(catalog.verify(&provider, 9)?, *catalog.receipt());
    assert_eq!(assembly.graph(), direct.graph());
    assert_eq!(assembly.receipt().assembly, *direct.receipt());
    assert_eq!(assembly.imported().review_bodies().len(), 2);
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
            .filter(|a| a.event == "artifact.ingested")
            .count(),
        2
    );
    assert!(matches!(
        FullDocumentFormContext::bind(
            assembly.graph(),
            assembly.graph().canonical_sha256()?,
            *ContentDigest::of(&bytes).as_bytes(),
            RevisionId::parse("baseline")?
        ),
        Err(FullDocumentFormError::Projection)
    ));
    for action in [
        hwpx_package::ActivationKind::Ole,
        hwpx_package::ActivationKind::FormCommand,
        hwpx_package::ActivationKind::ExternalLink,
    ] {
        assert!(assembly.imported().require_activation(action).is_err());
    }
    assert!(
        !format!(
            "{assembly:?} {:?} {:?}",
            assembly.imported().review_bodies(),
            assembly.receipt()
        )
        .contains("PRIVATE-MEMO")
    );
    Ok(())
}
#[test]
fn memo_catalog_and_assembly_creation_and_cached_verify_recheck_aead_acl_head_and_quarantine()
-> TestResult {
    let bytes = fixture::package(&fixture::table(&fixture::style(12), 1), Some("12"))?;
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
                    artifact_service::QuarantineReason::parse("REVIEW_ASSEMBLY_FIXTURE")?,
                    9,
                )?;
            }
        }
        assert!(meanings.import_catalog(&provider, 10).is_err());
        assert!(catalog.verify(&provider, 10).is_err());
        assert!(catalog.import_document_assembly(&provider, 10).is_err());
        assert!(assembly.verify(&provider, 10).is_err());
    }
    Ok(())
}
#[test]
fn stored_memo_catalog_and_assembly_reject_each_provider_scope_substitution() -> TestResult {
    let stored = StoredFixture::new(
        &fixture::package(&fixture::table(&fixture::style(12), 1), Some("12"))?,
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
        assert!(meanings.import_catalog(&other, 9).is_err());
        assert!(catalog.verify(&other, 9).is_err());
        assert!(catalog.import_document_assembly(&other, 9).is_err());
        assert!(assembly.verify(&other, 9).is_err());
    }
    Ok(())
}
#[test]
fn malformed_native_memo_catalog_denies_before_assembly_without_head_or_ingest_change() -> TestResult
{
    let style = fixture::style(12);
    for table in [
        fixture::table(&style, 2),
        fixture::table(&style.replace("memoType='NOMAL'", "memoType='NORMAL'"), 1),
        fixture::table(&format!("{style}{style}"), 2),
    ] {
        let bytes = fixture::package(&table, Some("12"))?;
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        assert!(meanings.import_catalog(&provider, 7).is_err());
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
                .filter(|a| a.event == "artifact.ingested")
                .count(),
            2
        );
    }
    Ok(())
}
