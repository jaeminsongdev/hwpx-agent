use super::*;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::StoredCommitRegistration;

impl<'a,R,B,S,V,F> StoredResultRevisionCas<'a,R,B,S,V,F>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRevisionJobRepository,F:FnMut()->u64,
{
    /// The registrar is the EXACT repository used for the later CAS, not a caller-selected peer.
    /// The supplied lease is syntactically validated, not an authorization issued by this API.
    /// # Errors
    /// Returns the existing source/output/scope binding errors. SQL later checks actual authority.
    #[allow(clippy::too_many_arguments)]
    pub fn bind_registered(artifacts:&'a ArtifactService<R,B,S>,revisions:&'a RevisionService<V>,
        context:&'a RequestContext,revision_context:&'a RevisionRequestContext,binding:StoredCommitBinding<'a>,lease:StoredJobLease,clock:F)
        ->Result<Self,StoredCommitError>{
        let mut result=Self::bind(artifacts,revisions,context,revision_context,binding,clock)?;
        result.job_registration=Some((revisions.repository(),lease));Ok(result)
    }
    /// # Errors
    /// New archived-intent server path. Captures original data before side effects; never issues execution authority.
    #[allow(clippy::too_many_arguments)]
    pub fn bind_registered_archived(artifacts:&'a ArtifactService<R,B,S>,revisions:&'a RevisionService<V>,
        context:&'a RequestContext,revision_context:&'a RevisionRequestContext,binding:StoredCommitBinding<'a>,lease:StoredJobLease,clock:F)
        ->Result<Self,StoredCommitError>{
        let archive=operation_engine::ArchivedExecutionManifest::capture(binding.manifest).map_err(|_|StoredCommitError::Binding)?;
        Self::bind_registered_with_archive(artifacts,revisions,context,revision_context,binding,archive,lease,clock)
    }
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn bind_registered_with_archive(artifacts:&'a ArtifactService<R,B,S>,revisions:&'a RevisionService<V>,
        context:&'a RequestContext,revision_context:&'a RevisionRequestContext,binding:StoredCommitBinding<'a>,archive:operation_engine::ArchivedExecutionManifest,
        lease:StoredJobLease,clock:F)->Result<Self,StoredCommitError>{
        let mut result=Self::bind_registered(artifacts,revisions,context,revision_context,binding,lease,clock)?;
        if archive.canonical_sha256()!=result.manifest_sha256{return Err(StoredCommitError::Binding);}
        result.manifest_archive=Some(archive);Ok(result)
    }
}
impl<R,B,S,V,F> StoredResultRevisionCas<'_,R,B,S,V,F>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,F:FnMut()->u64,
{
    pub(super) fn register_job_intent(&mut self,request:&ServiceRequest)->Result<(),StoredCommitError>{
        let Some((repository,lease))=self.job_registration else{return Ok(())};
        let registration=StoredCommitRegistration::new(lease,request.clone(),
            self.retained_result.as_ref().ok_or(StoredCommitError::Artifact)?,
            self.retained_intent.as_ref().ok_or(StoredCommitError::Artifact)?,
            self.retained_precommit.as_ref().ok_or(StoredCommitError::Artifact)?)
            .map_err(|_|StoredCommitError::Binding)?;
        let record=repository.register_commit_intent(self.revision_context,&registration)
            .map_err(|error|if error==RevisionError::CommitOutcomeUnknown{StoredCommitError::Unknown}else{StoredCommitError::Revision})?;
        let valid=record.validate_for(self.revision_context,&registration).is_ok();
        self.registration_response=Some(record.clone());
        if !valid{return Err(StoredCommitError::Binding);}
        self.registered_job_intent=Some(record);Ok(())
    }
}
