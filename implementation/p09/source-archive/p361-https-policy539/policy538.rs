//! Dedicated HTTPS policy domain on the exact25 admitted connection. No form/formula authority transfer.
use super::*;
pub(super) const MIGRATION25:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0025_p09_source_https_target_policy.up.sql"));
const READ:&str="SELECT tenant_id,project_id,branch_id,document_id,policy_version_id,generation,source_revision_id,source_head_generation,
    source_result_artifact_id,source_package_sha256::text,source_provenance_sha256::text,observed_graph_sha256::text,
    policy_artifact_id,policy_artifact_sha256::text,created_by_subject_sha256::text
    FROM hwpx_agent.read_source_https_target_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7)";
const FUNCTIONS:[(&str,bool);5]=[
    ("hwpx_agent.require_source_https_target_policy_role_v1(uuid,uuid,character,boolean)",false),
    ("hwpx_agent.require_source_https_target_policy_artifacts_v1(uuid,character,uuid,character,uuid,character,boolean)",false),
    ("hwpx_agent.register_source_https_target_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character)",true),
    ("hwpx_agent.read_source_https_target_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint)",true),
    ("hwpx_agent.revoke_source_https_target_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint)",true)];
pub struct HttpsPolicyReadRequest{project:ProjectId,branch:BranchId,document:String,head:crate::RevisionHead}
impl fmt::Debug for HttpsPolicyReadRequest{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("HttpsPolicyReadRequest(<redacted>)")}}
impl HttpsPolicyReadRequest{
    /// # Errors
    /// Validates the original SQL document identity and a positive bounded source head, not authority.
    pub fn new(project:ProjectId,branch:BranchId,document:String,head:crate::RevisionHead)->Result<Self,RevisionError>{
        super::super::super::SourceFormulaPolicyReadRequest::new(project,branch,document.clone(),head)?;
        Ok(Self{project,branch,document,head})
    }
}
#[derive(Clone,Eq,PartialEq)]
pub struct HttpsPolicyRecord{pub tenant:TenantId,pub project:ProjectId,pub branch:BranchId,pub document:String,pub version:Uuid,pub generation:u64,
    pub source_head:crate::RevisionHead,pub source_result:ArtifactId,pub source_package:ContentDigest,pub source_provenance:ContentDigest,pub observed_graph:ContentDigest,
    pub policy_artifact:ArtifactId,pub policy_digest:ContentDigest,pub creator:SubjectDigest}
