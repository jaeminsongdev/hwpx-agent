"""Bounded command-local IR opt1/CGU64 candidate, original signed assertions.

No claimed bottleneck or speedup before measurement. The previous RAM-stopped
suite is provenance only, not completion. All original Job/CPU/RAM limits stay.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import run_aead_dependency_signed_tests as base
from live_sql_evidence_reader import LiveSQLReader
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources,finish_watcher

c = base.c
SELF = 'tools/p09/run_ir_partitioned_signed_tests.py'
TEST = 'tools/p09/tests/test_ir_partitioned_signed_tests.py'
INVENTORY = 'ir-partitioned-signed-inventory'
PROFILE = 'ir-partitioned-signed-tests'
VARIANT = 'unchanged-r23-Rust-command-local-domain-ir-opt1-cgu64'
BASE_CONFIG = base.CONFIG
IR_CONFIG = tuple(f'profile.test.package.domain-ir.{key}={value}' for key,value in (
    ('opt-level','1'),('debug-assertions','true'),('overflow-checks','true'),
    ('codegen-units','64'),('debug','"line-tables-only"')))
CONFIG = (*BASE_CONFIG,*IR_CONFIG)
PARENT = {'path':'implementation/p09/evidence/p09-149-aead-full-stored.terminal-audit-run01.v1.json',
    'bytes':4931,'sha256':'377dcd379245f3724091010f673a68f9972db9ef52500a00526945b7d81063c5'}


def config_contract(entries):
    c.require(type(entries) is tuple and entries == CONFIG and len(entries) == 86
        and entries[:81] == BASE_CONFIG and len({x.split('=',1)[0] for x in entries}) == 86,
        'IR_PARTITION_CLOSED_CONFIG_REQUIRED')


def require_scope(task,seconds):
    c.require(task in (INVENTORY,PROFILE) and type(seconds) is int
        and 30 <= seconds <= (600 if task == INVENTORY else 180), 'IR_PARTITION_FINITE_SCOPE')
    config_contract(CONFIG)


@contextmanager
def adapter():
    config_contract(CONFIG)
    with patch.object(base,'SELF',SELF),patch.object(base,'TEST',TEST), \
            patch.object(base,'INVENTORY',INVENTORY),patch.object(base,'PROFILE',PROFILE), \
            patch.object(base,'VARIANT',VARIANT),patch.object(base,'CONFIG',CONFIG), \
            patch.object(base,'config_contract',config_contract):
        yield


def inventory_path(run):
    base.signed.previous.original.inventory_path(run)
    return f'implementation/p09/evidence/p09-149-ir-partition.inventory-run{run:02}.v1.json'


def load_binding(task,inventory_run):
    require_scope(task,180)
    # Load the unchanged base source set outside the adapter. The base inventory
    # proves only base81 compilation, never the new86 candidate compilation.
    expected,names,modules = base.load_binding(base.INVENTORY,2)
    resources = SQLRuntimeResources();row = {}
    try:
        resources.admit();q = LiveSQLReader(resources)
        base_path = base.inventory_path(2)
        base.accept_inventory(q.json(base_path),expected,names,modules)
        c.require(q.pin(PARENT['path']) == PARENT,'IR_PARTITION_PARENT_PIN_DRIFT')
        parent = q.json(PARENT['path'])
        c.require(parent['state'] == 'PASS_TERMINAL_SOURCE_AND_EXECUTION_AUDIT_NOT_SQL_NATIVE_OR_GATE'
            and parent['source_closing_exact'] and parent['execution_source_freezes_current_exact']
            and parent['current_Rust_inputs'] == 783 and parent['original_test_names'] == 249
            and parent['original_modules'] == 59 and parent['all_owned_trees_empty']
            and not parent['product_complete'] and parent['full249_current_qualified'] is False,
            'IR_PARTITION_STOPPED_PARENT_NOT_RUNTIME_PASS')
        for name in (base_path,PARENT['path'],SELF,TEST): expected[name] = q.pin(name)
        if task == PROFILE:
            path = inventory_path(inventory_run)
            with adapter():base.accept_inventory(q.json(path),expected,names,modules)
            expected[path] = q.pin(path)
        q.finish();return expected,names,modules
    finally:
        c.require(finish_watcher(resources,row),'STOP_BINDING_WATCHER_CLEANUP_FAILED')


def worker(task):
    require_scope(task,180)
    with adapter():return base.run_worker(task)


def run_owned(destination,expected,names,modules,task,seconds):
    require_scope(task,seconds);dump = json.dump
    def write(row,stream,**kwargs):
        c.require(row['test_package_profile_config'] == list(CONFIG),'IR_PARTITION_RECEIPT_CONFIG_DRIFT')
        row.update(IR_partition_parent_pin=PARENT,domain_ir_test_opt_level=1,
            domain_ir_test_codegen_units=64,IR_partitioned_compile_candidate=True,
            global_or_product_assertions_changed=False,statistical_speedup_proven=False)
        return dump(row,stream,**kwargs)
    with adapter(),patch.object(json,'dump',write):
        return base.run_owned(destination,expected,names,modules,task,seconds)


def light(destination):
    from tests.test_ir_partitioned_signed_tests import IrPartitionedSignedTests
    resources = SQLRuntimeResources();row = {}
    try:
        resources.admit();q = LiveSQLReader(resources)
        freeze = [q.pin(n) for n in (SELF,TEST,base.SELF,base.TEST,PARENT['path'])]
        with patch('subprocess.Popen',side_effect=AssertionError('IR_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('IR_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('IR_LIGHT_THREAD_FORBIDDEN')):
            result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(IrPartitionedSignedTests))
        failed = sorted({t.id().split('.')[-1] for t,_ in result.failures+result.errors+result.skipped})
        passed = result.testsRun == 8 and result.wasSuccessful() and not result.skipped
        q.finish();row.update(state='PASS_IR_PARTITION_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            tests_run=result.testsRun,tests_passed=result.testsRun-len(failed),failed_tests=failed,
            source_freeze=freeze,source_closing_exact=True,Cargo_SQL_native_executed=False,
            product_complete=False,P09_gate='OPEN',IO=q.summary())
    finally:row['resource_stop'] = resources.reason;finish_watcher(resources,row)
    c.require(row['resource_stop'] is None and row['resource_watcher_cleanup_confirmed'],'IR_PARTITION_LIGHT_RESOURCE_STOP')
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
    print(json.dumps({k:row[k] for k in ('state','tests_run','tests_passed','failed_tests')}));return 0 if passed else 2


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--task',choices=(INVENTORY,PROFILE),default=INVENTORY)
    parser.add_argument('--inventory-run',type=int,choices=range(1,100),default=1)
    parser.add_argument('--maximum-seconds',type=int,default=180);parser.add_argument('--light',action='store_true')
    args = parser.parse_args();require_scope(args.task,args.maximum_seconds)
    c.require(c.Path.cwd().resolve() == c.ROOT,'IR_PARTITION_ROOT_SCOPE')
    kind = 'light' if args.light else ('inventory' if args.task == INVENTORY else 'actual')
    destination = scoped_path(f'implementation/p09/evidence/p09-149-ir-partition.{kind}-run{args.run:02}.v1.json',fresh=True)
    if args.light:return light(destination)
    return run_owned(destination,*load_binding(args.task,args.inventory_run),args.task,args.maximum_seconds)


if __name__ == '__main__':
    if len(sys.argv[1:]) == 3 and sys.argv[1:3] == ['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code = ('DEFERRED_RESOURCE_ADMISSION_NOT_SATISFIED' if isinstance(error,ValueError)
            and str(error) == 'bootstrap_idle_window_not_admitted' else
            (str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z_]+',str(error)) else 'IR_PARTITION_OPERATION_FAILED'))
        print(json.dumps({'state':'FAILED_NOT_ACCEPTED','error_code':code}));raise SystemExit(2) from None
