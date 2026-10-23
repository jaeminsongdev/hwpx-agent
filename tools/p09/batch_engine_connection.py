"""Connect the published run010 graph to the original engine, without GO.

Retain the qualified batch metadata result when its exact programs match.
Explicit production inputs include this entry, its worker and the three
batch-policy helpers. Tests and the read-only qualification receipt are not
transitive runtime source unions.
"""
import json
import re
from types import SimpleNamespace as NS

SELF = 'tools/p09/batch_engine_connection.py'
TEST = 'tools/p09/tests/test_batch_engine_connection.py'
WORKER = 'tools/p09/batch_worker_launch.py'
POLICY_HELPERS = ('tools/p09/historical_receipt_batch_partition_v1.py',
    'tools/p09/phased_preservation_read_gate_v1.py',
    'tools/p09/phased_preservation_read_gate_v2.py')
EXECUTION_INPUTS = (SELF,WORKER)+POLICY_HELPERS
QUALIFICATION = dict(path='implementation/p09/evidence/p09-361-case165-batch-source-metadata-run010-qual001.v1.json',
    bytes=10829,sha256='8822f82682ad0268d29a64a5060ac59caf5d5ee74c8f4144994cd0389f40b8f5')
BOOTSTRAP = (
    dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62'),
    dict(path='tools/p09/prepared_run_closure_v1.py',bytes=23900,sha256='c159da53076f5bb88dce252db163f82a1f1d71522c9dd248349ca615dc84e672'),
    dict(path='tools/p09/owned_cpu_baseline_v1.py',bytes=1389,sha256='0fce7a5f5700270291b02167e96c3739943d5a44c0a912eef43555a1a729b4b5'),
    dict(path='tools/p09/terminal_metadata_pressure_v1.py',bytes=2956,sha256='7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd'),
    dict(path='tools/p09/distinct_final_sample_guard_v1.py',bytes=1683,sha256='8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3'))


def require(ok, code):
    if not ok:raise ValueError('BATCH_ENGINE_'+code)


def bootstrap_loader(root):
    """Exact small stdlib-only loader, no registered or hidden project module."""
    import hashlib
    pin=BOOTSTRAP[0];path=root/pin['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_BOOTSTRAP_SOURCE')
    for parent in (path.parent,*path.parent.parents):
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),'DIRECT_BOOTSTRAP_ANCESTORS')
        if parent==root:break
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'EXACT_BOOTSTRAP_LOADER')
    env=dict(__name__='p09_exact_entry_loader',__file__=pin['path'])
    exec(compile(raw,pin['path'],'exec'),env)
    return NS(**env)


def planning_libraries(root,reader,a,loader):
    """Original complete policy modules, explicitly linked before imports.

    Nothing is removed from sys.modules. Bodies and the default import graph
    stay unchanged; only private dependency namespaces are supplied.
    """
    import ast,os,threading
    evidence=a.read_exact(reader,QUALIFICATION)
    pins={p['path']:dict(p) for p in evidence['result']['construction_source_pins']}
    batch_name='tools/p09/batch_verification.py'
    actual,raw=reader._read(batch_name,parse=True);reader._bind(actual['path'],actual)
    a.exact(actual,pins[batch_name],'QUALIFIED_WHOLE_POLICY_FOR_PACED_BOOTSTRAP')
    nodes=[n for n in ast.parse(bytes(raw)).body if isinstance(n,ast.ClassDef) and n.name=='PacedNamespaceLoader']
    require(len(nodes)==1,'ONE_ORIGINAL_PACED_LOADER_CLASS')
    env=dict(NS=NS,scope=a.scope,os=os,threading=threading,require=require,
        __name__='p09_exact_entry_paced_loader')
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),batch_name,'exec'),env)
    for name in POLICY_HELPERS:pins[name]=dict(reader.pin(name))
    names=(*POLICY_HELPERS,'tools/p09/batch_worker_entry.py',batch_name,
        'tools/p09/batch_scope_admission.py','tools/p09/verification_reuse.py')
    paced=env['PacedNamespaceLoader'](loader,reader,pins)
    libraries,_=paced.api.load(root,[pins[n] for n in names],
        {'current_stored_runtime_scope':a.scope,'runtime_input_frame':a.native.frames})
    return libraries,paced


