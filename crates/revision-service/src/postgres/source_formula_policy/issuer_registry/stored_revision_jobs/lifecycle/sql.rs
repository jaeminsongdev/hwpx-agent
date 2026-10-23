use super::*;
use ::postgres::types::ToSql;
const CLAIM:&str="hwpx_agent.claim_stored_revision_job_v1";
const LEASE:&str="hwpx_agent.lease_stored_revision_job_v1";
const ADVANCE:&str="hwpx_agent.advance_idempotent_job_v2";
const COMPLETE:&str="hwpx_agent.complete_stored_revision_job_success_v1";
const UNKNOWN:&str="hwpx_agent.mark_idempotent_outcome_unknown_v2";
const RECONCILE:&str="hwpx_agent.reconcile_stored_revision_job_v1";

// These P14 transitions have no Source-only predicate. Preserve their original SQL bodies,
// and require the same bounded definer/path/PUBLIC/owner checks as the SQL23 entry points.
fn controls()->Result<Vec<(&'static str,ContentDigest)>,RevisionError>{
    let sql=std::str::from_utf8(MIGRATIONS[6]).map_err(|_|RevisionError::InvalidRequest)?;
    ["hwpx_agent.advance_idempotent_job_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,text,text,character)",
        "hwpx_agent.mark_idempotent_outcome_unknown_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,character)"]
        .into_iter().map(|signature|{
            let name=signature.split('(').next().ok_or(RevisionError::InvalidRequest)?;
            let text=&sql[sql.find(&format!("CREATE FUNCTION {name}(" )).ok_or(RevisionError::InvalidRequest)?..];
            let start=text.find("AS $$").ok_or(RevisionError::InvalidRequest)?+5;
            let end=start+text[start..].find("$$;").ok_or(RevisionError::InvalidRequest)?;
            Ok((signature,ContentDigest::of(text[start..end].as_bytes())))
        }).collect()
}
fn control_security(flags:[bool;5],body:ContentDigest,expected:ContentDigest)->Result<(),RevisionError>{
    if flags!=[true,true,true,false,true]||body!=expected{return Err(RevisionError::InvalidRequest);}Ok(())
}
pub(super) fn admit_controls(client:&mut Client)->Result<(),RevisionError>{
    for(signature,expected)in controls()?{
        let r=client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
            p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,p.prosrc,
            (pg_has_role(p.proowner,'USAGE') OR pg_has_role(p.proowner,'SET')) AS owner_role,
            NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
            FROM pg_proc p WHERE p.oid=$1::text::regprocedure",&[&signature]).map_err(db_error)?;
        control_security([value(&r,"allowed")?,value(&r,"prosecdef")?,value(&r,"bounded_path")?,value(&r,"owner_role")?,value(&r,"no_public")?],
            ContentDigest::of(value::<String>(&r,"prosrc")?.as_bytes()),expected)?;
    }Ok(())
}

