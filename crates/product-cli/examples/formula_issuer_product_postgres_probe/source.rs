//! Frozen original RAM input and original policy/signature/consumer paths. No publication or native claim.
use super::{ContentDigest, Ed25519KeyPair, Probe, RequestContext, Result, Service};
use artifact_service::{
    ArtifactDescriptor, ArtifactKind, ArtifactMetadataRepository, FileName, IngestRequest,
    MediaType,
};
use domain_ir::{CellCoordinate, DocumentId, FormulaExpression};
use hwpx_agent_cli::{
    form_product_request::stored_operations::{
        StoredProductRequest,
        formula::{FormulaPreparationReceipt, PRODUCT_OPERATION_REQUEST_SCHEMA},
    },
    form_stored_provider::{
        StoredFormProvider,
        actual_import::source_policy::{
            PolicyReadScope, SourcePolicyVersion,
            formulas::{
                issuer::{
                    FormulaIssuerError, SystemFormulaIssuerClock,
                    product::FormulaIssuerDependencies,
                    registry::{
                        RegistryFormulaApprovalProvider, RegistryFormulaTrustProvider,
                        provision::{
                            FormulaApprovalSigner, FormulaIssuerProvisioningReceipt,
                            FormulaIssuerWorkflowFailure, PostgresFormulaIssuerWriteGateway,
                            RegistryFormulaProvisioner,
                        },
                    },
                },
                postgres::PostgresFormulaPolicyProvider,
                registration::{
                    FormulaPolicyDecision, FormulaPolicyRegistrationError,
                    FormulaPolicyRegistrationRecord, FormulaPolicyRegistrationRepository,
                    postgres::PostgresFormulaPolicyRegistrar,
                },
                revocation::postgres::PostgresFormulaPolicyRevoker,
            },
        },
    },
};
use hwpx_package::{
    BoundedZipReader, PackageLimits, PreservingXmlDocument, WriterLimits,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        fields::{
            ImportedDocumentFields,
            semantics::{
                ImportedDocumentFieldSemantics, ImportedFieldMeaning,
                evaluation::ImportedSourceFormulaEvaluation,
            },
        },
        forms::ImportedDocumentForms,
    },
};
use revision_service::{
    BranchId, CommitId, FullDocumentIrBinding, ProjectId, RevisionCommitRequest, RevisionHead,
    RevisionId, RevisionRequestContext, RevisionService, RevisionValidationState,
    postgres::source_formula_policy::{
        SourceFormulaPolicyReadRequest,
        issuer_registry::{
            FormulaApprovalReadRequest, FormulaIssuerRegistryRepository,
            LocalPostgresFormulaIssuerRegistryRepository,
            management::{
                FormulaApprovalRevocation, FormulaIssuerTrustRevocation,
                FormulaRegistryManagementAction, LocalPostgresFormulaRegistryManagementRepository,
                RegistryManagementCapability,
            },
        },
        revocation::SourceFormulaPolicyRevocationRequest,
    },
};
use std::{
    collections::BTreeMap,
    io::{Cursor, Write},
    path::{Component, Path, PathBuf},
    sync::{
        Mutex,
        atomic::{AtomicUsize, Ordering},
    },
    time::{SystemTime, UNIX_EPOCH},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

pub(super) const PRIOR: &[u8] = b"P143 synthetic baseline prior, not a signed/native execution";
pub(super) const RECEIPT: &[u8] =
    b"P143 synthetic baseline validation receipt, not product publication";
const DOCUMENT: &str = "p143-source-document";
pub(super) struct Input {
    pub index: usize,
    pub original_sha: ContentDigest,
    pub mode: &'static str,
    pub only_one_numeric_leaf_changed: bool,
    pub raw: Vec<u8>,
    pub graph_bytes: Vec<u8>,
    pub graph_sha: ContentDigest,
}
pub(super) struct Pipeline<'a> {
    pub metadata: &'a super::LocalPostgresMetadataRepository,
    pub registry: &'a LocalPostgresFormulaIssuerRegistryRepository,
    pub writes: &'a PostgresFormulaIssuerWriteGateway<'a>,
    pub policies: &'a PostgresFormulaPolicyProvider,
    pub artifacts: &'a Service,
    pub blobs: &'a super::ProbeBlobStore,
    pub context: &'a RequestContext,
    pub pair: &'a Ed25519KeyPair,
    pub project: ProjectId,
}
fn now() -> Result<u64> {
    Ok(SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs())
}
fn branch() -> Result<BranchId> {
    Ok(BranchId::parse("brn_63000000000000000000000000000003")?)
}
fn forms(raw: &[u8]) -> Result<ImportedDocumentForms> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            raw,
            DocumentId::parse(DOCUMENT)?,
            *ContentDigest::of(raw).as_bytes(),
            SourceImportLimits::default(),
        )?,
    )?)
}
fn source_index(value: Option<&str>) -> Result<usize> {
    let Some(value) = value else {
        return Ok(0);
    };
    if value.is_empty() || value.len() > 2 || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err("source_input_index_invalid".into());
    }
    let index: usize = value.parse()?;
    if index >= 36 || index.to_string() != value {
        return Err("source_input_index_invalid".into());
    }
    Ok(index)
}
fn configured_index() -> Result<usize> {
    let value = match std::env::var("P143_SOURCE_INDEX") {
        Ok(value) => Some(value),
        Err(std::env::VarError::NotPresent) => None,
        Err(_) => return Err("source_input_index_invalid".into()),
    };
    source_index(value.as_deref())
}
pub(super) fn read() -> Result<Input> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest_path = root.join("implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json");
    let metadata = std::fs::symlink_metadata(&manifest_path)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() != 112_797 {
        return Err("manifest_type_or_size_drift".into());
    }
    let manifest = std::fs::read(manifest_path)?;
    if ContentDigest::of(&manifest).hex()
        != "36b30c931b760bddedb4950c46c8bf7ed84a046dc8998f7f4a51530cfe9f693d"
    {
        return Err("manifest_digest_drift".into());
    }
    let manifest: serde_json::Value = serde_json::from_slice(&manifest)?;
    let rows = manifest["actual_inputs"]
        .as_array()
        .ok_or("manifest_input_rows_missing")?;
    if rows.len() != 36 {
        return Err("manifest_input_coverage_drift".into());
    }
    let index = configured_index()?;
    let selected = rows.get(index).ok_or("source_input_index_invalid")?;
    let relative = Path::new(selected["path"].as_str().ok_or("source_path_missing")?);
    if relative.is_absolute()
        || relative
            .components()
            .any(|c| !matches!(c, Component::Normal(_)))
    {
        return Err("source_path_scope".into());
    }
    let path = root.join(relative);
    let metadata = std::fs::symlink_metadata(&path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() > 32 * 1024 * 1024
        || Some(metadata.len()) != selected["bytes"].as_u64()
    {
        return Err("source_type_or_size_drift".into());
    }
    let raw = std::fs::read(path)?;
    if Some(ContentDigest::of(&raw).hex().as_str()) != selected["sha256"].as_str() {
        return Err("source_digest_drift".into());
    }
    let original_sha = ContentDigest::of(&raw);
    let (raw, mode, only_one_numeric_leaf_changed) = configured_input(raw)?;
    let imported = forms(&raw)?;
    let graph_bytes = imported.graph().canonical_json()?;
    let graph_sha = ContentDigest::parse(&hex::encode(imported.graph().canonical_sha256()?))?;
    Ok(Input {
        index,
        original_sha,
        mode,
        only_one_numeric_leaf_changed,
        raw,
        graph_bytes,
        graph_sha,
    })
}
fn configured_input(original: Vec<u8>) -> Result<(Vec<u8>, &'static str, bool)> {
    match std::env::var("P144_INPUT_MODE") {
        Err(std::env::VarError::NotPresent) => Ok((original, "original", false)),
        Ok(value) if value == "original" => Ok((original, "original", false)),
        Ok(value) if value == "numeric_derivative" => {
            Ok((numeric_derivative(&original)?, "numeric_derivative", true))
        }
        _ => Err("source_input_mode_invalid".into()),
    }
}
// Test-only RAM derivative: resolve one numeric input through the ORIGINAL AST and source anchor.
fn numeric_derivative(original: &[u8]) -> Result<Vec<u8>> {
    let index = referenced_numeric_leaf(original)?;
    let mut parts = entries(original)?;
    let bytes = parts
        .get_mut("Contents/section0.xml")
        .ok_or("numeric_section")?;
    let xml = PreservingXmlDocument::parse(bytes)?;
    let span = xml
        .elements()
        .get(index)
        .ok_or("numeric_leaf")?
        .content_span()
        .ok_or("numeric_span")?;
    let number = std::str::from_utf8(&bytes[span.start()..span.end()])?.parse::<i64>()?;
    let replacement = number
        .checked_add(101)
        .ok_or("numeric_overflow")?
        .to_string();
    bytes.splice(span.start()..span.end(), replacement.bytes());
    let changed = pack(&parts)?;
    verify_one_leaf(original, &changed, index)?;
    Ok(changed)
}
fn referenced_numeric_leaf(original: &[u8]) -> Result<usize> {
    let imported = forms(original)?;
    let fields = ImportedDocumentFields::import(&imported)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    let [target] = evaluated.values() else {
        return Err("one_formula_target_required".into());
    };
    let formula = meanings
        .observations()
        .iter()
        .find_map(|meaning| {
            if meaning.reference_id == target.reference_id
                && let ImportedFieldMeaning::TableFormula { formula, .. } = &meaning.meaning
            {
                return Some(formula);
            }
            None
        })
        .ok_or("original_formula_AST")?;
    let binding = evaluated
        .source_bindings()
        .iter()
        .find(|binding| {
            binding.table_id == target.table_id
                && binding.interpretation == "observed_canonical_decimal_text"
                && references(formula.ast().expression(), binding.coordinate)
        })
        .ok_or("referenced_numeric_binding")?;
    let resolved = imported.source().resolve_anchor(&binding.source_anchor)?;
    if resolved.part().path().as_str() != "Contents/section0.xml" {
        return Err("numeric_part_scope".into());
    }
    let xml = resolved.part().xml().ok_or("numeric_XML")?;
    let cell = resolved.element().ok_or("numeric_cell")?;
    let span = cell.outer_span().ok_or("numeric_cell_span")?;
    xml.elements()
        .iter()
        .position(|element| {
            element.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                && element.name().local_name() == "t"
                && element
                    .outer_span()
                    .is_some_and(|leaf| leaf.start() >= span.start() && leaf.end() <= span.end())
        })
        .ok_or("referenced_numeric_text".into())
}
fn references(expression: &FormulaExpression, cell: CellCoordinate) -> bool {
    match expression {
        FormulaExpression::Decimal { .. } => false,
        FormulaExpression::Cell { reference } => {
            reference.row == cell.row && reference.column == cell.column
        }
        FormulaExpression::Range { range } => {
            cell.row >= range.start.row
                && cell.row <= range.end.row
                && cell.column >= range.start.column
                && cell.column <= range.end.column
        }
        FormulaExpression::Unary { operand, .. } => references(operand, cell),
        FormulaExpression::Binary { left, right, .. } => {
            references(left, cell) || references(right, cell)
        }
        FormulaExpression::Function { arguments, .. } => {
            arguments.iter().any(|argument| references(argument, cell))
        }
    }
}
fn entries(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let mut result = BTreeMap::new();
    for index in 0..reader.entries().len() {
        let name = reader.entries()[index].path.as_str().to_owned();
        if result.insert(name, reader.read_entry(index)?).is_some() {
            return Err("duplicate_part".into());
        }
    }
    Ok(result)
}
fn pack(parts: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    let first = parts.get_key_value("mimetype").ok_or("package_mimetype")?;
    for (name, bytes) in
        std::iter::once(first).chain(parts.iter().filter(|(name, _)| name.as_str() != "mimetype"))
    {
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}
fn verify_one_leaf(original: &[u8], changed: &[u8], index: usize) -> Result<()> {
    let old = entries(original)?;
    let next = entries(changed)?;
    if !old.keys().eq(next.keys()) {
        return Err("derivative_inventory_changed".into());
    }
    let part = "Contents/section0.xml";
    for (path, bytes) in &old {
        if path != part && next.get(path) != Some(bytes) {
            return Err("derivative_other_part_changed".into());
        }
    }
    let old_bytes = old.get(part).ok_or("original_section")?;
    let next_bytes = next.get(part).ok_or("derived_section")?;
    let xml = PreservingXmlDocument::parse(old_bytes)?;
    let newer = PreservingXmlDocument::parse(next_bytes)?;
    if xml.elements().len() != newer.elements().len() {
        return Err("derivative_element_count_changed".into());
    }
    let a = xml.elements().get(index).ok_or("original_numeric_leaf")?;
    let b = newer.elements().get(index).ok_or("derived_numeric_leaf")?;
    if !(a.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
        && a.name().local_name() == "t"
        && a.name() == b.name()
        && a.parent() == b.parent()
        && a.first_child().is_none()
        && b.first_child().is_none())
    {
        return Err("derivative_numeric_shape_changed".into());
    }
    let old_span = a.content_span().ok_or("original_numeric_span")?;
    let new_span = b.content_span().ok_or("derived_numeric_span")?;
    let old_value = &old_bytes[old_span.start()..old_span.end()];
    let new_value = &next_bytes[new_span.start()..new_span.end()];
    let mut reconstructed = old_bytes.clone();
    reconstructed.splice(old_span.start()..old_span.end(), new_value.iter().copied());
    if reconstructed != *next_bytes || old_value == new_value {
        return Err("outside_numeric_leaf_changed".into());
    }
    Ok(())
}
fn ingest(
    p: &Pipeline<'_>,
    raw: &[u8],
    kind: ArtifactKind,
    media: &str,
) -> Result<ArtifactDescriptor> {
    Ok(p.artifacts.ingest(
        p.context,
        IngestRequest {
            bytes: raw.to_vec(),
            kind,
            media_type: MediaType::parse(media)?,
            file_name: FileName::parse("p143-private-test.bin")?,
        },
        now()?,
    )?)
}
fn seed(probe: &mut Probe, p: &Pipeline<'_>, input: &Input) -> Result<RevisionHead> {
    probe.stage = "original_source_AEAD_and_full_IR_baseline";
    let prior = ingest(p, PRIOR, ArtifactKind::Source, "application/octet-stream")?;
    let result = ingest(
        p,
        &input.raw,
        ArtifactKind::Result,
        "application/vnd.hancom.hwpx+zip",
    )?;
    let ir = ingest(
        p,
        &input.graph_bytes,
        ArtifactKind::DocumentIr,
        hwpx_agent_cli::form_stored_provider::full_document::DOCUMENT_IR_MEDIA_TYPE,
    )?;
    let receipt = ingest(
        p,
        RECEIPT,
        ArtifactKind::Receipt,
        "application/octet-stream",
    )?;
    probe.check(
        "actual_locked_source_and_observed_IR_AEAD",
        result.sha256 == ContentDigest::of(&input.raw)
            && ir.sha256 == ContentDigest::of(&input.graph_bytes),
    )?;
    let request = RevisionCommitRequest::new(
        CommitId::generate(),
        p.project,
        branch()?,
        RevisionHead::empty(),
        RevisionId::generate(),
        vec![],
        prior.artifact_id,
        result.artifact_id,
        None,
        ContentDigest::of(b"P143 baseline fixture plan only"),
        RevisionValidationState::Verified,
        ContentDigest::of(b"P143 fixture validation not native"),
        receipt.sha256,
    )?
    .with_full_document_ir(FullDocumentIrBinding {
        artifact_id: ir.artifact_id,
        artifact_sha256: ir.sha256,
        result_package_sha256: result.sha256,
        canonical_graph_sha256: input.graph_sha,
    })?;
    super::worker::commit(&request, &prior.sha256.hex(), receipt.artifact_id)?;
    let context = RevisionRequestContext::new(p.context.tenant_id(), p.context.subject());
    let revisions = RevisionService::new(p.registry.policy_repository().revision_repository());
    let head = revisions.head(&context, p.project, branch()?)?;
    let node = revisions.node(&context, p.project, request.new_revision_id())?;
    probe.check(
        "original_leased_revision_seal_and_IR_link",
        head == RevisionHead::new(Some(request.new_revision_id()), 1)?
            && node.sealed()
            && node.full_document_ir() == request.full_document_ir(),
    )?;
    Ok(head)
}
struct Signer<'a> {
    pair: &'a Ed25519KeyPair,
    calls: AtomicUsize,
}
impl FormulaApprovalSigner for Signer<'_> {
    fn key_id(&self) -> &'static str {
        "p143-ephemeral"
    }
    fn sign(&self, raw: &[u8]) -> std::result::Result<[u8; 64], FormulaIssuerError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        self.pair
            .sign(raw)
            .as_ref()
            .try_into()
            .map_err(|_| FormulaIssuerError::Signature)
    }
}
struct Capture<F> {
    registrar: PostgresFormulaPolicyRegistrar,
    callback: F,
    approval: Mutex<
        Option<std::result::Result<FormulaIssuerProvisioningReceipt, FormulaIssuerWorkflowFailure>>,
    >,
}
impl<F> FormulaPolicyRegistrationRepository for Capture<F>
where
    F: Fn(
            &PolicyReadScope,
            &FormulaPolicyRegistrationRecord,
        )
            -> std::result::Result<FormulaIssuerProvisioningReceipt, FormulaIssuerWorkflowFailure>
        + Send
        + Sync,
{
    fn register_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
    ) -> std::result::Result<SourcePolicyVersion, FormulaPolicyRegistrationError> {
        let registered = self.registrar.register_formula_policy(scope, record)?;
        *self
            .approval
            .lock()
            .map_err(|_| FormulaPolicyRegistrationError::Repository)? =
            Some((self.callback)(scope, record));
        Ok(registered)
    }
}
pub(super) fn run(probe: &mut Probe, p: &Pipeline<'_>, input: &Input) -> Result<()> {
    eprintln!("P146_STAGE:source_begin");
    let head = seed(probe, p, input)?;
    let context = RevisionRequestContext::new(p.context.tenant_id(), p.context.subject());
    let revisions = RevisionService::new(p.registry.policy_repository().revision_repository());
    let provider = StoredFormProvider::bind(
        p.artifacts,
        &revisions,
        p.context,
        &context,
        p.project,
        branch()?,
        DocumentId::parse(DOCUMENT)?,
    )?;
    probe.stage = "source_derived_policy_and_original_SQL21_registration";
    let source = provider.import_actual_forms(head, now()?)?;
    let fields = source.import_field_ranges(&provider, now()?)?;
    let meanings = fields.import_semantics(&provider, now()?)?;
    let decisions: Vec<_> = meanings
        .observations()
        .iter()
        .filter(|m| matches!(m.meaning, ImportedFieldMeaning::TableFormula { .. }))
        .map(|m| FormulaPolicyDecision::new(m.reference_id.clone(), true))
        .collect();
    probe.check(
        "actual_source_formula_targets_not_caller_AST",
        !decisions.is_empty(),
    )?;
    let clock = SystemFormulaIssuerClock;
    let provisioner = RegistryFormulaProvisioner::new(
        p.registry,
        p.writes,
        p.policies,
        p.artifacts,
        p.context,
        &clock,
    );
    let signer = Signer {
        pair: p.pair,
        calls: AtomicUsize::new(0),
    };
    let capture = Capture {
        registrar: PostgresFormulaPolicyRegistrar::new(p.registry.policy_repository()),
        callback: |scope: &PolicyReadScope,
                   record: &FormulaPolicyRegistrationRecord|
         -> std::result::Result<
            FormulaIssuerProvisioningReceipt,
            FormulaIssuerWorkflowFailure,
        > { provisioner.issue_approval(scope, record, &signer, 0, 60) },
        approval: Mutex::new(None),
    };
    let policy = source
        .prepare_formula_policy_registration(&provider, &decisions, 0, now()?)?
        .register(&provider, &capture, now()?)?;
    probe.check(
        "original_generated_policy_SQL_CAS_and_readback",
        policy.generation == 1,
    )?;
    probe.stage = "original_Ed25519_approval_AEAD_SQL_commit_readback";
    let approval = capture
        .approval
        .lock()
        .map_err(|_| "capture_lock")?
        .take()
        .ok_or("capture_missing")??;
    probe.check(
        "original_signature_approval_SQL_commit_readback",
        approval.generation() == 1
            && signer.calls.load(Ordering::SeqCst) == 1
            && approval.artifact() != policy.artifact,
    )?;
    verify_consumer(
        probe,
        p,
        input,
        &provider,
        head,
        &LiveApprovalBinding {
            head,
            policy_version: policy.version,
            approval_version: approval.version(),
            generation: approval.generation(),
        },
    )
}
struct LiveApprovalBinding {
    head: RevisionHead,
    policy_version: uuid::Uuid,
    approval_version: uuid::Uuid,
    generation: u64,
}
type Provider<'a> = StoredFormProvider<
    'a,
    super::LocalPostgresMetadataRepository,
    super::ProbeBlobStore,
    super::ProbeRootScanner,
    revision_service::postgres::LocalPostgresRevisionRepository,
