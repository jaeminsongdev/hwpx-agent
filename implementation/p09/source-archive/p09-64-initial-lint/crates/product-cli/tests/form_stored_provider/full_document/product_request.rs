//! Service-backed request contract tests. Repositories/scanner/keys are synthetic fixtures.
//! They do NOT prove PostgreSQL persistence, a native importer, signed execution or publication.
use super::*;
use hwpx_agent_cli::form_product_request::{
    FORM_PRODUCT_REQUEST_SCHEMA, FormProductRequestError,
    stored::{StoredProductFormBindings, StoredProductFormError},
    stored_full_document::*,
};

fn bindings<'a>(
    form: &'a Fixture,
    access: &'a FormInputAccessPolicy,
) -> StoredProductFormBindings<'a> {
    StoredProductFormBindings {
        map: &form.map,
        policies: &form.policies,
        access,
    }
}

fn envelope(stored: &StoredFixture, form: &Fixture, input: &[u8]) -> Result<Value, Box<dyn Error>> {
    Ok(serde_json::json!({
        "schema_version": FORM_PRODUCT_REQUEST_SCHEMA,
        "idempotency_key": "P64-synthetic-private-retry-key",
        "project_id": stored.project.public_id(),
        "document_id": "actual-form-document",
        "base_revision": stored.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation": stored.head.generation(),
        "expected_source_package_sha256": hex::encode(Sha256::digest(&form.source)),
        "plan_id": "stored-full-document-plan",
        "form_input": serde_json::from_slice::<Value>(input)?
    }))
}

fn product_prepare(
    stored: &StoredFixture,
    form: &Fixture,
    request: &Value,
    access: &FormInputAccessPolicy,
) -> Result<PreparedStoredFullDocumentProductForm, Box<dyn Error>> {
    Ok(StoredFullDocumentProductFormRequest::prepare_json(
        &stored.provider()?,
        &serde_json::to_vec(request)?,
        &bindings(form, access),
        8,
    )?)
}

fn ingest_count(stored: &StoredFixture) -> Result<usize, Box<dyn Error>> {
    Ok(stored
        .metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested")
        .count())
}

fn assert_no_publish(
    stored: &StoredFixture,
    expected_head: RevisionHead,
    count: usize,
) -> TestResult {
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        expected_head
    );
    assert_eq!(ingest_count(stored)?, count);
    Ok(())
}

struct Case {
    stored: StoredFixture,
    form: Fixture,
    access: FormInputAccessPolicy,
    binding: FullDocumentIrBinding,
    request: Value,
}
impl Case {
    fn new() -> Result<Self, Box<dyn Error>> {
        let form = fixture()?;
        let (input, access) = form.request("P64 synthetic private value")?;
        let raw = serde_json::to_vec(&input)?;
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
        let request = envelope(&stored, &form, &raw)?;
        Ok(Self {
            stored,
            form,
            access,
            binding,
            request,
        })
    }
    fn prepare(&self) -> Result<PreparedStoredFullDocumentProductForm, Box<dyn Error>> {
        product_prepare(&self.stored, &self.form, &self.request, &self.access)
    }
}

