"""Bounded bootstrap and actual full162 decoding after original75 construction.

The complete original75 reconstruction is an internal constructor stage over
an exactly derived old representation, not evidence for an external old file.
The actual v3 transport is independently hashed and decoded in full afterward.
No engine, Native, process, receipt IO or execution permission is provided.
"""
import copy
import hashlib
import json
from types import SimpleNamespace as NS

SELF='tools/p09/fixed162_worker_transport_v1.py'
TEST='tools/p09/tests/test_fixed162_worker_transport_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
MODULE_FIELD='legacy_history_declaration_module_pin'
FAILURE_FIELD='native009_post_body_shared720_failure_provenance'
DATA=dict(path='tools/p09/fixed165_history_declaration_v1.py',bytes=5516,
    sha256='187fc9cd7190487ee5f1a0e2e03e6b22235fa882b0f85f461bb5d4c1e65bab27')
PINS=[DATA,
    dict(path='tools/p09/legacy_history_binding_v1.py',bytes=12533,
        sha256='60e0816173d29102b1c7371a9f17761f72f62cec83ef81f46ee51f5b38dd0ef4'),
    dict(path='tools/p09/native009_failure_binding_v1.py',bytes=7808,
        sha256='47eb2c21ac4b682324ac2a78e0494c44e050d8dd06c73f16632779ba38646798'),
    dict(path='tools/p09/bounded_binary_capsule_wire_v3.py',bytes=11826,
        sha256='056bcd4c28e1002a21ed33e988ef5afe422ce01c682d341ea61148e03c481957'),
    dict(path='tools/p09/native009_full75_transport_v1.py',bytes=23830,
        sha256='31d1eae0c6983a705bfba60b8160fe513f50822b0e74c2ab88c80a68963459ad')]


def require(ok,label):
    if not ok: raise ValueError('FIXED162_WORKER_'+label)


