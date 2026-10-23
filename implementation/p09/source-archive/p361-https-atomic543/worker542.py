"""542: actual atomic HTTPS policy locks + original SQL CAS, no earlier consumed roots replayed."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
from paced_postgres_hash import PacedPostgresHasher
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-https-atomic-542')
PROBE=ROOT/'target/debug/examples/sql26_https_atomic_recovery.exe'
OBSERVATION='target/p09-https-atomic-sql26-observation-542.json'

def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    hasher=PacedPostgresHasher();original.cluster.runtime.sha_file=hasher.sha_file
    row=dict(state='FAILED_HTTPS_POLICY_SQL26',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],policy_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,operational_database_accessed=False,actual_Hancom_COM_or_Native_started=False,
        synthetic_routes_and_scanner=True,policy_selector_actual_SQL=True,actual_atomic_policy_guard=False,parent_retained_ephemeral_test_keys=True,
        attested_external_issuer_key_custody_product_route_qualified=False)
    def registry(sql,label):
        value=json.loads(sql("SELECT json_build_object('versions',(SELECT count(*) FROM hwpx_agent.source_https_target_policy_versions),"
            "'revocations',(SELECT count(*) FROM hwpx_agent.source_https_target_policy_revocations),'latest',(SELECT max(generation) FROM hwpx_agent.source_https_target_policy_versions));\n",label))
        original.cluster.require(value==dict(versions=2,revocations=1,latest=2),'PG_HTTPS_POLICY_EXACT_IMMUTABLE_REGISTRY_COUNTS');row['policy_snapshots'].append(value)
    def before(sql,probe):probe('--cold-recover');registry(sql,'https_policy_before_restart')
    def after(sql,probe):registry(sql,'https_policy_after_restart')
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema26-https-atomic-542'],'PG_HTTPS_POLICY_CLOSED_MODE')
        original.campaign(row,schema_version=26,after_execute=before,artifact_key_mode='parent_ephemeral',expected_artifacts=9,after_restart=after)
        p=row['probes'];original.cluster.require(len(p)==6 and p[0]['migrations']==26 and p[1]['actual_policy_AEAD_artifact']is True
            and p[1]['policy_selector_isolated_not_operational']is False and p[1]['actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives']is True
            and p[1]['actual_atomic_policy_lock_and_binding_checks']is True
            and p[2]['state']=='PASS_HTTPS_REAL_SQL26_ATOMIC_POLICY_AND_ORIGINAL_REGISTERED_CAS_COMPLETION_NOT_ADMISSION'
            and p[2]['policy_guard_inside_same_original_CAS_transaction']is True
            and p[2]['guard_attached_automatically']is True and p[2]['actual_registered_row_and_AEAD_readback']is True,'PG_HTTPS_POLICY_REAL_SQL_AND_COORDINATOR_REQUIRED')
        original.cluster.require(all(v['state']=='PASS_HTTPS_PUBLIC_REQUEST_REGISTERED_EFFECT_RECOVERY_NO_LOCAL_HANDLES'
            and v['original_paths_absent']==4 and v['actual_HWPX_and_AEAD_readback']is True and v['same_job_attempt_and_revision']is True
            and v['changed_request_conflict']is True and v['missing_is_not_observed']is True and v['claim_lease_CAS_or_execution_retried']is False
            and v['all_original_files_restored_byte_exact']is True for v in(p[3],p[5])),'PG_HTTPS_POLICY_COLD_RECOVERY_BEFORE_AFTER_RESTART')
        original.cluster.require(len(row['policy_snapshots'])==2 and row['policy_snapshots'][0]==row['policy_snapshots'][1],'PG_HTTPS_POLICY_REGISTRY_PRESERVED_ACROSS_RESTART')
        row.update(state='PASS_HTTPS_SQL26_ATOMIC_POLICY_LOCKS_ORIGINAL_CAS_AND_PUBLIC_RECOVERY_NOT_ADMISSION_NATIVE_OR_GATE',https_SQL_cases=1,actual_atomic_policy_guard=True)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(state='FAILED_HTTPS_POLICY_SQL26',error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_HTTPS_POLICY_FAILURE_NO_RAW_VALUES')
    row['fresh_runtime_hash_io']=hasher.profile()
    payload=json.dumps(row,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_HTTPS_POLICY_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_HTTPS_POLICY_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(row['probes']))),flush=True)
    return 0 if row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
