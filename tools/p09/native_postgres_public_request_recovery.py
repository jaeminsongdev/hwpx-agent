"""Fresh owned SQL24/OS-key public request recovery before/after restart; no old job replay."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-public-request-recovery-472')
PROBE=ROOT/'target/debug/examples/sql24_public_request_recovery.exe'
OBSERVATION='target/p09-public-request-recovery-sql-observations-472.json'
def before_restart(sql,probe):probe('--cold-recover')
def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    receipt=dict(state='FAILED_PUBLIC_REQUEST_RECOVERY_SQL24',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_SQL23_registered_CAS_and_success_completion=False,
        actual_disk_AEAD_readback=False,actual_P09_product_or_Native_execution=False,operational_database_accessed=False,parent_retained_ephemeral_test_keys=False,
        synthetic_route_and_scanner=True,operational_key_provisioning_or_loss_recovery_qualified=False)
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema24-public-request-recovery'],'PG_PUBLIC_RECOVERY_CLOSED_MODE')
        original.campaign(receipt,schema_version=24,after_execute=before_restart,artifact_key_mode='windows_owned')
        probes=receipt['probes'];original.cluster.require(len(probes)==7 and probes[0]['migrations']==24 and probes[2]['legacy23_constructors_reject24']is True
            and probes[3]['guard_checks']==3 and probes[3]['actual_staged_hwpx_validator']is True,'PG_PUBLIC_RECOVERY_ORIGINAL_SQL24_HWPX_PATH')
        cold=[probes[4],probes[-1]['public_request_recovery']]
        original.cluster.require(all(p['state']=='PASS_PUBLIC_STRICT_REQUEST_TO_REGISTERED_EFFECT_WITHOUT_MANIFEST_CLAIM_OR_LOCATOR'
            and p['original_paths_absent']==4 and p['only_original_public_request_supplied']is True
            and p['original_manifest_claim_locator_or_ServiceRequest_supplied']is False and p['same_job_attempt_and_result_revision']is True
            and p['typed_changed_request_conflict']is True and p['missing_request_is_not_observed']is True
            and p['all_original_files_restored_byte_exact']is True and p['engine_claim_lease_CAS_job_transition_or_retry_executed']is False for p in cold),
            'PG_PUBLIC_RECOVERY_REQUEST_TO_EFFECT_BEFORE_AFTER_RESTART_NO_STATE_OR_LOCATOR_FILES')
        original.cluster.require(probes[-1]['execution_retried']is False and all(probes[i]['windows_signed_artifact_readback']['download_HMAC_issued_and_redeemed']is True for i in(3,6)),
            'PG_PUBLIC_RECOVERY_ORIGINAL_READBACK_AND_NO_RETRY')
        receipt.update(state='PASS_SCHEMA24_OS_KEYS_PUBLIC_REQUEST_REGISTERED_RECOVERY_BEFORE_AFTER_RESTART_WITHOUT_MANIFEST_CLAIM_LOCATOR_NOT_PRODUCT_OR_GATE',
            actual_public_request_registered_effect_recovery=True,all_original_files_restored_byte_exact=True)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(state='FAILED_PUBLIC_REQUEST_RECOVERY_SQL24',error_type=type(error).__name__,error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_PUBLIC_RECOVERY_FAILURE_NO_RAW_VALUES')
    payload=json.dumps(receipt,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_PUBLIC_RECOVERY_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_PUBLIC_RECOVERY_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,observation_bytes=len(payload),
        observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(receipt['probes']))),flush=True)
    return 0 if receipt['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
