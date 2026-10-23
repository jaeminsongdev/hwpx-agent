"""Publish one self-free run011 metadata plan, not runtime freshness credit.

Only the fixed producer64 plus named controls/data are admitted. Whole source
bytes are checked twice under the original guard before publication; no engine,
Frame, worker, product, prior suites or queue acceptance is executed.
"""
import copy
import json
from types import SimpleNamespace as NS

SELF='tools/p09/native011_metadata_report.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
GRAPH=dict(path=PREFIX+'successor-run010-graph002.v1.json',bytes=11673,
    sha256='104a632a894608e33f51e3ea98c9e0080dd226465b3efc92dc410e3e6a899363')
PRIOR=dict(path=PREFIX+'current-runtime-run010.v1.json',bytes=2312978,
    sha256='b617ea54f3c4ffa2a4317cde0772a45fc77d6763409b99bcd377d2b516c67d63')
PACKAGE=(
    dict(path=PREFIX+'successor-run011-zlib-manifest001.v1.json',bytes=99480,
        sha256='d08ab299f5af47054a820dfcb47c62ca669df7fb1dda291c973b0aacd40524c3'),
    dict(path=PREFIX+'successor-worker-capsule011.compact.zlib.v1.json',bytes=15058,
        sha256='a4056d0770b7cc87a469438408e3aaa00e9cd644592e41db3e1e0001b2537f3f'),
    dict(path=PREFIX+'successor-worker-bootstrap011.zlib.v1.json',bytes=4898,
        sha256='1a1a9d6c15e91fc861baf65389f5f0f85f99a23a810954eb360cd1b3fbab02d9'))
EXTRA_CODE=tuple('tools/p09/'+name+'.py' for name in (
    'native011_ready_worker','native011_preparation','native011_worker_transport','native011_zlib_binding',
    'native011_worker_preparation','native011_scope_map','native011_scope_delta','native011_parent_plan',
    'native011_parent_oracle','native011_shared_parent','native011_metadata_report',
    'native011_metadata_audit','native011_metadata_epochs',
    'batch_engine_connection','batch_zlib_engine','batch_zlib_binding','batch_zlib_mapping',
    'zlib165_mapping_declaration_v1','historical_receipt_batch_partition_v1',
    'phased_preservation_read_gate_v1','phased_preservation_read_gate_v2',
    'prepared_run_closure_v1','owned_cpu_baseline_v1','preparation_attributed_cpu_v1','distinct_final_sample_guard_v1'))


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_METADATA_REPORT_'+code)


def output_path(generation):
    require(type(generation) is int and 1<=generation<=8,'BOUNDED_EXPLICIT_GENERATION')
    return PREFIX+f'successor-run011-parent-metadata-plan{generation:03}.v1.json'


def expected_names(base,scope):
    require(base['state']=='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO'
        and type(base['index']) is int and base['index']==165 and base['cleanup_confirmed'] is True
        and base['fresh_inputs']==base['final_fresh_hashes']==64,'EXACT_PRODUCER64_BASE_NOT_PRODUCT')
    original=scope.pins(base['source_pins']);require(len(original)==64,'CLOSED_ORIGINAL64')
    return original,set(original)|set(EXTRA_CODE)|{GRAPH['path'],PRIOR['path']}|{p['path'] for p in PACKAGE}


