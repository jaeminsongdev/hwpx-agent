"""P140 exact owned SQL22 engine evidence; not Rust/crypto/custody/native/Gate integration."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest
import importlib.util

ROOT = Path(__file__).resolve().parents[2]


def module(name,path):
    spec = importlib.util.spec_from_file_location(name,ROOT/path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


PRE = module('p139_preserved','tools/p09/verify_formula_issuer_registry_provision.py')
T = module('p140_source_contracts','tools/p09/tests/test_formula_issuer_registry_sql.py')
D = module('p140_driver',T.DRIVER)
require,pin,read = PRE.require,PRE.pin,PRE.read
CURRENT = 'implementation/p09/evidence/p09-140-formula-issuer-registry-sql.source-progress.v1.json'
REPORT = 'implementation/p09/P09-140_FORMULA_ISSUER_REGISTRY_SQL_REPORT.md'
FAILURE = 'implementation/p09/evidence/p09-140-source-contract-failure.v1.json'
ROLE_GUARD = 'implementation/p09/source-archive/p09-140-initial-role-token-check/tools/p09/tests/test_formula_issuer_registry_sql.py'
INITIAL = 'implementation/p09/source-archive/p09-140-initial-rls-and-cleanup-check/source-preimages.v1.json'
BEFORE_RACE = 'implementation/p09/source-archive/p09-140-pre-concurrent-cas/source-preimages.v1.json'
RESOLUTIONS = [f'implementation/p09/evidence/p09-140-run0{n}-{name}-resolution.v1.json' for n,name in [(1,'failure'),(2,'readiness')]]
RUNTIME = [f'implementation/p09/evidence/p09-140-sql-run0{n}.v1.json' for n in range(1,5)]
DELTA = [T.DRIVER,T.FIXTURE,'tools/p09/tests/test_formula_issuer_registry_sql.py',
    'tools/p09/verify_formula_issuer_registry_sql.py',REPORT,FAILURE]+RESOLUTIONS
ARCHIVES = [INITIAL,BEFORE_RACE,ROLE_GUARD]


def predecessor():
    require(pin(PRE.CURRENT) == {'path':PRE.CURRENT,'bytes':16207,
        'sha256':'8e102423afe1b39f7fb2fe511de43e99c30ffdf595171dced0e930389d9eae81'},'P139_checkpoint_drift')
    with PRE.historical({},set(DELTA+ARCHIVES+RUNTIME+[CURRENT])):
        result = PRE.current()
    require(result['current_provision_cases'] == 8 and result['actual_sql_executed'] is False
        and result['P09_gate'] == 'OPEN' and result['product_complete'] is False,'P139_scope_promoted')
    return result


def contracts():
    result = PRE.contracts(T)
    require(result.testsRun == 8 and result.wasSuccessful() and not result.skipped,'SQL_harness_contracts_failed')
    saved = module('p140_initial_role_guard',ROLE_GUARD)
    saved.ROOT = ROOT
    failed = PRE.contracts(saved)
    finding = read(FAILURE)
    require(failed.testsRun == 8 and len(failed.failures) == 1 and not failed.errors and not failed.skipped
        and failed.failures[0][0]._testMethodName == finding['failed_contract'] and finding['passed'] == 7 and finding['failed'] == 1
        and finding['SQL_or_harness_changed_to_fix_guard'] is False,'SQL_failed_source_guard_not_preserved')
    before = (ROOT/ROLE_GUARD).read_text(encoding='utf-8')
    after = (ROOT/'tools/p09/tests/test_formula_issuer_registry_sql.py').read_text(encoding='utf-8')
    require(before.replace('GRANT ALL|BYPASSRLS;',r'GRANT ALL|\bBYPASSRLS;') == after,'SQL_role_guard_transition_drift')


def resource(doc):
    require(doc['resource_policy'] == {'logical_cpu_limit':1,'priority':'BelowNormal','container_memory_bytes':536870912,
        'container_swap_total_bytes':536870912,'pids_limit':64,'sample_seconds':2,'cpu_stop_percent':85,
        'cpu_stop_consecutive_samples':3,'minimum_available_ram_mib':4096},'SQL_resource_policy_changed')
    require(doc['resource_stop_reason'] is None and 0 < doc['elapsed_seconds'] <= 260 and doc['resource_samples'],
        'SQL_resource_stop_or_missing_observation')
    hot = 0
    for row in doc['resource_samples']:
        require(0 <= row['system_cpu_percent'] <= 100 and row['available_ram_mib'] >= 4096,'SQL_resource_pressure')
        hot = hot+1 if row['system_cpu_percent'] >= 85 else 0
        require(hot < 3,'SQL_sustained_CPU_pressure')


def frozen(doc,before):
    with PRE.historical(before):
        require(len(doc['source_freeze']) == len({p['path'] for p in doc['source_freeze']}) == 26
            and all(pin(p['path']) == p for p in doc['source_freeze']),'SQL_execution_source_binding_drift')
    require(doc['image'] == D.IMAGE and doc['image_id'] == D.IMAGE.rsplit('@',1)[1]
        and re.fullmatch(r'hwpx-agent-p140-[a-f0-9]{12}',doc['container']) is not None
        and doc['run_id'].replace('-','')[:12] == doc['container'].rsplit('-',1)[1], 'SQL_image_or_run_identity_drift')
    for flag in ['native_application_executed','rust_adapters_executed','operational_database_changed',
        'production_key_custody_qualified','real_AEAD_or_signatures_executed','atomic_product_publication_qualified','product_complete']:
        require(doc[flag] is False,'SQL_engine_scope_promoted')
    require(doc['P09_gate'] == 'OPEN','SQL_gate_promoted')
    resource(doc)


def absent(name):
    require(re.fullmatch(r'hwpx-agent-p140-[a-f0-9]{12}',name) is not None,'SQL_cleanup_name_drift')
    docker = shutil.which('docker')
    require(docker is not None,'SQL_cleanup_observer_unavailable')
    result = subprocess.run([docker,'inspect',name],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=15,check=False)
    require(result.returncode != 0 and re.search(r'no such (object|container)',result.stderr,re.IGNORECASE) is not None,
        'SQL_owned_container_absence_unverified')


def executions():
    initial = PRE.archive(INITIAL,2)
    r3 = PRE.archive(BEFORE_RACE,1)
    require(set(initial) == {T.DRIVER,T.FIXTURE} and set(r3) == {T.DRIVER},'SQL_archive_inventory_drift')
    before_ready = r3[T.DRIVER].decode('utf-8').replace(
        '            # The image initialization server accepts only Unix sockets; require the final TCP-listening server.\n','')
    before_ready = before_ready.replace('"pg_isready", "-h", "127.0.0.1", "-U"','"pg_isready", "-U"')
    views = [initial,{T.DRIVER:before_ready.encode('utf-8')},r3,{}]
    docs = [read(p) for p in RUNTIME]
    for doc,view in zip(docs,views):
        frozen(doc,view)
        absent(doc['container'])
    first,second,previous,current = docs
    require(first['state'] == 'FAIL_CLOSED' and first['failed_stage'] == 'SQL22_permission_and_metadata_checks'
        and first['sqlstate'] == '42501' and len(first['migrations_applied']) == 22
        and first['original_full_ir_metadata_assertions'] == 25 and not first['sql_checks_committed']
        and len(first['provisional_check_markers_before_rollback']) == 24 and first['container_removed'] is False
        and first['cleanup_error_code'] == 'owned_container_cleanup_unverified','SQL_initial_failure_not_preserved')
    resolution = read(RESOLUTIONS[0])
    require(resolution['owned_container_confirmed_absent'] is True and resolution['failed_transaction_not_promoted'] is True
        and resolution['access_profiles_or_production_permissions_weakened'] is False,'SQL_initial_resolution_drift')
    require(second['state'] == 'FAIL_CLOSED' and second['failed_stage'] == 'wait_ready'
        and not second['migrations_applied'] and second['actual_sql_executed'] is False and second['container_removed'] is True,
        'SQL_readiness_failure_not_preserved')
    resolution = read(RESOLUTIONS[1])
    require(resolution['direct_cause_not_proven_by_redacted_run02_diagnostic'] is True
        and resolution['production_adapter_retry_added'] is False,'SQL_readiness_failure_scope_promoted')
    expected = re.findall(r"SELECT pg_temp\.(?:ok|denied)\('([a-z0-9_]+)'",(ROOT/T.FIXTURE).read_text(encoding='utf-8'))
    migrations = [pin(p.relative_to(ROOT).as_posix()) for p in sorted((ROOT/'migrations/postgres').glob('*.up.sql'))]
    for doc in [previous,current]:
        require(doc['actual_sql_executed'] is True and doc['schema_versions'] == list(range(1,23))
            and doc['server_version_num'] == 180004 and doc['migrations_applied'] == migrations
            and doc['original_full_ir_metadata_assertions'] == 25 and doc['sql_check_inventory'] == doc['sql_checks_committed'] == expected
            and len(expected) == len(set(expected)) == 37 and not doc['provisional_check_markers_before_rollback']
            and doc['container_removed'] is True,'SQL_actual_engine_evidence_incomplete')
    require(previous['state'] == 'PASS_SQL22_ENGINE_METADATA_ONLY_NOT_RUST_CRYPTO_NATIVE_OR_GATE' and previous['concurrency'] is None,
        'SQL_historical_engine_only_promoted')
    require(current['state'] == 'PASS_SQL22_ENGINE_METADATA_AND_CONTENDED_CAS_NOT_RUST_CRYPTO_NATIVE_OR_GATE'
        and current['concurrency'] == {'state':'PASS_ONE_COMMIT_ONE_STALE_GENERATION_AFTER_REAL_LOCK_WAIT',
            'first_lock_holder_observed':True,'second_lock_wait_observed':True,'first_exit_code':0,'second_exit_code':3,
            'second_sqlstate':'40001','second_error_code':'FORMULA_ISSUER_GENERATION_CHANGED','rows':2,'latest_generation':2,'loser_rows':0,
            'winner_live_named_readback':True,'fixture_only_lock_hold_seconds':3,'production_retry_added':False},
        'SQL_actual_contention_evidence_incomplete')
    return current


def audit():
    old = predecessor()
    contracts()
    doc = executions()
    return {'state':'PASS_OWNED_SQL22_ENGINE_METADATA_CAS_NOT_RUST_CRYPTO_CUSTODY_ATOMIC_NATIVE_OR_GATE',
        'harness_source_contract_tests':8,'failed_guard_replay_count':1,'actual_sql_executed':True,
        'owned_schema_versions':list(range(1,23)),'current_committed_SQL_checks':37,'original_full_ir_metadata_assertions':25,
        'actual_contended_root_CAS_scenarios':1,'failed_engine_runs_preserved':2,'owned_containers_confirmed_absent':4,
        'historical_P139_component_cases':old['current_provision_cases'],'current_sql_receipt_path':RUNTIME[-1],
        'Rust_adapter_actual_database_executed':False,'real_crypto_and_DB_same_run_qualified':False,
        'operational_database_changed':False,'production_key_custody_qualified':False,'atomic_product_publication_qualified':False,
        'native_application_executed':False,'app_freeze_cause_resolved':False,
        'P09_gate':'OPEN','A12_gate':'OPEN','A13_gate':'OPEN','product_complete':False,'goal_status':'active','P10_new_implementation':False}


def groups():
    return {'source_delta':[pin(p) for p in DELTA],'source_archives_added':[pin(p) for p in ARCHIVES],
        'runtime_receipts':[pin(p) for p in RUNTIME],'predecessor_receipts_added':[pin(PRE.CURRENT)],
        'migration_inputs':[pin(p.relative_to(ROOT).as_posix()) for p in sorted((ROOT/'migrations/postgres').glob('*.up.sql'))],
        'original_fixture_inputs':[pin(D.ORIGINAL)]}


def checkpoint():
    result = audit()
    pins = groups()
    return {'schema_version':'hwpx-agent.p09-formula-issuer-registry-sql-source-progress/v1',**result,**pins,
        'previous_source_files_count':1225,'current_source_files_count':1225+len(DELTA),
        'source_inventory_counting':'historical_graph_plus_declared_delta_not_unique_path_union',
        'inherited_raw_pin_entries':3506,'new_raw_pin_entries':sum(len(v) for v in pins.values()),
        'remaining_coarse_groups_minimum':6,'remaining_groups_closed_by_slice':0,'minimum_30_conditions_not_exhaustive':True,
        'native34_state':'NOT_RUN_INPUT_CHANGED_RE_ADMISSION_REQUIRED'}


def current():
    result = checkpoint()
    require(read(CURRENT) == result,'SQL_checkpoint_scope_or_pin_drift')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',action='store_true')
    parser.add_argument('--source',action='store_true')
    args = parser.parse_args()
    resources = D.Resources()
    try:
        resources.start()
        result = checkpoint() if args.checkpoint else audit() if args.source else current()
        require(not resources.stop.is_set(),resources.reason or 'audit_resource_stop')
        hidden = {'source_delta','source_archives_added','runtime_receipts','predecessor_receipts_added','migration_inputs','original_fixture_inputs'}
        print(json.dumps(result if args.checkpoint else {k:v for k,v in result.items() if k not in hidden},indent=2))
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error,ValueError) and re.fullmatch(r'[A-Za-z0-9_]+',str(error)) else 'redacted'
        print(json.dumps({'state':'FAIL_CLOSED','error_code':code,'P09_gate':'OPEN'}))
        raise SystemExit(1) from None
    finally:
        resources.done.set()
        if resources.thread.is_alive():
            resources.thread.join(timeout=3)
