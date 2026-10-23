//! Policy restrictions held through the ORIGINAL leased CAS transaction. No registry/worker execution authority.
use super::*;
use super::https_policy::{HttpsPolicyRecord,HttpsPolicyReadRequest};
pub const SIGNATURE:&str="hwpx_agent.require_https_policy_commit_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,character,character,character,uuid,bigint,uuid,character)";
const GUARD:&str="SELECT hwpx_agent.require_https_policy_commit_v1($1,$2,$3,$4::character(64),$5,$6,$7,$8,$9::character(64),$10::character(64),$11::character(64),$12,$13,$14,$15::character(64))";
const MIGRATION26:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0026_p09_https_policy_atomic_commit.up.sql"));
#[derive(Clone)]pub struct HttpsCommitPolicyBinding{record:HttpsPolicyRecord,actor:SubjectDigest,plan:ContentDigest}
impl fmt::Debug for HttpsCommitPolicyBinding{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("HttpsCommitPolicyBinding(<redacted>; restriction_not_authority)")}}
impl LocalPostgresStoredRevisionJobsRepository{
    /// # Errors
    /// Requires the exact26 admitted connector and syntactically bounded data. SQL rechecks the actual current policy;
    /// neither a caller record nor this binding grants lease, CAS or execution authority.
    pub fn with_atomic_https_policy(&self,record:HttpsPolicyRecord,plan:ContentDigest)->Result<Self,RevisionError>{
        if !self.atomic_https_qualified||record.tenant!=self.inner.context.tenant_id()||record.version.is_nil()||record.generation==0
            ||record.generation>i64::MAX as u64||record.policy_artifact==record.source_result||plan.as_bytes()==&[0;32]{return Err(RevisionError::InvalidRequest);}
        HttpsPolicyReadRequest::new(record.project,record.branch,record.document.clone(),record.source_head)?;
        let mut next=self.clone();next.commit_policy=Some(HttpsCommitPolicyBinding{record,actor:self.inner.context.subject(),plan});Ok(next)
    }
}
impl HttpsCommitPolicyBinding{
    pub(super) fn matches(&self,c:&RevisionRequestContext,r:&RevisionCommitRequest)->Result<(),RevisionError>{
        let p=&self.record;
        if c.tenant_id()!=p.tenant||c.subject()!=self.actor||r.project_id()!=p.project||r.branch_id()!=p.branch||r.expected_head()!=p.source_head
            ||r.source_artifact_id()!=p.source_result||r.operation_plan_sha256()!=self.plan{return Err(RevisionError::InvalidRequest);}Ok(())
    }
    pub(super) fn require_in_transaction(&self,tx:&mut ::postgres::Transaction<'_>,c:&RevisionRequestContext)->Result<(),RevisionError>{
        let p=&self.record;let revision=p.source_head.revision_id().ok_or(RevisionError::InvalidHead)?.as_uuid();
        let head=i64::try_from(p.source_head.generation()).map_err(|_|RevisionError::InvalidHead)?;let generation=i64::try_from(p.generation).map_err(|_|RevisionError::InvalidRequest)?;
        tx.query_one(GUARD,&[&c.tenant_id().as_uuid(),&p.project.as_uuid(),&p.branch.as_uuid(),&c.subject().hex(),&p.document,&revision,&head,&p.source_result.as_uuid(),
            &p.source_package.hex(),&p.source_provenance.hex(),&p.observed_graph.hex(),&p.version,&generation,&p.policy_artifact.as_uuid(),&p.policy_digest.hex()]).map_err(db_error)?;Ok(())
    }
}
pub(super) fn schema26(rows:&[(i64,String,String)])->Result<(),RevisionError>{
    if rows.len()!=26||rows[25]!=(26,"p09.https_policy_atomic_commit_v1".into(),ContentDigest::of(MIGRATION26).hex()){return Err(RevisionError::InvalidRequest);}Ok(())
}
pub(super) fn admit(client:&mut Client)->Result<(),RevisionError>{
    let sql=std::str::from_utf8(MIGRATION26).map_err(|_|RevisionError::InvalidRequest)?;
    let begin=sql.find("AS $$").ok_or(RevisionError::InvalidRequest)?+5;let end=begin+sql[begin..].find("$$;").ok_or(RevisionError::InvalidRequest)?;
    let r=client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
        p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,p.prosrc,
        (pg_has_role(p.proowner,'USAGE') OR pg_has_role(p.proowner,'SET')) AS owner_role,
        NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
        FROM pg_proc p WHERE p.oid=$1::text::regprocedure",&[&SIGNATURE]).map_err(db_error)?;
    if !value::<bool>(&r,"allowed")?||!value::<bool>(&r,"prosecdef")?||!value::<bool>(&r,"bounded_path")?||value::<bool>(&r,"owner_role")?
        ||!value::<bool>(&r,"no_public")?||ContentDigest::of(value::<String>(&r,"prosrc")?.as_bytes())!=ContentDigest::of(sql[begin..end].as_bytes()){
        return Err(RevisionError::InvalidRequest);}Ok(())
}