// Closed SQL identifiers/parameter casts. Never interpolate client strings into SQL.
fn query(function:&str)->Result<String,RevisionError>{
    let casts:&[&str]=match function{
        CLAIM=>&["uuid","uuid","uuid","character(64)","uuid","uuid","uuid","uuid","uuid","bigint","character(64)","character(64)","character(64)","character(64)","character(64)","character(64)","text","character(64)","integer","integer","integer","integer","character(64)"],
        LEASE=>&["uuid","uuid","character(64)","uuid","uuid","uuid","uuid","integer","character(64)"],
        ADVANCE=>&["uuid","uuid","character(64)","uuid","uuid","uuid","uuid","integer","bigint","text","text","character(64)"],
        COMPLETE=>&["uuid","uuid","character(64)","uuid","uuid","uuid","uuid","integer","bigint","uuid","uuid","character(64)"],
        UNKNOWN=>&["uuid","uuid","character(64)","uuid","uuid","uuid","uuid","integer","bigint","uuid","character(64)"],
        RECONCILE=>&["uuid","uuid","character(64)","uuid","uuid","text","uuid","uuid","character(64)"],
        _=>return Err(RevisionError::InvalidRequest),
    };
    let args=casts.iter().enumerate().map(|(i,t)|format!("${}::{t}",i+1)).collect::<Vec<_>>().join(",");
    // Avoid an additional chrono/SQL timestamp dependency; retain exact microsecond time.
    Ok(format!("SELECT r.*, (extract(epoch FROM returned_retry_not_before)*1000000)::bigint AS retry_micros FROM {function}({args}) r"))
}
pub(super) fn decode(row:&Row)->Result<StoredJobObservation,RevisionError>{
    use StoredJobOutcome as O;use StoredJobState as S;
    let outcome=match value::<String>(row,"returned_outcome")?.as_str(){"new"=>O::New,"replay"=>O::Replay,"leased"=>O::Leased,
        "staged"=>O::Staged,"executing"=>O::Executing,"validating"=>O::Validating,"committed"=>O::Committed,"outcome_unknown"=>O::OutcomeUnknown,
        _=>return Err(RevisionError::RepositoryFailure)};
    let state=match value::<String>(row,"returned_state")?.as_str(){"claimed"=>S::Claimed,"in_progress"=>S::InProgress,"retry_pending"=>S::RetryPending,
        "outcome_unknown"=>S::OutcomeUnknown,"terminal_success"=>S::TerminalSuccess,"terminal_failure"=>S::TerminalFailure,_=>return Err(RevisionError::RepositoryFailure)};
    StoredJobObservation::observed(outcome,value(row,"returned_job_id")?,state,value(row,"returned_attempt_count")?,value(row,"returned_fencing_token")?,
        value(row,"retry_micros")?,value::<Option<Uuid>>(row,"returned_result_revision_id")?.map(crate::postgres::revision_id).transpose()?,
        value(row,"returned_terminal_error_code")?,value::<Option<Uuid>>(row,"returned_receipt_artifact_id")?.map(artifact_id).transpose()?)
}
fn event_valid(event:ContentDigest)->Result<(),RevisionError>{if event.as_bytes()==&[0;32]{Err(RevisionError::InvalidRequest)}else{Ok(())}}
impl LocalPostgresStoredRevisionJobsRepository{
    fn lifecycle<T>(&self,context:&RevisionRequestContext,event:ContentDigest,function:&str,args:&[&(dyn ToSql+Sync)],
        validate:impl FnOnce(&Row,StoredJobObservation)->Result<T,RevisionError>)->Result<T,RevisionError>{
        self.authorize_context(context)?;event_valid(event)?;let sql=query(function)?;
        self.inner.scoped(context.tenant_id(),IsolationLevel::ReadCommitted,|tx|{
            let row=tx.query_one(&sql,args).map_err(db_error)?;let observation=decode(&row)?;validate(&row,observation)
        })
    }
}
impl StoredJobLifecycleRepository for LocalPostgresStoredRevisionJobsRepository{
    fn with_job_lease(&self,lease:StoredJobLease)->Self{self.with_received_lease(lease)}
    fn claim_job(&self,c:&RevisionRequestContext,claim:&StoredJobClaim,event:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        let i=claim.input();let generation=i64::try_from(i.expected_head.generation()).map_err(|_|RevisionError::InvalidRequest)?;
        self.lifecycle(c,event,CLAIM,&[&c.tenant_id().as_uuid(),&i.project.as_uuid(),&i.branch.as_uuid(),&c.subject().hex(),&i.key,&i.job,&i.request,
            &i.source.as_uuid(),&i.expected_head.revision_id().map(RevisionId::as_uuid),&generation,&i.request_sha.hex(),&i.manifest_sha.hex(),&i.source_sha.hex(),
            &i.effect_sha.hex(),&i.precommit_sha.hex(),&i.plan_sha.hex(),&i.target_profile,&i.capability_sha.hex(),&i.max_attempts,&i.base_delay_seconds,&i.max_delay_seconds,&i.ttl_seconds,&event.hex()],
            |_,r|{if !matches!(r.outcome(),StoredJobOutcome::New|StoredJobOutcome::Replay)||r.job_id()!=i.job||r.attempt_no()>i.max_attempts{return Err(RevisionError::RepositoryFailure);}Ok(r)})
    }
    fn lease_job(&self,c:&RevisionRequestContext,claim:&StoredJobClaim,agent:Uuid,execution:Uuid,seconds:i32,event:ContentDigest)->Result<StoredJobLease,RevisionError>{
        if agent.is_nil()||execution.is_nil()||!(1..=3600).contains(&seconds){return Err(RevisionError::InvalidRequest);}
        let i=claim.input();self.lifecycle(c,event,LEASE,&[&c.tenant_id().as_uuid(),&i.project.as_uuid(),&c.subject().hex(),&i.key,&i.job,&agent,&execution,&seconds,&event.hex()],
            |row,r|{r.expect(i.job,StoredJobOutcome::Leased,None)?;if r.attempt_no()>i.max_attempts{return Err(RevisionError::RepositoryFailure);}
                StoredJobLease::new(RevisionLeaseIdentity{idempotency_key:i.key,job_id:i.job,agent_instance_id:agent,execution_id:execution,
                    attempt_no:r.attempt_no(),fencing_token:r.fencing_token(),authorization_id:value(row,"returned_commit_authorization_id")?})})
    }
    fn advance_job(&self,c:&RevisionRequestContext,project:ProjectId,lease:StoredJobLease,stage:StoredJobAdvance,event:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        let i=lease.identity();let(expected,next,outcome)=stage.states();
        self.lifecycle(c,event,ADVANCE,&[&c.tenant_id().as_uuid(),&project.as_uuid(),&c.subject().hex(),&i.idempotency_key,&i.job_id,&i.agent_instance_id,
            &i.execution_id,&i.attempt_no,&i.fencing_token,&expected,&next,&event.hex()],|_,r|{r.expect(i.job_id,outcome,Some(i.attempt_no))?;Ok(r)})
    }
    fn complete_job(&self,c:&RevisionRequestContext,project:ProjectId,lease:StoredJobLease,revision:RevisionId,precommit:ArtifactId,event:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        let i=lease.identity();self.lifecycle(c,event,COMPLETE,&[&c.tenant_id().as_uuid(),&project.as_uuid(),&c.subject().hex(),&i.idempotency_key,&i.job_id,&i.agent_instance_id,
            &i.execution_id,&i.attempt_no,&i.fencing_token,&revision.as_uuid(),&precommit.as_uuid(),&event.hex()],|_,r|{
                r.expect(i.job_id,StoredJobOutcome::Committed,Some(i.attempt_no))?;
                if r.result_revision_id()!=Some(revision)||r.receipt_artifact_id()!=Some(precommit){return Err(RevisionError::RepositoryFailure);}Ok(r)})
    }
    fn mark_job_unknown(&self,c:&RevisionRequestContext,project:ProjectId,lease:StoredJobLease,receipt:ArtifactId,event:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        let i=lease.identity();self.lifecycle(c,event,UNKNOWN,&[&c.tenant_id().as_uuid(),&project.as_uuid(),&c.subject().hex(),&i.idempotency_key,&i.job_id,&i.agent_instance_id,
            &i.execution_id,&i.attempt_no,&i.fencing_token,&receipt.as_uuid(),&event.hex()],|_,r|{
                r.expect(i.job_id,StoredJobOutcome::OutcomeUnknown,Some(i.attempt_no))?;
                if r.receipt_artifact_id()!=Some(receipt){return Err(RevisionError::RepositoryFailure);}Ok(r)})
    }
    fn reconcile_job_committed(&self,c:&RevisionRequestContext,lookup:StoredCommitIntentLookup,revision:RevisionId,precommit:ArtifactId,event:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        self.lifecycle(c,event,RECONCILE,&[&c.tenant_id().as_uuid(),&lookup.project.as_uuid(),&c.subject().hex(),&lookup.key,&lookup.job,&"committed",
            &revision.as_uuid(),&precommit.as_uuid(),&event.hex()],|_,r|{r.expect(lookup.job,StoredJobOutcome::Committed,Some(lookup.attempt))?;
                if r.result_revision_id()!=Some(revision)||r.receipt_artifact_id()!=Some(precommit){return Err(RevisionError::RepositoryFailure);}Ok(r)})
    }
}

