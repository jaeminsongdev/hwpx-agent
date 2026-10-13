//! Actual artifact ACL/scanner/AEAD and revision CAS fixtures, NOT native import/publication.
use super::*;
use hwpx_agent_cli::form_stored_provider::full_document::*;
use revision_service::FullDocumentIrBinding;

mod product_request;

fn graph(op: &PreparedFormOperation) -> Result<DocumentGraph, Box<dyn Error>> {
    let controls = op.selection_projection().sections()[0]
        .body
        .children
        .clone();
    let mut draft = DocumentGraphDraft::new(
        DocumentId::parse("actual-form-document")?,
        vec![Section {
            section_id: LogicalId::parse("caller-full-section")?,
            properties: Properties::new(),
            master_pages: vec![],
            headers_footers: vec![],
            body: Flow {
                children: vec![
                    Node::Paragraph(ParagraphNode {
                        common: NodeCommon::new(LogicalId::parse("keep-paragraph")?),
                        inlines: vec![Inline::Text {
                            text: "test-only caller paragraph".into(),
                        }],
                        paragraph_properties: Properties::new(),
                    }),
                    Node::Drawing(DrawingNode {
                        common: NodeCommon::new(LogicalId::parse("keep-drawing")?),
                        resource_id: None,
                        children: Flow { children: controls },
                        properties: Properties::new(),
                    }),
                ],
            },
        }],
    );
    draft.source_profile = Some(LogicalId::parse(
        "test-only-caller-graph-not-native-import",
    )?);
    draft
        .metadata
        .insert("keep_metadata", PropertyValue::Integer(7));
    Ok(DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits::default(),
    )?)
}

fn operation(
    form: &Fixture,
    raw: &[u8],
    access: &FormInputAccessPolicy,
) -> Result<PreparedFormOperation, Box<dyn Error>> {
    Ok(FormOperationPreparation::prepare_json(
        &FormOperationContext::bind(&form.source, &form.map, &form.policies)?,
        FormOperationIdentity::new(
            DocumentId::parse("actual-form-document")?,
            domain_ir::RevisionId::parse("test-only-reference-revision")?,
            PlanId::parse("test-only-reference-plan")?,
        )?,
        raw,
        access,
    )?)
}

// Attach to a NEW sealed fixture node only. Never mutate the original sealed revision.
fn attach(
    stored: &mut StoredFixture,
    graph: &DocumentGraph,
    raw: Vec<u8>,
    kind: ArtifactKind,
    media: &str,
    drift: usize,
) -> Result<FullDocumentIrBinding, Box<dyn Error>> {
    let ir = stored.artifacts.ingest(
        &stored.owner,
        IngestRequest {
            bytes: raw,
            media_type: MediaType::parse(media)?,
            file_name: FileName::parse("test-only-full-ir.json")?,
            kind,
        },
        4,
    )?;
    stored.artifacts.set_permissions(
        &stored.owner,
        ir.artifact_id,
        stored.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        5,
    )?;
    let mut binding = FullDocumentIrBinding {
        artifact_id: ir.artifact_id,
        artifact_sha256: ir.sha256,
        result_package_sha256: stored
            .artifacts
            .get_descriptor(&stored.reader, stored.result, 6)?
            .sha256,
        canonical_graph_sha256: ContentDigest::parse(&hex::encode(graph.canonical_sha256()?))?,
    };
    match drift {
        1 => binding.artifact_sha256 = ContentDigest::of(b"wrong-artifact"),
        2 => binding.result_package_sha256 = ContentDigest::of(b"wrong-package"),
        3 => binding.canonical_graph_sha256 = ContentDigest::of(b"wrong-graph"),
        _ => {}
    }
    let request = RevisionCommitRequest::new(
        CommitId::generate(),
        stored.project,
        stored.branch,
        stored.head,
        revision_service::RevisionId::generate(),
        stored.head.revision_id().into_iter().collect(),
        artifact_service::ArtifactId::generate(),
        stored.result,
        None,
        ContentDigest::of(b"test-only-operation"),
        RevisionValidationState::Verified,
        ContentDigest::of(b"test-only-validation"),
        ContentDigest::of(b"test-only-transaction"),
    )?
    .with_full_document_ir(binding)?;
    assert!(matches!(
        stored
            .revisions
            .commit(&stored.revision_context, &request)?,
        CommitOutcome::Committed(_)
    ));
    stored.head = stored
        .revisions
        .head(&stored.revision_context, stored.project, stored.branch)?;
    let node = stored.revisions.node(
        &stored.revision_context,
        stored.project,
        stored.head.revision_id().ok_or("head")?,
    )?;
    assert!(node.sealed());
    assert_eq!(node.full_document_ir(), Some(binding));
    Ok(binding)
}