def compose(base,sources,scope,generation):
    original,names=expected_names(base,scope);checked=scope.pins(list(sources.values()))
    require(checked==sources and set(checked)==names,'ONLY_NAMED_GRAPH_INPUTS_NOT_OBSERVED_UNION')
    require(all(checked[n]==p for n,p in original.items()),'EVERY_ORIGINAL_PRODUCER_PIN_RETAINED')
    require(all(checked[p['path']]==p for p in (GRAPH,PRIOR,*PACKAGE)),'EXACT_FIXED_REFERENCE_AND_PACKAGE')
    path=output_path(generation);require(path not in checked,'SELF_FREE_REPORT')
    row=copy.deepcopy(base)
    row.update(preparation_report_generation=4,physical_run=11,metadata_plan_generation=generation,
        manifest_pin=dict(PACKAGE[0]),capsule_pin=dict(PACKAGE[1]),bootstrap_pin=dict(PACKAGE[2]),
        source_pins=[dict(checked[n]) for n in sorted(checked)],fresh_inputs=len(checked),final_fresh_hashes=len(checked),
        reference_producer_graph_pin=dict(GRAPH),preserved_failed_native010_pin=dict(PRIOR),
        original_producer64_source_pins=[dict(original[n]) for n in sorted(original)],
        cleanup_confirmed=True,product_or_Native_executed=False,GO_authorized=False,accepted_count_delta=0,
        actual_Native_Frame_metadata_or_product_qualified=False,
        scope='Fixed declarations and producer source-byte qualification, not live runtime locks')
    return row


def validate(row,base,scope,generation):
    require(type(row) is dict,'EXACT_REPORT_OBJECT')
    sources=scope.pins(row['source_pins'])
    canonical=lambda value:json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False,separators=(',',':'))
    require(canonical(row)==canonical(compose(base,sources,scope,generation)),
        'ENTIRE_CANONICAL_REPORT_FROM_EXPLICIT_INPUTS')
    return sources


def main():
    import argparse,re,sys,time
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser();parser.add_argument('--generation',type=int,required=True)
    args=parser.parse_args();path=output_path(args.generation)
    denied=[]
    def deny(event,arguments):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('NATIVE011_REPORT_PROCESS_DENIED')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    receipt_path=f'implementation/p09/evidence/p09-361-native011-metadata-report-generation{args.generation:03}.v1.json'
    row=dict(state='FAILED_NATIVE011_METADATA_REPORT_NOT_NATIVE',GO_authorized=False,accepted_count_delta=0)
    q=candidate=None;started=time.monotonic()
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        require(not (c.ROOT/path).exists() and not (c.ROOT/receipt_path).exists(),'EXCLUSIVE_PLAN_AND_RECEIPT')
        base=a.read_exact(q,GRAPH);original,names=expected_names(base,scope)
        sources={name:dict(q.pin(name)) for name in sorted(names)}
        prior=a.read_exact(q,PRIOR)
        a.fields(prior,dict(state='DEFERRED_NOT_STARTED',worker_created=False,product_body_observed=False),
            'FAILED_NATIVE010_NEVER_PROMOTED')
        manifest=a.read_exact(q,PACKAGE[0])
        require(len(manifest['descriptors'])==162,'FULL_CURRENT_DESCRIPTOR_DECLARATION')
        candidate=compose(base,sources,scope,args.generation)
        require(len(q.snapshots)==len(sources),'EVERY_ACTUAL_PRODUCER_INPUT_EXPLICITLY_DECLARED')
        q.finish();guard.check(force=True)
        require(q.final_fresh_hashes==len(sources) and not denied,'FULL_PRODUCER_CLOSING_BYTES_NO_PROCESS')
        row.update(state='PASS_NATIVE011_METADATA_REPORT_SOURCE_BYTES_NOT_RUNTIME',
            fresh_inputs=len(sources),final_fresh_hashes=q.final_fresh_hashes,physical_run=11)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError) as error:
        candidate=None;value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_REPORT_FAILURE')
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=guard.samples,
            process_creation_attempts=len(denied))
        if candidate is not None and guard.cleanup:row['metadata_report_pin']=publisher.publish(c.ROOT,path,candidate,NS(require=c.require,exact=a.exact))
        receipt=publisher.publish(c.ROOT,receipt_path,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),cleanup=guard.cleanup,
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),elapsed=row['elapsed_seconds'],
            metadata_report_pin=row.get('metadata_report_pin'),receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and guard.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
