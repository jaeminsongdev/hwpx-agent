"""545: atomic fixture state preserves Send+Sync;544 compile failure is retained, no SQL replay."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
from paced_postgres_hash import PacedPostgresHasher
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-https-late-revoke-545')
PROBE=ROOT/'target/debug/examples/sql26_https_late_revoke.exe'
OBSERVATION='target/p09-https-late-revoke-sql26-observation-545.json'
def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    hasher=PacedPostgresHasher();original.cluster.runtime.sha_file=hasher.sha_file
    row=dict(state='FAILED_HTTPS_LATE_REVOKE_SQL26',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],policy_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,operational_database_accessed=False,actual_Hancom_COM_or_Native_started=False,
        synthetic_routes_and_scanner=True,policy_selector_actual_SQL=True,parent_retained_ephemeral_test_keys=True,
        attested_external_issuer_key_custody_product_route_qualified=False,previous_success_case_replayed=False)
    def registry(sql,*_):
        value=json.loads(sql("SELECT json_build_object('versions',(SELECT count(*) FROM hwpx_agent.source_https_target_policy_versions),"
            "'revocations',(SELECT count(*) FROM hwpx_agent.source_https_target_policy_revocations),'latest',(SELECT max(generation) FROM hwpx_agent.source_https_target_policy_versions));\n",'https_late_policy_registry'))
        original.cluster.require(value==dict(versions=1,revocations=1,latest=1),'PG_LATE_POLICY_IMMUTABLE_VERSION_AND_REVOCATION');row['policy_snapshots'].append(value)
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema26-https-late-revoke-545'],'PG_LATE_CLOSED_MODE')
        original.campaign(row,schema_version=26,after_execute=registry,after_restart=registry,expected_artifacts=7,execution_outcome='https_policy_denied')
        p=row['probes'];original.cluster.require(len(p)==4 and p[0]['migrations']==26 and p[1]['actual_policy_AEAD_artifact']is True
            and p[1]['actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives']is False
            and p[1]['actual_atomic_policy_lock_and_binding_checks']is False
            and p[2]['state']=='PASS_HTTPS_REAL_SQL26_LATE_REVOCATION_DENIES_ORIGINAL_CAS_RETAINS_EVIDENCE'
            and p[2]['last_app_guard_reads_completed']is True and p[2]['original_SQL_CAS_denied']is True
            and p[2]['result_intent_precommit_AEAD_retained']is True,'PG_LATE_ACTUAL_ATOMIC_CAS_DENIAL_REQUIRED')
        original.cluster.require(p[3]['state']=='PASS_HTTPS_LATE_REVOCATION_EXISTING_ATTEMPT_NO_REEXECUTION'
            and p[3]['job_in_progress_not_success']is True and p[3]['head_generation']==1 and p[3]['attempt']==1
            and p[3]['claim_lease_CAS_or_execution_retried']is False,'PG_LATE_RESTART_NO_REEXECUTION')
        original.cluster.require(len(row['policy_snapshots'])==2 and row['policy_snapshots'][0]==row['policy_snapshots'][1],'PG_LATE_REGISTRY_UNCHANGED_AFTER_RESTART')
        row.update(state='PASS_HTTPS_SQL26_LATE_POLICY_REVOCATION_ORIGINAL_CAS_DENIAL_AND_RESTART_NO_REEXECUTION_NOT_GATE',new_SQL_denial_cases=1)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(state='FAILED_HTTPS_LATE_REVOKE_SQL26',error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_LATE_FAILURE_NO_RAW_VALUES')
    row['fresh_runtime_hash_io']=hasher.profile()
    payload=json.dumps(row,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_LATE_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_LATE_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(row['probes']))),flush=True)
    return 0 if row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
