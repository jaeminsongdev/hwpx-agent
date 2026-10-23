#![allow(clippy::expect_used)] // Explicit synthetic fixture IDs only, not product code.
//! Stored comment preparation: actual service APIs, in-memory storage and synthetic complete IR.
//! No native HWPX/comment source authenticity, external issuer, SQL or product route is asserted.
#[path = "stored_comment_provider/comment_fixture.rs"]
mod comment_fixture;
#[path = "stored_comment_provider/store_fixture.rs"]
mod store_fixture;
use artifact_service::*;
use comment_fixture::{graph, id, limits, operations, request, state};
use domain_ir::*;
use hwpx_agent_cli::{
    comment_operation::*,
    form_stored_provider::{StoredFormError, StoredFormProvider, comments::*, full_document::*},
};
use revision_service::{FullDocumentIrBinding, RevisionHead, RevisionRequestContext};
use serde_json::{Value, json};
use std::{collections::BTreeSet, error::Error, sync::atomic::Ordering};
use store_fixture::{SOURCE, Stored};
use uuid::Uuid;
type TestResult = Result<(), Box<dyn Error>>;
#[path = "stored_comment_provider/rich_bodies.rs"]
mod rich_bodies;
type Fixture = (
    Stored,
    DocumentGraph,
    CommentDocumentState,
    FullDocumentIrBinding,
);

fn valid() -> Result<Fixture, Box<dyn Error>> {
    let state = state()?;
    let graph = graph(&state)?;
    let mut stored = Stored::new(ArtifactKind::Result, false)?;
    let binding = stored.attach(
        &graph,
        graph.canonical_json()?,
        ArtifactKind::DocumentIr,
        DOCUMENT_IR_MEDIA_TYPE,
        0,
    )?;
    Ok((stored, graph, state, binding))
}
fn context<'a>(
    stored: &Stored,
    graph: &'a DocumentGraph,
    state: &'a CommentDocumentState,
) -> Result<CommentOperationContext<'a>, Box<dyn Error>> {
    Ok(CommentOperationContext::bind(
        graph,
        state,
        graph.canonical_sha256()?,
        *ContentDigest::of(SOURCE).as_bytes(),
        domain_ir::RevisionId::parse(stored.head.revision_id().ok_or("fixture head")?.public_id())?,
    )?)
}
fn inputs(
    head: RevisionHead,
    raw: &[u8],
    insertion: Option<CommentInsertionTarget>,
) -> Result<StoredCommentInputs<'_>, Box<dyn Error>> {
    Ok(StoredCommentInputs {
        expected_head: head,
        plan_id: PlanId::parse("stored-comment-plan")?,
        request_json: raw,
        insertion,
    })
}
fn prepare(
    stored: &Stored,
    graph: &DocumentGraph,
    state: &CommentDocumentState,
) -> Result<PreparedStoredComment, Box<dyn Error>> {
    let raw = request(
        &context(stored, graph, state)?,
        state,
        operations(state).remove(3),
    )?;
    Ok(stored
        .provider()?
        .prepare_comment_json(inputs(stored.head, &raw, None)?, 10)?)
}
fn no_writes(stored: &Stored, ingested: usize) -> TestResult {
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    let events = stored.metadata.audit_events()?;
    assert_eq!(
        events
            .iter()
            .filter(|v| v.event == "artifact.ingested")
            .count(),
        ingested
    );
    Ok(())
}

