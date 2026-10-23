"""Close one exact observed Rust test result without Cargo/test/Native replay.

Original436's erroneous PASS label and CPU-stop fields remain immutable. Only
the exact read-only product observation is eligible; no Native/queue recovery.
"""
import argparse
import ast
import io
import json
from pathlib import PurePosixPath
import re
import time
from types import SimpleNamespace as NS
import unittest

SELF='tools/p09/finalize_catalog_mask_product.py'
TEST='tools/p09/tests/test_finalize_catalog_mask_product.py'
PLAN='implementation/p09/P09_COMPLETION_EXECUTION.md'
ORIGINAL='implementation/p09/evidence/p09-361-personal-info-catalog-mask-product-recovery436.v1.json'
ORIGINAL_SHA='af988e190744040939afe74f9b7fbb4b76023d165689eb93ce56d241cfd5d4cd'
RECOVERY='tools/p09/run_personal_info_catalog_mask_product_recovery.py'
ARCHIVE='implementation/p09/source-archive/p361-catalog-product-finalization436/run_personal_info_catalog_mask_product_recovery.py'
OLD_DRIVER_SHA='c717748c02ddd2f19255424698e501405dfa5712038f340a994fad2061f0db6e'
NEW_DRIVER_SHA='51524d1122367e1af5a09fee8a0ba26cc7abb25118a565b66cedd7b65a5c5893'
PASS='PASS_RETAINED_CATALOG_PRODUCT42_AFFECTED3_FINAL_FRESH_NOT_NATIVE_QUEUE_OR_GATE'
OBSERVED='OBSERVED_CATALOG_PRODUCT45_PENDING_CURRENT_INPUT_CLOSURE'


def require(ok,code):
    if not ok:raise ValueError('CATALOG_FINAL_'+code)


def validate_observation(row,expected):
    require(type(expected)is set and len(expected)==45,'EXPECTED45')
    require(row['error_code']=='STOP_PREPARATION_SYSTEM_PRESSURE90'
        and row['error_type']=='ValueError' and row['cleanup']is True
        and row['state']=='PASS_CATALOG_MASK_PRODUCT42_AFFECTED3_NOT_NATIVE_OR_GATE',
        'EXACT_INCOMPLETE436_NOT_ACCEPTANCE')
    require(row.get('final_fresh_hashes')is None and row['installed_config_final_fresh_hashes']==1,
        'ORIGINAL_FINAL_SOURCE_MISSING')
    require(row['product_cases_executed']==45 and row['new_product_cases']==42
        and row['affected_product_cases']==3 and row['complete_compile_input_closure_checked']is True,
        'OBSERVED_CASE_SCOPE')
    for key in('actual_DB_Hangul_or_COM_started','Native011_executed','prior_Native_replayed',
        'official249_replayed','source_document_mutation','ingest_commit_or_publication','native_execution_authorized'):
        require(row[key]is False,'NO_NATIVE_OR_MUTATION_RECOVERY')
    require(type(row['steps'])is list and len(row['steps'])==1,'ONE_OBSERVED_STEP')
    step=row['steps'][0]
    require(step['stage']=='optimized_catalog_products_shared_compiler45' and type(step['exit_code'])is int
        and step['exit_code']==0 and step['cleanup']is True and step['diagnostics']==[],'STEP_COMPLETED')
    cases=step['tests']
    require(type(cases)is list and len(cases)==45 and all(type(v)in(list,tuple) and len(v)==2
        and type(v[0])is str and v[1]=='ok' for v in cases),'ALL45_PASSED_NO_SKIP')
    require({name for name,_ in cases}==expected,'EXACT_UNIQUE45')
    job=step['owned_job'];account=job['last_job_accounting'];limits=job['limits_readback']
    require(all(job[key]is True for key in('worker_created','job_assigned','target_authorized',
        'owned_tree_empty','cleanup_confirmed','job_handle_closed')) and account['active_processes']==0
        and account['owned_processes']==[],'EXACT_OWNED_TREE_CLOSED')
    mask=limits['affinity_mask']
    require(limits['verified']is True and type(mask)is int and mask>0 and mask&(mask-1)==0
        and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384
        and limits['active_process_limit']==16 and limits['kill_on_close']is True
        and limits['breakaway_disabled']is True,'ORIGINAL_OWNED_GUARDS')
    require(0<account['peak_job_private_percent']<7,'ORIGINAL_JOB_MEMORY_STOP')
    pins=row['source_pins']
    require(type(pins)is list and len(pins)==851,'EXACT_INPUT851')
    paths=set()
    for pin in pins:
        require(type(pin)is dict and set(pin)=={'path','bytes','sha256'} and type(pin['path'])is str,
            'INPUT_PIN_SHAPE')
        name=PurePosixPath(pin['path'])
        require(not name.is_absolute() and '..'not in name.parts and ':'not in pin['path']
            and '\\'not in pin['path'] and pin['path']not in paths,'UNIQUE_ROOTED_INPUT')
        require(type(pin['bytes'])is int and pin['bytes']>=0 and type(pin['sha256'])is str
            and re.fullmatch('[a-f0-9]{64}',pin['sha256'])is not None,'INPUT_PIN_TYPES')
        paths.add(pin['path'])
    require(RECOVERY in paths and SELF not in paths,'EXACT_OLD_DRIVER_CLOSURE')
    compiled=row['actual_compiled_test_inputs']
    require(type(compiled)is list and len(compiled)==1 and len(compiled[0]['dependency_paths'])==13
        and len(set(compiled[0]['dependency_paths']))==13 and set(compiled[0]['dependency_paths'])<=paths,
        'COMPLETE_ACTUAL_TEST_INPUTS')
    return dict(observed_cases=45,new_cases=42,affected_cases=3,original_inputs=851,
        original_erroneous_PASS_label_is_not_acceptance=True,original_CPU_stop_preserved=True,
        product_or_Native_replay_allowed=False)