def bootstrap_bytes(hint):
    require(type(hint) is dict,'EXPLICIT_COMPLETE_BOOTSTRAP')
    raw=(json.dumps(hint,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')
    require(0<len(raw)<=16384,'ORIGINAL_BOOTSTRAP16K'); return raw


def connect(root,loader,scope,bytes_policy,xz,bounded,checkpoint,exact,*,version=6):
    require(type(version) is int and 6<=version<=13,'BOUNDED_PREPARATION_WIRE_VERSION')
    libs,source_proofs=loader.load(root,PINS,{})
    data,history,failure,binary,previous=(libs.fixed165_history_declaration_v1,libs.legacy_history_binding_v1,
        libs.native009_failure_binding_v1,libs.bounded_binary_capsule_wire_v3,libs.native009_full75_transport_v1)
    require(history.fingerprint(data.DECLARATION)==history.DECLARATION_SHA,'WHOLE_FIXED_HISTORY_DECLARATION')
    old=previous.connect(root,loader,scope,bytes_policy,xz,bounded,checkpoint,exact)
    # This is only an explicit versioned filename slot, not a run/count or
    # validation-body change. The complete old75 reconstruction is retained.
    # Resolve the fixed75 module's already source-pinned constant helper.
    slot_ns,_=loader.load(root,[previous.PINS[2]],{})
    constant=slot_ns.native009_full72_transport_v1.constant
    validator,suffix_proof=constant(old.runtime.validate_worker_hint,'.compact.v5.json',f'.compact.v{version}.json',
        'validate_worker_hint','current_queue_successor_runtime.py')
    old.runtime.validate_worker_hint.__globals__['validate_worker_hint']=validator
    old.runtime.validate_worker_hint=validator
    state=NS(reconstructions=0,constructor75_calls=0,actual162_decodes=0,history_parent_admission=False)
    def core_hint(hint):
        require(type(hint) is dict and MODULE_FIELD in hint and FAILURE_FIELD in hint,'BOTH_EXPLICIT_NEW_ROLE_FIELDS')
        exact(hint[MODULE_FIELD],DATA,'EXACT_CURRENT_SOURCE_MODULE_NOT_RECEIPT_REFERENCE')
        exact(hint[FAILURE_FIELD],failure.ROLE,'EXECUTED_FAILED009_NOT_CURRENT_ACCEPTANCE_OR_REPLAY')
        return {k:v for k,v in hint.items() if k not in (MODULE_FIELD,FAILURE_FIELD)}
    def validate(hint):
        bootstrap_bytes(hint); return old.validate(core_hint(hint))
    def catalog(rows):
        require(type(rows) is list and len(rows)==162,'ENTIRE162_TABLE')
        selected=history.from_transport(rows[:161],copy.deepcopy(data.DECLARATION))
        pair=dict(schema_version='hwpx-agent.p09-lossless-runtime-source-projection/v1',next_case=165,
            semantic_original_pin=copy.deepcopy(failure.ORIGINAL),physical_envelope_pin=copy.deepcopy(failure.PHYSICAL))
        exact(rows[-1],pair,'EXACT_FAILED009_FINAL_DESCRIPTOR')
        require(not selected.parent_source_admitted,'DECLARATION_IS_NOT_PARENT_SOURCE_ADMISSION'); return selected
    def upgrade(module,selected):
        history_proof=history.install(module,selected,xz,mode='worker')
        failure_proof=failure.install(module,selected.rows(),copy.deepcopy(failure.ROLE),xz)
        return history_proof,failure_proof
    def reconstruct(hint,wire,check):
        checkpoint(); check(); validate(hint); core=core_hint(hint)
        require(type(wire) is bytes and 0<len(wire)<=16384,'ACTUAL_WIRE16K')
        expected={k:hint['capsule_pin'][k] for k in ('bytes','sha256')}
        exact(expected,dict(bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest()),'ACTUAL_V3_TRANSPORT_BYTES')
        compact=binary.decode_compact(wire.decode('ascii'),check)
        require(type(compact.get('bindings')) is list and len(compact['bindings'])==162,'ALL162_FROM_ACTUAL_BOUNDED_WIRE')
        common=compact['descriptor_context']
        pin=lambda p:dict(zip(('path','bytes','sha256'),p))
        rows=[dict(schema_version=common[0],next_case=common[1],semantic_original_pin=pin(v[0]),physical_envelope_pin=pin(v[1])) for v in compact['bindings']]
        selected=catalog(rows); prior75=selected.prior()
        # A deterministic in-memory constructor packet. It is never opened,
        # published, or presented as the actual wire or a historical receipt.
        old_compact=copy.deepcopy(compact)
        triple=lambda p:[p['path'],p['bytes'],p['sha256']]
        old_compact['bindings']=[[triple(r['semantic_original_pin']),triple(r['physical_envelope_pin'])] for r in prior75]
        constructor_wire=bounded.encode_compact(old_compact,check).encode('ascii')
        constructor_hint=copy.deepcopy(core)
        constructor_hint['capsule_pin'].update(bytes=len(constructor_wire),sha256=hashlib.sha256(constructor_wire).hexdigest())
        constructor_hint['first_descriptor']=copy.deepcopy(prior75[0])
        base,constructor_proof=old.reconstruct(constructor_hint,constructor_wire,check); state.constructor75_calls+=1
        exact(base.binding.descriptors(),prior75,'WHOLE_ORIGINAL75_CONSTRUCTION_BEFORE_UPGRADE')
        history_proof,failure_proof=upgrade(base.binding_module,selected)
        complete=base.binding_module.Binding(rows,hint['manifest_pin'],next_case=165)
        graph,graph_proof=old.metadata.connect(root,loader,bytes_policy,base.binding_module,complete,hint['step'],9,check)
        graph.worker,wire_proof=binary.connect(graph.worker,check)
        # The original decoder checks the REAL wire/context/manifest and runs
        # every original75->161->162 constructor, not just the preparse above.
        bound,decoder_proof=graph.worker.decode(wire,expected,check); state.actual162_decodes+=1
        exact(bound.descriptors(),rows,'ACTUAL_V3_ALL162_AFTER_ORIGINAL_DECODER')
        exact(dict(bound.manifest_pin),hint['manifest_pin'],'ACTUAL_CURRENT_MANIFEST_NOT_CONSTRUCTOR_SUBSTITUTION')
        exact(bound.descriptors()[0],hint['first_descriptor'],'ACTUAL_CURRENT_FIRST_DESCRIPTOR')
        require(not history_proof.parent_source_admitted,'WORKER_STILL_HAS_NO_PARENT_ADMISSION')
        state.reconstructions+=1
        return NS(**{**vars(graph),'binding':bound}),dict(descriptor_count=162,
            original75_constructor_stage=constructor_proof,constructor_packet_is_derived_not_external_transport=True,
            actual_v3_transport_hash_and_full_original_decoder=decoder_proof,wire_connection=wire_proof,
            all_history161_and_failure162_constructors_completed=True,
            history_constructor_counts=dict(history_proof.state),failure_constructor_counts=dict(failure_proof.state),
            data_source_module_pin=DATA,parent_fresh_admission_still_required=True,
            metadata_Frame_or_worker_process_or_Native_or_GO_qualified=False)
    return NS(reconstruct=reconstruct,validate=validate,catalog=catalog,metadata=old.metadata,runtime=old.runtime,
        binary=binary,history=history,failure=failure,data=copy.deepcopy(data.DECLARATION),
        old_api=old,state=state,suffix_proof=suffix_proof,source_proofs=source_proofs+old.source_proofs,
        actual_engine_or_product_permission_provided=False)
