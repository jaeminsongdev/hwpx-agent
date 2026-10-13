use domain_ir::{form_input::*, *};
use hwpx_agent_cli::form_value_preparation::*;
use hwpx_package::{native_form_value_output::*, *};
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use std::{error::Error, fs, io::Cursor, path::Path};
type TestResult = Result<(), Box<dyn Error>>;
const CAPTURE: &str = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx";
const CAPTURE_SHA: &str = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7";

struct Fixture {
    source: Vec<u8>,
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
}
impl Fixture {
    fn context(&self) -> Result<FormValueContext<'_>, FormValuePreparationError> {
        FormValueContext::bind(
            &self.source,
            &self.map,
            &self.policies,
            FormValuePreparationLimits::bounded_default()?,
        )
    }
    fn request(&self, value: &str) -> Result<(Value, FormInputAccessPolicy), Box<dyn Error>> {
        let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
        let observed = NativeFormValueReader::read(
            &self.source,
            &self.map,
            &self.policies,
            limits,
            NativeFormPackageLimits::default(),
        )?;
        let draft: FormDocumentStateDraft =
            serde_json::from_slice(&observed.state().canonical_json(limits)?)?;
        let access = FormInputAccessPolicy {
            document_protection_sha256: draft.document_protection_sha256,
            input_allowed: true,
        };
        let req = FormInputRequestDraft {
            schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("product-form-request")?,
            expected_source_state_sha256: observed.state().canonical_sha256(limits)?,
            expected_document_flow_sha256: observed.native_v1().document_flow_sha256().into(),
            access: access.clone(),
            operation: FormInputOperation::SetValues {
                assignments: vec![FormInputAssignment {
                    target: self.policies[0].identity.clone(),
                    value: FormInputValue::Text {
                        value: value.into(),
                    },
                }],
            },
        };
        Ok((serde_json::to_value(req)?, access))
    }
}
fn fixture() -> Result<Fixture, Box<dyn Error>> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let path = root.join(CAPTURE);
    for ancestor in path.ancestors() {
        let m = fs::symlink_metadata(ancestor)?;
        if m.file_type().is_symlink() {
            return Err("fixture link".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("fixture reparse".into());
            }
        }
    }
    if fs::metadata(&path)?.len() != 14_556 {
        return Err("fixture size".into());
    }
    let source = fs::read(&path)?;
    if source.len() != 14_556 || hex::encode(Sha256::digest(&source)) != CAPTURE_SHA {
        return Err("fixture digest".into());
    }
    let mut zip = BoundedZipReader::open(Cursor::new(&source), PackageLimits::default())?;
    let entry = zip
        .entries()
        .iter()
        .find(|p| p.path.as_str() == "Contents/section0.xml")
        .ok_or("section")?
        .index;
    let section = zip.read_entry(entry)?;
    let xml = PreservingXmlDocument::parse(&section)?;
    let paragraphs = xml
        .elements()
        .iter()
        .filter(|e| {
            e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                && e.name().local_name() == "p"
        })
        .count();
    let map = NativeFormPackageMap {
        sections: vec![NativeFormPackageSectionMap {
            part: "Contents/section0.xml".into(),
            map: NativeFormHwpxMap {
                paragraph_ids: (0..paragraphs)
                    .map(|i| LogicalId::parse(format!("actual-p-{i}")))
                    .collect::<Result<_, _>>()?,
                component_controls: vec![FormControlIdentity {
                    logical_control_id: LogicalId::parse("actual-input-component")?,
                    native_object_id: 90001,
                }],
            },
        }],
    };
    let observed =
        NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
    let c = observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .next()
        .ok_or("control")?;
    let NativeFormObservedPayload::Text {
        value,
        multi_line,
        password_character,
        native_max_length,
        scroll_bars,
        tab_key_behavior,
        number_only,
        read_only,
        alignment,
    } = &c.payload
    else {
        return Err("text".into());
    };
    let policies = vec![NativeFormPackagePolicy {
        identity: c.component_identity.clone(),
        payload: FormControlPayload::Text {
            value: value.clone(),
            default_value: "caller-default".into(),
            validation: FormTextValidation {
                required: false,
                minimum_characters: 0,
                maximum_characters: None,
                external_validator_sha256: None,
            },
            multi_line: *multi_line,
            password_character: password_character.clone(),
            native_max_length: *native_max_length,
            scroll_bars: *scroll_bars,
            tab_key_behavior: *tab_key_behavior,
            number_only: *number_only,
            read_only: *read_only,
            alignment: *alignment,
        },
    }];
    Ok(Fixture {
        source,
        map,
        policies,
    })
}

