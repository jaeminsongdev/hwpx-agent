//! Fresh real IR ACL/quarantine and wrong-key filesystem checks, disposable fixtures only.
use super::{
    Artifacts, Failure, Input, Probe, Result, context, now, owner, project, read_service, reader,
    request, service,
};
use artifact_service::{
    ArtifactMetadataRepository, ArtifactPermission, ContentDigest, QuarantineReason, StorageState,
};
use domain_ir::DocumentId;
use hwpx_agent_cli::{
    form_product_request::{
        stored::StoredProductFormBindings,
        stored_full_document::{
            StoredFullDocumentProductFormError, StoredFullDocumentProductFormRequest,
        },
    },
    form_stored_provider::{
        StoredFormError, StoredFormProvider, full_document::StoredFullDocumentFormError,
    },
};
use std::collections::BTreeSet;

pub(super) fn run(
    p: &mut Probe,
    artifacts: &Artifacts,
    metadata: &artifact_service::LocalPostgresMetadataRepository,
    values: &[Input],
) -> Result<()> {
    let input = values.first().ok_or(Failure::Fixture)?;
    let revisions = read_service()?;
    let ctx = context()?;
    let reader = reader()?;
    let provider = StoredFormProvider::bind(
        artifacts,
        &revisions,
        &reader,
        &ctx,
        project()?,
        super::branch(0)?,
        DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
    )
    .map_err(|_| Failure::Fixture)?;
    let bindings = StoredProductFormBindings {
        map: &input.form.map,
        policies: &input.form.policies,
        access: &input.access,
    };
    let prepared = StoredFullDocumentProductFormRequest::prepare_json(
        &provider,
        &request(input, 0)?,
        &bindings,
        now()?,
    )?;
    let ir = metadata
        .find_by_content(
            reader.tenant_id(),
            ContentDigest::of(&input.graph.canonical_json().map_err(|_| Failure::Fixture)?),
        )?
        .ok_or(Failure::Fixture)?;
    let source = metadata
        .find_by_content(reader.tenant_id(), ContentDigest::of(&input.form.source))?
        .ok_or(Failure::Fixture)?;
    let head = revisions.head(&ctx, project()?, super::branch(0)?)?;
    let before = ingest_count(metadata)?;
    artifacts.set_permissions(
        &owner()?,
        ir.artifact_id(),
        reader.subject(),
        BTreeSet::new(),
        now()?,
    )?;
    p.check(
        input.label,
        "ir_acl_revocation_precedes_route",
        matches!(
            prepared.require_current_product_route(&provider, &bindings, now()?),
            Err(StoredFullDocumentProductFormError::FullDocument(
                StoredFullDocumentFormError::Artifact
            ))
        ),
    )?;
    p.check(
        input.label,
        "source_survives_ir_acl_revocation",
        artifacts.download(&reader, source.artifact_id(), now()?)? == input.form.source,
    )?;
    artifacts.set_permissions(
        &owner()?,
        ir.artifact_id(),
        reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        now()?,
    )?;
    p.check(
        input.label,
        "ir_acl_restore_fresh_verify",
        prepared.verify(&provider, &bindings, now()?)? == *prepared.receipt(),
    )?;
    wrong_key_and_no_publication(p, values, &prepared, &revisions, metadata, head, before)?;
    artifacts.quarantine(
        &owner()?,
        ir.artifact_id(),
        QuarantineReason::parse("P65_FIXTURE_IR_QUARANTINE")?,
        now()?,
    )?;
    p.check(
        input.label,
        "ir_quarantine_fresh_verify_denied",
        matches!(
            prepared.verify(&provider, &bindings, now()?),
            Err(StoredFullDocumentProductFormError::FullDocument(
                StoredFullDocumentFormError::Artifact
            ))
        ),
    )?;
    p.check(
        input.label,
        "source_survives_ir_quarantine",
        artifacts.download(&reader, source.artifact_id(), now()?)? == input.form.source,
    )?;
    p.check(
        input.label,
        "ir_quarantine_storage_state_persisted",
        quarantined(artifacts, ir.artifact_id())?
            && revisions.head(&ctx, project()?, super::branch(0)?)? == head
            && ingest_count(metadata)? == before,
    )?;
    Ok(())
}
fn wrong_key_and_no_publication(
    p: &mut Probe,
    values: &[Input],
    prepared: &hwpx_agent_cli::form_product_request::stored_full_document::PreparedStoredFullDocumentProductForm,
    revisions: &super::Revisions,
    metadata: &artifact_service::LocalPostgresMetadataRepository,
    head: revision_service::RevisionHead,
    before: usize,
) -> Result<()> {
    let input = values.first().ok_or(Failure::Fixture)?;
    let ctx = context()?;
    let reader = reader()?;
    let bindings = StoredProductFormBindings {
        map: &input.form.map,
        policies: &input.form.policies,
        access: &input.access,
    };
    let (wrong, _, _) = service(values, 66)?;
    let wrong_provider = StoredFormProvider::bind(
        &wrong,
        revisions,
        &reader,
        &ctx,
        project()?,
        super::branch(0)?,
        DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
    )
    .map_err(|_| Failure::Fixture)?;
    p.check(
        input.label,
        "wrong_aes_key_denied_from_actual_files",
        matches!(
            prepared.verify(&wrong_provider, &bindings, now()?),
            Err(StoredFullDocumentProductFormError::Provider(
                hwpx_agent_cli::form_product_request::stored::StoredProductFormError::Stored(
                    StoredFormError::Artifact
                )
            ))
        ),
    )?;
    p.check(
        input.label,
        "head_and_ingest_counts_unchanged",
        revisions.head(&ctx, project()?, super::branch(0)?)? == head
            && ingest_count(metadata)? == before,
    )?;
    Ok(())
}

fn ingest_count(metadata: &artifact_service::LocalPostgresMetadataRepository) -> Result<usize> {
    Ok(metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested" || e.event == "artifact.ingest.deduplicated")
        .count())
}
fn quarantined(artifacts: &Artifacts, id: artifact_service::ArtifactId) -> Result<bool> {
    Ok(artifacts
        .get_descriptor(&owner()?, id, now()?)?
        .storage_state
        == StorageState::Quarantined)
}