impl fmt::Debug for HttpsPolicyRecord{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("HttpsPolicyRecord(<redacted>)")}}
#[derive(Clone,Copy)]
pub struct HttpsPolicySource{pub result:ArtifactId,pub package:ContentDigest,pub provenance:ContentDigest,pub graph:ContentDigest}
pub struct HttpsPolicyRegistrationRequest{scope:HttpsPolicyReadRequest,expected:i64,version:Uuid,artifact:ArtifactId,digest:ContentDigest,source:HttpsPolicySource}
impl fmt::Debug for HttpsPolicyRegistrationRequest{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("HttpsPolicyRegistrationRequest(<redacted>)")}}
impl HttpsPolicyRegistrationRequest{
    /// # Errors
    /// Rejects nil version, exhausted generation and source/policy alias; data alone confers no privilege.
    pub fn new(scope:HttpsPolicyReadRequest,expected:u64,version:Uuid,artifact:ArtifactId,digest:ContentDigest,source:HttpsPolicySource)->Result<Self,RevisionError>{
        if version.is_nil()||expected>=i64::MAX as u64||artifact==source.result{return Err(RevisionError::InvalidRequest);}
        Ok(Self{scope,expected:i64::try_from(expected).map_err(|_|RevisionError::InvalidRequest)?,version,artifact,digest,source})
    }
}
impl LocalPostgresStoredRevisionJobsRepository{
    fn require_https(&self,c:&RevisionRequestContext)->Result<(),RevisionError>{
        if !self.https_policy_qualified{return Err(RevisionError::InvalidRequest);}self.inner.authorize_context(c)
    }
    /// # Errors
    /// Fixed principal plus current write membership, exact source head/latest/unrevoked policy and both ACLs.
    pub fn read_https_policy(&self,c:&RevisionRequestContext,s:&HttpsPolicyReadRequest)->Result<HttpsPolicyRecord,RevisionError>{
        self.require_https(c)?;self.inner.scoped(c.tenant_id(),IsolationLevel::RepeatableRead,|tx|read(tx,c,s))
    }
    /// # Errors
    /// One original scoped transaction: source/head lock, generation CAS, actual artifact management rights and exact readback.
    /// Unknown commit acknowledgement stays CommitOutcomeUnknown; there is no retry or reconciliation write.
    pub fn register_https_policy(&self,c:&RevisionRequestContext,r:&HttpsPolicyRegistrationRequest)->Result<HttpsPolicyRecord,RevisionError>{
        self.require_https(c)?;
        self.inner.scoped(c.tenant_id(),IsolationLevel::ReadCommitted,|tx|{
            let s=&r.scope;let revision=s.head.revision_id().ok_or(RevisionError::InvalidHead)?.as_uuid();
            let head=i64::try_from(s.head.generation()).map_err(|_|RevisionError::InvalidHead)?;
            let row=tx.query_one("SELECT hwpx_agent.register_source_https_target_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10::character(64),$11::character(64),$12::character(64),$13,$14::character(64)) AS generation",
                &[&c.tenant_id().as_uuid(),&s.project.as_uuid(),&s.branch.as_uuid(),&c.subject().hex(),&s.document,&r.version,&r.expected,&revision,&head,
                &r.source.package.hex(),&r.source.provenance.hex(),&r.source.graph.hex(),&r.artifact.as_uuid(),&r.digest.hex()]).map_err(db_error)?;
            if value::<i64>(&row,"generation")?!=r.expected+1{return Err(RevisionError::RepositoryFailure);}
            let actual=read(tx,c,s)?;
            if actual.version!=r.version||actual.generation!=u64::try_from(r.expected+1).map_err(|_|RevisionError::RepositoryFailure)?
                ||actual.policy_artifact!=r.artifact||actual.policy_digest!=r.digest||actual.creator!=c.subject()
                ||actual.source_result!=r.source.result||actual.source_package!=r.source.package||actual.source_provenance!=r.source.provenance
                ||actual.observed_graph!=r.source.graph{return Err(RevisionError::RepositoryFailure);}Ok(actual)
        })
    }
    /// # Errors
    /// Current editor role and latest-version CAS under a branch lock; no source-head prerequisite or deletion/retry.
    pub fn revoke_https_policy(&self,c:&RevisionRequestContext,s:&HttpsPolicyReadRequest,version:Uuid,generation:u64)->Result<(),RevisionError>{
        self.require_https(c)?;if version.is_nil()||generation==0||generation>i64::MAX as u64{return Err(RevisionError::InvalidRequest);}
        let generation=i64::try_from(generation).map_err(|_|RevisionError::InvalidRequest)?;
        self.inner.scoped(c.tenant_id(),IsolationLevel::ReadCommitted,|tx|{
            tx.query_one("SELECT hwpx_agent.revoke_source_https_target_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7)",
                &[&c.tenant_id().as_uuid(),&s.project.as_uuid(),&s.branch.as_uuid(),&c.subject().hex(),&s.document,&version,&generation]).map_err(db_error)?;Ok(())
        })
    }
}
fn read(tx:&mut ::postgres::Transaction<'_>,c:&RevisionRequestContext,s:&HttpsPolicyReadRequest)->Result<HttpsPolicyRecord,RevisionError>{
    let revision=s.head.revision_id().ok_or(RevisionError::InvalidHead)?.as_uuid();let generation=i64::try_from(s.head.generation()).map_err(|_|RevisionError::InvalidHead)?;
    let r=tx.query_one(READ,&[&c.tenant_id().as_uuid(),&s.project.as_uuid(),&s.branch.as_uuid(),&c.subject().hex(),&s.document,&revision,&generation]).map_err(db_error)?;
    let record=HttpsPolicyRecord{tenant:TenantId::new(value(&r,"tenant_id")?).map_err(|_|RevisionError::RepositoryFailure)?,
        project:ProjectId::parse(&format!("prj_{}",value::<Uuid>(&r,"project_id")?.simple()))?,branch:BranchId::parse(&format!("brn_{}",value::<Uuid>(&r,"branch_id")?.simple()))?,
        document:value(&r,"document_id")?,version:value(&r,"policy_version_id")?,generation:positive_generation(value(&r,"generation")?)?,
        source_head:crate::RevisionHead::new(Some(crate::RevisionId::parse(&format!("rev_{}",value::<Uuid>(&r,"source_revision_id")?.simple()))?),positive_generation(value(&r,"source_head_generation")?)?)?,
        source_result:artifact_id(value(&r,"source_result_artifact_id")?)?,source_package:row_digest(&r,"source_package_sha256")?,source_provenance:row_digest(&r,"source_provenance_sha256")?,
        observed_graph:row_digest(&r,"observed_graph_sha256")?,policy_artifact:artifact_id(value(&r,"policy_artifact_id")?)?,policy_digest:row_digest(&r,"policy_artifact_sha256")?,
        creator:SubjectDigest::parse(&value::<String>(&r,"created_by_subject_sha256")?).map_err(|_|RevisionError::RepositoryFailure)?};
    if record.tenant!=c.tenant_id()||record.project!=s.project||record.branch!=s.branch||record.document!=s.document||record.source_head!=s.head
        ||record.version.is_nil()||record.policy_artifact==record.source_result{return Err(RevisionError::RepositoryFailure);}Ok(record)
}
pub(super) fn schema25(rows:&[(i64,String,String)])->Result<(),RevisionError>{
    if rows.len()!=25||rows[24]!=(25,"p09.source_https_target_policy_v1".into(),ContentDigest::of(MIGRATION25).hex()){return Err(RevisionError::InvalidRequest);}Ok(())
}
pub(super) fn admit(client:&mut Client)->Result<(),RevisionError>{
    for table in["source_https_target_policy_versions","source_https_target_policy_revocations"]{
        let name=format!("hwpx_agent.{table}");let trigger=format!("{table}_immutable");
        let r=client.query_one("SELECT c.relrowsecurity,c.relforcerowsecurity,
            (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')) AS owner_role,
            (has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
              OR has_any_column_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')) AS direct,
            (SELECT count(*)=1 AND bool_and(p.policyname='tenant_isolation' AND p.cmd='ALL' AND p.permissive='PERMISSIVE'
             AND p.qual='(tenant_id = hwpx_agent.current_tenant_id())' AND p.with_check='(tenant_id = hwpx_agent.current_tenant_id())')
             FROM pg_policies p WHERE p.schemaname='hwpx_agent' AND p.tablename=$1) AS policy,
            EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=c.oid AND t.tgname=$3 AND t.tgenabled='O' AND NOT t.tgisinternal
             AND t.tgfoid='hwpx_agent.reject_immutable_change()'::regprocedure) AS immutable
            FROM pg_class c WHERE c.oid=$2::text::regclass",&[&table,&name,&trigger]).map_err(db_error)?;
        if !value::<bool>(&r,"relrowsecurity")?||!value::<bool>(&r,"relforcerowsecurity")?||value::<bool>(&r,"owner_role")?
            ||value::<bool>(&r,"direct")?||!value::<bool>(&r,"policy")?||!value::<bool>(&r,"immutable")?{return Err(RevisionError::InvalidRequest);}
    }
    let sql=std::str::from_utf8(MIGRATION25).map_err(|_|RevisionError::InvalidRequest)?;
    for(signature,allowed)in FUNCTIONS{
        let name=signature.split('(').next().ok_or(RevisionError::InvalidRequest)?;
        let source=&sql[sql.find(&format!("CREATE FUNCTION {name}(")).ok_or(RevisionError::InvalidRequest)?..];
        let begin=source.find("AS $$").ok_or(RevisionError::InvalidRequest)?+5;let end=begin+source[begin..].find("$$;").ok_or(RevisionError::InvalidRequest)?;
        let r=client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
            p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,p.prosrc,
            (pg_has_role(p.proowner,'USAGE') OR pg_has_role(p.proowner,'SET')) AS owner_role,
            NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
            FROM pg_proc p WHERE p.oid=$1::text::regprocedure",&[&signature]).map_err(db_error)?;
        if value::<bool>(&r,"allowed")?!=allowed||!value::<bool>(&r,"prosecdef")?||!value::<bool>(&r,"bounded_path")?||value::<bool>(&r,"owner_role")?
            ||!value::<bool>(&r,"no_public")?||ContentDigest::of(value::<String>(&r,"prosrc")?.as_bytes())!=ContentDigest::of(source[begin..end].as_bytes()){
            return Err(RevisionError::InvalidRequest);}
    }Ok(())
}
