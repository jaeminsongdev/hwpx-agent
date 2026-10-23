"""Construct a real unopened run011 parent, never a Native execution entry.

The original preservation partition is reconstructed, not guessed from a
case receipt. The failed010 Frame supplies declarations only. No full corpus
byte boundary, live Frame, metadata callback, GO or product is claimed here.
"""
import argparse
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
from types import SimpleNamespace as NS

SELF='tools/p09/native011_parent_plan.py'
PUBLISHER=dict(path='tools/p09/successor_preparation_workspace_v1.py',bytes=9656,
    sha256='003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98')
PARENT=dict(path='tools/p09/batch_zlib_engine.py',bytes=14940,
    sha256='fc2bc3e67e9352944916cc25a1c1863a888c1529913c20c9e9c9b29d31208772')
NATIVE_SOURCE=dict(path='tools/p09/run_case112_current_stored.py',bytes=23159,
    sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713')
FAILURE_NAMES=('FAILED_FIRST_PIN','FAILED_STOP_PIN')
ENTRY_SOURCE=dict(path='tools/p09/batch_engine_connection.py',bytes=26089,
    sha256='1559a74eb6e19761ce62d46e1bc9ecef06f613b076742ac974945481f2494262')
PARENT_CONTROLS=(SELF,'tools/p09/native011_parent_oracle.py')
SHARED_CONTROL='tools/p09/native011_shared_parent.py'
GUARDS=(
    dict(path='tools/p09/prepared_run_closure_v1.py',bytes=23900,
        sha256='c159da53076f5bb88dce252db163f82a1f1d71522c9dd248349ca615dc84e672'),
    dict(path='tools/p09/owned_cpu_baseline_v1.py',bytes=1389,
        sha256='0fce7a5f5700270291b02167e96c3739943d5a44c0a912eef43555a1a729b4b5'),
    dict(path='tools/p09/preparation_attributed_cpu_v1.py',bytes=9869,
        sha256='ddc1b48f17645337e65125373d9db822477ca6a94cc34e23992498e6c2c7d13d'),
    dict(path='tools/p09/distinct_final_sample_guard_v1.py',bytes=1683,
        sha256='8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3'))


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_PARENT_PLAN_'+code)


def bootstrap_loader(root):
    """Entire original loader bootstrap, without another default helper."""
    path=root/ENTRY_SOURCE['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_BOOTSTRAP_ENTRY')
    for parent in (path.parent,*path.parent.parents):
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),'DIRECT_ENTRY_ANCESTORS')
        if parent==root:break
    with path.open('rb') as stream:raw=stream.read(ENTRY_SOURCE['bytes']+1)
    require(len(raw)==ENTRY_SOURCE['bytes'] and hashlib.sha256(raw).hexdigest()==ENTRY_SOURCE['sha256'],
        'EXACT_WHOLE_ORIGINAL_BOOTSTRAP_ENTRY')
    nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in ('require','bootstrap_loader')
        or isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
        and n.targets[0].id=='BOOTSTRAP']
    require(len(nodes)==3,'WHOLE_ORIGINAL_BOOTSTRAP_DEFINITIONS_AND_PINS')
    env=dict(NS=NS)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),ENTRY_SOURCE['path'],'exec'),env)
    return env['bootstrap_loader'](root)