def private_package_imports(admission,worker,loader,configuration):
    """Reuse the original private import-map connector, never sys.modules."""
    import importlib
    def selected(name,*args,**kwargs):
        if name=='runtime_envelope_namespace_bundle_v1':
            require(not args and not kwargs,'EXACT_LOADER_IMPORT_NO_PACKAGE')
            return loader
        return importlib.import_module(name,*args,**kwargs)
    facade=NS(**{**vars(importlib),'import_module':selected})
    configuration.override_import(admission,'batch_worker_entry',worker)
    configuration.override_import(admission,'importlib',facade)


def admit_helpers(helpers,known,reader,exact):
    """Reject the complete undeclared set before any helper-byte reads."""
    names=helpers['original_Native_helper_union']
    missing=sorted(set(names)-set(known))
    if missing:
        raise ValueError('BATCH_ENGINE_EVERY_OBSERVED_HELPER_ALREADY_DECLARED',tuple(missing))
    for name in names:
        exact(reader.pin(name),known[name],'ACTUAL_HELPER_PIN_NOT_HIDDEN')


def retained_metadata(reader,a,admission):
    row = a.read_exact(reader,QUALIFICATION)
    require(row.get('schema_version') == 'hwpx-agent.p09-batch-source-metadata-qualification/v1'
        and row.get('qualification_only_not_native_or_execution_permission') is True,
        'EXACT_NO_GO_QUALIFICATION')
    a.exact(row['preparation_report_pin'],admission.PACKAGE[3],'EXACT_PUBLISHED_PACKAGE_QUALIFIED')
    result = row['result']
    a.fields(result,dict(state='PASS_BATCH_REAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE',
        cleanup_confirmed=True,GO_authorized=False,accepted_count_delta=0,
        product_or_worker_or_process_executed=False),'ACTUAL_COMPLETED_METADATA_NOT_NATIVE')
    a.fields(result['whole_batch'],dict(phase='EMPTY_BATCH_AUDITED_NOT_ACCEPTED',whole_inputs=3319,
        current_inputs=2898,preservation_inputs=421,whole_initial_complete=True,whole_final_complete=True,
        cases_with_original_Frame_checks=0),'EXACT_TWO_WHOLE_BOUNDARIES')
    rows = result['construction_source_pins']
    require(type(rows) is list and len(rows) == len(admission.PROGRAMS)
        and {p['path'] for p in rows} == set(admission.PROGRAMS),'EXACT_EIGHT_QUALIFIED_PROGRAMS')
    for pin in rows:a.exact(reader.fresh_pin(pin['path']),pin,'UNCHANGED_ACTUALLY_QUALIFIED_PROGRAM')
    return dict(retained_qualification_pin=dict(QUALIFICATION),unchanged_programs=len(rows),
        whole3319_or_parent_metadata_reexecuted=False,Native_or_product_qualification_reused=False)


def extend_execution(data,reader,batch):
    """Named production inputs; no test/receipt/observed-input expansion."""
    added = {name:dict(reader.pin(name)) for name in EXECUTION_INPUTS}
    previous = data.planned
    whole = batch.scope.extend(previous.whole,added)
    current = batch.scope.extend(previous.current,added)
    policy = batch.Batch(whole,current,previous.history,first_index=165,checkpoint=reader.checkpoint)
    data.planned = NS(batch=policy,whole=whole,current=current,history=previous.history,
        logical=batch.scope.extend(previous.logical,added))
    return added[SELF]


def original_scope_runtime(runtime):
    # install_scope returns a private namespace and never replaces this
    # original function in the factory's original globals. Recover that exact
    # source function, then let install_scope verify its full AST/code again.
    original = runtime.connect_factory.__globals__.get('current_input_scope')
    require(callable(original) and '_batch' not in original.__globals__,
        'ORIGINAL_SCOPE_NOT_PRIOR_BATCH_PROJECTION')
    return NS(**{**vars(runtime),'current_input_scope':original})


def current_logical(data,binding,checkpoint,scope,exact):
    normalized,_ = binding.semantic_union(data.planned.logical,checkpoint)
    carriers = {r['semantic_original_pin']['path']:r['physical_envelope_pin']['path']
        for r in binding.descriptors()}
    selected = {n:dict(p) for n,p in normalized.items() if carriers.get(n,n) in data.planned.current}
    projected,_ = binding.project(selected,checkpoint)
    exact({n:dict(p) for n,p in projected.physical_pins.items()},data.planned.current,'EXACT_NEW_CURRENT_PROJECTION')
    return selected


