"""Uninstalled exact162 zlib mapping and fresh-file qualification.

Reuse the original Projection body and v2 bounded-output decoder. Only its
private descriptor dependency selects the closed, independently pinned table.
No live Native Frame, product/GO, old manifest mutation or scope admission.
"""
import copy
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/batch_zlib_mapping.py'
TEST='tools/p09/tests/test_batch_zlib_mapping.py'
COMPARISON=dict(path='implementation/p09/evidence/p09-361-case165-batch-decoder-zlib-comparison-run010-attempt001.v1.json',
    bytes=129898,sha256='ff2589bdd5957fc645205e018a5e4317ba31389768f4759e5c5abe35c79ab687')
CODEC1=dict(path='tools/p09/runtime_record_envelope_v1.py',bytes=3596,
    sha256='59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5')
PREFIX='implementation/p09/evidence/p361-lossless-runtime-inputs/'
SCHEMA='hwpx-agent.p09-lossless-runtime-source-projection/v1'


def require(ok,code):
    if not ok:raise ValueError('BATCH_ZLIB_'+code)


def rows_from_comparison(report,originals,scope,exact):
    require(report.get('state')=='FAILED_BASELINE_AND_UNADOPTED_ZLIB_MEMORY_CANDIDATE_NOT_NATIVE'
        and report.get('GO_authorized') is False and report.get('candidate_physical_files_published') is False,
        'EXACT_UNADOPTED_COMPARISON')
    candidate=report['candidate'];exact(candidate['codec_pin'],CODEC1,'EXACT_EXISTING_ENCODER')
    require(candidate['state']=='PASS_FULL162_ZLIB_MEMORY_COMPARISON_NOT_ADOPTED_OR_NATIVE'
        and candidate['completed_mappings']==162 and len(originals)==162
        and len(candidate['mapping_records'])==162,'ALL162_NOT_A_SUBSET')
    result=[]
    for index,(record,original) in enumerate(zip(candidate['mapping_records'],originals),1):
        old=scope.pins([record['semantic_pin']])[record['semantic_pin']['path']]
        require(old['path'].startswith('implementation/p09/evidence/') and old['path'].endswith('.json'),
            'RECEIPTS_ONLY_NOT_CODE_EXE_OR_FIXTURE')
        exact(old,original['semantic_original_pin'],'SAME_DECLARED_SEMANTIC_ORIGINAL')
        exact(record['old_physical_pin'],original['physical_envelope_pin'],'SAME_OLD_PHYSICAL_ORIGINAL')
        new=dict(path=PREFIX+f'case165-zlib-g001-{index:03}.envelope.v1.json',
            bytes=record['candidate_encoded_bytes'],sha256=record['candidate_sha256'])
        exact(scope.pins([new])[new['path']],new,'VALID_TYPED_NEW_PHYSICAL_PIN')
        require(0<new['bytes']<=16*1024*1024,'ORIGINAL_CODEC16M_BOUND')
        result.append(dict(schema_version=SCHEMA,next_case=165,semantic_original_pin=old,physical_envelope_pin=new))
    require(len({r['semantic_original_pin']['path'] for r in result})==162
        and len({r['physical_envelope_pin']['path'] for r in result})==162,'UNIQUE_FULL162')
    return result


