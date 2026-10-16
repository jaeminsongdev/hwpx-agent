"""Measure the actual original worker encoder with the whole fixed162 table.

No engine, entry prepare, reconstruction or GO is called. Oversized wire stays
rejected; an independent byte count is diagnostic only, never a bypass packet.
The full inherited semantic declaration, not the small read subset, is recosted.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/probe_fixed162_packet_v1.py'
TEST='tools/p09/tests/test_probe_fixed162_packet_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
BUILDER=dict(path='tools/p09/qualify_native009_failure_binding_v1.py',bytes=15143,
    sha256='2643f3b0966ed170c74435fa6f69ecaf26547805bbe42fbdce45ee9e35ccf038')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
MANIFEST=dict(path=PREFIX+'native009-failure-binding-manifest001.v1.json',bytes=117065,
    sha256='4af8d451da3bd31925423b26754bfa2a0e4eba3848479eb1af1d33ed3880cc89')
PROFILE=dict(path=PREFIX+'fixed162-decoder-profile001.v1.json',bytes=170886,
    sha256='9a4c92483776eb0a504f99c000de326d89317783148b4d7fced1da7d2d201965')
TRIAL=dict(path=PREFIX+'fixed162-dictionary-trial001.v1.json',bytes=15032,
    sha256='fd1e9384303ee74988eae3a1567a36c724c207ab4690a21ffbf6917e78081c95')


def require(ok,label):
    if not ok: raise ValueError('FIXED162_PACKET_'+label)


def observe_encode(worker,bound,step,checkpoint):
    fn=worker.encode
    require(type(fn) is FunctionType and fn.__globals__.get('__name__','').startswith('p09_exact_'),'PRIVATE_ORIGINAL_ENCODER')
    env=fn.__globals__; original=env['json']; rows=[]
    class Spy:
        @staticmethod
        def dumps(row,**options):
            require(not rows,'ONE_ORIGINAL_ENCODE_ATTEMPT'); rows.append(copy.deepcopy(row))
            return original.dumps(row,**options)
    env['json']=Spy; data=proof=None; error=None
    try: data,proof=fn(bound,step['prior_queue_pin'],step['prior_candidate_pin'],checkpoint)
    except ValueError as caught:
        require(caught.args==('SUCCESSOR_WIRE_V2_ORIGINAL_16K_TRANSPORT',),'ONLY_REAL_WIRE_SIZE_DENIAL_EXPECTED')
        error=caught.args[0]
    finally: env['json']=original
    require(env['json'] is original and len(rows)==1,'RESTORED_WHOLE_ENCODER_DEPENDENCY')
    closure=dict(zip(original.dumps.__code__.co_freevars,(cell.cell_contents for cell in original.dumps.__closure__ or ())))
    pack=closure.get('pack'); require(type(pack) is FunctionType,'ORIGINAL_CURRENT_COMPACT_PACK')
    return NS(data=data,proof=proof,error=error,semantic=rows[0],compact=pack(rows[0]),original_json_restored=True)


def diagnostic_wire_count(compact,checkpoint):
    # Exactly the v2 representation, with no permission to return or publish
    # an oversized packet. The original encoder above remains authoritative.
    import base64,zlib
    checkpoint()
    raw=json.dumps(compact,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')
    require(0<len(raw)<=131072,'ORIGINAL_EXPANDED128K')
    compressed=zlib.compress(raw,9)
    outer=dict(schema_version='hwpx-agent.p09-bounded-compressed-worker-capsule/v2',raw_bytes=len(raw),
        raw_sha256=hashlib.sha256(raw).hexdigest(),zlib_base64=base64.b64encode(compressed).decode('ascii'))
    size=len(json.dumps(outer,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii'))
    checkpoint(); return dict(expanded_bytes=len(raw),compressed_bytes=len(compressed),wire_bytes=size,
        wire_limit_bytes=16384,expanded_limit_bytes=131072,fits_wire=size<=16384)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows(); denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('FIXED162_PACKET_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    original,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=original.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,_=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser(); parser.add_argument('--attempt',type=int,required=True)
    attempt=parser.parse_args().attempt; require(type(attempt) is int and 1<=attempt<=8,'FINITE_ATTEMPT')
    output=PREFIX+f'fixed162-packet-probe{attempt:03}.v1.json'; require(not(c.ROOT/output).exists(),'EXCLUSIVE_REPORT')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic(); q=None; phase='ADMISSION'
    row=dict(state='FAILED_FIXED162_PACKET_PROBE_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,
        Native009_replayed=False,actual_worker_engine_Job_Frame_or_Native_executed=False,
        full_current_runtime_scope_or_helper_bound_qualified=False,actual_metadata_Frame_shared_decoder5_qualified=False,
        worker_reconstruction_or_dispatch_qualified=False,source_inputs_excluded=0,original_limits_changed=False)
    try:
        guard.acquire(); q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,TEST): q.pin(path)
        profile=a.read_exact(q,PROFILE); trial=a.read_exact(q,TRIAL)
        a.fields(profile,dict(state='PROFILE_FULL162_COMPLETED_NOT_RUNTIME_QUALIFICATION',all324_completed=True,
            fresh_inputs=239,final_fresh_hashes=239,cleanup_confirmed=True),'COMPLETE_PROFILE_NOT_ADMISSION')
        a.fields(trial,dict(state='PASS_FOUR_DICTIONARY_REPRESENTATIVES8_NOT_WHOLE_CORPUS_OR_RUNTIME',
            representative_count=4,fresh_inputs=35,final_fresh_hashes=35,cleanup_confirmed=True),'BOUNDED_DICTIONARY_COMPARISON')
        for evidence in (profile,trial):
            for pin in evidence['source_pins']:
                if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'): a.exact(q.pin(pin['path']),pin,'CURRENT_DIAGNOSTIC_PROGRAMS')
        a.exact(q.pin(BUILDER['path']),BUILDER,'PRESERVED_FAILED_BUILDER_BODY')
        namespaces,_=loader.load(c.ROOT,[BUILDER],{}); builder=namespaces.qualify_native009_failure_binding_v1
        value=builder.build(c,a,q,loader,libs,construction,scope,bytes_policy,envelope)
        a.exact(q.pin(MANIFEST['path']),MANIFEST,'WHOLE_FIXED162_MANIFEST')
        bound=value.module.Binding(value.proof.rows,MANIFEST,next_case=165)
        entry_name='tools/p09/native009_full75_worker_entry_v1.py'
        entry_pin=q.snapshots[entry_name]; entries,_=loader.load(c.ROOT,[entry_pin],{}); entry=entries.native009_full75_worker_entry_v1
        transports,_=loader.load(c.ROOT,[entry.TRANSPORT],{})
        api=transports.native009_full75_transport_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a.exact)
        hint=a.read_exact(q,entry.HINT); step=hint['step']
        phase='ORIGINAL_WORKER_ENCODER_WITH_ALL162'
        graph,_=api.metadata.connect(c.ROOT,loader,bytes_policy,value.module,bound,step,9,guard.check)
        packet=observe_encode(graph.worker,bound,step,guard.check)
        a.exact(packet.semantic['descriptors'],value.proof.rows,'EVERY162_ROW_REACHES_ORIGINAL_ENCODER')
        counts=diagnostic_wire_count(packet.compact,guard.check)
        if packet.data is not None: a.exact(len(packet.data),counts['wire_bytes'],'DIAGNOSTIC_COUNT_EQUALS_ACTUAL_ENCODER')
        else: require(not counts['fits_wire'],'ORIGINAL_SIZE_DENIAL_PRESERVED')
        future_hint=dict(copy.deepcopy(hint),legacy_history_physical_evidence_provenance=value.catalog.declaration(),
            native009_post_body_shared720_failure_provenance=value.role)
        bootstrap_bytes=len((json.dumps(future_hint,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode('ascii'))
        spec=importlib.util.spec_from_file_location('fixed162_packet_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests); tests.M=sys.modules[__name__]
        tests.BOUNDED=libs.bounded_successor_capsule_wire_v2; tests.ACTUAL=packet; tests.COUNTS=counts
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=6,errors=0,failures=0,skipped=0),'PACKET_SIX_CONTRACTS')
        phase='FULL_DECLARATION_AND_ORIGINAL600_720_COST'
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced(): requests.append(1); q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced); require(len(rust)==787,'CURRENT_RUST787')
        model_name='tools/p09/whole_runtime_metadata_budget_v1.py'; model_pin=q.pin(model_name)
        models,_=loader.load(c.ROOT,[model_pin],{})
        required,_=bound.semantic_union(scope.extend(value.prior_scope,q.snapshots),guard.check)
        require(all(required.get(n)==p for n,p in value.prior_scope.items()) and set(rust)<=set(required),'ALL_PRIOR3280_AND_RUST_RETAINED')
        cost=bound.runtime_budget(required,len(requests),value.window.DIRECT.runtime_budget,guard.check)
        row.update(descriptor_count=162,original_encoder_error=packet.error,wire_counts=counts,
            diagnostic_naive_bootstrap_bytes=bootstrap_bytes,bootstrap_limit_bytes=16384,
            naive_full_role_bootstrap_fits=bootstrap_bytes<=16384,
            oversized_packet_published=False,original_encoder_dependency_restored=True,
            inherited_semantic_inputs=len(value.prior_scope),declared_semantic_inputs=len(required),
            all_prior_semantic_pins_retained=True,complete_prototype_runtime_budget=cost,
            whole720_necessary_model=models.whole_runtime_metadata_budget_v1.assess(cost),
            inventory_requests=len(requests),current_Rust_path_count=len(rust),
            profile_pin=PROFILE,dictionary_trial_pin=TRIAL,manifest_pin=MANIFEST,
            actual_separate162_qualification_still_failed=True,current_result_and_future_sources_must_be_recosted=True)
        phase='FINAL_FRESH_HASHES'; q.finish(); guard.check(force=True)
        row.update(state='PASS_ORIGINAL_FIXED162_PACKET_SIZE_AND_FULL_COST_DIAGNOSTIC6_NOT_TRANSPORT_QUALIFICATION',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-7:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]): row['error_code']=error.args[0]
    finally:
        if q is not None: row.update(observed_inputs=len(q.snapshots),closing_hashes_completed=q.final_fresh_hashes)
        guard.close(); row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'PROBE_OWNER_CLEANUP'); libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','wire_counts','diagnostic_naive_bootstrap_bytes',
        'declared_semantic_inputs','whole720_necessary_model','fresh_inputs','final_fresh_hashes','elapsed_seconds',
        'CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__': raise SystemExit(main())
