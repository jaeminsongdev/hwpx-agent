"""Exact73 packet through full72 composition and entire original reconstruction.

One fixed P154 role and private count/suffix slots only. Existing72 constructors,
full original parser/hash/schema, Source policy and worker body remain. No GO.
"""
import copy
import json
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native009_full73_transport_v1.py'
TEST='tools/p09/tests/test_native009_full73_transport_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
FIELD='legacy154_validation_failure_declaration'
MANIFEST=PREFIX+'successor-native009-full73-manifest001.v1.json'
CAPSULE=PREFIX+'successor-worker-capsule009.compact.v4.json'
HINT=PREFIX+'successor-worker-bootstrap009.v4.json'
INCOMPLETE_SCOPE_CODE=dict(path=PREFIX+'native009-full73-transport-code002.v1.json',bytes=79727,
    sha256='74fad026e406ba28506988b68fd74c71f754b970e3e0f4a7ff493ec27c309d7d')
CODE=dict(path=PREFIX+'legacy154-binding-code001.v1.json',bytes=77072,
    sha256='26ac4f6721fc19a8d555ee360026773a6c3130ecb3c93ff26d5eba6f95658d57')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
SOURCE_SNAPSHOT=dict(path='tools/p09/single_snapshot_source_guard_v1.py',bytes=4560,
    sha256='f3555f4395154be7c929e76eeb451226402b49cc54b0ab6da335ba94555eae43')
SOURCE_SNAPSHOT_CODE=dict(path=PREFIX+'preparation-single-snapshot-code001.v1.json',bytes=963,
    sha256='6b35c089e38f8fb3767e0231b9ec32681a66fa0f6a984184a38ff80b00713435')
PINS=[dict(path='tools/p09/native009_full72_transport_v1.py',bytes=15741,
    sha256='441a0c98198d0442552004d918d4f6516e1c67e38a9de3585cd8e5a84612080e'),
 dict(path='tools/p09/legacy154_binding_v1.py',bytes=18359,
    sha256='4f4244978eea24904c283bbb0cb86b3fac87bd7b4c25185ff1724db114e16681')]


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_FULL73_'+label)


def graph_path(attempt):
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_GRAPH_ATTEMPT')
    return PREFIX+f'successor-native009-full73-graph{attempt:03}.v1.json'


def closure_dependency(original,name,expected,replacement):
    require(type(original) is FunctionType and original.__name__=='reconstruct'
        and original.__code__.co_filename.replace('\\','/').endswith('native009_full72_transport_v1.py'),'EXACT_FULL72_OUTER_FUNCTION')
    slots=[i for i,n in enumerate(original.__code__.co_freevars) if n==name]
    require(len(slots)==1 and original.__closure__ is not None,'ONE_EXPLICIT_CLOSURE_DEPENDENCY')
    index=slots[0];before=original.__closure__
    require(before[index].cell_contents is expected,'SAME_ORIGINAL_INNER_RECONSTRUCTION')
    def cell(value):return (lambda:value).__closure__[0]
    revised=tuple(cell(replacement) if i==index else value for i,value in enumerate(before))
    fn=FunctionType(original.__code__,original.__globals__,name=original.__name__,argdefs=original.__defaults__,closure=revised)
    fn.__kwdefaults__=original.__kwdefaults__
    require(fn.__code__ is original.__code__ and fn.__defaults__ is original.__defaults__
        and all(fn.__closure__[i] is before[i] for i in range(len(before)) if i!=index)
        and before[index].cell_contents is expected,'ONLY_DECLARED_INNER_CLOSURE_CHANGED')
    undo=tuple(before[index] if i==index else value for i,value in enumerate(fn.__closure__))
    require(all(a is b for a,b in zip(undo,before)),'ENTIRE_ORIGINAL_CLOSURE_INVERSE')
    return fn,dict(dependency=name,closure_slot=index,only_one_declared_dependency_changed=True,
        entire_original_outer_code_defaults_globals_and_other_cells_retained=True,entire_closure_inverse=True)