def current_mappings(binding,current):
    """All original mappings must belong to this declared current boundary."""
    descriptors=binding.descriptors()
    require(descriptors and all(current.get(d['physical_envelope_pin']['path'])==d['physical_envelope_pin']
        for d in descriptors),'ALL_ORIGINAL_MAPPING_CARRIERS_EXACT_CURRENT')
    return descriptors


def shared_chain(frame,base,owner,module):
    """Only the original shared-budget layer, not arbitrary subclasses."""
    from types import FunctionType,CodeType
    mro=frame.__mro__
    require(len(mro)==5 and mro[3:]==(base,object),'EXACT_SHARED_FIVE_CLASS_CHAIN')
    shared=mro[1];fn=vars(shared).get('__init__')
    nested=[n for n in module.frame_type.__code__.co_consts if isinstance(n,CodeType) and n.co_name=='Frame']
    require(len(nested)==1,'ORIGINAL_SHARED_FRAME_DEFINITION')
    codes=[n for n in nested[0].co_consts if isinstance(n,CodeType) and n.co_name=='__init__']
    require(len(codes)==1 and type(fn) is FunctionType and fn.__code__ is codes[0]
        and shared.__bases__==(mro[2],),'ENTIRE_ORIGINAL_SHARED_CONSTRUCTOR_CODE')
    cells=dict(zip(fn.__code__.co_freevars,(c.cell_contents for c in fn.__closure__)))
    require(set(cells)=={'__class__','shared'} and cells['__class__'] is shared and cells['shared'] is owner,
        'EXACT_SAME_PRIVATE_SHARED_OWNER')
    return True


def shared_batch_type(batch,raw,components):
    """Explicit private dependency slot for the existing shared Frame layer.

    Keep the default Batch strict4 policy. This variant changes just its exact
    MRO predicate to strict5 plus the original shared constructor/owner proof.
    Every remaining statement has an AST inverse to the original method.
    """
    import ast,copy
    node=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Batch')
    node=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='connect_parent')
    untouched=ast.dump(node,include_attributes=False)
    def compile_class(method,environment):
        cls=ast.ClassDef(name='Batch',bases=[],keywords=[],body=[method],decorator_list=[])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),batch.SELF,'exec'),environment)
        return environment['Batch'].connect_parent
    env=dict(vars(batch))
    baseline=compile_class(copy.deepcopy(node),env)
    require(batch._code_shape(baseline.__code__)==batch._code_shape(batch.Batch.connect_parent.__code__),
        'ENTIRE_ORIGINAL_BATCH_PARENT_METHOD')
    substitutions=(('len(frame_type.__mro__) == 4','len(frame_type.__mro__) == 5'),
        ('frame_type.__mro__[2:] == (base, object)','_shared_chain(frame_type,base,self.shared,_shared_module)'))
    for old,new in substitutions:
        before=ast.parse(old,mode='eval').body;after=ast.parse(new,mode='eval').body
        hits=[]
        class Rewrite(ast.NodeTransformer):
            def visit(self,item):
                if ast.dump(item,include_attributes=False)==ast.dump(before,include_attributes=False):
                    changed=copy.deepcopy(after);changed._shared_before=copy.deepcopy(item);hits.append(1);return changed
                return super().visit(item)
        node=Rewrite().visit(node)
        require(len(hits)==1,'ONE_EXACT_SHARED_PARENT_PREDICATE_SLOT')
    class Undo(ast.NodeTransformer):
        def visit(self,item):
            return copy.deepcopy(item._shared_before) if hasattr(item,'_shared_before') else super().visit(item)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==untouched,
        'ALL_OTHER_BATCH_PARENT_STATEMENTS_UNCHANGED')
    module=components.shared_metadata_frame_decoder_budget_v1
    env=dict(vars(batch),_shared_chain=shared_chain,_shared_module=module)
    original=compile_class(node,env)
    class SharedBatch(batch.Batch):
        def connect_parent(self,engine,graph,*,connect_lifecycle=True):
            self.shared=module.SharedBudget()
            factory=graph.frames.frame_type
            def selected(base,binding):return module.frame_type(base,binding,factory,self.shared)
            self.metadata_connection=components.lossless_metadata_connection_v1.connect_engine(engine,graph.binding,
                components.fresh_lossless_metadata_reader_v1,graph.frames.connection.original.DecoderBudget,
                self.checkpoint,self.shared)
            graph.frames.frame_type=selected
            try:return original(self,engine,graph,connect_lifecycle=connect_lifecycle)
            finally:graph.frames.frame_type=factory
    return SharedBatch


