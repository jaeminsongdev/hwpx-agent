"""P177 current parser -> fresh r07 product; original compiler/Job guards intact."""
import argparse
import contextlib
import io
import json
import sys
import time
import unittest
from unittest.mock import patch
import build_immutable_graph_product as p
import build_observed_writer_product_r2 as historical
import xml_initial_capacity_binding as parser
import verify_weighted_audit_io_r2 as reader_contracts
import weighted_audit_io as weighted

b=p.b; s=p.s; c=p.c; observed=historical.prior
SELF='tools/p09/build_xml_capacity_product.py'
TEST='tools/p09/tests/test_xml_capacity_product_build.py'
RUN=7
TARGET=c.ROOT/'target/p09-175-xml-initial-capacity'
PARENT=dict(path='implementation/p09/evidence/p09-176-weighted-xml-capacity.source-closing-run01.v1.json',
    bytes=326734,sha256='65699628343203381151915833db7da4da75bbdeb5676bd25aee1dfa73f510ff')
PASS='PASS_XML_CAPACITY_CURRENT_PRODUCT_BUILD_ONLY_NOT_LISTING_FULL249_OR_GATE'
CONTRACT_COUNT=254
PREPARATION='implementation/p09/evidence/p09-177-xml-capacity-product-build.preparation-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-177-xml-capacity-product-build.actual-run01.v1.json'
RAW_PARSE=b.parse_build
RAW_COMMAND=observed.RAW_COMMAND
RAW_CAPTURE=observed.RAW_CAPTURE

def require(ok,code):c.require(ok,'XML_PRODUCT_'+code)

def executable_name():return (TARGET/'debug/deps/form_stored_provider-p152-r07.exe').relative_to(c.ROOT).as_posix()

def recipe():
    with patch.object(c,'TARGET',TARGET):return s.recipe(RUN)

