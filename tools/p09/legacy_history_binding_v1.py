"""Fixed 86 historical evidence aliases and seven already-admitted repacks.

No generic metadata rule is relaxed. Parent admission reads the fixed physical
proofs and current carrier hashes; worker declarations only reconstruct the
same sealed table. Original75 constructor runs first, then the whole raw161
constructor. Projection and all scope/byte/resource oracles remain original.
"""
import copy
import hashlib
import json
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/legacy_history_binding_v1.py'
TEST='tools/p09/tests/test_legacy_history_binding_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
HISTORY=dict(path=PREFIX+'legacy-history-physical-trial-g001-attempt001.v1.json',bytes=238781,
    sha256='a92f937bbfc518541d4800b88d4e0b6ada4ab7c0e09df9e7c278928040861f6e')
REPACK=dict(path=PREFIX+'legacy-zlib75-repack-g001-attempt001.v1.json',bytes=31751,
    sha256='b0796b374d181988ef8e0b0b321c5f4e8a3fdb65427b36b1f4cc93a93d15dc7f')
NATIVE=dict(path=PREFIX+'current-runtime-run009.v1.json',bytes=5046802,
    sha256='3588e9d53ff9b442c711d165e8ad09fb93627bc0dc756a467a059f11a71ce753')
MANIFEST=dict(path=PREFIX+'successor-native009-full75-manifest001.v1.json',bytes=57692,
    sha256='f19fb5603bc416d614d485995fbf71fa06da148b5204fcdc8b03f1511b91d615')
CATALOG_SHA='c990b33bbcd75537ca1a907cdc7dea4e00ae0b96108f2a9c7f3586d6879de1ba'
PRIOR_SHA='043408c4decc85b714c793566c6a456be93dd3cbd49f519debc89b638831f2c3'
COMPLETE_SHA='3b4d2d8a3dbad2e64dac988337df821d264878b55ee075a33dd515f69d5c4dad'
DECLARATION_SHA='e5a94983bdb7af7a93dc2231f6b70347e7d36c03eabf20b2b8c1f88cb706086a'
_PARENT_TOKEN=object()


def require(ok,label):
    if not ok: raise ValueError('LEGACY_HISTORY_BINDING_'+label)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(',',':')).encode('ascii')).hexdigest()


class Catalog:
    __slots__=('_rows','_prior','_declaration','_parent_source_token')
    def __init__(self,rows,declaration,*,_token=None):
        require(type(rows) is list and len(rows)==161 and fingerprint(rows)==COMPLETE_SHA,'EXACT_FIXED161_NOT_GENERIC_TABLE')
        require(type(declaration) is dict and fingerprint(declaration)==DECLARATION_SHA,'EXACT_UNPROMOTED_ROLE_DECLARATION')
        old={r['semantic_original_pin']['path']:r for r in declaration['old_seven_descriptors']}
        require(len(old)==7,'SEVEN_OLD_REPRESENTATIONS_ONLY')
        prior=[copy.deepcopy(old.get(r['semantic_original_pin']['path'],r)) for r in rows[:75]]
        require(fingerprint(prior)==PRIOR_SHA,'ENTIRE_PRIOR75_RECONSTRUCTED')
        self._rows=copy.deepcopy(rows); self._prior=prior; self._declaration=copy.deepcopy(declaration)
        self._parent_source_token=_token
    @property
    def parent_source_admitted(self): return self._parent_source_token is _PARENT_TOKEN
    def rows(self): return copy.deepcopy(self._rows)
    def prior(self): return copy.deepcopy(self._prior)
    def declaration(self): return copy.deepcopy(self._declaration)


def evidence_catalog(prior,history_rows,repack_rows,*,_token=None):
    history=[{k:r[k] for k in ('original','physical','reported_original_fields')} for r in history_rows]
    repacked=[{k:r[k] for k in ('original','old_physical','physical','reported_original_fields')} for r in repack_rows]
    body=dict(prior75_descriptors=prior,history86=history,repacked7=repacked)
    require(len(prior)==75 and len(history)==86 and len(repacked)==7 and fingerprint(body)==CATALOG_SHA,
        'FIXED_ORIGINAL_STATES_ABSENT_NULL_FALSE_TRUE_AND_ALL_PINS')
    changed={r['original']['path']:r['physical'] for r in repacked}
    rows=[dict(r,physical_envelope_pin=copy.deepcopy(changed.get(r['semantic_original_pin']['path'],r['physical_envelope_pin']))) for r in prior]
    rows.extend(dict(schema_version=prior[0]['schema_version'],next_case=165,
        semantic_original_pin=copy.deepcopy(r['original']),physical_envelope_pin=copy.deepcopy(r['physical'])) for r in history)
    old={r['semantic_original_pin']['path']:r for r in prior}
    declaration=dict(schema_version='hwpx-agent.p09-fixed-legacy-history-carriers/v1',current_case=165,
        source_trial_pins=[HISTORY,REPACK],source_native_pin=NATIVE,prior_manifest_pin=MANIFEST,
        catalog_sha256=CATALOG_SHA,prior75_sha256=PRIOR_SHA,complete161_sha256=COMPLETE_SHA,
        old_seven_descriptors=[copy.deepcopy(old[r['original']['path']]) for r in repacked],
        original_missing_fields_not_defaulted=True,failures_or_scoped_PASS_not_current_acceptance=True,
        product_execution_authorized=False)
    return Catalog(rows,declaration,_token=_token)


