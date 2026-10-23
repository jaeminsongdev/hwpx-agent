//! Source-bound storage preparation and real staged HWPX readback. Never an execution permit.
pub mod guard;
use super::*;
use artifact_service::ContentDigest;
use crate::stored_revision_commit::{StoredCommitBinding,StoredCommitError,job::{PreparedStoredJob,StoredJobOptions}};
use crate::stored_revision_commit::job::identity::{StoredRequestJobIdentity,StoredJobPolicy};
use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    structure::review::{ImportedDocumentReviewBodies,ReviewBodyImportReceipt}};
use operation_engine::{OutputValidator,TransactionLimits,ValidationOutcome};
use revision_service::{ProjectId,BranchId,RevisionHead,CommitId,RevisionId};

pub const CATALOG_MASK_STORAGE_PROFILE:&str="hwpx-agent.catalog-mask-storage-preparation/v1";
#[derive(Debug,Error)]
pub enum CatalogMaskStorageError{
    #[error("CATALOG_STORAGE_MANIFEST_REJECTED")]Manifest(#[from]CatalogMaskManifestError),
    #[error("CATALOG_STORAGE_PRODUCT_REJECTED")]Product(#[from]PersonalInfoCatalogMaskProductError),
    #[error("CATALOG_STORAGE_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("CATALOG_STORAGE_BINDING_REJECTED")]Binding,
    #[error("CATALOG_STORAGE_JOB_REJECTED")]Job(#[from]StoredCommitError),
}
type SError=CatalogMaskStorageError;
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct CatalogMaskStorageReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],
    pub output_bytes:usize,pub catalog_sha256:[u8;32],pub manifest_sha256:[u8;32],
    pub validation_contract_sha256:[u8;32],pub expected_output_review_import:ReviewBodyImportReceipt,
    pub execution_or_native_authority:bool,pub validation_executed:bool,
}
impl fmt::Debug for CatalogMaskStorageReceipt{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("CatalogMaskStorageReceipt(<redacted>; expected_contract_not_validation_success)")}
}
/// Borrows operation-local current source and the sole original output; cannot escape the callback.
/// It binds existing server storage primitives, not a product route, lease or trust decision.
pub struct PreparedCatalogMaskStorage<'a>{
    source:&'a[u8],output:&'a[u8],manifest:&'a ExecutionManifest,document:&'a domain_ir::DocumentId,
    project:ProjectId,branch:BranchId,head:RevisionHead,canonical_request_sha256:&'a str,
    route_set_sha256:[u8;32],receipt:CatalogMaskStorageReceipt,identity:StoredRequestJobIdentity,scoped_request_sha256:&'a str,
}
impl fmt::Debug for PreparedCatalogMaskStorage<'_>{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedCatalogMaskStorage(<redacted>; server_primitive_not_product_execution)")}
}
/// Private expectation comes only from the retained preserving candidate, never caller JSON/digests.
/// Full staged bytes are reimported once; no regex/index/mask/compiler replay or graph clone.
pub struct CatalogMaskOutputValidator<'a>{expected:&'a CatalogMaskStorageReceipt,document:&'a domain_ir::DocumentId,attempted:bool}
impl fmt::Debug for CatalogMaskOutputValidator<'_>{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("CatalogMaskOutputValidator(<redacted>; one_shot_direct_readback_only)")}
}
impl OutputValidator for CatalogMaskOutputValidator<'_>{
    fn validate(&mut self,bytes:&[u8])->ValidationOutcome{
        if self.attempted{return ValidationOutcome::Failed;}self.attempted=true;
        if bytes.len()!=self.expected.output_bytes||bytes.is_empty()
            ||<[u8;32]>::from(Sha256::digest(bytes))!=self.expected.output_package_sha256{return ValidationOutcome::Rejected;}
        let result=(||{
            let source=ImportedSourcePackage::import(bytes,self.document.clone(),self.expected.output_package_sha256,SourceImportLimits::default()).ok()?;
            source.observe_protection_signals().ok()?.require_no_observed_document_signals().ok()?;
            let forms=ImportedDocumentForms::import(source).ok()?;
            let review=ImportedDocumentReviewBodies::import(&forms).ok()?;
            (review.receipt()==&self.expected.expected_output_review_import).then_some(())
        })();
        if result.is_some(){ValidationOutcome::Valid}else{ValidationOutcome::Rejected}
    }
}
impl PreparedCatalogMaskStorage<'_>{
    /// Unclaimed deterministic server IDs only; not a DB observation, worker registration or execution permit.
    #[must_use]pub const fn job_identity(&self)->&StoredRequestJobIdentity{&self.identity}
    /// # Errors
    /// Uses the original strict request key/canonical/scoped binding. Caller cannot choose key/job/request UUIDs.
    /// Original job policy validation and current-state/route restrictions remain mandatory.
    pub fn prepare_bound_job(&self,policy:StoredJobPolicy,commit:CommitId,new_revision:RevisionId,limits:TransactionLimits)
        ->Result<PreparedStoredJob<'_>,SError>{
        if !self.identity.matches(self.project,self.canonical_request_sha256,self.scoped_request_sha256){return Err(SError::Binding);}
        let capability=ContentDigest::parse(&hex::encode(self.route_set_sha256)).map_err(|_|SError::Binding)?;
        self.prepare_job(self.identity.options(capability,policy),commit,new_revision,limits)
    }
    #[must_use]pub const fn receipt(&self)->&CatalogMaskStorageReceipt{&self.receipt}
    #[must_use]pub const fn manifest(&self)->&ExecutionManifest{self.manifest}
    #[must_use]pub const fn source_bytes(&self)->&[u8]{self.source}
    #[must_use]pub const fn output_bytes(&self)->&[u8]{self.output}
    #[must_use]pub fn output_validator(&self)->CatalogMaskOutputValidator<'_>{
        CatalogMaskOutputValidator{expected:&self.receipt,document:self.document,attempted:false}
    }
    /// # Errors
    /// Server-owned new identities only. Original source/head/output/validation contract cannot be replaced.
    /// This expectation digest does not assert validation has run; the real engine must invoke the validator.
    pub fn commit_binding(&self,commit:CommitId,new_revision:RevisionId)->Result<StoredCommitBinding<'_>,SError>{
        if Some(new_revision)==self.head.revision_id(){return Err(SError::Binding);}
        let validation_summary=ContentDigest::parse(&hex::encode(self.receipt.validation_contract_sha256)).map_err(|_|SError::Binding)?;
        Ok(StoredCommitBinding{manifest:self.manifest,output:self.output,project:self.project,branch:self.branch,
            expected_head:self.head,commit,new_revision,validation_summary})
    }
    /// # Errors
    /// Binds existing durable job preparation only; no claim/lease/execution/ingest/CAS occurs.
    /// Options remain authenticated server identities, not a mapping of public string keys to UUIDs.
    pub fn prepare_job(&self,options:StoredJobOptions,commit:CommitId,new_revision:RevisionId,limits:TransactionLimits)
        ->Result<PreparedStoredJob<'_>,SError>{
        if options.request_sha.hex()!=self.canonical_request_sha256||options.capability_sha.as_bytes()!=&self.route_set_sha256{
            return Err(SError::Binding);}
        Ok(PreparedStoredJob::prepare(self.commit_binding(commit,new_revision)?,options,limits)?)
    }
}
impl PreparedCatalogMaskExecutionManifest{
    /// # Errors
    /// Sole source-bound storage bridge, no caller source/plan/result/validation verdict.
    /// The trusted server must separately qualify execution and refresh config/routes at mutation boundaries.
    /// A retained preparation or validator is not current ACL/config/route authority.
    pub fn with_verified_storage_preparation<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,formats:&dyn CurrentPersonalInfoCatalogSource,
        context:&RouteContext,routes:&CapabilityRouteCatalog,now:u64,consume:impl FnOnce(PreparedCatalogMaskStorage<'_>)->T)->Result<T,SError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_bytes(provider,formats,context,routes,now,|output|->Result<T,SError>{
            let view=self.compiled.candidate.compiler_view()?;let r=&self.compiled.candidate.receipt().stored.output;
            if output.len()!=r.output_bytes||self.compiled.receipt.output_package_sha256!=r.output_package_sha256
                ||self.manifest.expected_source_sha256()!=r.source_package_sha256||r.output_review_import.source_package_sha256!=r.output_package_sha256{
                return Err(SError::Binding);}
            let contract=bounded_hash(&(CATALOG_MASK_STORAGE_PROFILE,&self.compiled.receipt,self.manifest_sha256,
                r.output_bytes,&r.output_review_import,r.catalog.source_sha256),MAX_METADATA_BYTES).map_err(|_|SError::Binding)?;
            let receipt=CatalogMaskStorageReceipt{profile:CATALOG_MASK_STORAGE_PROFILE,source_package_sha256:r.source_package_sha256,
                output_package_sha256:r.output_package_sha256,output_bytes:r.output_bytes,catalog_sha256:r.catalog.source_sha256,
                manifest_sha256:self.manifest_sha256,validation_contract_sha256:contract,expected_output_review_import:r.output_review_import.clone(),
                execution_or_native_authority:false,validation_executed:false};
            view.source.with_verified_compiler_source(provider,now,|source,project,branch,head|->Result<T,SError>{
                if source.len()as u64!=self.manifest.expected_source_size()||head.generation()!=self.compiled.receipt.head_generation{
                    return Err(SError::Binding);}
                let identity=self.compiled.candidate.server_job_identity(provider)?;
                self.compiled.candidate.check_final_inputs(provider,formats)?;
                Ok(consume(PreparedCatalogMaskStorage{source,output,manifest:&self.manifest,document:view.document,project,branch,head,
                    canonical_request_sha256:&self.compiled.receipt.canonical_request_sha256,route_set_sha256:self.manifest.route_set_sha256(),receipt,identity,
                    scoped_request_sha256:&self.compiled.receipt.scoped_request_sha256}))
            })?
        })?
    }
}
