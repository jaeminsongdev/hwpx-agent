"""New parent graph and exact zlib scope, construction only and always NO-GO.

The original engine, callback, shared Frame and independent checker bodies
are reused. Preparation does not replay the corpus or whole-boundary audit.
The connected launch selects only the already-qualified zlib EOF diagnostic.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/batch_zlib_engine.py'
TEST='tools/p09/tests/test_batch_zlib_engine.py'
GRAPH='implementation/p09/evidence/p09-361-case165-successor-run010-zlib-graph001.v1.json'
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
ENGINE=dict(path='tools/p09/batch_engine_connection.py',bytes=26089,
    sha256='1559a74eb6e19761ce62d46e1bc9ecef06f613b076742ac974945481f2494262')
PROFILE=dict(path='tools/p09/batch_zlib_runtime.py',bytes=6690,
    sha256='93ac8ed05a3fb0032746eb66294b753da60ca2184b6427c4d9bd9da9c6605435')


def require(ok,code):
    if not ok:raise ValueError('ZLIB_ENGINE_'+code)


def canonical(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')


def bootstrap(root):
    path=root/LOADER['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_LOADER')
    for parent in (path.parent,*path.parent.parents):
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),'DIRECT_LOADER_ANCESTORS')
        if parent==root:break
    with path.open('rb') as stream:raw=stream.read(LOADER['bytes']+1)
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_LOADER')
    env=dict(__name__='p09_exact_zlib_parent_loader',__file__=LOADER['path'])
    exec(compile(raw,LOADER['path'],'exec'),env)
    loader=NS(**env);modules,_=loader.load(root,[ENGINE,PROFILE],{})
    return loader,modules.batch_engine_connection,modules.batch_zlib_runtime


def source_table(data,q,entry,profile,scope):
    """Original producer64 plus named current sources, never observed union."""
    names=tuple(dict.fromkeys(entry.EXECUTION_INPUTS+profile.CODE+(profile.SELF,SELF)))
    additions={n:dict(q.pin(n)) for n in names}
    sources=scope.extend(data.package_sources,additions)
    for name,expected in sources.items():require(q.pin(name)==expected,'EXACT_GRAPH_SOURCE_BEFORE_CONSTRUCTION')
    return sources


def graph_record(data,sources,profile):
    row=copy.deepcopy(data.report)
    row.update(preparation_report_generation=3,manifest_pin=dict(profile.PACKAGE[0]),
        capsule_pin=dict(profile.PACKAGE[1]),bootstrap_pin=dict(profile.PACKAGE[2]),
        source_pins=[dict(sources[n]) for n in sorted(sources)],fresh_inputs=len(sources),final_fresh_hashes=len(sources),
        cleanup_confirmed=False,reference_producer64_source_pins=copy.deepcopy(data.report['source_pins']),
        zlib_binding_qualification_pin=dict(profile.QUALIFICATION),
        exact_current_graph_sources_not_former_runtime_requalification=True)
    return row


def project_plan(data,manifest,additions,batch,checkpoint):
    """Preserve all old semantics and the exact cold set; replace carriers."""
    scope=batch.scope;old=data.declared;prior=data.planned
    before=data.manifest['descriptors'];after=manifest['descriptors']
    require(type(before) is list and type(after) is list and len(before)==len(after)==162,'WHOLE162_SCOPE_TABLE')
    require([r['semantic_original_pin'] for r in before]==[r['semantic_original_pin'] for r in after],
        'EVERY_ORIGINAL_SEMANTIC_PIN_UNCHANGED')
    carriers={r['semantic_original_pin']['path']:dict(r['physical_envelope_pin']) for r in after}
    reverse={r['physical_envelope_pin']['path']:r for r in after}
    require(len(carriers)==len(reverse)==162,'BIJECTIVE_NEW_CARRIERS')
    def normalize(rows):
        result={}
        for name,pin in old.normalize(rows).items():
            checkpoint()
            if name in reverse:
                row=reverse[name];require(pin==row['physical_envelope_pin'],'EXACT_NEW_ALIAS_BEFORE_NORMALIZATION')
                pin=row['semantic_original_pin'];name=pin['path']
            require(name not in result or result[name]==pin,'NO_LOGICAL_ALIAS_CONFLICT')
            result[name]=dict(pin)
        return result
    def physical(rows):
        result={}
        for name,pin in normalize(rows).items():
            selected=carriers.get(name,pin)
            require(selected['path'] not in result or result[selected['path']]==selected,'NO_PHYSICAL_COLLISION')
            result[selected['path']]=dict(selected)
        return result
    logical_additions=normalize(list(additions.values()))
    physical_additions=physical(list(additions.values()))
    current=scope.extend(physical(list(prior.current.values())),physical_additions)
    whole=scope.extend(physical(list(prior.whole.values())),physical_additions)
    history=physical(list(prior.history.values()))
    require(history==prior.history,'EXACT_PRESERVATION_NOT_RECLASSIFIED')
    require(all(prior.current.get(r['physical_envelope_pin']['path'])==r['physical_envelope_pin'] for r in before),
        'ALL_OLD_CARRIERS_WERE_CURRENT')
    require(all(current.get(p['path'])==p for p in carriers.values()),'ALL_NEW_CARRIERS_EXACT_CURRENT')
    logical=scope.extend(normalize(list(prior.logical.values())),logical_additions)
    require(physical(list(logical.values()))==whole,'EXACT_FULL_LOGICAL_AND_PHYSICAL_SCOPE')
    policy=batch.Batch(whole,current,history,first_index=165,checkpoint=checkpoint)
    data.planned=NS(batch=policy,whole=whole,current=current,history=history,logical=logical)
    data.declared=NS(**{**vars(old),'normalize':normalize,'to_physical':physical})
    data.manifest=manifest
    return dict(original_semantic_pins_retained=162,physical_carriers_replaced=162,
        exact_preservation_retained=True,whole_inputs=len(whole),current_inputs=len(current),preservation_inputs=len(history))


def diagnostic_launch(launch,task,worker_path):
    """Only alter the factory's command to the qualified NO-GO zlib profile."""
    original=launch.connect
    def connect(root,pin,component,protocol,connection,factory,capture_type,subprocess,owned,checkpoint,**options):
        def selected(command,**kwargs):
            require(type(command) is list and len(command)==7
                and command[:3]==[sys.executable,'-B',str(root/worker_path)]
                and command[3]=='--ready-handle' and command[5:]==['--task',task],
                'EXACT_DIAGNOSTIC_PARENT_COMMAND')
            return factory([*command[:3],'--probe-no-go','--zlib',*command[3:]],**kwargs)
        return original(root,pin,component,protocol,connection,selected,capture_type,subprocess,owned,checkpoint,**options)
    return NS(**{**vars(launch),'connect':connect,'zlib_diagnostic_only':True})


