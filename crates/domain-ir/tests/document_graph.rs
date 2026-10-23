use std::collections::BTreeMap;
use std::error::Error;
use std::fmt::Write as _;

use domain_ir::{
    ArtifactRef, BreakKind, BreakNode, ChartNode, DOCUMENT_GRAPH_SCHEMA_VERSION, DocumentGraph,
    DocumentGraphDraft, DocumentGraphError, DocumentGraphLimits, DocumentId, DrawingNode,
    EmbeddedObjectNode, EmbeddedObjectType, EquationNode, EquationSource, FieldNode, Flow,
    FormControlNode, Inline, LogicalId, Node, NodeCommon, Note, OpaqueExtension,
    OpaquePreservation, ParagraphNode, Properties, PropertyValue, Provenance, Reference, Resource,
    ResourceKind, ReviewEntry, Section, SourceAnchorHandle, Style, TableCell, TableNode,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn borrowed_views_and_streaming_digest_match_owned_canonical_bytes() -> TestResult {
    let graph = DocumentGraph::from_draft(complete_draft(false)?, DocumentGraphLimits::default())?;
    let draft = graph.clone().into_draft();
    assert_eq!(graph.notes(), draft.notes.as_slice());
    assert_eq!(graph.review_entries(), draft.review.as_slice());
    assert_eq!(graph.metadata(), &draft.metadata);
    assert_eq!(
        serde_json::to_vec(&(graph.sections(), graph.notes()))?,
        serde_json::to_vec(&(&draft.sections, &draft.notes))?,
    );
    let expected: [u8; 32] = Sha256::digest(graph.canonical_json()?).into();
    assert_eq!(graph.canonical_sha256()?, expected);
    // Cross several buffer boundaries with escaped/non-ASCII values; no omitted bytes.
    let mut large = complete_draft(false)?;
    large.metadata.insert(
        "streaming-test",
        PropertyValue::Text("한글\\\"\n".repeat(20_000)),
    );
    let large = DocumentGraph::from_draft(large, DocumentGraphLimits::default())?;
    let expected: [u8; 32] = Sha256::digest(large.canonical_json()?).into();
    assert_eq!(large.canonical_sha256()?, expected);
    Ok(())
}

#[test]
fn complete_graph_roundtrips_with_stable_golden_digest() -> TestResult {
    let graph = DocumentGraph::from_draft(complete_draft(false)?, DocumentGraphLimits::default())?;
    let first = graph.canonical_json()?;
    let value: serde_json::Value = serde_json::from_slice(&first)?;
    assert!(value.get("resource_catalog").is_some());
    assert!(value.get("style_catalog").is_some());
    assert!(value.get("resources").is_none());
    assert!(value.get("styles").is_none());
    assert!(value["resource_catalog"][0].get("artifact_ref").is_some());
    let reopened = DocumentGraph::from_json(&first, DocumentGraphLimits::default())?;
    let second = reopened.canonical_json()?;
    assert_eq!(first, second);
    assert_eq!(graph, reopened);
    assert_eq!(
        hex(&graph.canonical_sha256()?),
        "2ab9ffef0263e14609afa148e412ba2915820e54e365c9a420c734f908a6f3c6"
    );
    assert_eq!(reopened.sections().len(), 1);
    assert_eq!(reopened.resources().len(), 3);
    assert_eq!(reopened.styles().len(), 2);
    Ok(())
}

#[test]
fn catalog_insertion_order_is_canonical_but_document_order_is_preserved() -> TestResult {
    let normal = DocumentGraph::from_draft(complete_draft(false)?, DocumentGraphLimits::default())?;
    let reversed =
        DocumentGraph::from_draft(complete_draft(true)?, DocumentGraphLimits::default())?;
    assert_eq!(normal.canonical_json()?, reversed.canonical_json()?);
    Ok(())
}

#[test]
fn identifiers_versions_and_required_sections_fail_closed() -> TestResult {
    assert_eq!(
        DocumentId::parse("").map_err(DocumentGraphError::code),
        Err("document_graph_invalid_identifier")
    );
    assert_eq!(
        LogicalId::parse("node\n1").map_err(DocumentGraphError::code),
        Err("document_graph_invalid_identifier")
    );

    let mut wrong_version = complete_draft(false)?;
    wrong_version.schema_version = "hwpx-agent.document-graph/v3".to_owned();
    assert_eq!(
        DocumentGraph::from_draft(wrong_version, DocumentGraphLimits::default()),
        Err(DocumentGraphError::UnsupportedVersion)
    );

    let missing = DocumentGraphDraft::new(DocumentId::parse("doc-empty")?, Vec::new());
    assert_eq!(
        DocumentGraph::from_draft(missing, DocumentGraphLimits::default()),
        Err(DocumentGraphError::MissingSection)
    );
    Ok(())
}

#[test]
fn duplicate_and_dangling_ids_are_distinct_stable_errors() -> TestResult {
    let mut duplicate = complete_draft(false)?;
    duplicate.styles[0].style_id = duplicate.resources[0].resource_id.clone();
    assert_eq!(
        DocumentGraph::from_draft(duplicate, DocumentGraphLimits::default()),
        Err(DocumentGraphError::DuplicateIdentifier)
    );

    let mut dangling = complete_draft(false)?;
    dangling.sections[0].body.children[0]
        .common_mut_for_test()
        .style_refs = vec![id("missing-style")?];
    assert_eq!(
        DocumentGraph::from_draft(dangling, DocumentGraphLimits::default()),
        Err(DocumentGraphError::DanglingReference)
    );
    Ok(())
}

#[test]
fn table_shape_depth_and_count_limits_reject_without_partial_graph() -> TestResult {
    let mut bad_table = complete_draft(false)?;
    let Node::Table(table) = &mut bad_table.sections[0].body.children[1] else {
        return Err("expected table node".into());
    };
    table.cells[0].row_span = 0;
    assert_eq!(
        DocumentGraph::from_draft(bad_table, DocumentGraphLimits::default()),
        Err(DocumentGraphError::InvalidTableShape)
    );

    let mut overlapping_table = complete_draft(false)?;
    let Node::Table(table) = &mut overlapping_table.sections[0].body.children[1] else {
        return Err("expected table node".into());
    };
    table.columns = 2;
    table.cells[0].column_span = 2;
    let mut overlapping_cell = table.cells[0].clone();
    overlapping_cell.cell_id = id("cell-overlap")?;
    overlapping_cell.column = 1;
    overlapping_cell.column_span = 1;
    table.cells.push(overlapping_cell);
    assert_eq!(
        DocumentGraph::from_draft(overlapping_table, DocumentGraphLimits::default()),
        Err(DocumentGraphError::InvalidTableShape)
    );

    let small = DocumentGraphLimits {
        max_nodes: 1,
        ..DocumentGraphLimits::default()
    };
    assert_eq!(
        DocumentGraph::from_draft(complete_draft(false)?, small),
        Err(DocumentGraphError::LimitExceeded)
    );

    let invalid = DocumentGraphLimits {
        max_depth: 0,
        ..DocumentGraphLimits::default()
    };
    assert_eq!(
        DocumentGraph::from_draft(complete_draft(false)?, invalid),
        Err(DocumentGraphError::InvalidLimit)
    );

    let unsafe_depth = DocumentGraphLimits {
        max_depth: 257,
        ..DocumentGraphLimits::default()
    };
    assert_eq!(
        DocumentGraph::from_draft(complete_draft(false)?, unsafe_depth),
        Err(DocumentGraphError::InvalidLimit)
    );
    Ok(())
}

#[test]
fn json_boundary_rejects_unknown_fields_and_excessive_bytes() -> TestResult {
    let graph = DocumentGraph::from_draft(complete_draft(false)?, DocumentGraphLimits::default())?;
    let canonical = graph.canonical_json()?;
    let mut value: serde_json::Value = serde_json::from_slice(&canonical)?;
    value["unexpected"] = serde_json::Value::Bool(true);
    let unknown = serde_json::to_vec(&value)?;
    assert_eq!(
        DocumentGraph::from_json(&unknown, DocumentGraphLimits::default()),
        Err(DocumentGraphError::InvalidJson)
    );

    let mut invalid_id_value: serde_json::Value = serde_json::from_slice(&canonical)?;
    invalid_id_value["document_id"] = serde_json::Value::String(String::new());
    assert_eq!(
        DocumentGraph::from_json(
            &serde_json::to_vec(&invalid_id_value)?,
            DocumentGraphLimits::default()
        ),
        Err(DocumentGraphError::InvalidJson)
    );

    let limits = DocumentGraphLimits {
        max_serialized_bytes: canonical.len() - 1,
        ..DocumentGraphLimits::default()
    };
    assert_eq!(
        DocumentGraph::from_json(&canonical, limits),
        Err(DocumentGraphError::LimitExceeded)
    );
    assert_eq!(
        DocumentGraph::from_draft(complete_draft(false)?, limits),
        Err(DocumentGraphError::LimitExceeded)
    );
    Ok(())
}

#[test]
fn nested_limits_invalid_keys_and_source_anchor_collisions_fail_closed() -> TestResult {
    let inline_limits = DocumentGraphLimits {
        max_inlines: 1,
        ..DocumentGraphLimits::default()
    };
    assert_eq!(
        DocumentGraph::from_draft(complete_draft(false)?, inline_limits),
        Err(DocumentGraphError::LimitExceeded)
    );

    let edge_limits = DocumentGraphLimits {
        max_edges: 1,
        ..DocumentGraphLimits::default()
    };
    assert_eq!(
        DocumentGraph::from_draft(complete_draft(false)?, edge_limits),
        Err(DocumentGraphError::LimitExceeded)
    );

    let mut invalid_key = complete_draft(false)?;
    let mut nested = BTreeMap::new();
    nested.insert(String::new(), PropertyValue::Boolean(true));
    invalid_key
        .metadata
        .insert("nested", PropertyValue::Object(nested));
    assert_eq!(
        DocumentGraph::from_draft(invalid_key, DocumentGraphLimits::default()),
        Err(DocumentGraphError::InvalidValue)
    );

    let mut duplicate_anchor = complete_draft(false)?;
    let anchor = duplicate_anchor.sections[0].body.children[0]
        .common()
        .source_anchor
        .clone()
        .ok_or("expected source anchor")?;
    duplicate_anchor.sections[0].body.children[1]
        .common_mut_for_test()
        .source_anchor = Some(anchor);
    assert_eq!(
        DocumentGraph::from_draft(duplicate_anchor, DocumentGraphLimits::default()),
        Err(DocumentGraphError::DuplicateIdentifier)
    );

    let mut dangling_opaque = complete_draft(false)?;
    let Node::Equation(equation) = &mut dangling_opaque.sections[0].body.children[2] else {
        return Err("expected equation node".into());
    };
    equation.source = EquationSource::NativeOpaque(id("missing-opaque")?);
    assert_eq!(
        DocumentGraph::from_draft(dangling_opaque, DocumentGraphLimits::default()),
        Err(DocumentGraphError::DanglingReference)
    );

    let mut invalid_preservation = complete_draft(false)?;
    invalid_preservation.opaque_preservation_bag[0].preservation = OpaquePreservation::None;
    assert_eq!(
        DocumentGraph::from_draft(invalid_preservation, DocumentGraphLimits::default()),
        Err(DocumentGraphError::InvalidValue)
    );
    Ok(())
}

#[test]
fn debug_and_errors_do_not_expose_document_values_or_source_paths() -> TestResult {
    let secret_text = "private-body-sentinel";
    let secret_path = "C:/private/source.hwpx";
    let mut draft = complete_draft(false)?;
    draft
        .metadata
        .insert("source_path", PropertyValue::Text(secret_path.to_owned()));
    let Node::Paragraph(paragraph) = &mut draft.sections[0].body.children[0] else {
        return Err("expected paragraph node".into());
    };
    paragraph.inlines = vec![Inline::Text {
        text: secret_text.to_owned(),
    }];
    let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    let debug = format!("{graph:?}");
    assert!(!debug.contains(secret_text));
    assert!(!debug.contains(secret_path));
    assert!(!format!("{:?}", graph.into_draft()).contains(secret_text));
    assert!(
        !DocumentGraphError::InvalidJson
            .to_string()
            .contains(secret_text)
    );
    Ok(())
}

trait NodeTestMutation {
    fn common_mut_for_test(&mut self) -> &mut NodeCommon;
}

impl NodeTestMutation for Node {
    fn common_mut_for_test(&mut self) -> &mut NodeCommon {
        match self {
            Self::Paragraph(node) => &mut node.common,
            Self::Table(node) => &mut node.common,
            Self::Equation(node) => &mut node.common,
            Self::Drawing(node) => &mut node.common,
            Self::Chart(node) => &mut node.common,
            Self::Field(node) => &mut node.common,
            Self::FormControl(node) => &mut node.common,
            Self::Break(node) => &mut node.common,
            Self::EmbeddedObject(node) => &mut node.common,
        }
    }
}

#[allow(clippy::too_many_lines)]
fn complete_draft(reverse_catalogs: bool) -> Result<DocumentGraphDraft, DocumentGraphError> {
    let resource_image = Resource {
        resource_id: id("resource-image")?,
        kind: ResourceKind::Image,
        artifact: Some(ArtifactRef {
            sha256: [1; 32],
            byte_length: 128,
            media_type: "image/png".to_owned(),
        }),
        metadata: Properties::new(),
    };
    let resource_chart = Resource {
        resource_id: id("resource-chart")?,
        kind: ResourceKind::ChartData,
        artifact: Some(ArtifactRef {
            sha256: [2; 32],
            byte_length: 64,
            media_type: "application/json".to_owned(),
        }),
        metadata: Properties::new(),
    };
    let resource_ole = Resource {
        resource_id: id("resource-ole")?,
        kind: ResourceKind::Ole,
        artifact: None,
        metadata: Properties::new(),
    };
    let style_base = Style {
        style_id: id("style-base")?,
        based_on: None,
        properties: Properties::new(),
    };
    let style_body = Style {
        style_id: id("style-body")?,
        based_on: Some(id("style-base")?),
        properties: Properties::new(),
    };

    let paragraph = Node::Paragraph(ParagraphNode {
        common: common("node-paragraph", &["style-body"], &["resource-image"])?,
        inlines: vec![
            Inline::Text {
                text: "synthetic paragraph".to_owned(),
            },
            Inline::FieldRef {
                reference_id: id("reference-main")?,
            },
            Inline::ChangeSpan {
                review_id: id("review-main")?,
                children: vec![Inline::Text {
                    text: "reviewed".to_owned(),
                }],
            },
            Inline::ControlRef {
                node_id: id("node-form")?,
            },
        ],
        paragraph_properties: Properties::new(),
    });

    let table = Node::Table(TableNode {
        common: common("node-table", &[], &[])?,
        rows: 1,
        columns: 1,
        cells: vec![TableCell {
            cell_id: id("cell-main")?,
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 1,
            body: Flow {
                children: vec![Node::Paragraph(ParagraphNode {
                    common: common("node-cell-paragraph", &["style-body"], &[])?,
                    inlines: vec![Inline::Text {
                        text: "cell".to_owned(),
                    }],
                    paragraph_properties: Properties::new(),
                })],
            },
            properties: Properties::new(),
        }],
        properties: Properties::new(),
    });

    let equation = Node::Equation(EquationNode {
        common: common("node-equation", &[], &[])?,
        source: EquationSource::Formula("x + y".to_owned()),
        display: true,
        properties: Properties::new(),
    });
    let drawing = Node::Drawing(DrawingNode {
        common: common("node-drawing", &[], &["resource-image"])?,
        resource_id: Some(id("resource-image")?),
        children: Flow {
            children: vec![Node::Break(BreakNode {
                common: common("node-drawing-break", &[], &[])?,
                break_kind: BreakKind::Column,
            })],
        },
        properties: Properties::new(),
    });
    let chart = Node::Chart(ChartNode {
        common: common("node-chart", &[], &["resource-chart"])?,
        data_resource_id: id("resource-chart")?,
        properties: Properties::new(),
    });
    let field = Node::Field(FieldNode {
        common: common("node-field", &[], &[])?,
        reference_id: id("reference-main")?,
        properties: Properties::new(),
    });
    let form = Node::FormControl(FormControlNode {
        common: common("node-form", &[], &[])?,
        control_kind: "button".to_owned(),
        properties: Properties::new(),
    });
    let page_break = Node::Break(BreakNode {
        common: common("node-break", &[], &[])?,
        break_kind: BreakKind::Page,
    });
    let embedded = Node::EmbeddedObject(EmbeddedObjectNode {
        common: common("node-embedded", &[], &["resource-ole"])?,
        object_type: EmbeddedObjectType::Ole,
        resource_id: id("resource-ole")?,
        properties: Properties::new(),
    });

    let section = Section {
        section_id: id("section-main")?,
        properties: Properties::new(),
        master_pages: Vec::new(),
        headers_footers: Vec::new(),
        body: Flow {
            children: vec![
                paragraph, table, equation, drawing, chart, field, form, page_break, embedded,
            ],
        },
    };
    let mut draft = DocumentGraphDraft::new(DocumentId::parse("document-main")?, vec![section]);
    draft.source_profile = Some(id("profile-current-2020")?);
    draft
        .metadata
        .insert("title", PropertyValue::Text("Synthetic graph".to_owned()));
    draft
        .settings
        .insert("track_changes", PropertyValue::Boolean(false));
    draft.resources = vec![resource_image, resource_chart, resource_ole];
    draft.styles = vec![style_base, style_body];
    draft.notes = vec![Note {
        note_id: id("note-main")?,
        body: Flow {
            children: vec![Node::Paragraph(ParagraphNode {
                common: common("node-note-paragraph", &[], &[])?,
                inlines: vec![Inline::Text {
                    text: "note".to_owned(),
                }],
                paragraph_properties: Properties::new(),
            })],
        },
        properties: Properties::new(),
    }];
    draft.references = vec![Reference {
        reference_id: id("reference-main")?,
        target_node_id: Some(id("node-paragraph")?),
        properties: Properties::new(),
    }];
    draft.review = vec![ReviewEntry {
        review_id: id("review-main")?,
        target_node_id: id("node-paragraph")?,
        properties: Properties::new(),
    }];
    draft.opaque_preservation_bag = vec![OpaqueExtension {
        handle: id("opaque-main")?,
        sha256: [3; 32],
        byte_length: 32,
        preservation: OpaquePreservation::PreserveExact,
    }];
    if reverse_catalogs {
        draft.resources.reverse();
        draft.styles.reverse();
    }
    Ok(draft)
}

fn common(
    value: &str,
    style_refs: &[&str],
    resource_refs: &[&str],
) -> Result<NodeCommon, DocumentGraphError> {
    let mut common = NodeCommon::new(id(value)?);
    common.style_refs = style_refs
        .iter()
        .map(|value| id(value))
        .collect::<Result<Vec<_>, _>>()?;
    common.resource_refs = resource_refs
        .iter()
        .map(|value| id(value))
        .collect::<Result<Vec<_>, _>>()?;
    common.source_anchor = Some(SourceAnchorHandle {
        opaque_handle: id(&format!("anchor-{value}"))?,
        fingerprint_sha256: [4; 32],
    });
    common.provenance = Provenance::Imported;
    common.preserve = OpaquePreservation::PreserveUnknown;
    Ok(common)
}

fn id(value: &str) -> Result<LogicalId, DocumentGraphError> {
    LogicalId::parse(value)
}

fn hex(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}

#[test]
fn schema_version_constant_is_exact() {
    assert_eq!(
        DOCUMENT_GRAPH_SCHEMA_VERSION,
        "hwpx-agent.document-graph/v2"
    );
}

#[test]
fn immutable_digest_memo_keeps_canonical_bytes_and_warm_cold_equality() -> TestResult {
    let draft = complete_draft(false)?;
    let warm = DocumentGraph::from_draft(draft.clone(), DocumentGraphLimits::default())?;
    let cold = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    let bytes = warm.canonical_json()?;
    let debug = format!("{warm:?}");
    let expected: [u8; 32] = Sha256::digest(&bytes).into();
    for _ in 0..16 {
        assert_eq!(warm.canonical_sha256()?, expected);
        assert_eq!(warm, cold);
        assert_eq!(serde_json::to_vec(&warm)?, bytes);
        assert_eq!(warm.canonical_json()?, bytes);
        assert_eq!(format!("{warm:?}"), debug);
    }
    Ok(())
}

#[test]
fn digest_memo_clone_and_reopened_graph_have_the_same_original_digest() -> TestResult {
    let graph = DocumentGraph::from_draft(complete_draft(false)?, DocumentGraphLimits::default())?;
    let before = graph.clone();
    let expected = graph.canonical_sha256()?;
    let after = graph.clone();
    let reopened = DocumentGraph::from_json(&graph.canonical_json()?, DocumentGraphLimits::default())?;
    for candidate in [before, after, reopened] {
        assert_eq!(candidate, graph);
        assert_eq!(candidate.canonical_sha256()?, expected);
        assert_eq!(candidate.canonical_json()?, graph.canonical_json()?);
    }
    Ok(())
}

#[test]
fn changed_draft_does_not_reuse_the_previous_immutable_digest() -> TestResult {
    let original = DocumentGraph::from_draft(complete_draft(false)?, DocumentGraphLimits::default())?;
    let previous = original.canonical_sha256()?;
    let mut changed = original.clone().into_draft();
    changed.metadata.insert("digest-memo-fixture", PropertyValue::Text("changed".to_owned()));
    let changed = DocumentGraph::from_draft(changed, DocumentGraphLimits::default())?;
    let expected: [u8; 32] = Sha256::digest(changed.canonical_json()?).into();
    assert_ne!(changed, original);
    assert_ne!(expected, previous);
    assert_eq!(changed.canonical_sha256()?, expected);
    assert_eq!(original.canonical_sha256()?, previous);
    Ok(())
}

#[test]
fn digest_memo_does_not_bypass_new_draft_serialized_size_admission() -> TestResult {
    let graph = DocumentGraph::from_draft(complete_draft(false)?, DocumentGraphLimits::default())?;
    let _ = graph.canonical_sha256()?;
    let limits = DocumentGraphLimits { max_serialized_bytes: 1, ..DocumentGraphLimits::default() };
    assert!(DocumentGraph::from_draft(graph.into_draft(), limits).is_err());
    Ok(())
}

#[test]
fn concurrent_immutable_digest_first_reads_return_identical_whole_bytes() -> TestResult {
    let graph = DocumentGraph::from_draft(complete_draft(false)?, DocumentGraphLimits::default())?;
    let expected: [u8; 32] = Sha256::digest(graph.canonical_json()?).into();
    std::thread::scope(|scope| {
        let first = scope.spawn(|| graph.canonical_sha256());
        let second = scope.spawn(|| graph.canonical_sha256());
        assert_eq!(first.join().expect("owned digest reader")?, expected);
        assert_eq!(second.join().expect("owned digest reader")?, expected);
        Ok::<(), DocumentGraphError>(())
    })?;
    assert_eq!(graph.canonical_sha256()?, expected);
    Ok(())
}