def bind_parent_controls(plan,controls,batch,checkpoint):
    """Declare named executable controls, never an observed helper union."""
    expected=set(PARENT_CONTROLS)
    require(type(controls) is dict and set(controls) in ({SELF},expected,expected|{SHARED_CONTROL})
        and batch.scope.pins(list(controls.values()))==controls,'EXPLICIT_PARENT_ENTRY_AND_OPTIONAL_ORACLE_ONLY')
    old=plan.batch;old.check()
    require(type(old) is batch.Batch and old.phase=='NEW' and old.parent_connection is None
        and old.initial is old.final is old.active is None and not old.cases
        and not old.metadata_reader_active,'PARENT_CONTROLS_BEFORE_ANY_BATCH_OPEN')
    require(all(batch.plain(getattr(old,n))==getattr(plan,n) for n in ('whole','current','history')),
        'PARENT_CONTROLS_EXACT_PLAN')
    require(not set(controls)&(set(plan.whole)|set(plan.logical)|set(plan.history)),
        'NO_CONTROL_REPLACEMENT_OR_HISTORY_RECLASSIFICATION')
    scope=batch.scope;whole=scope.extend(plan.whole,controls);current=scope.extend(plan.current,controls)
    logical=scope.extend(plan.logical,controls)
    owner=batch.Batch(whole,current,batch.plain(plan.history),first_index=165,checkpoint=checkpoint,identity=old.identity)
    return NS(**{**vars(plan),'batch':owner,'whole':whole,'current':current,'logical':logical}),dict(
        explicit_parent_control_pins=list(controls.values()),preservation_unchanged=True,original_plan_unmodified=True)


def declared_current(representation,scope):
    """Prove lossless declaration mapping, not current byte freshness."""
    semantic=scope.pins(representation['semantic_source_freeze'])
    physical=scope.pins(representation['physical_source_freeze'])
    descriptors=representation['descriptors']
    require(type(descriptors) is list and len(descriptors)==162,'EXACT162_DECLARED_DESCRIPTORS')
    aliases={};targets=set()
    for row in descriptors:
        require(type(row) is dict and set(row)=={'schema_version','next_case',
            'semantic_original_pin','physical_envelope_pin'} and row['next_case']==165
            and row['schema_version']=='hwpx-agent.p09-lossless-runtime-source-projection/v1',
            'EXACT_PRIOR_DESCRIPTOR_SCHEMA')
        original=scope.pins([row['semantic_original_pin']]);carrier=scope.pins([row['physical_envelope_pin']])
        name=next(iter(original));target=next(iter(carrier))
        require(name not in aliases and target not in targets,'UNIQUE_PRIOR_DECLARATION_ALIASES')
        require(semantic.get(name)==original[name] and physical.get(target)==carrier[target],
            'BOTH_DECLARED_ALIAS_ENDPOINTS_PRESENT')
        aliases[name]=carrier[target];targets.add(target)
    projected={}
    for name,pin in semantic.items():
        item=aliases.get(name,pin)
        require(item['path'] not in projected,'NO_PRIOR_PHYSICAL_COLLISION')
        projected[item['path']]=dict(item)
    require(projected==physical,'COMPLETE_PRIOR_LOGICAL_PHYSICAL_DECLARATION')
    return semantic,physical


def intrinsic_failures(raw,scope):
    """Resolve the two unconditional reads from the exact whole Native source."""
    require(type(raw) is bytes and len(raw)==NATIVE_SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==NATIVE_SOURCE['sha256'],'EXACT_ORIGINAL_NATIVE_SOURCE')
    tree=ast.parse(raw);pins={}
    for node in tree.body:
        if (isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
            and node.targets[0].id in FAILURE_NAMES):
            call=node.value
            require(isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='dict'
                and not call.args and {k.arg for k in call.keywords}=={'path','bytes','sha256'},
                'CLOSED_ORIGINAL_FAILURE_PIN_LITERAL')
            pins[node.targets[0].id]={k.arg:ast.literal_eval(k.value) for k in call.keywords}
    require(set(pins)==set(FAILURE_NAMES),'EXACT_TWO_ORIGINAL_FAILURE_DECLARATIONS')
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_owned')
    for name in FAILURE_NAMES:
        wanted=ast.dump(ast.parse('q.json('+name+'["path"])',mode='eval').body,include_attributes=False)
        require(sum(ast.dump(n,include_attributes=False)==wanted for n in ast.walk(function))==1,
            'ONE_ACTUAL_UNCONDITIONAL_INPUT_PINS_READ_PER_FAILURE')
    return scope.pins([pins[n] for n in FAILURE_NAMES])