#[test]
fn full_request_four_locked_whole_package_oracles_and_full_graph_plan_not_projection() -> TestResult
{
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
        let source_ir = graph.canonical_json()?;
        let mut stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
        let old_head = stored.head;
        let ir = attach(
            &mut stored,
            &graph,
            source_ir.clone(),
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        let request = envelope(&stored, &form, &raw)?;
        let prepared = product_prepare(&stored, &form, &request, &access)?;
        assert!(prepared.candidate_bytes() == expected);
        assert_eq!(
            prepared.receipt().profile,
            STORED_FULL_DOCUMENT_PRODUCT_FORM_PROFILE
        );
        assert_eq!(
            prepared.compiled_plan().plan_id().as_str(),
            "stored-full-document-plan"
        );
        assert_eq!(
            prepared.compiled_plan().base_revision().as_str(),
            stored.head.revision_id().ok_or("head")?.public_id()
        );
        assert_eq!(
            prepared.compiled_plan().base_graph_sha256(),
            graph.canonical_sha256()?
        );
        assert_ne!(
            prepared.compiled_plan().base_graph_sha256(),
            op.selection_projection().canonical_sha256()?
        );
        assert_eq!(
            prepared.receipt().full_document.ir_artifact_sha256,
            ir.artifact_sha256.hex()
        );
        assert_eq!(
            prepared
                .receipt()
                .full_document
                .full_document
                .changed_controls,
            op.receipt().changed_controls
        );

        // Restore ONLY complete_control_state_json in the target. Every other field must be exact.
        let original = graph.clone().into_draft();
        let mut target = prepared.target_graph().clone().into_draft();
        let Node::Drawing(source_controls) = &original.sections[0].body.children[1] else {
            return Err("source drawing".into());
        };
        let Node::Drawing(target_controls) = &mut target.sections[0].body.children[1] else {
            return Err("target drawing".into());
        };
        assert_eq!(
            source_controls.children.children.len(),
            target_controls.children.children.len()
        );
        for (source, target) in source_controls
            .children
            .children
            .iter()
            .zip(&mut target_controls.children.children)
        {
            let (Node::FormControl(source), Node::FormControl(target)) = (source, target) else {
                return Err("form node".into());
            };
            let state = source
                .properties
                .iter()
                .find(|(k, _)| *k == "complete_control_state_json")
                .ok_or("state")?
                .1
                .clone();
            target
                .properties
                .insert("complete_control_state_json", state);
        }
        assert!(target == original, "non-state whole graph fields changed");
        assert_eq!(
            prepared.verify(&stored.provider()?, &bindings(&form, &access), 9)?,
            *prepared.receipt()
        );
        assert_eq!(
            prepared.require_current_product_route(
                &stored.provider()?,
                &bindings(&form, &access),
                10
            ),
            Err(StoredFullDocumentProductFormError::FullDocument(
                StoredFullDocumentFormError::RouteUnqualified
            ))
        );
        assert!(
            stored
                .artifacts
                .download(&stored.reader, ir.artifact_id, 11)?
                == source_ir
        );
        assert!(
            stored
                .artifacts
                .download(&stored.reader, stored.result, 11)?
                == form.source
        );
        assert_eq!(
            stored
                .revisions
                .node(
                    &stored.revision_context,
                    stored.project,
                    old_head.revision_id().ok_or("old head")?
                )?
                .full_document_ir(),
            None
        );
        assert_no_publish(&stored, stored.head, 3)?;
    }
    Ok(())
}

