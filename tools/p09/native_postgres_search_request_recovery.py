"""Fresh owned SQL24 common-search path + public-request recovery across server restart. No Hancom."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
from paced_postgres_hash import PacedPostgresHasher
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-search-recovery-519')
PROBE=ROOT/'target/debug/examples/sql24_search_request_recovery.exe'
OBSERVATION='target/p09-common-search-sql24-observation-520.json'
def before_restart(sql,probe):probe('--cold-recover')
def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    hasher=PacedPostgresHasher();original.cluster.runtime.sha_file=hasher.sha_file
    row=dict(state='FAILED_COMMON_SEARCH_SQL24',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,operational_database_accessed=False,actual_Hancom_COM_or_Native_started=False,
        parent_retained_ephemeral_test_keys=True,synthetic_route_and_scanner=True,operational_key_custody_qualified=False)
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema24-common-search'],'PG_SEARCH_CLOSED_MODE')
        original.campaign(row,schema_version=24,after_execute=before_restart,artifact_key_mode='parent_ephemeral')
        p=row['probes'];original.cluster.require(len(p)==6 and p[0]['migrations']==24 and p[1]['legacy23_constructors_reject24']is True
            and p[2]['state']=='PASS_COMMON_SEARCH_HWPX_REAL_SQL24_REGISTERED_JOB_AND_CAS_NOT_PRODUCT'and p[2]['guard_checks']==3
            and p[2]['actual_staged_hwpx_validator']is True,'PG_SEARCH_REAL_COMMON_JOB_AND_VALIDATOR')
        original.cluster.require(all(v['state']=='PASS_COMMON_PUBLIC_SEARCH_REQUEST_TO_SQL24_COMMITTED_EFFECT_WITHOUT_MANIFEST_OR_LOCATOR'
            and v['original_paths_absent']==4 and v['same_job_attempt_and_result_revision']is True and v['typed_changed_request_conflict']is True
            and v['missing_request_is_not_observed']is True and v['actual_hwpx_and_AEAD_readback']is True and v['all_original_files_restored_byte_exact']is True
            and v['engine_claim_lease_CAS_job_transition_or_retry_executed']is False for v in(p[3],p[5])),'PG_SEARCH_COLD_EFFECT_RECOVERY_BEFORE_AFTER_RESTART')
        original.cluster.require(p[5]['execution_retried']is False,'PG_SEARCH_NO_EXECUTION_REPLAY')
        row.update(state='PASS_COMMON_SEARCH_SQL24_REAL_JOB_CAS_AND_PUBLIC_EFFECT_RECOVERY_BEFORE_AFTER_RESTART_NOT_NATIVE_OR_GATE',
            common_search_SQL_cases=1,actual_registered_effect_recovery=True)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(state='FAILED_COMMON_SEARCH_SQL24',error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_SEARCH_FAILURE_NO_RAW_VALUES')
    row['fresh_runtime_hash_io']=hasher.profile()
    payload=json.dumps(row,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_SEARCH_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_SEARCH_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(row['probes']))),flush=True)
    return 0 if row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