def bind_intrinsic_failures(plan,required,batch,checkpoint):
    """Explicit mandatory current dependencies, never guessed receipt history.

    Original read_plan's filename partition omits these two outer Native reads.
    Keep the original plan untouched; the new partition moves exactly these
    same-byte inputs from preservation to current and preserves the whole set.
    """
    old=plan.batch;old.check()
    require(type(old) is batch.Batch and old.phase=='NEW' and old.parent_connection is None
        and old.initial is old.final is old.active is None and not old.cases
        and not old.metadata_reader_active,'INTRINSIC_DEPENDENCIES_BEFORE_ANY_BATCH_OPEN')
    scope=batch.scope
    expected={
        'implementation/p09/evidence/p09-361-case112-current-runtime-run001.v1.json':
            (3720,'8c26646fe69111b5429f33ee53f13c044d2d3d45828d8141e15c3f7252e3f7e2'),
        'implementation/p09/evidence/p09-361-case112-current-runtime-run003.v1.json':
            (56097,'1fd05236e9c1a56be7402a708e4372e154f957e617cf6286bd1ef0ef6356c470')}
    require(scope.pins(list(required.values()))==required and set(required)==set(expected)
        and all((p['bytes'],p['sha256'])==expected[n] for n,p in required.items()),
        'ONLY_TWO_EXACT_INTRINSIC_FAILURE_PINS_NOT_ARBITRARY_PROMOTION')
    require(all(batch.plain(getattr(old,n))==getattr(plan,n) for n in ('whole','current','history')),
        'INTRINSIC_EXACT_UNOPENED_PLAN')
    require(all(plan.history.get(n)==p and plan.whole.get(n)==p and plan.logical.get(n)==p
        and n not in plan.current for n,p in required.items()),'EXACT_TWO_PRESERVED_RAW_INPUTS')
    current=scope.extend(plan.current,required)
    history={n:dict(p) for n,p in plan.history.items() if n not in required}
    require(set(current).isdisjoint(history) and {**current,**history}==plan.whole,
        'LOSSLESS_WHOLE_AND_ALL_OTHER_HISTORY_UNCHANGED')
    owner=batch.Batch(batch.plain(plan.whole),current,history,first_index=165,
        checkpoint=checkpoint,identity=old.identity)
    return NS(**{**vars(plan),'batch':owner,'current':current,'history':history}),dict(
        original_plan_unmodified=True,whole_input_pins_unchanged=True,
        mandatory_current_inputs=list(required.values()),
        preservation_before=len(plan.history),preservation_after=len(history),
        all_other_preservation_inputs_exactly_retained=True,
        basis='Exact original run_owned/input_pins JSON reads, not receipt filename or observed snapshots')