def admit(q,a):
    history=a.read_exact(q,HISTORY); repack=a.read_exact(q,REPACK); manifest=a.read_exact(q,MANIFEST)
    a.fields(history,dict(state='PASS_LEGACY86_OPAQUE_PHYSICAL_TRIAL8_NOT_RUNTIME_ALIAS_OR_SHARED_NATIVE_DECODER',
        contracts=dict(run=8,errors=0,failures=0,skipped=0),candidate_count=86,fresh_inputs=199,final_fresh_hashes=199,
        cleanup_confirmed=True,original_overwritten_or_deleted=False,generic_metadata_aliases_installed=False), 'FIXED86_BYTE_PROOF_NOT_GATE')
    a.fields(repack,dict(state='PASS_SEVEN_ALREADY_ALIASED_RECEIPTS_REPACK6_NOT_CURRENT_BINDING_OR_NATIVE',
        contracts=dict(run=6,errors=0,failures=0,skipped=0),fresh_inputs=49,final_fresh_hashes=49,
        cleanup_confirmed=True,original_or_old_carrier_overwritten_or_deleted=False,current75_descriptor_policy_changed=False), 'FIXED_SEVEN_BYTE_PROOF_NOT_GATE')
    for proof in (history,repack):
        for p in proof['source_pins']:
            if p['path'].startswith('tools/p09/') and p['path'].endswith('.py'): a.exact(q.pin(p['path']),p,'UNCHANGED_PHYSICAL_PROOF_PROGRAMS')
    catalog=evidence_catalog(manifest['descriptors'],history['records'],repack['records'],_token=_PARENT_TOKEN)
    native=a.read_exact(q,NATIVE)
    a.fields(native,dict(state='STOPPED_NOT_ACCEPTED',stop_reason='FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE',
        product_body_observed=True,actual_product_child_executed=True,Native_source_frame_qualified=False,
        cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),'NATIVE009_FAILURE_NOT_CURRENT_PRODUCT')
    physical={p['path']:p for p in native['source_freeze']}
    for r in history['records']: a.exact(physical.get(r['original']['path']),r['original'],'EVERY_HISTORY_ORIGINAL_IN_FIXED_NATIVE_SCOPE')
    a.exact(native['source_input_representation']['descriptors'],catalog.prior(),'ENTIRE_EXISTING75_FROM_REAL_NATIVE')
    for r in history['records']+repack['records']:
        a.exact(q.pin(r['physical']['path']),r['physical'],'CURRENT_FRESH_ENCODED_SOURCE_HASH')
    return catalog,history,repack,native


def from_transport(rows,declaration):
    # A correct declaration is not parent source admission or a GO permission.
    return Catalog(rows,declaration)