fn prepare(
    stored: &StoredFixture,
    form: &Fixture,
    raw: &[u8],
    access: &FormInputAccessPolicy,
) -> Result<PreparedStoredFullDocumentForm, StoredFullDocumentFormError> {
    let provider = stored
        .provider()
        .map_err(|_| StoredFullDocumentFormError::Source)?;
    provider.prepare_full_document_json(
        stored
            .inputs(form, raw, access)
            .map_err(|_| StoredFullDocumentFormError::Source)?,
        8,
    )
}

#[test]
fn stored_full_ir_all_five_kinds_defaults_empty_clear_keep_exact_candidates_and_real_graph()
-> TestResult {
    for label in [
        "five-kinds",
        "empty-text",
        "reset-defaults",
        "clear-selections",
    ] {
        let (form, expected) = matrix(label)?;
        let (raw, access) = matrix_request(label, &form)?;
        let op = operation(&form, &raw, &access)?;
        let graph = graph(&op)?;
        let before = graph.canonical_json()?;
        let mut stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
        let old_head = stored.head;
        let binding = attach(
            &mut stored,
            &graph,
            before.clone(),
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        let prepared = prepare(&stored, &form, &raw, &access)?;
        assert_eq!(prepared.candidate_bytes(), expected);
        assert_eq!(
            prepared.receipt().full_document.source_graph_sha256,
            hex::encode(graph.canonical_sha256()?)
        );
        assert_eq!(
            prepared.compiled_plan().base_graph_sha256(),
            graph.canonical_sha256()?
        );
        assert_eq!(
            prepared.receipt().ir_artifact_sha256,
            binding.artifact_sha256.hex()
        );
        assert_eq!(
            prepared.receipt().full_document.changed_controls,
            op.receipt().changed_controls
        );
        let Node::Paragraph(original) = &graph.sections()[0].body.children[0] else {
            return Err("paragraph".into());
        };
        let Node::Paragraph(target) = &prepared.target_graph().sections()[0].body.children[0]
        else {
            return Err("paragraph".into());
        };
        assert!(target == original);
        assert_eq!(
            prepared.verify(&stored.provider()?, &form.map, &form.policies, &access, 9)?,
            *prepared.receipt()
        );
        assert_eq!(
            prepared.require_current_product_route(
                &stored.provider()?,
                &form.map,
                &form.policies,
                &access,
                9
            ),
            Err(StoredFullDocumentFormError::RouteUnqualified)
        );
        assert_eq!(
            stored
                .artifacts
                .download(&stored.reader, binding.artifact_id, 10)?,
            before
        );
        assert_eq!(
            stored
                .artifacts
                .download(&stored.reader, stored.result, 10)?,
            form.source
        );
        assert_eq!(
            stored
                .revisions
                .head(&stored.revision_context, stored.project, stored.branch)?,
            stored.head,
            "prepare does not commit"
        );
        let old = stored.revisions.node(
            &stored.revision_context,
            stored.project,
            old_head.revision_id().ok_or("old head")?,
        )?;
        assert_eq!(old.full_document_ir(), None, "old node remains immutable");
    }
    Ok(())
}

#[test]
fn stored_full_ir_missing_link_and_wrong_kind_media_or_three_digests_fail_closed() -> TestResult {
    let form = fixture()?;
    let (request, access) = form.request("new value")?;
    let raw = serde_json::to_vec(&request)?;
    let graph = graph(&operation(&form, &raw, &access)?)?;
    let missing = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    assert!(matches!(
        prepare(&missing, &form, &raw, &access),
        Err(StoredFullDocumentFormError::MissingIr)
    ));
    for (kind, media, drift, expected) in [
        (
            ArtifactKind::Evidence,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
            StoredFullDocumentFormError::Artifact,
        ),
        (
            ArtifactKind::DocumentIr,
            "application/json",
            0,
            StoredFullDocumentFormError::Artifact,
        ),
        (
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            1,
            StoredFullDocumentFormError::Artifact,
        ),
        (
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            2,
            StoredFullDocumentFormError::Binding,
        ),
        (
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            3,
            StoredFullDocumentFormError::Graph,
        ),
    ] {
        let mut stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
        attach(
            &mut stored,
            &graph,
            graph.canonical_json()?,
            kind,
            media,
            drift,
        )?;
        assert!(matches!(prepare(&stored, &form, &raw, &access), Err(error) if error == expected));
    }
    Ok(())
}

#[test]
fn stored_full_ir_noncanonical_and_duplicate_properties_are_rejected_after_actual_download()
-> TestResult {
    let form = fixture()?;
    let (request, access) = form.request("new value")?;
    let raw = serde_json::to_vec(&request)?;
    let graph = graph(&operation(&form, &raw, &access)?)?;
    let canonical = String::from_utf8(graph.canonical_json()?)?;
    for bytes in [
        format!("{canonical}\n").into_bytes(),
        canonical
            .replacen(
                "\"metadata\":{",
                "\"metadata\":{\"keep_metadata\":{\"kind\":\"integer\",\"value\":8},",
                1,
            )
            .into_bytes(),
    ] {
        let mut stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
        attach(
            &mut stored,
            &graph,
            bytes,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(matches!(
            prepare(&stored, &form, &raw, &access),
            Err(StoredFullDocumentFormError::Graph)
        ));
    }
    Ok(())
}

#[test]
fn stored_full_ir_wrong_document_and_explicit_inventory_projection_are_not_promoted() -> TestResult
{
    let form = fixture()?;
    let (request, access) = form.request("new value")?;
    let raw = serde_json::to_vec(&request)?;
    let op = operation(&form, &raw, &access)?;
    let mut draft = graph(&op)?.into_draft();
    draft.document_id = DocumentId::parse("wrong-document")?;
    for graph in [
        DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?,
        op.selection_projection().clone(),
    ] {
        let mut stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
        attach(
            &mut stored,
            &graph,
            graph.canonical_json()?,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(matches!(
            prepare(&stored, &form, &raw, &access),
            Err(StoredFullDocumentFormError::Preparation)
        ));
    }
    Ok(())
}

fn with_valid(
    test: impl FnOnce(
        StoredFixture,
        Fixture,
        Vec<u8>,
        FormInputAccessPolicy,
        FullDocumentIrBinding,
        PreparedStoredFullDocumentForm,
    ) -> TestResult,
) -> TestResult {
    let form = fixture()?;
    let (request, access) = form.request("new private value")?;
    let raw = serde_json::to_vec(&request)?;
    let graph = graph(&operation(&form, &raw, &access)?)?;
    let mut stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let binding = attach(
        &mut stored,
        &graph,
        graph.canonical_json()?,
        ArtifactKind::DocumentIr,
        DOCUMENT_IR_MEDIA_TYPE,
        0,
    )?;
    let prepared = prepare(&stored, &form, &raw, &access)?;
    test(stored, form, raw, access, binding, prepared)
}

#[test]
fn stored_full_ir_fresh_ir_only_acl_revocation_precedes_signed_route() -> TestResult {
    with_valid(|stored, form, _, access, binding, prepared| {
        stored.artifacts.set_permissions(
            &stored.owner,
            binding.artifact_id,
            stored.reader.subject(),
            BTreeSet::new(),
            9,
        )?;
        assert_eq!(
            prepared.verify(&stored.provider()?, &form.map, &form.policies, &access, 10),
            Err(StoredFullDocumentFormError::Artifact)
        );
        assert_eq!(
            prepared.require_current_product_route(
                &stored.provider()?,
                &form.map,
                &form.policies,
                &access,
                10
            ),
            Err(StoredFullDocumentFormError::Artifact)
        );
        assert_eq!(
            stored
                .artifacts
                .download(&stored.reader, stored.result, 10)?,
            form.source,
            "package ACL intact"
        );
        Ok(())
    })
}
#[test]
fn stored_full_ir_ir_only_aead_corruption_is_rejected_without_touching_source() -> TestResult {
    with_valid(|stored, form, _, access, _, prepared| {
        stored.blobs.tamper_ir.store(true, Ordering::SeqCst);
        assert_eq!(
            prepared.verify(&stored.provider()?, &form.map, &form.policies, &access, 10),
            Err(StoredFullDocumentFormError::Artifact)
        );
        assert_eq!(
            stored
                .artifacts
                .download(&stored.reader, stored.result, 10)?,
            form.source,
            "package AEAD intact"
        );
        Ok(())
    })
}
#[test]
fn stored_full_ir_head_advance_and_access_revocation_do_not_rebind_old_preparation() -> TestResult {
    with_valid(|stored, form, _, access, _, prepared| {
        let mut revoked = access.clone();
        revoked.input_allowed = false;
        assert_eq!(
            prepared.verify(&stored.provider()?, &form.map, &form.policies, &revoked, 10),
            Err(StoredFullDocumentFormError::Source)
        );
        stored.advance()?;
        assert_eq!(
            prepared.verify(&stored.provider()?, &form.map, &form.policies, &access, 11),
            Err(StoredFullDocumentFormError::Source)
        );
        Ok(())
    })
}
#[test]
fn stored_full_ir_public_receipt_debug_never_exposes_values_paths_or_artifact_ids() -> TestResult {
    with_valid(|stored, _, _, _, binding, prepared| {
        for output in [
            serde_json::to_string(prepared.receipt())?,
            format!("{prepared:?}"),
            format!("{binding:?}"),
        ] {
            assert!(!output.contains("new private value"));
            assert!(!output.contains("test-only caller paragraph"));
            assert!(!output.contains(&binding.artifact_id.public_id()));
            assert!(!output.contains(&stored.result.public_id()));
            assert!(!output.contains("private-original.hwpx"));
            assert!(!output.contains("90001"));
        }
        Ok(())
    })
}
