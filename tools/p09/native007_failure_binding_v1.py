"""Exact failed007 extension of the entire existing69 private Binding.

Original69 constructor runs first, followed by the whole unchanged raw70
constructor. No scope/byte/handle oracle or Projection method is replaced.
This CODE candidate is not a Native launcher or an approval for product replay.
"""
import copy
import hashlib
import json
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native007_failure_binding_v1.py'
TEST='tools/p09/tests/test_native007_failure_binding_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
ORIGINAL=dict(path=PREFIX+'current-runtime-run007.v1.json',bytes=4199057,
    sha256='3271eb9b07cd0eb1462630bb0f61e7ca7894545ec67f0c516ea8d898391a0f6c')
PHYSICAL=dict(path='implementation/p09/evidence/p361-lossless-runtime-inputs/'+
    'case165-runtime-run007.failed.final-source.xz8m-g001.envelope.v1.json',bytes=287658,
    sha256='176d807b620e24f69be9a98fb717ba493b8a3ef77526ac31172d5115dffacb11')
PUBLICATION=dict(path=PREFIX+'native007-carrier-g001-attempt001.v1.json',bytes=7268,
    sha256='c03c5547826db4d1e3a68fee18afc15c57c77c9fde503fdfef7d60929272217e')
FULL70=dict(path=PREFIX+'native007-full70-physical-attempt001.v1.json',bytes=44584,
    sha256='8289618d2b018dd72fcf5497fc168d85192a00e15f4ac4784efad3b21dce66e4')
TABLE69='4039352dd41eccebe54d658024953dc71c84aba8910e117a0cd5bbf4f7993d87'
ROLE=dict(schema_version='hwpx-agent.p09-failed007-alias-admission/v1',current_case=165,
    failed_physical_run=7,candidate_successor_physical_run=9,
    source_role='same_case_executed_product_final_input_failure_not_accepted',
    failed_runtime_pin=ORIGINAL,physical_pin=PHYSICAL,physical_verification_pin=FULL70,
    actual_failed_product_child_executed=True,original_failure_promoted=False,current_product_or_GO_qualified=False)


def require(ok,label):
    if not ok:raise ValueError('NATIVE007_FAILURE_BINDING_'+label)


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(',',':')).encode('ascii')).hexdigest()


def admission(q,a):
    proof=a.read_exact(q,FULL70);pub=a.read_exact(q,PUBLICATION)
    a.fields(proof,dict(state='PASS_FULL70_TWO_FRESH_PHYSICAL_BOUNDARIES_NOT_NATIVE_BINDING_OR_ACCEPTANCE',
        pair_count=70,decode_count=140,fresh_inputs=165,final_fresh_hashes=165,cleanup_confirmed=True,
        accepted_count_delta=0,GO_authorized=False,original_full69_mapping_or_descriptor_policy_changed=False),'FULL70_PROOF')
    a.fields(pub,dict(state='PASS_NATIVE007_LOSSLESS_TWO_FRESH_READS_NOT_FULL70_OR_RUNTIME_BINDING',
        contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True),'NATIVE007_PUBLICATION')
    for obj,old,new in ((proof,'new_failed_semantic_pin','new_failed_physical_pin'),(pub,'original_pin','published_carrier_pin')):
        a.exact(obj[old],ORIGINAL,'EXACT_ORIGINAL');a.exact(obj[new],PHYSICAL,'EXACT_CARRIER')
    budget=proof['decoder_budget']
    a.fields(budget,dict(aggregate_limit_seconds=5.0,attempted_decodes=140,completed_decodes=140,
        active_decode=False,terminal_error_seen=False,two_boundaries_share_one_budget=True),'ORIGINAL_DECODER5')
    require(type(budget['elapsed_decoder_work_seconds']) is float and 0<=budget['elapsed_decoder_work_seconds']<5,'ACTUAL_FULL70_INSIDE5')
    for obj in (proof,pub):
        for pin in obj['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']),pin,'CURRENT_PHYSICAL_PROOF_PROGRAMS')
    a.exact(q.pin(PHYSICAL['path']),PHYSICAL,'CURRENT_CARRIER_PIN')
    return copy.deepcopy(ROLE)