def main():
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--inspect-oracle',action='store_true')
    parser.add_argument('--inspect-shared',action='store_true')
    parser.add_argument('--metadata-generation',type=int)
    args=parser.parse_args();require(1<=args.attempt<=8,'BOUNDED_READONLY_ATTEMPT')
    require((not args.inspect_shared or args.inspect_oracle)
        and ((args.metadata_generation is not None)==args.inspect_shared),'EXACT_SHARED_REPORT_AND_ORACLE_MODE')
    denied=[]
    def deny(event,arguments):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('NATIVE011_PARENT_PLAN_PROCESS_DENIED')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,owned_source_read_pressure as bytes_policy
    source_loader=bootstrap_loader(c.ROOT)
    # Whole pinned definitions, not hidden/removed sys.modules or weaker guards.
    guards,_=source_loader.load(c.ROOT,list(GUARDS),{})
    host,baseline,policy,final=(getattr(guards,n) for n in ('prepared_run_closure_v1',
        'owned_cpu_baseline_v1','preparation_attributed_cpu_v1','distinct_final_sample_guard_v1'))
    publishers,_=source_loader.load(c.ROOT,[PUBLISHER],{})
    publisher=publishers.successor_preparation_workspace_v1
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    family='shared-parent' if args.inspect_shared else 'parent-oracle' if args.inspect_oracle else 'parent-plan'
    output=f'implementation/p09/evidence/p09-361-native011-{family}-attempt{args.attempt:03}.v1.json'
    row=dict(state='FAILED_NATIVE011_REAL_PARENT_CONSTRUCTION_NOT_NATIVE',stage='BOOTSTRAP',
        GO_authorized=False,accepted_count_delta=0,official_accepted_count=158,
        full_current_bytes_or_live_Native_Frame_qualified=False,worker_IO_exemptions_applied=False)
    q=None;shared_resources=None;started=time.monotonic()
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        require(not (c.ROOT/output).exists(),'EXCLUSIVE_NEW_RESULT')
        q.pin(SELF);a.exact(q.pin(PUBLISHER['path']),PUBLISHER,'ORIGINAL_PRIVATE_PUBLISHER')
        a.exact(q.pin(ENTRY_SOURCE['path']),ENTRY_SOURCE,'ORIGINAL_BOOTSTRAP_ENTRY_FIRST_AND_CLOSING_BYTES')
        q.pin(source_loader.SELF)
        for pin in GUARDS:a.exact(q.pin(pin['path']),pin,'ORIGINAL_PRIVATE_GUARD_FIRST_AND_CLOSING_BYTES')
        paths=('native011_preparation','native011_worker_transport','native011_zlib_binding',
            'native011_worker_preparation','native011_scope_map','native011_scope_delta',
            'batch_zlib_engine','batch_engine_connection')
        if args.inspect_oracle:paths+=('native011_parent_oracle',)
        if args.inspect_shared:paths+=('native011_metadata_report','native011_shared_parent')
        pins=[q.pin('tools/p09/'+name+'.py') for name in paths];allowed={p['path']:p for p in pins}
        a.exact(allowed[PARENT['path']],PARENT,'UNCHANGED_ORIGINAL_SCOPE_PROJECTOR')
        class Source:
            def __init__(self,name):self.name=name
            def __fspath__(self):return os.fspath(c.ROOT/self.name)
            def open(self,mode):
                require(mode=='rb' and self.name in allowed,'DECLARED_PRIVATE_SOURCE_ONLY')
                pin=allowed[self.name];before=q.maximum_parse_bytes
                try:
                    q.maximum_parse_bytes=min(before,pin['bytes']+1)
                    actual,raw=q._read(self.name,parse=True);q._bind(self.name,actual)
                finally:q.maximum_parse_bytes=before
                a.exact(actual,pin,'FRESH_PRIVATE_SOURCE_BYTES');return io.BytesIO(raw)
        class Root:
            def __fspath__(self):return os.fspath(c.ROOT)
            def __truediv__(self,name):return Source(name)
        modules,_=source_loader.load(Root(),pins,{'current_stored_runtime_scope':scope})
        entry,parent=modules.batch_engine_connection,modules.batch_zlib_engine
        a.exact(allowed[entry.SELF],parent.ENGINE,'UNCHANGED_ORIGINAL_PLAN_ENTRY')
        row['stage']='RECONSTRUCT_ORIGINAL_PRESERVATION_PARTITION'
        libraries,_=entry.planning_libraries(c.ROOT,q,a,source_loader)
        admission,batch,reuse=(getattr(libraries,n) for n in
            ('batch_scope_admission','batch_verification','verification_reuse'))
        data=admission.read_plan(q,a,batch,reuse);entry.extend_execution(data,q,batch)
        old=data.planned
        mapping,delta=modules.native011_scope_map,modules.native011_scope_delta
        prior=a.read_exact(q,mapping.PRIOR);worker_receipt=a.read_exact(q,mapping.WORKER)
        a.fields(prior,dict(state='DEFERRED_NOT_STARTED',worker_created=False,product_body_observed=False),
            'FAILED_PRIOR_DECLARATION_NEVER_ACCEPTED')
        original_current,physical=declared_current(
            prior['source_frame']['explicit_source_input_representation'],scope)
        require(len(physical)==prior['source_frame']['input_count']==2929,'EXACT_FAILED_PRIOR_CURRENT_COUNT')
        a.exact(old.logical[NATIVE_SOURCE['path']],NATIVE_SOURCE,'DECLARED_ORIGINAL_NATIVE_SOURCE')
        raw=modules.native011_preparation.bounded_read(q,a,NATIVE_SOURCE,65536)
        required_failures=intrinsic_failures(raw,scope)
        a.exact(prior['preserved_failed_first_pin'],required_failures[
            prior['preserved_failed_first_pin']['path']],'SAME_FAILED_FIRST_IDENTITY_NOT_ACCEPTANCE')
        a.exact(prior['preserved_pre_worker_commit_stop_pin'],required_failures[
            prior['preserved_pre_worker_commit_stop_pin']['path']],'SAME_FAILED_STOP_IDENTITY_NOT_ACCEPTANCE')
        data.planned,partition_proof=bind_intrinsic_failures(data.planned,required_failures,batch,q.checkpoint)
        row['mandatory_current_partition_correction']=partition_proof
        history=batch.plain(data.planned.history)
        overlap=sorted(set(original_current)&set(history))
        row['prior_declared_current_overlaps_reconstructed_preservation']=dict(count=len(overlap),
            same_pins=all(original_current[n]==history[n] for n in overlap),paths=overlap[:16])
        require(not overlap,'NO_PRIOR_DECLARATION_PROMOTES_PRESERVATION')
        manifest=a.read_exact(q,modules.native011_worker_preparation.PACKAGE[0])
        row['stage']='PROJECT_REAL_PLAN_AND_EXPLICIT_EIGHT_ADDITIONS'
        projection=parent.project_plan(data,manifest,original_current,batch,q.checkpoint)
        require(data.planned.history==history,'EXACT_RECONSTRUCTED_PRESERVATION_RETAINED')
        changes=delta.derive(worker_receipt['source_pins'],data.planned.current,data.planned.logical)
        data.planned,delta_proof=delta.extend_plan(data.planned,changes,worker_receipt['source_pins'],batch,q.checkpoint)
        control_names=PARENT_CONTROLS if args.inspect_oracle else (SELF,)
        if args.inspect_shared:control_names+=(SHARED_CONTROL,)
        controls={n:dict(q.pin(n)) for n in control_names}
        data.planned,parent_controls=bind_parent_controls(data.planned,controls,batch,q.checkpoint)
        row['explicit_parent_controls']=parent_controls
        if args.inspect_shared:
            admitted=modules.native011_shared_parent.admit_report(c.ROOT,q,a,batch,data,args.metadata_generation)
            row['metadata_report_admission']=admitted.proof
        require(data.declared.to_physical(list(data.planned.logical.values()))==data.planned.whole,
            'FULL_NEW_WHOLE_LOGICAL_PHYSICAL_EQUALITY')
        row.update(projection=projection,scope_delta=delta_proof,
            partition=dict(whole_inputs=len(data.planned.whole),current_inputs=len(data.planned.current),
                preservation_inputs=len(history),preservation_sha256=delta.digest(history),
                whole_sha256=delta.digest(data.planned.whole),current_sha256=delta.digest(data.planned.current)),
            declared_cost=scope.cost(data.planned.current,14),complete_600_second_cost_qualified=False)
        row['stage']='CONSTRUCT_REAL_RUN011_ENGINE_AND_ORIGINAL_PARENT'
        prepared=modules.native011_worker_preparation.prepare(c.ROOT,q,a,scope,bytes_policy,source_loader)
        linked=prepared.linked
        def metadata_unavailable(reader):
            q.checkpoint();require(False,'NEW_METADATA_AND_WHOLE_BOUNDARIES_NOT_YET_CONNECTED')
        linked.engine.run_owned.__globals__['binding']=metadata_unavailable
        if args.inspect_shared:
            shared_resources=modules.native011_shared_parent.prepare(c.ROOT,q,a,source_loader,batch,data,prepared,entry)
        actual,state=data.planned.batch.connect_parent(linked.engine,prepared.entry.graph)
        connection=data.planned.batch.parent_connection
        require(actual.worker is linked.original_worker and state.attempts==0 and state.frames==[]
            and linked.state.attempts==linked.state.calls==0 and data.planned.batch.phase=='NEW'
            and data.planned.batch.initial is data.planned.batch.final is data.planned.batch.active is None
            and connection.lifecycle_connected and len(connection.frame_type.__mro__)==(5 if args.inspect_shared else 4),
            'ACTUAL_ORIGINAL_PARENT_CONNECTED_NO_FRAME_OR_WORKER_EXECUTED')
        require(actual.run_owned.__globals__['binding'] is metadata_unavailable,
            'ACTUAL_PARENT_METADATA_FAILS_CLOSED')
        if args.inspect_shared:
            bound=modules.native011_shared_parent.attach(c.ROOT,q,a,batch,data,prepared,actual,entry,shared_resources,admitted)
            row['shared_parent_connection']=bound.proof
        if args.inspect_oracle:
            row['stage']='REAL_PARENT_INDEPENDENT_CHECKER_AND_DECLARED_BUDGET'
            row['oracle_construction']={}
            modules.native011_parent_oracle.connect(c.ROOT,q,a,source_loader,batch,data,prepared,actual,
                entry,row['oracle_construction'])
        q.finish();guard.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'FULL_CONSTRUCTION_CLOSING_BYTES_NO_PROCESS')
        row.update(state='PASS_REAL_NATIVE011_UNOPENED_PLAN_AND_PARENT_NOT_LIVE_FRAME_OR_NATIVE',
            preparation=prepared.proof,actual_parent_constructed=True,parent_attempts=0,Frame_instances=0,
            worker_attempts=0,worker_calls=0,product_calls=0,metadata_blocked=True,
            reconstructed_preservation_unchanged=data.planned.history==history,
            all_required_worker_inputs_in_current=len(worker_receipt['source_pins']),
            helper64_full_Native_union_qualified=False,independent_checker_connected=False,
            failed_native010_promoted=False,whole_declared_corpus_freshly_hashed=False,
            prior_suites_reexecuted=False)
        if args.inspect_oracle:
            row.update(state='PASS_REAL_NATIVE011_PARENT_ORACLE_AND_DECLARED_BUDGET_NOT_NATIVE',
                independent_checker_connected=True,helper64_full_Native_union_qualified=True)
        if args.inspect_shared:
            row.update(state='PASS_REAL_NATIVE011_SHARED_METADATA_CALLBACK_CONSTRUCTION_NOT_NATIVE',
                metadata_blocking_reason='ORIGINAL_WHOLE_BATCH_AUDIT_REQUIRED',metadata_body_executed=False)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,NameError,ImportError) as error:
        row['error_type']=type(error).__name__
        row['error_code']=error.args[0] if error.args and type(error.args[0]) is str and re.fullmatch(
            '[A-Za-z0-9_]{1,160}',error.args[0]) else 'CLOSED_PARENT_PLAN_FAILURE'
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        if shared_resources is not None and hasattr(shared_resources.batch,'shared'):
            shared_resources.batch.shared.restore()
            row['shared_budget_restored']=shared_resources.batch.shared.restored
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=guard.samples,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            process_creation_attempts=len(denied))
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        oracle=row.get('oracle_construction',{});inventory=oracle.get('helper_inventory',{})
        print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),
            error_frames=row.get('error_frames'),partition=row.get('partition'),cleanup=row['cleanup_confirmed'],
            preservation_overlap=row.get('prior_declared_current_overlaps_reconstructed_preservation'),
            oracle=dict(stage=oracle.get('stage'),default_helpers=inventory.get('default_count'),
                Native_helpers=inventory.get('Native_count'),missing_source=oracle.get('missing_source_open'),
                missing_declared_sources=oracle.get('missing_declared_sources'),
                with_preparation15_seconds=oracle.get('budget',{}).get('with_preparation15_seconds'),
                independent_checker_connected=oracle.get('independent_checker_connected')) if oracle else None,
            shared_callback_bound=row.get('shared_parent_connection',{}).get('actual_metadata_callback_bound'),
            fresh=row['fresh_inputs'],final=row['final_fresh_hashes'],elapsed=row['elapsed_seconds'],receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
