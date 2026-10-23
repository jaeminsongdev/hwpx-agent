//! Persisted caller-complete rich IR using ORIGINAL service/fixture APIs; NOT native/SQL evidence.
use super::*;
use hwpx_agent_cli::{
    comment_operation::rich_bodies::*, form_stored_provider::comments::rich_bodies::*,
};
type RichFixture = (
    Stored,
    DocumentGraph,
    CommentDocumentState,
    FullDocumentIrBinding,
    Vec<CommentRichBody>,
);
fn paragraph(prefix: &str) -> Node {
    Node::Paragraph(ParagraphNode {
        common: NodeCommon::new(id(prefix)),
        inlines: vec![
            Inline::Text {
                text: "P109-PRIVATE 한글 & body".into(),
            },
            Inline::Tab,
            Inline::LineBreak,
        ],
        paragraph_properties: Properties::new(),
    })
}
fn body(prefix: &str) -> Flow {
    let mut paragraph = paragraph(&format!("{prefix}-p"));
    if let Node::Paragraph(p) = &mut paragraph {
        p.common.style_refs.push(id("unrelated-style"));
    }
    Flow {
        children: vec![
            paragraph,
            Node::Table(TableNode {
                common: NodeCommon::new(id(&format!("{prefix}-table"))),
                rows: 1,
                columns: 1,
                cells: vec![TableCell {
                    cell_id: id(&format!("{prefix}-cell")),
                    row: 0,
                    column: 0,
                    row_span: 1,
                    column_span: 1,
                    body: Flow {
                        children: vec![self::paragraph(&format!("{prefix}-cell-p"))],
                    },
                    properties: Properties::new(),
                }],
                properties: Properties::new(),
            }),
        ],
    }
}
fn rich_bodies() -> Vec<CommentRichBody> {
    [
        ("explanation-1", "hidden"),
        ("comment-1", "memo1"),
        ("comment-2", "memo2"),
    ]
    .into_iter()
    .map(|(review, prefix)| CommentRichBody {
        review_id: id(review),
        body: body(prefix),
    })
    .collect()
}
fn rich_state(bodies: &[CommentRichBody]) -> Result<CommentDocumentState, Box<dyn Error>> {
    let mut value: Value = serde_json::from_slice(&state()?.canonical_json(limits())?)?;
    for body in bodies {
        for (list, key) in [
            ("hidden_explanations", "logical_explanation_id"),
            ("comments", "logical_comment_id"),
        ] {
            for entry in value[list].as_array_mut().ok_or("entries")? {
                if entry["identity"][key].as_str() == Some(body.review_id.as_str()) {
                    entry["body_graph_sha256"] = Value::String(body_sha256(&body.body)?);
                }
            }
        }
    }
    Ok(CommentDocumentState::from_draft(
        serde_json::from_value(value)?,
        limits(),
    )?)
}
fn rich_graph(
    state: &CommentDocumentState,
    bodies: &[CommentRichBody],
) -> Result<DocumentGraph, Box<dyn Error>> {
    let mut draft = graph(state)?.into_draft();
    draft.metadata.insert(
        COMMENT_RICH_BODIES_PROPERTY,
        PropertyValue::Text(bodies_json(bodies)?),
    );
    Ok(DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits::default(),
    )?)
}
fn valid_rich() -> Result<RichFixture, Box<dyn Error>> {
    let bodies = rich_bodies();
    let state = rich_state(&bodies)?;
    let graph = rich_graph(&state, &bodies)?;
    let mut stored = Stored::new(ArtifactKind::Result, false)?;
    let binding = stored.attach(
        &graph,
        graph.canonical_json()?,
        ArtifactKind::DocumentIr,
        DOCUMENT_IR_MEDIA_TYPE,
        0,
    )?;
    Ok((stored, graph, state, binding, bodies))
}
fn prepare_rich(
    stored: &Stored,
    graph: &DocumentGraph,
    state: &CommentDocumentState,
) -> Result<PreparedStoredRichComment, Box<dyn Error>> {
    let raw = request(
        &context(stored, graph, state)?,
        state,
        operations(state).remove(3),
    )?;
    Ok(stored
        .provider()?
        .prepare_rich_comment_json(inputs(stored.head, &raw, None)?, None, 10)?)
}
#[test]
fn all_five_operations_load_entire_persisted_bodies_and_bind_actual_final_compiler_without_writes()
-> TestResult {
    let (stored, graph, state, binding, bodies) = valid_rich()?;
    let ctx = context(&stored, &graph, &state)?;
    let rich = CommentRichContext::bind(&ctx, bodies)?;
    let before = graph.clone().into_draft();
    for mut operation in operations(&state) {
        let (insertion, new_body) =
            if let CommentOperation::InsertComment { comment, .. } = &mut operation {
                let new_body = CommentRichBody {
                    review_id: comment.identity.logical_comment_id.clone(),
                    body: body("new-memo"),
                };
                comment.body_graph_sha256 = body_sha256(&new_body.body)?;
                (
                    Some(CommentInsertionTarget {
                        anchor: comment.anchor.clone(),
                        node_id: id("body-3"),
                    }),
                    Some(new_body),
                )
            } else {
                (None, None)
            };
        let raw = request(&ctx, &state, operation)?;
        let expected = RichCommentOperationPreparation::prepare_json(
            &rich,
            PlanId::parse("stored-comment-plan")?,
            &raw,
            insertion.clone(),
            new_body.clone(),
        )?;
        let prepared = stored.provider()?.prepare_rich_comment_json(
            inputs(stored.head, &raw, insertion)?,
            new_body,
            10,
        )?;
        assert_eq!(prepared.target_graph(), expected.target_graph());
        assert_eq!(prepared.compiled_plan(), expected.compiled());
        assert_eq!(prepared.target_bodies(), expected.target_bodies());
        assert_eq!(&prepared.receipt().operation, expected.receipt());
        assert_eq!(
            prepared.receipt().ir_artifact_sha256,
            binding.artifact_sha256.hex()
        );
        assert_eq!(
            prepared.verify(&stored.provider()?, 11)?,
            *prepared.receipt()
        );
        assert_eq!(
            prepared.require_current_product_route(&stored.provider()?, 11),
            Err(StoredCommentError::RouteUnqualified)
        );
        let target = prepared.target_graph().clone().into_draft();
        assert_eq!(target.sections, before.sections);
        assert_eq!(target.notes, before.notes);
        assert_eq!(target.resources, before.resources);
        assert_eq!(target.references, before.references);
        assert!(
            !prepared.receipt().operation.native_metadata_verified
                && !prepared.receipt().operation.hwpx_lowered
                && !prepared.receipt().operation.execution_authority_verified
        );
        let receipt = serde_json::to_string(prepared.receipt())?;
        let debug = format!("{prepared:?}");
        for private in [
            "P109-PRIVATE",
            "P94 synthetic",
            "comment-document",
            "comment-1",
            "fixture-complete-ir.json",
        ] {
            assert!(!receipt.contains(private) && !debug.contains(private));
        }
        assert_eq!(
            stored
                .artifacts
                .download(&stored.reader, binding.artifact_id, 12)?,
            graph.canonical_json()?
        );
        assert_eq!(
            stored
                .artifacts
                .download(&stored.reader, stored.result, 12)?,
            SOURCE
        );
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn canonical_outer_ir_never_admits_noncanonical_unknown_duplicate_or_missing_inner_body_json()
-> TestResult {
    let (_, original, state, _, bodies) = valid_rich()?;
    let json = bodies_json(&bodies)?;
    let mut unknown: Value = serde_json::from_str(&json)?;
    unknown[0]["caller_approval"] = json!(true);
    let mut missing: Value = serde_json::from_str(&json)?;
    missing[0].as_object_mut().ok_or("body")?.remove("body");
    for value in [
        PropertyValue::Boolean(true),
        PropertyValue::Text("{}".into()),
        PropertyValue::Text(format!("{json}\n")),
        PropertyValue::Text(json.replacen('{', "{\"review_id\":\"duplicate\",", 1)),
        PropertyValue::Text(serde_json::to_string(&unknown)?),
        PropertyValue::Text(serde_json::to_string(&missing)?),
    ] {
        let mut draft = original.clone().into_draft();
        draft.metadata.insert(COMMENT_RICH_BODIES_PROPERTY, value);
        let changed = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(
            &changed,
            changed.canonical_json()?,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(prepare_rich(&stored, &changed, &state).is_err());
        no_writes(&stored, 3)?;
    }
    // The original whole-IR string ceiling rejects this BEFORE inner body parsing.
    // Keep that stronger boundary; do not widen graph limits to reach the new 8MiB guard.
    let mut oversized = original.clone().into_draft();
    oversized.metadata.insert(
        COMMENT_RICH_BODIES_PROPERTY,
        PropertyValue::Text(" ".repeat(8 * 1024 * 1024 + 1)),
    );
    assert!(matches!(
        DocumentGraph::from_draft(oversized, DocumentGraphLimits::default()),
        Err(DocumentGraphError::LimitExceeded)
    ));
    let mut raw_graph: Value = serde_json::from_slice(&original.canonical_json()?)?;
    raw_graph["metadata"][COMMENT_RICH_BODIES_PROPERTY] = json!({
        "kind":"text", "value":" ".repeat(8 * 1024 * 1024 + 1)
    });
    let mut oversized_store = Stored::new(ArtifactKind::Result, false)?;
    oversized_store.attach(
        &original,
        serde_json::to_vec(&raw_graph)?,
        ArtifactKind::DocumentIr,
        DOCUMENT_IR_MEDIA_TYPE,
        0,
    )?;
    let oversized_error = prepare_rich(&oversized_store, &original, &state)
        .err()
        .ok_or("oversize admitted")?;
    assert!(
        oversized_error
            .to_string()
            .contains("stored_comment_ir_invalid")
    );
    no_writes(&oversized_store, 3)?;
    let mut draft = graph(&state)?.into_draft();
    draft
        .metadata
        .insert("unrelated", PropertyValue::Text("no rich view".into()));
    let changed = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    let mut stored = Stored::new(ArtifactKind::Result, false)?;
    stored.attach(
        &changed,
        changed.canonical_json()?,
        ArtifactKind::DocumentIr,
        DOCUMENT_IR_MEDIA_TYPE,
        0,
    )?;
    assert!(prepare_rich(&stored, &changed, &state).is_err());
    Ok(())
}
#[test]
fn persisted_entire_body_order_digest_and_original_graph_protection_constraints_are_checked()
-> TestResult {
    for variant in 0..7 {
        let mut bodies = rich_bodies();
        let state = rich_state(&bodies)?;
        match variant {
            0 => {
                bodies.pop();
            }
            1 => bodies.reverse(),
            2 => bodies.push(bodies[0].clone()),
            3 => bodies[0].body = body("different"),
            _ => {}
        }
        if let Node::Table(t) = &mut bodies[0].body.children[1] {
            match variant {
                4 => t.cells[0].row = 1,
                5 => t.cells[0]
                    .properties
                    .insert("protected", PropertyValue::Boolean(true)),
                6 => t.common.resource_refs.push(id("missing-resource")),
                _ => {}
            }
        }
        let bound_state = if variant >= 4 {
            rich_state(&bodies)?
        } else {
            state
        };
        let graph = rich_graph(&bound_state, &bodies)?;
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(
            &graph,
            graph.canonical_json()?,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(
            prepare_rich(&stored, &graph, &bound_state).is_err(),
            "variant {variant}"
        );
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn independent_result_and_ir_acl_aead_quarantine_fail_before_route_and_regrant_reverifies()
-> TestResult {
    for ir in [false, true] {
        for fault in 0..3 {
            let (stored, graph, state, binding, _) = valid_rich()?;
            let prepared = prepare_rich(&stored, &graph, &state)?;
            let artifact = if ir {
                binding.artifact_id
            } else {
                stored.result
            };
            let flag = if ir {
                &stored.blob.ir_tamper
            } else {
                &stored.blob.result_tamper
            };
            match fault {
                0 => {
                    stored.artifacts.set_permissions(
                        &stored.owner,
                        artifact,
                        stored.reader.subject(),
                        BTreeSet::new(),
                        11,
                    )?;
                }
                1 => flag.store(true, Ordering::SeqCst),
                _ => {
                    stored.artifacts.quarantine(
                        &stored.owner,
                        artifact,
                        QuarantineReason::parse("P109_FIXTURE")?,
                        11,
                    )?;
                }
            }
            assert!(prepared.verify(&stored.provider()?, 12).is_err());
            assert!(!matches!(
                prepared.require_current_product_route(&stored.provider()?, 12),
                Err(StoredCommentError::RouteUnqualified)
            ));
            assert!(prepare_rich(&stored, &graph, &state).is_err());
            if fault < 2 {
                flag.store(false, Ordering::SeqCst);
                stored.artifacts.set_permissions(
                    &stored.owner,
                    artifact,
                    stored.reader.subject(),
                    BTreeSet::from([ArtifactPermission::Read]),
                    13,
                )?;
                assert_eq!(
                    prepared.verify(&stored.provider()?, 14)?,
                    *prepared.receipt()
                );
            }
            no_writes(&stored, 3)?;
        }
    }
    Ok(())
}
#[test]
fn actual_head_advance_in_download_or_after_cache_rejects_without_atomic_publication_claim()
-> TestResult {
    for prepared_first in [false, true] {
        let (stored, graph, state, _, _) = valid_rich()?;
        let prepared = if prepared_first {
            Some(prepare_rich(&stored, &graph, &state)?)
        } else {
            None
        };
        stored.advance_on_next_ir_read()?;
        if let Some(prepared) = prepared {
            assert_eq!(
                prepared.verify(&stored.provider()?, 12),
                Err(StoredCommentError::Ir(StoredFullDocumentFormError::Head))
            );
        } else {
            assert!(prepare_rich(&stored, &graph, &state).is_err());
        }
    }
    let (stored, graph, state, binding, _) = valid_rich()?;
    let prepared = prepare_rich(&stored, &graph, &state)?;
    stored.advance()?;
    assert_eq!(
        prepared.require_current_product_route(&stored.provider()?, 12),
        Err(StoredCommentError::Source(StoredFormError::Head))
    );
    let old = stored.revisions.node(
        &stored.revision_context,
        stored.project,
        stored.head.revision_id().ok_or("head")?,
    )?;
    assert_eq!(old.full_document_ir(), Some(binding));
    Ok(())
}
#[test]
fn fresh_actor_tenant_project_branch_and_document_cannot_rebind_cached_rich_preparation()
-> TestResult {
    let (stored, graph, state, _, _) = valid_rich()?;
    let prepared = prepare_rich(&stored, &graph, &state)?;
    for variant in 0..5 {
        let actor = RequestContext::new(
            if variant == 1 {
                TenantId::new(Uuid::from_u128(109))?
            } else {
                stored.reader.tenant_id()
            },
            if variant == 0 {
                SubjectDigest::from_authenticated_subject("P109 OTHER FIXTURE")?
            } else {
                stored.reader.subject()
            },
            [AuthScope::DocumentRead],
        );
        let revisions = RevisionRequestContext::new(actor.tenant_id(), actor.subject());
        let provider = StoredFormProvider::bind(
            &stored.artifacts,
            &stored.revisions,
            &actor,
            &revisions,
            if variant == 2 {
                revision_service::ProjectId::parse("prj_94000000000000000000000000000002")?
            } else {
                stored.project
            },
            if variant == 3 {
                revision_service::BranchId::parse("brn_94000000000000000000000000000002")?
            } else {
                stored.branch
            },
            if variant == 4 {
                DocumentId::parse("other-document")?
            } else {
                graph.document_id().clone()
            },
        )?;
        assert_eq!(
            prepared.verify(&provider, 12),
            Err(StoredCommentError::Scope)
        );
        assert_eq!(
            prepared.require_current_product_route(&provider, 12),
            Err(StoredCommentError::Scope)
        );
    }
    no_writes(&stored, 3)
}
#[test]
fn stored_rich_insertion_and_original_request_and_partial_document_admission_never_default()
-> TestResult {
    let (stored, original, state, _, _) = valid_rich()?;
    let ctx = context(&stored, &original, &state)?;
    let insert = operations(&state).remove(1);
    let CommentOperation::InsertComment { comment, .. } = &insert else {
        return Err("insert".into());
    };
    let insertion = CommentInsertionTarget {
        anchor: comment.anchor.clone(),
        node_id: id("body-3"),
    };
    let raw = request(&ctx, &state, insert.clone())?;
    for new_body in [
        None,
        Some(CommentRichBody {
            review_id: id("wrong"),
            body: body("new"),
        }),
        Some(CommentRichBody {
            review_id: id("comment-3"),
            body: body("new"),
        }),
    ] {
        assert!(
            stored
                .provider()?
                .prepare_rich_comment_json(
                    inputs(stored.head, &raw, Some(insertion.clone()))?,
                    new_body,
                    10
                )
                .is_err()
        );
    }
    let raw = request(&ctx, &state, operations(&state).remove(0))?;
    let mut invalid: Value = serde_json::from_slice(&raw)?;
    invalid["existing_bodies_override"] = json!([]);
    assert!(
        stored
            .provider()?
            .prepare_rich_comment_json(
                inputs(stored.head, &serde_json::to_vec(&invalid)?, None)?,
                None,
                10
            )
            .is_err()
    );
    for fault in 0..4 {
        let mut draft = original.clone().into_draft();
        match fault {
            0 => draft.metadata.insert(
                "review_body_import_profile",
                PropertyValue::Text(
                    hwpx_package::document_import::structure::review::REVIEW_BODY_IMPORT_PROFILE
                        .into(),
                ),
            ),
            1 => draft.security_state.protected = true,
            2 => draft.security_state.encrypted = true,
            _ => draft.security_state.signed = true,
        }
        let changed = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(
            &changed,
            changed.canonical_json()?,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(prepare_rich(&stored, &changed, &state).is_err());
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn original_missing_ir_kind_media_scanner_and_binding_digest_guards_are_not_bypassed() -> TestResult
{
    let bodies = rich_bodies();
    let state = rich_state(&bodies)?;
    let graph = rich_graph(&state, &bodies)?;
    let missing = Stored::new(ArtifactKind::Result, false)?;
    assert!(prepare_rich(&missing, &graph, &state).is_err());
    for (kind, media, fault) in [
        (ArtifactKind::Evidence, DOCUMENT_IR_MEDIA_TYPE, 0),
        (ArtifactKind::DocumentIr, "application/json", 0),
        (ArtifactKind::DocumentIr, DOCUMENT_IR_MEDIA_TYPE, 1),
        (ArtifactKind::DocumentIr, DOCUMENT_IR_MEDIA_TYPE, 2),
        (ArtifactKind::DocumentIr, DOCUMENT_IR_MEDIA_TYPE, 3),
        (ArtifactKind::DocumentIr, DOCUMENT_IR_MEDIA_TYPE, 4),
    ] {
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(&graph, graph.canonical_json()?, kind, media, fault)?;
        assert!(prepare_rich(&stored, &graph, &state).is_err());
        no_writes(&stored, 3)?;
    }
    for (kind, unverified) in [
        (ArtifactKind::Evidence, false),
        (ArtifactKind::Result, true),
    ] {
        let stored = Stored::new(kind, unverified)?;
        assert!(prepare_rich(&stored, &graph, &state).is_err());
    }
    Ok(())
}
