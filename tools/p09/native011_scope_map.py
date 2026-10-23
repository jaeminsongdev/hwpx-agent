"""Compare worker control inputs with the last failed Native declaration.

An envelope alias is not a lock on the worker's raw pathname. This produces
coverage diagnostics only: no input addition, scope mutation, IO exemption,
current Native011 qualification, process launch, product or acceptance.
"""
from types import SimpleNamespace as NS
import current_stored_runtime_scope as scope

SELF='tools/p09/native011_scope_map.py'
PRIOR=dict(path='implementation/p09/evidence/p09-361-case165-current-runtime-run010.v1.json',
    bytes=2312978,sha256='b617ea54f3c4ffa2a4317cde0772a45fc77d6763409b99bcd377d2b516c67d63')
WORKER=dict(path='implementation/p09/evidence/p09-361-native011-inherited-event-worker001.v1.json',
    bytes=45663,sha256='b0a4817ba79f7a8acb7764a2f9ceac89f86fe2312baa0f991ecb763dfdd0337f')
CATEGORIES=('DIRECT_PIN_DECLARED','PHYSICAL_ALIAS_ONLY_NOT_RAW_LOCK',
    'ALIAS_OUTSIDE_PRIOR_FRAME','SEMANTIC_DECLARATION_ONLY','MISSING_FROM_PRIOR_DECLARATION','PIN_CONFLICT')


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_SCOPE_MAP_'+code)


def compare(worker_pins,representation,*,prior_frame_count):
    """Classify every required input once; never upgrade a failed epoch."""
    wanted=scope.pins(worker_pins)
    semantic=scope.pins(representation['semantic_source_freeze'])
    physical=scope.pins(representation['physical_source_freeze'])
    require(type(prior_frame_count) is int and prior_frame_count==len(physical),
        'PRIOR_FRAME_COUNT_MATCHES_PHYSICAL_DECLARATION')
    require(type(representation['descriptors']) is list and 0<len(representation['descriptors'])<=249,
        'CLOSED_DESCRIPTOR_DECLARATION')
    aliases={}
    for item in representation['descriptors']:
        require(type(item) is dict and set(item)=={'schema_version','next_case','semantic_original_pin','physical_envelope_pin'}
            and item['schema_version']=='hwpx-agent.p09-lossless-runtime-source-projection/v1'
            and type(item['next_case']) is int and item['next_case']==165,'EXACT_DESCRIPTOR_SCHEMA_AND_CONTEXT')
        old=scope.pins([item['semantic_original_pin']]);new=scope.pins([item['physical_envelope_pin']])
        old_pin=next(iter(old.values()));new_pin=next(iter(new.values()))
        name=old_pin['path']
        require(name not in aliases,'UNIQUE_SEMANTIC_DESCRIPTOR_PATH')
        aliases[name]=(old_pin,new_pin)
    records=[];counts={key:0 for key in CATEGORIES}
    for name,pin in wanted.items():
        old,new=aliases.get(name,(None,None))
        row=dict(required_pin=dict(pin),prior_epoch_only=True,live_coverage_claimed=False)
        if name in physical:
            category='DIRECT_PIN_DECLARED' if physical[name]==pin else 'PIN_CONFLICT'
            row['prior_physical_pin']=dict(physical[name])
        elif name in semantic and semantic[name]!=pin or old is not None and old!=pin:
            category='PIN_CONFLICT'
            row['prior_semantic_pin']=dict(semantic.get(name,old))
        elif old is not None:
            row['prior_alias_pin']=dict(new)
            if new['path'] in physical:
                require(physical[new['path']]==new,'ALIAS_PHYSICAL_PIN_CONFLICT')
                category='PHYSICAL_ALIAS_ONLY_NOT_RAW_LOCK'
            else:category='ALIAS_OUTSIDE_PRIOR_FRAME'
        elif name in semantic:category='SEMANTIC_DECLARATION_ONLY'
        else:category='MISSING_FROM_PRIOR_DECLARATION'
        row['category']=category;records.append(row);counts[category]+=1
    require(sum(counts.values())==len(wanted)==len(records),'EVERY_REQUIRED_INPUT_EXACTLY_ONCE')
    return dict(worker_input_count=len(wanted),prior_semantic_input_count=len(semantic),
        prior_physical_input_count=len(physical),descriptor_count=len(aliases),counts=counts,records=records,
        prior_failed_declaration_only=True,current_native011_scope_constructed=False,
        live_parent_Frame_coverage_qualified=False,raw_alias_assumed_to_be_locked=False,
        input_scope_modified=False,worker_IO_exemptions_applied=False)


