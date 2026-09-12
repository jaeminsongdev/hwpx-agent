#![allow(clippy::expect_used)]

use domain_ir::{
    BookmarkEntry, BookmarkIdentity, BookmarkNativeTag, ExternalLinkPolicy,
    LINK_REFERENCE_SCHEMA_VERSION, LinkAnchor, LinkPoint, LinkReferenceBuilder,
    LinkReferenceDocumentState, LinkReferenceDocumentStateDraft, LinkReferenceLimitConfig,
    LinkReferenceLimits, LinkReferenceOperation, LinkReferencePlan, LinkReferenceRequest,
    LinkReferenceRequestDraft, LinkReferenceSectionState, LogicalId,
};
use hwpx_package::{
    BookmarkHwpxBuilder, BookmarkHwpxError, BookmarkHwpxLimitConfig, BookmarkHwpxLimits,
    BookmarkHwpxLowerer, BookmarkHwpxReader,
};

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const EMPTY: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const FLOW_A: &str = A;
const FLOW_B: &str = B;

fn limits() -> LinkReferenceLimits {
    LinkReferenceLimits::new(LinkReferenceLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> BookmarkHwpxLimits {
    BookmarkHwpxLimits::new(BookmarkHwpxLimitConfig::default()).expect("HWPX limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("logical id")
}

fn point(inline_ordinal: u32) -> LinkPoint {
    LinkPoint {
        paragraph_ordinal: 0,
        run_ordinal: 0,
        inline_ordinal,
    }
}

fn bookmark(identity: &str, name: &str, inline_ordinal: u32) -> BookmarkEntry {
    let point = point(inline_ordinal);
    BookmarkEntry {
        identity: BookmarkIdentity {
            logical_bookmark_id: id(identity),
        },
        name: name.to_owned(),
        anchor: LinkAnchor {
            section_id: id("section-1"),
            start: point,
            end: point,
        },
        native_tag: BookmarkNativeTag::Bookmark,
        opaque_native_payload_sha256: EMPTY.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn state(bookmarks: Vec<BookmarkEntry>) -> LinkReferenceDocumentState {
    LinkReferenceDocumentState::from_draft(
        LinkReferenceDocumentStateDraft {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
            sections: vec![LinkReferenceSectionState {
                section_id: id("section-1"),
                paragraph_count: 1,
                run_topology_sha256: A.to_owned(),
                inline_topology_sha256: B.to_owned(),
                opaque_section_state_sha256: C.to_owned(),
                locked: false,
            }],
            bookmarks,
            hyperlinks: Vec::new(),
            occupied_non_hyperlink_begin_control_ids: Vec::new(),
            occupied_non_hyperlink_field_ids: Vec::new(),
            external_link_policy: ExternalLinkPolicy {
                allow_https: false,
                allow_mailto: false,
                allow_managed_documents: false,
                approvals: Vec::new(),
                policy_revision_sha256: A.to_owned(),
            },
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
    .expect("state")
}

fn domain_plan(
    source: &LinkReferenceDocumentState,
    operation: LinkReferenceOperation,
) -> LinkReferencePlan {
    let request = LinkReferenceRequest::from_draft(
        LinkReferenceRequestDraft {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-bookmark"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
    .expect("request");
    LinkReferenceBuilder::plan(source, &request, FLOW_A, limits()).expect("domain plan")
}

fn section(body: &str) -> Vec<u8> {
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<hp:sec xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\"><hp:p id=\"1\"><hp:run charPrIDRef=\"0\">{body}</hp:run></hp:p></hp:sec>"
    )
    .into_bytes()
}

#[test]
fn reads_exact_point_markers_and_preserves_order_and_boundaries() {
    let source = section(
        "<hp:t>A</hp:t><hp:ctrl><hp:bookmark name=\"first&amp;one\"/></hp:ctrl><hp:t>B</hp:t><hp:ctrl> <hp:bookmark name=\"second\"/> </hp:ctrl>",
    );
    let expected = state(vec![
        bookmark("bookmark-1", "first&one", 1),
        bookmark("bookmark-2", "second", 2),
    ]);
    let readback = BookmarkHwpxReader::read_section(&source, &expected, limits(), hwpx_limits())
        .expect("readback");
    assert_eq!(readback.bookmark_count, 2);
    assert_eq!(readback.bookmark_wrapper_sha256.len(), 2);
    assert_eq!(readback.state, expected);
    assert!(!format!("{readback:?}").contains("first&one"));
}

#[test]
fn ref_031_inserts_one_marker_at_exact_content_boundary() {
    let source = section("<hp:t>A</hp:t><!--keep--><hp:t>B</hp:t>");
    let source_state = state(Vec::new());
    let new_bookmark = bookmark("bookmark-new", "new&point", 1);
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: new_bookmark,
        },
    );
    let plan = BookmarkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    assert_eq!(
        plan.canonical_json(hwpx_limits()).expect("plan JSON"),
        plan.canonical_json(hwpx_limits()).expect("repeat JSON")
    );
    let (output, receipt) = BookmarkHwpxLowerer::lower_section_with_receipt(
        &source,
        &plan,
        &source_state,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("lowering");
    assert_eq!(receipt.inserted_bookmarks, 1);
    assert_eq!(receipt.deleted_bookmarks, 0);
    assert_eq!(receipt.target_document_flow_sha256, FLOW_B);
    assert_eq!(
        String::from_utf8(output).expect("UTF-8"),
        String::from_utf8(section(
            "<hp:t>A</hp:t><!--keep--><hp:ctrl><hp:bookmark name=\"new&amp;point\"/></hp:ctrl><hp:t>B</hp:t>"
        ))
        .expect("UTF-8")
    );
}

#[test]
fn ref_032_deletes_only_the_exact_wrapper() {
    let source = section(
        "PREFIX<hp:t>A</hp:t><hp:ctrl> <hp:bookmark name=\"remove\"/> </hp:ctrl><hp:t>B</hp:t>SUFFIX",
    );
    let removed = bookmark("bookmark-remove", "remove", 1);
    let source_state = state(vec![removed.clone()]);
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::DeleteBookmark {
            target: removed.identity,
        },
    );
    let plan = BookmarkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let output = BookmarkHwpxLowerer::lower_section(
        &source,
        &plan,
        &source_state,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("lowering");
    assert_eq!(
        String::from_utf8(output).expect("UTF-8"),
        String::from_utf8(section("PREFIX<hp:t>A</hp:t><hp:t>B</hp:t>SUFFIX")).expect("UTF-8")
    );
}

#[test]
fn same_boundary_insertion_respects_complete_bookmark_inventory_order() {
    let source =
        section("<hp:t>A</hp:t><hp:ctrl><hp:bookmark name=\"old\"/></hp:ctrl><hp:t>B</hp:t>");
    let old = bookmark("bookmark-old", "old", 1);
    let source_state = state(vec![old]);
    let new = bookmark("bookmark-new", "new", 1);
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: new,
        },
    );
    let plan = BookmarkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let output = BookmarkHwpxLowerer::lower_section(
        &source,
        &plan,
        &source_state,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("lowering");
    let text = String::from_utf8(output).expect("UTF-8");
    assert!(
        text.contains("<hp:bookmark name=\"new\"/></hp:ctrl><hp:ctrl><hp:bookmark name=\"old\"/>")
    );
}

#[test]
fn default_namespace_insertion_uses_the_source_lexical_form() {
    let source = br#"<?xml version="1.0" encoding="UTF-8"?>
<sec xmlns="http://www.hancom.co.kr/hwpml/2011/paragraph"><p id="1"><run charPrIDRef="0"><t>A</t></run></p></sec>"#
        .to_vec();
    let source_state = state(Vec::new());
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: bookmark("bookmark-default-ns", "point", 1),
        },
    );
    let plan = BookmarkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let output = BookmarkHwpxLowerer::lower_section(
        &source,
        &plan,
        &source_state,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("lowering");
    let text = String::from_utf8(output).expect("UTF-8");
    assert!(text.contains("<t>A</t><ctrl><bookmark name=\"point\"/></ctrl>"));
    assert!(!text.contains("hp:ctrl"));
}

#[test]
fn nonpoint_opaque_locked_and_out_of_range_bookmarks_fail_closed() {
    let source = section("<hp:t>A</hp:t><hp:t>B</hp:t>");
    let source_state = state(Vec::new());
    let mut invalid = bookmark("bookmark-invalid", "invalid", 1);
    invalid.anchor.end.inline_ordinal = 2;
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: invalid,
        },
    );
    assert!(matches!(
        BookmarkHwpxBuilder::plan(
            &source,
            &source_state,
            &domain,
            FLOW_A,
            limits(),
            hwpx_limits(),
        ),
        Err(BookmarkHwpxError::NonRepresentable)
    ));

    let mut locked = bookmark("bookmark-locked", "locked", 1);
    locked.locked = true;
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: locked,
        },
    );
    assert!(matches!(
        BookmarkHwpxBuilder::plan(
            &source,
            &source_state,
            &domain,
            FLOW_A,
            limits(),
            hwpx_limits(),
        ),
        Err(BookmarkHwpxError::NonRepresentable)
    ));

    let mut opaque = bookmark("bookmark-opaque", "opaque", 1);
    opaque.opaque_native_payload_sha256 = A.to_owned();
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: opaque,
        },
    );
    assert!(matches!(
        BookmarkHwpxBuilder::plan(
            &source,
            &source_state,
            &domain,
            FLOW_A,
            limits(),
            hwpx_limits(),
        ),
        Err(BookmarkHwpxError::NonRepresentable)
    ));

    let out_of_range = bookmark("bookmark-range", "range", 3);
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: out_of_range,
        },
    );
    let plan = BookmarkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("plan admits point before lowering");
    assert_eq!(
        BookmarkHwpxLowerer::lower_section(
            &source,
            &plan,
            &source_state,
            FLOW_A,
            limits(),
            hwpx_limits(),
        ),
        Err(BookmarkHwpxError::NonRepresentable)
    );
}