use hwpx_agent_cli::form_value_operation::*;

fn checked_fixture(name: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let path = root.join(name);
    for ancestor in path.ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        if metadata.file_type().is_symlink() {
            return Err("fixture link".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("fixture reparse".into());
            }
        }
    }
    if !fs::metadata(&path)?.is_file() || fs::metadata(&path)?.len() > 1024 * 1024 {
        return Err("fixture bound".into());
    }
    Ok(fs::read(path)?)
}
fn matrix(label: &str) -> Result<(Fixture, Vec<u8>), Box<dyn Error>> {
    let manifest = checked_fixture("fixture-manifest.json")?;
    if hex::encode(Sha256::digest(&manifest))
        != "8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e"
    {
        return Err("manifest identity".into());
    }
    let manifest: Value = serde_json::from_slice(&manifest)?;
    let row = manifest["cases"]
        .as_array()
        .ok_or("cases")?
        .iter()
        .find(|r| r["case"] == label)
        .ok_or("case")?;
    let source = checked_fixture(row["source"]["path"].as_str().ok_or("source")?)?;
    let output = checked_fixture(row["output"]["path"].as_str().ok_or("output")?)?;
    for (value, key) in [(&source, "source"), (&output, "output")] {
        if hex::encode(Sha256::digest(value)) != row[key]["sha256"].as_str().ok_or("sha")?
            || u64::try_from(value.len())? != row[key]["bytes"].as_u64().ok_or("bytes")?
        {
            return Err("fixture identity".into());
        }
    }
    let map = NativeFormPackageMap {
        sections: (0..2)
            .map(|section| -> Result<_, Box<dyn Error>> {
                Ok(NativeFormPackageSectionMap {
                    part: format!("Contents/section{section}.xml"),
                    map: NativeFormHwpxMap {
                        paragraph_ids: (0..2)
                            .map(|i| LogicalId::parse(format!("p40-section{section}-p{i}")))
                            .collect::<Result<_, _>>()?,
                        component_controls: (if section == 0 {
                            vec![0, 1, 2, 3, 4]
                        } else {
                            vec![5]
                        })
                        .into_iter()
                        .map(|i| -> Result<_, Box<dyn Error>> {
                            Ok(FormControlIdentity {
                                logical_control_id: LogicalId::parse(format!("p40-control{i}"))?,
                                native_object_id: 90001 + i,
                            })
                        })
                        .collect::<Result<_, _>>()?,
                    },
                })
            })
            .collect::<Result<_, _>>()?,
    };
    let native = NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
    let policies = native
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(matrix_policy)
        .collect::<Result<Vec<_>, _>>()?;
    Ok((
        Fixture {
            source,
            map,
            policies,
        },
        output,
    ))
}
fn text_payload(c: &NativeFormControlObservation) -> Result<FormControlPayload, Box<dyn Error>> {
    let NativeFormObservedPayload::Text {
        value,
        multi_line,
        password_character,
        native_max_length,
        scroll_bars,
        tab_key_behavior,
        number_only,
        read_only,
        alignment,
    } = &c.payload
    else {
        return Err("text".into());
    };
    Ok(FormControlPayload::Text {
        value: value.clone(),
        default_value: "caller-default".into(),
        validation: FormTextValidation {
            required: false,
            minimum_characters: 0,
            maximum_characters: None,
            external_validator_sha256: None,
        },
        multi_line: *multi_line,
        password_character: password_character.clone(),
        native_max_length: *native_max_length,
        scroll_bars: *scroll_bars,
        tab_key_behavior: *tab_key_behavior,
        number_only: *number_only,
        read_only: *read_only,
        alignment: *alignment,
    })
}
fn matrix_policy(
    c: &NativeFormControlObservation,
) -> Result<NativeFormPackagePolicy, Box<dyn Error>> {
    let selection_validation = || FormSelectionValidation {
        required: false,
        external_validator_sha256: None,
    };
    let payload = match &c.payload {
        NativeFormObservedPayload::Text { .. } => text_payload(c)?,
        NativeFormObservedPayload::Button {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
        } if c.tag == NativeFormTag::RadioBtn => FormControlPayload::Radio {
            caption: caption.clone(),
            value: *value,
            default_value: if c.component_identity.native_object_id == 90003 {
                FormButtonValue::Checked
            } else {
                FormButtonValue::Unchecked
            },
            radio_group_name: radio_group_name.clone().ok_or("radio")?,
            group_required: true,
            tri_state: *tri_state,
            back_style: *back_style,
        },
        NativeFormObservedPayload::Button {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
        } => FormControlPayload::Checkbox {
            caption: caption.clone(),
            value: *value,
            default_value: FormButtonValue::Unchecked,
            must_be_checked: false,
            radio_group_name: radio_group_name.clone(),
            tri_state: *tri_state,
            back_style: *back_style,
        },
        NativeFormObservedPayload::Combo {
            items,
            selected_value,
            list_box_rows,
            list_box_width_hwp_units,
            edit_enable,
        } => FormControlPayload::Combo {
            items: items.clone(),
            selected_value: selected_value.clone(),
            default_selected_value: Some("b".into()),
            validation: selection_validation(),
            list_box_rows: *list_box_rows,
            list_box_width_hwp_units: *list_box_width_hwp_units,
            edit_enable: *edit_enable,
        },
        NativeFormObservedPayload::List {
            items,
            selected_value,
            item_height_hwp_units,
            top_index,
        } => FormControlPayload::List {
            items: items.clone(),
            selected_value: selected_value.clone(),
            default_selected_value: Some("a".into()),
            validation: selection_validation(),
            item_height_hwp_units: *item_height_hwp_units,
            top_index: *top_index,
        },
    };
    Ok(NativeFormPackagePolicy {
        identity: c.component_identity.clone(),
        payload,
    })
}
fn product_request(
    f: &Fixture,
    operation: FormInputOperation,
) -> Result<(Vec<u8>, FormInputAccessPolicy), Box<dyn Error>> {
    let (mut value, access) = f.request("temporary")?;
    value["operation"] = serde_json::to_value(operation)?;
    Ok((serde_json::to_vec(&value)?, access))
}
fn identity(plan: &str, revision: &str) -> Result<FormOperationIdentity, Box<dyn Error>> {
    Ok(FormOperationIdentity::new(
        DocumentId::parse("actual-form-document")?,
        RevisionId::parse(revision)?,
        PlanId::parse(plan)?,
    )?)
}
fn operation_context(f: &Fixture) -> Result<FormOperationContext<'_>, Box<dyn Error>> {
    Ok(FormOperationContext::bind(&f.source, &f.map, &f.policies)?)
}
fn matrix_request(
    label: &str,
    f: &Fixture,
) -> Result<(Vec<u8>, FormInputAccessPolicy), Box<dyn Error>> {
    let assignment = |index: usize, value| FormInputAssignment {
        target: f.policies[index].identity.clone(),
        value,
    };
    let operation = match label {
        "five-kinds" => FormInputOperation::SetValues {
            assignments: vec![
                assignment(
                    0,
                    FormInputValue::Text {
                        value: "新 & <\"'> 🚀\r\n\tline".into(),
                    },
                ),
                assignment(
                    1,
                    FormInputValue::Checkbox {
                        value: FormButtonValue::Indeterminate,
                    },
                ),
                assignment(
                    2,
                    FormInputValue::Radio {
                        value: FormButtonValue::Unchecked,
                    },
                ),
                assignment(
                    3,
                    FormInputValue::Combo {
                        selected_value: Some("b".into()),
                    },
                ),
                assignment(
                    4,
                    FormInputValue::List {
                        selected_value: Some("a".into()),
                    },
                ),
                assignment(
                    5,
                    FormInputValue::Radio {
                        value: FormButtonValue::Checked,
                    },
                ),
            ],
        },
        "empty-text" => FormInputOperation::SetValues {
            assignments: vec![assignment(
                0,
                FormInputValue::Text {
                    value: "value & 🚀".into(),
                },
            )],
        },
        "reset-defaults" => FormInputOperation::ResetDefaults {
            targets: f.policies.iter().map(|p| p.identity.clone()).collect(),
        },
        _ => FormInputOperation::SetValues {
            assignments: vec![
                assignment(
                    3,
                    FormInputValue::Combo {
                        selected_value: None,
                    },
                ),
                assignment(
                    4,
                    FormInputValue::List {
                        selected_value: None,
                    },
                ),
            ],
        },
    };
    let (request, access) = product_request(f, operation)?;

    Ok((request, access))
}
fn arg_text<'a>(op: &'a CompiledOperation, key: &str) -> Result<&'a str, Box<dyn Error>> {
    match op.arguments().get(key).ok_or("argument")?.value() {
        CanonicalArgumentValue::Text(s) => Ok(s),
        _ => Err("argument kind".into()),
    }
}