def install(module,prior_rows,admitted,xz,*,physical_run):
    require(type(physical_run) is int and physical_run==9,'EXACT_NEW_RUN9')
    require(type(module) is NS and type(getattr(module,'source',None)) is NS,'PRIVATE_BINDING_MODULE')
    module.exact(admitted,ROLE,'EXACT_TYPED_EXECUTED_BUT_FAILED007')
    require(type(prior_rows) is list and len(prior_rows)==69 and fingerprint(prior_rows)==TABLE69,'ENTIRE_FIXED_PRIOR69')
    require(hasattr(module,'native008_failure_alias') and not hasattr(module,'native007_failure_alias'),'ONE_EXTENSION_AFTER008')
    source=module.source;env=source.Projection.__init__.__globals__
    require(env.get('__name__','').startswith('p09_exact_') and env.get('descriptor') is source.descriptor
        and not any(getattr(m,'__dict__',None) is env for m in tuple(sys.modules.values()) if m),'PRIVATE_GRAPH_NOT_DEFAULT')
    original=module.Binding.__init__;raw=module.xz_original_initialize
    require(type(raw) is FunctionType and raw.__code__.co_filename.replace('\\','/').endswith('runtime_envelope_scope_binding_v1.py'),'WHOLE_RAW_CONSTRUCTOR')
    descriptor_before=source.descriptor;codec_before=source.codec;representation_before=module.Binding.representation
    methods={k:v for k,v in vars(module.Binding).items() if k not in ('__init__','representation')}
    projection_methods=dict(vars(source.Projection));prior=copy.deepcopy(prior_rows);provenance=copy.deepcopy(admitted)
    pair=dict(schema_version=source.SCHEMA,next_case=165,semantic_original_pin=dict(ORIGINAL),physical_envelope_pin=dict(PHYSICAL))
    complete=prior+[pair];state=dict(ready=False)
    def descriptor(old,new,*,next_case):
        if type(old) is not dict or old.get('path')!=ORIGINAL['path']:return descriptor_before(old,new,next_case=next_case)
        require(type(next_case) is int and next_case==165,'EXACT_CASE165')
        module.exact(source.copy_pin(old),ORIGINAL,'EXACT_FAILED007_ORIGINAL')
        module.exact(source.copy_pin(new),PHYSICAL,'EXACT_FAILED007_PHYSICAL');return copy.deepcopy(pair)
    def initialize(self,rows,manifest_pin,*,next_case):
        state['ready']=False;module.exact(rows,complete,'ENTIRE69_PLUS_EXACT007')
        require(type(next_case) is int and next_case==165,'EXACT_FULL70_CASE')
        original(self,rows[:69],manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),prior,'ORIGINAL69_CONSTRUCTOR_COMPLETED')
        raw(self,rows,manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),complete,'WHOLE_RAW_CONSTRUCTOR70_COMPLETED');state['ready']=True
    def decode(encoded,checkpoint):
        checkpoint();require(type(encoded) is bytes and 0<len(encoded)<=xz.MAX_BYTES,'FRESH_BOUNDED_CODEC_BYTES')
        if hashlib.sha256(encoded).hexdigest()==PHYSICAL['sha256']:
            require(state['ready'],'FULL70_CONSTRUCTOR_BEFORE007_DECODE');return xz.decode(encoded,checkpoint)
        return codec_before.decode(encoded,checkpoint)
    def representation(self,projection):
        require(ORIGINAL['path'] in self.originals,'EXPLICIT_FAILED007_REQUIRED')
        row=representation_before(self,projection);row['same_case_failed165_run007_provenance']=copy.deepcopy(provenance);return row
    source.descriptor=descriptor;env['descriptor']=descriptor
    source.codec=NS(**{**vars(codec_before),'decode':decode});env['codec']=source.codec
    module.Binding.__init__=initialize;module.Binding.representation=representation;module.native007_failure_alias=copy.deepcopy(provenance)
    require(all(vars(module.Binding).get(k) is v for k,v in methods.items()),'ALL_NONCONSTRUCTOR_ORACLES_RETAINED')
    require(all(vars(source.Projection).get(k) is v for k,v in projection_methods.items()),'ALL_PROJECTION_METHODS_RETAINED')
    return dict(entire_original69_before_whole_raw70=True,original_nonconstructor_and_Projection_methods_retained=True,
        failed007_execution_true_and_failed008_execution_unknown_preserved=True,Native_or_GO_authorized=False)