>;
fn expected(input: &Input) -> Result<(Vec<u8>, &'static str)> {
    let imported = forms(&input.raw)?;
    let fields = ImportedDocumentFields::import(&imported)?;
    let semantics = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluation = ImportedSourceFormulaEvaluation::import(&semantics)?;
    match evaluation.lower_results(&input.raw, WriterLimits::default()) {
        Ok(output) => Ok((output.with_verified_bytes(<[u8]>::to_vec)?, "changed")),
        Err(hwpx_package::document_import::fields::semantics::evaluation::output::FormulaResultOutputError::NoChange) => {
            evaluation.verify_source(&input.raw)?;
            Ok((input.raw.clone(), "unchanged"))
        }
        Err(error) => Err(Box::new(error)),
    }
}
fn verify_consumer(
    probe: &mut Probe,
    p: &Pipeline<'_>,
    input: &Input,
    provider: &Provider<'_>,
    head: RevisionHead,
    binding: &LiveApprovalBinding,
) -> Result<()> {
    eprintln!("P146_STAGE:consumer_begin");
    let approvals = RegistryFormulaApprovalProvider::new(p.registry);
    let clock = SystemFormulaIssuerClock;
    let trust = RegistryFormulaTrustProvider::new(p.registry, p.artifacts, p.context, &clock);
    let deps = FormulaIssuerDependencies::new(p.policies, &approvals, &trust, &clock);
    let raw = serde_json::to_vec(
        &serde_json::json!({"schema_version":PRODUCT_OPERATION_REQUEST_SCHEMA,
        "idempotency_key":"P143-private-owned-test","project_id":p.project.public_id(),"document_id":DOCUMENT,
        "base_revision":head.revision_id().ok_or("head_missing")?.public_id(),"expected_head_generation":head.generation(),
        "expected_source_package_sha256":ContentDigest::of(&input.raw),"plan_id":"signed-formula-plan",
        "operation":{"kind":"recalculate_table_formulas"}}),
    )?;
    let metadata = p.metadata;
    let before = metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested")
        .count();
    probe.stage = "original_mandatory_signature_consumer";
    let prepared = StoredProductRequest::prepare_formula_with_issuer(provider, &deps, &raw)
        .map_err(consumer_error)?;
    probe.stage = "independent_evaluator_expected_outcome";
    let (wanted, expected_outcome) = expected(input)?;
    let actual_outcome = match &prepared.receipt().product.product.formula {
        FormulaPreparationReceipt::Changed { .. } => "changed",
        FormulaPreparationReceipt::Unchanged { .. } => "unchanged",
    };
    probe.formula_outcome = Some(actual_outcome);
    probe.check(
        "original_consumer_candidate_equals_independent_evaluator",
        actual_outcome == expected_outcome
            && prepared.with_verified_bytes(provider, &deps, <[u8]>::to_vec)? == wanted,
    )?;
    probe.check(
        "fresh_consumer_exact_without_cached_trust",
        prepared.with_verified_bytes(provider, &deps, <[u8]>::to_vec)? == wanted,
    )?;
    probe.check(
        "full_product_route_not_falsely_enabled",
        route_denial_matches(
            actual_outcome,
            prepared.require_current_product_route(provider, &deps),
        ),
    )?;
    let after = metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested")
        .count();
    let ctx = RevisionRequestContext::new(p.context.tenant_id(), p.context.subject());
    let revisions = RevisionService::new(p.registry.policy_repository().revision_repository());
    probe.check(
        "consumer_preserves_head_and_artifact_ingest_count",
        before == after && revisions.head(&ctx, p.project, branch()?)? == head,
    )?;
    // P150 owned-local extension: retain original fresh signed authority checks.
    if p.blobs.is_durable() {
        p.blobs.reopen()?;
        probe.check("durable_signed_consumer_fresh_handle_whole_candidate_exact",
            prepared.with_verified_bytes(provider,&deps,<[u8]>::to_vec)? == wanted)?;
        probe.check("durable_signed_consumer_no_head_or_ingest_change",
            metadata.audit_events()?.iter().filter(|e| e.event == "artifact.ingested").count() == after
                && revisions.head(&ctx,p.project,branch()?)? == head)?;
    }
    // End P150 owned-local extension.
    // P151 negative-controls extension: all original live negatives execute first.
    verify_live_approval(probe, p, provider, &prepared, &raw, &wanted, binding)?;
    if p.blobs.is_durable() {
        super::durable_negative::exercise(probe, metadata, p.blobs, p.context, || {
            Ok(revisions.head(&ctx, p.project, branch()?)? == head)
        })?;
    }
    Ok(())
    // End P151 negative-controls extension.
}

