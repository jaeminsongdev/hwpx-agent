"""Fresh owned SQL24/HWPX artifact path; crypto keys exist only in three owned Windows entries.

The original campaign retains DB bootstrap credentials, NOT artifact AES/HMAC material.
Its key installer exits before all application probes. No prior database/job is restarted.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-catalog-custody-464')
PROBE=ROOT/'target/debug/examples/sql24_catalog_windows_custody.exe'
OBSERVATION='target/p09-catalog-windows-custody-sql-observations-464.json'

def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    receipt=dict(state='FAILED_CATALOG_WINDOWS_CUSTODY_SQL24',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_SQL23_registered_CAS_and_success_completion=False,
        actual_disk_AEAD_readback=False,actual_P09_product_or_Native_execution=False,operational_database_accessed=False,
        parent_retained_ephemeral_test_keys=False,artifact_key_bytes_generated_in_parent=False,synthetic_route_and_scanner=True,
        operational_key_provisioning_or_loss_recovery_qualified=False,application_children_receive_admin_password=False)
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema24-windows-custody'],'PG_CUSTODY_CLOSED_WORKER_MODE')
        original.campaign(receipt,schema_version=24,artifact_key_mode='windows_owned')
        probes=receipt['probes']
        original.cluster.require(len(probes)==6 and probes[0]['migrations']==24 and probes[1]['state']=='PASS_OWNED_WINDOWS_KEY_INSTALLER_EXIT_WITHOUT_KEY_EXPORT'
            and probes[2]['legacy23_constructors_reject24']is True and probes[3]['guard_checks']==3
            and probes[3]['actual_staged_hwpx_validator']is True and probes[3]['cold_request_lookup']['cold_lookup']is True
            and probes[-1]['state']=='PASS_RESTART_CATALOG_SQL_REGISTERED_ROW_HEAD_AND_ACTUAL_HWPX_AEAD_READBACK'
            and probes[-1]['execution_retried']is False,'PG_CUSTODY_EXACT_INSTALLER_EXECUTION_AND_RESTART')
        for probe in [probes[0],*probes[2:]]:
            original.cluster.require(probe['artifact_AES_HMAC_environment_absent']is True and probe['key_installer_not_running']is True,'PG_CUSTODY_ALL_APPLICATIONS_WITHOUT_KEY_ENVIRONMENT')
        original.cluster.require(all(probes[i]['windows_signed_artifact_readback']['download_HMAC_issued_and_redeemed']is True
            and probes[i]['windows_signed_artifact_readback']['current_SQL_ACL_and_AEAD_readback']is True for i in(3,5)),'PG_CUSTODY_REAL_SIGNED_ARTIFACT_READBACK_BEFORE_AFTER_RESTART')
        receipt.update(state='PASS_SCHEMA24_HWPX_GUARDED_STORAGE_OS_KEYS_AEAD_SIGNED_READBACK_AND_RESTART_NOT_TRUSTED_PRODUCT_OR_GATE',
            actual_windows_keys_in_original_SQL24_artifact_path=True,key_installer_exited_before_seed_and_execution=True,
            actual_signed_download_readback_before_after_restart=True,actual_source_output_and_receipts_AEAD_readback=True)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(state='FAILED_CATALOG_WINDOWS_CUSTODY_SQL24',error_type=type(error).__name__,error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_CUSTODY_FAILURE_NO_RAW_VALUES')
    payload=json.dumps(receipt,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_CUSTODY_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_CUSTODY_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,observation_bytes=len(payload),
        observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(receipt['probes']))),flush=True)
    return 0 if receipt['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
