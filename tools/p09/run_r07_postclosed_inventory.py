"""P182 list ONLY separately post-closed r07, never retrofit original CPU STOP."""
import argparse
import contextlib
import io
import json
import sys
import time
import unittest
from unittest.mock import patch
import close_r07_compiler_output as closing
import run_current_stored_inventory as i
import run_writer_xml_product_inventory as historical
import owned_source_read_pressure as pressure
import pre_go_parent_cpu_observer_r2 as observer
b=closing.b; c=b.c; s=b.s
SELF='tools/p09/run_r07_postclosed_inventory.py'
TEST='tools/p09/tests/test_r07_postclosed_inventory.py'
CLOSING=dict(path=closing.DEST,bytes=335682,
    sha256='d401903c987ba1d9b7c0760d4ef3a4ed89a8a7618ee64faf867d8dc10dfcfda7')
PREP='implementation/p09/evidence/p09-182-r07-postclosed-inventory.preparation-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-182-r07-postclosed-inventory.actual-run01.v1.json'
PASS='PASS_POSTCLOSED_R07_COMPILED249_LISTING_ONLY_NOT_TEST_RUNTIME_OR_GATE'

def require(ok,code):b.require(ok,'POSTCLOSED_LIST_'+code)

def closing_scope(row):
    require(row['state']==closing.PASS and row['source_closing_exact']
        and row['current_build_accepted'] and row['separate_current_post_closing_exact']
        and row['original_build_accepted'] is False and row['original_run_state']=='STOPPED_NOT_ACCEPTED'
        and row['original_source_final_hash_not_retroactively_promoted']
        and row['original_incomplete_final_freeze_preserved']
        and row['original_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and row['contract_tests_passed']==271 and row['post_closing_contract_tests_passed']==6
        and row['total_contract_tests_passed']==277 and row['protected_executables_exact']==67
        and row['current_Rust_input_count']==785 and row['current_source_test_count']==249
        and row['current_source_module_instance_count']==59 and row['parser_delta_closing_pin']==b.PARENT
        and row['actual_build_receipt_pin']==closing.ACTUAL and row['preparation_receipt_pin']==closing.PREP
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],
        'SEPARATE_CURRENT_BUILD_ONLY')
    require(all(row[k] is False for k in ('current_compiled249_qualified','full249_current_qualified',
        'signed16_current_qualified','product_complete','PC_freeze_resolved',
        'actual_new_Cargo_or_EXE_SQL_Hangul_or_child_executed'))
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','NO_RUNTIME_PROMOTION')
    expected=s.inputs.inventory(row['bound_input_pins'],1423);exe=row['compiled_test_executable_pin']
    require(exe['path']==b.executable_name() and expected.get(exe['path'])==exe
        and sum(n.endswith('.exe') for n in expected)==68,'WHOLE67_PLUS_R07')
    require(row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==1423 and row['IO']['finished']
        and row['IO']['maximum_scope_seconds']==600 and row['IO']['all_original_read_operations_preserved']
        and row['IO']['read_rates_by_kind']=={'binary':2621440,'other':4194304},'WHOLE_CURRENT_CLOSING')
    return expected,exe

def worker(task):
    require(task==i.task_for(7),'EXACT_R07_TASK')
    with patch.object(i,'EXE_RUN',7),patch.object(c,'TARGET',b.TARGET):return i.worker(task)

def contracts():
    historical.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_r07_postclosed_inventory')
    with patch('subprocess.Popen',side_effect=AssertionError('P182_CONTRACT_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P182_CONTRACT_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P182_CONTRACT_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'CONTRACT12_PLUS6')
    return dict(contract_tests_passed=18,contract_tests_run=18)

def helpers():
    result={SELF,TEST,CLOSING['path']}
    for module in tuple(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file:
            path=c.Path(file).absolute()
            if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':
                result.add(path.relative_to(c.ROOT).as_posix())
    return sorted(result)

def load_binding():
    destination=s.scoped_path(PREP,fresh=True);resources=s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,goal_status='active',
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',actual_EXE_executed=False)
    accepted=False;binding=None;started=time.monotonic()
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources)
        require(q.pin(CLOSING['path'])==CLOSING,'CLOSING_PIN')
        row=q.json(CLOSING['path']);expected,exe=closing_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'ALL_CURRENT_BUILD_INPUTS')
        require(q.pin(closing.ACTUAL['path'])==closing.ACTUAL,'ORIGINAL_STOP_IMMUTABLE')
        actual=q.json(closing.ACTUAL['path']);frozen=closing.metadata_scope(actual)
        require(all(expected.get(n)==p for n,p in frozen.items()),'ALL1418_COMPILE_BEFORE_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=b.p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ORIGINAL249_59')
        archive=q.json(b.parser.ARCHIVE);_,old=b.parser.preimage(archive,b.parser.SOURCE)
        b.parser.inverse(q.text(b.parser.SOURCE),old.decode('utf-8'))
        out.update(contracts())
        for n in helpers():expected[n]=q.pin(n)
        q.finish();binding=(expected,names,modules,exe);accepted=True
        out.update(state='PASS_R07_LISTING_PREPARATION_ONLY_NOT_ACTUAL_OR_GATE',source_closing_exact=True,
            current_compile_closing_pin=CLOSING,compiled_test_executable_pin=exe,
            current_Rust_input_count=785,source_test_names=names,source_module_instances=modules,
            protected_executables_exact=68,original_STOP_receipt_unchanged=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            accepted=False;out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=b.weighted.resource_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason','wall_seconds')}),flush=True)
    require(accepted,'PREPARATION_NOT_ACCEPTED');return binding

def run_owned(destination,binding):
    readers=[];dump=json.dump
    class Reader(pressure.WeightedReader):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);readers.append(self)
    def write(row,stream,**kw):
        samples=[r for r in row.get('samples',[]) if 'parent_cpu_machine_percent' in r]
        row.update(goal_status='active',A12_gate='OPEN',A13_gate='OPEN',
            parent_ProcessTimes_observation_connected=True,foreign_Process_query_executed=False,
            additional_Process_query_scope='current_parent_pseudo_handle_only',
            additional_observer_thread_started=False,native_Process_query_executed=True,
            parent_CPU_max_machine_percent=max((r['parent_cpu_machine_percent'] for r in samples),default=None),
            source_read_checks_skipped=False,original_STOP_receipt_unchanged=True,
            full_product_performance_improvement_measured=False,
            source_reader_passes=[dict(read_passes=r.read_passes,bytes_read=r.bytes_read,
                read_rates_by_kind={'binary':pressure.BINARY_RATE,'other':pressure.OTHER_RATE},
                bytes_read_by_kind=dict(r.pacer.bytes_by_kind)) for r in readers])
        return dump(row,stream,**kw)
    with contextlib.ExitStack() as stack:
        for module,name,value in ((i,'SELF',SELF),(i,'CLOSING',CLOSING),(i,'PASS',PASS),
            (c,'TARGET',b.TARGET),(c,'Windows',observer.RAW_PARENT),
            (c,'AuditEvidenceReader',Reader),(json,'dump',write)):
            stack.enter_context(patch.object(module,name,value))
        return i.run_owned(7,destination,*binding)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);mode=ap.parse_args().mode
    require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    if mode=='actual':return run_owned(s.scoped_path(ACTUAL,fresh=True),load_binding())
    destination=s.scoped_path('implementation/p09/evidence/p09-182-r07-postclosed-inventory.light-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED',actual_EXE_executed=False,
        current_compiled249_qualified=False,product_complete=False,P09_gate='OPEN')
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources);out.update(contracts())
        for n in (SELF,TEST,i.SELF,i.TEST,historical.SELF,historical.TEST):q.pin(n)
        q.finish();out.update(state='PASS_R07_LISTING_CONTRACT18_ONLY_NOT_ACTUAL_OR_GATE')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    raise SystemExit(main())
