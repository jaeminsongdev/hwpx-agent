"""Fresh571: common observe/prepare -> original atomic SQL -> one cold observation after restart."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
from paced_postgres_hash import PacedPostgresHasher
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-https-common-571')
PROBE=ROOT/'target/debug/examples/sql26_https_common571_recovery.exe'
OBSERVATION='target/p09-https-common-sql26-observation-571.json'

def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    hasher=PacedPostgresHasher();original.cluster.runtime.sha_file=hasher.sha_file
    row=dict(state='FAILED_HTTPS_COMMON_SQL26',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],policy_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,operational_database_accessed=False,actual_Hancom_COM_or_Native_started=False,
        synthetic_routes_and_scanner=True,policy_selector_actual_SQL=True,parent_retained_ephemeral_test_keys=True,
        old_policy_security_negative_matrix_replayed=False,attested_external_issuer_key_custody_product_route_qualified=False)
    def registry(sql,label):
        value=json.loads(sql("SELECT json_build_object('versions',(SELECT count(*) FROM hwpx_agent.source_https_target_policy_versions),"
            "'revocations',(SELECT count(*) FROM hwpx_agent.source_https_target_policy_revocations),'latest',(SELECT max(generation) FROM hwpx_agent.source_https_target_policy_versions));\n",label))
        original.cluster.require(value==dict(versions=2,revocations=0,latest=2),'PG_HTTPS_COMMON_EXACT_TWO_GENERATIONS_NO_NEGATIVE_MATRIX')
        row['policy_snapshots'].append(value)
    def before(sql,probe):registry(sql,'https_common_policy_before_restart')
    def after(sql,probe):registry(sql,'https_common_policy_after_restart')
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema26-https-common-571'],'PG_HTTPS_COMMON_CLOSED_MODE')
        original.campaign(row,schema_version=26,after_execute=before,artifact_key_mode='parent_ephemeral',expected_artifacts=8,after_restart=after)
        probes=row['probes'];original.cluster.require(len(probes)==5 and probes[0]['migrations']==26
            and probes[1]['actual_policy_AEAD_artifact']is True and probes[1]['actual_two_current_SQL_policy_generations_without_old_negative_matrix']is True
            and probes[1]['actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives']is False
            and probes[1]['actual_atomic_policy_lock_and_binding_checks']is False,'PG_HTTPS_COMMON_MINIMAL_CURRENT_POLICY_SEED_NO_OLD_MATRIX')
        result=probes[2]
        original.cluster.require(result['state']=='PASS_HTTPS_COMMON_SQL26_ORIGINAL_ATOMIC_CAS_COMPLETION_NOT_ADMISSION'
            and result['common_policy_bound_dispatch']is True and result['unavailable_route_before_claim_callback_and_workspace_denied']is True
            and result['guard_attached_automatically']is True and result['policy_guard_inside_same_original_CAS_transaction']is True
            and result['actual_registered_row_and_AEAD_readback']is True and result['source_preserved']is True
            and result['route_unqualified']is True and result['current_route_callbacks']==5,'PG_HTTPS_COMMON_ACTUAL_DISPATCH_TO_ORIGINAL_CAS')
        recovered=probes[4]
        original.cluster.require(recovered['state']=='PASS_HTTPS_PUBLIC_REQUEST_REGISTERED_EFFECT_RECOVERY_NO_LOCAL_HANDLES'
            and recovered['original_paths_absent']==4 and recovered['actual_HWPX_and_AEAD_readback']is True
            and recovered['same_job_attempt_and_revision']is True and recovered['changed_request_conflict']is True
            and recovered['missing_is_not_observed']is True and recovered['claim_lease_CAS_or_execution_retried']is False
            and recovered['all_original_files_restored_byte_exact']is True
            and recovered['common_observation_entry_without_policy_or_compilation']is True,'PG_HTTPS_COMMON_NEW_RESULT_COLD_RECOVERY_NO_EXECUTION_REPLAY')
        original.cluster.require(probes[3]['state']=='PASS_HTTPS_WRONG_AES_KEY_DENIED','PG_HTTPS_COMMON_WRONG_KEY_DENIED')
        original.cluster.require(len(row['policy_snapshots'])==2 and row['policy_snapshots'][0]==row['policy_snapshots'][1],'PG_HTTPS_COMMON_POLICY_ROWS_PRESERVED')
        row.update(state='PASS_COMMON_HTTPS_SQL26_CURRENT_POLICY_ORIGINAL_CAS_AND_COLD_RECOVERY_NOT_NATIVE_OR_GATE',https_SQL_cases=1,
            actual_common_dispatch_atomic_policy_CAS=True,common_prepare_and_recovery_entry=True,duplicate_equivalent_cold_recovery_probe_executed=False)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(state='FAILED_HTTPS_COMMON_SQL26',error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_HTTPS_COMMON_FAILURE_NO_RAW_VALUES')
    row['fresh_runtime_hash_io']=hasher.profile()
    payload=json.dumps(row,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_HTTPS_COMMON_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_HTTPS_COMMON_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(row['probes']))),flush=True)
    return 0 if row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
