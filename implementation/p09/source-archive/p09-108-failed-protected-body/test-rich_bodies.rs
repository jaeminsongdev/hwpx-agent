//! Complete caller IR fixtures only; never native metadata/source import qualification.
use super::*;
use hwpx_agent_cli::comment_operation::rich_bodies::*;

fn rich_flow(prefix: &str) -> Flow {
    let mut p = paragraph(&format!("{prefix}-paragraph"));
    if let Node::Paragraph(p) = &mut p {
        p.inlines = vec![
            Inline::Text {
                text: "RICH-PRIVATE 한글 &".into(),
            },
            Inline::Tab,
            Inline::LineBreak,
        ];
        p.common.style_refs.push(id("unrelated-style"));
    }
    Flow {
        children: vec![
            p,
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
                        children: vec![paragraph(&format!("{prefix}-cell-paragraph"))],
                    },
                    properties: Properties::new(),
                }],
                properties: Properties::new(),
            }),
        ],
    }
}
fn bodies() -> Vec<CommentRichBody> {
    [
        ("explanation-1", "hidden"),
        ("comment-1", "memo1"),
        ("comment-2", "memo2"),
    ]
    .into_iter()
    .map(|(review, prefix)| CommentRichBody {
        review_id: id(review),
        body: rich_flow(prefix),
    })
    .collect()
}
fn state_for(
    bodies: &[CommentRichBody],
) -> Result<CommentDocumentState, Box<dyn std::error::Error>> {
    let mut value: Value = serde_json::from_slice(&state()?.canonical_json(limits())?)?;
    for body in bodies {
        let mut found = false;
        for (list, key) in [
            ("hidden_explanations", "logical_explanation_id"),
            ("comments", "logical_comment_id"),
        ] {
            for entry in value[list].as_array_mut().ok_or("entries")? {
                if entry["identity"][key].as_str() == Some(body.review_id.as_str()) {
                    entry["body_graph_sha256"] = Value::String(body_sha256(&body.body)?);
                    found = true;
                }
            }
        }
        if !found {
            return Err("unknown fixture body".into());
        }
    }
    Ok(CommentDocumentState::from_draft(
        serde_json::from_value(value)?,
        limits(),
    )?)
}
fn graph_for(
    state: &CommentDocumentState,
    bodies: &[CommentRichBody],
) -> Result<DocumentGraph, Box<dyn std::error::Error>> {
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
#[test]
fn all_five_rich_operations_validate_actual_nested_flow_and_compile_final_not_intermediate_graph()
-> TestResult {
    let bodies = bodies();
    let state = state_for(&bodies)?;
    let source = graph_for(&state, &bodies)?;
    let base = context(&source, &state)?;
    let rich = CommentRichContext::bind(&base, bodies.clone())?;
    let original = source.clone().into_draft();
    for mut operation in operations(&state) {
        let (insertion, inserted) =
            if let CommentOperation::InsertComment { comment, .. } = &mut operation {
                let body = CommentRichBody {
                    review_id: comment.identity.logical_comment_id.clone(),
                    body: rich_flow("new-memo"),
                };
                comment.body_graph_sha256 = body_sha256(&body.body)?;
                (
                    Some(CommentInsertionTarget {
                        anchor: comment.anchor.clone(),
                        node_id: id("body-3"),
                    }),
                    Some(body),
                )
            } else {
                (None, None)
            };
        let json = request(&base, &state, operation)?;
        let plan = PlanId::parse("rich-plan")?;
        let intermediate = CommentOperationPreparation::prepare_json(
            &base,
            plan.clone(),
            &json,
            insertion.clone(),
        )?;
        let prepared = RichCommentOperationPreparation::prepare_json(
            &rich,
            plan,
            &json,
            insertion,
            inserted.clone(),
        )?;
        assert_eq!(prepared.verify(&rich)?, *prepared.receipt());
        assert_eq!(
            prepared.receipt().target_graph_sha256,
            hex::encode(prepared.target_graph().canonical_sha256()?)
        );
        for compiled in prepared.compiled().operations() {
            assert_eq!(
                compiled
                    .arguments()
                    .get("target_graph_sha256")
                    .ok_or("target arg")?
                    .value(),
                &CanonicalArgumentValue::Text(prepared.receipt().target_graph_sha256.clone())
            );
        }
        let after = prepared.target_graph().clone().into_draft();
        assert_eq!(after.sections, original.sections);
        assert_eq!(after.notes, original.notes);
        assert_eq!(after.resources, original.resources);
        assert_eq!(after.references, original.references);
        if inserted.is_some() {
            assert_ne!(prepared.target_graph(), intermediate.target_graph());
            assert_ne!(prepared.compiled(), intermediate.compiled());
            assert_eq!(prepared.target_bodies().len(), 4);
            assert_eq!(prepared.target_bodies()[0], bodies[0]);
            assert_eq!(prepared.target_bodies()[1], bodies[1]);
            assert_eq!(prepared.target_bodies()[2], inserted.ok_or("inserted")?);
            assert_eq!(prepared.target_bodies()[3], bodies[2]);
        } else {
            assert_eq!(prepared.target_graph(), intermediate.target_graph());
            assert_eq!(prepared.target_bodies(), bodies);
        }
        assert!(
            !prepared.receipt().native_metadata_verified
                && !prepared.receipt().hwpx_lowered
                && !prepared.receipt().execution_authority_verified
        );
        assert_eq!(
            prepared.require_current_product_route(&rich).err(),
            Some(CommentRichBodyError::Operation(
                CommentOperationError::RouteUnqualified
            ))
        );
        assert!(!format!("{rich:?}{prepared:?} {:?}", prepared.receipt()).contains("RICH-PRIVATE"));
    }
    Ok(())
}
#[test]
fn complete_exact_ordered_body_inventory_and_flow_digest_are_mandatory() -> TestResult {
    let bodies = bodies();
    let state = state_for(&bodies)?;
    let source = graph_for(&state, &bodies)?;
    let base = context(&source, &state)?;
    let mut missing = bodies.clone();
    missing.pop();
    let mut extra = bodies.clone();
    extra.push(bodies[0].clone());
    let mut reversed = bodies.clone();
    reversed.reverse();
    let mut changed = bodies.clone();
    changed[0].body = rich_flow("changed");
    for values in [missing, extra, reversed, changed] {
        assert!(CommentRichContext::bind(&base, values).is_err());
    }
    let mut draft = source.into_draft();
    let mut without_body_view = Properties::new();
    for (key, value) in draft.metadata.iter() {
        if key != COMMENT_RICH_BODIES_PROPERTY {
            without_body_view.insert(key, value.clone());
        }
    }
    draft.metadata = without_body_view;
    let no_view = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    assert!(CommentRichContext::bind(&context(&no_view, &state)?, bodies).is_err());
    Ok(())
}
#[test]
fn original_global_ids_style_resource_and_table_geometry_validate_complete_rich_bodies()
-> TestResult {
    for variant in 0..5 {
        let mut bodies = bodies();
        if let Node::Paragraph(p) = &mut bodies[0].body.children[0] {
            match variant {
                0 => p.common.node_id = id("body-1"),
                1 => p.common.style_refs.push(id("missing-style")),
                2 => p.common.resource_refs.push(id("missing-resource")),
                _ => {}
            }
        }
        if let Node::Table(t) = &mut bodies[0].body.children[1] {
            if variant == 3 {
                t.cells[0].row = 1;
            }
            if variant == 4 {
                t.cells[0].body.children = vec![paragraph("memo1-paragraph")];
            }
        }
        let state = state_for(&bodies)?;
        let source = graph_for(&state, &bodies)?;
        let base = context(&source, &state)?;
        assert!(
            matches!(
                CommentRichContext::bind(&base, bodies),
                Err(CommentRichBodyError::Graph)
            ),
            "variant {variant}"
        );
    }
    Ok(())
}
#[test]
fn original_full_admission_and_nested_body_protection_are_not_bypassed() -> TestResult {
    let mut protected_bodies = bodies();
    if let Node::Table(t) = &mut protected_bodies[0].body.children[1] {
        t.common
            .semantics
            .insert("protected", PropertyValue::Boolean(true));
    }
    let state = state_for(&protected_bodies)?;
    let source = graph_for(&state, &protected_bodies)?;
    let base = context(&source, &state)?;
    assert!(CommentRichContext::bind(&base, protected_bodies).is_err());
    let bodies = bodies();
    let state = state_for(&bodies)?;
    let mut draft = graph_for(&state, &bodies)?.into_draft();
    draft.metadata.insert(
        "review_body_import_profile",
        PropertyValue::Text(
            hwpx_package::document_import::structure::review::REVIEW_BODY_IMPORT_PROFILE.into(),
        ),
    );
    let partial = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    assert!(context(&partial, &state).is_err());
    Ok(())
}
#[test]
fn insertion_requires_exact_new_body_and_noninsertion_rejects_extra_body() -> TestResult {
    let bodies = bodies();
    let state = state_for(&bodies)?;
    let source = graph_for(&state, &bodies)?;
    let base = context(&source, &state)?;
    let rich = CommentRichContext::bind(&base, bodies)?;
    let operation = operations(&state).remove(1);
    let insertion = if let CommentOperation::InsertComment { comment, .. } = &operation {
        CommentInsertionTarget {
            anchor: comment.anchor.clone(),
            node_id: id("body-3"),
        }
    } else {
        return Err("insert fixture".into());
    };
    let json = request(&base, &state, operation)?;
    for body in [
        None,
        Some(CommentRichBody {
            review_id: id("wrong-review"),
            body: rich_flow("new"),
        }),
        Some(CommentRichBody {
            review_id: id("comment-3"),
            body: rich_flow("new"),
        }),
    ] {
        assert!(
            RichCommentOperationPreparation::prepare_json(
                &rich,
                PlanId::parse("rejected")?,
                &json,
                Some(insertion.clone()),
                body
            )
            .is_err()
        );
    }
    let json = request(&base, &state, operations(&state).remove(0))?;
    assert!(
        RichCommentOperationPreparation::prepare_json(
            &rich,
            PlanId::parse("extra")?,
            &json,
            None,
            Some(CommentRichBody {
                review_id: id("comment-3"),
                body: rich_flow("extra")
            })
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn fresh_graph_body_package_and_revision_drift_reject_immutable_preparation() -> TestResult {
    let bodies = bodies();
    let state = state_for(&bodies)?;
    let source = graph_for(&state, &bodies)?;
    let base = context(&source, &state)?;
    let rich = CommentRichContext::bind(&base, bodies.clone())?;
    let prepared = RichCommentOperationPreparation::prepare_json(
        &rich,
        PlanId::parse("fresh")?,
        &request(&base, &state, operations(&state).remove(0))?,
        None,
        None,
    )?;
    for (package, revision) in [([8; 32], "r1"), ([7; 32], "r2")] {
        let other = CommentOperationContext::bind(
            &source,
            &state,
            source.canonical_sha256()?,
            package,
            RevisionId::parse(revision)?,
        )?;
        assert!(
            prepared
                .verify(&CommentRichContext::bind(&other, bodies.clone())?)
                .is_err()
        );
    }
    let mut draft = source.clone().into_draft();
    draft.metadata.insert(
        "unrelated-preserved-metadata",
        PropertyValue::Text("changed".into()),
    );
    let changed = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    assert!(
        prepared
            .verify(&CommentRichContext::bind(
                &context(&changed, &state)?,
                bodies.clone()
            )?)
            .is_err()
    );
    let mut changed_bodies = bodies;
    changed_bodies[0].body = rich_flow("different-source-body");
    let changed_state = state_for(&changed_bodies)?;
    let changed = graph_for(&changed_state, &changed_bodies)?;
    assert!(
        prepared
            .verify(&CommentRichContext::bind(
                &context(&changed, &changed_state)?,
                changed_bodies
            )?)
            .is_err()
    );
    Ok(())
}
#[test]
fn original_strict_request_unknown_keys_and_wrong_flow_are_still_rejected() -> TestResult {
    let bodies = bodies();
    let state = state_for(&bodies)?;
    let source = graph_for(&state, &bodies)?;
    let base = context(&source, &state)?;
    let rich = CommentRichContext::bind(&base, bodies)?;
    let json = request(&base, &state, operations(&state).remove(0))?;
    let mut unknown: Value = serde_json::from_slice(&json)?;
    unknown["native_approval"] = json!(true);
    assert!(
        RichCommentOperationPreparation::prepare_json(
            &rich,
            PlanId::parse("unknown")?,
            &serde_json::to_vec(&unknown)?,
            None,
            None
        )
        .is_err()
    );
    let mut drift: Value = serde_json::from_slice(&json)?;
    drift["expected_document_flow_sha256"] = json!("b".repeat(64));
    assert!(
        RichCommentOperationPreparation::prepare_json(
            &rich,
            PlanId::parse("drift")?,
            &serde_json::to_vec(&drift)?,
            None,
            None
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn explicit_empty_flow_is_bound_and_serialization_has_finite_aggregate_budget() -> TestResult {
    let mut bodies = bodies();
    bodies[0].body = Flow::default();
    let state = state_for(&bodies)?;
    let source = graph_for(&state, &bodies)?;
    let base = context(&source, &state)?;
    CommentRichContext::bind(&base, bodies)?;
    let mut large = paragraph("large");
    if let Node::Paragraph(p) = &mut large {
        p.inlines = vec![Inline::Text {
            text: "x".repeat(8 * 1024 * 1024),
        }];
    }
    assert_eq!(
        body_sha256(&Flow {
            children: vec![large]
        })
        .err(),
        Some(CommentRichBodyError::Limit)
    );
    let medium = CommentRichBody {
        review_id: id("medium"),
        body: Flow {
            children: vec![Node::Paragraph(ParagraphNode {
                common: NodeCommon::new(id("medium-body")),
                inlines: vec![Inline::Text {
                    text: "x".repeat(1024 * 1024),
                }],
                paragraph_properties: Properties::new(),
            })],
        },
    };
    assert_eq!(
        bodies_json(&vec![medium; 8]).err(),
        Some(CommentRichBodyError::Limit)
    );
    Ok(())
}