fn live_denial_matches<T>(
    result: &std::result::Result<T, hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::product::IssuerFormulaProductError>,
) -> bool {
    use hwpx_agent_cli::{
        form_product_request::stored_operations::policy::PolicyFormulaProductError,
        form_stored_provider::actual_import::source_policy::formulas::{
            StoredFormulaPolicyError, issuer::product::IssuerFormulaProductError,
        },
    };
    matches!(
        result,
        Err(IssuerFormulaProductError::Product(
            PolicyFormulaProductError::Policy(StoredFormulaPolicyError::Repository)
        ))
    )
}

fn verify_live_approval(
    probe: &mut Probe,
    p: &Pipeline<'_>,
    provider: &Provider<'_>,
    prepared: &hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::product::PreparedIssuerFormulaProduct,
    raw: &[u8],
    wanted: &[u8],
    binding: &LiveApprovalBinding,
) -> Result<()> {
    if std::env::var_os("P148_LIVE_CASE").is_some() {
        return verify_live_authority(probe, p, provider, prepared, raw, wanted, binding);
    }
    match std::env::var("P146_LIVE_CASE") {
        Err(std::env::VarError::NotPresent) => return Ok(()),
        Ok(value) if value == "approval" => {}
        _ => return Err("live_case_not_allowlisted".into()),
    }
    eprintln!("P146_STAGE:live_begin");
    let ctx = RevisionRequestContext::new(p.context.tenant_id(), p.context.subject());
    let request = FormulaApprovalReadRequest::new(
        SourceFormulaPolicyReadRequest::new(p.project, branch()?, DOCUMENT.into(), binding.head)?,
        binding.policy_version,
        1,
    )?;
    let before = p.registry.read_approval(&ctx, &request)?;
    probe.check(
        "live_SQL_approval_exact_current_binding",
        before.version == binding.approval_version
            && before.generation == binding.generation
            && before.generation == 1,
    )?;
    let connect = || {
        LocalPostgresFormulaRegistryManagementRepository::connect(
            &super::config("p141_approval")?,
            ctx.clone(),
            RegistryManagementCapability::Approval,
        )
        .map_err(|error| -> Box<dyn std::error::Error> { Box::new(error) })
    };
    eprintln!("P146_STAGE:connect_first_begin");
    let first = connect()?;
    eprintln!("P146_STAGE:connect_second_begin");
    let second = connect()?;
    eprintln!("P146_STAGE:stale_CAS_begin");
    let stale = FormulaApprovalRevocation::new(
        p.project,
        branch()?,
        DOCUMENT.into(),
        binding.policy_version,
        binding.approval_version,
        2,
    )?;
    probe.check(
        "live_SQL_stale_generation_rejected_without_mutation",
        matches!(
            first.revoke_approval(&ctx, &stale),
            Err(revision_service::RevisionError::RepositoryFailure)
        ) && p.registry.read_approval(&ctx, &request)? == before,
    )?;
    let approvals = RegistryFormulaApprovalProvider::new(p.registry);
    let clock = SystemFormulaIssuerClock;
    let trust = RegistryFormulaTrustProvider::new(p.registry, p.artifacts, p.context, &clock);
    let deps = FormulaIssuerDependencies::new(p.policies, &approvals, &trust, &clock);
    probe.check(
        "live_SQL_consumer_survives_rejected_CAS",
        prepared.with_verified_bytes(provider, &deps, <[u8]>::to_vec)? == wanted,
    )?;
    eprintln!("P146_STAGE:race_begin");
    let revoke = FormulaApprovalRevocation::new(
        p.project,
        branch()?,
        DOCUMENT.into(),
        binding.policy_version,
        binding.approval_version,
        binding.generation,
    )?;
    revocation_race(probe, &first, &second, &ctx, &revoke, binding)?;
    probe.check(
        "live_SQL_revoked_approval_read_denied",
        matches!(
            p.registry.read_approval(&ctx, &request),
            Err(revision_service::RevisionError::InvalidRequest)
        ),
    )?;
    eprintln!("P146_STAGE:denied_callback_begin");
    let callback_calls = AtomicUsize::new(0);
    let denied = prepared.with_verified_bytes(provider, &deps, |_| {
        callback_calls.fetch_add(1, Ordering::SeqCst);
    });
    probe.check(
        "live_SQL_prepared_candidate_denied_callback_zero",
        live_denial_matches(&denied) && callback_calls.load(Ordering::SeqCst) == 0,
    )?;
    probe.check(
        "live_SQL_fresh_prepare_denied",
        live_denial_matches(&StoredProductRequest::prepare_formula_with_issuer(
            provider, &deps, raw,
        )),
    )?;
    probe.check(
        "live_SQL_route_denied_not_merely_unqualified",
        live_denial_matches(&prepared.require_current_product_route(provider, &deps)),
    )?;
    let revisions = RevisionService::new(p.registry.policy_repository().revision_repository());
    probe.check(
        "live_SQL_revocation_preserves_revision_head",
        revisions.head(&ctx, p.project, branch()?)? == binding.head,
    )
}

