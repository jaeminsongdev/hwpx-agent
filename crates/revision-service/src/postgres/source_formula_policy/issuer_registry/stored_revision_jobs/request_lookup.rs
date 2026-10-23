//! Schema24 cold-request observation. No claim, lease, retry, executor or no-effect inference.
use super::*;
use lifecycle::{StoredJobObservation,StoredJobOutcome};
use thiserror::Error;
pub(super) const MIGRATION24:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0024_p09_stored_request_lookup.up.sql"));
const SIGNATURE:&str="hwpx_agent.read_stored_revision_request_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint)";
const READ:&str="SELECT r.*,(extract(epoch FROM returned_retry_not_before)*1000000)::bigint AS retry_micros
    FROM hwpx_agent.read_stored_revision_request_v1($1,$2,$3,$4::character(64),$5,$6,$7,$8::character(64),$9::character(64),$10,$11) r";

#[derive(Clone,Eq,PartialEq)]
pub struct StoredRequestLookup{project:ProjectId,branch:BranchId,key:Uuid,job:Uuid,request:Uuid,canonical:ContentDigest,source:ContentDigest,head:crate::RevisionHead}
impl fmt::Debug for StoredRequestLookup{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("StoredRequestLookup(<redacted>; observation_only)")}}
impl StoredRequestLookup{
    /// Trusted request binding only, never an executable permit or client-deserializable claim.
    /// # Errors
    /// Rejects nil IDs, absent/overflowing head and invalid full-width digests.
    #[allow(clippy::too_many_arguments)]
    pub fn new(project:ProjectId,branch:BranchId,key:Uuid,job:Uuid,request:Uuid,canonical:ContentDigest,source:ContentDigest,head:crate::RevisionHead)->Result<Self,RevisionError>{
        if [key,job,request].iter().any(Uuid::is_nil)||head.revision_id().is_none()||head.generation()==0||i64::try_from(head.generation()).is_err()
            ||canonical.as_bytes()==&[0;32]||source.as_bytes()==&[0;32]{return Err(RevisionError::InvalidRequest);}
        Ok(Self{project,branch,key,job,request,canonical,source,head})
    }
    #[must_use]pub const fn project_id(&self)->ProjectId{self.project}
    #[must_use]pub const fn branch_id(&self)->BranchId{self.branch}
    #[must_use]pub const fn job_id(&self)->Uuid{self.job}
    #[must_use]pub const fn idempotency_key(&self)->Uuid{self.key}
}
#[derive(Clone,Debug,Eq,PartialEq,Error)]
pub enum StoredRequestLookupError{
    #[error("stored request key has a different immutable request binding")]KeyConflict,
    #[error("stored request observation is unavailable")]Repository(#[from]RevisionError),
}
/// Neither case authorizes execution. Existing state is not independent committed-effect/readback proof.
#[derive(Clone,Debug,Eq,PartialEq)]
pub enum StoredRequestObservation{NotObserved,Existing(StoredJobObservation)}
pub trait StoredRequestLookupRepository:RevisionRepository{
    /// # Errors
    /// Current authenticated context/project/source ACL and exact original request must be checked.
    /// NotObserved is NOT a claim, no-effect statement or an authorization to retry.
    fn observe_request(&self,context:&RevisionRequestContext,lookup:&StoredRequestLookup)->Result<StoredRequestObservation,StoredRequestLookupError>;
}
pub(super) fn schema24(rows:&[(i64,String,String)])->Result<(),RevisionError>{
    if rows.len()!=24||rows[23]!=(24,"p09.stored_request_lookup_v1".into(),ContentDigest::of(MIGRATION24).hex()){
        return Err(RevisionError::InvalidRequest);}Ok(())
}
fn body()->Result<ContentDigest,RevisionError>{
    let sql=std::str::from_utf8(MIGRATION24).map_err(|_|RevisionError::InvalidRequest)?;
    let start=sql.find("CREATE FUNCTION hwpx_agent.read_stored_revision_request_v1(").ok_or(RevisionError::InvalidRequest)?;
    let text=&sql[start..];let begin=text.find("AS $$").ok_or(RevisionError::InvalidRequest)?+5;
    let end=begin+text[begin..].find("$$;").ok_or(RevisionError::InvalidRequest)?;Ok(ContentDigest::of(text[begin..end].as_bytes()))
}
fn security(flags:[bool;6],actual:ContentDigest)->Result<(),RevisionError>{
    if flags!=[true,true,true,false,true,true]||actual!=body()?{Err(RevisionError::InvalidRequest)}else{Ok(())}
}
fn point_index(flags:[bool;3],columns:&[String],expected:&[&str])->Result<(),RevisionError>{
    if flags!=[true;3]||!columns.iter().map(String::as_str).eq(expected.iter().copied()){Err(RevisionError::InvalidRequest)}else{Ok(())}
}
pub(super) fn admit(client:&mut Client)->Result<(),RevisionError>{
    for(table,columns)in[("idempotency_records",["tenant_id","project_id","idempotency_key"]),("jobs",["tenant_id","project_id","job_id"]) ]{
        let name=format!("hwpx_agent.{table}");
        let row=client.query_one("SELECT i.indisunique,i.indisvalid,i.indisready,ARRAY(SELECT a.attname::text FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum,n)
            JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.attnum ORDER BY k.n) AS columns
            FROM pg_index i WHERE i.indrelid=$1::text::regclass AND i.indisprimary",&[&name]).map_err(db_error)?;
        point_index([value(&row,"indisunique")?,value(&row,"indisvalid")?,value(&row,"indisready")?],&value::<Vec<String>>(&row,"columns")?,&columns)?;
    }
    let row=client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
        p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,p.prosrc,
        (pg_has_role(p.proowner,'USAGE') OR pg_has_role(p.proowner,'SET')) AS owner_role,p.provolatile='s' AS stable,
        NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
        FROM pg_proc p WHERE p.oid=$1::text::regprocedure",&[&SIGNATURE]).map_err(db_error)?;
    security([value(&row,"allowed")?,value(&row,"prosecdef")?,value(&row,"bounded_path")?,value(&row,"owner_role")?,value(&row,"no_public")?,value(&row,"stable")?],
        ContentDigest::of(value::<String>(&row,"prosrc")?.as_bytes()))
}
fn conflict(code:Option<&str>,message:Option<&str>)->bool{code==Some("23505")&&message==Some("STORED_REQUEST_KEY_CONFLICT")}
fn query_error(error: ::postgres::Error)->StoredRequestLookupError{
    if conflict(error.code().map(::postgres::error::SqlState::code),error.as_db_error().map(::postgres::error::DbError::message)){
        StoredRequestLookupError::KeyConflict
    }else{StoredRequestLookupError::Repository(db_error(error))}
}