def install(module,catalog,xz,*,mode):
    require(type(catalog) is Catalog and mode in ('parent','worker'),'EXACT_CATALOG_AND_MODE')
    require(mode!='parent' or catalog.parent_source_admitted,'PARENT_SOURCE_ADMISSION_REQUIRED')
    require(type(module) is NS and not hasattr(module,'legacy_history_catalog'),'ONE_PRIVATE_CATALOG_LAYER')
    source=module.source; env=source.Projection.__init__.__globals__
    require(env.get('__name__','').startswith('p09_exact_') and env.get('descriptor') is source.descriptor
        and not any(getattr(m,'__dict__',None) is env for m in tuple(sys.modules.values()) if m),'PRIVATE_ORIGINAL_PROJECTION_ONLY')
    complete,prior,declaration=catalog.rows(),catalog.prior(),catalog.declaration()
    require(fingerprint(complete)==COMPLETE_SHA and fingerprint(prior)==PRIOR_SHA and fingerprint(declaration)==DECLARATION_SHA,'SEALED_TABLES_NOT_MUTABLE_INPUTS')
    old_init,raw_init=module.Binding.__init__,module.xz_original_initialize
    require(type(raw_init) is FunctionType and raw_init.__code__.co_filename.replace('\\','/').endswith('runtime_envelope_scope_binding_v1.py'),'ENTIRE_RAW_ORIGINAL_CONSTRUCTOR')
    old_descriptor,old_codec=source.descriptor,source.codec
    old_representation,old_union=module.Binding.representation,module.Binding.semantic_union
    methods={n:f for n,f in vars(module.Binding).items() if n not in ('__init__','representation','semantic_union')}
    projections=dict(vars(source.Projection))
    prior_by_name={r['semantic_original_pin']['path']:r for r in prior}
    special={r['semantic_original_pin']['path']:r for r in complete
        if r['semantic_original_pin']['path'] not in prior_by_name or r!=prior_by_name[r['semantic_original_pin']['path']]}
    require(len(special)==93,'EXACT86_PLUS_SEVEN_REPACKS')
    old_aliases={r['physical_envelope_pin']['path']:r for r in declaration['old_seven_descriptors']}
    hashes={r['physical_envelope_pin']['sha256'] for r in special.values()}
    state=dict(ready=False,validating_prior=False,prior_constructor_calls=0,new_constructor_calls=0)
    def descriptor(old,new,*,next_case):
        if state['validating_prior'] or type(old) is not dict or old.get('path') not in special:
            return old_descriptor(old,new,next_case=next_case)
        require(type(next_case) is int and next_case==165,'ONLY_FIXED_CASE165')
        expected=special[old['path']]
        module.exact(source.copy_pin(old),expected['semantic_original_pin'],'EXACT_FIXED_HISTORY_ORIGINAL')
        module.exact(source.copy_pin(new),expected['physical_envelope_pin'],'EXACT_FIXED_HISTORY_PHYSICAL')
        return copy.deepcopy(expected)
    def initialize(self,rows,manifest_pin,*,next_case):
        state['ready']=False
        module.exact(rows,complete,'COMPLETE_FIXED161_ONLY')
        require(type(next_case) is int and next_case==165,'TYPED_CURRENT_CONTEXT')
        state['validating_prior']=True
        try:
            old_init(self,copy.deepcopy(prior),manifest_pin,next_case=next_case)
            module.exact(self.descriptors(),prior,'WHOLE_ORIGINAL75_CONSTRUCTION_COMPLETED')
            state['prior_constructor_calls']+=1
        finally: state['validating_prior']=False
        raw_init(self,rows,manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),complete,'WHOLE_RAW_ORIGINAL161_COMPLETED')
        state['new_constructor_calls']+=1; state['ready']=True
    def semantic_union(self,rows,checkpoint):
        require(type(rows) is dict,'COMPLETE_MAPPING_KEYS_REQUIRED')
        verified=source.scope.pins(list(rows.values()))
        module.exact(verified,rows,'ORIGINAL_MAPPING_KEY_IDENTITY')
        normalized={}
        for name,p in verified.items():
            checkpoint()
            if name in old_aliases:
                expected=old_aliases[name]
                module.exact(p,expected['physical_envelope_pin'],'OLD_PHYSICAL_ALIAS_EXACT_HASH_NOT_PATH_ONLY')
                p=dict(expected['semantic_original_pin']); name=p['path']
            require(name not in normalized or normalized[name]==p,'NO_CONFLICT_DURING_EXACT_OLD_ALIAS_RECONCILIATION')
            normalized[name]=dict(p)
        return old_union(self,normalized,checkpoint)
    def decode(raw,checkpoint):
        checkpoint()
        require(type(raw) is bytes and 0<len(raw)<=xz.MAX_BYTES,'FRESH_BOUNDED_ENCODED_INPUT')
        if hashlib.sha256(raw).hexdigest() in hashes:
            require(state['ready'],'COMPLETE161_BEFORE_NEW_CODEC')
            return xz.decode(raw,checkpoint)
        return old_codec.decode(raw,checkpoint)
    def representation(self,projection):
        row=old_representation(self,projection)
        row['legacy_history_physical_evidence_provenance']=copy.deepcopy(declaration)
        return row
    source.descriptor=env['descriptor']=descriptor
    source.codec=env['codec']=NS(**{**vars(old_codec),'decode':decode})
    module.Binding.__init__,module.Binding.semantic_union,module.Binding.representation=initialize,semantic_union,representation
    module.legacy_history_catalog=copy.deepcopy(declaration)
    require(all(vars(module.Binding).get(n) is f for n,f in methods.items()),'ALL_OTHER_ORIGINAL_BINDING_ORACLES_RETAINED')
    require(all(vars(source.Projection).get(n) is f for n,f in projections.items()),'ENTIRE_ORIGINAL_PROJECTION_RETAINED')
    return NS(state=state,original_constructor=old_init,raw_constructor=raw_init,original_union=old_union,
        original_representation=old_representation,methods=methods,projections=projections,mode=mode,
        product_execution_authorized=False,parent_source_admitted=catalog.parent_source_admitted)
