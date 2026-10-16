"""Actual full73 parent metadata admission and closing hashes; no Native entry.

Use the engine's original BuildReader and unchanged live pressure binding.
Register the real shared metadata decoder before any future Frame. Never
substitute a standalone decoder budget, fake Job cleanup or a product receipt.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/qualify_native009_full73_metadata_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
PARENT_PROOF=dict(path=PREFIX+'native009-full73-parent-connection003.v1.json',bytes=92954,
    sha256='f186ec913c3ce6b7c9703634a0c34859b0f5eac581f447457610d47034268a34')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
QUALIFIER='tools/p09/qualify_native009_full73_parent_v1.py'
FAILED_METADATA=dict(path=PREFIX+'native009-full73-metadata002.v1.json',bytes=8139,
    sha256='2e75b98d9003635fbe5483a694049aea3641df7ce6cea66564270f200f4e866b')
CPU_STOP=dict(path=PREFIX+'native009-full73-metadata004.v1.json',bytes=8974,
    sha256='7698af5526b94ceac655a773b46206ff5d9bbe87d0676753674417a56941bbe5')
STRUCTURE_STOP=dict(path=PREFIX+'native009-full73-metadata005.v1.json',bytes=3697,
    sha256='e902c51046f19c0b5c9241e7659ba7f38b01f4a31a8e96ef86a45479ac9aea66')
EXISTING_SNAPSHOT_STOP=dict(path=PREFIX+'native009-full73-metadata006.v1.json',bytes=12201,
    sha256='4dc47db25e179919948322b0895100ece2eed8ee79ae9d4d02fdf1e2e8daa1f8')
CODE_IDENTITY_STOP=dict(path=PREFIX+'native009-full73-metadata007.v1.json',bytes=12168,
    sha256='a0b01c06369199de1a0a37e190e0be6dcb43884b84d78bf8ab94210d3d80c33d')
PUBLICATION_REVIEW=PREFIX+'native009-full73-metadata-publication-review003.v1.json'
SNAPSHOT_SOURCE=dict(path='tools/p09/single_snapshot_source_guard_v1.py',bytes=4560,
    sha256='f3555f4395154be7c929e76eeb451226402b49cc54b0ab6da335ba94555eae43')


def require(ok,label):
    if not ok:raise ValueError('FULL73_METADATA_'+label)


def restore_pin_map(required,record,scope,exact):
    import hashlib
    require(type(record) is dict and set(record)=={'schema_version','omitted_declared_paths','extra_physical_pins','raw_pin_count','raw_pin_map_sha256'},'COMPACT_PIN_MAP_FIELDS')
    require(record['schema_version']=='hwpx-agent.p09-metadata-pin-map-over-declared-scope/v1','COMPACT_PIN_MAP_SCHEMA')
    omitted=record['omitted_declared_paths'];extra=record['extra_physical_pins']
    require(type(omitted) is list and omitted==sorted(set(omitted)) and set(omitted)<=set(required),'EXACT_OMISSION_SET')
    require(type(extra) is list,'COMPACT_EXTRA_PIN_LIST')
    extra={} if not extra else scope.pins(extra)
    require(not(set(extra)&set(required)),'NO_COMPACT_PIN_CONFLICT_OVERRIDE')
    restored={n:dict(p) for n,p in required.items() if n not in omitted}
    restored.update(extra)
    exact(scope.pins(list(restored.values())),restored,'RESTORED_PIN_MAP_SHAPE')
    require(type(record['raw_pin_count']) is int and len(restored)==record['raw_pin_count'],'COMPACT_PIN_COUNT')
    digest=hashlib.sha256(json.dumps(restored,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()
    exact(digest,record['raw_pin_map_sha256'],'COMPACT_PIN_MAP_DIGEST')
    return restored


def compact_pin_map(required,actual,scope,exact):
    import hashlib
    require(type(required) is dict and bool(required) and type(actual) is dict and bool(actual),'NONEMPTY_PIN_MAPS')
    exact(scope.pins(list(required.values())),required,'DECLARED_PIN_MAP_SHAPE')
    exact(scope.pins(list(actual.values())),actual,'ACTUAL_PIN_MAP_SHAPE')
    record=dict(schema_version='hwpx-agent.p09-metadata-pin-map-over-declared-scope/v1',
        omitted_declared_paths=sorted(set(required)-set(actual)),
        extra_physical_pins=sorted((p for n,p in actual.items() if n not in required),key=lambda p:p['path']),
        raw_pin_count=len(actual),raw_pin_map_sha256=hashlib.sha256(json.dumps(actual,ensure_ascii=True,
            sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest())
    exact(restore_pin_map(required,record,scope,exact),actual,'WHOLE_ACTUAL_PIN_MAP_LOSSLESS_ROUNDTRIP')
    return record


def encoding_contracts(scope,exact):
    def pin(name):return dict(path=name,bytes=1,sha256='a'*64)
    required=scope.pins([pin(f'input/{n:04}.json') for n in range(3230)])
    full=compact_pin_map(required,required,scope,exact)
    exact(restore_pin_map(required,full,scope,exact),required,'ENCODER_FULL_MAP')
    subset={n:p for i,(n,p) in enumerate(required.items()) if i>1}
    omitted=compact_pin_map(required,subset,scope,exact)
    require(len(omitted['omitted_declared_paths'])==2,'ENCODER_EXACT_OMISSIONS')
    actual=scope.extend(subset,scope.pins([pin(f'physical/{n}.json') for n in range(4)]))
    expanded=compact_pin_map(required,actual,scope,exact)
    require(len(expanded['extra_physical_pins'])==4,'ENCODER_EXACT_EXTRAS')
    conflict=dict(required);name=next(iter(conflict));conflict[name]=dict(conflict[name],sha256='b'*64)
    try:compact_pin_map(required,conflict,scope,exact)
    except ValueError:pass
    else:raise ValueError('FULL73_METADATA_ENCODER_CONFLICT_ACCEPTED')
    try:restore_pin_map(required,dict(full,raw_pin_map_sha256='0'*64),scope,exact)
    except ValueError:pass
    else:raise ValueError('FULL73_METADATA_ENCODER_DIGEST_MUTATION_ACCEPTED')
    raw_bytes=len(json.dumps(actual,ensure_ascii=True,indent=2).encode('ascii'))
    compact_bytes=len(json.dumps(expanded,ensure_ascii=True,indent=2).encode('ascii'))
    require(raw_bytes>262144 and compact_bytes<2048,'ENCODER_3230_INPUTS_WITHOUT_PUBLISHER_LIMIT_INCREASE')
    return dict(state='PASS_BOUNDED_METADATA_REPORT_PIN_MAP6_NOT_RUNTIME_OR_PRODUCT',contracts=6,
        raw_fixture_bytes=raw_bytes,compact_fixture_bytes=compact_bytes,publisher_limit_bytes=262144,
        raw_pin_count=len(actual),full_map_losslessly_restored=True,actual_product_or_Native_executed=False)


def code_body_comparison(actual,expected):
    # Source-pinned AST definitions may retain different debug line metadata.
    # Every executable field, including constants/closures/exception tables,
    # remains exact; this does not rewrite or replace either function.
    fields=('co_code','co_consts','co_names','co_varnames','co_freevars','co_cellvars','co_flags',
        'co_argcount','co_posonlyargcount','co_kwonlyargcount','co_nlocals','co_stacksize','co_exceptiontable',
        'co_name','co_qualname')
    compared={name:getattr(actual,name)==getattr(expected,name) for name in fields}
    origin=Path(actual.co_filename).name==Path(expected.co_filename).name
    return dict(executable_fields_equal=all(compared.values()),executable_field_equalities=compared,
        source_basename_equal=origin,full_code_equal=actual==expected,
        debug_line_equal=actual.co_firstlineno==expected.co_firstlineno,
        debug_line_table_equal=actual.co_linetable==expected.co_linetable)


def compiled_snapshot_references(raw):
    import ast,hashlib
    from types import CodeType
    require(type(raw) is bytes and len(raw)==SNAPSHOT_SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==SNAPSHOT_SOURCE['sha256'],'EXACT_SNAPSHOT_SOURCE_FOR_CODE_REFERENCES')
    tree=ast.parse(raw.decode('utf-8'))
    roots={'full_module':compile(raw.decode('utf-8'),SNAPSHOT_SOURCE['path'],'exec',dont_inherit=True,optimize=0),
        'private_non_import_AST':compile(ast.fix_missing_locations(ast.Module(body=[node for node in tree.body
            if not isinstance(node,(ast.Import,ast.ImportFrom))],type_ignores=[])),SNAPSHOT_SOURCE['path'],'exec',dont_inherit=True,optimize=0)}
    def one(parent,name):
        found=[code for code in parent.co_consts if type(code) is CodeType and code.co_name==name]
        require(len(found)==1,'ONE_EXACT_SOURCE_CODE_DEFINITION');return found[0]
    references={}
    for name,root in roots.items():
        counter=one(root,'Counters')
        references[name]=dict(fresh_source=one(root,'source'),counter_init=one(counter,'__init__'),counter_summary=one(counter,'summary'))
    return references


def adopt_source_snapshot(reader,snapshot,raw,code_diagnostics=None,source_references=None):
    old=type(reader)
    require(snapshot.original.AuditEvidenceReader in old.__mro__,'ORIGINAL_AUDIT_READER_ANCESTOR')
    require(reader.read_passes==reader.bytes_read==0 and not reader.snapshots,'FRESH_UNUSED_REAL_READER_ONLY')
    if hasattr(reader,'_single_snapshot_source_counters'):
        Expected,proof=snapshot.reader_type(snapshot.original.AuditEvidenceReader,raw)
        layers=[cls for cls in old.__mro__ if '_source' in vars(cls)
            and getattr(vars(cls)['_source'],'__code__',None)==Expected._source.__code__]
        require(len(layers)==1 and type(reader).source_snapshot_diagnostics.__code__==Expected.source_snapshot_diagnostics.__code__,
            'ONE_EXACT_EXISTING_SNAPSHOT_METHOD_FAMILY')
        source_fn=layers[0]._source.__globals__['source'];counters=reader._single_snapshot_source_counters
        comparisons={name:code_body_comparison(fn.__code__,reference.__code__) for name,fn,reference in (
            ('fresh_source',source_fn,snapshot.source),('counter_init',type(counters).__init__,snapshot.Counters.__init__),
            ('counter_summary',type(counters).summary,snapshot.Counters.summary))}
        if code_diagnostics is not None:code_diagnostics.update(comparisons)
        functions=dict(fresh_source=source_fn,counter_init=type(counters).__init__,counter_summary=type(counters).summary)
        references=source_references or {'exact_loaded_helper':dict(fresh_source=snapshot.source.__code__,
            counter_init=snapshot.Counters.__init__.__code__,counter_summary=snapshot.Counters.summary.__code__)}
        matched=[name for name,expected in references.items() if all(fn.__code__==expected[key] for key,fn in functions.items())]
        if code_diagnostics is not None:code_diagnostics['exact_pinned_compilation_matches']=matched
        require(bool(matched) and source_fn.__defaults__==snapshot.source.__defaults__ and source_fn.__kwdefaults__==snapshot.source.__kwdefaults__,
            'EXISTING_FRESH_STAT_AND_COUNTER_BODIES')
        stats=reader.source_snapshot_diagnostics()
        require(all(stats[n]==0 for n in ('source_requests','fresh_no_follow_stat_attempts','ordinary_windows_snapshot_decisions',
            'exact_original_fallback_requests','ordinary_nonfile_rejections')) and not stats['stat_result_cached_or_reused_between_source_requests'],
            'EXISTING_SNAPSHOT_IS_FRESH_NOT_REUSED_READ_EVIDENCE')
        return dict(proof,existing_verified_snapshot_reused=True,actual_original_allocation_result_adopted=False,
            original_reader_instance_class_fields_and_builder_methods_unchanged=True,original_initialization_not_repeated=True,
            original_default_build_namespace_not_mutated=True,held_Native_Frame_reader_not_changed=True,
            exact_pinned_compilation_matches=matched,
            original_reader_class_name=old.__name__)
    owners=[cls for cls in old.__mro__ if vars(cls).get('_source') is old._source]
    require(len(owners)==1 and len(owners[0].__bases__)==1,'EXACT_SOURCE_OWNER_BASE')
    Snapshot,proof=snapshot.reader_type(owners[0].__bases__[0],raw)
    # The production allocator may be a factory returning a different class.
    # Adopt its untouched fresh result instead of changing/re-running allocation.
    # C3 preserves every builder/route super() and additional path predicate.
    class Reader(old,Snapshot):pass
    for name in ('__init__','_read','_source'):
        require(getattr(Reader,name) is getattr(old,name),'WHOLE_BUILDER_METHODS_RETAINED')
    require(old in Reader.__mro__ and Snapshot in Reader.__mro__,'ORIGINAL_BUILDER_AND_FRESH_LEAF_MRO')
    before=dict(vars(reader));pacer=reader.pacer
    reader.__class__=Reader
    reader._single_snapshot_source_counters=snapshot.Counters()
    require(reader.pacer is pacer and all(vars(reader).get(n) is value for n,value in before.items()),'ALL_REAL_READER_FIELDS_AND_PACER_RETAINED')
    return dict(proof,
        original_builder_source_and_ancestor_checks_and_read_and_constructor_functions_retained=True,
        original_default_build_namespace_not_mutated=True,held_Native_Frame_reader_not_changed=True,
        existing_verified_snapshot_reused=False,actual_original_allocation_result_adopted=True,original_initialization_not_repeated=True,
        original_reader_class_name=old.__name__,original_source_owner_class_name=owners[0].__name__)


def source_mro_contracts(root,snapshot,raw):
    class Base(snapshot.original.AuditEvidenceReader):pass
    class Builder(Base):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.extra_checks=0
        def _read(self,*args,**kwargs):return super()._read(*args,**kwargs)
        def _source(self,name):
            path=super()._source(name);self.extra_checks+=1;return path
    allocations=[]
    class Factory:
        def __new__(cls,*args,**kwargs):allocations.append(1);return Builder(*args,**kwargs)
    original=NS(BuildReader=Factory)
    reader=original.BuildReader(root,lambda:None);before_type=type(reader);before_pacer=reader.pacer
    proof=adopt_source_snapshot(reader,snapshot,raw)
    existing_type=type(reader);existing_fields=dict(vars(reader))
    reused=adopt_source_snapshot(reader,snapshot,raw)
    require(reused['existing_verified_snapshot_reused'] and type(reader) is existing_type
        and all(vars(reader).get(n) is value for n,value in existing_fields.items()),'MRO_CONTRACT_EXISTING_QUALIFIED_LAYER_REUSED')
    require(all(getattr(type(reader),n) is getattr(Builder,n) for n in ('__init__','_read','_source')),'MRO_CONTRACT_WHOLE_METHODS')
    first=reader.pin(SELF);second=reader.fresh_pin(SELF)
    require(first==second and reader.extra_checks==reader.read_passes==2,'MRO_CONTRACT_ORIGINAL_EXTRA_CHECKS_AND_TWO_REAL_READS')
    stats=reader.source_snapshot_diagnostics()
    require(stats['source_requests']==stats['fresh_no_follow_stat_attempts']==stats['ordinary_windows_snapshot_decisions']==2
        and stats['exact_original_fallback_requests']==0 and not stats['stat_result_cached_or_reused_between_source_requests'],'MRO_CONTRACT_FRESH_STAT_NOT_CACHE')
    require(original.BuildReader is Factory and type(reader) is not before_type and reader.pacer is before_pacer
        and allocations==[1] and proof['original_default_build_namespace_not_mutated'],'MRO_CONTRACT_FACTORY_AND_FIELDS_UNCHANGED')
    try:adopt_source_snapshot(reader,snapshot,raw)
    except ValueError as error:require(error.args==('FULL73_METADATA_FRESH_UNUSED_REAL_READER_ONLY',),'MRO_CONTRACT_EXACT_ACTIVE_READER_REJECTION')
    else:raise ValueError('FULL73_METADATA_MRO_ACTIVE_READER_ACCEPTED')
    references=compiled_snapshot_references((root/SNAPSHOT_SOURCE['path']).read_bytes())
    functions=dict(fresh_source=snapshot.source,counter_init=snapshot.Counters.__init__,counter_summary=snapshot.Counters.summary)
    matched=[name for name,expected in references.items() if all(fn.__code__==expected[key] for key,fn in functions.items())]
    require(bool(matched),'MRO_CONTRACT_IMPORTED_HELPER_MATCHES_EXACT_FRESH_COMPILE')
    code=snapshot.Counters.__init__.__code__
    constants=tuple(1 if type(v) is int and v==0 else v for v in code.co_consts)
    require(constants!=code.co_consts and all(code.replace(co_consts=constants)!=r['counter_init'] for r in references.values()),
        'MRO_CONTRACT_EXECUTABLE_CONSTANT_MUTATION_REJECTED')
    return dict(state='PASS_METADATA_BUILDER_SNAPSHOT_MRO8_NOT_FULL_CONNECTION_OR_NATIVE',contracts=8,
        actual_small_source_reads=reader.read_passes,snapshot=stats,exact_fresh_compilation_matches=matched,
        compilation_variants_source_code_equal=references['full_module']['fresh_source']==references['private_non_import_AST']['fresh_source'],
        actual_product_or_Native_executed=False)


def main():
    import argparse,os,re,threading,time,traceback
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    if '--check-report-encoding' in sys.argv[1:]:
        require(sys.argv[1:]==['--check-report-encoding'],'ONLY_ENCODING_CONTRACT_MODE')
        import accept_case112_current_epoch as a
        import current_stored_runtime_scope as scope
        print(json.dumps(encoding_contracts(scope,a.exact),allow_nan=False));return 0
    if '--check-source-mro' in sys.argv[1:]:
        require(sys.argv[1:]==['--check-source-mro'],'ONLY_SOURCE_MRO_CONTRACT_MODE')
        import single_snapshot_source_guard_v1 as snapshot
        raw=(c.ROOT/snapshot.ORIGINAL_PIN['path']).read_bytes()
        print(json.dumps(source_mro_contracts(c.ROOT,snapshot,raw),allow_nan=False));return 0
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen':denied.append(1);raise ValueError('FULL73_METADATA_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    boot,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=boot.native009_full72_construction_v1
    # Construction's13 fixed libraries suffice for the fresh reader/graph.
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,imports=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--generation',type=int,choices=(1,2),default=1)
    arguments=parser.parse_args();attempt=arguments.attempt;generation=arguments.generation
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_ATTEMPT')
    output=PREFIX+(f'native009-full73-metadata{attempt:03}.v1.json' if generation==1 else
        f'native009-full73-metadata-g{generation:03}-attempt{attempt:03}.v1.json')
    native=c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not(c.ROOT/output).exists() and not native.exists(),'EXCLUSIVE_REPORT_AND_NO_NATIVE009')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic();phase='CURRENT_ADMISSION';binding_state=metadata=shared=None
    original_check=guard.check;progress_state=dict(sample=0,last=started)
    def checkpoint(force=False):
        original_check(force=force)
        count=len(guard.samples)
        if count==progress_state['sample']:return
        progress_state['sample']=count;now=time.monotonic()
        if now-progress_state['last']<30:return
        progress_state['last']=now;sample=guard.samples[-1]
        print(json.dumps(dict(progress=True,phase=phase,elapsed_seconds=round(now-started,2),
            metadata_read_passes=0 if metadata is None else metadata.read_passes,
            metadata_inputs=0 if metadata is None else len(metadata.snapshots),
            system_CPU=sample['system_cpu_percent'],owned_CPU=sample.get('parent_cpu_machine_percent'),
            available_RAM_percent=sample['available_ram_percent'])),flush=True)
    # Passive progress over the same already-sampled Guard; no extra observer.
    guard.check=checkpoint
    row=dict(state='FAILED_FULL73_ACTUAL_PARENT_METADATA_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        diagnostic_generation=generation,diagnostic_attempt=attempt,
        actual_product_or_Native_executed=False,actual_Native_Frame_created=False,preparation_CPU_policy_changed=False,
        whole_Native_source_or_product_acceptance_qualified=False,current_result_and_future_sources_must_be_recosted=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        row['producer_source_pin']=q.pin(SELF)
        parent_proof=a.read_exact(q,PARENT_PROOF)
        a.exact(q.pin(FAILED_METADATA['path']),FAILED_METADATA,'ORIGINAL_MISSING_SHARED_CONNECTION_FAILURE')
        a.exact(q.pin(CPU_STOP['path']),CPU_STOP,'ORIGINAL_CPU_STOP_NOT_REUSED_AS_COMPLETION')
        a.exact(q.pin(STRUCTURE_STOP['path']),STRUCTURE_STOP,'ORIGINAL_FACTORY_INTERFACE_REJECTION')
        a.exact(q.pin(EXISTING_SNAPSHOT_STOP['path']),EXISTING_SNAPSHOT_STOP,'ORIGINAL_DUPLICATE_SNAPSHOT_REJECTION')
        a.exact(q.pin(CODE_IDENTITY_STOP['path']),CODE_IDENTITY_STOP,'ORIGINAL_EXISTING_CODE_IDENTITY_REJECTION')
        review=q.json(PUBLICATION_REVIEW)
        a.fields(review,dict(state='FAILED_RESULT_PUBLICATION_REVIEW_NOT_RUNTIME_OR_NATIVE_ACCEPTANCE',
            expected_original_output_absent_after_terminal_exit=True,process_exit_code=1,
            unchanged_publisher_limit_bytes=262144,inner_final_qualification_outcome_not_recoverable=True,
            accepted_count_delta=0,GO_authorized=False),'FAILED_PUBLICATION_REVIEW_NOT_RUNTIME_AUTHORITY')
        a.fields(parent_proof,dict(state='PASS_FULL73_PARENT_LAUNCH_JOB_FRAME_AND_ORACLE25_WITH_REPLAYABLE_DECLARED_COST_NOT_NATIVE',
            contracts=dict(run=25,errors=0,failures=0,skipped=0),semantic_inputs=3223,fresh_inputs=392,final_fresh_hashes=392,
            actual_parent_attempts=0,actual_worker_calls=0,actual_Frame_instances=0,subprocess_creation_attempts=0,
            previous_scope_and_budget_exactly_reconstructed=True,persisted_scope_uses_original_noninjecting_union=True,
            cleanup_confirmed=True),'CURRENT_REPLAYABLE_PARENT_COMPOSITION25')
        pins=scope.pins(parent_proof['source_pins'])
        for pin in pins.values():
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']),pin,'ALL_QUALIFIED_CURRENT_CODE')
        for pin in [CONSTRUCTION]+construction.PINS:a.exact(q.pin(pin['path']),pin,'CORE_GRAPH_SOURCES')
        names,_=loader.load(c.ROOT,[pins[QUALIFIER]],{})
        upstream=names.qualify_native009_full73_parent_v1
        extra,_=loader.load(c.ROOT,upstream.READINESS,{})
        modules,_=loader.load(c.ROOT,[pins[upstream.ENTRY],pins[upstream.PARENT],construction.DECLARATION],{})
        entry=modules.native009_full73_worker_entry_v1;parent=modules.native009_parent_launch_v1
        base=a.read_exact(q,parent_proof['declared_scope_base_pin'])
        inherited=scope.extend(scope.pins(base['input_pins']),{parent_proof['declared_scope_base_pin']['path']:parent_proof['declared_scope_base_pin']})
        inherited=scope.extend(inherited,scope.pins(parent_proof['declared_scope_delta_pins']))
        graph_pin=pins[PREFIX+'successor-native009-full73-graph005.v1.json']
        prepared=a.read_exact(q,graph_pin);hint=a.read_exact(q,entry.HINT)
        a.exact(entry.HINT,prepared['bootstrap_pin'],'CURRENT_V4_HINT');a.exact(entry.WIRE,prepared['capsule_pin'],'CURRENT_V4_WIRE')
        transport,_=loader.load(c.ROOT,[entry.TRANSPORT],{})
        facade=NS(connect=transport.native009_full73_transport_v1.connect,constant=libs.native009_full72_transport_v1.constant)
        source=libs.native009_verified_source_profile_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a,q,hint,facade)
        pin,raw=q._read(entry.WIRE['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,entry.WIRE,'EXACT_PACKET')
        api=source.api;graph,_=api.reconstruct(hint,bytes(raw),guard.check);del raw
        inherited,_=graph.binding.semantic_union(inherited,guard.check)
        a.exact(len(inherited),parent_proof['semantic_inputs'],'COMPLETE_PREVIOUS_SCOPE')
        original_union=type(graph.binding).semantic_union
        modules.native009_parent_scope_v1.inherit_declaration(graph,inherited,scope)
        launch=entry.launch_api(c.ROOT,loader)
        proxy,context=parent.recovery_api(libs.post_product_recovery_connection_v1,c.ROOT,q.snapshots[upstream.ENTRY],launch,
            extra.worker_readiness_v1,extra.worker_readiness_connection_v1,c)
        built=api.build(c.ROOT,loader,api,graph,envelope.prior,proxy,libs.post_product_recovery_window_v1,guard.check)
        old_budget=graph.binding.runtime_budget(inherited,parent_proof['inventory_requests'],built.window.DIRECT.runtime_budget,guard.check)
        a.exact(old_budget,parent_proof['original_complete_runtime_budget'],'ENTIRE_PREVIOUS_COST')
        a.exact(q.pin(upstream.SNAPSHOT['path']),upstream.SNAPSHOT,'EXACT_QUALIFIED_FRESH_SOURCE_SNAPSHOT_HELPER')
        snapshots,_=loader.load(c.ROOT,[upstream.SNAPSHOT],{'audit_evidence_io':original_io})
        snapshot=snapshots.single_snapshot_source_guard_v1
        pin,raw=q._read(snapshot.ORIGINAL_PIN['path'],parse=True);q._bind(pin['path'],pin)
        a.exact(pin,snapshot.ORIGINAL_PIN,'UNCHANGED_AUDIT_SOURCE_FOR_LEAF_OPTIMIZATION')
        source_snapshot_raw=bytes(raw);del raw
        pin,raw=q._read(SNAPSHOT_SOURCE['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,SNAPSHOT_SOURCE,'CURRENT_SNAPSHOT_REFERENCE_SOURCE')
        source_references=compiled_snapshot_references(bytes(raw));del raw
        configuration_pin=inherited['tools/p09/current_queue_successor_lossless_runtime_v4.py']
        a.exact(q.pin(configuration_pin['path']),configuration_pin,'EXACT_EXISTING_LOSSLESS_CONFIGURATION')
        configurations,_=loader.load(c.ROOT,[configuration_pin],{})
        configuration=configurations.current_queue_successor_lossless_runtime_v4
        for pin in configuration.PINS[1:]:a.exact(q.pin(pin['path']),pin,'EXACT_EXISTING_SHARED_READER_COMPONENT')
        components,_=loader.load(c.ROOT,configuration.PINS[1:],{})
        configuration.configure(api.runtime,components)
        row['lossless_configuration_source_pin']=configuration_pin
        connected=construction.construct(c.ROOT,loader,api,graph,built,envelope,libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1,a,q,scope,inherited,prepared,graph_pin,guard.check)
        context.bind_parent(connected.parent_state)
        helpers=construction.helper_inventory(c.ROOT,connected.parent)
        require(helpers['Native_count']<=64,'ACTUAL_HELPER64_BEFORE_METADATA')
        row['helper_inventory_before_metadata']=helpers
        build=connected.original_run.__globals__['build']
        # The real configured Frame MRO carries the very same shared owner.
        owners=[]
        for cls in connected.frame.__mro__:
            fn=vars(cls).get('__init__')
            if callable(fn) and getattr(fn,'__closure__',None) and fn.__code__.co_filename.replace('\\','/').endswith('shared_metadata_frame_decoder_budget_v1.py'):
                cells=dict(zip(fn.__code__.co_freevars,(cell.cell_contents for cell in fn.__closure__)))
                if 'shared' in cells:owners.append(cells['shared'])
        require(len(owners)==1,'ONE_ORIGINAL_FRAME_SHARED_OWNER');shared=owners[0]
        require(shared.metadata is None and shared.frame is None,'FRESH_UNEXECUTED_SHARED_BUDGET')
        phase='ACTUAL_ORIGINAL_PARENT_METADATA_CALLBACK'
        metadata=build.BuildReader(c.ROOT,guard.check)
        row['original_metadata_reader_interface']=dict(class_name=type(metadata).__name__,
            MRO_class_names=[cls.__name__ for cls in type(metadata).__mro__],
            source_owner_class_names=[cls.__name__ for cls in type(metadata).__mro__ if vars(cls).get('_source') is type(metadata)._source],
            original_allocator_name=getattr(type(metadata).__new__,'__name__',None))
        row['existing_source_code_comparison']={}
        row['metadata_builder_source_snapshot_connection']=adopt_source_snapshot(metadata,snapshot,source_snapshot_raw,
            row['existing_source_code_comparison'],source_references)
        del source_snapshot_raw
        metadata.pacer=bytes_policy.OwnedPacer()
        owner=NS(lock=threading.Lock(),samples=guard.samples,checkpoint_io=guard.check)
        binding_state=build.pressure.PreSaturationReadCheckpoint(metadata,owner)
        require(shared.metadata is metadata._lossless_metadata_router.budget and shared.frame is None,'REAL_READER_REGISTERED_IN_FRAME_SHARED_OWNER')
        phase='EARLY_CURRENT_SCOPE_COST_BEFORE_WHOLE_METADATA'
        early_required=scope.extend(connected.oracle_inherited,q.snapshots)
        early_required,_=graph.binding.semantic_union(early_required,guard.check)
        early_inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        early_requests=[]
        def early_paced():early_requests.append(1);q.open_pacer.reserve()
        early_rust=early_inventory.rust_inputs(c.ROOT,early_paced)
        require(len(early_rust)==787 and set(early_rust)<=set(early_required),'CURRENT_EARLY_RUST787_BEFORE_COST')
        early_budget=graph.binding.runtime_budget(early_required,len(early_requests),built.window.DIRECT.runtime_budget,guard.check)
        early_total=early_budget['predicted_runtime_combined_seconds']+15
        row.update(early_current_declared_budget=early_budget,early_declared_inputs=len(early_required),
            early_predicted_complete_seconds_with_readiness=early_total,early_current_inventory_requests=len(early_requests),
            early_cost_is_not_full_metadata_or_Native_acceptance=True)
        require(early_total<600,'CURRENT_KNOWN_SCOPE_ALREADY_OUTSIDE600_BEFORE_WHOLE_METADATA')
        phase='ACTUAL_ORIGINAL_PARENT_METADATA_CALLBACK'
        require(connected.original_run is built.engine.run_owned,'SAME_WHOLE_ORIGINAL_ENGINE_FUNCTION')
        actual_callback=connected.original_run.__globals__['binding']
        required,rust=actual_callback(metadata)
        a.exact(sorted(early_rust),sorted(rust),'SAME_REAL_RUST_SET_BEFORE_AND_AFTER_CALLBACK')
        require(len(connected.callback_calls)==1 and len(rust)==787,'ONE_REAL_WHOLE_CALLBACK_AND_RUST787')
        for descriptor in graph.binding.descriptors():
            pin=descriptor['semantic_original_pin'];a.exact(metadata.pin(pin['path']),pin,'ALL73_REAL_SEMANTIC_PINS')
        require(len(graph.binding.descriptors())==73,'ALL73_CURRENT_BINDINGS')
        phase='ACTUAL_METADATA_CLOSING_HASHES';metadata.finish()
        require(metadata.final_fresh_hashes==len(metadata.snapshots)>0,'EVERY_REAL_METADATA_INPUT_FINAL_HASHED')
        routed=metadata._lossless_metadata_router
        require(set(routed.counts)==set(graph.binding.originals) and all(n>=2 for n in routed.counts.values()),'ALL73_FRESH_FIRST_AND_FINAL_DECODE')
        after=construction.helper_inventory(c.ROOT,connected.parent)
        a.exact(after,helpers,'NO_LATE_PROJECT_HELPER_DRIFT')
        required=scope.extend(required,connected.oracle_inherited);required=scope.extend(required,q.snapshots)
        required=scope.extend(required,metadata.snapshots);required,_=graph.binding.semantic_union(required,guard.check)
        require(all(required.get(n)==pin for n,pin in inherited.items()),'NO_PREVIOUS_SCOPE_REMOVED')
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        a.exact(sorted(inventory.rust_inputs(c.ROOT,paced)),sorted(rust),'FRESH_CURRENT_RUST_INVENTORY')
        budget=graph.binding.runtime_budget(required,len(requests),built.window.DIRECT.runtime_budget,guard.check)
        total=budget['predicted_runtime_combined_seconds']+15
        _,delta=upstream.compact_scope(graph.binding,original_union,scope,base,parent_proof['declared_scope_base_pin'],required,guard.check,a.exact)
        row.update(semantic_inputs=len(required),metadata_fresh_inputs=len(metadata.snapshots),metadata_final_fresh_hashes=metadata.final_fresh_hashes,
            actual_metadata_read_passes=metadata.read_passes,actual_metadata_physical_bytes=metadata.bytes_read,
            actual_metadata_source_pins_compact=compact_pin_map(required,metadata.snapshots,scope,a.exact),
            actual_metadata_pin_map_losslessly_reconstructed=True,metadata_pressure=build.pressure_summary(binding_state),
            metadata_source_predicate_optimization=metadata.source_snapshot_diagnostics(),
            original_whole_parent_callback_executions=len(connected.callback_calls),descriptor_count=73,
            all73_fresh_first_and_final_decodes=True,shared_decoder=shared.evidence(),helper_inventory_after_metadata=after,
            previous_scope_and_budget_exactly_reconstructed=True,original_complete_runtime_budget=budget,
            predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600,
            current_Rust_path_count=len(rust),inventory_requests=len(requests),additional_readiness_seconds_without_old_credit=15,
            declared_scope_base_pin=parent_proof['declared_scope_base_pin'],declared_scope_delta_pins=delta)
        phase='FINAL_QUALIFIER_HASHES';q.finish();guard.check(force=True)
        require(context.jobs==context.attempts==len(connected.parent_state.frames)==built.state.calls==0 and not denied and not native.exists(),'NO_NATIVE_FRAME_JOB_WORKER_OR_PRODUCT')
        require(total<600,'COMPLETE_DECLARED_SCOPE_PLUS_READINESS_OUTSIDE600')
        row.update(state='PASS_FULL73_ACTUAL_PARENT_METADATA_AND_SHARED_DECODER_NOT_NATIVE_FRAME_OR_PRODUCT',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        if metadata is not None:
            row['partial_metadata_diagnostics']=dict(read_passes=metadata.read_passes,physical_bytes=metadata.bytes_read,
                input_count=len(metadata.snapshots),final_fresh_hashes=metadata.final_fresh_hashes,
                not_a_complete_hash_or_Native_or_product_claim=True)
            if callable(getattr(metadata,'source_snapshot_diagnostics',None)):
                row['partial_metadata_diagnostics']['source_predicate_snapshot']=metadata.source_snapshot_diagnostics()
        if binding_state is not None:binding_state.restore()
        if shared is not None:shared.restore()
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
        row['last_original_resource_samples']=[{k:s.get(k) for k in ('time_utc','system_cpu_percent','parent_cpu_machine_percent',
            'available_ram_percent','commit_used_percent','parent_private_mib')} for s in guard.samples[-8:]]
    require(guard.cleanup,'OWNER_CLEANUP')
    try:libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    except ValueError as error:
        if error.args!=('CURRENT_EPOCH_ACCEPT_WORKSPACE_BOUNDED_RECEIPT',):raise
        # Preserve a terminal failure rather than lose the result again. This
        # intentionally cannot stand in for the detailed whole-input proof.
        failure=dict(state='FAILED_BOUNDED_METADATA_RESULT_PUBLICATION_NOT_ACCEPTED',accepted_count_delta=0,
            GO_authorized=False,actual_product_or_Native_executed=False,actual_Native_Frame_created=False,
            producer_source_pin=row.get('producer_source_pin'),cleanup_confirmed=guard.cleanup,
            full_detailed_result_not_published=True,original_publisher_limit_bytes=262144,
            elapsed_seconds=row.get('elapsed_seconds'),operation_phase=row.get('operation_phase'))
        libs.successor_preparation_workspace_v1.publish(c.ROOT,output,failure,a)
        print(json.dumps(failure,allow_nan=False));return 1
    print(json.dumps({k:row.get(k) for k in ('state','semantic_inputs','metadata_fresh_inputs','metadata_final_fresh_hashes','fresh_inputs','final_fresh_hashes',
        'predicted_complete_seconds_with_readiness','shared_decoder','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max',
        'RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