def closing_fresh(row,source,installed,guard):
    # One attempt only. Preserve partial counts even when any mandatory check raises.
    require(not row.get('final_fresh_attempted',False),'FINAL_FRESH_NOT_REENTERED')
    row['final_fresh_attempted']=True
    try:
        installed.finish();source.finish();guard.check(force=True)
    finally:
        row.update(fresh_inputs=len(source.snapshots),final_fresh_hashes=source.final_fresh_hashes,
            installed_config_final_fresh_hashes=installed.final_fresh_hashes)


def successful_exit(row):
    count=row.get('fresh_inputs')
    return (row.get('state')==PASS and row.get('cleanup')is True and row.get('error_code')is None
        and row.get('error_type')is None and type(count)is int and count>0
        and type(row.get('final_fresh_hashes'))is int and row['final_fresh_hashes']==count
        and type(row.get('installed_config_final_fresh_hashes'))is int and row['installed_config_final_fresh_hashes']==1)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=int,choices=range(437,445),required=True);args=parser.parse_args(argv)
    import named_style_verification_runtime as runtime
    import resource_sample_table as layout
    import run_personal_info_catalog_mask_product as product
    c,a,shared=runtime.c,runtime.a,runtime.shared
    output=f'implementation/p09/evidence/p09-361-catalog-product-retained-final{args.run}.v1.json'
    require(not(c.ROOT/output).exists(),'IMMUTABLE_OUTPUT')
    selection=runtime.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic()
    row=dict(state=OBSERVED,own_cpu_selection=selection,product_tests_executed=0,Cargo_started=False,
        actual_DB_Hangul_COM_or_Native_started=False,official249_replayed=False,accepted_count_delta=0,
        source_document_mutation=False,ingest_commit_or_publication=False,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        original=layout.unpack(q.json(ORIGINAL));require(q.snapshots[ORIGINAL]['sha256']==ORIGINAL_SHA,'ORIGINAL436_BYTES')
        for name in(SELF,TEST,PLAN,RECOVERY):q.pin(name)
        require(q.snapshots[RECOVERY]['sha256']==NEW_DRIVER_SHA,'EXACT_CURRENT_COMPLETION_FIX_BEFORE_CONTRACTS')
        # Tests load only pure validation functions; no worker, compiler or child.
        from tests import test_finalize_catalog_mask_product as contracts
        contracts.MODULE=__import__(__name__) if __name__!='__main__' else __import__('sys').modules[__name__]
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(contracts))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        require(row['contracts']==dict(run=24,errors=0,failures=0,skipped=0),'ALL_FINALIZATION24')
        text=q.text(product.TEST);expected={product.PREFIX+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}|product.AFFECTED
        row['retained_observation']=validate_observation(original,expected)
        print(json.dumps(dict(state='RETAINED45_NO_REPLAY_CHECKING_ORIGINAL_INPUTS',inputs=851)),flush=True)
        for old in tuple(original['source_pins']):
            if old['path']==RECOVERY:
                archived=q.pin(ARCHIVE);require(archived['sha256']==old['sha256']==OLD_DRIVER_SHA
                    and archived['bytes']==old['bytes'],'ORIGINAL_DRIVER_BYTES_PRESERVED')
                require(q.pin(RECOVERY)['sha256']==NEW_DRIVER_SHA,'EXACT_FINAL_STATUS_FIX')
                row['archived_execution_driver']=dict(original=old,archived=archived,current=q.snapshots[RECOVERY])
            else:require(q.pin(old['path'])==old,'UNCHANGED_ALL_PRODUCT_TEST_AND_RUNTIME_INPUTS')
        for name in(SELF,TEST,PLAN):q.pin(name)
        for name in(SELF,TEST,RECOVERY):ast.parse(q.text(name),filename=name)
        require(shared.source_inventory(guard.check)<=set(q.snapshots),'CURRENT_SOURCE_INVENTORY_COVERED')
        dep=original['actual_compiled_test_inputs'][0]
        require(q.pin(dep['dep_info']['path'])==dep['dep_info'],'EXACT_ACTUAL_DEP_INFO')
        dependencies,_=product.prior.dependencies(dep['dep_info']['path'],guard)
        require(dependencies==dep['dependency_paths'],'UNCHANGED_ACTUAL_DEPENDENCY_LIST')
        image=a.AcceptanceReader(product.CONFIG.parent,guard.check)
        require(image.pin(product.CONFIG.name)==original['installed_config_pins'][0],'EXACT_INSTALLED_CATALOG')
        row['original436_pin']=q.snapshots[ORIGINAL]
        print(json.dumps(dict(state='RETAINED45_FINAL_FRESH_ONLY',inputs=len(q.snapshots),product_replays=0)),flush=True)
        closing_fresh(row,q,image,guard)
        # Mandatory completion is checked before this label is ever installed.
        row.update(state=PASS,retained_product_cases_accepted=45,new_product_cases=42,affected_product_cases=3)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None
        row.update(state='FAILED_RETAINED_CATALOG_PRODUCT_FINALIZATION',error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('[A-Za-z0-9_]{1,180}',code)else'CATALOG_FINAL_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),
            installed_config_pins=[]if image is None else list(image.snapshots.values()),
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            parent_CPU_max=max((s['parent_cpu_machine_percent']for s in samples if s['parent_cpu_machine_percent']is not None),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','contracts','retained_product_cases_accepted',
            'fresh_inputs','final_fresh_hashes','installed_config_final_fresh_hashes','cleanup','elapsed_seconds',
            'system_CPU_max','parent_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if successful_exit(row)else 2


if __name__=='__main__':raise SystemExit(main())