def parent_scope(row):
    require(row.get('state')=='PASS_XML_INITIAL_CAPACITY_DELTA_AND_ALL74_LIB_ONLY_NOT_FULL249_OR_GATE'
        and row.get('source_closing_exact') is True and row.get('actual_unit_tests_passed')==74
        and row.get('whole_original_core_and_tests_inverse_exact') is True
        and row.get('all_original_package_lib_tests_preserved') is True and row.get('typecheck_accepted') is True
        and row.get('current_Rust_input_count')==785 and row.get('protected_parent_EXE_inputs_exact')==66
        and row.get('contract_tests_passed')==64 and row.get('reader_contract_tests_passed')==37
        and row.get('total_contract_tests_passed')==101 and row.get('resource_stop_reason') is None
        and row.get('resource_watcher_cleanup_confirmed') is True,'PARENT_SCOPE')
    require(all(row.get(k) is False for k in ('current_compiled249_qualified','full249_current_qualified',
        'signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and row.get('P09_gate')==row.get('A12_gate')==row.get('A13_gate')=='OPEN','NO_PRODUCT_PROMOTION')
    expected=s.inputs.inventory(row['bound_input_pins'],1395)
    protected={n:pin for n,pin in expected.items() if n.endswith('.exe')}
    require(len(protected)==67 and protected.get(row['fresh_package_lib_executable_pin']['path'])
        ==row['fresh_package_lib_executable_pin'],'PROTECTED66_PLUS_FRESH_LIB')
    changes=s.inputs.inventory(row['declared_Rust_source_changes'],1)
    require(set(changes)=={parser.SOURCE} and expected[parser.SOURCE]==changes[parser.SOURCE]
        and len(row['source_test_names'])==249 and len(row['source_module_instances'])==59,'SOURCE_DELTA')
    require(row['IO']['finished'] and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==1395
        and row['IO']['maximum_scope_seconds']==600 and row['IO']['all_original_read_operations_preserved'],
        'FULL_FRESH_PARENT')
    return expected,protected

def fresh_scope(protected):
    name=executable_name();require(name not in protected,'NEW_SUFFIX_NOT_HISTORY');s.scoped_path(name,fresh=True)
    require(TARGET.is_dir() and not TARGET.is_symlink() and not TARGET.is_junction()
        and TARGET.resolve()==TARGET,'ISOLATED_TARGET_NO_LINK')
    require(not list((TARGET/'debug/deps').glob('form_stored_provider*.exe')),'NO_PRIOR_PRODUCT_IN_TARGET')
    return name

def progress_command(args,kw,validator):
    require(args[1:]==recipe()['argv_without_cargo'],'EXACT_R07_COMMAND')
    with patch.object(b.legacy.stream,'CargoStream',observed.progress.CargoStream):
        return RAW_COMMAND(args,kw,validator)

def worker(task):
    require(task==b.task_for(RUN),'CLOSED_R07_TASK')
    with patch.object(b,'TARGET',TARGET),patch.object(c,'TARGET',TARGET), \
            patch.object(b.legacy.stream,'run_command',progress_command):return b.worker(task)

def contracts():
    # Historical fixtures run with their historical targets/generations intact.
    historical.contracts();reader_contracts.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_xml_capacity_product_build')
    with patch('subprocess.Popen',side_effect=AssertionError('P177_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P177_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P177_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==12 and not result.skipped,'CONTRACT205_PLUS37_PLUS12')
    return dict(contract_tests_passed=CONTRACT_COUNT,contract_tests_run=CONTRACT_COUNT)

def helpers():
    names={SELF,TEST,PARENT['path'],parser.ARCHIVE,PREPARATION if (c.ROOT/PREPARATION).exists() else SELF}
    for module in tuple(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file:
            path=c.Path(file).absolute()
            if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
    return sorted(names)

def load_binding():
    destination=s.scoped_path(PREPARATION,fresh=True);resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,actual_Cargo_SQL_native_executed=False)
    accepted=False;binding=None
    try:
        resources.admit();q=weighted.WeightedLiveReader(resources);require(q.pin(PARENT['path'])==PARENT,'PARENT_PIN')
        row=q.json(PARENT['path']);expected,protected=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'ALL_PARENT_BYTES_CURRENT')
        archive=q.json(parser.ARCHIVE);_,old=parser.preimage(archive,parser.SOURCE)
        parser.inverse(q.text(parser.SOURCE),old.decode('utf-8'))
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ALL_ORIGINAL249_59')
        fresh_scope(protected);out.update(contracts());local=helpers()
        for n in local:expected[n]=q.pin(n)
        q.finish();accepted=True;binding=(expected,list(protected.values()),local)
        out.update(state='PASS_R07_CURRENT_SOURCE_PREPARATION_ONLY_NOT_BUILD_RUNTIME_OR_GATE',source_closing_exact=True,
            parser_delta_closing_pin=PARENT,current_Rust_input_count=785,protected_executables_exact=67,
            source_test_names=names,source_module_instances=modules,compile_recipe=recipe(),
            imported_helper_inventory=local,whole_original_parser_inverse_exact=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=parser.d.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):accepted=False;out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=weighted.resource_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','wall_seconds','resource_stop_reason')}),flush=True)
    require(accepted,'PREPARATION_NOT_ACCEPTED');return binding

def run_owned(destination,binding):
    captures=[];readers=[];dump=json.dump
    class ObservedCapture(RAW_CAPTURE):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);captures.append(self)
        def diagnostics(self):
            row=super().diagnostics();row['validated_compiler_progress']=observed.observe_capture(self);return row
    class OwnedReader(weighted.WeightedReader):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);readers.append(self)
    def validated_parse(output,run,*,require_stream=False):
        require(run==RUN,'PARSE_R07');result=RAW_PARSE(output,run,require_stream=require_stream)
        require(len(captures)==1,'ONE_PARENT_CAPTURE');observed.require_closed(observed.observe_capture(captures[0]));return result
    def write(row,stream,**kw):
        if row.get('state')==p.PASS:row['state']=PASS
        row.pop('current_graph_delta_closing_pin',None)
        row.update(schema_version='hwpx-agent.p09-xml-capacity-product-build/v1',goal_status='active',
            parser_delta_closing_pin=PARENT,protected_executables_expected=67,previous_parent_EXE_inputs_preserved=67,
            isolated_target=TARGET.relative_to(c.ROOT).as_posix(),compile_recipe=recipe(),
            actual_cache_hit_or_speedup_proven=False,parser_lib74_accepted=True,
            bounded_validated_compiler_progress_connected=True,original_complete_Cargo_validation_preserved=True,
            additional_process_query_or_thread=False,native_Process_query_executed=False,
            weighted_fresh_source_reads_connected=True,source_read_checks_skipped=False,
            source_reader_passes=[dict(read_passes=r.read_passes,bytes_read=r.bytes_read,
                read_rates_by_kind={'binary':weighted.BINARY_RATE,'other':weighted.OTHER_RATE},
                bytes_read_by_kind=dict(r.pacer.bytes_by_kind),pacer_bytes_read=r.pacer.bytes_paced) for r in readers],
            A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False)
        return dump(row,stream,**kw)
    with contextlib.ExitStack() as stack:
        for module,name,value in ((p,'RUN',RUN),(p,'SELF',SELF),(p,'PARENT',PARENT),(b,'TARGET',TARGET),
            (c,'TARGET',TARGET),(c,'AuditEvidenceReader',OwnedReader),(b.legacy,'AuditEvidenceReader',OwnedReader),
            (b,'parse_build',validated_parse),(b.legacy.original.capture,'FullCapture',ObservedCapture),(json,'dump',write)):
            stack.enter_context(patch.object(module,name,value))
        return p.run_owned(destination,*binding)

def light():
    destination=s.scoped_path('implementation/p09/evidence/p09-177-xml-capacity-product-build.light-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN')
    try:
        resources.admit();q=weighted.WeightedLiveReader(resources);out.update(contracts())
        for n in helpers():q.pin(n)
        q.finish();out.update(state='PASS_R07_BUILD_READER_WORKER_CONTRACTS_ONLY_NOT_ACTUAL_OR_GATE',
            actual_Cargo_SQL_native_executed=False,source_closing_exact=True,compile_recipe=recipe())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=parser.d.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['resource_tail']=weighted.resource_tail(resources)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);mode=ap.parse_args().mode
    require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    if mode=='light':return light()
    destination=s.scoped_path(ACTUAL,fresh=True);fresh_scope({});return run_owned(destination,load_binding())

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,b.subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=parser.d.original.closed_error(error))))
        raise SystemExit(2) from None