fn verify_live_authority(
    probe: &mut Probe,
    p: &Pipeline<'_>,
    provider: &Provider<'_>,
    prepared: &hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::product::PreparedIssuerFormulaProduct,
    raw: &[u8],
    wanted: &[u8],
    binding: &LiveApprovalBinding,
) -> Result<()> {
    let case = std::env::var("P148_LIVE_CASE")?;
    if !matches!(case.as_str(), "trust" | "policy") || std::env::var_os("P146_LIVE_CASE").is_some()
    {
        return Err("authority_case_not_allowlisted".into());
    }
    let ctx = RevisionRequestContext::new(p.context.tenant_id(), p.context.subject());
    let request =
        SourceFormulaPolicyReadRequest::new(p.project, branch()?, DOCUMENT.into(), binding.head)?;
    let policy_before = p
        .registry
        .policy_repository()
        .read_current(&ctx, &request)?;
    let root_before = p.registry.read_trust(&ctx, p.project)?;
    let approval = p.registry.read_approval(
        &ctx,
        &FormulaApprovalReadRequest::new(
            SourceFormulaPolicyReadRequest::new(
                p.project,
                branch()?,
                DOCUMENT.into(),
                binding.head,
            )?,
            binding.policy_version,
            1,
        )?,
    )?;
    probe.check(
        "live_authority_exact_current_binding",
        root_before.generation == 4
            && policy_before.version == binding.policy_version
            && policy_before.generation == 1
            && approval.version == binding.approval_version
            && approval.generation == binding.generation
            && approval.trust_version == root_before.version
            && approval.trust_generation == root_before.generation,
    )?;
    let source_before = p
        .artifacts
        .download(p.context, policy_before.source_result, now()?)?;
    let ingests_before = p
        .metadata
        .audit_events()?
        .iter()
        .filter(|event| event.event == "artifact.ingested")
        .count();
    verify_authority_stale(probe, p, binding, &case)?;
    let approvals = RegistryFormulaApprovalProvider::new(p.registry);
    let clock = SystemFormulaIssuerClock;
    let trust = RegistryFormulaTrustProvider::new(p.registry, p.artifacts, p.context, &clock);
    let deps = FormulaIssuerDependencies::new(p.policies, &approvals, &trust, &clock);
    probe.check(
        "live_authority_consumer_survives_rejected_CAS",
        prepared.with_verified_bytes(provider, &deps, <[u8]>::to_vec)? == wanted,
    )?;
    let source = provider.import_actual_forms(binding.head, now()?)?;
    let cached_policy = source.bind_stored_formula_policy(provider, p.policies, now()?)?;
    verify_authority_revoke(probe, p, provider, binding, &case)?;
    verify_authority_denials(probe, p, provider, prepared, raw)?;
    let policy_state_exact = if case == "trust" {
        cached_policy.verify(&source, provider, p.policies, now()?)? == *cached_policy.receipt()
    } else {
        matches!(cached_policy.verify(&source, provider, p.policies, now()?),
            Err(hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::StoredFormulaPolicyError::Repository))
    };
    probe.check(
        "live_authority_cached_policy_state_exact",
        policy_state_exact,
    )?;
    verify_authority_preservation(
        probe,
        p,
        binding,
        &policy_before,
        &root_before,
        &source_before,
        ingests_before,
    )
}

