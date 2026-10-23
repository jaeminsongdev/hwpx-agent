//! Original compiler + original authenticated candidate, isolated service fixtures.
use super::*;
use domain_ir::{
    CanonicalArgumentValue, CompiledOperation, CompiledOperationPlan, OperationPlanLimits, PlanId,
};
use hwpx_agent_cli::form_stored_provider::actual_import::bookmark_command_output::compiled::{
    BOOKMARK_COMMAND_EDIT_CAPABILITY, BookmarkCommandCompileError as C,
};
use hwpx_package::document_import::fields::bookmark_crossref::BookmarkCrossReferenceDisplay as ObservedDisplay;
fn plan_id() -> Result<PlanId, Box<dyn Error>> {
    Ok(PlanId::parse("bookmark-command-compiler623")?)
}
fn text<'a>(op: &'a CompiledOperation, key: &str) -> Result<&'a str, Box<dyn Error>> {
    match op.arguments().get(key).ok_or("argument")?.value() {
        CanonicalArgumentValue::Text(value) => Ok(value),
        _ => Err("argument kind".into()),
    }
}
fn unchanged(stored: &StoredFixture, original: &[u8]) -> TestResult {
    require(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?
            == stored.head,
    )?;
    require(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.ingested")
            .count()
            == 2,
    )?;
    require(
        stored
            .artifacts
            .download(&stored.owner, stored.result, 20)?
            == original,
    )
}
pub(crate) fn observation() -> Result<Value, Box<dyn Error>> {
    let corpus: Value = serde_json::from_str(CORPUS)?;
    require(
        hex::encode(Sha256::digest(CORPUS.as_bytes()))
            == "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f",
    )?;
    let pin = &corpus["cases"][2]["artifacts"]["saved"];
    let bytes = read_pin(pin)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let p = provider(&stored, &ctx)?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, false)?;
    let candidate = prepare(&source, &p, &s)?;
    let digest = candidate.receipt().output.output_package_sha256;
    let compiled = candidate.compile(&p, plan_id()?, 6)?;
    require(
        compiled.compiled().operations().len() == 1
            && compiled.receipt().compiled_plan_sha256 == compiled.compiled().canonical_sha256()?,
    )?;
    let output = compiled.with_verified_bytes(&p, 7, |v| v.to_vec())?;
    require(<[u8; 32]>::from(Sha256::digest(&output)) == digest)?;
    let bound = Product::read_source_bookmark_crossrefs(
        &output,
        DocumentId::parse("actual-form-document")?,
        Sha256::digest(&output).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    require(
        bound.bindings().len() == 1
            && bound.bindings()[0].hyperlink
            && bound.bindings()[0].display == ObservedDisplay::Page,
    )?;
    require(compiled.verify(&p, 8)? == compiled.receipt())?;
    require(matches!(
        compiled.require_current_product_route(&p, 9),
        Err(C::Stored(E::RouteUnqualified))
    ))?;
    unchanged(&stored, &bytes)?;
    require(read_pin(pin)? == bytes)?;
    Ok(
        json!({"state":"compiled_bookmark623_actual_source_fixture_not_native_CAS_or_route","source_sha256":pin["sha256"],
        "receipt":compiled.receipt(),"actual_native_started":false,"head_changed":false,"result_ingested":false,
        "source_overwritten":false,"route_qualified":false,"P09_complete":false}),
    )
}
#[test]
fn actual_captured_candidate_compiles_and_reads_back_without_native_or_publication() -> TestResult {
    observation()?;
    Ok(())
}
#[test]
fn plan_uses_original_revision_graph_exact_field_owner_hashes_and_no_raw_values() -> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let source = p.import_actual_forms(f.head, 4)?;
    let s = selection(&source, true)?;
    let candidate = prepare(&source, &p, &s)?;
    let before = candidate.with_verified_bytes(&p, 5, |v| v.to_vec())?;
    let output_receipt = candidate.receipt().output.clone();
    let c = candidate.compile(&p, plan_id()?, 6)?;
    let plan = c.compiled();
    assert_eq!(plan.plan_id(), &plan_id()?);
    assert_eq!(plan.operations().len(), 1);
    assert_eq!(
        plan.base_revision().as_str(),
        f.head.revision_id().ok_or("head")?.public_id()
    );
    assert_eq!(
        plan.base_graph_sha256(),
        source.imported().graph().canonical_sha256()?
    );
    assert_eq!(c.receipt().compiled_plan_sha256, plan.canonical_sha256()?);
    let op = &plan.operations()[0];
    let change = &output_receipt.changes[0];
    assert_eq!(
        op.capability_id().as_str(),
        BOOKMARK_COMMAND_EDIT_CAPABILITY
    );
    assert_ne!(op.capability_id().as_str(), "ref.crossref_insert");
    assert_eq!(op.arguments().len(), 12);
    assert!(op.depends_on().is_empty());
    for (key, expected) in [
        (
            "source_field_sha256",
            hex::encode(change.source_field_sha256),
        ),
        (
            "source_meaning_sha256",
            hex::encode(change.source_meaning_sha256),
        ),
        (
            "output_command_sha256",
            hex::encode(change.output_command_sha256),
        ),
        (
            "selected_target_id_sha256",
            hex::encode(change.selected_target_id_sha256),
        ),
        (
            "selected_target_state_sha256",
            change.selected_target_state_sha256.clone(),
        ),
        ("request_sha256", hex::encode(output_receipt.request_sha256)),
        (
            "output_package_sha256",
            hex::encode(output_receipt.output_package_sha256),
        ),
    ] {
        assert_eq!(text(op, key)?, expected);
    }
    assert_eq!(text(op, "source_reference_id")?, s.id.as_str());
    let fields = ImportedDocumentFields::import(source.imported())?;
    assert_eq!(
        text(op, "source_field_anchor_json")?,
        serde_json::to_string(&fields.fields()[0].begin_anchor)?
    );
    let canonical = plan.canonical_json()?;
    assert_eq!(
        CompiledOperationPlan::from_canonical_json(&canonical, OperationPlanLimits::default())?,
        *plan
    );
    for value in [
        String::from_utf8(canonical)?,
        serde_json::to_string(c.receipt())?,
        format!("{c:?}"),
    ] {
        for raw in [
            "private-old",
            "private-new",
            "private-cache",
            "原文",
            "?private",
        ] {
            assert!(!value.contains(raw));
        }
    }
    assert_eq!(before, c.with_verified_bytes(&p, 7, |v| v.to_vec())?);
    assert!(!c.receipt().execution_or_publication_authority);
    assert!(c.receipt().cached_values_preserved_not_refreshed);
    // Route denial is not a false permission grant or a source-denial poison.
    assert!(matches!(
        c.require_current_product_route(&p, 8),
        Err(C::Stored(E::RouteUnqualified))
    ));
    c.verify(&p, 9)?;
    unchanged(&f, &bytes)
}
fn many_sample() -> Result<Vec<u8>, Box<dyn Error>> {
    let mut body = String::new();
    for (paragraph, ids) in [(1, vec![10, 11]), (2, vec![12])] {
        body.push_str(&format!("<hp:p id='{paragraph}'>"));
        if paragraph == 1 {
            body.push_str(&fixture::marker("private-old"));
            body.push_str(&fixture::marker("private-new"));
        }
        for id in ids {
            body.push_str(&format!("<hp:run charPrIDRef='0'><hp:ctrl><hp:fieldBegin id='{id}' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='Command'>?private-old;6;1;0;0</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>private-cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl></hp:run>"));
        }
        body.push_str("</hp:p>");
    }
    base::package(&body)
}
#[test]
fn reordered_multiple_fields_resolve_actual_distinct_control_owners_not_paragraph_order()
-> TestResult {
    let bytes = many_sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let source = p.import_actual_forms(f.head, 4)?;
    let fields = ImportedDocumentFields::import(source.imported())?;
    let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
    let target = &source.bookmarks()[1].reference_id;
    let requests = [2, 0, 1]
        .into_iter()
        .map(|i| {
            Ok(Change {
                reference_id: &fields.fields()[i].reference_id,
                expected_source_field_sha256: fields.fields()[i].begin_anchor.fingerprint_sha256,
                expected_meaning_sha256: index.meaning_sha256(i)?,
                target_id: target,
                display: Display::Page,
                hyperlink: true,
            })
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    let c = source
        .prepare_bookmark_command_candidate(&p, &requests, limits()?, WriterLimits::default(), 5)?
        .compile(&p, plan_id()?, 6)?;
    let ops = c.compiled().operations();
    assert_eq!(ops.len(), 3);
    let nodes = &source.imported().graph().sections()[0].body.children;
    let raw = source.imported().source();
    // Independent smallest-containing-source-span oracle, not production's parent map.
    for (op, i) in ops.iter().zip([2, 0, 1]) {
        let at = raw.resolve_anchor(&fields.fields()[i].begin_anchor)?;
        let span = at
            .element()
            .and_then(|e| e.outer_span())
            .ok_or("field span")?;
        let mut owners = Vec::new();
        for node in nodes {
            if let Some(anchor) = &node.common().source_anchor {
                let owner = raw.resolve_anchor(anchor)?;
                if owner.part().path() == at.part().path() {
                    if let Some(outer) = owner.element().and_then(|e| e.outer_span()) {
                        if outer.start() <= span.start() && span.end() <= outer.end() {
                            owners.push((outer.end() - outer.start(), node, owner));
                        }
                    }
                }
            }
        }
        owners.sort_by_key(|v| v.0);
        let (_, expected, resolved) = owners.first().ok_or("actual owner")?;
        assert_eq!(op.target().node_id(), &expected.common().node_id);
        assert!(matches!(expected, domain_ir::Node::EmbeddedObject(_)));
        assert_eq!(
            resolved.element().ok_or("owner")?.name().local_name(),
            "ctrl"
        );
        assert_eq!(
            text(op, "source_reference_id")?,
            fields.fields()[i].reference_id.as_str()
        );
    }
    assert_ne!(ops[1].target().node_id(), ops[2].target().node_id());
    let output = c.with_verified_bytes(&p, 7, |v| v.to_vec())?;
    let bound = Product::read_source_bookmark_crossrefs(
        &output,
        DocumentId::parse("actual-form-document")?,
        Sha256::digest(&output).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    assert_eq!(bound.bindings().len(), 3);
    assert!(
        bound
            .bindings()
            .iter()
            .all(|v| v.hyperlink && v.display == ObservedDisplay::Page)
    );
    unchanged(&f, &bytes)
}
#[test]
fn compilation_rejects_read_scope_acl_quarantine_ciphertext_or_advanced_head() -> TestResult {
    for variant in 0..5 {
        let f = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
        let ctx = write_context(&f);
        let p = provider(&f, &ctx)?;
        let source = p.import_actual_forms(f.head, 4)?;
        let s = selection(&source, true)?;
        let c = prepare(&source, &p, &s)?;
        let read = f.provider()?;
        match variant {
            0 => {}
            1 => {
                f.artifacts.set_permissions(
                    &f.owner,
                    f.result,
                    f.reader.subject(),
                    BTreeSet::new(),
                    6,
                )?;
            }
            2 => {
                f.artifacts.quarantine(
                    &f.owner,
                    f.result,
                    QuarantineReason::parse("COMPILER_FIXTURE")?,
                    6,
                )?;
            }
            3 => f.blobs.tamper.store(true, Ordering::SeqCst),
            _ => advance(&f)?,
        }
        assert!(matches!(
            c.compile(if variant == 0 { &read } else { &p }, plan_id()?, 7),
            Err(C::Stored(_))
        ));
    }
    Ok(())
}
#[test]
fn compiled_delivery_preserves_current_scope_acl_aead_head_denials_and_sticky_poison() -> TestResult
{
    for variant in 0..5 {
        let f = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
        let ctx = write_context(&f);
        let p = provider(&f, &ctx)?;
        let source = p.import_actual_forms(f.head, 4)?;
        let s = selection(&source, true)?;
        let c = prepare(&source, &p, &s)?.compile(&p, plan_id()?, 6)?;
        let read = f.provider()?;
        match variant {
            0 => {}
            1 => {
                f.artifacts.set_permissions(
                    &f.owner,
                    f.result,
                    f.reader.subject(),
                    BTreeSet::new(),
                    7,
                )?;
            }
            2 => {
                f.artifacts.quarantine(
                    &f.owner,
                    f.result,
                    QuarantineReason::parse("COMPILED_FIXTURE")?,
                    7,
                )?;
            }
            3 => f.blobs.tamper.store(true, Ordering::SeqCst),
            _ => advance(&f)?,
        }
        let hit = AtomicBool::new(false);
        assert!(matches!(
            c.with_verified_bytes(if variant == 0 { &read } else { &p }, 8, |_| hit
                .store(true, Ordering::SeqCst)),
            Err(C::Stored(_))
        ));
        assert!(!hit.load(Ordering::SeqCst));
        if variant == 1 {
            f.artifacts.set_permissions(
                &f.owner,
                f.result,
                f.reader.subject(),
                BTreeSet::from([ArtifactPermission::Read]),
                9,
            )?;
        }
        f.blobs.tamper.store(false, Ordering::SeqCst);
        assert!(matches!(
            c.verify(&p, 10),
            Err(C::Stored(E::PreviouslyDenied))
        ));
    }
    Ok(())
}
#[test]
fn head_change_after_compilation_before_return_is_rejected() -> TestResult {
    let f = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let revisions = RevisionService::new(HeadFault {
        inner: f.revisions.repository().clone(),
        reads: AtomicUsize::new(0),
        at: AtomicUsize::new(0),
        fail: true,
        hook: None,
    });
    let p = StoredFormProvider::bind(
        &f.artifacts,
        &revisions,
        &ctx,
        &f.revision_context,
        f.project,
        f.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let source = p.import_actual_forms(f.head, 4)?;
    let s = selection(&source, true)?;
    let candidate = source.prepare_bookmark_command_candidate(
        &p,
        &[s.request()],
        limits()?,
        WriterLimits::default(),
        5,
    )?;
    revisions.repository().arm(7); // First delivery has six head reads; seven is post-compile verification.
    assert!(matches!(
        candidate.compile(&p, plan_id()?, 6),
        Err(C::Stored(_))
    ));
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst), 7);
    Ok(())
}
#[test]
fn actual_acl_revocation_after_compilation_prevents_returning_plan() -> TestResult {
    let f = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let revoke = || {
        f.artifacts
            .set_permissions(&f.owner, f.result, f.reader.subject(), BTreeSet::new(), 6)
            .expect("fixture revoke");
    };
    let revisions = RevisionService::new(HeadFault {
        inner: f.revisions.repository().clone(),
        reads: AtomicUsize::new(0),
        at: AtomicUsize::new(0),
        fail: false,
        hook: Some(Box::new(revoke)),
    });
    let p = StoredFormProvider::bind(
        &f.artifacts,
        &revisions,
        &ctx,
        &f.revision_context,
        f.project,
        f.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let source = p.import_actual_forms(f.head, 4)?;
    let s = selection(&source, true)?;
    let candidate = source.prepare_bookmark_command_candidate(
        &p,
        &[s.request()],
        limits()?,
        WriterLimits::default(),
        5,
    )?;
    revisions.repository().arm(7);
    assert!(matches!(
        candidate.compile(&p, plan_id()?, 6),
        Err(C::Stored(_))
    ));
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst), 7);
    Ok(())
}
#[test]
fn compiled_writer_final_head_check_still_blocks_callback_after_fresh_source_read() -> TestResult {
    let f = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let revisions = RevisionService::new(HeadFault {
        inner: f.revisions.repository().clone(),
        reads: AtomicUsize::new(0),
        at: AtomicUsize::new(0),
        fail: true,
        hook: None,
    });
    let p = StoredFormProvider::bind(
        &f.artifacts,
        &revisions,
        &ctx,
        &f.revision_context,
        f.project,
        f.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let source = p.import_actual_forms(f.head, 4)?;
    let s = selection(&source, true)?;
    let c = source
        .prepare_bookmark_command_candidate(
            &p,
            &[s.request()],
            limits()?,
            WriterLimits::default(),
            5,
        )?
        .compile(&p, plan_id()?, 6)?;
    revisions.repository().arm(6);
    let hit = AtomicBool::new(false);
    assert!(matches!(
        c.with_verified_bytes(&p, 7, |_| hit.store(true, Ordering::SeqCst)),
        Err(C::Stored(_))
    ));
    assert!(!hit.load(Ordering::SeqCst));
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst), 6);
    assert!(matches!(
        c.verify(&p, 8),
        Err(C::Stored(E::PreviouslyDenied))
    ));
    Ok(())
}