def attach_callback(assembled,connected,data,explicit,batch,raw_runtime,report_pin,manifest_pin):
    descriptors=current_mappings(connected.graph.binding,data.planned.current)
    runtime, inverse = batch.install_scope(original_scope_runtime(connected.runtime),raw_runtime,assembled.batch)
    env = assembled.built.engine.run_owned.__globals__
    require(env is assembled.parent.run_owned.__globals__,'SAME_ACTUAL_PARENT_AND_ENGINE_ENVIRONMENT')
    require(getattr(env.get('binding'),'__name__',None) == 'metadata_unavailable',
        'REPLACE_ONLY_EXPLICIT_UNAVAILABLE_BINDING')
    calls=[]
    def callback(reader):
        calls.append(1)
        result=runtime.current_input_scope(reader,connected.graph,connected.core['step'],
            report_pin,manifest_pin,explicit)
        # Preserve the existing lossless-v4 requirement: every declared
        # semantic mapping is actually admitted before the shared Native Frame.
        with assembled.batch.metadata_reader(reader,connected.graph.binding):
            for descriptor in descriptors:
                pin=descriptor['semantic_original_pin']
                connected.graph.binding.__class__.project.__globals__['exact'](
                    reader.pin(pin['path']),pin,'V4_ALL_REAL_METADATA_SEMANTIC_PINS')
        return result
    env['binding'] = callback
    require(assembled.built.engine.run_owned.__globals__['binding'] is callback
        and assembled.parent.run_owned.__globals__['binding'] is callback,'ONE_REAL_CALLBACK_NOT_STALE_COPY')
    return NS(callback=callback,calls=calls,runtime=runtime,inverse=inverse)


