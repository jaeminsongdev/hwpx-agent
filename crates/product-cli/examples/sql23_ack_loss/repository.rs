//! Inject one lost application acknowledgement; SQL effects remain real and observable.
//! Never claims a PostgreSQL transport fault. No retry or outcome mutation is added here.
use super::*;
#[derive(Default)]pub struct Calls{pub fired:AtomicBool,pub cas:AtomicUsize,pub register:AtomicUsize,pub complete:AtomicUsize,pub unknown:AtomicUsize}
#[derive(Clone)]pub struct AckRepository{pub inner:LocalPostgresStoredRevisionJobsRepository,pub case:String,pub calls:Arc<Calls>}
impl AckRepository{
    pub fn new(inner:LocalPostgresStoredRevisionJobsRepository,case:String)->Self{Self{inner,case,calls:Arc::default()}}
    fn lost<T>(&self)->Result<T,RevisionError>{if self.calls.fired.swap(true,Ordering::SeqCst){return Err(RevisionError::InvalidRequest);}Err(RevisionError::CommitOutcomeUnknown)}
    fn drop_ack<T>(&self,result:Result<T,RevisionError>)->Result<T,RevisionError>{result?;self.lost()}
    pub fn counts(&self)->Value{json!({"injected":self.calls.fired.load(Ordering::SeqCst),"cas_calls":self.calls.cas.load(Ordering::SeqCst),
        "register_calls":self.calls.register.load(Ordering::SeqCst),"complete_calls":self.calls.complete.load(Ordering::SeqCst),"unknown_calls":self.calls.unknown.load(Ordering::SeqCst)})}
}
impl RevisionRepository for AckRepository{
    fn authorize_context(&self,c:&RevisionRequestContext)->Result<(),RevisionError>{self.inner.authorize_context(c)}
    fn compare_and_swap(&self,c:&RevisionRequestContext,r:&RevisionCommitRequest)->Result<CommitOutcome,RevisionError>{
        self.calls.cas.fetch_add(1,Ordering::SeqCst);
        if self.case=="cas_before"{return self.lost();}
        let observed=self.inner.compare_and_swap(c,r);if self.case=="cas_after"{self.drop_ack(observed)}else{observed}}
    fn head(&self,t:TenantId,p:ProjectId,b:BranchId)->Result<RevisionHead,RevisionError>{self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:ProjectId,r:RevisionId)->Result<RevisionNode,RevisionError>{self.inner.node(t,p,r)}
}
impl StoredRevisionJobRepository for AckRepository{
    fn register_commit_intent(&self,c:&RevisionRequestContext,r:&StoredCommitRegistration)->Result<StoredCommitIntentRecord,RevisionError>{
        self.calls.register.fetch_add(1,Ordering::SeqCst);let observed=self.inner.register_commit_intent(c,r);
        if self.case=="register_after"{self.drop_ack(observed)}else{observed}}
    fn read_commit_intent(&self,c:&RevisionRequestContext,l:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,RevisionError>{self.inner.read_commit_intent(c,l)}
}
impl StoredJobLifecycleRepository for AckRepository{
    fn with_job_lease(&self,l:StoredJobLease)->Self{Self{inner:self.inner.with_job_lease(l),case:self.case.clone(),calls:Arc::clone(&self.calls)}}
    fn claim_job(&self,c:&RevisionRequestContext,r:&StoredJobClaim,e:ContentDigest)->Result<StoredJobObservation,RevisionError>{self.inner.claim_job(c,r,e)}
    fn lease_job(&self,c:&RevisionRequestContext,r:&StoredJobClaim,a:Uuid,x:Uuid,s:i32,e:ContentDigest)->Result<StoredJobLease,RevisionError>{self.inner.lease_job(c,r,a,x,s,e)}
    fn advance_job(&self,c:&RevisionRequestContext,p:ProjectId,l:StoredJobLease,s:StoredJobAdvance,e:ContentDigest)->Result<StoredJobObservation,RevisionError>{self.inner.advance_job(c,p,l,s,e)}
    fn complete_job(&self,c:&RevisionRequestContext,p:ProjectId,l:StoredJobLease,r:RevisionId,a:ArtifactId,e:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        self.calls.complete.fetch_add(1,Ordering::SeqCst);let observed=self.inner.complete_job(c,p,l,r,a,e);
        if self.case=="complete_after"{self.drop_ack(observed)}else{observed}}
    fn mark_job_unknown(&self,c:&RevisionRequestContext,p:ProjectId,l:StoredJobLease,a:ArtifactId,e:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        self.calls.unknown.fetch_add(1,Ordering::SeqCst);self.inner.mark_job_unknown(c,p,l,a,e)}
    fn reconcile_job_committed(&self,c:&RevisionRequestContext,l:StoredCommitIntentLookup,r:RevisionId,a:ArtifactId,e:ContentDigest)->Result<StoredJobObservation,RevisionError>{self.inner.reconcile_job_committed(c,l,r,a,e)}
}
