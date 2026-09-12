#![allow(clippy::expect_used)]

use domain_ir::{
    ExternalLinkPolicy, ExternalTargetApproval, HyperlinkEntry, HyperlinkFieldType,
    HyperlinkIdentity, HyperlinkNativeBeginTag, HyperlinkNativeEndTag, HyperlinkNativePair,
    HyperlinkSemanticBinding, HyperlinkTarget, LINK_REFERENCE_SCHEMA_VERSION, LinkAnchor,
    LinkPoint, LinkReferenceBuilder, LinkReferenceDocumentState, LinkReferenceDocumentStateDraft,
    LinkReferenceLimitConfig, LinkReferenceLimits, LinkReferenceOperation, LinkReferencePlan,
    LinkReferenceRequest, LinkReferenceRequestDraft, LinkReferenceSectionState, LogicalId,
};
use hwpx_package::{
    HYPERLINK_HWPX_PROFILE_ID, HyperlinkHwpxBuilder, HyperlinkHwpxError, HyperlinkHwpxLimitConfig,
    HyperlinkHwpxLimits, HyperlinkHwpxLowerer, HyperlinkHwpxReader,
};
use sha2::{Digest as _, Sha256};

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const FLOW_A: &str = A;
const FLOW_B: &str = B;
const EMPTY: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const DISPLAY: &str = "P09-HYPERLINK-DISCOVERY";

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("logical id")
}

