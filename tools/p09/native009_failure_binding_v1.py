"""One exact post-body Native009 failure after the complete fixed161 table.

Preserve the original161 constructor and every nonconstructor scope/resource/
byte oracle. This is a data/codec connection, not a launcher or replay grant.
"""
import copy
import hashlib
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native009_failure_binding_v1.py'
TEST='tools/p09/tests/test_native009_failure_binding_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
ORIGINAL=dict(path=PREFIX+'current-runtime-run009.v1.json',bytes=5046802,
    sha256='3588e9d53ff9b442c711d165e8ad09fb93627bc0dc756a467a059f11a71ce753')
PHYSICAL=dict(path='implementation/p09/evidence/p361-lossless-runtime-inputs/case165-runtime-run009.failed.shared720.xz8m-g001.envelope.v1.json',
    bytes=315450,sha256='067b3776ae108b0c13949e3f81fba429a316c1a5f1cda8c11b3ff5f6f8ea6e8c')
PUBLICATION=dict(path=PREFIX+'native009-carrier-g001-attempt001.v1.json',bytes=9311,
    sha256='51dbbfd7aa709427d4cbb2192ce6841540325760cef6c129aa52d0330128fa60')
PRIOR_CODE=dict(path=PREFIX+'legacy-history-binding-code001.v1.json',bytes=80312,
    sha256='709a4107ebb9ebdaf2b5adf2f23de1f9958c213ad0c0010f2040a4e929e39fd6')
TABLE161='3b4d2d8a3dbad2e64dac988337df821d264878b55ee075a33dd515f69d5c4dad'
ROLE=dict(schema_version='hwpx-agent.p09-failed009-shared720-alias/v1',current_case=165,failed_physical_run=9,
    source_role='same_case_actual_body_PASS_final_source_shared720_failure_not_accepted_or_prebody',
    original_pin=ORIGINAL,physical_pin=PHYSICAL,physical_verification_pin=PUBLICATION,prior161_code_pin=PRIOR_CODE,
    actual_failed_product_child_executed=True,original_failure_promoted=False,original_failed_Native_qualified=False,
    current_product_or_GO_qualified=False,product_replay_authorized=False,parent_fresh_source_admission_required=True)


def require(ok,label):
    if not ok: raise ValueError('NATIVE009_FAILURE_BINDING_'+label)


def admission(q,a,loader):
    publication=a.read_exact(q,PUBLICATION); prior=a.read_exact(q,PRIOR_CODE)
    a.fields(publication,dict(state='PASS_NATIVE009_POST_BODY_SHARED720_FAILURE_CARRIER10_NOT_BINDING_OR_ACCEPTANCE',
        contracts=dict(run=10,errors=0,failures=0,skipped=0),fresh_inputs=27,final_fresh_hashes=27,physical_decode_boundaries=2,
        cleanup_confirmed=True,source_role=ROLE['source_role'],original_product_execution_true_preserved=True,
        failed_product_not_accepted=True,not_reclassified_as_prebody=True,Native009_replayed=False),'EXACT_FAILED009_PHYSICAL_PROOF')
    a.fields(prior,dict(state='PASS_FIXED161_BINDING18_AND_TWO_PHYSICAL_DECODE_PASSES_NOT_WORKER_OR_NATIVE',
        contracts=dict(run=18,errors=0,failures=0,skipped=0),descriptor_count=161,fresh_inputs=229,final_fresh_hashes=229,
        cleanup_confirmed=True,all_prior_semantic_pins_retained=True,Native009_replayed=False),'WHOLE_PRIOR161_BINDING')
    a.exact(publication['original_pin'],ORIGINAL,'EXACT_NATIVE009_ORIGINAL'); a.exact(publication['published_carrier_pin'],PHYSICAL,'EXACT_NATIVE009_PHYSICAL')
    for proof in (publication,prior):
        for pin in proof['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'): a.exact(q.pin(pin['path']),pin,'UNCHANGED_QUALIFIED_PROGRAMS')
    pins={p['path']:p for p in publication['source_pins']}; producer='tools/p09/prepare_native009_carrier_v1.py'
    modules,_=loader.load(q.root,[pins[producer]],{}); validator=modules.prepare_native009_carrier_v1
    native=a.read_exact(q,ORIGINAL); actual=validator.validate_projection(validator.projection(native))
    a.exact(actual,publication['reported_original_failure'],'BODY_PASS_CLOSING_FAILURE_AND_TRUE_EXECUTION_UNCHANGED')
    a.exact(q.pin(PHYSICAL['path']),PHYSICAL,'CURRENT_NEW_CARRIER_HASH')
    return copy.deepcopy(ROLE),prior,native