def main():
    import argparse,importlib.util,io,re,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import flat_current_queue_envelope_runtime_v25 as envelope
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import receipt_xz_envelope_v1 as xz
    import bounded_successor_capsule_wire_v2 as bounded
    import ast_clone_namespace_v1 as cloner
    import ast_copy_namespace_connection_v1 as optimization
    import native009_worker_transport_v1 as transport
    import native009_parent_scope_v1 as parent
    import prepare_native007_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt)
    output=PREFIX+f'native007-binding-code{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_CODE_REPORT')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic()
    row=dict(state='FAILED_NATIVE007_BINDING_CODE_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,
        product_or_Native_executed=False,full70_worker_transport_or_current_Native_scope_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF);q.pin(TEST)
        admitted=admission(q,a)
        loader,_=optimization.connect(envelope.namespace_bundle,cloner)
        api=transport.connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a.exact);parent.version2(api,transport)
        hint=q.json(parent.BOOTSTRAP)
        capsule,data=q._read(hint['capsule_pin']['path'],parse=True);q._bind(capsule['path'],capsule)
        a.exact(capsule,hint['capsule_pin'],'SAME_FULL69_WIRE')
        graph,_=api.reconstruct(hint,bytes(data),guard.check);del data
        module=graph.binding_module;prior=graph.binding.descriptors();require(fingerprint(prior)==TABLE69,'REAL_COMPLETE69_RECONSTRUCTION')
        methods={k:v for k,v in vars(module.Binding).items() if k not in ('__init__','representation')};projection=dict(vars(module.source.Projection))
        row['installation_proof']=install(module,prior,admitted,xz,physical_run=9)
        rows=copy.deepcopy(prior)+[dict(schema_version=module.source.SCHEMA,next_case=165,semantic_original_pin=dict(ORIGINAL),physical_envelope_pin=dict(PHYSICAL))]
        name=PREFIX+f'native007-binding-code-manifest{attempt:03}.v1.json'
        manifest=dict(schema_version='hwpx-agent.p09-full70-binding-code-fixture/v1',descriptors=rows,
            Native_graph_or_worker_packet_qualified=False)
        pin=parent.publish_bytes(c.ROOT,name,(json.dumps(manifest,ensure_ascii=True,indent=2)+'\n').encode('ascii'),q,guard,bytes_policy,a,262144)
        actual,encoded=q._read(PHYSICAL['path'],parse=True);a.exact(actual,PHYSICAL,'ACTUAL_CARRIER_FOR_CODE_TEST')
        # Check the unconstructed private graph here, not through test ordering.
        try:module.source.codec.decode(bytes(encoded),guard.check)
        except ValueError as error:require(error.args==('NATIVE007_FAILURE_BINDING_FULL70_CONSTRUCTOR_BEFORE007_DECODE',),'EXACT_UNCONSTRUCTED_DENIAL')
        else:require(False,'UNCONSTRUCTED_DECODE_DENIED')
        spec=importlib.util.spec_from_file_location('native007_binding_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.BINDING=module;tests.ROWS=rows;tests.PIN=pin;tests.SCOPE=scope
        tests.CHECK=guard.check;tests.CARRIER=bytes(encoded);tests.METHODS=methods;tests.PROJECTION=projection;tests.PRIOR=prior;tests.XZ=xz
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=9,errors=0,failures=0,skipped=0),'ALL_BINDING9')
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE007_FULL70_BINDING_CODE9_NOT_WORKER_OR_NATIVE',manifest_pin=pin,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            one_private_module_reused_for_contracts_not_reloaded_per_assertion=True,prior_complete69_table_unchanged=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP');publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','fresh_inputs','final_fresh_hashes',
        'elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','error_type','error_code')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
