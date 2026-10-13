"""P184 original whole r07 listing preparation with own-parent/file observation.

No recompile, foreign process sampler, extra observer thread, altered rate,
deadline, skipped fresh read or retroactive promotion of P182 CPU STOP.
"""
import argparse
import contextlib
import io
import json
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_r07_postclosed_inventory as prior
import readonly_parent_file_observation as observation
b=prior.b; c=prior.c; s=prior.s
SELF='tools/p09/run_observed_r07_inventory.py'
TEST='tools/p09/tests/test_observed_r07_inventory.py'
PREP='implementation/p09/evidence/p09-184-observed-r07-inventory.preparation-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-184-observed-r07-inventory.actual-run01.v1.json'
LIGHT='implementation/p09/evidence/p09-184-observed-r07-inventory.light-run01.v1.json'
PASS='PASS_OBSERVED_POSTCLOSED_R07_COMPILED249_LISTING_ONLY_NOT_RUNTIME_OR_GATE'
FAILED_PREP='implementation/p09/evidence/p09-182-r07-postclosed-inventory.preparation-run01.v1.json'
ORIGINAL_LIGHT='implementation/p09/evidence/p09-182-r07-postclosed-inventory.light-run01.v1.json'
RAW_HELPERS=prior.helpers
RAW_CONTRACTS=prior.contracts

class Reader(observation.ObservedReader):
    def json(self,name):
        row=super().json(name)
        if name==prior.CLOSING['path']:
            expected,_=prior.closing_scope(row)
            self.reader.protected=frozenset(n for n in expected if n.endswith('.exe'))
            prior.require(len(self.reader.protected)==68,'READONLY_PROTECTED68')
        return row

def helpers():
    return sorted(set(RAW_HELPERS())|{SELF,TEST,prior.__file__ and 'tools/p09/run_r07_postclosed_inventory.py',
        'tools/p09/tests/test_r07_postclosed_inventory.py',FAILED_PREP,ORIGINAL_LIGHT,
        observation.SELF,observation.TEST,
        'implementation/p09/evidence/p09-183-readonly-parent-file-observation.light-run01.v1.json',
        'implementation/p09/evidence/p09-183-readonly-parent-file-observation.observe-run01.v1.json'})

def contracts():
    RAW_CONTRACTS();observation.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_r07_inventory')
    with patch('subprocess.Popen',side_effect=AssertionError('P184_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P184_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P184_NO_OBSERVER_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    prior.require(result.wasSuccessful() and result.testsRun==4 and not result.skipped,'CONTRACT18_PLUS11_PLUS4')
    return dict(contract_tests_passed=33,contract_tests_run=33)

def worker(task):return prior.worker(task)

def closed_error(error):
    code=str(error) if isinstance(error,ValueError) else 'OBSERVED_INVENTORY_REDACTED_FAILURE'
    return code if re.fullmatch('[A-Za-z0-9_]{1,160}',code or '') else 'OBSERVED_INVENTORY_REDACTED_FAILURE'

def actual():
    destination=s.scoped_path(ACTUAL,fresh=True);dump=json.dump
    io_module=SimpleNamespace(WeightedLiveReader=Reader,resource_tail=observation.parent_tail)
    def write(row,stream,**kw):
        row.update(readonly_parent_ProcessTimes_observation_connected=True,
            readonly_parent_Process_query_executed=True,foreign_Process_query_executed=False,
            readonly_extra_sampler_thread_started=False,readonly_observation_scope='current_parent_pseudo_handle_only',
            original_P182_CPU_stop_receipt_preserved=True,original_resource_guards_and_read_rates_preserved=True)
        return dump(row,stream,**kw)
    with contextlib.ExitStack() as stack:
        for module,name,value in ((prior,'SELF',SELF),(prior,'TEST',TEST),(prior,'PREP',PREP),
            (prior,'ACTUAL',ACTUAL),(prior,'PASS',PASS),(prior,'helpers',helpers),(prior,'contracts',contracts),
            (s,'SQLRuntimeResources',observation.ObservedResources),(b,'weighted',io_module),(json,'dump',write)):
            stack.enter_context(patch.object(module,name,value))
        binding=prior.load_binding()
        return prior.run_owned(destination,binding)

def light():
    destination=s.scoped_path(LIGHT,fresh=True);resources=observation.OriginalResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        actual_whole_preparation_listing_SQL_Hangul_Cargo_or_child_executed=False)
    try:
        resources.admit();q=observation.weighted.WeightedLiveReader(resources);out.update(contracts())
        for n in (SELF,TEST,observation.SELF,observation.TEST,FAILED_PREP,ORIGINAL_LIGHT):q.pin(n)
        failed=q.json(FAILED_PREP)
        prior.require(failed['state']=='FAILED_NOT_ACCEPTED' and not failed['source_closing_exact']
            and failed['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and failed['resource_watcher_cleanup_confirmed'] and not failed['actual_EXE_executed']
            and not failed['IO']['finished'] and failed['IO']['final_fresh_hashes']<failed['IO']['bound_inputs'],
            'P182_ORIGINAL_PREPARATION_STOP')
        q.finish();out.update(state='PASS_OBSERVED_R07_LISTING_CONTRACT33_ONLY_NOT_ACTUAL_OR_CAUSE',
            original_P182_CPU_stop_receipt_preserved=True,original_P182_preparation_pin=q.reader.snapshots[FAILED_PREP])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);mode=ap.parse_args().mode
    prior.require(c.Path.cwd().resolve()==c.ROOT,'OBSERVED_INVENTORY_CWD')
    return light() if mode=='light' else actual()

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,b.b.subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=closed_error(error))))
        raise SystemExit(2) from None