def connect(root,reader,data,connected,a,batch,admission):
    from types import FunctionType
    paths=('lossless_metadata_connection_v1','fresh_lossless_metadata_reader_v1',
        'shared_metadata_frame_decoder_budget_v1','native009_full72_construction_v1',
        'native009_parent_launch_v1','worker_readiness_v1','worker_readiness_connection_v1','batch_worker_launch',
        'current_queue_successor_lossless_runtime_v4','native009_full75_dispatch_connection_v1')
    require(all('tools/p09/'+n+'.py' in connected.known for n in paths),'ALL_NAMED_CONNECTION_SOURCES_DECLARED')
    components,_=connected.loader.load(root,[connected.known['tools/p09/'+n+'.py'] for n in paths],{})
    actual,raw_batch=reader._read(batch.SELF,parse=True);reader._bind(actual['path'],actual)
    a.exact(actual,connected.known[batch.SELF],'ORIGINAL_BATCH_FOR_EXACT_SHARED_SLOT')
    SharedBatch=shared_batch_type(batch,bytes(raw_batch),components)
    actual,raw_engine = reader._read(batch.ENGINE,parse=True);reader._bind(actual['path'],actual)
    a.exact(actual,connected.known[batch.ENGINE],'ORIGINAL_WHOLE_ENGINE_BUILDER')
    actual,raw_runtime = reader._read(batch.RUNTIME,parse=True);reader._bind(actual['path'],actual)
    a.exact(actual,connected.known[batch.RUNTIME],'ORIGINAL_WHOLE_SCOPE_AND_FACTORY')
    builder = batch.prepare_engine_builder(bytes(raw_engine),connected.runtime,bytes(raw_runtime))
    api = NS(runtime=connected.runtime,metadata=connected.runtime.metadata)
    configuration=components.current_queue_successor_lossless_runtime_v4
    oracle_api,oracle_state=components.native009_full75_dispatch_connection_v1.oracle_loader(
        root,connected.loader,configuration,api.metadata,a,connected.known[configuration.ORACLE['path']])
    launch=components.batch_worker_launch.launch_api(root,connected.loader)
    require(launch.ENTRY==WORKER and launch.TASK==connected.graph.worker.TASK,'EXACT_RUN010_WORKER_LAUNCH')
    contexts=[]
    def load(actual_root,pins,reuse):
        libraries,proof=oracle_api.load(actual_root,pins,reuse)
        if hasattr(libraries,'post_product_recovery_connection_v1'):
            require(not contexts,'ONE_REAL_PARENT_READINESS_CONSTRUCTION')
            context_api,context=components.native009_parent_launch_v1.recovery_api(
                libraries.post_product_recovery_connection_v1,root,dict(data.planned.current[WORKER]),launch,
                components.worker_readiness_v1,components.worker_readiness_connection_v1,
                a.c)
            contexts.append(context)
            libraries=NS(**{**vars(libraries),'post_product_recovery_connection_v1':context_api})
        return libraries,proof
    loader=NS(**{**vars(connected.loader),'load':load})
    prepared = NS(loader=loader,future_engine=builder,api=api,
        admitted_entry=NS(graph=connected.graph))
    original=batch.construct_runtime
    construct=FunctionType(original.__code__,dict(original.__globals__,Batch=SharedBatch),
        argdefs=original.__defaults__,closure=original.__closure__)
    construct.__kwdefaults__=original.__kwdefaults__
    assembled = construct(root,reader,prepared,data.planned,data.planned.logical,connected.known,a)
    require(oracle_state.loads==1 and oracle_state.oracle is not None,'ONE_ORIGINAL_ADDITIONAL_ACCOUNTING_ORACLE')
    oracle_proof=components.native009_full75_dispatch_connection_v1.verify_checker(
        assembled.checker,connected.graph,configuration)
    require(len(contexts)==1,'ACTUAL_ORIGINAL_PARENT_READINESS_CONTEXT')
    context=contexts[0];context.bind_parent(assembled.batch.parent_connection.state)
    explicit = admission.parent_sources(data,batch)
    explicit = batch.scope.extend(explicit,{n:dict(data.planned.current[n]) for n in EXECUTION_INPUTS})
    attached = attach_callback(assembled,connected,data,explicit,batch,bytes(raw_runtime),admission.PACKAGE[3],admission.PACKAGE[0])
    # A real callback must still refuse IO before its OWN new batch begin().
    denied = NS(checkpoint=reader.checkpoint)
    try:attached.callback(denied)
    except ValueError as error:
        require(error.args == ('BATCH_VERIFY_READY_METADATA_OWNER_ONLY',),'EXACT_PREAUDIT_DENIAL_NOT_RESOURCE_STOP')
    else:require(False,'NO_METADATA_IO_BEFORE_NEW_BATCH_AUDIT')
    required = current_logical(data,connected.graph.binding,reader.checkpoint,batch.scope,a.exact)
    cost = connected.graph.binding.runtime_budget(required,167,assembled.built.window.DIRECT.runtime_budget,reader.checkpoint)
    total = cost['predicted_runtime_combined_seconds']+15
    require(total < 600 and cost['unallocated_margin_seconds'] == 60,'ORIGINAL_COMPLETE600_PLUS_PREPARATION15')
    require(assembled.built.state.attempts == assembled.built.state.calls == 0
        and assembled.batch.parent_connection.state.attempts == 0
        and assembled.batch.parent_connection.state.frames == [],'ZERO_ACTUAL_EXECUTION')
    helpers=components.native009_full72_construction_v1.helper_inventory(root,assembled.parent)
    # Observe the real current process before any project test imports. Never
    # remove helpers or increase64 to make a Native qualification pass.
    admit_helpers(helpers,connected.known,reader,a.exact)
    shared=assembled.batch.shared
    require(shared.metadata is shared.frame is None and not shared.restored,'FRESH_UNUSED_SHARED_OWNER')
    require(context.attempts==context.jobs==0 and not context.bindings and context.parent.attempts==0,
        'NO_JOB_READINESS_OR_WORKER_EXECUTION')
    return NS(assembled=assembled,attached=attached,proof=dict(
        actual_original_engine_and_historical_checker_constructed=True,
        actual_new_manifest_and_full162_graph_connected=True,
        current_metadata_callback_bound_to_actual_engine_and_parent=True,
        original_scope_AST_inverse=attached.inverse['exact_original_AST_inverse'],
        preaudit_callback_calls=len(attached.calls),preaudit_denied_before_metadata_IO=True,
        actual_worker_attempts=0,actual_parent_attempts=0,Frame_instances=0,
        physical_identity=10,logical_public_run=1,product_capture_seconds=10,
        current_scope_declaration=assembled.batch.summary(),
        shared_owner_connected_but_unused=True,
        original_shared_Frame_constructor_and_exact_private_owner_verified=True,
        additional_independent_accounting_oracle=oracle_proof,
        original_accounting_oracle_loads=oracle_state.loads,
        all_original_metadata_mappings_in_current=len(current_mappings(connected.graph.binding,data.planned.current)),
        metadata_connection_readers=len(assembled.batch.metadata_connection.readers),
        helper_inventory=helpers,helper64_nominal_fit=helpers['Native_count']<=64,
        actual_run010_readiness_context_bound_but_unused=True,
        original_readiness_seconds=components.worker_readiness_v1.SECONDS,
        readiness_context=context.evidence(),worker_entry_pin=dict(data.planned.current[WORKER]),
        original_complete_cost=cost,with_preparation15_seconds=total,
        actual_engine_execution_or_current_whole_sources_or_Native_qualified=False,
        metadata_Frame_shared_decoder5_or_worker_readiness_or_helper64_qualified=False,
        GO_authorized=False,accepted_count_delta=0,
        original_constructor_observations=assembled.proof))