def loader_for_parent(loader):
    def load(root,pins,reuse):
        modules,proof=loader.load(root,pins,reuse)
        if hasattr(modules,'batch_worker_launch'):
            worker=modules.batch_worker_launch;original=worker.launch_api
            def launch(actual_root,actual_loader):
                return diagnostic_launch(original(actual_root,actual_loader),worker.TASK,worker.SELF)
            modules=NS(**{**vars(modules),'batch_worker_launch':NS(**{**vars(worker),'launch_api':launch})})
        return modules,proof
    return NS(**{**vars(loader),'load':load})


def connect_package(root,q,data,graph,known,a,batch,profile,loader,byte_policy):
    libraries,_=loader.load(root,[known['tools/p09/native009_full72_construction_v1.py']],{})
    loader,_=libraries.native009_full72_construction_v1.private_runtime_imports(loader)
    names,_=loader.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('fixed162_worker_transport_v1','receipt_xz_envelope_v1','bounded_successor_capsule_wire_v2','batch_worker_entry')],{})
    api=names.fixed162_worker_transport_v1.connect(root,loader,batch.scope,byte_policy,names.receipt_xz_envelope_v1,
        names.bounded_successor_capsule_wire_v2,q.checkpoint,a.exact)
    def read(pin,limit):
        require(limit==16384 and pin['bytes']<=limit,'EXACT_ENTRY16K')
        before=q.maximum_parse_bytes
        try:
            q.maximum_parse_bytes=min(before,limit+1);actual,raw=q._read(pin['path'],parse=True);q._bind(actual['path'],actual)
        finally:q.maximum_parse_bytes=before
        a.exact(actual,pin,'REAL_FRESH_PARENT_ENTRY_BYTES');return bytes(raw)
    entry=profile.reconstruct(root,q,a,batch.scope,loader,known,api,names.bounded_successor_capsule_wire_v2,
        byte_policy,names.batch_worker_entry,graph,read)
    a.exact(entry.graph.binding.descriptors(),data.manifest['descriptors'],'PARENT_EXACT_NEW162')
    actual,raw=q._read(batch.RUNTIME,parse=True);q._bind(actual['path'],actual)
    a.exact(actual,known[batch.RUNTIME],'ORIGINAL_PARENT_SCOPE_SOURCE')
    runtime,_=batch.install_scope(entry.runtime,bytes(raw),data.planned.batch)
    return NS(graph=entry.graph,runtime=runtime,core=entry.core,known=known,loader=loader_for_parent(loader))