fn verify_authority_preservation(
    probe: &mut Probe,
    p: &Pipeline<'_>,
    binding: &LiveApprovalBinding,
    policy_before: &revision_service::postgres::source_formula_policy::SourceFormulaPolicyRecord,
    root_before: &revision_service::postgres::source_formula_policy::issuer_registry::FormulaIssuerTrustRecord,
    source_before: &[u8],
    ingests_before: usize,
) -> Result<()> {
    let ctx = RevisionRequestContext::new(p.context.tenant_id(), p.context.subject());
    let request =
        SourceFormulaPolicyReadRequest::new(p.project, branch()?, DOCUMENT.into(), binding.head)?;
    probe.check(
        "live_authority_original_source_bytes_preserved",
        p.artifacts
            .download(p.context, policy_before.source_result, now()?)?
            == source_before,
    )?;
    let revisions = RevisionService::new(p.registry.policy_repository().revision_repository());
    probe.check(
        "live_authority_revision_head_preserved",
        revisions.head(&ctx, p.project, branch()?)? == binding.head,
    )?;
    let ingests_after = p
        .metadata
        .audit_events()?
        .iter()
        .filter(|event| event.event == "artifact.ingested")
        .count();
    probe.check(
        "live_authority_artifact_ingest_count_preserved",
        ingests_after == ingests_before,
    )?;
    let unrelated_exact = if std::env::var("P148_LIVE_CASE")? == "trust" {
        p.registry
            .policy_repository()
            .read_current(&ctx, &request)?
            == *policy_before
    } else {
        p.registry.read_trust(&ctx, p.project)? == *root_before
    };
    probe.check(
        "live_authority_unrelated_authority_preserved",
        unrelated_exact,
    )
}