def main():
    import argparse,sys,time,traceback
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
    denied=[]
    def audit(event,values):
        if event in ('subprocess.Popen','os.system','os.startfile'):
            denied.append(event);raise ValueError('BATCH_ENGINE_PROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a
    import conservative_maintenance as c
    import owned_source_read_pressure as bytes_policy
    bootstrap=bootstrap_loader(c.ROOT)
    guards,_=bootstrap.load(c.ROOT,list(BOOTSTRAP[1:]),{})
    host,baseline,pressure,final=(getattr(guards,n) for n in
        ('prepared_run_closure_v1','owned_cpu_baseline_v1','terminal_metadata_pressure_v1','distinct_final_sample_guard_v1'))
    host.configure_host_policy(c)
    guard=baseline.guard_type(pressure.guard_type(final.guard_type(a.Guard)))()
    reader=None;started=time.monotonic()
    row=dict(state='FAILED_CURRENT_BATCH_ENGINE_CONNECTION_NOT_NATIVE',GO_authorized=False,
        accepted_count_delta=0,product_or_worker_process_executed=False,evidence_files_created=0)
    try:
        guard.acquire();reader=a.AcceptanceReader(c.ROOT,guard.check)
        for pin in BOOTSTRAP:a.exact(reader.pin(pin['path']),pin,'ORIGINAL_UNCHANGED_BOOTSTRAP_AND_GUARDS')
        libraries,paced=planning_libraries(c.ROOT,reader,a,bootstrap)
        admission,batch,reuse=(getattr(libraries,n) for n in ('batch_scope_admission','batch_verification','verification_reuse'))
        row['retained_metadata']=retained_metadata(reader,a,admission)
        data=admission.read_plan(reader,a,batch,reuse)
        row['new_execution_program_pin']=extend_execution(data,reader,batch)
        config_pin=data.planned.logical['tools/p09/current_queue_successor_lossless_runtime_v4.py']
        private_loader=batch.PacedNamespaceLoader(bootstrap,reader,{config_pin['path']:config_pin}).api
        config,_=private_loader.load(c.ROOT,[config_pin],{})
        private_package_imports(admission,libraries.batch_worker_entry,bootstrap,
            config.current_queue_successor_lossless_runtime_v4)
        connected=admission.connect_package(c.ROOT,reader,data,a,batch,bytes_policy)
        result=connect(c.ROOT,reader,data,connected,a,batch,admission)
        reader.finish();guard.check(force=True)
        require(reader.final_fresh_hashes == len(reader.snapshots) and not denied,'ALL_FRESH_CLOSING_AND_NO_PROCESS')
        row.update(state='PASS_CURRENT_BATCH_ENGINE_CALLBACK_AND_ORIGINAL_COST_NOT_NATIVE',connection=result.proof)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError,ImportError) as error:
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        if error.args and error.args[0]=='BATCH_ENGINE_EVERY_OBSERVED_HELPER_ALREADY_DECLARED':
            row['undeclared_helper_paths']=list(error.args[1])
        row['error_frames']=[dict(file=c.Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        guard.close()
        if guard.cleanup is not True:row['state']='CLEANUP_FAILED_NOT_NATIVE'
        row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            fresh_inputs=0 if reader is None else len(reader.snapshots),
            final_fresh_hashes=0 if reader is None else reader.final_fresh_hashes,
            physical_bytes_read=0 if reader is None else reader.bytes_read,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s.get('parent_cpu_machine_percent') or 0 for s in guard.samples),default=None),
            private_MiB_max=max((s['parent_private_mib'] for s in guard.samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in guard.samples),default=None),
            subprocess_creation_attempts=len(denied))
        print(json.dumps(row,ensure_ascii=True))
    return 0 if row['state'].startswith('PASS_') else 2


if __name__ == '__main__':raise SystemExit(main())
