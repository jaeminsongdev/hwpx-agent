"""New full162 zlib Binding/transport, preserving the old reference as history.

No source Frame, product/GO or acceptance entry. The original generic Binding
constructor/oracles execute in a new private namespace; the old162 constructor
table remains the independent semantic root, not a relabelled new wire.
"""
import copy
import hashlib
import json
import sys
from types import SimpleNamespace as NS

SELF='tools/p09/batch_zlib_binding.py'
TEST='tools/p09/tests/test_batch_zlib_binding.py'
DATA='tools/p09/zlib165_mapping_declaration_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
MANIFEST=PREFIX+'successor-run010-zlib-manifest001.v1.json'
WIRE=PREFIX+'successor-worker-capsule010.compact.zlib.v1.json'
BOOTSTRAP=PREFIX+'successor-worker-bootstrap010.zlib.v1.json'
HISTORY_KEYS=frozenset(('closed_prebody_source_policy','same_case_failed165_run007_provenance',
    'same_case_failed165_run008_provenance','historical_validation_failures_provenance',
    'legacy149_validation_failures_provenance','legacy154_validation_failure_provenance',
    'legacy_history_physical_evidence_provenance','native009_post_body_shared720_failure_provenance'))
BASE_KEYS=frozenset(('schema_version','next_case','manifest_pin','semantic_source_freeze','physical_source_freeze',
    'descriptors','full_original_product_oracle_required','original_raw_receipts_not_claimed_as_physically_locked',
    'historical_predecessor_provenance','historical_provenance_is_current_acceptance'))


def require(ok,code):
    if not ok:raise ValueError('ZLIB_BINDING_'+code)