fn verify_authority_stale(
    probe: &mut Probe,
    p: &Pipeline<'_>,
    binding: &LiveApprovalBinding,
    case: &str,
) -> Result<()> {
    let ctx = RevisionRequestContext::new(p.context.tenant_id(), p.context.subject());
    let unchanged = if case == "trust" {
        let before = p.registry.read_trust(&ctx, p.project)?;
        let manager = LocalPostgresFormulaRegistryManagementRepository::connect(
            &super::config("p141_root")?,
            ctx.clone(),
            RegistryManagementCapability::Trust,
        )?;
        let stale = FormulaIssuerTrustRevocation::new(p.project, before.version, 5)?;
        matches!(
            manager.revoke_trust(&ctx, &stale),
            Err(revision_service::RevisionError::RepositoryFailure)
        ) && p.registry.read_trust(&ctx, p.project)? == before
    } else {
        let repository = p.registry.policy_repository();
        let request = SourceFormulaPolicyReadRequest::new(
            p.project,
            branch()?,
            DOCUMENT.into(),
            binding.head,
        )?;
        let before = repository.read_current(&ctx, &request)?;
        let stale = SourceFormulaPolicyRevocationRequest::new(
            p.project,
            branch()?,
            DOCUMENT.into(),
            binding.policy_version,
            2,
        )?;
        matches!(
            repository.revoke_policy(&ctx, &stale),
            Err(revision_service::RevisionError::RepositoryFailure)
        ) && repository.read_current(&ctx, &request)? == before
    };
    probe.check("live_authority_stale_CAS_preserves_binding", unchanged)
}