use artifact_service::{
    Aes256GcmKeyring, ArtifactKind, ArtifactMetadataRepository, ArtifactPermission,
    ArtifactScanner, ArtifactService, ArtifactServiceConfig, AuthScope, ContentDigest,
    DownloadSigner, EncryptedBlobStore, FileName, InMemoryBlobStore, InMemoryMetadataRepository,
    IngestRequest, KeyReference, MediaType, ObjectKey, QuarantineReason, RequestContext,
    ScanEvidence, ScanRequest, ScanVerdict, ScannerReference, ScannerSignatureVersion,
    SubjectDigest, TenantId,
};
use hwpx_agent_cli::form_stored_provider::*;
use revision_service::{
    BranchId, CommitId, CommitOutcome, InMemoryRevisionRepository, RevisionCommitRequest,
    RevisionHead, RevisionRequestContext, RevisionService, RevisionValidationState,
};
use std::{
    collections::BTreeSet,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
};
use uuid::Uuid;

// TEST ONLY: local scanner fixture and synthetic crypto keys, NOT a real scanner,
// external issuer/native approval or product signed form route.
#[derive(Debug)]
struct FixtureScanner {
    unavailable: bool,
}
impl ArtifactScanner for FixtureScanner {
    fn scan(&self, _: ScanRequest<'_>) -> Result<ScanEvidence, artifact_service::ArtifactError> {
        Ok(ScanEvidence {
            engine: ScannerReference::parse("scanner.fixture-only")?,
            signature_version: ScannerSignatureVersion::parse("not-native-v1")?,
            verdict: if self.unavailable {
                ScanVerdict::Unverified(QuarantineReason::parse("FIXTURE_UNVERIFIED")?)
            } else {
                ScanVerdict::Clean
            },
        })
    }
}
#[derive(Clone, Debug, Default)]
struct FaultBlob {
    inner: InMemoryBlobStore,
    tamper: Arc<AtomicBool>,
}
impl EncryptedBlobStore for FaultBlob {
    fn put_if_absent(
        &self,
        key: &ObjectKey,
        bytes: &[u8],
    ) -> Result<(), artifact_service::ArtifactError> {
        self.inner.put_if_absent(key, bytes)
    }
    fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, artifact_service::ArtifactError> {
        let mut value = self.inner.get(key)?;
        if self.tamper.load(Ordering::SeqCst)
            && let Some(bytes) = &mut value
            && let Some(first) = bytes.first_mut()
        {
            *first ^= 1;
        }
        Ok(value)
    }
    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> Result<(), artifact_service::ArtifactError> {
        self.inner.relocate_if_absent(source, target)
    }
}
type Artifacts = ArtifactService<InMemoryMetadataRepository, FaultBlob, FixtureScanner>;
type Provider<'a> = StoredFormProvider<
    'a,
    InMemoryMetadataRepository,
    FaultBlob,
    FixtureScanner,
    InMemoryRevisionRepository,
