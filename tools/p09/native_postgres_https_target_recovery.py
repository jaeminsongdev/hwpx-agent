"""537: one fresh HTTPS SQL job; synthetic policy selector/routes, real disk crypto and SQL lifecycle."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
from paced_postgres_hash import PacedPostgresHasher
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-https-target-537')
PROBE=ROOT/'target/debug/examples/sql24_https_target_recovery.exe'
OBSERVATION='target/p09-https-sql24-observation-537.json'

def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    hasher=PacedPostgresHasher();original.cluster.runtime.sha_file=hasher.sha_file
    row=dict(state='FAILED_HTTPS_SQL24',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,operational_database_accessed=False,actual_Hancom_COM_or_Native_started=False,
        synthetic_policy_selector_routes_and_scanner=True,parent_retained_ephemeral_test_keys=True,operational_key_custody_or_product_route_qualified=False)
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema24-https-target-537'],'PG_HTTPS_CLOSED_MODE')
        original.campaign(row,schema_version=24,after_execute=lambda sql,probe:probe('--cold-recover'),artifact_key_mode='parent_ephemeral',expected_artifacts=7)
        p=row['probes'];original.cluster.require(len(p)==6 and p[0]['migrations']==24 and p[1]['actual_policy_AEAD_artifact']is True
            and p[2]['state']=='PASS_HTTPS_REAL_SQL24_GUARDED_JOB_REGISTERED_CAS_COMPLETION_NOT_ADMISSION'
            and p[2]['guard_attached_automatically']is True and p[2]['actual_registered_row_and_AEAD_readback']is True,'PG_HTTPS_REAL_COORDINATOR_REQUIRED')
        original.cluster.require(all(v['state']=='PASS_HTTPS_PUBLIC_REQUEST_REGISTERED_EFFECT_RECOVERY_NO_LOCAL_HANDLES'
            and v['original_paths_absent']==4 and v['actual_HWPX_and_AEAD_readback']is True and v['same_job_attempt_and_revision']is True
            and v['changed_request_conflict']is True and v['missing_is_not_observed']is True and v['claim_lease_CAS_or_execution_retried']is False
            and v['all_original_files_restored_byte_exact']is True for v in(p[3],p[5])),'PG_HTTPS_COLD_RECOVERY_BEFORE_AFTER_RESTART')
        row.update(state='PASS_HTTPS_REAL_SQL24_ONE_GUARDED_JOB_AND_PUBLIC_REGISTERED_EFFECT_RECOVERY_NOT_ADMISSION_NATIVE_OR_GATE',https_SQL_cases=1)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(state='FAILED_HTTPS_SQL24',error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_HTTPS_FAILURE_NO_RAW_VALUES')
    row['fresh_runtime_hash_io']=hasher.profile()
    payload=json.dumps(row,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_HTTPS_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_HTTPS_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(row['probes']))),flush=True)
    return 0 if row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