#[test]
fn full_request_original_recursive_strict_parser_rejects_before_artifact_audit() -> TestResult {
    let case = Case::new()?;
    let raw = serde_json::to_string(&case.request)?;
    let mut malformed = vec![
        vec![],
        vec![b' '; 2 * 1024 * 1024 + 1],
        b"{".to_vec(),
        b"[]".to_vec(),
        b"null".to_vec(),
        vec![0xff],
        format!("{raw} {{}}").into_bytes(),
        raw.replacen("\"plan_id\":", "\"plan_id\":\"duplicate\",\"plan_id\":", 1)
            .into_bytes(),
        raw.replacen(
            "\"request_id\":",
            "\"request_id\":\"duplicate\",\"request_id\":",
            1,
        )
        .into_bytes(),
        raw.replacen(
            "\"input_allowed\":",
            "\"input_allowed\":false,\"input_allowed\":",
            1,
        )
        .into_bytes(),
    ];
    for (field, value) in [
        ("schema_version", serde_json::json!("unknown")),
        ("expected_head_generation", serde_json::json!(0)),
        ("expected_head_generation", serde_json::json!("2")),
        ("expected_head_generation", serde_json::json!(2.5)),
        (
            "expected_source_package_sha256",
            serde_json::json!("A".repeat(64)),
        ),
        (
            "expected_source_package_sha256",
            serde_json::json!("0".repeat(63)),
        ),
        ("idempotency_key", Value::Null),
        ("plan_id", serde_json::json!(17)),
        ("document_id", serde_json::json!("x".repeat(1025))),
        ("artifact_id", serde_json::json!("caller-selected")),
        ("ir_artifact_id", serde_json::json!("caller-selected")),
        ("full_document_ir", serde_json::json!({})),
        ("graph", serde_json::json!({})),
        ("path", serde_json::json!(CAPTURE)),
        ("approved", serde_json::json!(true)),
        ("execution_manifest", serde_json::json!({})),
        ("lease", serde_json::json!({})),
    ] {
        let mut changed = case.request.clone();
        changed[field] = value;
        malformed.push(serde_json::to_vec(&changed)?);
    }
    let before = case.stored.metadata.audit_events()?.len();
    for raw in malformed {
        assert!(matches!(
            StoredFullDocumentProductFormRequest::prepare_json(
                &case.stored.provider()?,
                &raw,
                &bindings(&case.form, &case.access),
                8
            ),
            Err(StoredFullDocumentProductFormError::Request(
                FormProductRequestError::Request | FormProductRequestError::Limit
            ))
        ));
        assert_eq!(case.stored.metadata.audit_events()?.len(), before);
    }
    assert_no_publish(&case.stored, case.stored.head, 3)
}

#[test]
fn full_request_project_document_source_revision_generation_are_provider_bound() -> TestResult {
    let case = Case::new()?;
    for (field, value, expected) in [
        (
            "project_id",
            serde_json::json!("prj_45000000000000000000000000000002"),
            StoredProductFormError::Stored(StoredFormError::Scope),
        ),
        (
            "document_id",
            serde_json::json!("wrong-document"),
            StoredProductFormError::Stored(StoredFormError::Scope),
        ),
        (
            "expected_source_package_sha256",
            serde_json::json!("0".repeat(64)),
            StoredProductFormError::Stored(StoredFormError::Drift),
        ),
        (
            "base_revision",
            serde_json::json!(revision_service::RevisionId::generate().public_id()),
            StoredProductFormError::Stored(StoredFormError::Head),
        ),
        (
            "expected_head_generation",
            serde_json::json!(case.stored.head.generation() + 1),
            StoredProductFormError::Stored(StoredFormError::Head),
        ),
        (
            "base_revision",
            serde_json::json!("not-a-stored-revision"),
            StoredProductFormError::Head,
        ),
    ] {
        let mut changed = case.request.clone();
        changed[field] = value;
        assert_eq!(
            StoredFullDocumentProductFormRequest::prepare_json(
                &case.stored.provider()?,
                &serde_json::to_vec(&changed)?,
                &bindings(&case.form, &case.access),
                8
            )
            .err()
            .ok_or("expected rejection")?,
            StoredFullDocumentProductFormError::Provider(expected)
        );
    }
    assert_no_publish(&case.stored, case.stored.head, 3)
}

#[test]
fn full_request_missing_ir_wrong_kind_media_and_three_hashes_never_fall_back() -> TestResult {
    let form = fixture()?;
    let (input, access) = form.request("test value")?;
    let raw = serde_json::to_vec(&input)?;
    let graph = graph(&operation(&form, &raw, &access)?)?;
    let missing = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let request = envelope(&missing, &form, &raw)?;
    assert!(
        missing.prepare(&form, &raw, &access).is_ok(),
        "inventory path can prepare this fixture"
    );
    assert_eq!(
        product_prepare(&missing, &form, &request, &access)
            .err()
            .ok_or("expected rejection")?
            .downcast::<StoredFullDocumentProductFormError>()
            .map_err(|_| "error type")?
            .as_ref(),
        &StoredFullDocumentProductFormError::FullDocument(StoredFullDocumentFormError::MissingIr)
    );
    assert_no_publish(&missing, missing.head, 2)?;
    for (kind, media, drift, error) in [
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
        let request = envelope(&stored, &form, &raw)?;
        assert!(
            matches!(StoredFullDocumentProductFormRequest::prepare_json(&stored.provider()?, &serde_json::to_vec(&request)?, &bindings(&form, &access), 8), Err(StoredFullDocumentProductFormError::FullDocument(actual)) if actual == error)
        );
        assert_no_publish(&stored, stored.head, 3)?;
    }
    Ok(())
}