#[test]
fn malformed_structure_and_projection_mismatch_are_rejected() {
    let expected = state(vec![bookmark("bookmark-1", "one", 0)]);
    for source in [
        section("<hp:bookmark name=\"one\"/>"),
        section("<hp:ctrl bad=\"1\"><hp:bookmark name=\"one\"/></hp:ctrl>"),
        section("<hp:ctrl><hp:bookmark name=\"one\" bad=\"1\"/></hp:ctrl>"),
        section("<hp:ctrl><hp:bookmark name=\"other\"/></hp:ctrl>"),
    ] {
        assert!(
            BookmarkHwpxReader::read_section(&source, &expected, limits(), hwpx_limits(),).is_err()
        );
    }
}

#[test]
fn source_state_flow_plan_and_finite_limits_are_bound() {
    let source = section("<hp:t>A</hp:t><hp:t>B</hp:t>");
    let source_state = state(Vec::new());
    let domain = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertBookmark {
            insertion_index: 0,
            bookmark: bookmark("bookmark-new", "private-bookmark-value", 1),
        },
    );
    let plan = BookmarkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let mut drifted = source.clone();
    drifted.push(b' ');
    assert_eq!(
        BookmarkHwpxLowerer::lower_section(
            &drifted,
            &plan,
            &source_state,
            FLOW_A,
            limits(),
            hwpx_limits(),
        ),
        Err(BookmarkHwpxError::SourceDrift)
    );
    let drifted_state = state(vec![bookmark("bookmark-drift", "drift", 1)]);
    assert_eq!(
        BookmarkHwpxLowerer::lower_section(
            &source,
            &plan,
            &drifted_state,
            FLOW_A,
            limits(),
            hwpx_limits(),
        ),
        Err(BookmarkHwpxError::SourceDrift)
    );
    assert_eq!(
        BookmarkHwpxLowerer::lower_section(
            &source,
            &plan,
            &source_state,
            FLOW_B,
            limits(),
            hwpx_limits(),
        ),
        Err(BookmarkHwpxError::SourceDrift)
    );
    let tiny = BookmarkHwpxLimits::new(BookmarkHwpxLimitConfig {
        plan_bytes: 1,
        ..BookmarkHwpxLimitConfig::default()
    })
    .expect("finite limits");
    assert_eq!(
        plan.canonical_json(tiny),
        Err(BookmarkHwpxError::OutputLimit)
    );
    let debug = format!("{plan:?}");
    assert!(!debug.contains("private-bookmark-value"));
    assert!(!debug.contains(A));
    assert_eq!(
        BookmarkHwpxError::SourceDrift.code(),
        "bookmark_hwpx_source_drift"
    );
}
