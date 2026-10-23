//! Pure preparation tests on exact historical packages; full graphs are caller/test supplied.
use super::*;
use hwpx_agent_cli::form_value_operation::full_document::*;

fn full_graph(operation: &PreparedFormOperation) -> Result<DocumentGraph, Box<dyn Error>> {
    let nodes = operation.selection_projection().sections()[0]
        .body
        .children
        .clone();
    let paragraph = Node::Paragraph(ParagraphNode {
        common: NodeCommon::new(LogicalId::parse("preserved-paragraph")?),
        inlines: vec![Inline::Text {
            text: "preserved private paragraph 🚀".into(),
        }],
        paragraph_properties: Properties::new(),
    });
    let drawing = Node::Drawing(DrawingNode {
        common: NodeCommon::new(LogicalId::parse("preserved-drawing")?),
        resource_id: None,
        children: Flow {
            children: nodes[..2].to_vec(),
        },
        properties: Properties::new(),
    });
    let table = Node::Table(TableNode {
        common: NodeCommon::new(LogicalId::parse("preserved-table")?),
        rows: 1,
        columns: 1,
        cells: vec![TableCell {
            cell_id: LogicalId::parse("preserved-cell")?,
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 1,
            body: Flow {
                children: vec![drawing, nodes[2].clone()],
            },
            properties: Properties::new(),
        }],
        properties: Properties::new(),
    });
    let mut draft = DocumentGraphDraft::new(
        operation.selection_projection().document_id().clone(),
        vec![
            Section {
                section_id: LogicalId::parse("full-section0")?,
                properties: Properties::new(),
                master_pages: vec![],
                headers_footers: vec![],
                body: Flow {
                    children: vec![paragraph, table],
                },
            },
            Section {
                section_id: LogicalId::parse("full-section1")?,
                properties: Properties::new(),
                master_pages: vec![],
                headers_footers: vec![],
                body: Flow {
                    children: nodes[3..5].to_vec(),
                },
            },
        ],
    );
    draft.notes.push(Note {
        note_id: LogicalId::parse("preserved-note")?,
        body: Flow {
            children: vec![nodes[5].clone()],
        },
        properties: Properties::new(),
    });
    draft.source_profile = Some(LogicalId::parse(
        "caller-full-graph-test-not-import-evidence",
    )?);
    draft.metadata.insert(
        "keep_metadata",
        PropertyValue::Text("metadata sentinel".into()),
    );
    draft
        .settings
        .insert("keep_settings", PropertyValue::Integer(7));
    draft
        .security_state
        .properties
        .insert("keep_policy", PropertyValue::Boolean(true));
    draft.accessibility.language = Some("ko-KR".into());
    add_catalogs(&mut draft)?;
    draft.references.push(Reference {
        reference_id: LogicalId::parse("keep-reference")?,
        target_node_id: Some(LogicalId::parse("preserved-paragraph")?),
        properties: Properties::new(),
    });
    draft.review.push(ReviewEntry {
        review_id: LogicalId::parse("keep-review")?,
        target_node_id: LogicalId::parse("preserved-paragraph")?,
        properties: Properties::new(),
    });
    Ok(DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits::default(),
    )?)
}

fn add_catalogs(draft: &mut DocumentGraphDraft) -> TestResult {
    draft.resources.push(Resource {
        resource_id: LogicalId::parse("keep-resource")?,
        kind: ResourceKind::Image,
        artifact: Some(ArtifactRef {
            sha256: [3; 32],
            byte_length: 11,
            media_type: "image/png".into(),
        }),
        metadata: Properties::new(),
    });
    draft.styles.push(Style {
        style_id: LogicalId::parse("keep-style")?,
        based_on: None,
        properties: Properties::new(),
    });
    draft.opaque_preservation_bag.push(OpaqueExtension {
        handle: LogicalId::parse("keep-opaque")?,
        sha256: [4; 32],
        byte_length: 12,
        preservation: OpaquePreservation::PreserveExact,
    });
    Ok(())
}

fn context<'a>(
    graph: &'a DocumentGraph,
    f: &Fixture,
) -> Result<FullDocumentFormContext<'a>, Box<dyn Error>> {
    Ok(FullDocumentFormContext::bind(
        graph,
        graph.canonical_sha256()?,
        Sha256::digest(&f.source).into(),
        RevisionId::parse("revision-1")?,
    )?)
}

// Independent whole-tree comparison: mask ONLY complete state properties of form nodes.
fn mask_state(value: &mut Value) {
    match value {
        Value::Object(fields) => {
            if fields.get("node_type").and_then(Value::as_str) == Some("form_control")
                && let Some(Value::Object(properties)) = fields.get_mut("properties")
            {
                properties.insert(
                    "complete_control_state_json".into(),
                    json!("state-only-mask"),
                );
            }
            for child in fields.values_mut() {
                mask_state(child);
            }
        }
        Value::Array(values) => {
            for child in values {
                mask_state(child);
            }
        }
        _ => {}
    }
}

