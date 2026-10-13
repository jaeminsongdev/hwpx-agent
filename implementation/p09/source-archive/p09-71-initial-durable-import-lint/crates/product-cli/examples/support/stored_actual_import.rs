//! Durable P70 actual-source import using the original fixture's real PG/file backends.
//! The old baseline IR, scanner, keys, Source and execution authority remain synthetic.
use super::{
    Artifacts, Failure, Input, Probe, Result, branch, context, now, owner, project, read_service,
    reader, service,
};
use artifact_service::{
    ArtifactMetadataRepository, ContentDigest, EncryptedBlobStore, LocalEncryptedBlobStore,
    LocalPostgresMetadataRepository,
};
use domain_ir::{DocumentId, RevisionId};
use hwpx_agent_cli::{
    form_stored_provider::{
        StoredFormError, StoredFormProvider, actual_import::StoredActualFormImportError,
    },
    form_value_operation::full_document::{FullDocumentFormContext, FullDocumentFormError},
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    forms::{
        ImportedDocumentForms,
        policies::{FormPolicySourceBinding, PolicyBoundDocumentForms},
    },
};
use std::collections::BTreeSet;

#[path = "../../../hwpx-package/examples/document_import_form_policies_support/mod.rs"]
mod policies;

pub(super) fn run(
    p: &mut Probe,
    artifacts: &Artifacts,
    metadata: &LocalPostgresMetadataRepository,
    blobs: &LocalEncryptedBlobStore,
    values: &[Input],
) -> Result<()> {
    let revisions = read_service()?;
    let ctx = context()?;
    let actor = reader()?;
    for (index, input) in values.iter().enumerate() {
        let case = u8::try_from(index).map_err(|_| Failure::Fixture)?;
        let provider = StoredFormProvider::bind(
            artifacts,
            &revisions,
            &actor,
            &ctx,
            project()?,
            branch(case)?,
            DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
        )
        .map_err(|_| Failure::Fixture)?;
        let head = revisions.head(&ctx, project()?, branch(case)?)?;
        let before = ingest_count(metadata)?;
        let imported = provider
            .import_actual_forms(head, now()?)
            .map_err(|_| Failure::Fixture)?;
        let bytes = policies::fixture_bytes(input.label, "source").map_err(|_| Failure::Fixture)?;
        p.check(
            input.label,
            "actual_locked_source_digest",
            bytes == input.form.source
                && imported.receipt().imported.source_package_sha256
                    == *ContentDigest::of(&bytes).as_bytes(),
        )?;
        let direct = ImportedDocumentForms::import(
            ImportedSourcePackage::import(
                &bytes,
                DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
                *ContentDigest::of(&bytes).as_bytes(),
                SourceImportLimits::default(),
            )
            .map_err(|_| Failure::Fixture)?,
        )
        .map_err(|_| Failure::Fixture)?;
        p.check(
            input.label,
            "actual_whole_graph_observations_exact",
            imported.imported().graph() == direct.graph()
                && imported.imported().forms() == direct.forms()
                && imported.receipt().imported == *direct.receipt(),
        )?;
        p.check(
            input.label,
            "fresh_actual_import_verify_exact",
            imported
                .verify(&provider, now()?)
                .map_err(|_| Failure::Fixture)?
                == *imported.receipt(),
        )?;
        let binding = FormPolicySourceBinding::for_imported(imported.imported());
        let supplied = policies::explicit_test_policies(imported.imported());
        let bound = imported
            .bind_policies(&provider, &binding, &supplied, now()?)
            .map_err(|_| Failure::Fixture)?;
        let original = PolicyBoundDocumentForms::bind(&direct, &binding, &supplied)
            .map_err(|_| Failure::Fixture)?;
        p.check(
            input.label,
            "actual_complete_policy_graph_state_exact",
            bound.graph() == original.graph()
                && bound.state() == original.state()
                && bound.receipt().policy == *original.receipt(),
        )?;
        p.check(
            input.label,
            "fresh_actual_bound_policy_verify_exact",
            bound
                .verify(&provider, &binding, &supplied, now()?)
                .map_err(|_| Failure::Fixture)?
                == *bound.receipt(),
        )?;
        p.check(
            input.label,
            "actual_partial_product_denied",
            matches!(
                FullDocumentFormContext::bind(
                    bound.graph(),
                    bound
                        .graph()
                        .canonical_sha256()
                        .map_err(|_| Failure::Fixture)?,
                    *ContentDigest::of(&bytes).as_bytes(),
                    RevisionId::parse(head.revision_id().ok_or(Failure::Fixture)?.public_id())
                        .map_err(|_| Failure::Fixture)?
                ),
                Err(FullDocumentFormError::Projection)
            ),
        )?;
        p.check(
            input.label,
            "actual_head_and_ingest_unchanged",
            ingest_count(metadata)? == before
                && revisions.head(&ctx, project()?, branch(case)?)? == head,
        )?;
        let record = metadata
            .find_by_content(actor.tenant_id(), ContentDigest::of(&bytes))?
            .ok_or(Failure::Fixture)?;
        let cipher = blobs.get(record.object_key())?.ok_or(Failure::Fixture)?;
        p.check(
            input.label,
            "actual_source_encrypted_not_plaintext",
            cipher.len() == bytes.len() + 16 && cipher != bytes,
        )?;
        // A receipt of partial import/policy only. Do not mislabel graph/state
        // hashes as candidate HWPX or fill the original candidate_sha256 array.
        p.receipts
            .push(ContentDigest::of(&serde_json::to_vec(bound.receipt())?).hex());
    }
    Ok(())
}