fn state_limits() -> LinkReferenceLimits {
    LinkReferenceLimits::new(LinkReferenceLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> HyperlinkHwpxLimits {
    HyperlinkHwpxLimits::new(HyperlinkHwpxLimitConfig::default()).expect("HWPX limits")
}

fn sha(value: &str) -> String {
    let bytes: [u8; 32] = Sha256::digest(value.as_bytes()).into();
    let mut output = String::with_capacity(64);
    for byte in bytes {
        use std::fmt::Write as _;
        write!(output, "{byte:02x}").expect("write to string");
    }
    output
}

fn approvals(targets: &[HyperlinkTarget]) -> ExternalLinkPolicy {
    let limits = state_limits();
    let mut values = targets
        .iter()
        .map(|target| ExternalTargetApproval {
            kind: target.external_kind().expect("external target"),
            target_sha256: target
                .external_approval_sha256(limits)
                .expect("approval digest"),
        })
        .collect::<Vec<_>>();
    values.sort();
    ExternalLinkPolicy {
        allow_https: true,
        allow_mailto: false,
        allow_managed_documents: false,
        approvals: values,
        policy_revision_sha256: A.to_owned(),
    }
}

fn state(
    hyperlinks: Vec<HyperlinkEntry>,
    targets: &[HyperlinkTarget],
) -> LinkReferenceDocumentState {
    LinkReferenceDocumentState::from_draft(
        LinkReferenceDocumentStateDraft {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
            sections: vec![LinkReferenceSectionState {
                section_id: id("section-1"),
                paragraph_count: 1,
                run_topology_sha256: A.to_owned(),
                inline_topology_sha256: B.to_owned(),
                opaque_section_state_sha256: A.to_owned(),
                locked: false,
            }],
            bookmarks: Vec::new(),
            hyperlinks,
            occupied_non_hyperlink_begin_control_ids: vec![900],
            occupied_non_hyperlink_field_ids: vec![901],
            external_link_policy: approvals(targets),
            non_reference_content_sha256: A.to_owned(),
            unrelated_field_inventory_sha256: B.to_owned(),
            style_catalog_sha256: A.to_owned(),
            object_inventory_sha256: B.to_owned(),
            relationship_inventory_sha256: A.to_owned(),
            resource_inventory_sha256: B.to_owned(),
            document_protection_sha256: A.to_owned(),
            opaque_document_state_sha256: B.to_owned(),
            document_locked: false,
        },
        state_limits(),
    )
    .expect("state")
}

fn hyperlink(target: HyperlinkTarget, begin: u32, field: u32) -> HyperlinkEntry {
    HyperlinkEntry {
        identity: HyperlinkIdentity {
            logical_hyperlink_id: id("hyperlink-1"),
            begin_control_id: begin,
            field_id: field,
        },
        anchor: LinkAnchor {
            section_id: id("section-1"),
            start: LinkPoint {
                paragraph_ordinal: 0,
                run_ordinal: 0,
                inline_ordinal: 0,
            },
            end: LinkPoint {
                paragraph_ordinal: 0,
                run_ordinal: 0,
                inline_ordinal: 1,
            },
        },
        display_text_sha256: sha(DISPLAY),
        native_pair: HyperlinkNativePair {
            begin_tag: HyperlinkNativeBeginTag::FieldBegin,
            end_tag: HyperlinkNativeEndTag::FieldEnd,
            field_type: HyperlinkFieldType::Hyperlink,
            semantic_binding: HyperlinkSemanticBinding::Hangul2020HttpsCurrentTabV1,
            end_begin_control_id_ref: begin,
            end_field_id: field,
            field_name_sha256: Some(EMPTY.to_owned()),
            editable: false,
            dirty: true,
            z_order: -1,
            parameters_sha256: HyperlinkHwpxReader::parameters_sha256(
                &target,
                state_limits(),
                hwpx_limits(),
            )
            .expect("parameters digest"),
            sub_list_sha256: None,
            meta_tag_sha256: None,
            opaque_begin_state_sha256: EMPTY.to_owned(),
            opaque_end_state_sha256: EMPTY.to_owned(),
        },
        target,
        opaque_native_payload_sha256: EMPTY.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn source() -> Vec<u8> {
    format!(
        "<hp:sec xmlns:hp=\"{NS}\"><hp:p id=\"7\"><hp:run charPrIDRef=\"7\"><hp:t>{DISPLAY}</hp:t></hp:run><hp:linesegarray/></hp:p></hp:sec>"
    )
    .into_bytes()
}

fn domain_plan(
    source: &LinkReferenceDocumentState,
    operation: LinkReferenceOperation,
) -> LinkReferencePlan {
    let request = LinkReferenceRequest::from_draft(
        LinkReferenceRequestDraft {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        state_limits(),
    )
    .expect("request");
    LinkReferenceBuilder::plan(source, &request, FLOW_A, state_limits()).expect("domain plan")
}

fn insert_fixture(
    approved_targets: &[HyperlinkTarget],
    target: HyperlinkTarget,
) -> (Vec<u8>, LinkReferenceDocumentState, LinkReferencePlan) {
    let source_state = state(Vec::new(), approved_targets);
    let entry = hyperlink(target, 1_192_847_399, 627_600_491);
    let plan = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertHyperlink {
            insertion_index: 0,
            hyperlink: Box::new(entry),
        },
    );
    (source(), source_state, plan)
}

fn expected_parameters(uri: &str) -> String {
    let suffix = uri.strip_prefix("https://").expect("https");
    format!(
        "<hp:parameters cnt=\"6\" name=\"\"><hp:integerParam name=\"Prop\">0</hp:integerParam><hp:stringParam name=\"Command\">https\\://{suffix};1;0;0;</hp:stringParam><hp:stringParam name=\"Path\">{uri}</hp:stringParam><hp:stringParam name=\"Category\">HWPHYPERLINK_TYPE_URL</hp:stringParam><hp:stringParam name=\"TargetType\">HWPHYPERLINK_TARGET_BOOKMARK</hp:stringParam><hp:stringParam name=\"DocOpenType\">HWPHYPERLINK_JUMP_CURRENTTAB</hp:stringParam></hp:parameters>"
    )
}

#[test]
fn insert_emits_exact_discovered_hangul_2020_https_field_and_reads_back() {
    let target = HyperlinkTarget::Https {
        uri: "https://example.com/p09".to_owned(),
    };
    let (source, source_state, domain) =
        insert_fixture(std::slice::from_ref(&target), target.clone());
    let adapter = HyperlinkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("adapter plan");
    let (output, receipt) = HyperlinkHwpxLowerer::lower_section_with_receipt(
        &source,
        &adapter,
        &source_state,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    let text = String::from_utf8(output.clone()).expect("UTF-8");
    let exact = format!(
        "<hp:run charPrIDRef=\"0\"><hp:ctrl><hp:fieldBegin id=\"1192847399\" type=\"HYPERLINK\" name=\"\" editable=\"0\" dirty=\"1\" zorder=\"-1\" fieldid=\"627600491\">{}</hp:fieldBegin></hp:ctrl></hp:run><hp:run charPrIDRef=\"7\"><hp:t>{DISPLAY}</hp:t></hp:run><hp:run charPrIDRef=\"0\"><hp:ctrl><hp:fieldEnd beginIDRef=\"1192847399\" fieldid=\"627600491\"/></hp:ctrl><hp:t/></hp:run>",
        expected_parameters("https://example.com/p09")
    );
    assert!(text.contains(&exact));
    assert_eq!(receipt.profile_id, HYPERLINK_HWPX_PROFILE_ID);
    assert_eq!(receipt.capability_id, "ref.hyperlink_insert");
    assert_eq!(receipt.inserted_hyperlinks, 1);
    assert_eq!(receipt.edited_hyperlinks, 0);
    let readback = HyperlinkHwpxReader::read_section(
        &output,
        domain.target_state(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("readback");
    assert_eq!(readback.hyperlink_count, 1);
    assert_eq!(readback.state, *domain.target_state());
}

#[test]
fn target_edit_replaces_only_parameters_and_preserves_display_bytes() {
    let old_target = HyperlinkTarget::Https {
        uri: "https://example.com/old".to_owned(),
    };
    let new_target = HyperlinkTarget::Https {
        uri: "https://example.com/new".to_owned(),
    };
    let approved = [old_target.clone(), new_target.clone()];
    let (source, empty_state, insert) = insert_fixture(&approved, old_target);
    let insert_adapter = HyperlinkHwpxBuilder::plan(
        &source,
        &empty_state,
        &insert,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("insert adapter");
    let inserted = HyperlinkHwpxLowerer::lower_section(
        &source,
        &insert_adapter,
        &empty_state,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("insert");
    let current = insert.target_state().clone();
    let edit = domain_plan(
        &current,
        LinkReferenceOperation::EditHyperlink {
            target: current.hyperlinks()[0].identity.clone(),
            new_target: new_target.clone(),
            new_display_text_sha256: sha(DISPLAY),
            new_parameters_sha256: HyperlinkHwpxReader::parameters_sha256(
                &new_target,
                state_limits(),
                hwpx_limits(),
            )
            .expect("new parameters"),
        },
    );
    let adapter = HyperlinkHwpxBuilder::plan(
        &inserted,
        &current,
        &edit,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("edit adapter");
    let (output, receipt) = HyperlinkHwpxLowerer::lower_section_with_receipt(
        &inserted,
        &adapter,
        &current,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("edit");
    let old_parameters = expected_parameters("https://example.com/old");
    let new_parameters = expected_parameters("https://example.com/new");
    let expected = String::from_utf8(inserted.clone())
        .expect("UTF-8")
        .replacen(&old_parameters, &new_parameters, 1)
        .into_bytes();
    assert_eq!(output, expected);
    assert_eq!(receipt.inserted_hyperlinks, 0);
    assert_eq!(receipt.edited_hyperlinks, 1);
    assert_eq!(receipt.capability_id, "ref.hyperlink_edit");
}

#[test]
fn exact_discovery_fragment_is_admitted_without_promoting_target_execution() {
    let target = HyperlinkTarget::Https {
        uri: "https://example.com/p09".to_owned(),
    };
    let entry = hyperlink(target.clone(), 1_192_847_399, 627_600_491);
    let expected_state = state(vec![entry], std::slice::from_ref(&target));
    let xml = format!(
        "<hp:sec xmlns:hp=\"{NS}\"><hp:p><hp:run charPrIDRef=\"0\"><hp:ctrl><hp:fieldBegin id=\"1192847399\" type=\"HYPERLINK\" name=\"\" editable=\"0\" dirty=\"1\" zorder=\"-1\" fieldid=\"627600491\">{}</hp:fieldBegin></hp:ctrl></hp:run><hp:run charPrIDRef=\"7\"><hp:t>{DISPLAY}</hp:t></hp:run><hp:run charPrIDRef=\"0\"><hp:ctrl><hp:fieldEnd beginIDRef=\"1192847399\" fieldid=\"627600491\"/></hp:ctrl><hp:t/></hp:run></hp:p></hp:sec>",
        expected_parameters("https://example.com/p09")
    );
    let readback = HyperlinkHwpxReader::read_section(
        xml.as_bytes(),
        &expected_state,
        state_limits(),
        hwpx_limits(),
    )
    .expect("discovery readback");
    assert_eq!(readback.hyperlink_count, 1);
}

#[test]
fn https_query_escaping_and_zero_character_style_round_trip_exactly() {
    let target = HyperlinkTarget::Https {
        uri: "https://example.com/p09?a=1&b=2".to_owned(),
    };
    let (mut source, source_state, domain) =
        insert_fixture(std::slice::from_ref(&target), target.clone());
    source = String::from_utf8(source)
        .expect("UTF-8")
        .replacen("charPrIDRef=\"7\"", "charPrIDRef=\"0\"", 1)
        .into_bytes();
    let adapter = HyperlinkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("adapter");
    let output = HyperlinkHwpxLowerer::lower_section(
        &source,
        &adapter,
        &source_state,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    let text = String::from_utf8(output).expect("UTF-8");
    assert!(text.contains("https://example.com/p09?a=1&amp;b=2"));
    assert!(text.contains("https\\://example.com/p09?a=1&amp;b=2;1;0;0;"));
}

#[test]
fn unverified_profile_and_display_edit_fail_closed() {
    let old_target = HyperlinkTarget::Https {
        uri: "https://example.com/old".to_owned(),
    };
    let new_target = HyperlinkTarget::Https {
        uri: "https://example.com/new".to_owned(),
    };
    let approved = [old_target.clone(), new_target.clone()];
    let source_state = state(Vec::new(), &approved);
    let source = source();
    let mut unverified = hyperlink(old_target.clone(), 1_192_847_399, 627_600_491);
    unverified.native_pair.semantic_binding = HyperlinkSemanticBinding::UnverifiedFieldParameters;
    let insert = domain_plan(
        &source_state,
        LinkReferenceOperation::InsertHyperlink {
            insertion_index: 0,
            hyperlink: Box::new(unverified),
        },
    );
    assert!(matches!(
        HyperlinkHwpxBuilder::plan(
            &source,
            &source_state,
            &insert,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(HyperlinkHwpxError::NonRepresentable)
    ));

    let (source, source_state, insert) = insert_fixture(&approved, old_target);
    let adapter = HyperlinkHwpxBuilder::plan(
        &source,
        &source_state,
        &insert,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("insert adapter");
    let inserted = HyperlinkHwpxLowerer::lower_section(
        &source,
        &adapter,
        &source_state,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("insert");
    let current = insert.target_state().clone();
    let edit = domain_plan(
        &current,
        LinkReferenceOperation::EditHyperlink {
            target: current.hyperlinks()[0].identity.clone(),
            new_target: new_target.clone(),
            new_display_text_sha256: sha("changed display"),
            new_parameters_sha256: HyperlinkHwpxReader::parameters_sha256(
                &new_target,
                state_limits(),
                hwpx_limits(),
            )
            .expect("parameters"),
        },
    );
    assert!(matches!(
        HyperlinkHwpxBuilder::plan(
            &inserted,
            &current,
            &edit,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(HyperlinkHwpxError::NonRepresentable)
    ));
}

#[test]
fn malformed_parameter_order_value_comment_and_stray_text_are_rejected() {
    let target = HyperlinkTarget::Https {
        uri: "https://example.com/p09".to_owned(),
    };
    let (source, source_state, domain) =
        insert_fixture(std::slice::from_ref(&target), target.clone());
    let adapter = HyperlinkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("adapter");
    let output = HyperlinkHwpxLowerer::lower_section(
        &source,
        &adapter,
        &source_state,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("output");
    let valid = String::from_utf8(output).expect("UTF-8");
    let bad = [
        valid.replacen("HWPHYPERLINK_TYPE_URL", "HWPHYPERLINK_TYPE_FILE", 1),
        valid.replacen(
            "<hp:parameters cnt=\"6\" name=\"\">",
            "<hp:parameters cnt=\"6\" name=\"\"><!--bad-->",
            1,
        ),
        valid.replacen(
            "<hp:parameters cnt=\"6\" name=\"\">",
            "<hp:parameters cnt=\"6\" name=\"\">stray",
            1,
        ),
        valid.replacen("name=\"Prop\"", "name=\"Path\"", 1),
    ];
    for malformed in bad {
        assert_eq!(
            HyperlinkHwpxReader::read_section(
                malformed.as_bytes(),
                domain.target_state(),
                state_limits(),
                hwpx_limits(),
            ),
            Err(HyperlinkHwpxError::InvalidHyperlink)
        );
    }
}

#[test]
fn request_and_lowering_recheck_exact_section_state_and_flow() {
    let target = HyperlinkTarget::Https {
        uri: "https://example.com/p09".to_owned(),
    };
    let (source, source_state, domain) =
        insert_fixture(std::slice::from_ref(&target), target.clone());
    assert!(matches!(
        HyperlinkHwpxBuilder::plan(
            &source,
            &source_state,
            &domain,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        ),
        Err(HyperlinkHwpxError::NonRepresentable)
    ));
    let adapter = HyperlinkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("adapter");
    let mut drifted = source.clone();
    drifted.push(b' ');
    assert_eq!(
        HyperlinkHwpxLowerer::lower_section(
            &drifted,
            &adapter,
            &source_state,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(HyperlinkHwpxError::SourceDrift)
    );
    assert_eq!(
        HyperlinkHwpxLowerer::lower_section(
            &source,
            &adapter,
            &source_state,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        ),
        Err(HyperlinkHwpxError::SourceDrift)
    );
}

#[test]
fn finite_limits_and_redacted_debug_are_stable() {
    assert_eq!(
        HyperlinkHwpxLimits::new(HyperlinkHwpxLimitConfig {
            text_bytes: 0,
            ..HyperlinkHwpxLimitConfig::default()
        }),
        Err(HyperlinkHwpxError::InvalidLimit)
    );
    let target = HyperlinkTarget::Https {
        uri: "https://example.com/sensitive".to_owned(),
    };
    let (source, source_state, domain) =
        insert_fixture(std::slice::from_ref(&target), target.clone());
    let tiny = HyperlinkHwpxLimits::new(HyperlinkHwpxLimitConfig {
        section_bytes: source.len() - 1,
        ..HyperlinkHwpxLimitConfig::default()
    })
    .expect("tiny limits");
    assert!(matches!(
        HyperlinkHwpxBuilder::plan(
            &source,
            &source_state,
            &domain,
            FLOW_A,
            state_limits(),
            tiny,
        ),
        Err(HyperlinkHwpxError::InputLimit)
    ));
    let adapter = HyperlinkHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("adapter");
    let debug = format!("{adapter:?}");
    assert!(!debug.contains("example.com"));
    assert!(!debug.contains(DISPLAY));
    assert!(debug.len() < 256);
    assert_eq!(
        HyperlinkHwpxError::ProjectionMismatch.code(),
        "hyperlink_hwpx_projection_mismatch"
    );
}
