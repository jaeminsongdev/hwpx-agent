"""Test-only domain-ir opt1/64CGU comparison under unchanged owned hard caps.

No source/algorithm/auth/assertion removal. Compile exact current249 before the
original signed16 test. Previous16CGU memory stop and r13 runtime stop stay failed.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import run_scheduled_signed_tests as previous
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources,finish_watcher

maintenance=previous.maintenance
SELF='tools/p09/run_split_domain_signed_tests.py'
TEST='tools/p09/tests/test_split_domain_signed_tests.py'
INVENTORY='stored-signed-split-domain-inventory'
PROFILE='stored-signed-split-domain-tests'
VARIANT='unchanged-r11-Rust-domain-ir-opt1-cgu64-two-packages-opt1-r14'
BASE_CONFIG=previous.previous.CONFIG
DOMAIN_CONFIG=('profile.test.package.domain-ir.opt-level=1',
    'profile.test.package.domain-ir.debug-assertions=true',
    'profile.test.package.domain-ir.overflow-checks=true',
    'profile.test.package.domain-ir.codegen-units=64',
    'profile.test.package.domain-ir.debug="line-tables-only"')
CONFIG=(*BASE_CONFIG,*DOMAIN_CONFIG)
PARENT='implementation/p09/evidence/p09-149-signed-scheduled.summary-run01.v1.json'
PARENT_PIN={'path':PARENT,'bytes':6404,
    'sha256':'a567bb39e98412a6702da44c8edc332155f9e832850d24da2dd07b317cf6b245'}


def require_duration(task,seconds):
    maintenance.require(task in (INVENTORY,PROFILE) and type(seconds) is int
        and 30<=seconds<=(600 if task==INVENTORY else 180),'SPLIT_DOMAIN_FINITE_SCOPE')


def config_contract(entries):
    maintenance.require(type(entries) is tuple and entries==(*BASE_CONFIG,*DOMAIN_CONFIG)
        and len(entries)==16 and len({e.split('=',1)[0] for e in entries})==16,
        'SPLIT_DOMAIN_CLOSED_PROFILE_REQUIRED')


def inventory_path(run):
    previous.inventory_path(run)
    return f'implementation/p09/evidence/p09-149-signed-split-domain.inventory-run{run:02}.v1.json'


def accept_inventory(row,expected,names,modules):
    config_contract(CONFIG)
    maintenance.require(row.get('source_variant')==VARIANT and row.get('task')==INVENTORY
        and row.get('test_package_profile_config')==list(CONFIG)
        and row.get('domain_test_codegen_units')==64
        and row.get('original_owned_resource_policy_changed') is False,
        'SPLIT_DOMAIN_CURRENT_PROFILE_INVENTORY_REQUIRED')
    # Only helper discriminators are translated. The REAL config stays unchanged;
    # original fresh whole source/name/module/cleanup checks are all inherited.
    with patch.object(previous.previous,'CONFIG',CONFIG):
        previous.accept_inventory(dict(row,source_variant=previous.VARIANT,task=previous.INVENTORY),expected,names,modules)


def load_binding(windows,task,inventory_run):
    require_duration(task,180);config_contract(CONFIG)
    expected,names,modules,schedule=previous.load_binding(windows,previous.INVENTORY,1)
    resources=SQLRuntimeResources();resources.admit()
    reader=AuditEvidenceReader(maintenance.ROOT,resources.checkpoint_io)
    try:
        maintenance.require(reader.pin(PARENT)==PARENT_PIN,'SPLIT_DOMAIN_PARENT_PIN_DRIFT')
        parent=reader.json(PARENT)
        maintenance.require(parent['compiled_inventory_current_exact'] is True
            and parent['source_closing_exact'] is True and parent['source_test_count']==249
            and parent['source_module_instances']==59 and parent['current_Rust_inputs']==783
            and parent['actual']['state']=='STOPPED_NOT_ACCEPTED'
            and parent['actual']['stop_reason']=='STOP_DURATION_LIMIT'
            and parent['actual']['whole_signed16_complete'] is False
            and parent['product_complete'] is False,'SPLIT_DOMAIN_PARENT_SCOPE')
        for pin in parent['current_helpers']:
            maintenance.require(reader.pin(pin['path'])==pin,'SPLIT_DOMAIN_PARENT_HELPER_DRIFT')
        for pin in parent['support_pins']:
            maintenance.require(reader.pin(pin['path'])==pin,'SPLIT_DOMAIN_PARENT_EVIDENCE_DRIFT')
        expected.update({n:reader.pin(n) for n in (SELF,TEST,PARENT)})
        if task==PROFILE:
            name=inventory_path(inventory_run)
            accept_inventory(reader.json(name),expected,names,modules)
            expected[name]=reader.pin(name)
        reader.finish()
    finally:
        maintenance.require(finish_watcher(resources,{}),'STOP_BINDING_WATCHER_CLEANUP_FAILED')
    return expected,names,modules,schedule


def run_worker(task):
    require_duration(task,180);config_contract(CONFIG)
    with patch.object(previous,'INVENTORY',INVENTORY),patch.object(previous,'PROFILE',PROFILE), \
            patch.object(previous.previous,'CONFIG',CONFIG):
        return previous.run_worker(task)


def run_owned(destination,expected,names,modules,schedule,task,seconds):
    require_duration(task,seconds);config_contract(CONFIG)
    real_dump=json.dump
    def write(row,stream,**kwargs):
        row.update(source_variant=VARIANT,test_package_profile_config=list(CONFIG),
            domain_test_codegen_units=64,domain_test_opt_level=1,
            split_domain_parent_pin=PARENT_PIN,compiler_memory_root_cause_proven=False,
            Rust_sources_or_original_test_assertions_changed=False,
            original_owned_resource_policy_changed=False,full249_current_qualified=False,
            product_complete=False,P09_gate='OPEN')
        return real_dump(row,stream,**kwargs)
    with patch.object(previous,'SELF',SELF),patch.object(previous,'TEST',TEST), \
            patch.object(previous,'INVENTORY',INVENTORY),patch.object(previous,'PROFILE',PROFILE), \
            patch.object(previous.previous,'CONFIG',CONFIG),patch.object(json,'dump',write):
        return previous.run_owned(destination,expected,names,modules,schedule,task,seconds)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--task',choices=(INVENTORY,PROFILE),default=PROFILE)
    parser.add_argument('--inventory-run',type=int,choices=range(1,100),default=1)
    parser.add_argument('--maximum-seconds',type=int,default=180)
    parser.add_argument('--light',action='store_true')
    args=parser.parse_args();require_duration(args.task,args.maximum_seconds)
    maintenance.require(maintenance.Path.cwd().resolve()==maintenance.ROOT,'SPLIT_DOMAIN_ROOT_SCOPE')
    windows=maintenance.Windows()
    kind='light' if args.light else ('inventory' if args.task==INVENTORY else 'actual')
    destination=scoped_path(f'implementation/p09/evidence/p09-149-signed-split-domain.{kind}-run{args.run:02}.v1.json',fresh=True)
    if not args.light:
        expected,names,modules,schedule=load_binding(windows,args.task,args.inventory_run)
        return run_owned(destination,expected,names,modules,schedule,args.task,args.maximum_seconds)
    from tests.test_split_domain_signed_tests import SplitDomainSignedTests
    resources=SQLRuntimeResources();resources.admit()
    reader=AuditEvidenceReader(maintenance.ROOT,resources.checkpoint_io)
    try:
        freeze=[reader.pin(n) for n in (SELF,TEST,PARENT)]
        with patch('subprocess.Popen',side_effect=AssertionError('SPLIT_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('SPLIT_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('SPLIT_LIGHT_THREAD_FORBIDDEN')):
            result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(SplitDomainSignedTests))
        reader.finish()
    finally:
        maintenance.require(finish_watcher(resources,{}),'STOP_BINDING_WATCHER_CLEANUP_FAILED')
    failed=sorted({t.id().split('.')[-1] for t,_ in result.failures+result.errors+result.skipped})
    passed=result.testsRun==10 and result.wasSuccessful() and not result.skipped
    row={'state':'PASS_SPLIT_DOMAIN_CONTRACT_ONLY_NOT_COMPILE_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
        'tests_run':result.testsRun,'tests_passed':result.testsRun-len(failed),'failed_tests':failed,
        'source_freeze':freeze,'source_freeze_exact_after':True,'test_package_profile_config':list(CONFIG),
        'product_complete':False,'P09_gate':'OPEN','Cargo_SQL_native_executed':False}
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
    print(json.dumps({k:row[k] for k in ('state','tests_run','tests_passed','failed_tests')}))
    return 0 if passed else 2


if __name__=='__main__':
    if len(sys.argv[1:])==3 and sys.argv[1:3]==['--owned-worker','--task']:
        raise SystemExit(run_worker(sys.argv[3]))
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[A-Z_]+',str(error)) else 'SPLIT_DOMAIN_OPERATION_FAILED'
        print(json.dumps({'state':'FAILED_NOT_ACCEPTED','error_code':code}))
        raise SystemExit(2) from None
