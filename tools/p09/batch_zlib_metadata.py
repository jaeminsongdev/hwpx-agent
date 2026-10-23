"""Actual engine metadata and whole boundaries; permanently NO-GO.

Reuse the sealed parent construction and approved preparation CPU profile.
Only read-only preparation owners rotate; no Native/Frame timer is started.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/batch_zlib_metadata.py'
TEST='tools/p09/tests/test_batch_zlib_metadata.py'
PREPARATION=dict(path='tools/p09/batch_zlib_preparation.py',bytes=10190,
    sha256='0cadfd15f518a0cf2915115caa950cd55a8b64849415545d5a851fcdada1e49c')


def require(ok,code):
    if not ok:raise ValueError('ZLIB_METADATA_'+code)


def epoch_evidence(record):
    """Bounded copies of existing samples; no new sampler/query or decisions."""
    fields=('time_utc','system_cpu_percent','available_ram_mib','total_ram_mib',
        'available_ram_percent','commit_used_percent','parent_cpu_machine_percent',
        'parent_private_mib','parent_private_percent')
    samples=record['samples']
    return dict({k:v for k,v in record.items() if k!='samples'},
        original_resource_sample_count=len(samples),terminal_resource_sample_limit=8,
        terminal_resource_samples=[{k:sample[k] for k in fields if k in sample} for sample in samples[-8:]],
        additional_sampler_or_query_started=False)


def readiness_context(result):
    fn=result.assembled.built.window.WINDOW_LINK.connect_engine
    require(type(fn) is FunctionType and fn.__closure__ is not None,'ORIGINAL_READINESS_CLOSURE')
    cells=dict(zip(fn.__code__.co_freevars,(c.cell_contents for c in fn.__closure__)))
    require('context' in cells,'ACTUAL_READINESS_CONTEXT')
    return cells['context']


def idle(result,*,closed=False):
    """Inspect actual retained owners, never hide a constructed connection."""
    assembled=result.assembled;batch=assembled.batch;parent=batch.parent_connection
    phases=('EMPTY_BATCH_AUDITED_NOT_ACCEPTED',) if closed else ('NEW','READY')
    require(batch.identity()==batch.owner and batch.phase in phases and batch.active is None
        and not batch.cases and not batch.metadata_reader_active,'READ_ONLY_BATCH_OWNER')
    if batch.phase=='NEW':
        require(batch.initial is batch.final is batch.initial_reader is None,'NO_BOUNDARY_BEFORE_REAL_OPENING')
    else:
        expected={n:dict(p) for n,p in batch.whole.items()}
        opening=batch.initial_reader
        require(opening is not None and batch.initial==expected and opening.snapshots==expected
            and opening.read_passes==len(expected)
            and opening.bytes_read==sum(p['bytes'] for p in expected.values()),'ACTUAL_COMPLETE_WHOLE_OPENING')
        require(batch.final==expected if closed else batch.final is None,'ACTUAL_COMPLETE_WHOLE_CLOSING')
    require(parent is not None and assembled.built.state.attempts==assembled.built.state.calls==0
        and parent.state.attempts==0 and parent.state.frames==[],'ZERO_NATIVE_PARENT_FRAME_EXECUTION')
    require(all(set(vars(cls))==set(saved) and all(vars(cls)[name] is value for name,value in saved.items())
        for cls,saved in parent.classes),'UNCHANGED_FRAME_CLASSES')
    require(all(fn.__code__ is code and fn.__defaults__ is defaults and fn.__closure__ is closure
        and fn.__kwdefaults__==keywords for fn,code,defaults,closure,keywords in parent.methods),
        'UNCHANGED_FRAME_METHODS')
    shared=batch.shared
    require(shared.identity()==shared.owner and shared.frame is None and not shared.restored
        and shared.error is None and all(b is None or b.active is None and b.error is None
            for b in (shared.metadata,shared.frame)),
        'NO_FRAME_OR_ACTIVE_FAILED_SHARED_DECODER')
    context=readiness_context(result)
    require(context.parent is parent.state and not context.active and context.attempts==context.jobs==0
        and context.owner is context.job is None and context.bindings==[]
        and context.restorations==context.frame_checks==0,'ZERO_READINESS_JOB_OR_WORKER_EXECUTION')
    return context


class ReadOnlyEpochs:
    """Exact three read-only stages, permanently latched on any failure."""
    STAGES=('construction','opening_and_metadata','closing')

    def __init__(self,factory,*,clock=time.monotonic,identity=lambda:(os.getpid(),threading.get_ident())):
        self.factory=factory;self.clock=clock;self.identity=identity;self.owner=identity()
        self.guard=None;self.records=[];self.broken=False;self.closed=False
        self.result=None;self.stage=None;self.started=None

    def check(self,*args,**kwargs):
        try:
            require(not self.closed and not self.broken and self.identity()==self.owner and self.guard is not None,
                'LIVE_SAME_OWNER_PREPARATION')
            return self.guard.check(*args,**kwargs)
        except BaseException:
            self.broken=True;raise

    def bind(self,result):
        try:
            require(self.result is None and self.stage=='construction' and self.guard is not None,'ONE_CONSTRUCTED_PARENT')
            self.check();idle(result);self.result=result
        except BaseException:
            self.broken=True;raise

    def advance(self,stage):
        try:
            require(not self.closed and not self.broken and self.identity()==self.owner,'NO_RETRY_OR_OWNER_CHANGE')
            index=len(self.records)+(self.guard is not None)
            require(index<len(self.STAGES) and stage==self.STAGES[index],'THREE_EXACT_SERIAL_STAGES')
            if self.guard is not None:
                self.check(force=True)
                require(self.result is not None,'ACTUAL_PARENT_BEFORE_READ_ONLY_ROTATION')
                idle(self.result);self._release()
            self.stage=stage;self.started=self.clock()
            role='dispatch_construction' if stage=='construction' else 'whole_metadata_preflight'
            self.guard=self.factory(role);self.guard.acquire()
        except BaseException:
            self.broken=True;raise

    def _release(self):
        guard=self.guard
        if guard is None:return
        self.guard=None
        try:guard.close()
        finally:
            self.records.append(dict(stage=self.stage,elapsed_seconds=self.clock()-self.started,
                cleanup_confirmed=guard.cleanup,samples=list(guard.samples),
                preparation_policy=guard.preparation_CPU.summary(),owned_limits=guard.preparation_limits))
        require(guard.cleanup is True,'OWNER_CLEANUP_BEFORE_SUCCESSOR')

    def close(self):
        self.closed=True
        try:self._release()
        except BaseException:
            self.broken=True;raise


def process_blocker(denied):
    def audit(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('ZLIB_METADATA_PROCESS_PERMANENTLY_DENIED')
    return audit


def bootstrap(root):
    path=root/PREPARATION['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_PREPARATION_SOURCE')
    with path.open('rb') as stream:raw=stream.read(PREPARATION['bytes']+1)
    require(len(raw)==PREPARATION['bytes'] and hashlib.sha256(raw).hexdigest()==PREPARATION['sha256'],
        'SEALED_APPROVED_PREPARATION_SOURCE')
    # Exact declared source, private just like its sealed parent. Do not import
    # a second top-level driver or remove/hide anything from sys.modules.
    environment=dict(__name__='p09_exact_zlib_metadata_preparation',__file__=str(path))
    exec(compile(raw,PREPARATION['path'],'exec'),environment)
    prep=NS(**environment)
    parent=prep.parent_module(root);loader,entry,profile=parent.bootstrap(root)
    return prep,parent,loader,entry,profile


def construct(root,q,epochs,a,parent,entry,profile,loader,prep,policy,witness,byte_policy):
    """Same sealed construction, with this one named diagnostic input added."""
    for name in (SELF,TEST,parent.SELF,parent.TEST):q.pin(name)
    for p in (*entry.BOOTSTRAP,parent.ENGINE,parent.PROFILE,PREPARATION):
        a.exact(q.pin(p['path']),p,'EXACT_UNCHANGED_CONSTRUCTION_SOURCE')
    libraries,_=entry.planning_libraries(root,q,a,loader)
    admission,batch,reuse=(getattr(libraries,n) for n in ('batch_scope_admission','batch_verification','verification_reuse'))
    data=admission.read_plan(q,a,batch,reuse);entry.extend_execution(data,q,batch)
    profile.admit(root,q,a,batch.scope,data.report,data.package_sources,entry.WORKER)
    selected=prep.connect(parent,policy,witness)
    sources=selected.__globals__['source_table'](data,q,entry,profile,batch.scope)
    for p in profile.PACKAGE:a.exact(q.pin(p['path']),p,'EXACT_QUALIFIED_ZLIB_FILE3')
    manifest=a.read_exact(q,profile.PACKAGE[0]);graph_pin=q.pin(prep.GRAPH);graph=a.read_exact(q,graph_pin)
    expected=parent.graph_record(data,sources,profile);expected['cleanup_confirmed']=True
    a.exact(graph,expected,'EXACT_SEALED_GRAPH004')
    additions=batch.scope.extend(sources,batch.scope.pins(list(profile.PACKAGE)+[graph_pin,profile.QUALIFICATION]))
    additions=batch.scope.extend(additions,{SELF:dict(q.pin(SELF))})
    projection=parent.project_plan(data,manifest,additions,batch,epochs.check)
    data.package_sources=sources;data.report=graph
    known=batch.scope.extend(data.planned.logical,batch.scope.pins(data.evidence['source_pins']))
    initial=batch.PacedNamespaceLoader(loader,q,known).api
    libraries,_=initial.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('ast_clone_namespace_v1','ast_copy_namespace_connection_v1')],{})
    optimized,_=libraries.ast_copy_namespace_connection_v1.connect(loader,libraries.ast_clone_namespace_v1)
    paced=batch.PacedNamespaceLoader(optimized,q,known).api
    connected=parent.connect_package(root,q,data,graph,known,a,batch,profile,paced,byte_policy)
    def parent_sources(actual_data,actual_batch):
        return batch.scope.extend(admission.parent_sources(actual_data,actual_batch),additions)
    api=NS(**{**vars(admission),'PACKAGE':(*profile.PACKAGE,graph_pin),'parent_sources':parent_sources})
    helpers,_=connected.loader.load(root,[known['tools/p09/fresh_lossless_metadata_reader_v1.py']],{})
    result=entry.connect(root,q,data,connected,a,batch,api)
    require(result.proof['helper64_nominal_fit'],'ORIGINAL_HELPER64_RETAINED')
    epochs.bind(result)
    # It is this actual engine's new Batch that the callback checks.
    data.planned.batch=result.assembled.batch
    return NS(result=result,data=data,connected=connected,batch=batch,projection=projection,
        fresh=helpers.fresh_lossless_metadata_reader_v1)


def approved_admission(root,prep,loader,entry,a,c):
    # The exact source was qualified before the human approved installation.
    # Select it only for this private preparation bootstrap. The full original
    # design/probe witnesses and closing reads still execute, without changing
    # the sealed default admission or any Native dependency.
    libraries,_=loader.load(root,[prep.POLICY],{})
    instances=[]
    selected=prep.policy_loader(loader,libraries.preparation_attributed_cpu_v1,instances)
    try:policy,witness,Reader,chunk=prep.admission(root,selected,entry,a,c)
    except (ValueError,OSError) as error:
        error.preparation_evidence=[epoch_evidence(dict(stage='policy_admission',cleanup_confirmed=g.cleanup,
            samples=g.samples,preparation_policy=g.preparation_CPU.summary(),owned_limits=g.preparation_limits))
            for g in instances]
        raise
    require(len(instances)==1 and instances[0].cleanup is True,'ONE_CLOSED_APPROVED_ADMISSION_OWNER')
    witness=dict(witness,preparation_policy=instances[0].preparation_CPU.summary(),
        owned_limits=instances[0].preparation_limits,default_admission_policy_changed=False)
    return policy,witness,Reader,chunk


def metadata(root,epochs,context,a):
    result=context.result;batch=result.assembled.batch;binding=context.connected.graph.binding
    require(batch.phase=='READY' and batch.initial==context.batch.plain(batch.whole),'ACTUAL_WHOLE_OPENING_REQUIRED')
    build=result.assembled.built.engine.run_owned.__globals__['build']
    reader=build.BuildReader(root,epochs.check)
    required,rust=result.attached.callback(reader)
    projection,_=binding.project(required,epochs.check)
    a.exact(context.batch.plain(projection.physical_pins),context.data.planned.current,'ACTUAL_EXACT_CURRENT_INPUT_SCOPE')
    with batch.metadata_reader(reader,binding):reader.finish()
    epochs.check(force=True);idle(result)
    require(reader.final_fresh_hashes==len(reader.snapshots),'ALL_CURRENT_METADATA_CLOSING')
    connection=batch.metadata_connection
    require(len(connection.readers)==len(connection.budgets)==1 and connection.readers[0] is reader,
        'ONE_ACTUAL_ENGINE_METADATA_READER')
    return dict(state='PASS_ACTUAL_ENGINE_METADATA_CALLBACK_NOT_NATIVE',
        fresh_inputs=len(reader.snapshots),final_fresh_hashes=reader.final_fresh_hashes,
        physical_read_passes=reader.read_passes,physical_bytes_read=reader.bytes_read,
        selected_current_inputs=len(projection.physical_pins),rust_inputs=len(rust),
        metadata=context.fresh.summary(reader),shared_decoder=batch.shared.evidence(),
        callback_calls=len(result.attached.calls),full162_forced_by_original_callback=True,
        original_engine_run_owned_called=False,Frame_created=False,GO_authorized=False)


def main():
    require(sys.argv[1:]==['--metadata'],'ONLY_READ_ONLY_METADATA_NO_NATIVE_OR_GO')
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/p09'));sys.dont_write_bytecode=True
    denied=[];sys.addaudithook(process_blocker(denied))
    prep,parent,loader,entry,profile=bootstrap(root)
    import accept_case112_current_epoch as a,conservative_maintenance as c,owned_source_read_pressure as byte_policy
    policy,witness,Reader,chunk=approved_admission(root,prep,loader,entry,a,c)
    guards,_=loader.load(root,list(entry.BOOTSTRAP[1:]),{})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    def factory(role):
        return guards.owned_cpu_baseline_v1.guard_type(policy.guard_type(
            guards.distinct_final_sample_guard_v1.guard_type(a.Guard),role=role))()
    epochs=ReadOnlyEpochs(factory);q=context=opening=closing=None;started=time.monotonic()
    row=dict(state='FAILED_ACTUAL_ZLIB_METADATA_NOT_NATIVE',GO_authorized=False,accepted_count_delta=0,
        product_worker_Frame_or_Native_executed=False,policy_admission=witness)
    def progress(state):
        print(json.dumps(dict(state=state,GO_authorized=False,elapsed_seconds=time.monotonic()-started)),flush=True)
    try:
        epochs.advance('construction');q=Reader(root,epochs.check)
        context=construct(root,q,epochs,a,parent,entry,profile,loader,prep,policy,witness,byte_policy)
        q.finish();epochs.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'FULL_CONSTRUCTION_CLOSING')
        row.update(construction=context.result.proof,scope_projection=context.projection,source_pins=list(q.snapshots.values()))
        epochs.advance('opening_and_metadata');progress('RUNNING_ACTUAL_ZLIB_WHOLE_OPENING')
        opening=Reader(root,epochs.check);context.result.assembled.batch.begin(opening)
        progress('RUNNING_ACTUAL_ZLIB_ENGINE_METADATA')
        row['metadata']=metadata(root,epochs,context,a)
        epochs.advance('closing');progress('RUNNING_ACTUAL_ZLIB_WHOLE_CLOSING')
        closing=Reader(root,epochs.check);row['whole_batch']=context.result.assembled.batch.finish(closing)
        idle(context.result,closed=True);epochs.check(force=True)
        require(not denied,'ZERO_PROCESS_CREATION_ATTEMPTS')
        row['state']='PASS_ACTUAL_ZLIB_ENGINE_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE'
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError,ImportError,MemoryError) as error:
        epochs.broken=True;row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        if error.args and error.args[0]=='BATCH_ENGINE_EVERY_OBSERVED_HELPER_ALREADY_DECLARED':row['undeclared_helpers']=list(error.args[1])
        import traceback
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        if context is not None:context.result.assembled.batch.shared.restore()
        try:epochs.close()
        except (ValueError,OSError):row['state']='CLEANUP_FAILED_ZLIB_METADATA_NOT_NATIVE'
        cleanup=bool(epochs.records) and all(r['cleanup_confirmed'] is True for r in epochs.records)
        if not cleanup:row['state']='CLEANUP_FAILED_ZLIB_METADATA_NOT_NATIVE'
        samples=[s for r in epochs.records for s in r['samples']]
        row.update(cleanup_confirmed=cleanup,elapsed_seconds=time.monotonic()-started,
            preparation_epochs=[epoch_evidence(r) for r in epochs.records],
            construction_fresh_inputs=0 if q is None else len(q.snapshots),
            construction_final_hashes=0 if q is None else q.final_fresh_hashes,process_creation_attempts=len(denied),
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            owned_CPU_max=max((s.get('parent_cpu_machine_percent') or 0 for s in samples),default=None),
            private_MiB_max=max((s['parent_private_mib'] for s in samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in samples),default=None),
            Native_policy_changed=False,failed_phase_retried=False)
        for label,reader in (('whole_opening',opening),('whole_closing',closing)):
            if reader is not None:row[label]=dict(fresh_inputs=len(reader.snapshots),read_passes=reader.read_passes,
                physical_bytes_read=reader.bytes_read,source_stat=reader.source_snapshot_diagnostics(),workspace=chunk.summary(reader))
        if context is not None:row['terminal_batch_phase']=context.result.assembled.batch.phase
        print(json.dumps(row,ensure_ascii=True),flush=True)
    return 0 if row['state'].startswith('PASS_') and cleanup else 2


def entrypoint():
    """Keep early admission failures measurable instead of losing telemetry."""
    try:return main()
    except (ValueError,OSError,KeyError,TypeError,AttributeError,ImportError) as error:
        import traceback
        row=dict(state='FAILED_ZLIB_METADATA_BOOTSTRAP_OR_ADMISSION_NOT_NATIVE',error_type=type(error).__name__,
            GO_authorized=False,accepted_count_delta=0,product_worker_Frame_or_Native_executed=False,
            preparation_evidence=getattr(error,'preparation_evidence',[]),
            error_frames=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
                for f in traceback.extract_tb(error.__traceback__)[-6:]])
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        print(json.dumps(row,ensure_ascii=True),flush=True);return 2


if __name__=='__main__':raise SystemExit(entrypoint())