fn collect_states(
    value: &Value,
    states: &mut std::collections::BTreeMap<String, String>,
) -> TestResult {
    match value {
        Value::Object(fields) => {
            if fields.get("node_type").and_then(Value::as_str) == Some("form_control") {
                let id = fields["common"]["node_id"].as_str().ok_or("logical id")?;
                let state = fields["properties"]["complete_control_state_json"]["value"]
                    .as_str()
                    .ok_or("state")?;
                if states.insert(id.into(), state.into()).is_some() {
                    return Err("duplicate form".into());
                }
            }
            for child in fields.values() {
                collect_states(child, states)?;
            }
        }
        Value::Array(values) => {
            for child in values {
                collect_states(child, states)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn matrix_full(label: &str) -> TestResult {
    let (f, expected) = matrix(label)?;
    let (request, access) = matrix_request(label, &f)?;
    let native = operation_context(&f)?;
    let operation = FormOperationPreparation::prepare_json(
        &native,
        identity("full-plan", "revision-1")?,
        &request,
        &access,
    )?;
    let graph = full_graph(&operation)?;
    let before = graph.canonical_json()?;
    let full = context(&graph, &f)?;
    let prepared = FullDocumentFormPreparation::prepare(&full, &operation, &native, &access)?;
    assert_eq!(
        prepared.verify(&full, &operation, &native, &access)?,
        *prepared.receipt()
    );
    assert_eq!(
        prepared.compiled_plan().base_graph_sha256(),
        graph.canonical_sha256()?
    );
    assert_ne!(
        prepared.compiled_plan().base_graph_sha256(),
        operation.compiled_plan().base_graph_sha256()
    );
    assert_ne!(
        prepared.receipt().inventory_operation_sha256,
        prepared.receipt().full_graph_operation_sha256
    );
    assert_eq!(prepared.receipt().matched_controls, 6);
    assert_eq!(
        prepared.receipt().changed_controls,
        operation.receipt().changed_controls
    );
    assert_eq!(
        prepared.compiled_plan().operations().len(),
        operation.compiled_plan().operations().len()
    );
    for (full_op, original) in prepared
        .compiled_plan()
        .operations()
        .iter()
        .zip(operation.compiled_plan().operations())
    {
        assert_eq!(full_op.target().node_id(), original.target().node_id());
        assert_eq!(full_op.capability_id(), original.capability_id());
        assert_eq!(
            arg_text(full_op, "target_control_state_json")?,
            arg_text(original, "target_control_state_json")?
        );
        assert_eq!(
            arg_text(full_op, "source_full_graph_sha256")?,
            hex::encode(graph.canonical_sha256()?)
        );
        assert_eq!(
            arg_text(full_op, "target_full_graph_sha256")?,
            prepared.receipt().target_graph_sha256
        );
        assert_ne!(
            full_op.target().structural_path(),
            original.target().structural_path()
        );
    }
    let mut source: Value = serde_json::from_slice(&before)?;
    let mut target = serde_json::to_value(prepared.target_graph())?;
    let mut expected_states = std::collections::BTreeMap::new();
    let mut actual_states = std::collections::BTreeMap::new();
    collect_states(&source, &mut expected_states)?;
    collect_states(&target, &mut actual_states)?;
    for op in operation.compiled_plan().operations() {
        expected_states.insert(
            op.target().node_id().as_str().into(),
            arg_text(op, "target_control_state_json")?.into(),
        );
    }
    assert!(
        expected_states == actual_states,
        "every complete source or target form state must match"
    );
    mask_state(&mut source);
    mask_state(&mut target);
    assert_eq!(
        source, target,
        "all other full-graph fields must stay byte-canonical-equivalent"
    );
    assert_eq!(
        graph.canonical_json()?,
        before,
        "original immutable IR unchanged"
    );
    assert_eq!(operation.candidate_bytes(), expected);
    assert_eq!(
        prepared.require_current_product_route(&full, &operation, &native, &access),
        Err(FullDocumentFormError::RouteUnqualified)
    );
    Ok(())
}
#[test]
fn full_ir_all_five_kinds_nested_table_drawing_note_and_second_section() -> TestResult {
    matrix_full("five-kinds")
}
#[test]
fn full_ir_empty_text_preserves_all_other_controls() -> TestResult {
    matrix_full("empty-text")
}
#[test]
fn full_ir_reset_defaults_preserves_complete_graph() -> TestResult {
    matrix_full("reset-defaults")
}
#[test]
fn full_ir_clear_selections_is_atomic_on_actual_full_ir() -> TestResult {
    matrix_full("clear-selections")
}

fn with_prepared(
    test: impl FnOnce(
        &Fixture,
        &PreparedFormOperation,
        &FormOperationContext<'_>,
        &FormInputAccessPolicy,
        DocumentGraph,
    ) -> TestResult,
) -> TestResult {
    let (f, _) = matrix("five-kinds")?;
    let (request, access) = matrix_request("five-kinds", &f)?;
    let native = operation_context(&f)?;
    let operation = FormOperationPreparation::prepare_json(
        &native,
        identity("full-plan", "revision-1")?,
        &request,
        &access,
    )?;
    let graph = full_graph(&operation)?;
    test(&f, &operation, &native, &access, graph)
}

#[test]
fn full_ir_projection_and_security_flags_fail_closed() -> TestResult {
    with_prepared(|f, op, _, _, graph| {
        assert!(
            matches!(context(op.selection_projection(), f), Err(error) if error.to_string() == "FULL_DOCUMENT_FORM_INVENTORY_PROJECTION_REJECTED")
        );
        for flag in 0..3 {
            let mut draft = graph.clone().into_draft();
            match flag {
                0 => draft.security_state.protected = true,
                1 => draft.security_state.encrypted = true,
                _ => draft.security_state.signed = true,
            }
            let bad = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
            assert!(
                matches!(context(&bad, f), Err(error) if error.to_string() == "FULL_DOCUMENT_FORM_PROTECTED_GRAPH_REJECTED")
            );
        }
        Ok(())
    })
}

#[test]
fn full_ir_wrong_package_graph_document_and_revision_fail_closed() -> TestResult {
    with_prepared(|f, op, native, access, graph| {
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                [0; 32],
                Sha256::digest(&f.source).into(),
                RevisionId::parse("revision-1")?
            ),
            Err(FullDocumentFormError::Binding)
        ));
        for (package, revision) in [
            ([0; 32], "revision-1"),
            (Sha256::digest(&f.source).into(), "revision-2"),
        ] {
            let bad = FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                package,
                RevisionId::parse(revision)?,
            )?;
            assert!(matches!(
                FullDocumentFormPreparation::prepare(&bad, op, native, access),
                Err(FullDocumentFormError::Binding)
            ));
        }
        let mut draft = graph.into_draft();
        draft.document_id = DocumentId::parse("different-document")?;
        let bad = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormPreparation::prepare(&context(&bad, f)?, op, native, access),
            Err(FullDocumentFormError::Binding)
        ));
        Ok(())
    })
}