def connect(root,loader,scope,bytes_policy,xz,bounded,checkpoint,exact):
    libs,proofs=loader.load(root,PINS,{})
    previous=libs.native009_full72_transport_v1;added=libs.legacy154_binding_v1;injected=[]
    def load(actual_root,pins,reuse):
        names,proof=loader.load(actual_root,pins,reuse)
        if pins==previous.PINS:
            require(not injected,'ONE_FULL72_DEPENDENCY_INJECTION');injected.append(True)
            legacy=names.legacy_validation_binding_v1
            def installed(module,prior70,admitted,codec,*,physical_run):
                before=legacy.install(module,prior70,admitted,codec,physical_run=physical_run)
                prior72=copy.deepcopy(prior70)+[dict(schema_version=module.source.SCHEMA,next_case=165,
                    semantic_original_pin=copy.deepcopy(r['original']),physical_envelope_pin=copy.deepcopy(r['physical'])) for r in legacy.RECORDS]
                extension=added.install(module,prior72,copy.deepcopy(added.ROLE),codec,physical_run=physical_run)
                return dict(before,legacy154_entire72_then_raw73_installed=extension)
            names=NS(**{**vars(names),'legacy_validation_binding_v1':NS(**{**vars(legacy),'install':installed})})
        return names,proof
    proxy=NS(**{**vars(loader),'load':load})
    api72=previous.connect(root,proxy,scope,bytes_policy,xz,bounded,checkpoint,exact)
    old=api72.runtime.validate_worker_hint
    suffix,suffix_proof=previous.constant(old,'.compact.v3.json','.compact.v4.json','validate_worker_hint','current_queue_successor_runtime.py')
    old.__globals__['validate_worker_hint']=suffix;api72.runtime.validate_worker_hint=suffix
    closure=dict(zip(api72.reconstruct.__code__.co_freevars,(c.cell_contents for c in api72.reconstruct.__closure__)))
    original_inner=closure['reconstruction']
    inner,inner_proof=previous.constant(original_inner,72,73,'reconstruct','native009_worker_transport_v1.py')
    outer,outer_proof=previous.constant(api72.reconstruct,72,73,'reconstruct','native009_full72_transport_v1.py')
    reconstruction,closure_proof=closure_dependency(outer,'reconstruction',original_inner,inner)
    build,engine_proof=previous.constant(api72.build,72,73,'build','native009_engine_connection_v1.py')
    def core_hint(hint):
        require(type(hint) is dict and FIELD in hint,'EXPLICIT_FIXED_P154_FAILURE_DECLARATION')
        exact(hint[FIELD],added.ROLE,'UNKNOWN_FAILED_P154_NOT_FALSE_OR_PASS')
        return {k:v for k,v in hint.items() if k!=FIELD}
    def validate(hint):return api72.validate(core_hint(hint))
    def factory(hint,prior68):return api72.factory(core_hint(hint),prior68)
    def reconstruct(hint,wire,check):
        checkpoint();core=core_hint(hint);api72.validate(core)
        graph,proof=reconstruction(core,wire,check)
        require(len(graph.binding.descriptors())==73,'ALL73_AFTER_WHOLE_ORIGINAL_RECONSTRUCTION')
        return graph,dict(proof,descriptor_count=73,full72_outer_and_original_raw_reconstruction_bodies_retained=True,
            count_slots_and_one_named_closure_dependency_have_inverses=True,actual_Native_or_product_qualified=False)
    require(injected==[True],'ACTUAL_FULL72_DEPENDENCY_INJECTED')
    return NS(runtime=api72.runtime,metadata=api72.metadata,factory=factory,validate=validate,reconstruct=reconstruct,build=build,
        roles=NS(**{**vars(api72.roles),'legacy154':copy.deepcopy(added.ROLE)}),source_proofs=proofs+api72.source_proofs,
        inner_count_proof=inner_proof,outer_count_proof=outer_proof,closure_proof=closure_proof,engine_proof=engine_proof,
        suffix_proof=suffix_proof,original_default_modules_mutated=False,old_api=api72,original_inner=original_inner,
        revised_inner=inner,original_outer=api72.reconstruct,revised_outer=reconstruction)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def denied_product(event,args):
        if event=='subprocess.Popen':denied.append(1);raise ValueError('TRANSPORT_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(denied_product)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    bootstrap,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=bootstrap.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,_=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);attempt=parser.parse_args().attempt
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_ATTEMPT')
    output=PREFIX+f'native009-full73-transport-code{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists() and not(c.ROOT/graph_path(attempt)).exists(),'EXCLUSIVE_REPORT_AND_GRAPH')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic();phase='ADMISSION';prepared=None
    row=dict(state='FAILED_NATIVE009_FULL73_TRANSPORT_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,
        actual_worker_product_or_Native_executed=False,current_full_source_Frame_or_dispatch_qualified=False,
        current_report_graph_and_later_worker_dispatch_results_must_be_recosted=True)
    encoded=lambda value:(json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode('ascii')
    try:
        guard.acquire();seed=a.AcceptanceReader(c.ROOT,guard.check)
        a.exact(seed.pin(SOURCE_SNAPSHOT['path']),SOURCE_SNAPSHOT,'FRESH_QUALIFIED_SOURCE_PREDICATE_COMPONENT')
        predicates,_=loader.load(c.ROOT,[SOURCE_SNAPSHOT],{'audit_evidence_io':original_io})
        snapshot=predicates.single_snapshot_source_guard_v1
        leaf_pin,leaf=seed._read(snapshot.ORIGINAL_PIN['path'],parse=True);seed._bind(leaf_pin['path'],leaf_pin)
        a.exact(leaf_pin,snapshot.ORIGINAL_PIN,'UNCHANGED_ORIGINAL_READER_LEAF')
        Reader,reader_proof=snapshot.reader_type(a.AcceptanceReader,bytes(leaf));del leaf
        q=Reader(c.ROOT,guard.check)
        for pin in seed.snapshots.values():a.exact(q.pin(pin['path']),pin,'REOPEN_ALL_PREDICATE_BOOTSTRAP_INPUTS')
        qualified=a.read_exact(q,SOURCE_SNAPSHOT_CODE)
        a.fields(qualified,dict(state='PASS_PREPARATION_SINGLE_SNAPSHOT_CODE10_NOT_NATIVE_OR_PRODUCT',
            contracts=dict(run=10,errors=0,failures=0,skipped=0),fresh_inputs=3,final_fresh_hashes=3,cleanup_confirmed=True),
            'ACTUAL_UNCHANGED_SINGLE_SNAPSHOT10')
        for pin in qualified['source_pins']:a.exact(q.pin(pin['path']),pin,'ALL_CURRENT_PREDICATE_QUALIFICATION_SOURCES')
        row['preparation_reader_proof']=reader_proof
        row['preparation_reader_qualification_pin']=SOURCE_SNAPSHOT_CODE
        for name in (SELF,TEST,'tools/p09/prepare_current_queue_step.py',PREFIX+'step-config001.v1.json'):q.pin(name)
        for pin in [CONSTRUCTION]+construction.PINS+PINS:a.exact(q.pin(pin['path']),pin,'CURRENT_EXACT_SOURCE_DEPENDENCIES')
        code=a.read_exact(q,CODE)
        a.fields(code,dict(state='PASS_LEGACY154_FULL73_BINDING10_AND_DECLARED_COST_NOT_WORKER_OR_NATIVE',
            contracts=dict(run=10,errors=0,failures=0,skipped=0),fresh_inputs=386,final_fresh_hashes=386,
            cleanup_confirmed=True,actual_engine_worker_calls=0,declared_cost_nominal_fits600=True),'CURRENT_BINDING73_CODE10')
        for pin in code['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'ALL_QUALIFIED_PROGRAMS')
        fixture=a.read_exact(q,code['code_manifest_pin']);rows=fixture['descriptors'];require(len(rows)==73,'ALL_REAL73_ROWS')
        old_decl=a.read_exact(q,code['declared_scope_base_pin'])
        scope_base=scope.extend(scope.pins(old_decl['input_pins']),{code['declared_scope_base_pin']['path']:code['declared_scope_base_pin']})
        inherited=scope.pins(list(scope_base.values()))
        inherited=scope.extend(inherited,scope.pins(code['source_pins']))
        # source_pins is the producer's freshly read subset, not its complete
        # inherited declaration. Reconstruct the same two explicitly referenced
        # proof declarations used by the original Binding CODE before adding
        # any new transport inputs. Never drop opaque preparation evidence.
        lineage=[code['prior_parent_connection_pin'],code['new_physical73_proof_pin']]
        for dependency in lineage:
            declaration=a.read_exact(q,dependency)
            inherited=scope.extend(inherited,scope.pins(declaration['source_pins']))
        retained=a.read_exact(q,INCOMPLETE_SCOPE_CODE)
        a.fields(retained,dict(state='PASS_NATIVE009_FULL73_ORIGINAL_RECONSTRUCTION14_AND_DECLARED_COST_NOT_WORKER_OR_NATIVE',
            contracts=dict(run=14,errors=0,failures=0,skipped=0),semantic_inputs=3211,cleanup_confirmed=True,
            actual_engine_worker_calls=0),'RETAIN_OLD_PACKET_TEST_NOT_COMPLETE_SCOPE_OR_COST_AUTHORITY')
        row['superseded_incomplete_scope_qualification_pin']=INCOMPLETE_SCOPE_CODE
        row['prior_incomplete_scope_cost_or_freshness_reused']=False
        old_hint=q.json(libs.native009_full72_transport_v1.HINT);old_manifest=a.read_exact(q,old_hint['manifest_pin'])
        step=old_hint['step'];authority=a.read_exact(q,step['prior_queue_pin'])
        a.fields(authority,dict(accepted_count_after=158,next_runtime_index=165,runtime_candidate_pin=step['prior_candidate_pin']),'ACTUAL_UNADVANCED_AUTHORITY')
        hint=copy.deepcopy(old_hint)
        # Use the same qualified slot utility for Source's full original verify.
        # The new transport's connect body is explicit; default modules stay.
        transport=NS(connect=connect,constant=libs.native009_full72_transport_v1.constant)
        phase='FRESH_VERIFIED_SOURCE_BEFORE73_FACTORY'
        fresh=libs.native009_verified_source_profile_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a,q,hint,transport)
        api=fresh.api
        manifest=dict(old_manifest,schema_version='hwpx-agent.p09-native009-full73-manifest/v1',descriptors=rows,
            legacy154_validation_failure_role=api.roles.legacy154,current_whole_Native_source_scope_qualified=False)
        adapters,_=loader.load(c.ROOT,[construction.DECLARATION],{})
        parent=adapters.native009_parent_scope_v1
        manifest_pin=parent.publish_bytes(c.ROOT,MANIFEST,encoded(manifest),q,guard,bytes_policy,a,262144)
        hint.update(manifest_pin=manifest_pin,**{FIELD:api.roles.legacy154})
        module=api.factory(dict(hint,capsule_pin=dict(path=CAPSULE,bytes=1,sha256='0'*64)),rows[:68])
        bound=module.Binding(rows,manifest_pin,next_case=165)
        graph,_=api.metadata.connect(c.ROOT,loader,bytes_policy,module,bound,step,9,guard.check)
        wire,_=graph.worker.encode(bound,step['prior_queue_pin'],step['prior_candidate_pin'],guard.check)
        hint['capsule_pin']=parent.publish_bytes(c.ROOT,CAPSULE,wire,q,guard,bytes_policy,a,16384)
        hint_pin=parent.publish_bytes(c.ROOT,HINT,encoded(hint),q,guard,bytes_policy,a,16384)
        phase='WHOLE_ORIGINAL73_RECONSTRUCTION'
        observed=dict(active=True,data_file_opens=0)
        def audit(event,args):
            if observed['active'] and event=='open' and args and isinstance(args[0],str) and args[0].lower().endswith('.json'):observed['data_file_opens']+=1
        sys.addaudithook(audit)
        try:rebuilt,proof=api.reconstruct(hint,wire,guard.check)
        finally:observed['active']=False
        a.exact(observed['data_file_opens'],0,'ORIGINAL_RECONSTRUCTION_NO_DATA_JSON_OPENS')
        a.exact(rebuilt.binding.descriptors(),rows,'ALL73_ORIGINAL_DECODE_NOT_PREPARSED_SUBSTITUTION')
        linked=api.build(c.ROOT,loader,api,rebuilt,envelope.prior,libs.post_product_recovery_connection_v1,libs.post_product_recovery_window_v1,guard.check)
        phase='EXACT_PREVIOUS_DECLARATION_RECONSTRUCTION'
        baseline=module.Binding(rows,code['code_manifest_pin'],next_case=165)
        inherited,_=baseline.semantic_union(inherited,guard.check)
        baseline_projection,_=baseline.project(inherited,guard.check)
        baseline_bytes=sum(p['bytes'] for p in baseline_projection.physical_pins.values())
        a.exact(len(inherited),code['semantic_inputs'],'ALL3207_PREVIOUS_DECLARED_INPUTS_RECONSTRUCTED')
        a.exact(baseline_bytes,code['physical_bytes'],'EXACT_PREVIOUS_PHYSICAL_BYTE_DECLARATION')
        row.update(inherited_previous_scope_exactly_reconstructed=True,inherited_previous_semantic_inputs=len(inherited),
            inherited_previous_physical_bytes=baseline_bytes,inherited_scope_dependency_pins=lineage)
        phase='CURRENT_TRANSPORT_CONTRACTS'
        spec=importlib.util.spec_from_file_location('native009_full73_transport_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.API=api;tests.HINT=hint;tests.WIRE=wire;tests.GRAPH=rebuilt;tests.ROWS=rows
        tests.CHECK=guard.check;tests.BOUNDED=libs.bounded_successor_capsule_wire_v2;tests.LINKED=linked;tests.OBSERVED=observed
        tests.BASIS=inherited;tests.PREVIOUS_CODE=code;tests.BASIS_BYTES=baseline_bytes
        tests.READER=q;tests.ORIGINAL_READER=a.AcceptanceReader
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=16,errors=0,failures=0,skipped=0),'ALL_TRANSPORT16_WITH_SCOPE_AND_READER_COMPOSITION')
        phase='CURRENT_DECLARED_COMPLETE_COST'
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        required=scope.extend(inherited,q.snapshots);required,_=rebuilt.binding.semantic_union(required,guard.check)
        require(all(required.get(n)==pin for n,pin in inherited.items() if n not in rebuilt.binding.reverse),'NO_OLD_DECLARED_INPUT_REMOVED')
        normalized_base,_=rebuilt.binding.semantic_union(scope_base,guard.check)
        delta=sorted((pin for n,pin in required.items() if n not in normalized_base),key=lambda p:p['path'])
        a.exact(scope.extend(normalized_base,scope.pins(delta)),required,'WHOLE_DECLARED_SCOPE_BASE_AND_COMPACT_DELTA_ROUNDTRIP')
        row['declared_scope_delta_pins']=delta
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced);require(len(rust)==787 and set(rust)<=set(required),'CURRENT_RUST787')
        budget=rebuilt.binding.runtime_budget(required,len(requests),linked.window.DIRECT.runtime_budget,guard.check);total=budget['predicted_runtime_combined_seconds']+15
        row.update(original_complete_runtime_budget=budget,predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600,
            semantic_inputs=len(required),current_Rust_path_count=len(rust),inventory_requests=len(requests),
            additional_readiness_seconds_without_old_credit=15,declared_scope_base_pin=code['declared_scope_base_pin'],
            actual_engine_worker_calls=linked.state.calls,manifest_pin=manifest_pin,capsule_pin=hint['capsule_pin'],bootstrap_pin=hint_pin)
        require(total<600,'COMPLETE_DECLARED_SCOPE_PLUS_READINESS_OUTSIDE600')
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True);require(not denied,'NO_SUBPROCESS_ATTEMPTS')
        row.update(state='PASS_NATIVE009_FULL73_ORIGINAL_RECONSTRUCTION16_AND_FULL_DECLARED_COST_NOT_WORKER_OR_NATIVE',descriptor_count=73,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            reconstruction_proof=proof,inner_count_proof=api.inner_count_proof,outer_count_proof=api.outer_count_proof,
            closure_proof=api.closure_proof,engine_count_proof=api.engine_proof,suffix_proof=api.suffix_proof,reconstruction_JSON_file_opens=0)
        row['metadata_source_predicate_optimization']=q.source_snapshot_diagnostics()
        prepared=dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',index=165,physical_run=9,step=step,
            manifest_pin=manifest_pin,capsule_pin=hint['capsule_pin'],bootstrap_pin=hint_pin,descriptors=73,accepted_count_delta=0,
            product_or_Native_executed=False,GO_authorized=False,actual_current_source_Frame_qualified=False,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,cleanup_confirmed=True)
        prepared.update(declared_scope_base_pin=code['declared_scope_base_pin'],declared_scope_delta_pins=delta,
            inherited_previous_scope_exactly_reconstructed=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP')
    if prepared is not None:row['graph_report_pin']=libs.successor_preparation_workspace_v1.publish(c.ROOT,graph_path(attempt),prepared,a)
    libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','descriptor_count','manifest_pin','capsule_pin','bootstrap_pin',
        'semantic_inputs','current_Rust_path_count','inventory_requests','predicted_complete_seconds_with_readiness','fresh_inputs','final_fresh_hashes',
        'actual_engine_worker_calls','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed',
        'operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