#[cfg(test)]mod tests{
    use super::*;
    type R=Result<(),Box<dyn std::error::Error>>;
    fn make(key:Uuid,source:ContentDigest,head:crate::RevisionHead)->Result<StoredRequestLookup,RevisionError>{
        StoredRequestLookup::new(ProjectId::parse("prj_00000000000000000000000000000001")?,BranchId::parse("brn_00000000000000000000000000000002")?,
            key,Uuid::from_u128(4),Uuid::from_u128(5),ContentDigest::of(b"request"),source,head)
    }
    fn head()->Result<crate::RevisionHead,RevisionError>{crate::RevisionHead::new(Some(RevisionId::parse("rev_00000000000000000000000000000003")?),1)}
    #[test]fn lookup_binding_rejects_nil_ids_zero_hash_absent_and_overflowing_head()->R{
        assert!(make(Uuid::from_u128(3),ContentDigest::of(b"source"),head()?).is_ok());
        assert!(make(Uuid::nil(),ContentDigest::of(b"source"),head()?).is_err());
        assert!(make(Uuid::from_u128(3),ContentDigest::parse(&"0".repeat(64))?,head()?).is_err());
        assert!(make(Uuid::from_u128(3),ContentDigest::of(b"source"),crate::RevisionHead::empty()).is_err());
        assert!(make(Uuid::from_u128(3),ContentDigest::of(b"source"),crate::RevisionHead::new(head()?.revision_id(),u64::MAX)?).is_err());Ok(())
    }
    #[test]fn lookup_function_requires_rights_definer_fixed_path_nonowner_no_public_and_stable()->R{
        let good=[true,true,true,false,true,true];assert!(security(good,body()?).is_ok());
        for index in 0..6{let mut flags=good;flags[index]=!flags[index];assert!(security(flags,body()?).is_err());}
        assert!(security(good,ContentDigest::of(b"changed body")).is_err());Ok(())
    }
    #[test]fn exact_ready_unique_composite_point_lookup_indexes_are_mandatory()->R{
        let names=["tenant_id","project_id","idempotency_key"];let good=names.iter().map(|s|s.to_string()).collect::<Vec<_>>();point_index([true;3],&good,&names)?;
        for i in 0..3{let mut flags=[true;3];flags[i]=false;assert!(point_index(flags,&good,&names).is_err());}
        assert!(point_index([true;3],&good[..2],&names).is_err());let mut wrong=good;wrong.swap(0,1);assert!(point_index([true;3],&wrong,&names).is_err());Ok(())
    }
    #[test]fn only_exact_sqlstate_and_closed_lookup_message_become_key_conflict(){
        assert!(conflict(Some("23505"),Some("STORED_REQUEST_KEY_CONFLICT")));
        for(code,message)in[(None,None),(Some("08006"),Some("STORED_REQUEST_KEY_CONFLICT")),(Some("23505"),Some("OTHER_CONFLICT")),(Some("23505"),Some("PRIVATE backend details"))]{assert!(!conflict(code,message));}
    }
    #[test]fn query_has_eleven_bound_parameters_and_no_claim_lease_or_mutation(){
        assert_eq!(READ.matches('$').count(),11);assert!(READ.contains("read_stored_revision_request_v1"));
        for word in["INSERT","UPDATE","DELETE","FOR UPDATE","claim_","lease_","schedule_idempotent_retry"]{assert!(!READ.contains(word));}
    }
    #[test]fn observations_and_debug_never_describe_a_lookup_as_an_execution_permit()->R{
        let q=make(Uuid::from_u128(3),ContentDigest::of(b"source"),head()?)?;
        assert_eq!(format!("{q:?}"),"StoredRequestLookup(<redacted>; observation_only)");
        let observed=StoredJobObservation::observed(StoredJobOutcome::Replay,q.job,lifecycle::StoredJobState::Claimed,0,0,None,None,None,None)?;
        assert_ne!(StoredRequestObservation::NotObserved,StoredRequestObservation::Existing(observed));Ok(())
    }
}
impl StoredRequestLookupRepository for LocalPostgresStoredRevisionJobsRepository{
    fn observe_request(&self,context:&RevisionRequestContext,i:&StoredRequestLookup)->Result<StoredRequestObservation,StoredRequestLookupError>{
        self.authorize_context(context)?;if !self.request_lookup_qualified{return Err(RevisionError::InvalidRequest.into());}
        // Separate READ ONLY transaction: STABLE alone does not prevent a called VOLATILE helper writing.
        let mut client=self.inner.client.try_lock().map_err(|_|RevisionError::RepositoryFailure)?;
        let mut tx=client.build_transaction().isolation_level(IsolationLevel::RepeatableRead).read_only(true).start().map_err(db_error)?;
        tx.query_one("SELECT set_config('hwpx_agent.tenant_id',$1,true),set_config('hwpx_agent.subject_sha256',$2,true)",
            &[&context.tenant_id().as_uuid().hyphenated().to_string(),&context.subject().hex()]).map_err(db_error)?;
        let generation=i64::try_from(i.head.generation()).map_err(|_|RevisionError::InvalidRequest)?;
        let row=tx.query_opt(READ,&[&context.tenant_id().as_uuid(),&i.project.as_uuid(),&i.branch.as_uuid(),&context.subject().hex(),&i.key,&i.job,&i.request,
            &i.canonical.hex(),&i.source.hex(),&i.head.revision_id().map(RevisionId::as_uuid),&generation]).map_err(query_error)?;
        let observation=match row{
            None=>StoredRequestObservation::NotObserved,
            Some(row)=>{let observed=lifecycle::decode_observation(&row)?;
                if observed.outcome()!=StoredJobOutcome::Replay||observed.job_id()!=i.job{return Err(RevisionError::RepositoryFailure.into());}
                StoredRequestObservation::Existing(observed)}
        };
        tx.commit().map_err(|_|RevisionError::CommitOutcomeUnknown)?;Ok(observation)
    }
}
