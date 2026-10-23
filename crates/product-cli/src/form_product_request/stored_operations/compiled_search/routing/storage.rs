//! Original source candidate -> shared storage primitives. No execution route or key claim.
use super::*;
use artifact_service::ContentDigest;
use crate::{stored_revision_commit::{StoredCommitBinding,StoredCommitError,StoredPrecommitGuard,
    job::{PreparedStoredJob,identity::{StoredRequestJobIdentity,StoredJobPolicy}}},
    form_stored_provider::actual_import::source_search::StoredSourceSearchError};
use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,structure::review::ImportedDocumentReviewBodies};
use operation_engine::{OutputValidator,ValidationOutcome,TransactionLimits};
use revision_service::{ProjectId,BranchId,RevisionHead,CommitId,RevisionId};

pub const SEARCH_STORAGE_PROFILE:&str="hwpx-agent.search-mutation-storage-preparation/v1";
#[derive(Debug,Error)]
pub enum SearchStorageError {
    #[error("SEARCH_STORAGE_MANIFEST_REJECTED")]Manifest(#[from]SearchManifestError),
    #[error("SEARCH_STORAGE_SOURCE_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("SEARCH_STORAGE_IDENTITY_REJECTED")]Identity(#[from]StoredSourceSearchError),
    #[error("SEARCH_STORAGE_BINDING_REJECTED")]Binding,
    #[error("SEARCH_STORAGE_JOB_REJECTED")]Job(#[from]StoredCommitError),
}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SearchStorageReceipt {
    pub profile:&'static str,pub request_schema:&'static str,pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],
    pub output_bytes:usize,pub compiled_plan_sha256:[u8;32],pub manifest_sha256:[u8;32],pub validation_contract_sha256:[u8;32],
    pub validation_executed:bool,pub execution_or_native_authority:bool,
}
impl fmt::Debug for SearchStorageReceipt {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SearchStorageReceipt(<redacted>; not_validation_or_authority)")}}
/// Source/output borrows cannot escape the operation-local current verification callback.
pub struct PreparedSearchStorage<'a> {
    source:&'a[u8],output:&'a[u8],manifest:&'a ExecutionManifest,document:&'a domain_ir::DocumentId,
    project:ProjectId,branch:BranchId,head:RevisionHead,receipt:SearchStorageReceipt,identity:StoredRequestJobIdentity,
    canonical:&'a str,scoped:&'a str,
}
impl fmt::Debug for PreparedSearchStorage<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedSearchStorage(<redacted>; unclaimed_not_product_execution)")}}
impl<'a> PreparedSearchStorage<'a>{
    // Shared construction from operation-local verified bytes, not a caller artifact/output selector.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn bind_verified(source:&'a[u8],output:&'a[u8],manifest:&'a ExecutionManifest,document:&'a domain_ir::DocumentId,
        scope:(ProjectId,BranchId,RevisionHead),receipt:SearchStorageReceipt,identity:StoredRequestJobIdentity,request:(&'a str,&'a str))
        ->Result<Self,SearchStorageError>{
        let(project,branch,head)=scope;let(canonical,scoped)=request;
        if source.is_empty()||output.is_empty()||output.len()!=receipt.output_bytes||source.len()as u64!=manifest.expected_source_size()
            ||<[u8;32]>::from(Sha256::digest(source))!=receipt.source_package_sha256||<[u8;32]>::from(Sha256::digest(output))!=receipt.output_package_sha256
            ||manifest.expected_source_sha256()!=receipt.source_package_sha256||manifest.compiled_plan_sha256()!=receipt.compiled_plan_sha256
            ||manifest.canonical_sha256().map_err(|_|SearchStorageError::Binding)?!=receipt.manifest_sha256
            ||head.revision_id().is_none_or(|id|id.public_id()!=manifest.base_revision().as_str())
            ||!identity.matches(project,canonical,scoped)||receipt.validation_contract_sha256==[0;32]
            ||receipt.validation_executed||receipt.execution_or_native_authority{return Err(SearchStorageError::Binding);}
        Ok(Self{source,output,manifest,document,project,branch,head,receipt,identity,canonical,scoped})
    }
}
/// One actual staged-byte import. Exact candidate digest binds all content; no search/compiler replay.
/// Forms/review/protection import is direct readback, not Native rendering or full v13 qualification.
pub struct SearchOutputValidator<'a> {receipt:&'a SearchStorageReceipt,document:&'a domain_ir::DocumentId,attempted:bool}
impl fmt::Debug for SearchOutputValidator<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SearchOutputValidator(<redacted>; one_shot_direct_readback)")}}
impl OutputValidator for SearchOutputValidator<'_> {
    fn validate(&mut self,bytes:&[u8])->ValidationOutcome {
        if self.attempted{return ValidationOutcome::Failed;}self.attempted=true;
        if bytes.is_empty()||bytes.len()!=self.receipt.output_bytes||<[u8;32]>::from(Sha256::digest(bytes))!=self.receipt.output_package_sha256 {
            return ValidationOutcome::Rejected;
        }
        let readback=(||{
            let source=ImportedSourcePackage::import(bytes,self.document.clone(),self.receipt.output_package_sha256,Default::default()).ok()?;
            source.observe_protection_signals().ok()?.require_no_observed_document_signals().ok()?;
            let forms=ImportedDocumentForms::import(source).ok()?;let review=ImportedDocumentReviewBodies::import(&forms).ok()?;
            (review.receipt().source_package_sha256==self.receipt.output_package_sha256).then_some(())
        })();
        if readback.is_some(){ValidationOutcome::Valid}else{ValidationOutcome::Rejected}
    }
}
impl PreparedSearchStorage<'_> {
    #[must_use]pub const fn receipt(&self)->&SearchStorageReceipt {&self.receipt}
    #[must_use]pub const fn source_bytes(&self)->&[u8] {self.source}
    #[must_use]pub const fn output_bytes(&self)->&[u8] {self.output}
    #[must_use]pub const fn manifest(&self)->&ExecutionManifest {self.manifest}
    #[must_use]pub const fn job_identity(&self)->&StoredRequestJobIdentity {&self.identity}
    #[must_use]pub fn output_validator(&self)->SearchOutputValidator<'_> {SearchOutputValidator {receipt:&self.receipt,document:self.document,attempted:false}}
    /// # Errors
    /// Server-owned revision IDs only; all original source/plan/output/manifest binding remains fixed.
    pub fn commit_binding(&self,commit:CommitId,new_revision:RevisionId)->Result<StoredCommitBinding<'_>,SearchStorageError> {
        if Some(new_revision)==self.head.revision_id(){return Err(SearchStorageError::Binding);}
        let summary=ContentDigest::parse(&hex::encode(self.receipt.validation_contract_sha256)).map_err(|_|SearchStorageError::Binding)?;
        Ok(StoredCommitBinding {manifest:self.manifest,output:self.output,project:self.project,branch:self.branch,expected_head:self.head,
            commit,new_revision,validation_summary:summary})
    }
    /// # Errors
    /// Same strict public key maps to the same server namespace IDs across changed content/schema.
    /// Does not claim/register/lease/execute/ingest/CAS; durable storage must conflict on changed binding.
    pub fn prepare_bound_job(&self,policy:StoredJobPolicy,commit:CommitId,new_revision:RevisionId,limits:TransactionLimits)
        ->Result<PreparedStoredJob<'_>,SearchStorageError> {
        if !self.identity.matches(self.project,self.canonical,self.scoped){return Err(SearchStorageError::Binding);}
        let capability=ContentDigest::parse(&hex::encode(self.manifest.route_set_sha256())).map_err(|_|SearchStorageError::Binding)?;
        Ok(PreparedStoredJob::prepare(self.commit_binding(commit,new_revision)?,self.identity.options(capability,policy),limits)?)
    }
}
impl PreparedSearchExecutionManifest {
    /// # Errors
    /// Binds the actual retained candidate to common storage; accepts no substitute source/output/plan or verdict.
    /// Routing evidence is server-owned DATA and remains unqualified; the trusted executor must qualify authority.
    pub fn with_verified_storage_preparation<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,context:&RouteContext,
        routes:&CapabilityRouteCatalog,now:u64,consume:impl FnOnce(PreparedSearchStorage<'_>)->T)->Result<T,SearchStorageError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.with_verified_bytes(provider,context,routes,now,|output|->Result<T,SearchStorageError>{
            let v=self.compiled.candidate.compiler_view();let r=self.compiled.receipt();
            if output.is_empty()||<[u8;32]>::from(Sha256::digest(output))!=r.output_package_sha256
                ||self.manifest.expected_source_sha256()!=r.source_package_sha256{return Err(SearchStorageError::Binding);}
            let validation=bounded_hash(&(SEARCH_STORAGE_PROFILE,r,self.manifest_sha256,output.len()),MAX_METADATA_BYTES)
                .map_err(|_|SearchStorageError::Binding)?;
            let receipt=SearchStorageReceipt {profile:SEARCH_STORAGE_PROFILE,request_schema:r.request_schema,source_package_sha256:r.source_package_sha256,
                output_package_sha256:r.output_package_sha256,output_bytes:output.len(),compiled_plan_sha256:r.compiled_plan_sha256,
                manifest_sha256:self.manifest_sha256,validation_contract_sha256:validation,validation_executed:false,execution_or_native_authority:false};
            v.source.with_verified_compiler_source(provider,now,|source,project,branch,head|->Result<T,SearchStorageError>{
                if source.len()as u64!=self.manifest.expected_source_size()||head.generation()!=r.head_generation
                    ||<[u8;32]>::from(Sha256::digest(source))!=r.source_package_sha256{return Err(SearchStorageError::Binding);}
                let identity=provider.source_search_job_identity(v.project,v.document,v.key,&r.canonical_request_sha256,&r.scoped_request_sha256)?;
                v.source.check_compiler_head(provider)?;
                let prepared=PreparedSearchStorage::bind_verified(source,output,&self.manifest,v.document,(project,branch,head),receipt,identity,
                    (&r.canonical_request_sha256,&r.scoped_request_sha256))?;
                Ok(consume(prepared))
            })?
        })?
    }
    /// Trusted server refreshes routing/time for EVERY ingest and final-CAS boundary.
    /// This is an additional restriction, not a product-route permit. Failure latches for this attempt.
    pub fn current_commit_guard<'a,R,B,S,V,F>(&'a self,provider:&'a StoredFormProvider<'_,R,B,S,V>,mut current:F)->impl StoredPrecommitGuard+'a
    where R:ArtifactMetadataRepository+'a,B:EncryptedBlobStore+'a,S:ArtifactScanner+'a,V:RevisionRepository+'a,
        F:FnMut()->Result<(RouteContext,CapabilityRouteCatalog,u64),()>+'a {
        let mut stopped=false;
        move||{
            if stopped{return Err(StoredCommitError::CurrentGuard);}
            if current().and_then(|(c,r,n)|self.verify(provider,&c,&r,n).map(|_|()).map_err(|_|())).is_err() {
                stopped=true;return Err(StoredCommitError::CurrentGuard);
            }Ok(())
        }
    }
}