pub(super) fn denied(p: &mut Probe, artifacts: &Artifacts, values: &[Input]) -> Result<()> {
    let revisions = read_service()?;
    let ctx = context()?;
    let actor = reader()?;
    for (index, input) in values.iter().enumerate() {
        let case = u8::try_from(index).map_err(|_| Failure::Fixture)?;
        let provider = StoredFormProvider::bind(
            artifacts,
            &revisions,
            &actor,
            &ctx,
            project()?,
            branch(case)?,
            DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
        )
        .map_err(|_| Failure::Fixture)?;
        let expected = revision_service::RevisionHead::new(Some(super::revision(case)?), 1)?;
        p.check(
            input.label,
            "actual_project_acl_denied",
            matches!(
                provider.import_actual_forms(expected, now()?),
                Err(StoredActualFormImportError::Source(
                    StoredFormError::Head | StoredFormError::Artifact
                ))
            ),
        )?;
    }
    Ok(())
}

pub(super) fn safety(
    p: &mut Probe,
    artifacts: &Artifacts,
    metadata: &LocalPostgresMetadataRepository,
    values: &[Input],
) -> Result<()> {
    let input = values.first().ok_or(Failure::Fixture)?;
    let revisions = read_service()?;
    let ctx = context()?;
    let actor = reader()?;
    let provider = StoredFormProvider::bind(
        artifacts,
        &revisions,
        &actor,
        &ctx,
        project()?,
        branch(0)?,
        DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
    )
    .map_err(|_| Failure::Fixture)?;
    let head = revisions.head(&ctx, project()?, branch(0)?)?;
    let imported = provider
        .import_actual_forms(head, now()?)
        .map_err(|_| Failure::Fixture)?;
    let binding = FormPolicySourceBinding::for_imported(imported.imported());
    let supplied = policies::explicit_test_policies(imported.imported());
    let bound = imported
        .bind_policies(&provider, &binding, &supplied, now()?)
        .map_err(|_| Failure::Fixture)?;
    let before = ingest_count(metadata)?;
    let artifact = imported.receipt().source_artifact;
    let record = metadata
        .find_by_content(actor.tenant_id(), ContentDigest::of(&input.form.source))?
        .ok_or(Failure::Fixture)?;
    if record.descriptor().artifact_id != artifact {
        return Err(Failure::Fixture);
    }
    let permissions = record.permissions_for(actor.subject());
    artifacts.set_permissions(
        &owner()?,
        artifact,
        actor.subject(),
        BTreeSet::new(),
        now()?,
    )?;
    // Always restore ACL even if the new negative test or original service fails.
    let blocked = (|| -> Result<()> {
        p.check(
            input.label,
            "actual_result_acl_revocation_import_denied",
            matches!(
                provider.import_actual_forms(head, now()?),
                Err(StoredActualFormImportError::Source(
                    StoredFormError::Artifact
                ))
            ),
        )?;
        p.check(
            input.label,
            "actual_result_acl_revocation_cached_import_denied",
            matches!(
                imported.verify(&provider, now()?),
                Err(StoredActualFormImportError::Source(
                    StoredFormError::Artifact
                ))
            ),
        )?;
        p.check(
            input.label,
            "actual_result_acl_revocation_cached_policy_denied",
            matches!(
                bound.verify(&provider, &binding, &supplied, now()?),
                Err(StoredActualFormImportError::Source(
                    StoredFormError::Artifact
                ))
            ),
        )?;
        Ok(())
    })();
    artifacts.set_permissions(&owner()?, artifact, actor.subject(), permissions, now()?)?;
    blocked?;
    p.check(
        input.label,
        "actual_result_acl_restore_exact",
        bound
            .verify(&provider, &binding, &supplied, now()?)
            .map_err(|_| Failure::Fixture)?
            == *bound.receipt(),
    )?;
    let (wrong, _, _) = service(values, 66)?;
    let wrong_provider = StoredFormProvider::bind(
        &wrong,
        &revisions,
        &actor,
        &ctx,
        project()?,
        branch(0)?,
        DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
    )
    .map_err(|_| Failure::Fixture)?;
    p.check(
        input.label,
        "actual_source_wrong_aes_key_denied",
        matches!(
            wrong_provider.import_actual_forms(head, now()?),
            Err(StoredActualFormImportError::Source(
                StoredFormError::Artifact
            ))
        ),
    )?;
    p.check(
        input.label,
        "actual_safety_head_ingest_unchanged",
        ingest_count(metadata)? == before && revisions.head(&ctx, project()?, branch(0)?)? == head,
    )?;
    p.check(
        input.label,
        "actual_cached_receipt_stays_partial",
        matches!(
            FullDocumentFormContext::bind(
                bound.graph(),
                bound
                    .graph()
                    .canonical_sha256()
                    .map_err(|_| Failure::Fixture)?,
                *ContentDigest::of(&input.form.source).as_bytes(),
                RevisionId::parse(head.revision_id().ok_or(Failure::Fixture)?.public_id())
                    .map_err(|_| Failure::Fixture)?
            ),
            Err(FullDocumentFormError::Projection)
        ),
    )?;
    Ok(())
}
fn ingest_count(metadata: &LocalPostgresMetadataRepository) -> Result<usize> {
    Ok(metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested" || e.event == "artifact.ingest.deduplicated")
        .count())
}