def canonical(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')


def digest(value):return hashlib.sha256(canonical(value)[:-1]).hexdigest()


def pin(name,raw):return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def declared_rows(reference,declaration,mapping,checkpoint):
    checkpoint();old=reference.binding.descriptors()
    require(len(old)==162 and digest(old)==declaration.OLD_TABLE_SHA256 and len(declaration.ENCODED)==162,
        'EXACT_ORIGINAL_CONSTRUCTOR_TABLE_AND_NEW162')
    rows=[]
    for index,(before,encoded) in enumerate(zip(old,declaration.ENCODED),1):
        checkpoint();require(type(encoded) is tuple and len(encoded)==2,'TYPED_PHYSICAL_DECLARATION')
        rows.append(dict(schema_version=mapping.SCHEMA,next_case=165,
            semantic_original_pin=copy.deepcopy(before['semantic_original_pin']),
            physical_envelope_pin=dict(path=mapping.PREFIX+f'case165-zlib-g001-{index:03}.envelope.v1.json',
                bytes=encoded[0],sha256=encoded[1])))
    require(digest(rows)==declaration.NEW_TABLE_SHA256,'EXACT_FRESH_FILE_QUALIFIED_NEW_TABLE')
    return rows


def historical_context(reference,checkpoint):
    required={n:dict(p) for n,p in reference.binding.originals.items()}
    required[reference.binding.manifest_pin['path']]=dict(reference.binding.manifest_pin)
    projection,_=reference.binding.project(required,checkpoint)
    representation=reference.binding.representation(projection)
    extra=set(representation)-BASE_KEYS
    if extra!=HISTORY_KEYS:
        raise ValueError('ZLIB_BINDING_EXACT_ALL_HISTORICAL_ROLES',tuple(sorted(extra)))
    return copy.deepcopy(representation['historical_predecessor_provenance']),{
        key:copy.deepcopy(representation[key]) for key in HISTORY_KEYS}


def manifest(rows,history,roles,declaration):
    require(digest(rows)==declaration.NEW_TABLE_SHA256 and set(roles)==HISTORY_KEYS,'EXACT_MANIFEST_DECLARATION')
    return dict(schema_version='hwpx-agent.p09-run010-zlib-manifest/v1',next_case=165,physical_run=10,
        accepted_count_before=158,descriptors=copy.deepcopy(rows),historical_predecessor_provenance=copy.deepcopy(history),
        original_historical_input_roles=copy.deepcopy(roles),reference_manifest_pin=dict(declaration.REFERENCE_MANIFEST),
        reference_descriptor_table_sha256=declaration.OLD_TABLE_SHA256,
        physical_codec_pin=dict(declaration.CODEC2),physical_qualification_pin=dict(declaration.QUALIFICATION),
        original_semantic_pins_unchanged=True,current_whole_Native_source_scope_qualified=False,
        GO_authorized=False)


def connect(root,loader,scope,reference,declaration,mapping,bindings,checkpoint):
    """New generic Binding plus exact old/new alias and historical-role layers."""
    rows=declared_rows(reference,declaration,mapping,checkpoint)
    history,roles=historical_context(reference,checkpoint)
    manifest_row=manifest(rows,history,roles,declaration);manifest_raw=canonical(manifest_row)
    manifest_pin=pin(MANIFEST,manifest_raw)
    module,original_proof=bindings.connect(root,loader,scope,165,history)
    module.exact(bindings.PINS[1],declaration.CODEC2,'EXACT_V2_BOUNDED_OUTPUT_SOURCE')
    mapping.projection_factory(module.source,module.source.codec,rows,module.exact)
    raw_init,raw_union,raw_represent=module.Binding.__init__,module.Binding.semantic_union,module.Binding.representation
    methods={n:v for n,v in vars(module.Binding).items() if n not in ('__init__','semantic_union','representation')}
    frozen=copy.deepcopy(rows);historical=copy.deepcopy(roles);state=NS(constructor_calls=0)
    def initialize(self,actual_rows,actual_manifest,*,next_case):
        require(type(next_case) is int and next_case==165,'EXACT_NEW_CONTEXT165')
        module.exact(actual_rows,frozen,'WHOLE_NEW162_NOT_SUBSET_OR_OLD_TABLE')
        module.exact(actual_manifest,manifest_pin,'ONLY_NEW_MANIFEST_NOT_OLD_REFERENCE')
        raw_init(self,actual_rows,actual_manifest,next_case=next_case)
        module.exact(self.descriptors(),frozen,'WHOLE_ORIGINAL_GENERIC_CONSTRUCTOR_COMPLETED')
        state.constructor_calls+=1
    def semantic_union(self,actual_rows,check):
        check();verified=scope.pins(list(actual_rows.values()));module.exact(verified,actual_rows,'EXACT_MAPPING_KEYS')
        normalized={};current_aliases=0
        for name,value in verified.items():
            check()
            if name in self.reverse:
                module.exact(value,dict(self.physical[name]),'EXACT_CURRENT_PHYSICAL_ALIAS')
                name=self.reverse[name];value=dict(self.originals[name]);current_aliases+=1
            require(name not in normalized or normalized[name]==value,'NO_OLD_NEW_ALIAS_CONFLICT')
            normalized[name]=dict(value)
        old_semantic,old_proof=reference.binding.semantic_union(normalized,check)
        result,proof=raw_union(self,old_semantic,check)
        return result,dict(proof,prior_exact_alias_reconciliation=old_proof,current_zlib_aliases=current_aliases,
            both_old_and_new_physical_aliases_checked_before_full_semantic_union=True)
    def represented(self,projection):
        result=raw_represent(self,projection)
        for name in HISTORY_KEYS:result[name]=copy.deepcopy(historical[name])
        result['current_zlib_mapping_provenance']=dict(schema_version='hwpx-agent.p09-zlib-current-mapping/v1',
            physical_qualification_pin=dict(declaration.QUALIFICATION),codec_pin=dict(declaration.CODEC2),
            old_descriptor_table_sha256=declaration.OLD_TABLE_SHA256,new_descriptor_table_sha256=declaration.NEW_TABLE_SHA256,
            original_failures_not_promoted=True,current_product_or_GO_qualified=False)
        return result
    module.Binding.__init__,module.Binding.semantic_union,module.Binding.representation=initialize,semantic_union,represented
    require(all(vars(module.Binding).get(n) is value for n,value in methods.items()),'ALL_OTHER_ORIGINAL_SCOPE_BYTE_RESOURCE_ORACLES')
    bound=module.Binding(copy.deepcopy(rows),manifest_pin,next_case=165)
    return NS(binding_module=module,binding=bound,manifest=manifest_row,manifest_raw=manifest_raw,manifest_pin=manifest_pin,
        state=state,reference=reference,proof=dict(original_reference_table_verified=True,new_generic_constructor_executed=True,
            original_generic_constructor_cursor_inverse=original_proof['exact_constructor_inverse_code_equal'],
            all_other_original_scope_byte_resource_oracles_retained=True,historical_roles_preserved=sorted(HISTORY_KEYS),
            original_Projection_class_methods_and_v2_decoder_retained=True,
            current_Native_product_or_GO_qualified=False))


def worker_graph(root,loader,known,api,bounded,byte_policy,reference,step,declaration,worker,checkpoint):
    require(digest(reference.binding.descriptors())==declaration.NEW_TABLE_SHA256,'NEW_REFERENCE_BEFORE_TRANSPORT')
    graph,runtime=worker.transport_graph(root,loader,known,api,bounded,byte_policy,reference,step,checkpoint)
    original=runtime.validate_worker_hint
    revised=runtime.metadata.project(original,dict(original.__globals__),{'.compact.v1.json':'.compact.zlib.v1.json'})
    original.__globals__['validate_worker_hint']=revised;runtime.validate_worker_hint=revised
    return NS(reference=reference,graph=graph,runtime=runtime)


def transport(root,loader,known,api,bounded,byte_policy,old_reference,step,declaration,mapping,bindings,worker,checkpoint):
    """Original inner codec, complete new graph and a versioned path slot."""
    reference=connect(root,loader,old_reference.binding_module.source.scope,
        old_reference,declaration,mapping,bindings,checkpoint)
    return worker_graph(root,loader,known,api,bounded,byte_policy,reference,step,declaration,worker,checkpoint)


def entry_reconstructor(worker,metadata):
    """Two exact data-path slots; every original admission predicate remains."""
    original=worker.reconstruct
    revised=metadata.project(original,dict(original.__globals__),{
        PREFIX+'successor-worker-bootstrap010.v1.json':BOOTSTRAP,
        PREFIX+'successor-worker-capsule010.compact.v1.json':WIRE})
    return revised


def preparation_hint(previous,reference,wire_pin):
    """Carry the exact old context into a distinct, closed NO-GO package."""
    require(type(previous) is dict and type(previous.get('index')) is int and previous['index']==165
        and type(previous.get('run')) is int and previous['run']==9,'REFERENCE165_RUN009_CONTEXT')
    require(type(previous.get('step')) is dict and previous['step'].get('index')==165
        and previous['step'].get('before')==158,'UNCHANGED_QUEUE_CURSOR158')
    fields=('schema_version','index','run','step','capsule_pin','manifest_pin','first_descriptor',
        'historical_pairs','historical_provenance')
    core={name:copy.deepcopy(previous[name]) for name in fields}
    require(type(wire_pin) is dict and set(wire_pin)=={'bytes','sha256'}
        and type(wire_pin['bytes']) is int and 0<wire_pin['bytes']<=16384,'NEW_WIRE16K_PIN')
    core.update(run=10,manifest_pin=dict(reference.manifest_pin),capsule_pin=dict(path=WIRE,**wire_pin),
        first_descriptor=copy.deepcopy(reference.binding.descriptors()[0]))
    return core


def main():
    import re,time,traceback
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.dont_write_bytecode=True
    require(not sys.argv[1:],'NO_EXTRA_ARGUMENTS')
    denied=[]
    def audit(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile'):
            denied.append(event);raise ValueError('ZLIB_BINDING_PROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import batch_engine_connection as entry,owned_source_read_pressure as byte_policy
    bootstrap=entry.bootstrap_loader(c.ROOT);guards,_=bootstrap.load(c.ROOT,list(entry.BOOTSTRAP[1:]),{})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    guard=guards.owned_cpu_baseline_v1.guard_type(guards.terminal_metadata_pressure_v1.guard_type(
        guards.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    source=None;started=time.monotonic();stage='CONSTRUCTION'
    row=dict(state='FAILED_NEW_ZLIB_BINDING_AND_DISK_TRANSPORT_NOT_NATIVE',GO_authorized=False,
        accepted_count_delta=0,product_or_worker_process_or_Native_executed=False)
    try:
        guard.acquire();source=a.AcceptanceReader(c.ROOT,guard.check)
        for n in (SELF,TEST,DATA,'tools/p09/batch_zlib_mapping.py',entry.SELF,
                  'tools/p09/owned_source_read_pressure.py'):source.pin(n)
        for p in entry.BOOTSTRAP:a.exact(source.pin(p['path']),p,'ORIGINAL_BOOTSTRAP')
        libraries,_=entry.planning_libraries(c.ROOT,source,a,bootstrap)
        admission,batch,reuse=(getattr(libraries,n) for n in ('batch_scope_admission','batch_verification','verification_reuse'))
        data=admission.read_plan(source,a,batch,reuse);entry.extend_execution(data,source,batch)
        # The old010 package is not an ancestor of the new data. Build directly
        # from its independently qualified original009 reference, not twice via
        # an unrelated010 constructor. Keep the original source allow-list.
        additions={n:dict(source.pin(n)) for n in (SELF,TEST,DATA,'tools/p09/batch_zlib_mapping.py')}
        known=batch.scope.extend(data.planned.logical,batch.scope.pins(data.evidence['source_pins']))
        known=batch.scope.extend(known,additions)
        initial=batch.PacedNamespaceLoader(bootstrap,source,known).api
        names,_=initial.load(c.ROOT,[known['tools/p09/'+n+'.py'] for n in
            ('ast_clone_namespace_v1','ast_copy_namespace_connection_v1')],{})
        optimized,_=names.ast_copy_namespace_connection_v1.connect(bootstrap,names.ast_clone_namespace_v1)
        loader=batch.PacedNamespaceLoader(optimized,source,known).api
        names,_=loader.load(c.ROOT,[known['tools/p09/native009_full72_construction_v1.py']],{})
        loader,_=names.native009_full72_construction_v1.private_runtime_imports(loader)
        names,_=loader.load(c.ROOT,[known['tools/p09/'+n+'.py'] for n in
            ('zlib165_mapping_declaration_v1','batch_zlib_mapping','current_queue_successor_binding',
             'batch_worker_entry','bounded_successor_capsule_wire_v2','native009_parent_scope_v1',
             'fixed162_worker_transport_v1','receipt_xz_envelope_v1')],{})
        declaration,mapping,bindings,worker=(getattr(names,n) for n in
            ('zlib165_mapping_declaration_v1','batch_zlib_mapping','current_queue_successor_binding','batch_worker_entry'))
        qualification=a.read_exact(source,declaration.QUALIFICATION)
        a.exact(digest(qualification['current_result']['descriptors']),declaration.NEW_TABLE_SHA256,'QUALIFIED_NEW_TABLE_SOURCE')
        api=names.fixed162_worker_transport_v1.connect(c.ROOT,loader,batch.scope,byte_policy,
            names.receipt_xz_envelope_v1,names.bounded_successor_capsule_wire_v2,guard.check,a.exact)
        def read(p,limit):
            require(limit==16384 and p['bytes']<=limit,'ORIGINAL_ENTRY16K')
            before=source.maximum_parse_bytes
            try:
                source.maximum_parse_bytes=min(before,limit+1)
                actual,raw=source._read(p['path'],parse=True);source._bind(actual['path'],actual)
            finally:source.maximum_parse_bytes=before
            a.exact(actual,p,'ACTUAL_BOUNDED_ENTRY_BYTES');return bytes(raw)
        previous=json.loads(read(dict(declaration.REFERENCE_BOOTSTRAP),16384).decode('ascii'))
        old_reference,old_proof=api.reconstruct(previous,read(dict(declaration.REFERENCE_WIRE),16384),guard.check)
        a.exact(dict(old_reference.binding.manifest_pin),dict(declaration.REFERENCE_MANIFEST),'INDEPENDENT_ORIGINAL009_MANIFEST')
        prepared=transport(c.ROOT,loader,known,api,names.bounded_successor_capsule_wire_v2,byte_policy,
            old_reference,previous['step'],declaration,mapping,bindings,worker,guard.check)
        wire,wire_pin=prepared.graph.worker.encode(prepared.reference.binding,
            previous['step']['prior_queue_pin'],previous['step']['prior_candidate_pin'],guard.check)
        decoded,_=prepared.graph.worker.decode(wire,wire_pin,guard.check)
        a.exact(decoded.descriptors(),prepared.reference.binding.descriptors(),'ACTUAL_ALL_NEW162_WIRE_ROUNDTRIP')
        a.exact(dict(decoded.manifest_pin),prepared.reference.manifest_pin,'NEW_MANIFEST_NOT_REFERENCE_RELABEL')
        core=preparation_hint(previous,prepared.reference,wire_pin)
        a.exact(prepared.runtime.validate_worker_hint(core,prepared.graph.worker.TASK),(165,10),'EXACT_NEW_HINT')
        hint=dict(schema_version='hwpx-agent.p09-run010-worker-preparation/v1',execution=core,
            reference_bootstrap_pin=dict(declaration.REFERENCE_BOOTSTRAP),reference_wire_pin=dict(declaration.REFERENCE_WIRE),
            reference_is_constructor_data_not_product_replay=True,GO_authorized=False)
        payloads=((MANIFEST,prepared.reference.manifest_raw,262144),(WIRE,wire,16384),(BOOTSTRAP,canonical(hint),16384))
        require(all(type(raw) is bytes and 0<len(raw)<=limit for _,raw,limit in payloads),'ALL_PAYLOAD_BOUNDS_BEFORE_ANY_PUBLICATION')
        stage='PUBLICATION';published=[];created=[]
        for name,raw,limit in payloads:
            existed=(c.ROOT/name).exists()
            p=names.native009_parent_scope_v1.publish_bytes(c.ROOT,name,raw,source,guard,byte_policy,a,limit)
            published.append(p)
            if not existed:created.append(name)
        stage='DISK_ADMISSION'
        independent=[]
        def reference_factory(prior,packet,check):
            old,proof=api.reconstruct(prior,packet,check)
            a.exact(dict(old.binding.manifest_pin),dict(declaration.REFERENCE_MANIFEST),'DISK_ORIGINAL009_MANIFEST')
            new=connect(c.ROOT,loader,batch.scope,old,declaration,mapping,bindings,check)
            a.exact(new.manifest_pin,prepared.reference.manifest_pin,'INDEPENDENT_NEW_MANIFEST')
            independent.append(new)
            return new,proof
        def transport_factory(reference,step,check):
            item=worker_graph(c.ROOT,loader,known,api,names.bounded_successor_capsule_wire_v2,byte_policy,
                reference,step,declaration,worker,check)
            return item.graph,item.runtime
        reconstruct=entry_reconstructor(worker,prepared.runtime.metadata)
        rebuilt=reconstruct(prepared.graph.worker.TASK,published[2],read,reference_factory,transport_factory,guard.check)
        require(len(independent)==1 and independent[0] is not prepared.reference,'INDEPENDENT_BINDING_NOT_PARENT_REUSE')
        a.exact(rebuilt.graph.binding.descriptors(),prepared.reference.binding.descriptors(),'DISK_ALL162_EQUAL_PARENT')
        a.exact(dict(rebuilt.graph.binding.manifest_pin),published[0],'DISK_EXACT_PUBLISHED_NEW_MANIFEST')
        require(rebuilt.proof['metadata_byte_admissions']==4,'EXACT_FOUR_FRESH_ENTRY_READS')
        stage='FINAL_SOURCE_CHECK';source.finish();guard.check(force=True)
        require(source.final_fresh_hashes==len(source.snapshots) and not denied,'ALL_SOURCE_CLOSING_AND_NO_PROCESS')
        row.update(state='PASS_NEW_ZLIB_BINDING_AND_FRESH_DISK_TRANSPORT_NOT_NATIVE',
            descriptor_count=len(rebuilt.graph.binding.descriptors()),new_manifest_and_full_table_independently_reconstructed=True,
            publication_pins=published,created_files=created,reused_files=[p['path'] for p in published if p['path'] not in created],
            binding_proof=prepared.reference.proof,actual_entry_proof=rebuilt.proof,
            source_pins=list(source.snapshots.values()),old010_package_constructor_replayed=False,
            original009_constructor_calls=api.state.reconstructions,original009_full162_decodes=api.state.actual162_decodes,
            source_Frame_or_live_shared_decoder_or_worker_readiness_qualified=False,
            installed_in_product=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError,NameError,ImportError) as error:
        row.update(error_type=type(error).__name__,failure_stage=stage)
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        if error.args and error.args[0]=='ZLIB_BINDING_EXACT_ALL_HISTORICAL_ROLES':row['observed_history_keys']=list(error.args[1])
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            subprocess_creation_attempts=len(denied),
            fresh_inputs=0 if source is None else len(source.snapshots),final_fresh_hashes=0 if source is None else source.final_fresh_hashes,
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_max=max((s.get('parent_cpu_machine_percent') or 0 for s in guard.samples),default=None),
            private_MiB_max=max((s['parent_private_mib'] for s in guard.samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
        if guard.cleanup is not True:row['state']='CLEANUP_FAILED_ZLIB_BINDING_NOT_NATIVE'
        print(json.dumps(row))
    return 0 if row['state'].startswith('PASS_') and guard.cleanup is True else 2


if __name__=='__main__':raise SystemExit(main())