def main():
    import re,time,traceback
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.dont_write_bytecode=True
    require(sys.argv[1:] in (['--prepare-graph'],['--connect']),'CLOSED_NO_GO_MODES')
    prepare=sys.argv[1]=='--prepare-graph';denied=[]
    def audit(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile'):
            denied.append(event);raise ValueError('ZLIB_ENGINE_PROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a,conservative_maintenance as c,owned_source_read_pressure as byte_policy
    loader,entry,profile=bootstrap(c.ROOT)
    guards,_=loader.load(c.ROOT,list(entry.BOOTSTRAP[1:]),{})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    guard=guards.owned_cpu_baseline_v1.guard_type(guards.terminal_metadata_pressure_v1.guard_type(
        guards.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NEW_ZLIB_PARENT_NOT_NATIVE',GO_authorized=False,
        accepted_count_delta=0,product_or_worker_or_Native_executed=False);candidate=None
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for n in (SELF,TEST):q.pin(n)
        for p in (*entry.BOOTSTRAP,ENGINE,PROFILE):a.exact(q.pin(p['path']),p,'PINNED_PRIVATE_PARENT_BOOTSTRAP')
        libraries,_=entry.planning_libraries(c.ROOT,q,a,loader)
        admission,batch,reuse=(getattr(libraries,n) for n in ('batch_scope_admission','batch_verification','verification_reuse'))
        data=admission.read_plan(q,a,batch,reuse);entry.extend_execution(data,q,batch)
        retained,_=profile.admit(c.ROOT,q,a,batch.scope,data.report,data.package_sources,entry.WORKER)
        sources=source_table(data,q,entry,profile,batch.scope)
        for p in profile.PACKAGE:a.exact(q.pin(p['path']),p,'EXACT_QUALIFIED_ZLIB_FILE3')
        manifest=a.read_exact(q,profile.PACKAGE[0])
        if prepare:
            candidate=graph_record(data,sources,profile)
        else:
            graph_pin=q.pin(GRAPH);graph=a.read_exact(q,graph_pin)
            expected=graph_record(data,sources,profile);expected['cleanup_confirmed']=True
            a.exact(graph,expected,'EXACT_NEW_GRAPH_FROM_CURRENT_SOURCES_NOT_OLD002')
            additions=batch.scope.extend(sources,batch.scope.pins(list(profile.PACKAGE)+[graph_pin,profile.QUALIFICATION]))
            row['scope_projection']=project_plan(data,manifest,additions,batch,q.checkpoint)
            data.package_sources=sources;data.report=graph
            known=batch.scope.extend(data.planned.logical,batch.scope.pins(data.evidence['source_pins']))
            initial=batch.PacedNamespaceLoader(loader,q,known).api
            libraries,_=initial.load(c.ROOT,[known['tools/p09/'+n+'.py'] for n in
                ('ast_clone_namespace_v1','ast_copy_namespace_connection_v1')],{})
            optimized,_=libraries.ast_copy_namespace_connection_v1.connect(loader,libraries.ast_clone_namespace_v1)
            paced=batch.PacedNamespaceLoader(optimized,q,known).api
            connected=connect_package(c.ROOT,q,data,graph,known,a,batch,profile,paced,byte_policy)
            original_sources=admission.parent_sources
            def parent_sources(actual_data,actual_batch):
                explicit=original_sources(actual_data,actual_batch)
                return batch.scope.extend(explicit,additions)
            selected=NS(**{**vars(admission),'PACKAGE':(*profile.PACKAGE,graph_pin),'parent_sources':parent_sources})
            result=entry.connect(c.ROOT,q,data,connected,a,batch,selected)
            require(result.proof['helper64_nominal_fit'],'ORIGINAL_HELPER64_NOT_INCREASED')
            row['connection']=result.proof
        q.finish();guard.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'FULL_CLOSING_AND_ZERO_PROCESS')
        row.update(state='PASS_NEW_ZLIB_PARENT_GRAPH_SOURCES_NOT_NATIVE' if prepare else 'PASS_NEW_ZLIB_PARENT_CONNECTION_NOT_NATIVE',
            source_pins=list(q.snapshots.values()),graph_sources=len(sources))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError,ImportError,MemoryError) as error:
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        if error.args and error.args[0]=='BATCH_ENGINE_EVERY_OBSERVED_HELPER_ALREADY_DECLARED':row['undeclared_helpers']=list(error.args[1])
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        guard.close()
        if guard.cleanup is not True:row['state']='CLEANUP_FAILED_ZLIB_PARENT_NOT_NATIVE'
        if candidate is not None and row['state']=='PASS_NEW_ZLIB_PARENT_GRAPH_SOURCES_NOT_NATIVE' and guard.cleanup is True:
            candidate['cleanup_confirmed']=True;row['prepared_graph']=candidate
        row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            process_creation_attempts=len(denied),system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_max=max((s.get('parent_cpu_machine_percent') or 0 for s in guard.samples),default=None),
            private_MiB_max=max((s['parent_private_mib'] for s in guard.samples),default=None))
        print(json.dumps(row))
    return 0 if row['state'].startswith('PASS_') and guard.cleanup is True else 2


if __name__=='__main__':raise SystemExit(main())
