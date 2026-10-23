"""One closed generated-HWPX SQL23 fixture, reusing the original cluster/AEAD campaign.

No old database, Hancom, operational key custody, trusted product or Native route.
Fresh-process restart checks registered rows/head and actual HWPX readback; it is
NOT full immutable-manifest reconstruction or an authorization to replay the job.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original

ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-catalog-447')
PROBE=ROOT/'target/debug/examples/sql23_catalog_storage.exe'
OBSERVATION='target/p09-catalog-sql23-storage-observations-447.json'

def main(identity=False):
    global OWNED,PROBE,OBSERVATION
    if identity:
        OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-catalog-identity-450')
        PROBE=ROOT/'target/debug/examples/sql23_catalog_identity_storage.exe'
        OBSERVATION='target/p09-catalog-identity-sql23-observations-450.json'
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    receipt=dict(state='FAILED_CATALOG_SQL23_STORAGE',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_SQL23_registered_CAS_and_success_completion=False,
        actual_disk_AEAD_readback=False,actual_P09_product_or_Native_execution=False,synthetic_route_and_scanner=True,
        generated_hwpx_and_original_staged_validator=True,full_manifest_reconciliation_qualified=False,
        parent_retained_ephemeral_test_keys=True,operational_database_accessed=False)
    try:
        original.cluster.require(sys.argv[1:]==['--owned-generated-hwpx-catalog-campaign'],'PG_CATALOG_CLOSED_WORKER_MODE')
        original.campaign(receipt)
        original.cluster.require(receipt['state']=='PASS_REAL_DISK_AEAD_SQL23_REGISTERED_CAS_COMPLETION_AND_RESTART_NOT_PRODUCT_OR_P09_GATE'
            and len(receipt['probes'])==5 and receipt['probes'][2]['state']=='PASS_REAL_CATALOG_HWPX_SQL23_GUARDED_JOB_CAS_COMPLETION'
            and receipt['probes'][2]['guard_checks']==3 and receipt['probes'][-1]['state']=='PASS_RESTART_CATALOG_SQL_REGISTERED_ROW_HEAD_AND_ACTUAL_HWPX_AEAD_READBACK',
            'PG_CATALOG_REAL_HWPX_AND_THREE_CURRENT_GUARDS')
        receipt['state']='PASS_GENERATED_CATALOG_HWPX_SQL23_GUARDED_JOB_AEAD_HEAD_RESTART_NOT_TRUSTED_PRODUCT_OR_GATE'
        if identity:
            original.cluster.require(all(receipt['probes'][2].get(k)is True for k in('request_key_bound','retained_claim_replay_observed','changed_request_rejected')),'PG_CATALOG_BOUND_KEY_REPLAY_AND_REJECTED_REQUEST')
            receipt.update(state='PASS_BOUND_CATALOG_REQUEST_KEY_SQL23_REPLAY_REJECTION_AEAD_RESTART_NOT_TRUSTED_PRODUCT_OR_GATE',
                request_key_mapping_exercised=True,cold_public_request_lookup_or_full_recovery_qualified=False)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(state='FAILED_CATALOG_SQL23_STORAGE',error_type=type(error).__name__,
            error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_CATALOG_FAILURE_NO_RAW_VALUES')
    payload=json.dumps(receipt,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_CATALOG_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_CATALOG_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(receipt['probes']))),flush=True)
    return 0 if receipt['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