def projection_factory(source,codec,rows,exact):
    """Keep every Projection method and the original codec dependency intact."""
    require(source.SCHEMA==SCHEMA and len(rows)==162,'EXACT_SOURCE_SCHEMA_AND162')
    env=source.Projection.__init__.__globals__
    require(env.get('__name__','').startswith('p09_exact_') and env.get('descriptor') is source.descriptor
        and source.codec is codec and env['codec'] is codec
        and not any(getattr(m,'__dict__',None) is env for m in tuple(sys.modules.values()) if m),
        'PRIVATE_ORIGINAL_SOURCE_AND_V2_CODEC')
    methods=dict(vars(source.Projection));table=copy.deepcopy(rows)
    for index,row in enumerate(table,1):
        require(set(row)=={'schema_version','next_case','semantic_original_pin','physical_envelope_pin'}
            and row['schema_version']==SCHEMA and type(row['next_case']) is int and row['next_case']==165,
            'CLOSED_EXACT_DESCRIPTOR_CONTEXT')
        old=source.copy_pin(row['semantic_original_pin']);new=source.copy_pin(row['physical_envelope_pin'])
        require(old['path'].startswith('implementation/p09/evidence/') and old['path'].endswith('.json')
            and new['path']==PREFIX+f'case165-zlib-g001-{index:03}.envelope.v1.json'
            and 0<new['bytes']<=codec.MAX_BYTES,'ONLY_EXPLICIT_RECEIPT_AND_GENERATION')
    expected={r['semantic_original_pin']['path']:r for r in table}
    require(len(expected)==162,'EXACT_UNIQUE_SEMANTIC_TABLE')
    original=source.descriptor
    def descriptor(old,new,*,next_case):
        require(type(next_case) is int and next_case==165,'EXACT_CASE165')
        old,new=source.copy_pin(old),source.copy_pin(new)
        require(old['path'] in expected,'ONLY_CLOSED162_NOT_OTHER_INPUTS')
        row=expected[old['path']]
        exact(old,row['semantic_original_pin'],'EXACT_EXPECTED_ORIGINAL')
        exact(new,row['physical_envelope_pin'],'EXACT_EXPECTED_NEW_CARRIER')
        return copy.deepcopy(row)
    source.descriptor=env['descriptor']=descriptor
    require(all(vars(source.Projection).get(name) is value for name,value in methods.items()),
        'ALL_ORIGINAL_PROJECTION_METHODS_RETAINED')
    def project(required,checkpoint):
        return source.Projection(required,copy.deepcopy(table),next_case=165,checkpoint=checkpoint)
    return NS(project=project,source=source,rows=copy.deepcopy(table),original_descriptor=original,
        original_Projection_class_and_all_methods_retained=True,installed_in_product=False)


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.dont_write_bytecode=True
    require(not sys.argv[1:],'NO_EXTRA_ARGUMENTS')
    def audit(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile'):raise ValueError('BATCH_ZLIB_PROCESS_DENIED')
    sys.addaudithook(audit)
    import ast
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import batch_engine_connection as entry,owned_source_read_pressure as byte_policy
    bootstrap=entry.bootstrap_loader(c.ROOT);guards,_=bootstrap.load(c.ROOT,list(entry.BOOTSTRAP[1:]),{})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    guard=guards.owned_cpu_baseline_v1.guard_type(guards.terminal_metadata_pressure_v1.guard_type(
        guards.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    source=old_reader=generated=fresh=shared=None;budgets={};published=[];created=reused=0;stage='CONSTRUCTION'
    started=time.monotonic();row=dict(state='FAILED_ZLIB_FILES_AND_V2_DIRECT_BUDGET_NOT_ADOPTED',
        GO_authorized=False,accepted_count_delta=0,actual_Native_Frame_created=False,
        actual_product_or_worker_executed=False,installed_in_product=False)
    try:
        guard.acquire();source=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,entry.SELF):source.pin(name)
        for pin in entry.BOOTSTRAP:a.exact(source.pin(pin['path']),pin,'ORIGINAL_BOOTSTRAP')
        report=a.read_exact(source,COMPARISON)
        libraries,_=entry.planning_libraries(c.ROOT,source,a,bootstrap)
        admission,batch,reuse=(getattr(libraries,n) for n in ('batch_scope_admission','batch_verification','verification_reuse'))
        data=admission.read_plan(source,a,batch,reuse);entry.extend_execution(data,source,batch)
        config_pin=data.planned.logical['tools/p09/current_queue_successor_lossless_runtime_v4.py']
        loader=batch.PacedNamespaceLoader(bootstrap,source,{config_pin['path']:config_pin}).api
        config,_=loader.load(c.ROOT,[config_pin],{})
        entry.private_package_imports(admission,libraries.batch_worker_entry,bootstrap,
            config.current_queue_successor_lossless_runtime_v4)
        connected=admission.connect_package(c.ROOT,source,data,a,batch,byte_policy)
        binding=connected.graph.binding;originals=entry.current_mappings(binding,data.planned.current)
        rows=rows_from_comparison(report,originals,batch.scope,a.exact)
        names=('runtime_record_envelope_v1','runtime_record_envelope_v2','runtime_envelope_source_projection_v1',
            'native009_parent_scope_v1')
        modules,_=connected.loader.load(c.ROOT,[connected.known['tools/p09/'+n+'.py'] for n in names],
            {'current_stored_runtime_scope':batch.scope})
        a.exact(connected.known[CODEC1['path']],CODEC1,'SAME_PINNED_CODEC_ENCODER')
        codec=modules.runtime_record_envelope_v2
        mapping=projection_factory(modules.runtime_envelope_source_projection_v1,codec,rows,a.exact)
        required=entry.current_logical(data,binding,guard.check,batch.scope,a.exact)
        # These two named runtime/test sources are prospective additions only.
        required=batch.scope.extend(required,{n:dict(source.pin(n)) for n in (SELF,TEST)})
        projection=mapping.project(required,guard.check)
        before,_=binding.project(required,guard.check)
        a.exact(dict(before.semantic_pins),dict(projection.semantic_pins),'ALL_SEMANTIC_INPUTS_UNCHANGED')
        a.exact(len(before.physical_pins),len(projection.physical_pins),'BIJECTIVE_FULL_SOURCE_COUNT')
        view_pin=connected.known['tools/p09/held_native_read_views_v1.py']
        pin,raw=source._read(view_pin['path'],parse=True);source._bind(pin['path'],pin);a.exact(pin,view_pin,'WHOLE_ORIGINAL_COST_SOURCE')
        model=next(n for n in ast.parse(bytes(raw)).body if isinstance(n,ast.FunctionDef) and n.name=='model')
        env=dict(require=a.require);exec(compile(ast.fix_missing_locations(ast.Module(body=[model],type_ignores=[])),view_pin['path'],'exec'),env)
        screen=admission.early_budget({n:dict(p) for n,p in projection.physical_pins.items()},batch.scope,NS(model=env['model']))
        source.finish();guard.check(force=True)
        row.update(source_pins=list(source.snapshots.values()),source_fresh=len(source.snapshots),source_final=source.final_fresh_hashes,
            descriptors=rows,prospective_current_inputs=len(projection.physical_pins),conservative_cost_screen=screen,
            final_manifest_wire_bootstrap_and_live_Native_cost_qualified=False,
            original_Projection_class_and_all_methods_retained=True,bounded_output_decoder='runtime_record_envelope_v2')
        original=connected.graph.frames.connection.original.DecoderBudget
        old_budget=original(guard.check);old_reader=a.AcceptanceReader(c.ROOT,guard.check)
        generated=a.AcceptanceReader(c.ROOT,guard.check)
        write_pacer=byte_policy.OwnedPacer();publish_policy=NS(OwnedPacer=lambda:write_pacer)
        stage='BUILD_FILES'
        for index,(old,new) in enumerate(zip(originals,rows),1):
            guard.check();target=new['physical_envelope_pin']
            if (c.ROOT/target['path']).exists():
                a.exact(generated.fresh_pin(target['path']),target,'ONLY_EXACT_EXISTING_CANDIDATE_REUSED');reused+=1
            else:
                pin=old['physical_envelope_pin'];actual,raw=old_reader._read(pin['path'],parse=True);old_reader._bind(actual['path'],actual)
                a.exact(actual,pin,'FRESH_OLD_CARRIER');raw=bytes(raw)
                decoded=old_budget.run(lambda check:before.decode_fresh(old['semantic_original_pin']['path'],actual,raw,check))
                encoded=codec.encode(decoded,guard.check)
                a.exact(dict(bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest()),
                    {k:target[k] for k in ('bytes','sha256')},'SAME_MEASURED_CANDIDATE_BYTES')
                published_pin=modules.native009_parent_scope_v1.publish_bytes(c.ROOT,target['path'],encoded,generated,
                    guard,publish_policy,a,codec.MAX_BYTES)
                a.exact(published_pin,target,'EXACT_NEW_CANDIDATE_FILE');created+=1
                del decoded,encoded,raw
            published.append(dict(target))
            if index%32==0:print(json.dumps(dict(progress=stage,completed=index,created=created,reused=reused)),flush=True)
        old_reader.finish();generated.finish();guard.check(force=True)
        row['generation']=dict(created=created,reused=reused,published=len(published),
            old_fresh=len(old_reader.snapshots),old_final=old_reader.final_fresh_hashes,
            new_fresh=len(generated.snapshots),new_final=generated.final_fresh_hashes,
            written_bytes=write_pacer.bytes_by_kind['other'],one_original_write_pacer_for_all_files=True)
        shared=connected.metadata_libraries.shared_metadata_frame_decoder_budget_v1.SharedBudget()
        for role in ('metadata','frame'):budgets[role]=shared.attach(role,original(guard.check))
        fresh=a.AcceptanceReader(c.ROOT,guard.check);stage='FRESH_FILE_DECODES'
        for role in ('metadata','frame'):
            for number in (1,2):
                for index,descriptor in enumerate(rows,1):
                    guard.check();pin=descriptor['physical_envelope_pin'];semantic=descriptor['semantic_original_pin']
                    actual,raw=fresh._read(pin['path'],parse=True);fresh._bind(actual['path'],actual)
                    a.exact(actual,pin,'FRESH_ACTUAL_CANDIDATE_CARRIER');raw=bytes(raw)
                    decoded=budgets[role].run(lambda check:projection.decode_fresh(semantic['path'],actual,raw,check))
                    del decoded,raw
                    if index%32==0:print(json.dumps(dict(progress=stage,role=role,pass_number=number,completed=index)),flush=True)
        fresh.finish();guard.check(force=True)
        require(all(b.completed==324 for b in budgets.values()) and fresh.final_fresh_hashes==162,'ALL648_AND162_CLOSING')
        row['state']='PASS_ZLIB_FILES_AND_V2_DIRECT_BUDGET_NOT_ADOPTED_OR_NATIVE'
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError) as error:
        row.update(error_type=type(error).__name__,failure_stage=stage)
        if stage=='BUILD_FILES' and 'target' in locals():row['last_build_target']=target['path']
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        import traceback
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        guard.close()
        row.update(created_files=created,reused_files=reused,published_count=len(published),cleanup_confirmed=guard.cleanup,
            elapsed_seconds=time.monotonic()-started,system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_max=max((s.get('parent_cpu_machine_percent') or 0 for s in guard.samples),default=None),
            private_MiB_max=max((s['parent_private_mib'] for s in guard.samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
        if shared is not None:
            try:row['direct_role_budget_evidence']=shared.evidence()
            finally:shared.restore()
        if fresh is not None:row['physical_reader']=dict(fresh_inputs=len(fresh.snapshots),final_fresh_hashes=fresh.final_fresh_hashes,
            read_passes=fresh.read_passes,physical_bytes_read=fresh.bytes_read)
        print(json.dumps(row))
    return 0 if row['state'].startswith('PASS_') and guard.cleanup is True else 2


if __name__=='__main__':raise SystemExit(main())
