"""P187 all249 current r07, original1200/full parser, near-saturation IO yielding."""
import argparse
import contextlib
import io
import json
import sys
import time
import unittest
from unittest.mock import patch
import run_current_stored_full as original
import run_writer_current_full as historical
import close_observed_r07_listing_output as listing
import owned_read_backpressure as owned
import near_saturation_read_backpressure as pressure
b=listing.b; s=listing.s; c=listing.c
SELF='tools/p09/run_current_r07_full.py'
TEST='tools/p09/tests/test_current_r07_full.py'
RUN=7
PARENT=dict(path=listing.DEST,bytes=339893,sha256='7b06997d3b8090967597fad1d12b94446e20e3a17ba206233ae8711fdb1d455d')
PREP='implementation/p09/evidence/p09-187-current-r07-full.preparation-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-187-current-r07-full.actual-run01.v1.json'
PASS='PASS_CURRENT_R07_UNFILTERED_ALL249_ONLY_NOT_SQL_HANGUL_PRODUCT_OR_GATE'

def require(ok,code):b.require(ok,'R07_FULL_'+code)

def parent_scope(row):
    require(row['state']==listing.PASS and row['source_closing_exact'] and row['current_compiled249_qualified']
        and row['current_build_accepted'] and row['separate_current_post_closing_exact']
        and row['compiled_test_count']==249 and row['current_Rust_input_count']==785
        and row['current_source_module_instance_count']==59 and row['protected_parent_EXE_inputs_exact']==68
        and row['total_contract_tests_passed']==82 and row['listing_contract_tests_passed']==33
        and row['reader_contract_tests_passed']==43 and row['post_closing_contract_tests_passed']==6
        and row['current_compile_closing_pin']==listing.run.prior.CLOSING
        and row['actual_inventory_receipt_pin']==listing.ACTUAL and row['preparation_receipt_pin']==listing.PREP
        and row['original_run_state']=='STOPPED_NOT_ACCEPTED' and not row['original_listing_run_accepted']
        and row['original_source_final_hash_not_retroactively_promoted'] and row['original_incomplete_final_freeze_preserved']
        and row['validated_original_list_output_by_pinned_control_flow'] and row['source_listing_replay_not_new_stdout']
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'COMPILED_ONLY_COMPOUND_PARENT')
    require(all(row[k] is False for k in ('runtime_test_bodies_executed','full249_current_qualified','signed16_current_qualified',
        'product_complete','PC_freeze_resolved','actual_new_list_Cargo_SQL_Hangul_child_or_test_body_executed'))
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','NO_RUNTIME_OR_GATE_PROMOTION')
    expected=s.inputs.inventory(row['bound_input_pins'],1442);exe=row['compiled_test_executable_pin']
    require(exe==listing.EXE and expected.get(exe['path'])==exe and sum(n.endswith('.exe') for n in expected)==68
        and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==1442 and row['IO']['finished']
        and row['IO']['maximum_scope_seconds']==600 and row['IO']['all_original_read_operations_preserved'], 'WHOLE_CURRENT68')
    return expected,exe

def worker(task):
    require(task==original.task_for(RUN),'CLOSED_R07_FULL_TASK')
    def current_name(requested):
        require(type(requested) is int and requested==1,'ORIGINAL_SINGLE_LOOKUP')
        return b.executable_name()
    with patch.object(c,'TARGET',b.TARGET),patch.object(original.inventory.build,'executable_name',current_name):
        return original.worker(task)

def contracts():
    historical.contracts();pressure.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_owned_read_backpressure','test_current_r07_full'))
    with patch('subprocess.Popen',side_effect=AssertionError('P187_NO_LIGHT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P187_NO_LIGHT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P187_NO_NEW_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==11 and not result.skipped,'CONTRACT32_PLUS43_PLUS4_PLUS7')
    return dict(contract_tests_passed=86,contract_tests_run=86)

def helpers():
    result={SELF,TEST,PARENT['path'],owned.SELF,owned.TEST,pressure.SELF,pressure.TEST,
        original.SELF,original.TEST,original.full.SELF,original.full.TEST}
    for module in tuple(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file:
            path=c.Path(file).absolute()
            if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':result.add(path.relative_to(c.ROOT).as_posix())
    return sorted(result)

def load_binding():
    destination=s.scoped_path(PREP,fresh=True);resources=pressure.observation.ObservedResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,current_compiled249_qualified=True,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',actual_test_EXE_or_SQL_Hangul_or_Cargo_executed=False)
    accepted=False;binding=None
    try:
        resources.admit();q=pressure.PressureReader(resources);require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_CURRENT249')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        q.reader.protected=frozenset(n for n in expected if n.endswith('.exe'))
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_COMPILED')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=b.p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ALL_ORIGINAL249_59')
        archive=q.json(b.parser.ARCHIVE);_,old=b.parser.preimage(archive,b.parser.SOURCE)
        b.parser.inverse(q.text(b.parser.SOURCE),old.decode('utf-8'))
        out.update(contracts())
        for n in helpers():expected[n]=q.pin(n)
        q.finish();accepted=True;binding=(expected,names,modules,exe)
        out.update(state='PASS_CURRENT_R07_FULL249_PREPARATION_ONLY_NOT_RUNTIME_OR_GATE',source_closing_exact=True,
            current_inventory_closing_pin=PARENT,compiled_test_executable_pin=exe,current_Rust_input_count=785,
            source_test_names=names,source_module_instances=modules,protected_executables_exact=68)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):accepted=False;out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=pressure.observation.parent_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason','wall_seconds')}),flush=True)
    require(accepted,'PREPARATION_NOT_ACCEPTED');return binding

def run_owned(destination,binding):
    box=owned.LatestOriginalSample();readers=[];protected={n for n in binding[0] if n.endswith('.exe')};dump=json.dump
    class Reader(owned.OwnedReader):
        def __init__(self,*a,**kw):super().__init__(*a,samples=box,protected=protected,**kw);readers.append(self)
    def write(row,stream,**kw):
        samples=[x for x in row.get('samples',[]) if 'parent_cpu_machine_percent' in x]
        row.update(goal_status='active',A12_gate='OPEN',A13_gate='OPEN',actual_Hangul_COM_or_SQL_run=False,
            native_Process_query_executed=True,foreign_Process_query_executed=False,
            own_parent_ProcessTimes_observation_connected=True,additional_observer_thread_started=False,
            extra_hash_sampler_started=False,latest_original_sample_shadow_only=True,
            parent_CPU_max_machine_percent=max((x['parent_cpu_machine_percent'] for x in samples),default=None),
            owned_source_reader_passes=[r.diagnostics() for r in readers],
            full_product_performance_improvement_measured=False,original_P184_stop_receipt_preserved=True)
        return dump(row,stream,**kw)
    with contextlib.ExitStack() as stack:
        for module,name,value in ((original,'SELF',SELF),(original,'TEST',TEST),(original,'PARENT',PARENT),
            (original,'PASS',PASS),(c,'TARGET',b.TARGET),(c,'Windows',owned.windows_type(box)),
            (c,'AuditEvidenceReader',Reader),(s,'SQLRuntimeResources',pressure.observation.ObservedResources),(json,'dump',write)):
            stack.enter_context(patch.object(module,name,value))
        return original.run_owned(RUN,destination,*binding)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);mode=ap.parse_args().mode
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');original.require_scope(1200)
    if mode=='actual':return run_owned(s.scoped_path(ACTUAL,fresh=True),load_binding())
    destination=s.scoped_path('implementation/p09/evidence/p09-187-current-r07-full.light-run01.v1.json',fresh=True)
    resources=pressure.observation.OriginalResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',
        actual_test_EXE_or_Cargo_SQL_Hangul_or_child_executed=False,full249_current_qualified=False,
        signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN')
    try:
        resources.admit();q=pressure.PressureReader(resources);out.update(contracts())
        for n in (SELF,TEST,owned.SELF,owned.TEST,pressure.SELF,pressure.TEST,original.SELF,original.TEST):q.pin(n)
        q.finish();out.update(state='PASS_CURRENT_R07_FULL249_CONTRACT86_ONLY_NOT_RUNTIME_OR_GATE')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,original.subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=original.closed_error(error))));raise SystemExit(2) from None