#[cfg(test)]
mod tests{
    use super::*;
    #[test]fn all_six_queries_have_closed_names_and_exact_parameter_casts()->Result<(),RevisionError>{
        for(name,count)in[(CLAIM,23),(LEASE,9),(ADVANCE,12),(COMPLETE,12),(UNKNOWN,11),(RECONCILE,9)]{
            let q=query(name)?;assert!(q.contains(&format!("FROM {name}(")));assert_eq!(q.matches('$').count(),count);
            assert!(q.contains("AS retry_micros"));assert!(q.contains("$3::character(64)")||name==CLAIM);
        }
        assert!(query("hwpx_agent.claim_idempotent_job_v2").is_err());assert!(query("x); DROP SCHEMA hwpx_agent").is_err());Ok(())
    }
    #[test]fn zero_event_is_rejected_without_a_query()->Result<(),Box<dyn std::error::Error>>{assert!(event_valid(ContentDigest::of(b"event")).is_ok());assert!(event_valid(ContentDigest::parse(&"0".repeat(64))?).is_err());Ok(())}
    #[test]fn only_two_unchanged_source_independent_controls_are_admitted()->Result<(),RevisionError>{
        let c=controls()?;assert_eq!(c.len(),2);assert!(c[0].0.starts_with(ADVANCE));assert!(c[1].0.starts_with(UNKNOWN));
        assert_ne!(c[0].1,c[1].1);assert!(c.iter().all(|v|v.1.as_bytes()!=&[0;32]));Ok(())
    }
    #[test]fn every_unsafe_control_privilege_or_body_fails_closed(){
        let h=ContentDigest::of(b"body");let good=[true,true,true,false,true];assert!(control_security(good,h,h).is_ok());
        for i in 0..5{let mut bad=good;bad[i]=!bad[i];assert!(control_security(bad,h,h).is_err());}
        assert!(control_security(good,ContentDigest::of(b"altered"),h).is_err());
    }
}
