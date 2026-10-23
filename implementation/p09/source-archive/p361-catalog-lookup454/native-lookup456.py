"""One fresh schema24 read-only cold lookup campaign, original SQL23 pipeline preserved.

Only this parent owns test admin credentials. Lookup/execution children receive
the original least-privileged application-role credentials, never admin secrets.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-catalog-lookup-454')
PROBE=ROOT/'target/debug/examples/sql24_catalog_request_lookup.exe'
OBSERVATION='target/p09-catalog-cold-request-lookup-observations-454.json'
def acl_checks(sql,probe):
    project="tenant_id='00000000-0000-0000-0000-000000000001'::uuid AND project_id='00000000-0000-0000-0000-000000000002'::uuid AND subject_sha256=repeat('a',64)"
    source="tenant_id='00000000-0000-0000-0000-000000000001'::uuid AND subject_sha256=repeat('a',64) AND artifact_id=(SELECT source_artifact_id FROM hwpx_agent.idempotency_records WHERE tenant_id='00000000-0000-0000-0000-000000000001'::uuid AND project_id='00000000-0000-0000-0000-000000000002'::uuid AND expected_revision_id='00000000-0000-0000-0000-000000000014'::uuid)"
    try:
        original.cluster.require(sql(f"UPDATE hwpx_agent.project_acl SET role='reader' WHERE {project} RETURNING true;\n",'lookup_fixture_project_acl_revoke')=='t','PG_LOOKUP_EXACT_ONE_PROJECT_ACL')
        probe('--lookup-denied')
    finally:sql(f"UPDATE hwpx_agent.project_acl SET role='owner' WHERE {project};\n",'lookup_fixture_project_acl_restore')
    probe('--lookup-restored')
    try:
        original.cluster.require(sql(f"UPDATE hwpx_agent.artifact_acl SET can_read=false,can_manage=false WHERE {source} RETURNING true;\n",'lookup_fixture_source_acl_revoke')=='t','PG_LOOKUP_EXACT_ONE_SOURCE_ACL')
        probe('--lookup-denied')
    finally:sql(f"UPDATE hwpx_agent.artifact_acl SET can_read=true,can_manage=true WHERE {source};\n",'lookup_fixture_source_acl_restore')
    probe('--lookup-restored')
def main():
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    receipt=dict(state='FAILED_CATALOG_COLD_REQUEST_LOOKUP',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],database_root=str(OWNED/'cluster'),
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_SQL23_registered_CAS_and_success_completion=False,
        actual_disk_AEAD_readback=False,actual_P09_product_or_Native_execution=False,operational_database_accessed=False,
        parent_retained_ephemeral_test_keys=True,synthetic_route_and_scanner=True,lookup_children_receive_admin_password=False)
    try:
        original.cluster.require(sys.argv[1:]==['--owned-schema24-cold-lookup'],'PG_LOOKUP_CLOSED_WORKER_MODE')
        original.campaign(receipt,schema_version=24,after_execute=acl_checks)
        probes=receipt['probes'];original.cluster.require(len(probes)==9 and probes[0]['migrations']==24 and probes[1]['legacy23_constructors_reject24']is True
            and probes[2]['cold_request_lookup']['cold_lookup']is True and probes[2]['cold_request_lookup']['typed_changed_request_conflict']is True
            and probes[2]['cold_request_lookup']['missing_is_not_observed']is True
            and sum(p['state']=='PASS_COLD_LOOKUP_CURRENT_SQL_ACL_DENIAL'for p in probes)==2
            and probes[-1]['cold_request_lookup']['cold_lookup']is True,'PG_LOOKUP_EXACT24_COLD_CONFLICT_MISSING_ACL_RESTART')
        receipt.update(state='PASS_SCHEMA24_COLD_PUBLIC_REQUEST_LOOKUP_NO_RECOMPILE_ACL_CONFLICT_RESTART_NOT_PRODUCT_OR_GATE',actual_SQL24_cold_request_observation=True,
            actual_current_project_and_source_acl_denials=True,actual_old_schema23_denies24=True,lookup_result_is_not_execution_or_completed_effect_authority=True)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=str(error);receipt.update(state='FAILED_CATALOG_COLD_REQUEST_LOOKUP',error_type=type(error).__name__,error_code=code if re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_LOOKUP_FAILURE_NO_RAW_VALUES')
    payload=json.dumps(receipt,separators=(',',':')).encode();original.cluster.require(len(payload)<=262144,'PG_LOOKUP_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION;original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),'PG_LOOKUP_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=receipt['state'],stage=receipt['stage'],error_code=receipt.get('error_code'),observation_path=OBSERVATION,observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(receipt['probes']))),flush=True)
    return 0 if receipt['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