>;
fn fixture_artifacts(
    metadata: InMemoryMetadataRepository,
    blobs: FaultBlob,
    unverified: bool,
) -> Result<Artifacts, Box<dyn Error>> {
    let reference = KeyReference::parse("fixture.p45-aes")?;
    let keyring = Aes256GcmKeyring::new(reference.clone(), [(reference, [45; 32])])?;
    let signer = DownloadSigner::new(
        "https://fixture.example.test/download",
        KeyReference::parse("fixture.p45-hmac")?,
        &[46; 32],
        60,
    )?;
    Ok(ArtifactService::new(
        metadata,
        blobs,
        FixtureScanner {
            unavailable: unverified,
        },
        keyring,
        signer,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?,
    ))
}
struct StoredFixture {
    artifacts: Artifacts,
    metadata: InMemoryMetadataRepository,
    blobs: FaultBlob,
    revisions: RevisionService<InMemoryRevisionRepository>,
    owner: RequestContext,
    reader: RequestContext,
    revision_context: RevisionRequestContext,
    project: revision_service::ProjectId,
    branch: BranchId,
    result: artifact_service::ArtifactId,
    head: RevisionHead,
}
impl StoredFixture {
    fn new(source: &[u8], kind: ArtifactKind, unverified: bool) -> Result<Self, Box<dyn Error>> {
        let tenant = TenantId::new(Uuid::from_u128(451))?;
        let subject = SubjectDigest::from_authenticated_subject("P45 fixture owner private")?;
        let reader_subject =
            SubjectDigest::from_authenticated_subject("P45 fixture reader private")?;
        let owner = RequestContext::new(
            tenant,
            subject,
            [
                AuthScope::DocumentRead,
                AuthScope::DocumentWrite,
                AuthScope::ArtifactShare,
                AuthScope::SecurityModify,
            ],
        );
        let reader = RequestContext::new(tenant, reader_subject, [AuthScope::DocumentRead]);
        let revision_context = RevisionRequestContext::new(tenant, reader_subject);
        let metadata = InMemoryMetadataRepository::default();
        let blobs = FaultBlob::default();
        let artifacts = fixture_artifacts(metadata.clone(), blobs.clone(), unverified)?;
        let prior = artifacts.ingest(
            &owner,
            IngestRequest {
                bytes: b"P45 prior source METADATA FIXTURE ONLY".to_vec(),
                media_type: MediaType::parse("application/octet-stream")?,
                file_name: FileName::parse("prior.bin")?,
                kind: ArtifactKind::Source,
            },
            1,
        )?;
        let result = artifacts.ingest(
            &owner,
            IngestRequest {
                bytes: source.to_vec(),
                media_type: MediaType::parse("application/vnd.hancom.hwpx+zip")?,
                file_name: FileName::parse("private-original.hwpx")?,
                kind,
            },
            2,
        )?;
        artifacts.set_permissions(
            &owner,
            result.artifact_id,
            reader_subject,
            BTreeSet::from([ArtifactPermission::Read]),
            3,
        )?;
        let project = revision_service::ProjectId::parse("prj_45000000000000000000000000000001")?;
        let branch = BranchId::parse("brn_45000000000000000000000000000001")?;
        let repository = InMemoryRevisionRepository::default();
        repository.provision_stream(tenant, project, branch)?;
        let revisions = RevisionService::new(repository);
        // Actual sealed repository-node fixture. These opaque metadata digests and
        // Verified tag are NOT a form/native execution manifest or product commit.
        let request = RevisionCommitRequest::new(
            CommitId::generate(),
            project,
            branch,
            RevisionHead::empty(),
            revision_service::RevisionId::generate(),
            vec![],
            prior.artifact_id,
            result.artifact_id,
            None,
            ContentDigest::of(b"fixture operation only"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"fixture validation only"),
            ContentDigest::of(b"fixture transaction only"),
        )?;
        assert!(matches!(
            revisions.commit(&revision_context, &request)?,
            CommitOutcome::Committed(_)
        ));
        let head = revisions.head(&revision_context, project, branch)?;
        Ok(Self {
            artifacts,
            metadata,
            blobs,
            revisions,
            owner,
            reader,
            revision_context,
            project,
            branch,
            result: result.artifact_id,
            head,
        })
    }
    fn provider(&self) -> Result<Provider<'_>, StoredFormError> {
        StoredFormProvider::bind(
            &self.artifacts,
            &self.revisions,
            &self.reader,
            &self.revision_context,
            self.project,
            self.branch,
            DocumentId::parse("actual-form-document").map_err(|_| StoredFormError::Scope)?,
        )
    }
    fn prepare(
        &self,
        form: &Fixture,
        raw: &[u8],
        access: &FormInputAccessPolicy,
    ) -> Result<PreparedStoredForm, StoredFormError> {
        self.provider()?
            .prepare_json(self.inputs(form, raw, access)?, 4)
    }
    fn inputs<'a>(
        &self,
        form: &'a Fixture,
        raw: &'a [u8],
        access: &'a FormInputAccessPolicy,
    ) -> Result<StoredFormInputs<'a>, StoredFormError> {
        Ok(StoredFormInputs {
            expected_head: self.head,
            plan_id: PlanId::parse("stored-form-plan").map_err(|_| StoredFormError::Preparation)?,
            form_input_json: raw,
            map: &form.map,
            policies: &form.policies,
            access,
        })
    }
    fn advance(&self) -> Result<(), Box<dyn Error>> {
        let request = RevisionCommitRequest::new(
            CommitId::generate(),
            self.project,
            self.branch,
            self.head,
            revision_service::RevisionId::generate(),
            self.head.revision_id().into_iter().collect(),
            artifact_service::ArtifactId::generate(),
            self.result,
            None,
            ContentDigest::of(b"advance fixture operation"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"advance fixture validation"),
            ContentDigest::of(b"advance fixture transaction"),
        )?;
        assert!(matches!(
            self.revisions.commit(&self.revision_context, &request)?,
            CommitOutcome::Committed(_)
        ));
        Ok(())
    }
}