#[test]
fn all_five_original_operations_use_revision_selected_ir_and_original_compiler_without_writes()
-> TestResult {
    let (stored, graph, state, binding) = valid()?;
    let original = graph.canonical_json()?;
    let ctx = context(&stored, &graph, &state)?;
    for operation in operations(&state) {
        let insertion = if let CommentOperation::InsertComment { comment, .. } = &operation {
            Some(CommentInsertionTarget {
                anchor: comment.anchor.clone(),
                node_id: id("body-3"),
            })
        } else {
            None
        };
        let raw = request(&ctx, &state, operation)?;
        let expected = CommentOperationPreparation::prepare_json(
            &ctx,
            PlanId::parse("stored-comment-plan")?,
            &raw,
            insertion.clone(),
        )?;
        let prepared = stored
            .provider()?
            .prepare_comment_json(inputs(stored.head, &raw, insertion)?, 10)?;
        assert_eq!(prepared.target_graph(), expected.target_graph());
        assert_eq!(prepared.compiled_plan(), expected.compiled());
        assert_eq!(prepared.receipt().operation, *expected.receipt());
        assert_eq!(
            prepared.receipt().source_sha256,
            ContentDigest::of(SOURCE).hex()
        );
        assert_eq!(prepared.receipt().source_bytes, SOURCE.len());
        assert_eq!(
            prepared.receipt().ir_artifact_sha256,
            binding.artifact_sha256.hex()
        );
        assert_eq!(
            prepared.verify(&stored.provider()?, 11)?,
            *prepared.receipt()
        );
        assert_eq!(
            prepared.require_current_product_route(&stored.provider()?, 12),
            Err(StoredCommentError::RouteUnqualified)
        );
        assert!(
            !prepared
                .receipt()
                .operation
                .native_author_time_state_verified
        );
        assert!(!prepared.receipt().operation.hwpx_lowered);
        assert!(!prepared.receipt().operation.execution_authority_verified);
        assert_eq!(
            stored
                .artifacts
                .download(&stored.reader, stored.result, 13)?,
            SOURCE
        );
        assert_eq!(
            stored
                .artifacts
                .download(&stored.reader, binding.artifact_id, 13)?,
            original
        );
        no_writes(&stored, 3)?;
    }
    let events = stored.metadata.audit_events()?;
    assert!(
        events
            .iter()
            .any(|v| v.event == "artifact.download" && v.artifact_id == stored.result)
    );
    assert!(
        events
            .iter()
            .any(|v| v.event == "artifact.download" && v.artifact_id == binding.artifact_id)
    );
    Ok(())
}
#[test]
fn missing_ir_wrong_kind_media_and_three_binding_digests_are_rejected() -> TestResult {
    let state = state()?;
    let graph = graph(&state)?;
    let missing = Stored::new(ArtifactKind::Result, false)?;
    assert!(prepare(&missing, &graph, &state).is_err());
    for (kind, media, fault) in [
        (ArtifactKind::Evidence, DOCUMENT_IR_MEDIA_TYPE, 0),
        (ArtifactKind::DocumentIr, "application/json", 0),
        (ArtifactKind::DocumentIr, DOCUMENT_IR_MEDIA_TYPE, 1),
        (ArtifactKind::DocumentIr, DOCUMENT_IR_MEDIA_TYPE, 2),
        (ArtifactKind::DocumentIr, DOCUMENT_IR_MEDIA_TYPE, 3),
    ] {
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(&graph, graph.canonical_json()?, kind, media, fault)?;
        assert!(prepare(&stored, &graph, &state).is_err());
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn exact_raw_ir_canonicalization_rejects_whitespace_duplicate_and_unknown_keys() -> TestResult {
    let state = state()?;
    let graph = graph(&state)?;
    let original = String::from_utf8(graph.canonical_json()?)?;
    let faults = [
        format!("{original}\n"),
        original.replacen('{', "{\"schema_version\":\"duplicate\",", 1),
        original.replacen('{', "{\"unknown\":1,", 1),
    ];
    for raw in faults {
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(
            &graph,
            raw.into_bytes(),
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(prepare(&stored, &graph, &state).is_err());
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn stored_complete_comment_state_never_defaults_missing_unknown_duplicate_or_oversized_data()
-> TestResult {
    let state = state()?;
    let original = graph(&state)?;
    let raw = String::from_utf8(state.canonical_json(limits())?)?;
    let invalid = [
        PropertyValue::Text("{}".into()),
        PropertyValue::Boolean(true),
        PropertyValue::Text(format!("{raw}\n")),
        PropertyValue::Text(raw.replacen('{', "{\"schema_version\":\"duplicate\",", 1)),
        PropertyValue::Text(raw.replacen('{', "{\"unknown\":true,", 1)),
        PropertyValue::Text(" ".repeat(1024 * 1024 + 1)),
    ];
    for value in invalid {
        let mut draft = original.clone().into_draft();
        draft.metadata.insert(COMMENT_STATE_PROPERTY, value);
        let altered = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(
            &altered,
            altered.canonical_json()?,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(prepare(&stored, &original, &state).is_err());
        no_writes(&stored, 3)?;
    }
    let mut draft = original.clone().into_draft();
    draft.metadata = Properties::new();
    let altered = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    let mut stored = Stored::new(ArtifactKind::Result, false)?;
    stored.attach(
        &altered,
        altered.canonical_json()?,
        ArtifactKind::DocumentIr,
        DOCUMENT_IR_MEDIA_TYPE,
        0,
    )?;
    assert!(prepare(&stored, &original, &state).is_err());
    Ok(())
}
#[test]
fn persisted_partial_import_or_protected_signed_encrypted_graphs_are_not_authority() -> TestResult {
    let state = state()?;
    let original = graph(&state)?;
    for fault in 0..5 {
        let mut draft = original.clone().into_draft();
        match fault {
            0 => draft.metadata.insert(
                "review_body_import_profile",
                PropertyValue::Text(
                    hwpx_package::document_import::structure::review::REVIEW_BODY_IMPORT_PROFILE
                        .into(),
                ),
            ),
            1 => {
                draft.source_profile = Some(id(
                    hwpx_package::document_import::structure::STRUCTURE_IMPORT_PROFILE,
                ));
            }
            2 => draft.security_state.protected = true,
            3 => draft.security_state.signed = true,
            _ => draft.security_state.encrypted = true,
        }
        let altered = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(
            &altered,
            altered.canonical_json()?,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(prepare(&stored, &original, &state).is_err());
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn stored_comment_views_require_exact_complete_section_style_and_review_binding() -> TestResult {
    let state = state()?;
    let original = graph(&state)?;
    for fault in 0..4 {
        let mut draft = original.clone().into_draft();
        match fault {
            0 => {
                draft.review.remove(0);
            }
            1 => draft.review[1].target_node_id = id("body-1"),
            2 => draft.styles[0]
                .properties
                .insert(COMMENT_STYLE_PROPERTY, PropertyValue::Text("{}".into())),
            _ => draft.sections[0]
                .properties
                .insert(COMMENT_SECTION_PROPERTY, PropertyValue::Text("{}".into())),
        }
        let altered = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        let mut stored = Stored::new(ArtifactKind::Result, false)?;
        stored.attach(
            &altered,
            altered.canonical_json()?,
            ArtifactKind::DocumentIr,
            DOCUMENT_IR_MEDIA_TYPE,
            0,
        )?;
        assert!(prepare(&stored, &original, &state).is_err());
    }
    Ok(())
}
#[test]
fn document_scope_is_checked_before_complete_state_and_different_scope_cannot_reverify()
-> TestResult {
    let (stored, graph, state, _) = valid()?;
    let prepared = prepare(&stored, &graph, &state)?;
    let wrong = stored.provider_document("other-document")?;
    assert_eq!(prepared.verify(&wrong, 11), Err(StoredCommentError::Scope));
    let raw = request(
        &context(&stored, &graph, &state)?,
        &state,
        operations(&state).remove(3),
    )?;
    assert!(matches!(
        wrong.prepare_comment_json(inputs(stored.head, &raw, None)?, 11),
        Err(StoredCommentError::Scope)
    ));
    no_writes(&stored, 3)
}
#[test]
fn independent_ir_and_source_acl_revocations_precede_route_denial_and_regrant_revalidates()
-> TestResult {
    for ir in [false, true] {
        let (stored, graph, state, binding) = valid()?;
        let prepared = prepare(&stored, &graph, &state)?;
        let target = if ir {
            binding.artifact_id
        } else {
            stored.result
        };
        let untouched = if ir {
            stored.result
        } else {
            binding.artifact_id
        };
        stored.artifacts.set_permissions(
            &stored.owner,
            target,
            stored.reader.subject(),
            BTreeSet::new(),
            11,
        )?;
        let error = if ir {
            StoredCommentError::Ir(StoredFullDocumentFormError::Artifact)
        } else {
            StoredCommentError::Source(StoredFormError::Artifact)
        };
        assert_eq!(
            prepared.verify(&stored.provider()?, 12).as_ref().err(),
            Some(&error)
        );
        assert_eq!(
            prepared.require_current_product_route(&stored.provider()?, 12),
            Err(error)
        );
        assert!(
            !stored
                .artifacts
                .download(&stored.reader, untouched, 12)?
                .is_empty()
        );
        stored.artifacts.set_permissions(
            &stored.owner,
            target,
            stored.reader.subject(),
            BTreeSet::from([ArtifactPermission::Read]),
            13,
        )?;
        assert_eq!(
            prepared.verify(&stored.provider()?, 14)?,
            *prepared.receipt()
        );
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn independent_ir_and_source_quarantine_precede_route_denial() -> TestResult {
    for ir in [false, true] {
        let (stored, graph, state, binding) = valid()?;
        let prepared = prepare(&stored, &graph, &state)?;
        stored.artifacts.quarantine(
            &stored.owner,
            if ir {
                binding.artifact_id
            } else {
                stored.result
            },
            QuarantineReason::parse("P94_FIXTURE_QUARANTINE")?,
            11,
        )?;
        assert!(prepared.verify(&stored.provider()?, 12).is_err());
        assert!(!matches!(
            prepared.require_current_product_route(&stored.provider()?, 12),
            Err(StoredCommentError::RouteUnqualified)
        ));
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn independent_ir_and_source_ciphertext_corruption_rejects_and_never_changes_other_content()
-> TestResult {
    for ir in [false, true] {
        let (stored, graph, state, binding) = valid()?;
        let prepared = prepare(&stored, &graph, &state)?;
        let flag = if ir {
            &stored.blob.ir_tamper
        } else {
            &stored.blob.result_tamper
        };
        flag.store(true, Ordering::SeqCst);
        assert!(prepared.verify(&stored.provider()?, 11).is_err());
        assert!(!matches!(
            prepared.require_current_product_route(&stored.provider()?, 11),
            Err(StoredCommentError::RouteUnqualified)
        ));
        let untouched = if ir {
            stored.result
        } else {
            binding.artifact_id
        };
        assert!(
            !stored
                .artifacts
                .download(&stored.reader, untouched, 11)?
                .is_empty()
        );
        flag.store(false, Ordering::SeqCst);
        assert_eq!(
            prepared.verify(&stored.provider()?, 12)?,
            *prepared.receipt()
        );
        no_writes(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn unverified_scanner_for_source_or_ir_and_wrong_source_kind_never_prepare() -> TestResult {
    let state = state()?;
    let graph = graph(&state)?;
    for (kind, unverified) in [
        (ArtifactKind::Evidence, false),
        (ArtifactKind::Result, true),
    ] {
        let stored = Stored::new(kind, unverified)?;
        assert!(prepare(&stored, &graph, &state).is_err());
    }
    let mut stored = Stored::new(ArtifactKind::Result, false)?;
    stored.attach(
        &graph,
        graph.canonical_json()?,
        ArtifactKind::DocumentIr,
        DOCUMENT_IR_MEDIA_TYPE,
        4,
    )?;
    assert!(prepare(&stored, &graph, &state).is_err());
    no_writes(&stored, 3)
}
#[test]
fn head_advance_and_empty_head_are_rejected_without_mutating_prior_sealed_node() -> TestResult {
    let (stored, graph, state, binding) = valid()?;
    let prepared = prepare(&stored, &graph, &state)?;
    let raw = request(
        &context(&stored, &graph, &state)?,
        &state,
        operations(&state).remove(3),
    )?;
    assert!(
        stored
            .provider()?
            .prepare_comment_json(inputs(RevisionHead::empty(), &raw, None)?, 11)
            .is_err()
    );
    stored.advance()?;
    assert_eq!(
        prepared.verify(&stored.provider()?, 12),
        Err(StoredCommentError::Source(StoredFormError::Head))
    );
    assert_eq!(
        prepared.require_current_product_route(&stored.provider()?, 12),
        Err(StoredCommentError::Source(StoredFormError::Head))
    );
    let old = stored.revisions.node(
        &stored.revision_context,
        stored.project,
        stored.head.revision_id().ok_or("old fixture head")?,
    )?;
    assert!(old.sealed());
    assert_eq!(old.full_document_ir(), Some(binding));
    assert_eq!(old.result_artifact_id(), stored.result);
    Ok(())
}
#[test]
fn provider_rejects_mismatched_actor_tenant_or_absent_read_scope_and_other_actor_reverification()
-> TestResult {
    let (stored, graph, state, _) = valid()?;
    let prepared = prepare(&stored, &graph, &state)?;
    let other = SubjectDigest::from_authenticated_subject("P94 other fixture actor")?;
    let contexts = [
        RequestContext::new(stored.reader.tenant_id(), other, [AuthScope::DocumentRead]),
        RequestContext::new(
            TenantId::new(Uuid::from_u128(9402))?,
            stored.reader.subject(),
            [AuthScope::DocumentRead],
        ),
        RequestContext::new(stored.reader.tenant_id(), stored.reader.subject(), []),
    ];
    for actor in contexts {
        assert!(
            StoredFormProvider::bind(
                &stored.artifacts,
                &stored.revisions,
                &actor,
                &stored.revision_context,
                stored.project,
                stored.branch,
                graph.document_id().clone()
            )
            .is_err()
        );
    }
    let actor = RequestContext::new(stored.reader.tenant_id(), other, [AuthScope::DocumentRead]);
    let revisions = RevisionRequestContext::new(actor.tenant_id(), actor.subject());
    let other_provider = StoredFormProvider::bind(
        &stored.artifacts,
        &stored.revisions,
        &actor,
        &revisions,
        stored.project,
        stored.branch,
        graph.document_id().clone(),
    )?;
    assert_eq!(
        prepared.verify(&other_provider, 11),
        Err(StoredCommentError::Scope)
    );
    no_writes(&stored, 3)
}
#[test]
fn request_and_insertion_remain_strict_and_do_not_publish_or_default_native_values() -> TestResult {
    let (stored, graph, state, _) = valid()?;
    let ctx = context(&stored, &graph, &state)?;
    let raw = request(&ctx, &state, operations(&state).remove(3))?;
    let mut extra: Value = serde_json::from_slice(&raw)?;
    extra["caller_artifact_id"] = json!("art_fake");
    let duplicate =
        String::from_utf8(raw.clone())?.replacen('{', "{\"schema_version\":\"duplicate\",", 1);
    let invalid = [
        serde_json::to_vec(&extra)?,
        duplicate.into_bytes(),
        vec![b' '; 1024 * 1024 + 1],
        serde_json::to_vec(&json!({"operation":{"kind":"delete_comment"}}))?,
    ];
    for raw in invalid {
        assert!(
            stored
                .provider()?
                .prepare_comment_json(inputs(stored.head, &raw, None)?, 11)
                .is_err()
        );
    }
    let insertion = operations(&state).remove(1);
    let CommentOperation::InsertComment { comment, .. } = &insertion else {
        return Err("fixture insert".into());
    };
    let invalid = [
        None,
        Some(CommentInsertionTarget {
            anchor: comment.anchor.clone(),
            node_id: id("body-4"),
        }),
        Some(CommentInsertionTarget {
            anchor: comment.anchor.clone(),
            node_id: id("missing"),
        }),
    ];
    let raw = request(&ctx, &state, insertion.clone())?;
    for binding in invalid {
        assert!(
            stored
                .provider()?
                .prepare_comment_json(inputs(stored.head, &raw, binding)?, 11)
                .is_err()
        );
    }
    no_writes(&stored, 3)
}
#[test]
fn safe_receipt_and_debug_never_contain_document_actor_request_or_paths() -> TestResult {
    let (stored, graph, state, _) = valid()?;
    let prepared = prepare(&stored, &graph, &state)?;
    let receipt = serde_json::to_string(prepared.receipt())?;
    let debug = format!("{prepared:?} {:?}", stored.provider()?);
    for private in [
        "synthetic caller text",
        "P94 synthetic",
        "comment-document",
        "body-1",
        "fixture-complete-ir.json",
        "comment-1",
    ] {
        assert!(!receipt.contains(private));
        assert!(!debug.contains(private));
    }
    assert!(receipt.contains(STORED_COMMENT_PROFILE));
    no_writes(&stored, 3)
}

#[test]
fn head_change_during_actual_ir_download_is_rejected_in_prepare_and_fresh_verify() -> TestResult {
    for prepared_first in [false, true] {
        let (stored, graph, state, binding) = valid()?;
        let prepared = if prepared_first {
            Some(prepare(&stored, &graph, &state)?)
        } else {
            None
        };
        stored.advance_on_next_ir_read()?;
        if let Some(prepared) = prepared {
            assert_eq!(
                prepared.verify(&stored.provider()?, 11),
                Err(StoredCommentError::Ir(StoredFullDocumentFormError::Head))
            );
        } else {
            let raw = request(
                &context(&stored, &graph, &state)?,
                &state,
                operations(&state).remove(3),
            )?;
            assert!(matches!(
                stored
                    .provider()?
                    .prepare_comment_json(inputs(stored.head, &raw, None)?, 11),
                Err(StoredCommentError::Ir(StoredFullDocumentFormError::Head))
            ));
        }
        assert_ne!(
            stored
                .revisions
                .head(&stored.revision_context, stored.project, stored.branch)?,
            stored.head
        );
        let original = stored.revisions.node(
            &stored.revision_context,
            stored.project,
            stored.head.revision_id().ok_or("fixture original head")?,
        )?;
        assert_eq!(original.full_document_ir(), Some(binding));
        assert_eq!(
            stored
                .metadata
                .audit_events()?
                .iter()
                .filter(|v| v.event == "artifact.ingested")
                .count(),
            3
        );
    }
    Ok(())
}
