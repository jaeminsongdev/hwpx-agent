"""New owned SQL24 job generation with archived-intent recovery and original files unavailable."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-catalog-archived-custody-468')
PROBE=ROOT/'target/debug/examples/sql24_archived_manifest_custody.exe'
OBSERVATION='target/p09-archived-manifest-custody-sql-observations-468.json'
def cold_before_restart(sql,probe):probe('--cold-recover')
def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    receipt=dict(state='FAILED_ARCHIVED_MANIFEST_CUSTODY_SQL24',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_SQL23_registered_CAS_and_success_completion=False,
        actual_disk_AEAD_readback=False,actual_P09_product_or_Native_execution=False,operational_database_accessed=False,parent_retained_ephemeral_test_keys=False,
        synthetic_route_and_scanner=True,operational_key_provisioning_or_loss_recovery_qualified=False)
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema24-archived-manifest-custody'],'PG_ARCHIVE_CLOSED_WORKER_MODE')
        original.campaign(receipt,schema_version=24,after_execute=cold_before_restart,artifact_key_mode='windows_owned')
        probes=receipt['probes'];original.cluster.require(len(probes)==7 and probes[0]['migrations']==24 and probes[2]['legacy23_constructors_reject24']is True
            and probes[3]['guard_checks']==3 and probes[3]['actual_staged_hwpx_validator']is True,'PG_ARCHIVE_EXACT_V2_JOB_AND_ORIGINAL_STORAGE_PATH')
        cold=[probes[4],probes[-1]['archived_manifest_recovery']]
        original.cluster.require(all(p['state']=='PASS_ARCHIVED_REGISTERED_COMMIT_WITHOUT_ORIGINAL_FILES_OR_RAM'and p['original_files_absent']==3
            and p['original_manifest_or_ServiceRequest_supplied']is False and p['all_original_files_restored_byte_exact']is True
            and p['engine_claim_lease_CAS_or_job_transition_executed']is False for p in cold),'PG_ARCHIVE_READONLY_RECOVERY_BEFORE_AFTER_RESTART_NO_ORIGINAL_FILES')
        original.cluster.require(probes[-1]['execution_retried']is False and all(probes[i]['windows_signed_artifact_readback']['download_HMAC_issued_and_redeemed']is True for i in(3,6)),
            'PG_ARCHIVE_ORIGINAL_AEAD_HWPX_AND_SIGNED_READBACK_PRESERVED')
        receipt.update(state='PASS_SCHEMA24_OS_KEYS_ARCHIVED_MANIFEST_RECOVERY_BEFORE_AFTER_RESTART_WITHOUT_ORIGINAL_FILES_NOT_PRODUCT_OR_GATE',
            actual_archived_manifest_registered_recovery_without_original_files=True,all_original_files_restored_byte_exact=True,actual_windows_keys_in_original_SQL24_artifact_path=True)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(state='FAILED_ARCHIVED_MANIFEST_CUSTODY_SQL24',error_type=type(error).__name__,error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_ARCHIVE_FAILURE_NO_RAW_VALUES')
    payload=json.dumps(receipt,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_ARCHIVE_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_ARCHIVE_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,observation_bytes=len(payload),
        observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(receipt['probes']))),flush=True)
    return 0 if receipt['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