#[test]
fn stored_actual_capture_uses_real_sealed_node_acl_aead_and_original_compiler_without_publish()
-> TestResult {
    let form = fixture()?;
    let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let (json, access) = form.request("P40 값 & <한글> \" ' 🚀")?;
    let raw = serde_json::to_vec(&json)?;
    let prepared = stored.prepare(&form, &raw, &access)?;
    let original = FormOperationPreparation::prepare_json(
        &operation_context(&form)?,
        identity(
            "stored-form-plan",
            &stored.head.revision_id().ok_or("head")?.public_id(),
        )?,
        &raw,
        &access,
    )?;
    let values = FormValuePreparation::prepare_json(&form.context()?, &raw, &access)?;
    assert_eq!(prepared.candidate_bytes(), original.candidate_bytes());
    assert_eq!(prepared.candidate_bytes(), values.candidate_bytes());
    let expected = checked_fixture("actual-output.hwpx")?;
    assert_eq!(
        hex::encode(Sha256::digest(&expected)),
        "bb0a1b43fa83d6f88dbabdb63324fb7cd95546d982562d73ce76d5b54c2dca4f"
    );
    assert_eq!(prepared.candidate_bytes(), expected);
    assert!(
        !arg_text(
            &original.compiled_plan().operations()[0],
            "target_control_state_json"
        )?
        .is_empty()
    );
    assert_eq!(prepared.receipt().source_sha256, CAPTURE_SHA);
    assert_eq!(prepared.receipt().source_bytes, 14556);
    assert_eq!(
        prepared.verify(&stored.provider()?, &form.map, &form.policies, &access, 5)?,
        *prepared.receipt()
    );
    assert_eq!(
        prepared.require_current_product_route(
            &stored.provider()?,
            &form.map,
            &form.policies,
            &access,
            6
        ),
        Err(StoredFormError::RouteUnqualified)
    );
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    let audits = stored.metadata.audit_events()?;
    assert!(
        audits
            .iter()
            .any(|event| event.event == "artifact.download")
    );
    assert_eq!(
        audits
            .iter()
            .filter(|event| event.event == "artifact.ingested")
            .count(),
        2
    );
    let node = stored.revisions.node(
        &stored.revision_context,
        stored.project,
        stored.head.revision_id().ok_or("head")?,
    )?;
    assert_eq!(node.project_id(), stored.project);
    assert_eq!(node.result_artifact_id(), stored.result);
    assert!(node.sealed());
    Ok(())
}
#[test]
fn stored_all_five_kinds_required_radio_defaults_empty_clear_match_whole_predecessor() -> TestResult
{
    for label in [
        "five-kinds",
        "empty-text",
        "reset-defaults",
        "clear-selections",
    ] {
        let (form, expected) = matrix(label)?;
        let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
        let (raw, access) = matrix_request(label, &form)?;
        let prepared = stored.prepare(&form, &raw, &access)?;
        assert_eq!(prepared.candidate_bytes(), expected);
        assert_eq!(
            prepared.verify(&stored.provider()?, &form.map, &form.policies, &access, 5)?,
            *prepared.receipt()
        );
        assert_eq!(
            prepared.require_current_product_route(
                &stored.provider()?,
                &form.map,
                &form.policies,
                &access,
                6
            ),
            Err(StoredFormError::RouteUnqualified)
        );
        assert_eq!(
            stored
                .revisions
                .head(&stored.revision_context, stored.project, stored.branch)?,
            stored.head
        );
    }
    Ok(())
}
#[test]
fn stored_fresh_acl_revocation_blocks_preparation_verification_and_route() -> TestResult {
    let form = fixture()?;
    let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let (json, access) = form.request("new value")?;
    let raw = serde_json::to_vec(&json)?;
    let prepared = stored.prepare(&form, &raw, &access)?;
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        5,
    )?;
    assert_eq!(
        stored
            .prepare(&form, &raw, &access)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Artifact
    );
    assert_eq!(
        prepared
            .verify(&stored.provider()?, &form.map, &form.policies, &access, 6)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Artifact
    );
    assert_eq!(
        prepared.require_current_product_route(
            &stored.provider()?,
            &form.map,
            &form.policies,
            &access,
            6
        ),
        Err(StoredFormError::Artifact)
    );
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    Ok(())
}
#[test]
fn stored_real_head_advance_rejects_old_preparation_even_when_actual_artifact_is_unchanged()
-> TestResult {
    let form = fixture()?;
    let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let (json, access) = form.request("new value")?;
    let raw = serde_json::to_vec(&json)?;
    let prepared = stored.prepare(&form, &raw, &access)?;
    stored.advance()?;
    assert_eq!(
        stored
            .prepare(&form, &raw, &access)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Head
    );
    assert_eq!(
        prepared
            .verify(&stored.provider()?, &form.map, &form.policies, &access, 5)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Head
    );
    assert_eq!(
        prepared.require_current_product_route(
            &stored.provider()?,
            &form.map,
            &form.policies,
            &access,
            5
        ),
        Err(StoredFormError::Head)
    );
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?
            .generation(),
        2
    );
    Ok(())
}
#[test]
fn stored_provider_tenant_subject_scope_branch_document_cannot_be_substituted() -> TestResult {
    let form = fixture()?;
    let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let wrong_revision =
        RevisionRequestContext::new(stored.reader.tenant_id(), stored.owner.subject());
    assert_eq!(
        StoredFormProvider::bind(
            &stored.artifacts,
            &stored.revisions,
            &stored.reader,
            &wrong_revision,
            stored.project,
            stored.branch,
            DocumentId::parse("actual-form-document")?
        )
        .err()
        .ok_or("expected stored failure")?,
        StoredFormError::Scope
    );
    let no_read = RequestContext::new(stored.reader.tenant_id(), stored.reader.subject(), []);
    assert_eq!(
        StoredFormProvider::bind(
            &stored.artifacts,
            &stored.revisions,
            &no_read,
            &stored.revision_context,
            stored.project,
            stored.branch,
            DocumentId::parse("actual-form-document")?
        )
        .err()
        .ok_or("expected stored failure")?,
        StoredFormError::Scope
    );
    let (json, access) = form.request("new value")?;
    let raw = serde_json::to_vec(&json)?;
    let prepared = stored.prepare(&form, &raw, &access)?;
    let another = StoredFormProvider::bind(
        &stored.artifacts,
        &stored.revisions,
        &stored.reader,
        &stored.revision_context,
        stored.project,
        stored.branch,
        DocumentId::parse("another-document")?,
    )?;
    assert_eq!(
        prepared
            .verify(&another, &form.map, &form.policies, &access, 5)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Scope
    );
    let missing = StoredFormProvider::bind(
        &stored.artifacts,
        &stored.revisions,
        &stored.reader,
        &stored.revision_context,
        stored.project,
        BranchId::generate(),
        DocumentId::parse("actual-form-document")?,
    )?;
    assert_eq!(
        missing
            .prepare_json(stored.inputs(&form, &raw, &access)?, 5)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Head
    );
    let other_tenant = TenantId::new(Uuid::from_u128(452))?;
    let other_artifact = RequestContext::new(
        other_tenant,
        stored.reader.subject(),
        [AuthScope::DocumentRead],
    );
    let other_revision = RevisionRequestContext::new(other_tenant, stored.reader.subject());
    let cross = StoredFormProvider::bind(
        &stored.artifacts,
        &stored.revisions,
        &other_artifact,
        &other_revision,
        stored.project,
        stored.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    assert_eq!(
        cross
            .prepare_json(stored.inputs(&form, &raw, &access)?, 5)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Head
    );
    Ok(())
}
#[test]
fn stored_quarantine_unverified_wrong_artifact_kind_and_corrupt_ciphertext_never_prepare()
-> TestResult {
    let form = fixture()?;
    let (json, access) = form.request("new value")?;
    let raw = serde_json::to_vec(&json)?;
    for (kind, unverified) in [(ArtifactKind::Result, true), (ArtifactKind::Source, false)] {
        let stored = StoredFixture::new(&form.source, kind, unverified)?;
        assert_eq!(
            stored
                .prepare(&form, &raw, &access)
                .err()
                .ok_or("expected stored failure")?,
            StoredFormError::Artifact
        );
    }
    let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let prepared = stored.prepare(&form, &raw, &access)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert_eq!(
        stored
            .prepare(&form, &raw, &access)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Artifact
    );
    assert_eq!(
        prepared
            .verify(&stored.provider()?, &form.map, &form.policies, &access, 5)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Artifact
    );
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    stored.artifacts.quarantine(
        &stored.owner,
        stored.result,
        QuarantineReason::parse("P45_FIXTURE_QUARANTINE")?,
        6,
    )?;
    assert_eq!(
        prepared
            .verify(&stored.provider()?, &form.map, &form.policies, &access, 7)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Artifact
    );
    Ok(())
}
#[test]
fn stored_fresh_map_policy_access_and_malformed_input_fail_without_ingest_or_commit() -> TestResult
{
    let form = fixture()?;
    let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let (json, access) = form.request("new value")?;
    let raw = serde_json::to_vec(&json)?;
    let prepared = stored.prepare(&form, &raw, &access)?;
    let mut revoked = access.clone();
    revoked.input_allowed = false;
    assert_eq!(
        prepared
            .verify(&stored.provider()?, &form.map, &form.policies, &revoked, 5)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Drift
    );
    assert_eq!(
        stored
            .prepare(&form, b"{}", &access)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Preparation
    );
    let mut changed = form.policies.clone();
    if let FormControlPayload::Text { default_value, .. } = &mut changed[0].payload {
        *default_value = "changed".into();
    }
    assert_eq!(
        prepared
            .verify(&stored.provider()?, &form.map, &changed, &access, 5)
            .err()
            .ok_or("expected stored failure")?,
        StoredFormError::Drift
    );
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    assert_eq!(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|event| event.event == "artifact.ingested")
            .count(),
        2
    );
    Ok(())
}
#[test]
fn stored_receipts_debug_and_fixed_errors_do_not_expose_source_subject_artifact_or_paths()
-> TestResult {
    let form = fixture()?;
    let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let (json, access) = form.request("P45 PRIVATE value must not leak")?;
    let raw = serde_json::to_vec(&json)?;
    let prepared = stored.prepare(&form, &raw, &access)?;
    let public = format!(
        "{} {:?} {:?} {}",
        serde_json::to_string(prepared.receipt())?,
        prepared,
        stored.provider()?,
        StoredFormError::Artifact
    );
    for private in [
        "P45 PRIVATE",
        "P45 fixture owner",
        "P45 fixture reader",
        "private-original.hwpx",
        CAPTURE,
    ] {
        assert!(!public.contains(private));
    }
    assert!(!public.contains(&stored.result.public_id()));
    assert!(!public.contains(&stored.reader.subject().hex()));
    assert!(!public.contains(&stored.reader.tenant_id().canonical()));
    Ok(())
}