#[test]
fn full_request_noncanonical_duplicate_ir_is_not_admitted_by_envelope() -> TestResult {
    let form = fixture()?;
    let (input, access) = form.request("test value")?;
    let raw = serde_json::to_vec(&input)?;
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
        let request = envelope(&stored, &form, &raw)?;
        assert!(matches!(
            StoredFullDocumentProductFormRequest::prepare_json(
                &stored.provider()?,
                &serde_json::to_vec(&request)?,
                &bindings(&form, &access),
                8
            ),
            Err(StoredFullDocumentProductFormError::FullDocument(
                StoredFullDocumentFormError::Graph
            ))
        ));
        assert_no_publish(&stored, stored.head, 3)?;
    }
    Ok(())
}

#[test]
fn full_request_inventory_wrong_document_and_protected_ir_remain_unqualified() -> TestResult {
    let form = fixture()?;
    let (input, access) = form.request("test value")?;
    let raw = serde_json::to_vec(&input)?;
    let op = operation(&form, &raw, &access)?;
    let mut wrong = graph(&op)?.into_draft();
    wrong.document_id = DocumentId::parse("wrong-document")?;
    let mut graphs = vec![
        op.selection_projection().clone(),
        DocumentGraph::from_draft(wrong, DocumentGraphLimits::default())?,
    ];
    for index in 0..3 {
        let mut draft = graph(&op)?.into_draft();
        match index {
            0 => draft.security_state.protected = true,
            1 => draft.security_state.encrypted = true,
            _ => draft.security_state.signed = true,
        }
        graphs.push(DocumentGraph::from_draft(
            draft,
            DocumentGraphLimits::default(),
        )?);
    }
    for graph in graphs {
        let mut stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
        attach(
            &mut stored,
            &graph,
            graph.canonical_json()?,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        let request = envelope(&stored, &form, &raw)?;
        assert!(matches!(
            StoredFullDocumentProductFormRequest::prepare_json(
                &stored.provider()?,
                &serde_json::to_vec(&request)?,
                &bindings(&form, &access),
                8
            ),
            Err(StoredFullDocumentProductFormError::FullDocument(
                StoredFullDocumentFormError::Preparation
            ))
        ));
        assert_no_publish(&stored, stored.head, 3)?;
    }
    Ok(())
}

#[test]
fn full_request_fresh_ir_acl_is_independent_of_source_acl_and_precedes_route() -> TestResult {
    let case = Case::new()?;
    let prepared = case.prepare()?;
    case.stored.artifacts.set_permissions(
        &case.stored.owner,
        case.binding.artifact_id,
        case.stored.reader.subject(),
        BTreeSet::new(),
        9,
    )?;
    let expected =
        StoredFullDocumentProductFormError::FullDocument(StoredFullDocumentFormError::Artifact);
    assert_eq!(
        prepared.verify(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            10
        ),
        Err(expected)
    );
    assert_eq!(
        prepared.require_current_product_route(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            10
        ),
        Err(StoredFullDocumentProductFormError::FullDocument(
            StoredFullDocumentFormError::Artifact
        ))
    );
    assert!(
        case.stored
            .artifacts
            .download(&case.stored.reader, case.stored.result, 10)?
            == case.form.source
    );
    case.stored.artifacts.set_permissions(
        &case.stored.owner,
        case.binding.artifact_id,
        case.stored.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        11,
    )?;
    assert_eq!(
        prepared.verify(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            12
        )?,
        *prepared.receipt()
    );
    case.stored.artifacts.set_permissions(
        &case.stored.owner,
        case.stored.result,
        case.stored.reader.subject(),
        BTreeSet::new(),
        13,
    )?;
    assert_eq!(
        prepared.verify(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            14
        ),
        Err(StoredFullDocumentProductFormError::Provider(
            StoredProductFormError::Stored(StoredFormError::Artifact)
        ))
    );
    assert_no_publish(&case.stored, case.stored.head, 3)
}

#[test]
fn full_request_fresh_ir_aead_corruption_recovery_and_source_corruption_are_checked() -> TestResult
{
    let case = Case::new()?;
    let prepared = case.prepare()?;
    case.stored.blobs.tamper_ir.store(true, Ordering::SeqCst);
    assert_eq!(
        prepared.verify(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            10
        ),
        Err(StoredFullDocumentProductFormError::FullDocument(
            StoredFullDocumentFormError::Artifact
        ))
    );
    assert!(
        case.stored
            .artifacts
            .download(&case.stored.reader, case.stored.result, 10)?
            == case.form.source
    );
    case.stored.blobs.tamper_ir.store(false, Ordering::SeqCst);
    assert_eq!(
        prepared.verify(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            11
        )?,
        *prepared.receipt()
    );
    case.stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert_eq!(
        prepared.require_current_product_route(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            12
        ),
        Err(StoredFullDocumentProductFormError::Provider(
            StoredProductFormError::Stored(StoredFormError::Artifact)
        ))
    );
    assert_no_publish(&case.stored, case.stored.head, 3)
}

#[test]
fn full_request_fresh_ir_quarantine_blocks_an_old_valid_preparation() -> TestResult {
    let case = Case::new()?;
    let prepared = case.prepare()?;
    case.stored.artifacts.quarantine(
        &case.stored.owner,
        case.binding.artifact_id,
        QuarantineReason::parse("P64_SYNTHETIC_QUARANTINE")?,
        9,
    )?;
    assert_eq!(
        prepared.verify(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            10
        ),
        Err(StoredFullDocumentProductFormError::FullDocument(
            StoredFullDocumentFormError::Artifact
        ))
    );
    assert!(
        case.stored
            .artifacts
            .download(&case.stored.reader, case.stored.result, 10)?
            == case.form.source
    );
    assert_no_publish(&case.stored, case.stored.head, 3)
}

#[test]
fn full_request_real_head_advance_invalidates_old_and_fresh_missing_ir_cannot_fall_back()
-> TestResult {
    let mut case = Case::new()?;
    let prepared = case.prepare()?;
    let input = serde_json::to_vec(&case.request["form_input"])?;
    case.stored.advance()?;
    let new_head = case.stored.revisions.head(
        &case.stored.revision_context,
        case.stored.project,
        case.stored.branch,
    )?;
    assert_eq!(
        prepared.verify(
            &case.stored.provider()?,
            &bindings(&case.form, &case.access),
            10
        ),
        Err(StoredFullDocumentProductFormError::Provider(
            StoredProductFormError::Stored(StoredFormError::Head)
        ))
    );
    case.stored.head = new_head;
    let fresh = envelope(&case.stored, &case.form, &input)?;
    assert!(matches!(
        StoredFullDocumentProductFormRequest::prepare_json(
            &case.stored.provider()?,
            &serde_json::to_vec(&fresh)?,
            &bindings(&case.form, &case.access),
            11
        ),
        Err(StoredFullDocumentProductFormError::FullDocument(
            StoredFullDocumentFormError::MissingIr
        ))
    ));
    assert_no_publish(&case.stored, new_head, 3)
}

#[test]
fn full_request_fresh_map_policy_access_or_provider_scope_cannot_rebind() -> TestResult {
    let case = Case::new()?;
    let prepared = case.prepare()?;
    let mut access = case.access.clone();
    access.input_allowed = false;
    assert!(
        prepared
            .verify(&case.stored.provider()?, &bindings(&case.form, &access), 9)
            .is_err()
    );
    let mut policies = case.form.policies.clone();
    let FormControlPayload::Text { default_value, .. } = &mut policies[0].payload else {
        return Err("text".into());
    };
    *default_value = "changed provider default".into();
    let changed = StoredProductFormBindings {
        map: &case.form.map,
        policies: &policies,
        access: &case.access,
    };
    assert!(
        prepared
            .verify(&case.stored.provider()?, &changed, 9)
            .is_err()
    );
    let mut map = case.form.map.clone();
    map.sections[0].map.component_controls[0].logical_control_id =
        LogicalId::parse("different-control")?;
    let changed = StoredProductFormBindings {
        map: &map,
        policies: &case.form.policies,
        access: &case.access,
    };
    assert!(
        prepared
            .verify(&case.stored.provider()?, &changed, 9)
            .is_err()
    );
    let wrong = StoredFormProvider::bind(
        &case.stored.artifacts,
        &case.stored.revisions,
        &case.stored.reader,
        &case.stored.revision_context,
        case.stored.project,
        case.stored.branch,
        DocumentId::parse("wrong-document")?,
    )?;
    assert_eq!(
        prepared.verify(&wrong, &bindings(&case.form, &case.access), 9),
        Err(StoredFullDocumentProductFormError::Provider(
            StoredProductFormError::Stored(StoredFormError::Scope)
        ))
    );
    assert_no_publish(&case.stored, case.stored.head, 3)
}

#[test]
fn full_request_canonical_retry_plan_key_and_public_receipt_are_not_idempotency_or_secrets()
-> TestResult {
    let case = Case::new()?;
    let original = case.prepare()?;
    let pretty = StoredFullDocumentProductFormRequest::prepare_json(
        &case.stored.provider()?,
        &serde_json::to_vec_pretty(&case.request)?,
        &bindings(&case.form, &case.access),
        9,
    )?;
    assert_ne!(
        original.receipt().raw_request_sha256,
        pretty.receipt().raw_request_sha256
    );
    assert_eq!(
        original.receipt().canonical_request_sha256,
        pretty.receipt().canonical_request_sha256
    );
    assert_eq!(
        original.receipt().scoped_request_sha256,
        pretty.receipt().scoped_request_sha256
    );
    assert_eq!(
        original.receipt().full_document,
        pretty.receipt().full_document
    );
    assert!(original.candidate_bytes() == pretty.candidate_bytes());
    assert!(original.target_graph() == pretty.target_graph());
    for (field, value) in [
        ("idempotency_key", "another-synthetic-key"),
        ("plan_id", "another-synthetic-plan"),
    ] {
        let mut changed = case.request.clone();
        changed[field] = serde_json::json!(value);
        let prepared = product_prepare(&case.stored, &case.form, &changed, &case.access)?;
        assert_ne!(
            prepared.receipt().canonical_request_sha256,
            original.receipt().canonical_request_sha256
        );
        assert_ne!(
            prepared.receipt().scoped_request_sha256,
            original.receipt().scoped_request_sha256
        );
        assert!(prepared.candidate_bytes() == original.candidate_bytes());
        assert!(prepared.target_graph() == original.target_graph());
        assert_eq!(
            prepared.compiled_plan().plan_id().as_str(),
            changed["plan_id"].as_str().ok_or("plan")?
        );
    }
    for output in [
        serde_json::to_string(original.receipt())?,
        format!("{original:?}"),
        format!("{:?}", bindings(&case.form, &case.access)),
    ] {
        for private in [
            "P64 synthetic private value",
            "test-only caller paragraph",
            "P64-synthetic-private-retry-key",
            "stored-full-document-plan",
            CAPTURE,
            &case.binding.artifact_id.public_id(),
            &case.stored.result.public_id(),
            &case.stored.project.public_id(),
            &case.stored.head.revision_id().ok_or("head")?.public_id(),
        ] {
            assert!(
                !output.contains(private),
                "private receipt/debug field leaked"
            );
        }
    }
    assert_no_publish(&case.stored, case.stored.head, 3)
}