fn verify_authority_revoke(
    probe: &mut Probe,
    p: &Pipeline<'_>,
    provider: &Provider<'_>,
    binding: &LiveApprovalBinding,
    case: &str,
) -> Result<()> {
    let ctx = RevisionRequestContext::new(p.context.tenant_id(), p.context.subject());
    if case == "trust" {
        let before = p.registry.read_trust(&ctx, p.project)?;
        let manager = LocalPostgresFormulaRegistryManagementRepository::connect(
            &super::config("p141_root")?,
            ctx.clone(),
            RegistryManagementCapability::Trust,
        )?;
        let request =
            FormulaIssuerTrustRevocation::new(p.project, before.version, before.generation)?;
        let receipt = manager.revoke_trust(&ctx, &request)?;
        probe.check(
            "live_authority_revoke_commit_ack_exact",
            receipt.version() == before.version
                && receipt.generation() == 4
                && receipt.tenant() == ctx.tenant_id()
                && receipt.project() == p.project
                && receipt.actor() == ctx.subject()
                && receipt.action() == FormulaRegistryManagementAction::RevokeTrust,
        )?;
        probe.check(
            "live_authority_duplicate_revoke_denied",
            matches!(
                manager.revoke_trust(&ctx, &request),
                Err(revision_service::RevisionError::RepositoryFailure)
            ),
        )?;
        probe.check(
            "live_authority_named_read_denied",
            matches!(
                p.registry.read_trust(&ctx, p.project),
                Err(revision_service::RevisionError::InvalidRequest)
            ),
        )
    } else {
        let repository = p.registry.policy_repository();
        let request = SourceFormulaPolicyReadRequest::new(
            p.project,
            branch()?,
            DOCUMENT.into(),
            binding.head,
        )?;
        let before = repository.read_current(&ctx, &request)?;
        let revoker = PostgresFormulaPolicyRevoker::new(repository.clone());
        let source = provider.import_actual_forms(binding.head, now()?)?;
        let policy = source.bind_stored_formula_policy(provider, &revoker, now()?)?;
        let receipt = policy.revoke(&source, provider, &revoker, now()?)?;
        probe.check(
            "live_authority_revoke_commit_ack_exact",
            receipt.version == binding.policy_version
                && receipt.generation == 1
                && receipt.policy_sha256 == before.policy_digest,
        )?;
        let duplicate = SourceFormulaPolicyRevocationRequest::new(
            p.project,
            branch()?,
            DOCUMENT.into(),
            binding.policy_version,
            1,
        )?;
        probe.check(
            "live_authority_duplicate_revoke_denied",
            matches!(
                repository.revoke_policy(&ctx, &duplicate),
                Err(revision_service::RevisionError::RepositoryFailure)
            ),
        )?;
        probe.check(
            "live_authority_named_read_denied",
            matches!(
                repository.read_current(&ctx, &request),
                Err(revision_service::RevisionError::InvalidRequest)
            ),
        )
    }
}

fn verify_authority_denials(
    probe: &mut Probe,
    p: &Pipeline<'_>,
    provider: &Provider<'_>,
    prepared: &hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::product::PreparedIssuerFormulaProduct,
    raw: &[u8],
) -> Result<()> {
    let approvals = RegistryFormulaApprovalProvider::new(p.registry);
    let clock = SystemFormulaIssuerClock;
    let trust = RegistryFormulaTrustProvider::new(p.registry, p.artifacts, p.context, &clock);
    let deps = FormulaIssuerDependencies::new(p.policies, &approvals, &trust, &clock);
    probe.check(
        "live_authority_prepared_verify_denied",
        live_denial_matches(&prepared.verify(provider, &deps)),
    )?;
    let callbacks = AtomicUsize::new(0);
    let denied = prepared.with_verified_bytes(provider, &deps, |_| {
        callbacks.fetch_add(1, Ordering::SeqCst);
    });
    probe.check(
        "live_authority_prepared_callback_denied_zero",
        live_denial_matches(&denied) && callbacks.load(Ordering::SeqCst) == 0,
    )?;
    probe.check(
        "live_authority_fresh_prepare_denied",
        live_denial_matches(&StoredProductRequest::prepare_formula_with_issuer(
            provider, &deps, raw,
        )),
    )?;
    probe.check(
        "live_authority_route_denied_not_merely_unqualified",
        live_denial_matches(&prepared.require_current_product_route(provider, &deps)),
    )
}

