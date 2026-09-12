#![allow(clippy::expect_used)]

use domain_ir::{
    BookmarkEntry, BookmarkIdentity, BookmarkNativeTag, ExternalLinkPolicy, ExternalTargetApproval,
    HyperlinkEntry, HyperlinkFieldType, HyperlinkIdentity, HyperlinkNativeBeginTag,
    HyperlinkNativeEndTag, HyperlinkNativePair, HyperlinkSemanticBinding, HyperlinkTarget,
    LINK_REFERENCE_SCHEMA_VERSION, LinkAnchor, LinkPoint, LinkReferenceBuilder,
    LinkReferenceDocumentState, LinkReferenceDocumentStateDraft, LinkReferenceError,
    LinkReferenceLimitConfig, LinkReferenceLimits, LinkReferenceOperation, LinkReferenceRequest,
    LinkReferenceRequestDraft, LinkReferenceSectionState, LogicalId, OpaqueLinkProperty,
};
use serde_json::Value;

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const FLOW_A: &str = A;
const FLOW_B: &str = B;

fn limits() -> LinkReferenceLimits {
    LinkReferenceLimits::new(LinkReferenceLimitConfig::default()).expect("valid limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("valid logical id")
}

fn point(paragraph: u32, run: u32, inline: u32) -> LinkPoint {
    LinkPoint {
        paragraph_ordinal: paragraph,
        run_ordinal: run,
        inline_ordinal: inline,
    }
}

fn anchor(start_inline: u32, end_inline: u32) -> LinkAnchor {
    LinkAnchor {
        section_id: id("section-1"),
        start: point(0, 0, start_inline),
        end: point(0, 0, end_inline),
    }
}

fn section(locked: bool) -> LinkReferenceSectionState {
    LinkReferenceSectionState {
        section_id: id("section-1"),
        paragraph_count: 4,
        run_topology_sha256: A.to_owned(),
        inline_topology_sha256: B.to_owned(),
        opaque_section_state_sha256: C.to_owned(),
        locked,
    }
}

fn bookmark(index: u32, name: &str, locked: bool) -> BookmarkEntry {
    BookmarkEntry {
        identity: BookmarkIdentity {
            logical_bookmark_id: id(&format!("bookmark-{index}")),
        },
        name: name.to_owned(),
        anchor: anchor(index * 2, index * 2 + 1),
        native_tag: BookmarkNativeTag::Bookmark,
        opaque_native_payload_sha256: A.to_owned(),
        opaque_properties: vec![OpaqueLinkProperty {
            namespace: "hp".to_owned(),
            name: format!("bookmark_{index}"),
            value_sha256: B.to_owned(),
        }],
        locked,
    }
}

fn native_pair(begin_control_id: u32, field_id: u32) -> HyperlinkNativePair {
    HyperlinkNativePair {
        begin_tag: HyperlinkNativeBeginTag::FieldBegin,
        end_tag: HyperlinkNativeEndTag::FieldEnd,
        field_type: HyperlinkFieldType::Hyperlink,
        semantic_binding: HyperlinkSemanticBinding::UnverifiedFieldParameters,
        end_begin_control_id_ref: begin_control_id,
        end_field_id: field_id,
        field_name_sha256: Some(A.to_owned()),
        editable: true,
        dirty: false,
        z_order: -1,
        parameters_sha256: B.to_owned(),
        sub_list_sha256: Some(C.to_owned()),
        meta_tag_sha256: None,
        opaque_begin_state_sha256: A.to_owned(),
        opaque_end_state_sha256: B.to_owned(),
    }
}

fn hyperlink(index: u32, target: HyperlinkTarget, locked: bool) -> HyperlinkEntry {
    HyperlinkEntry {
        identity: HyperlinkIdentity {
            logical_hyperlink_id: id(&format!("hyperlink-{index}")),
            begin_control_id: 100 + index,
            field_id: 200 + index,
        },
        anchor: anchor(20 + index * 2, 21 + index * 2),
        target,
        display_text_sha256: C.to_owned(),
        native_pair: native_pair(100 + index, 200 + index),
        opaque_native_payload_sha256: A.to_owned(),
        opaque_properties: vec![OpaqueLinkProperty {
            namespace: "hp".to_owned(),
            name: format!("hyperlink_{index}"),
            value_sha256: B.to_owned(),
        }],
        locked,
    }
}

fn policy(targets: &[HyperlinkTarget]) -> ExternalLinkPolicy {
    let mut approvals = targets
        .iter()
        .filter_map(|target| {
            Some(ExternalTargetApproval {
                kind: target.external_kind()?,
                target_sha256: target.external_approval_sha256(limits()).expect("approval"),
            })
        })
        .collect::<Vec<_>>();
    approvals.sort();
    ExternalLinkPolicy {
        allow_https: targets
            .iter()
            .any(|target| matches!(target, HyperlinkTarget::Https { .. })),
        allow_mailto: targets
            .iter()
            .any(|target| matches!(target, HyperlinkTarget::Mailto { .. })),
        allow_managed_documents: targets
            .iter()
            .any(|target| matches!(target, HyperlinkTarget::ManagedDocument { .. })),
        approvals,
        policy_revision_sha256: A.to_owned(),
    }
}

fn state(
    bookmarks: Vec<BookmarkEntry>,
    hyperlinks: Vec<HyperlinkEntry>,
    external_link_policy: ExternalLinkPolicy,
) -> Result<LinkReferenceDocumentState, LinkReferenceError> {
    state_with_occupied(
        bookmarks,
        hyperlinks,
        external_link_policy,
        Vec::new(),
        Vec::new(),
    )
}

fn state_with_occupied(
    bookmarks: Vec<BookmarkEntry>,
    hyperlinks: Vec<HyperlinkEntry>,
    external_link_policy: ExternalLinkPolicy,
    occupied_begin_control_ids: Vec<u32>,
    occupied_field_ids: Vec<u32>,
) -> Result<LinkReferenceDocumentState, LinkReferenceError> {
    LinkReferenceDocumentState::from_draft(
        LinkReferenceDocumentStateDraft {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
            sections: vec![section(false)],
            bookmarks,
            hyperlinks,
            occupied_non_hyperlink_begin_control_ids: occupied_begin_control_ids,
            occupied_non_hyperlink_field_ids: occupied_field_ids,
            external_link_policy,
            non_reference_content_sha256: A.to_owned(),
            unrelated_field_inventory_sha256: B.to_owned(),
            style_catalog_sha256: C.to_owned(),
            object_inventory_sha256: A.to_owned(),
            relationship_inventory_sha256: B.to_owned(),
            resource_inventory_sha256: C.to_owned(),
            document_protection_sha256: A.to_owned(),
            opaque_document_state_sha256: B.to_owned(),
            document_locked: false,
        },
        limits(),
    )
}

fn request(
    source: &LinkReferenceDocumentState,
    operation: LinkReferenceOperation,
) -> Result<LinkReferenceRequest, LinkReferenceError> {
    LinkReferenceRequest::from_draft(
        LinkReferenceRequestDraft {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
}

fn execute(
    source: &LinkReferenceDocumentState,
    operation: LinkReferenceOperation,
) -> Result<LinkReferenceDocumentState, LinkReferenceError> {
    let request = request(source, operation)?;
    let plan = LinkReferenceBuilder::plan(source, &request, FLOW_A, limits())?;
    Ok(LinkReferenceBuilder::build(&plan, source, FLOW_A, limits())?.state)
}

fn value(state: &LinkReferenceDocumentState) -> Value {
    serde_json::from_slice(&state.canonical_json(limits()).expect("json")).expect("value")
}

#[test]
fn schema_capabilities_native_shapes_and_external_digest_are_exact() {
    let operations = [
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: bookmark(1, "장-하나", false),
        },
        LinkReferenceOperation::DeleteBookmark {
            target: bookmark(1, "장-하나", false).identity,
        },
        LinkReferenceOperation::InsertHyperlink {
            insertion_index: 0,
            hyperlink: Box::new(hyperlink(
                1,
                HyperlinkTarget::InternalBookmark {
                    bookmark_id: id("bookmark-1"),
                },
                false,
            )),
        },
        LinkReferenceOperation::EditHyperlink {
            target: hyperlink(
                1,
                HyperlinkTarget::InternalBookmark {
                    bookmark_id: id("bookmark-1"),
                },
                false,
            )
            .identity,
            new_target: HyperlinkTarget::Https {
                uri: "https://example.test/reference".to_owned(),
            },
            new_display_text_sha256: A.to_owned(),
            new_parameters_sha256: C.to_owned(),
        },
    ];
    assert_eq!(
        operations.map(|operation| operation.capability_id()),
        [
            "ref.bookmark_insert",
            "ref.bookmark_delete",
            "ref.hyperlink_insert",
            "ref.hyperlink_edit",
        ]
    );
    assert_eq!(BookmarkNativeTag::Bookmark, BookmarkNativeTag::Bookmark);
    assert_eq!(HyperlinkFieldType::Hyperlink, HyperlinkFieldType::Hyperlink);

    let external = HyperlinkTarget::Https {
        uri: "https://example.test/reference".to_owned(),
    };
    assert_eq!(
        external.external_approval_sha256(limits()).expect("hash"),
        external.external_approval_sha256(limits()).expect("hash")
    );
    assert_eq!(
        HyperlinkTarget::InternalBookmark {
            bookmark_id: id("bookmark-1")
        }
        .external_approval_sha256(limits()),
        Err(LinkReferenceError::InvalidTarget)
    );
}

#[test]
fn bookmark_insert_and_unreferenced_delete_are_exact_and_preserving() {
    let source = state(Vec::new(), Vec::new(), policy(&[])).expect("state");
    let inserted = execute(
        &source,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: bookmark(1, "장-하나", false),
        },
    )
    .expect("insert");
    assert_eq!(inserted.bookmarks().len(), 1);
    assert_eq!(inserted.hyperlinks(), source.hyperlinks());
    let before = value(&source);
    let after = value(&inserted);
    for key in [
        "sections",
        "occupied_non_hyperlink_begin_control_ids",
        "occupied_non_hyperlink_field_ids",
        "external_link_policy",
        "non_reference_content_sha256",
        "unrelated_field_inventory_sha256",
        "style_catalog_sha256",
        "object_inventory_sha256",
        "relationship_inventory_sha256",
        "resource_inventory_sha256",
        "document_protection_sha256",
        "opaque_document_state_sha256",
        "document_locked",
    ] {
        assert_eq!(before[key], after[key], "preserved {key}");
    }

    let deleted = execute(
        &inserted,
        LinkReferenceOperation::DeleteBookmark {
            target: inserted.bookmarks()[0].identity.clone(),
        },
    )
    .expect("delete");
    assert_eq!(deleted, source);
}

#[test]
fn bookmark_delete_rejects_dangling_internal_hyperlink() {
    let target = HyperlinkTarget::InternalBookmark {
        bookmark_id: id("bookmark-1"),
    };
    let source = state(
        vec![bookmark(1, "chapter-one", false)],
        vec![hyperlink(1, target, false)],
        policy(&[]),
    )
    .expect("state");
    assert_eq!(
        request(
            &source,
            LinkReferenceOperation::DeleteBookmark {
                target: source.bookmarks()[0].identity.clone(),
            }
        ),
        Err(LinkReferenceError::DanglingReference)
    );
}

#[test]
fn inserts_internal_https_mailto_and_managed_document_targets() {
    let https = HyperlinkTarget::Https {
        uri: "https://example.test/a?x=1#part".to_owned(),
    };
    let mailto = HyperlinkTarget::Mailto {
        address: "person@example.test".to_owned(),
    };
    let managed = HyperlinkTarget::ManagedDocument {
        artifact_id: id("artifact-2"),
        bookmark_name: Some("장-둘".to_owned()),
    };
    let external_policy = policy(&[https.clone(), mailto.clone(), managed.clone()]);
    let mut current = state(
        vec![bookmark(1, "chapter-one", false)],
        Vec::new(),
        external_policy,
    )
    .expect("state");
    let targets = [
        HyperlinkTarget::InternalBookmark {
            bookmark_id: id("bookmark-1"),
        },
        https,
        mailto,
        managed,
    ];
    for (index, target) in targets.into_iter().enumerate() {
        current = execute(
            &current,
            LinkReferenceOperation::InsertHyperlink {
                insertion_index: index,
                hyperlink: Box::new(hyperlink(
                    u32::try_from(index + 1).expect("small fixture"),
                    target,
                    false,
                )),
            },
        )
        .expect("insert hyperlink");
    }
    assert_eq!(current.hyperlinks().len(), 4);
    assert_eq!(current.bookmarks().len(), 1);
}

#[test]
fn edit_changes_only_target_display_and_native_parameter_digest() {
    let old_target = HyperlinkTarget::InternalBookmark {
        bookmark_id: id("bookmark-1"),
    };
    let new_target = HyperlinkTarget::Https {
        uri: "https://example.test/updated".to_owned(),
    };
    let source = state(
        vec![bookmark(1, "chapter-one", false)],
        vec![hyperlink(1, old_target, false)],
        policy(std::slice::from_ref(&new_target)),
    )
    .expect("state");
    let before = source.hyperlinks()[0].clone();
    let after = execute(
        &source,
        LinkReferenceOperation::EditHyperlink {
            target: before.identity.clone(),
            new_target: new_target.clone(),
            new_display_text_sha256: A.to_owned(),
            new_parameters_sha256: C.to_owned(),
        },
    )
    .expect("edit");
    let changed = &after.hyperlinks()[0];
    assert_eq!(changed.target, new_target);
    assert_eq!(changed.display_text_sha256, A);
    assert_eq!(changed.native_pair.parameters_sha256, C);
    assert_eq!(changed.identity, before.identity);
    assert_eq!(changed.anchor, before.anchor);
    let mut preserved_native = before.native_pair;
    preserved_native.parameters_sha256 = C.to_owned();
    assert_eq!(changed.native_pair, preserved_native);
    assert_eq!(changed.opaque_properties, before.opaque_properties);
    assert_eq!(after.bookmarks(), source.bookmarks());
    assert_eq!(after.sections(), source.sections());
    assert_eq!(after.external_link_policy(), source.external_link_policy());
}

#[test]
fn unsafe_unapproved_and_malformed_external_targets_fail_closed() {
    let source = state(Vec::new(), Vec::new(), policy(&[])).expect("state");
    for invalid in [
        HyperlinkTarget::Https {
            uri: "http://example.test".to_owned(),
        },
        HyperlinkTarget::Https {
            uri: "https://user@example.test".to_owned(),
        },
        HyperlinkTarget::Https {
            uri: "https://example.test/a path".to_owned(),
        },
        HyperlinkTarget::Https {
            uri: "https://:".to_owned(),
        },
        HyperlinkTarget::Https {
            uri: "https://bad_host.test".to_owned(),
        },
        HyperlinkTarget::Https {
            uri: "https://example.test/%zz".to_owned(),
        },
        HyperlinkTarget::Mailto {
            address: "person@example".to_owned(),
        },
        HyperlinkTarget::Mailto {
            address: "mailto:person@example.test".to_owned(),
        },
        HyperlinkTarget::Mailto {
            address: ".person@example.test".to_owned(),
        },
        HyperlinkTarget::Mailto {
            address: "person@bad_domain.test".to_owned(),
        },
        HyperlinkTarget::ManagedDocument {
            artifact_id: id("folder/document.hwpx"),
            bookmark_name: None,
        },
    ] {
        assert_eq!(
            request(
                &source,
                LinkReferenceOperation::InsertHyperlink {
                    insertion_index: 0,
                    hyperlink: Box::new(hyperlink(1, invalid, false)),
                }
            ),
            Err(LinkReferenceError::InvalidTarget)
        );
    }

    let valid = HyperlinkTarget::Https {
        uri: "https://example.test/denied".to_owned(),
    };
    assert_eq!(
        request(
            &source,
            LinkReferenceOperation::InsertHyperlink {
                insertion_index: 0,
                hyperlink: Box::new(hyperlink(1, valid, false)),
            }
        ),
        Err(LinkReferenceError::ExternalTargetDenied)
    );
}

#[test]
fn duplicate_dangling_anchor_native_and_name_states_are_rejected() {
    assert_eq!(
        state(
            vec![bookmark(1, "same", false), bookmark(2, "same", false)],
            Vec::new(),
            policy(&[])
        ),
        Err(LinkReferenceError::InvalidBookmarkName)
    );
    let dangling = hyperlink(
        1,
        HyperlinkTarget::InternalBookmark {
            bookmark_id: id("bookmark-missing"),
        },
        false,
    );
    assert_eq!(
        state(Vec::new(), vec![dangling], policy(&[])),
        Err(LinkReferenceError::DanglingReference)
    );

    let mut bad_native = hyperlink(
        1,
        HyperlinkTarget::InternalBookmark {
            bookmark_id: id("bookmark-1"),
        },
        false,
    );
    bad_native.native_pair.end_field_id += 1;
    assert_eq!(
        state(
            vec![bookmark(1, "chapter-one", false)],
            vec![bad_native],
            policy(&[])
        ),
        Err(LinkReferenceError::InvalidNativeBinding)
    );

    let colliding = hyperlink(
        1,
        HyperlinkTarget::InternalBookmark {
            bookmark_id: id("bookmark-1"),
        },
        false,
    );
    assert_eq!(
        state_with_occupied(
            vec![bookmark(1, "chapter-one", false)],
            vec![colliding.clone()],
            policy(&[]),
            vec![101],
            Vec::new(),
        ),
        Err(LinkReferenceError::InvalidIdentity)
    );
    assert_eq!(
        state_with_occupied(
            vec![bookmark(1, "chapter-one", false)],
            vec![colliding],
            policy(&[]),
            Vec::new(),
            vec![201],
        ),
        Err(LinkReferenceError::InvalidIdentity)
    );
    assert_eq!(
        state_with_occupied(Vec::new(), Vec::new(), policy(&[]), vec![2, 1], Vec::new()),
        Err(LinkReferenceError::InvalidIdentity)
    );

    let mut bad_anchor = bookmark(1, "chapter-one", false);
    bad_anchor.anchor.end.paragraph_ordinal = 4;
    assert_eq!(
        state(vec![bad_anchor], Vec::new(), policy(&[])),
        Err(LinkReferenceError::InvalidIdentity)
    );

    let mut wrongly_qualified = hyperlink(
        1,
        HyperlinkTarget::InternalBookmark {
            bookmark_id: id("bookmark-1"),
        },
        false,
    );
    wrongly_qualified.native_pair.semantic_binding =
        HyperlinkSemanticBinding::Hangul2020HttpsCurrentTabV1;
    assert_eq!(
        state(
            vec![bookmark(1, "chapter-one", false)],
            vec![wrongly_qualified],
            policy(&[]),
        ),
        Err(LinkReferenceError::InvalidNativeBinding)
    );
}

#[test]
fn protection_index_and_noop_rules_have_no_partial_output() {
    let locked_bookmark = bookmark(1, "locked", true);
    let source = state(vec![locked_bookmark.clone()], Vec::new(), policy(&[])).expect("state");
    assert_eq!(
        request(
            &source,
            LinkReferenceOperation::DeleteBookmark {
                target: locked_bookmark.identity,
            }
        ),
        Err(LinkReferenceError::Protected)
    );
    assert_eq!(
        request(
            &source,
            LinkReferenceOperation::InsertBookmark {
                insertion_index: 2,
                bookmark: bookmark(2, "new", false),
            }
        ),
        Err(LinkReferenceError::InvalidInsertionIndex)
    );

    let target = HyperlinkTarget::InternalBookmark {
        bookmark_id: id("bookmark-1"),
    };
    let link_source = state(
        vec![bookmark(1, "chapter-one", false)],
        vec![hyperlink(1, target.clone(), false)],
        policy(&[]),
    )
    .expect("state");
    assert_eq!(
        request(
            &link_source,
            LinkReferenceOperation::EditHyperlink {
                target: link_source.hyperlinks()[0].identity.clone(),
                new_target: target,
                new_display_text_sha256: C.to_owned(),
                new_parameters_sha256: B.to_owned(),
            }
        ),
        Err(LinkReferenceError::Noop)
    );
}

#[test]
fn request_plan_and_build_recheck_exact_state_and_flow() {
    let source = state(Vec::new(), Vec::new(), policy(&[])).expect("state");
    let operation = LinkReferenceOperation::InsertBookmark {
        insertion_index: 0,
        bookmark: bookmark(1, "chapter-one", false),
    };
    assert_eq!(
        LinkReferenceRequest::from_draft(
            LinkReferenceRequestDraft {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
                request_id: id("request-1"),
                expected_source_state_sha256: B.to_owned(),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation: operation.clone(),
            },
            &source,
            FLOW_A,
            limits(),
        ),
        Err(LinkReferenceError::SourceStateDrift)
    );
    assert_eq!(
        LinkReferenceRequest::from_draft(
            LinkReferenceRequestDraft {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
                request_id: id("request-1"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation: operation.clone(),
            },
            &source,
            FLOW_B,
            limits(),
        ),
        Err(LinkReferenceError::DocumentFlowDrift)
    );
    let valid = request(&source, operation).expect("request");
    let plan = LinkReferenceBuilder::plan(&source, &valid, FLOW_A, limits()).expect("plan");
    assert_eq!(
        LinkReferenceBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(LinkReferenceError::DocumentFlowDrift)
    );
    let drifted = execute(
        &source,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: bookmark(2, "different", false),
        },
    )
    .expect("drifted");
    assert_eq!(
        LinkReferenceBuilder::build(&plan, &drifted, FLOW_A, limits()),
        Err(LinkReferenceError::SourceStateDrift)
    );
}

#[test]
fn strict_json_limits_errors_and_debug_output_are_bounded_and_redacted() {
    let source = state(Vec::new(), Vec::new(), policy(&[])).expect("state");
    let draft = LinkReferenceRequestDraft {
        schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: bookmark(1, "secret-bookmark-name", false),
        },
    };
    let bytes = serde_json::to_vec(&draft).expect("json");
    let duplicate = String::from_utf8(bytes.clone()).expect("utf8").replacen(
        "{\"schema_version\"",
        "{\"schema_version\":\"hwpx-agent.link-reference/v1\",\"schema_version\"",
        1,
    );
    assert_eq!(
        LinkReferenceRequest::from_json(duplicate.as_bytes(), &source, FLOW_A, limits()),
        Err(LinkReferenceError::InvalidJson)
    );
    let unknown =
        String::from_utf8(bytes.clone())
            .expect("utf8")
            .replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        LinkReferenceRequest::from_json(unknown.as_bytes(), &source, FLOW_A, limits()),
        Err(LinkReferenceError::InvalidJson)
    );
    let tiny = LinkReferenceLimits::new(LinkReferenceLimitConfig {
        input_bytes: 8,
        output_bytes: 1024,
        ..LinkReferenceLimitConfig::default()
    })
    .expect("tiny limits");
    assert_eq!(
        LinkReferenceRequest::from_json(&bytes, &source, FLOW_A, tiny),
        Err(LinkReferenceError::InputLimit)
    );

    let request = request(
        &source,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: bookmark(1, "secret-bookmark-name", false),
        },
    )
    .expect("request");
    let debug = format!("{request:?}");
    assert!(!debug.contains("secret-bookmark-name"));
    assert!(!debug.contains(A));
    assert!(!format!("{:?}", point(777, 888, 999)).contains("777"));
    assert_eq!(
        LinkReferenceError::ExternalTargetDenied.code(),
        "link_reference_external_target_denied"
    );
    assert!(format!("{source:?}").len() < 256);
}