def main():
    import argparse,json,re,sys,time,traceback
    from pathlib import Path
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args();require(1<=args.attempt<=8,'BOUNDED_MAPPING_ATTEMPT')
    denied=[]
    def deny(event,arguments):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('NATIVE011_SCOPE_MAP_PROCESS_DENIED')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    output=f'implementation/p09/evidence/p09-361-native011-prior-scope-map-attempt{args.attempt:03}.v1.json'
    row=dict(state='FAILED_NATIVE011_PRIOR_DECLARATION_MAPPING_NOT_CURRENT_SCOPE',GO_authorized=False,
        product_executed=False,accepted_count_delta=0,official_accepted_count=158)
    q=None;started=time.monotonic()
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        require(not (c.ROOT/output).exists(),'NEW_MAPPING_RESULT');q.pin(SELF);q.pin(scope.SELF)
        prior=a.read_exact(q,PRIOR);worker=a.read_exact(q,WORKER)
        a.fields(prior,dict(task='case165-current-r010-tests',state='DEFERRED_NOT_STARTED',
            worker_created=False,product_body_observed=False,cleanup_confirmed=True),'ORIGINAL_FAILED_PRIOR_NOT_NATIVE011')
        a.fields(worker,dict(state='PASS_ORIGINAL_INHERITED_EVENT_EOF_WORKER_NOT_PRODUCT',fresh_inputs=198,
            final_fresh_hashes=198,actual_product_GO_received=False,process_creation_attempts=0),'REAL_WORKER198_CONTROL_INPUTS')
        frame_declaration=prior['source_frame']['explicit_source_input_representation']
        mapping=compare(worker['source_pins'],frame_declaration,
            prior_frame_count=prior['source_frame']['input_count'])
        q.finish();guard.check(force=True)
        require(not denied and q.final_fresh_hashes==len(q.snapshots),'MAPPING_CLOSING_AND_NO_PROCESS')
        row.update(state='MAPPED_ALL198_AGAINST_FAILED_NATIVE010_DECLARATION_NOT_LIVE_NATIVE011_COVERAGE',
            mapping=mapping,prior_frame_state=prior['source_frame']['frame_state'],
            top_and_frame_declarations_equal=prior['source_input_representation']==frame_declaration,
            prior_byte_boundary_count=len(prior['source_frame']['actual_byte_boundaries']),
            raw_corpus_or_worker_reexecuted=False,input_scope_modified=False,worker_IO_exemptions_applied=False)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,NameError,ImportError) as error:
        row['error_type']=type(error).__name__
        row['error_code']=error.args[0] if error.args and type(error.args[0]) is str and re.fullmatch(
            '[A-Za-z0-9_]{1,160}',error.args[0]) else 'CLOSED_PRIOR_SCOPE_MAPPING_FAILURE'
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-5:]]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=guard.samples,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            process_creation_attempts=len(denied))
        if not row['cleanup_confirmed']:row['state']='FAILED_MAPPING_CLEANUP'
        pin=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        summary=row.get('mapping',{})
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),error_frames=row.get('error_frames'),
            counts=summary.get('counts'),prior_physical_inputs=summary.get('prior_physical_input_count'),
            prior_semantic_inputs=summary.get('prior_semantic_input_count'),
            cleanup=row['cleanup_confirmed'],fresh=row['fresh_inputs'],final=row['final_fresh_hashes'],
            elapsed=row['elapsed_seconds'],CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in guard.samples),default=None),receipt=pin)),flush=True)
    return 0 if row['state'].startswith('MAPPED_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