fn revocation_race(
    probe: &mut Probe,
    first: &LocalPostgresFormulaRegistryManagementRepository,
    second: &LocalPostgresFormulaRegistryManagementRepository,
    ctx: &RevisionRequestContext,
    revoke: &FormulaApprovalRevocation,
    binding: &LiveApprovalBinding,
) -> Result<()> {
    let barrier = std::sync::Barrier::new(3);
    probe.stage = "live_SQL_duplicate_revocation_race";
    let results = std::thread::scope(|scope| {
        let one = scope.spawn(|| {
            barrier.wait();
            first.revoke_approval(ctx, revoke)
        });
        let two = scope.spawn(|| {
            barrier.wait();
            second.revoke_approval(ctx, revoke)
        });
        barrier.wait();
        [one.join(), two.join()]
    });
    eprintln!("P146_STAGE:race_joined");
    let (mut commits, mut denials) = (0, 0);
    for result in results {
        match result.map_err(|_| "live_SQL_race_thread_failed")? {
            Ok(receipt)
                if receipt.version() == binding.approval_version && receipt.generation() == 1 =>
            {
                commits += 1;
            }
            Err(revision_service::RevisionError::RepositoryFailure) => denials += 1,
            _ => return Err("live_SQL_race_unexpected_result".into()),
        }
    }
    probe.check(
        "live_SQL_revocation_race_one_commit_one_denial",
        commits == 1 && denials == 1,
    )
}

fn route_denial_matches(
    outcome: &str,
    result: std::result::Result<(), hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::product::IssuerFormulaProductError>,
) -> bool {
    use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductOperationError as Operation, policy::PolicyFormulaProductError as Policy};
    use hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::product::IssuerFormulaProductError as Issuer;
    use hwpx_agent_cli::form_stored_provider::actual_import::field_ranges::semantics::evaluation::output::{StoredFormulaOutputError as Output, compiler::StoredFormulaCompilerError as Compiler};
    matches!(
        (outcome, result),
        (
            "unchanged",
            Err(Issuer::Product(Policy::Product(
                Operation::RouteUnqualified
            )))
        ) | (
            "changed",
            Err(Issuer::Product(Policy::Product(Operation::Compiler(
                Compiler::Source(Output::RouteUnqualified)
            ))))
        )
    )
}

fn consumer_error(
    error: hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::product::IssuerFormulaProductError,
) -> Box<dyn std::error::Error> {
    use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductOperationError as Operation, policy::PolicyFormulaProductError as Policy};
    use hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::product::IssuerFormulaProductError as Issuer;
    let code = match &error {
        Issuer::Issuer(_) => "ISSUER",
        Issuer::Drift => "ISSUER_DRIFT",
        Issuer::Product(Policy::Kind) => "KIND",
        Issuer::Product(Policy::Drift) => "PRODUCT_DRIFT",
        Issuer::Product(Policy::Policy(_)) => "POLICY",
        Issuer::Product(Policy::Product(Operation::Request(_))) => "REQUEST",
        Issuer::Product(Policy::Product(Operation::Provider(_))) => "PROVIDER",
        Issuer::Product(Policy::Product(Operation::Source(_))) => "SOURCE",
        Issuer::Product(Policy::Product(Operation::Compiler(_))) => "COMPILER",
        Issuer::Product(Policy::Product(_)) => "ORIGINAL_PRODUCT",
    };
    eprintln!("P143_CONSUMER_ERROR code={code}");
    Box::new(error)
}

#[cfg(test)]
mod source_index_tests {
    use super::source_index;

    #[test]
    fn default_is_original_index_zero() {
        assert_eq!(source_index(None).ok(), Some(0));
    }
    #[test]
    fn accepts_all_exact_manifest_indices() {
        for index in 0..36 {
            assert_eq!(source_index(Some(&index.to_string())).ok(), Some(index));
        }
    }
    #[test]
    fn rejects_outside_manifest_range() {
        for value in ["36", "99"] {
            assert!(source_index(Some(value)).is_err());
        }
    }
    #[test]
    fn rejects_noncanonical_or_noninteger_values() {
        for value in ["", "-1", "+1", " 1", "1 ", "01", "1.0", "a", "\u{1f34e}"] {
            assert!(source_index(Some(value)).is_err());
        }
    }
    #[test]
    fn rejects_oversized_input_without_overflow() {
        assert!(source_index(Some("1844674407370955161600000000")).is_err());
    }
}

#[cfg(test)]
mod route_tests {
    use super::route_denial_matches;
    use hwpx_agent_cli::form_product_request::stored_operations::{
        StoredProductOperationError as Operation, policy::PolicyFormulaProductError as Policy,
    };
    use hwpx_agent_cli::form_stored_provider::actual_import::{
        field_ranges::semantics::evaluation::output::{
            StoredFormulaOutputError as Output, compiler::StoredFormulaCompilerError as Compiler,
        },
        source_policy::formulas::{
            StoredFormulaPolicyError,
            issuer::{FormulaIssuerError, product::IssuerFormulaProductError as Issuer},
        },
    };

    fn unchanged() -> Issuer {
        Issuer::Product(Policy::Product(Operation::RouteUnqualified))
    }
    fn changed() -> Issuer {
        Issuer::Product(Policy::Product(Operation::Compiler(Compiler::Source(
            Output::RouteUnqualified,
        ))))
    }
    #[test]
    fn accepts_only_exact_unchanged_route_denial() {
        assert!(route_denial_matches("unchanged", Err(unchanged())));
    }
    #[test]
    fn accepts_only_exact_changed_route_denial() {
        assert!(route_denial_matches("changed", Err(changed())));
    }
    #[test]
    fn rejects_signature_and_policy_failures_as_route_success() {
        assert!(!route_denial_matches(
            "unchanged",
            Err(Issuer::Issuer(FormulaIssuerError::Signature))
        ));
        assert!(!route_denial_matches(
            "changed",
            Err(Issuer::Product(Policy::Policy(
                StoredFormulaPolicyError::Repository
            )))
        ));
    }
    #[test]
    fn rejects_wrong_outcome_route_branch() {
        assert!(!route_denial_matches("changed", Err(unchanged())));
        assert!(!route_denial_matches("unchanged", Err(changed())));
    }
    #[test]
    fn rejects_product_route_success() {
        assert!(!route_denial_matches("changed", Ok(())));
        assert!(!route_denial_matches("unchanged", Ok(())));
    }
    #[test]
    fn rejects_unknown_outcome() {
        assert!(!route_denial_matches("unknown", Err(unchanged())));
    }
}