def install(module,prior_rows,role,xz):
    require(type(module) is NS and hasattr(module,'legacy_history_catalog') and not hasattr(module,'native009_failure_role'),'ONE_LAYER_AFTER_FIXED161')
    module.exact(role,ROLE,'EXACT_EXECUTED_BUT_FAILED009_ROLE')
    source=module.source; env=source.Projection.__init__.__globals__
    require(env.get('__name__','').startswith('p09_exact_') and env.get('descriptor') is source.descriptor
        and not any(getattr(m,'__dict__',None) is env for m in tuple(sys.modules.values()) if m),'PRIVATE_ORIGINAL_SOURCE_NAMESPACE')
    import json
    digest=hashlib.sha256(json.dumps(prior_rows,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(',',':')).encode('ascii')).hexdigest()
    require(type(prior_rows) is list and len(prior_rows)==161 and digest==TABLE161,'ENTIRE_FIXED161_NOT_SUBSET')
    old_init,raw_init=module.Binding.__init__,module.xz_original_initialize
    require(type(raw_init) is FunctionType and raw_init.__code__.co_filename.replace('\\','/').endswith('runtime_envelope_scope_binding_v1.py'),'WHOLE_RAW_ORIGINAL_CONSTRUCTOR')
    old_descriptor,old_codec,old_representation=source.descriptor,source.codec,module.Binding.representation
    methods={n:f for n,f in vars(module.Binding).items() if n not in ('__init__','representation')}
    projections=dict(vars(source.Projection)); prior=copy.deepcopy(prior_rows); provenance=copy.deepcopy(role)
    pair=dict(schema_version=source.SCHEMA,next_case=165,semantic_original_pin=dict(ORIGINAL),physical_envelope_pin=dict(PHYSICAL))
    complete=prior+[pair]; state=dict(ready=False,prior_constructor_calls=0,new_constructor_calls=0)
    def descriptor(old,new,*,next_case):
        if type(old) is not dict or old.get('path')!=ORIGINAL['path']: return old_descriptor(old,new,next_case=next_case)
        require(type(next_case) is int and next_case==165,'ONLY_FIXED_CASE165')
        module.exact(source.copy_pin(old),ORIGINAL,'EXACT_ORIGINAL_FAILURE_PIN')
        module.exact(source.copy_pin(new),PHYSICAL,'EXACT_NEW_PHYSICAL_PIN')
        return copy.deepcopy(pair)
    def initialize(self,rows,manifest_pin,*,next_case):
        state['ready']=False; module.exact(rows,complete,'ENTIRE161_PLUS_EXACT_FAILURE009')
        require(type(next_case) is int and next_case==165,'EXACT_TYPED_CASE')
        old_init(self,rows[:161],manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),prior,'ENTIRE_PRIOR161_CONSTRUCTOR_COMPLETED'); state['prior_constructor_calls']+=1
        raw_init(self,rows,manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),complete,'ENTIRE_RAW162_CONSTRUCTOR_COMPLETED'); state['new_constructor_calls']+=1; state['ready']=True
    def decode(raw,checkpoint):
        checkpoint()
        require(type(raw) is bytes and 0<len(raw)<=xz.MAX_BYTES,'FRESH_BOUNDED_CODEC_BYTES')
        if hashlib.sha256(raw).hexdigest()==PHYSICAL['sha256']:
            require(state['ready'],'ENTIRE162_BEFORE_NEW009_DECODE')
            return xz.decode(raw,checkpoint)
        return old_codec.decode(raw,checkpoint)
    def representation(self,projection):
        row=old_representation(self,projection); row['native009_post_body_shared720_failure_provenance']=copy.deepcopy(provenance)
        return row
    source.descriptor=env['descriptor']=descriptor; source.codec=env['codec']=NS(**{**vars(old_codec),'decode':decode})
    module.Binding.__init__,module.Binding.representation=initialize,representation; module.native009_failure_role=copy.deepcopy(provenance)
    require(all(vars(module.Binding).get(n) is f for n,f in methods.items()),'ALL_OTHER_BINDING_ORACLES_RETAINED')
    require(all(vars(source.Projection).get(n) is f for n,f in projections.items()),'ALL_ORIGINAL_PROJECTION_METHODS_RETAINED')
    return NS(state=state,methods=methods,projections=projections,old_constructor=old_init,
        old_representation=old_representation,rows=complete,pair=pair,product_replay_authorized=False)