#[test]
fn full_ir_missing_extra_wrong_kind_and_noncanonical_state_fail_closed() -> TestResult {
    with_prepared(|f, op, native, access, graph| {
        for variant in 0..6 {
            let mut draft = graph.clone().into_draft();
            match variant {
                0 => {
                    draft.sections[1].body.children.pop();
                }
                1 => {
                    let mut extra = draft.sections[1].body.children[0].clone();
                    if let Node::FormControl(node) = &mut extra {
                        node.common.node_id = LogicalId::parse("extra-form")?;
                    }
                    draft.sections[1].body.children.push(extra);
                }
                _ => {
                    let Node::FormControl(node) = &mut draft.sections[1].body.children[0] else {
                        return Err("form".into());
                    };
                    match variant {
                        2 => node.control_kind = "different-kind".into(),
                        3 => node.properties.insert(
                            "complete_control_state_json",
                            PropertyValue::Text("{}".into()),
                        ),
                        4 => node
                            .properties
                            .insert("complete_control_state_json", PropertyValue::Boolean(true)),
                        _ => node.properties = Properties::new(),
                    }
                }
            }
            let bad = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
            assert!(matches!(
                FullDocumentFormPreparation::prepare(&context(&bad, f)?, op, native, access),
                Err(FullDocumentFormError::Inventory)
            ));
        }
        Ok(())
    })
}

#[test]
fn full_ir_fresh_nonform_drift_invalidates_prepared_binding() -> TestResult {
    with_prepared(|f, op, native, access, graph| {
        let prepared =
            FullDocumentFormPreparation::prepare(&context(&graph, f)?, op, native, access)?;
        let mut draft = graph.into_draft();
        draft
            .settings
            .insert("new-setting", PropertyValue::Integer(9));
        let fresh = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        assert_eq!(
            prepared.verify(&context(&fresh, f)?, op, native, access),
            Err(FullDocumentFormError::Binding)
        );
        Ok(())
    })
}

#[test]
fn full_ir_fresh_access_denial_and_sensitive_debug_are_not_bypassed() -> TestResult {
    with_prepared(|f, op, native, access, graph| {
        let full = context(&graph, f)?;
        let prepared = FullDocumentFormPreparation::prepare(&full, op, native, access)?;
        let mut deny = access.clone();
        deny.input_allowed = false;
        assert_eq!(
            prepared.verify(&full, op, native, &deny),
            Err(FullDocumentFormError::Operation)
        );
        for public in [
            format!("{full:?}"),
            format!("{prepared:?}"),
            serde_json::to_string(prepared.receipt())?,
        ] {
            assert!(!public.contains("preserved private paragraph"));
            assert!(!public.contains("新 &"));
            assert!(!public.contains("90001"));
        }
        Ok(())
    })
}
