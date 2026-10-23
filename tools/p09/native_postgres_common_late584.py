"""Prepared584: common request's late policy revoke -> original CAS denial -> restart observation.

One fresh owned database only. Never replay545/571 or execute Native. Run only
under the normal resource/lock verifier after external CROSSREF005 is terminal.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import native_postgres_storage as original
from paced_postgres_hash import PacedPostgresHasher
ROOT=original.ROOT
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-common-late-584')
PROBE=ROOT/'target/debug/examples/sql26_https_common_late584.exe'
OBSERVATION='target/p09-common-late-sql26-observation-584.json'


def registry_snapshot(value):
    original.cluster.require(type(value)is dict and set(value)=={'versions','revocations','latest'}
        and all(type(v)is int for v in value.values())and value==dict(versions=1,revocations=1,latest=1),
        'PG_COMMON_LATE584_ONE_POLICY_ONE_REVOCATION_NO_REISSUE')
    return dict(value)


def validate_probes(probes):
    original.cluster.require(type(probes)is list and len(probes)==4,'PG_COMMON_LATE584_FOUR_PROBES_NO_DUPLICATE_RECOVERY')
    fixture,seed,result,recovered=probes
    original.cluster.require(fixture['migrations']==26 and seed['actual_policy_AEAD_artifact']is True
        and seed['actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives']is False
        and seed['actual_atomic_policy_lock_and_binding_checks']is False,'PG_COMMON_LATE584_MINIMAL_POLICY_SEED_NOT_OLD_MATRIX')
    original.cluster.require(result['state']=='PASS_COMMON_LATE584_ORIGINAL_SQL_CAS_DENIAL_AND_EVIDENCE_NOT_ADMISSION'
        and result['common_policy_bound_dispatch']is True and result['last_app_guard_reads_completed']is True
        and result['original_SQL_CAS_denied']is True and result['result_intent_precommit_AEAD_retained']is True
        and result['source_and_head_preserved']is True and type(result['current_route_callbacks'])is int
        and result['current_route_callbacks']==5 and result['route_unqualified']is True,
        'PG_COMMON_LATE584_COMMON_ENTRY_AND_ORIGINAL_SQL_DENIAL_REQUIRED')
    expected=dict(state='PASS_COMMON_LATE584_REGISTERED_UNCOMMITTED_OBSERVATION_NO_REEXECUTION',
        common_existing_without_policy_or_compilation=True,registered_effect_not_observed_not_no_effect_proof=True,
        job_in_progress_not_success=True,head_generation=1,attempt=1,fencing_token=1,claim_lease_CAS_or_execution_retried=False)
    for observed in(result['read_only_observation'],recovered):
        original.cluster.require(type(observed)is dict and set(observed)==set(expected)
            and all(type(observed[k])is type(v)and observed[k]==v for k,v in expected.items()),
            'PG_COMMON_LATE584_SAME_UNCOMMITTED_ATTEMPT_BEFORE_AND_AFTER_RESTART_NO_RETRY')


def main():
    original.cluster.require(sys.argv[1:]==['--owned-schema26-common-late-584'],'PG_COMMON_LATE584_CLOSED_MODE')
    original.OWNED,original.PROBE,original.OBSERVATION=OWNED,PROBE,OBSERVATION
    hasher=PacedPostgresHasher();original.cluster.runtime.sha_file=hasher.sha_file
    row=dict(state='FAILED_COMMON_LATE584_SQL26',stage='preflight',commands=[],probes=[],snapshots=[],blob_snapshots=[],policy_snapshots=[],
        database_root=str(OWNED/'cluster'),actual_owned_postmaster_started=False,operational_database_accessed=False,
        actual_Hancom_COM_or_Native_started=False,synthetic_routes_and_scanner=True,policy_selector_actual_SQL=True,
        parent_retained_ephemeral_test_keys=True,old545_571_and_old_negative_matrix_replayed=False,
        attested_external_issuer_key_custody_product_route_qualified=False)
    def registry(sql,*_):
        value=json.loads(sql("SELECT json_build_object('versions',(SELECT count(*) FROM hwpx_agent.source_https_target_policy_versions),"
            "'revocations',(SELECT count(*) FROM hwpx_agent.source_https_target_policy_revocations),'latest',(SELECT max(generation) FROM hwpx_agent.source_https_target_policy_versions));\n",
            'common_late584_current_policy_registry'))
        # Preserve a bounded, validated-shape observation before its exact-value assertion.
        original.cluster.require(type(value)is dict and set(value)=={'versions','revocations','latest'}
            and all(type(v)is int and 0<=v<=10000000 for v in value.values()),'PG_COMMON_LATE584_REGISTRY_SHAPE')
        row['policy_snapshots'].append(dict(value));registry_snapshot(value)
    try:
        original.campaign(row,schema_version=26,after_execute=registry,after_restart=registry,
            expected_artifacts=7,execution_outcome='https_policy_denied')
        validate_probes(row['probes'])
        original.cluster.require(len(row['policy_snapshots'])==2 and row['policy_snapshots'][0]==row['policy_snapshots'][1],
            'PG_COMMON_LATE584_POLICY_ROWS_UNCHANGED_ACROSS_RESTART')
        row.update(state='PASS_COMMON_SQL26_LATE_REVOCATION_DENIED_AND_RESTART_OBSERVATION_NOT_NATIVE_OR_GATE',
            actual_common_dispatch_atomic_policy_CAS_denial=True,common_existing_after_restart_without_reexecution=True,
            duplicate_equivalent_recovery_executed=False,new_SQL_cases=1)
    except(ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('PG_[A-Z0-9_]{1,110}',code)else'PG_COMMON_LATE584_FAILURE_NO_RAW_VALUES')
    row['fresh_runtime_hash_io']=hasher.profile();payload=json.dumps(row,separators=(',',':')).encode()
    original.cluster.require(len(payload)<=262144,'PG_COMMON_LATE584_OBSERVATION_BOUND')
    path=ROOT/OBSERVATION
    original.cluster.require(not path.exists()and path.parent.is_dir()and not path.parent.is_symlink()and not path.parent.is_junction(),
        'PG_COMMON_LATE584_IMMUTABLE_OBSERVATION')
    with path.open('xb')as stream:stream.write(payload)
    print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),observation_path=OBSERVATION,
        observation_bytes=len(payload),observation_sha256=hashlib.sha256(payload).hexdigest(),probe_count=len(row['probes']))),flush=True)
    return 0 if row['state'].startswith('PASS_')else 2


if __name__=='__main__':raise SystemExit(main())
