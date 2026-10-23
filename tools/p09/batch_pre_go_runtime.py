"""Actual first Frame/readiness diagnostic; no GO or product permission.

Use the original parent, its Native guard/Job/Frame, whole opening audit and
the qualified one-way checkpoint handoff. A single allowed child has BOTH
--probe-no-go and --zlib; its own audit rejects product process creation.
The original pre-GO transport raises before the strict Input starts its clock.
An intentional stop is never a full Frame commit, product or queue acceptance.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/batch_pre_go_runtime.py'
TEST='tools/p09/tests/test_batch_pre_go_runtime.py'
PARENT=dict(path='tools/p09/batch_zlib_frame_probe.py',bytes=8012,
    sha256='f94c1b6f5a7f149faa3e925a653a1e89ee62088f61953584fdb88c3ec09cf768')
SOURCES=(
    dict(path='tools/p09/batch_pre_go_stop.py',bytes=10898,
        sha256='aed9cb21eab18611b1acec81eaacd7080c32a068c90cfa9d810c3fac822abab6'),
    dict(path='tools/p09/batch_pre_go_receipt.py',bytes=6836,
        sha256='8f4c89832c98a401cb2c459564fb68732a564b8a76d6bd855e779779e306ff28'),
    dict(path='tools/p09/batch_native_checkpoint.py',bytes=5743,
        sha256='8295901ed4345141ca4417651fc172afc342a3da6dab5f0fb0701a30be299994'))
WORKER='tools/p09/batch_worker_launch.py'
TASK='case165-current-r010-tests'
RECEIPT='implementation/p09/evidence/p09-361-case165-pre-go-runtime-diagnostic004-run010.v1.json'
INTENT='implementation/p09/evidence/p09-361-case165-pre-go-runtime-diagnostic004.intent.v1.json'
CANONICAL='implementation/p09/evidence/p09-361-case165-current-runtime-run010.v1.json'
ORIGINAL_ENGINE=dict(path='tools/p09/run_case112_current_stored.py',bytes=23159,
    sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713')
LATE_NAMES=('FAILED_FIRST_PIN','FAILED_STOP_PIN')


def require(ok,code):
    if not ok:raise ValueError('PRE_GO_RUNTIME_'+code)


def direct_absence(root,name):
    path=root/name
    for directory in (path.parent,*path.parent.parents):
        require(directory.is_dir() and not directory.is_symlink() and not directory.is_junction(),'DIRECT_OUTPUT_ANCESTORS')
        if directory==root:break
    try:path.lstat()
    except FileNotFoundError:return True
    return False


def bootstrap(root):
    path=root/PARENT['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_QUALIFIED_PROBE')
    for directory in (path.parent,*path.parent.parents):
        require(directory.is_dir() and not directory.is_symlink() and not directory.is_junction(),'DIRECT_SOURCE_ANCESTORS')
        if directory==root:break
    with path.open('rb') as stream:raw=stream.read(PARENT['bytes']+1)
    require(len(raw)==PARENT['bytes'] and hashlib.sha256(raw).hexdigest()==PARENT['sha256'],'EXACT_QUALIFIED_PROBE')
    env=dict(__name__='p09_exact_actual_pre_go_probe',__file__=str(path))
    exec(compile(raw,PARENT['path'],'exec'),env)
    return NS(**env)


class ProcessPolicy:
    def __init__(self,root):
        self.root=root;self.context=None;self.armed=False;self.attempts=0;self.denied=[]
    def arm(self,context):
        require(not self.armed and self.context is None and not self.denied and not context.active and context.attempts==0,
            'ONE_UNUSED_CONTEXT_BEFORE_NATIVE')
        self.context=context;self.armed=True
    def __call__(self,event,args):
        if event not in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):return
        try:
            require(event=='subprocess.Popen' and self.armed and self.attempts==0 and not self.denied and len(args)==4,
                'ONE_EXACT_NO_GO_CHILD_ONLY')
            # CPython on Windows emits the already-quoted command STRING at
            # this audit boundary, not the original Popen argv list. Match its
            # exact list2cmdline representation; do not shell-parse input.
            command=args[1]
            prefix=subprocess.list2cmdline([sys.executable,'-B',str(self.root/WORKER),
                '--probe-no-go','--zlib','--ready-handle'])
            suffix=subprocess.list2cmdline(['--task',TASK])
            match=re.fullmatch(re.escape(prefix)+' ([1-9][0-9]{0,19}) '+re.escape(suffix),command) if type(command) is str else None
            require(match is not None and int(match[1])<2**64 and args[0] in (None,sys.executable)
                and os.fspath(args[2])==os.fspath(self.root) and args[3] is None,
                'EXACT_DIAGNOSTIC_ARGV_ROOT_AND_INHERITED_EVENT')
            self.context.checkpoint()  # Actual Frame, Native guard and owner Job.
            self.attempts+=1
        except BaseException:
            self.denied.append(event);raise


def connect_callback(context,relay,actual_context):
    env=context.result.assembled.built.engine.run_owned.__globals__
    original=context.result.attached.callback
    require(env['binding'] is original,'ONE_ACTUAL_CURRENT_METADATA_CALLBACK')
    def callback(reader):
        relay.admit_metadata(reader,actual_context)
        return original(reader)
    env['binding']=callback
    def restore():
        require(not actual_context.active and env['binding'] is callback,'ORIGINAL_PARENT_CLOSED_BEFORE_CALLBACK_RESTORE')
        env['binding']=original
    return restore


def source_checkpoint(relay):
    """Original construction profiler may call the reader guard reentrantly.

    During preparation use its exact original guard, as before the handoff.
    Never skip the profiling call or resource check. Only after handoff use
    the original Handoff.check with its unchanged Native recursion latch.
    """
    def checkpoint(*args,**kwargs):
        try:
            if relay.phase=='PREPARATION':
                require(not relay.broken and relay.identity()==relay.owner,'SAME_PREPARATION_SOURCE_OWNER')
                return relay.preparation.check(*args,**kwargs)
            return relay.check(*args,**kwargs)
        except BaseException:relay.broken=True;raise
    return checkpoint


def engine_dependency_pins(raw):
    """Closed original source declarations, never an observed-reader union."""
    require(type(raw) is bytes and len(raw)==ORIGINAL_ENGINE['bytes']
        and hashlib.sha256(raw).hexdigest()==ORIGINAL_ENGINE['sha256'],'EXACT_ORIGINAL_ENGINE_DEPENDENCY_SOURCE')
    found={}
    for node in ast.parse(raw).body:
        if not isinstance(node,ast.Assign) or len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name):continue
        name=node.targets[0].id
        if name not in LATE_NAMES:continue
        require(name not in found and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name)
            and node.value.func.id=='dict' and not node.value.args,'EXACT_ORIGINAL_PIN_DECLARATION')
        values={}
        for keyword in node.value.keywords:
            require(keyword.arg in ('path','bytes','sha256') and keyword.arg not in values,'EXACT_THREE_PIN_KEYWORDS')
            values[keyword.arg]=ast.literal_eval(keyword.value)
        require(set(values)=={'path','bytes','sha256'} and type(values['path']) is str
            and type(values['bytes']) is int and values['bytes']>0 and type(values['sha256']) is str
            and re.fullmatch('[a-f0-9]{64}',values['sha256']) is not None,'EXACT_ORIGINAL_SOURCE_PIN_TYPES')
        found[name]=values
    require(set(found)==set(LATE_NAMES),'BOTH_ORIGINAL_LATE_READ_DECLARATIONS')
    return tuple(dict(found[name]) for name in LATE_NAMES)


def require_current_dependencies(parent,pins):
    original=parent.project_plan
    def project(data,manifest,additions,batch,checkpoint):
        proof=original(data,manifest,additions,batch,checkpoint)
        prior=data.planned;checkpoint()
        require(prior.batch.phase=='NEW' and prior.batch.parent_connection is None
            and not prior.batch.cases and prior.batch.active is None,'ROLE_CORRECTION_BEFORE_REAL_BATCH_OR_PARENT')
        required=batch.scope.pins(list(pins))
        require(len(required)==2 and all(prior.history.get(n)==p and prior.whole.get(n)==p
            and n not in prior.current for n,p in required.items()),'BOTH_FROZEN_CURRENT_DEPENDENCIES_WERE_PRESERVATION_ONLY')
        current=batch.scope.extend(prior.current,required)
        history={n:dict(p) for n,p in prior.history.items() if n not in required}
        require(not set(current)&set(history) and {**current,**history}==prior.whole,
            'ALL_WHOLE_PINS_PRESERVED_WITHOUT_EXCLUSION')
        policy=batch.Batch(prior.whole,current,history,first_index=165,checkpoint=checkpoint,
            identity=prior.batch.identity)
        data.planned=NS(**{**vars(prior),'batch':policy,'current':current,'history':history})
        return dict(proof,current_inputs=len(current),preservation_inputs=len(history),
            original_late_current_dependencies=[dict(p) for p in pins],
            original_engine_dependency_source=dict(ORIGINAL_ENGINE),
            full_preservation_pins_unchanged=True,observed_reader_union_used=False,
            role_change_before_owner_execution=True)
    return NS(**{**vars(parent),'project_plan':project})


def bind_parent_entry(context):
    """Restore compose_parent's original SELF/TEST metadata dependency.

    Batch composes its own original Frame hooks instead of calling that
    complete composer twice. Its omitted entry metadata must still match the
    unmodified launcher, not the old product-window template's entry path.
    """
    assembled=context.result.assembled;built=assembled.built
    require(assembled.batch.parent_connection.state.attempts==0
        and assembled.batch.parent_connection.state.frames==[]
        and built.state.attempts==built.state.calls==0,'ENTRY_METADATA_BEFORE_ANY_ORIGINAL_EXECUTION')
    expected=(context.connected.runtime.SELF,context.connected.runtime.TEST)
    require(expected==('tools/p09/current_queue_successor_runtime.py',
        'tools/p09/tests/test_current_queue_successor_runtime.py'),'EXACT_ORIGINAL_SUCCESSOR_ENTRY_METADATA')
    run=built.engine.run_owned;worker=built.original_worker
    environments=(run.__globals__,worker.__globals__)
    before=[(env['SELF'],env['TEST']) for env in environments]
    prior=('tools/p09/flat_current_queue_product_window_runtime_v18.py',
        'tools/p09/tests/test_flat_current_queue_product_window_runtime_v18.py')
    require(all(pair in (prior,expected) for pair in before),'ONLY_ORIGINAL_TEMPLATE_OR_CURRENT_ENTRY_PAIR')
    require(all(not any(getattr(module,'__dict__',None) is env for module in tuple(sys.modules.values()) if module)
        for env in environments),'PRIVATE_ENGINE_AND_WORKER_ENVIRONMENTS_ONLY')
    for env in environments:env.update(SELF=expected[0],TEST=expected[1])
    return dict(original_parent_entry_metadata_restored=True,original_template_entry_pairs=before,
        actual_parent_entry=expected[0],actual_parent_test=expected[1],
        original_engine_and_worker_objects_code_defaults_and_closures_unchanged=True,
        original_launcher_expected_command_check_weakened=False,default_modules_mutated=False)


def diagnostic_namespace(original):
    """Next distinct NO-GO receipt, unchanged qualified projector function code."""
    require(original.RECEIPT.endswith('diagnostic001-run010.v1.json')
        and original.DIAGNOSTIC+'010.v1.json'==original.RECEIPT,'EXACT_QUALIFIED_DIAGNOSTIC001_SOURCE')
    old=original.project_engine.__globals__
    env=dict(old,DIAGNOSTIC=RECEIPT[:-len('010.v1.json')],RECEIPT=RECEIPT)
    result=dict(vars(original))
    for name,value in tuple(vars(original).items()):
        if type(value) is FunctionType and value.__globals__ is old:
            changed=FunctionType(value.__code__,env,name=value.__name__,argdefs=value.__defaults__,closure=value.__closure__)
            changed.__kwdefaults__=value.__kwdefaults__
            require(changed.__code__ is value.__code__ and changed.__defaults__ is value.__defaults__
                and changed.__closure__ is value.__closure__,'ORIGINAL_NAMESPACE_FAMILY_CODE_DEFAULTS_CLOSURE')
            env[name]=changed;result[name]=changed
    result.update(DIAGNOSTIC=env['DIAGNOSTIC'],RECEIPT=env['RECEIPT'])
    return NS(**result)


def validate_terminal(row,context,adapter,relay,actual_context,policy,a):
    """Combine actual owners and original failed receipt, never invent PASS."""
    a.fields(row,dict(stop_reason='BATCH_PRE_GO_DIAGNOSTIC_STOP',cleanup_confirmed=True,
        owned_tree_empty=True,worker_created=True,job_assigned=True,writer_authorized=False,
        product_body_observed=False,actual_product_child_executed=False,
        Native_source_frame_qualified=False,current_generation_runtime_candidate_qualified=False,
        accepted_count_delta=0),'EXACT_ORIGINAL_DIAGNOSTIC_STOP_NOT_PRODUCT')
    require(row['state']!='PASS_SCOPED_NOT_GATE' and not row['passed_test_names'],'ORIGINAL_FAILURE_REMAINS_FAILURE')
    a.fields(row['job_final'],dict(active_processes=0,owned_processes=[]),'ACTUAL_ORIGINAL_EMPTY_JOB')
    require(policy.attempts==1 and not policy.denied,'ONE_NO_GO_PROCESS_WITHOUT_DENIED_EXTRA_SPAWN')
    require(relay.phase=='NATIVE_TERMINAL' and not relay.broken and relay.bindings==1,
        'ONE_SUCCESSFUL_ORIGINAL_NATIVE_CHECKPOINT_HANDOFF')
    stop=adapter.evidence(cleanup_required=True)
    batch=context.result.assembled.batch;state=batch.parent_connection.state
    require(state.attempts==1 and len(state.frames)==1 and state.frames[0] is actual_context.parent.frames[0],
        'SAME_ACTUAL_PARENT_FRAME')
    frame=state.frames[0]
    require(frame.state=='CLOSED' and not frame.registered and frame.registry.active is None
        and not frame.reading and len(frame.boundaries)==1 and frame.boundaries[0]['role']=='before',
        'ONE_REAL_FIRST_BYTE_BOUNDARY_CLOSED_NOT_COMMITTED')
    held=frame.held
    require(held.acquired and held.closed and not held.owned and not held.active_readers
        and held.active_streams==0 and held.close_failures==0 and held.opened_handles==held.closed_handles,
        'ALL_ACTUAL_INPUT_HANDLES_STREAMS_AND_READERS_CLOSED')
    require(frame.raw_policy.restored and not frame.raw_policy.installed,'ACTUAL_RAW_ACCESS_POLICY_RESTORED')
    a.exact(row['source_frame'],frame.summary(),'SAME_ORIGINAL_FINAL_FRAME_SUMMARY')
    require(batch.phase=='BROKEN' and not batch.cases,'ABORTED_BATCH_NEVER_ACCEPTED')
    shared=batch.shared.evidence()
    require(shared['metadata_registered'] and shared['Frame_registered'] and not shared['terminal_error_seen']
        and shared['total_decoder_work_seconds']<=5,'ACTUAL_SHARED_DECODER_RETAINED')
    return dict(pre_GO_stop=stop,checkpoint_handoff=relay.evidence(),
        actual_frame_state=frame.state,actual_first_byte_boundaries=1,Frame_committed=False,
        physical_inputs=len(frame.inputs),physical_bytes=sum(p['bytes'] for p in frame.inputs.values()),
        opened_handles=held.opened_handles,closed_handles=held.closed_handles,
        shared_decoder=shared,terminal_batch_phase=batch.phase,
        original_failed_receipt_state=row['state'],original_stop_reason=row['stop_reason'],
        original_job_final=dict(row['job_final']),original_resource_sample_count=len(row['samples']),
        original_elapsed_seconds=row['elapsed_seconds'],
        actual_Native_or_product_or_queue_qualified=False)


def main():
    require(sys.argv[1:] in (['--connect-only'],['--diagnose-no-go']),'CLOSED_CONNECT_OR_NO_GO_DIAGNOSTIC_MODES')
    diagnose=sys.argv[1]=='--diagnose-no-go'
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/p09'));sys.dont_write_bytecode=True
    policy_audit=ProcessPolicy(root);sys.addaudithook(policy_audit)
    probe=bootstrap(root);metadata=probe.bootstrap(root)
    prep,parent,loader,entry,profile=metadata.bootstrap(root)
    import accept_case112_current_epoch as a,conservative_maintenance as c,owned_source_read_pressure as byte_policy
    policy,witness,Reader,chunk=metadata.approved_admission(root,prep,loader,entry,a,c)
    guards,_=loader.load(root,list(entry.BOOTSTRAP[1:]),{})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    def factory(role):
        return guards.owned_cpu_baseline_v1.guard_type(policy.guard_type(
            guards.distinct_final_sample_guard_v1.guard_type(a.Guard),role=role))()
    epochs=metadata.ReadOnlyEpochs(factory);q=context=adapter=relay=restore=None;opening=None
    actual_context=namespace=publisher=None;started=time.monotonic();native_called=False
    row=dict(state='FAILED_ACTUAL_PRE_GO_DIAGNOSTIC',mode='diagnose-no-go' if diagnose else 'connect-only',
        GO_authorized=False,accepted_count_delta=0,Native008_or_Native009_reexecuted=False,
        canonical_Native_receipt_or_intent_written=False,policy_admission=witness)
    def progress(stage):
        print(json.dumps(dict(stage=stage,elapsed_seconds=time.monotonic()-started,GO_authorized=False)),flush=True)
    try:
        require(all(direct_absence(root,n) for n in (CANONICAL,RECEIPT,INTENT)),'NO_EXISTING_DIAGNOSTIC_OR_CANONICAL_RESULT')
        epochs.advance('construction')
        # Initialize EVERY preparation reader/pacer/loader dependency with
        # this relay from the start. Rebinding q.checkpoint later would leave
        # inner-reader and lazy-loader closures on the closed preparation.
        libs,_=loader.load(root,list(SOURCES),{})
        relay=libs.batch_native_checkpoint.Handoff(epochs,metadata.idle)
        q=Reader(root,source_checkpoint(relay))
        for p in (PARENT,probe.METADATA,*SOURCES):a.exact(q.pin(p['path']),p,'EXACT_QUALIFIED_CURRENT_PROGRAM')
        q.pin(SELF);q.pin(TEST)
        extras={name:dict(q.pin(name)) for name in (SELF,PARENT['path'],*(p['path'] for p in SOURCES))}
        source,raw=q._read(ORIGINAL_ENGINE['path'],parse=True);q._bind(source['path'],source)
        a.exact(source,ORIGINAL_ENGINE,'EXACT_FROZEN_ORIGINAL_ENGINE_SOURCE')
        late=engine_dependency_pins(bytes(raw))
        selected=probe.extended_parent(parent,extras)
        selected=require_current_dependencies(selected,late)
        selected,namespace=diagnostic_namespace(libs.batch_pre_go_receipt).parent_api(selected)
        context=metadata.construct(root,q,relay,a,selected,entry,profile,loader,prep,policy,witness,byte_policy)
        actual_context=metadata.readiness_context(context.result)
        env=context.result.assembled.built.engine.run_owned.__globals__
        for name,pin in zip(LATE_NAMES,late):a.exact(env[name],pin,'SAME_ACTUAL_ENGINE_LATE_DEPENDENCIES')
        row['parent_entry_binding']=bind_parent_entry(context)
        adapter=libs.batch_pre_go_stop.connect_parent(actual_context)
        restore=connect_callback(context,relay,actual_context)
        require(namespace.loads==namespace.windows==namespace.links==1
            and namespace.projection['diagnostic_receipt']==RECEIPT,'ACTUAL_EXCLUSIVE_DIAGNOSTIC_NAMESPACE')
        known=context.connected.known
        publishers,_=context.connected.loader.load(root,[known['tools/p09/successor_preparation_workspace_v1.py']],{})
        publisher=publishers.successor_preparation_workspace_v1
        inspections,_=context.connected.loader.load(root,[known['tools/p09/native009_full72_construction_v1.py']],{})
        actual_helpers=inspections.native009_full72_construction_v1.helper_inventory(root,context.result.assembled.parent)
        require(actual_helpers['Native_count']<=64,'ORIGINAL_NATIVE_HELPER64_AFTER_ENTRY_BINDING')
        for name in actual_helpers['original_Native_helper_union']:
            require(name in known and name in context.result.assembled.batch.current,'ALL_ENTRY_HELPERS_DECLARED_CURRENT')
            a.exact(q.pin(name),known[name],'EXACT_CURRENT_HELPER_AFTER_ENTRY_BINDING')
        q.finish();epochs.check(force=True);metadata.idle(context.result)
        require(q.final_fresh_hashes==len(q.snapshots),'COMPLETE_CURRENT_CONSTRUCTION_CLOSING')
        row.update(construction_source_pins=list(q.snapshots.values()),construction_fresh_inputs=len(q.snapshots),
            construction_final_hashes=q.final_fresh_hashes,scope_projection=context.projection,
            helper_inventory=actual_helpers,diagnostic_namespace=namespace.projection,
            with_preparation15_seconds=context.result.proof['with_preparation15_seconds'])
        if not diagnose:
            row['state']='PASS_ACTUAL_DIAGNOSTIC_DRIVER_CONNECTION_NOT_NATIVE'
        else:
            row['diagnostic_intent_pin']=publisher.publish(root,INTENT,dict(
                schema_version='hwpx-agent.p09-pre-go-diagnostic-intent/v1',mode='NO_GO_DIAGNOSTIC_ONLY',
                result_path=RECEIPT,GO_authorized=False,accepted_count_delta=0,
                current_programs=[dict(extras[n]) for n in sorted(extras)]),a)
            epochs.advance('opening_and_metadata');progress('RUNNING_FRESH_WHOLE_OPENING_FOR_PRE_GO_DIAGNOSTIC')
            opening=Reader(root,relay.check);context.result.assembled.batch.begin(opening)
            epochs.check(force=True);metadata.idle(context.result);epochs.close();relay.arm()
            policy_audit.arm(actual_context);progress('RUNNING_ORIGINAL_NATIVE_TO_PRE_GO_STOP_ONLY')
            native_called=True
            try:row['original_parent_exit_code']=context.result.assembled.parent.run_owned(1)
            finally:
                relay.finish_native(actual_context)
                adapter.restore()
                restore();restore=None
            # The original parent is terminal. Start a separate short read-only
            # observer, never rotate/reset the Native or original lock clocks.
            guard=factory('whole_metadata_preflight');closing=None
            try:
                guard.acquire();closing=Reader(root,guard.check)
                result=closing.json(RECEIPT)
                row['actual_diagnostic']=validate_terminal(result,context,adapter,relay,actual_context,policy_audit,a)
                closing.finish();guard.check(force=True)
                row.update(original_diagnostic_receipt_pin=dict(closing.snapshots[RECEIPT]),
                    diagnostic_receipt_fresh_inputs=len(closing.snapshots),diagnostic_receipt_final_hashes=closing.final_fresh_hashes,
                    original_Native_resource_tail=metadata.epoch_evidence(dict(stage='original_native_terminal',
                        samples=result['samples'],cleanup_confirmed=result['cleanup_confirmed'])))
            finally:
                guard.close();row['terminal_observer_cleanup']=guard.cleanup
            require(guard.cleanup is True,'TERMINAL_READONLY_OBSERVER_CLEANUP')
            require(direct_absence(root,CANONICAL),'CANONICAL_NATIVE_RESULT_STILL_ABSENT')
            row['state']='PASS_ACTUAL_FIRST_FRAME_AND_SAME_JOB_READY_PRE_GO_STOP_NOT_PRODUCT'
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError,ImportError,MemoryError) as error:
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        import traceback
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        try:
            if adapter is not None:adapter.restore()
            if restore is not None:restore()
            if context is not None:context.result.assembled.batch.shared.restore()
        except (ValueError,OSError):row['state']='CLEANUP_FAILED_ACTUAL_PRE_GO_DIAGNOSTIC'
        try:epochs.close()
        except (ValueError,OSError):row['state']='CLEANUP_FAILED_ACTUAL_PRE_GO_DIAGNOSTIC'
        cleanup=bool(epochs.records) and all(r['cleanup_confirmed'] is True for r in epochs.records)
        if actual_context is not None:
            cleanup=cleanup and not actual_context.active
            row['actual_parent_context']=actual_context.evidence()
        if not cleanup:row['state']='CLEANUP_FAILED_ACTUAL_PRE_GO_DIAGNOSTIC'
        row.update(preparation_cleanup_confirmed=cleanup,elapsed_seconds=time.monotonic()-started,
            preparation_epochs=[metadata.epoch_evidence(r) for r in epochs.records],
            original_parent_execution_attempted=native_called,
            process_creation_attempts=policy_audit.attempts,denied_process_creation_events=policy_audit.denied,
            checkpoint_handoff=None if relay is None else relay.evidence(),
            original_Native_policy_changed=False,actual_product_execution_authorized=False)
        if opening is not None:row['whole_opening']=dict(fresh_inputs=len(opening.snapshots),read_passes=opening.read_passes,
            physical_bytes_read=opening.bytes_read,source_stat=opening.source_snapshot_diagnostics(),workspace=chunk.summary(opening))
        print(json.dumps(row,ensure_ascii=True),flush=True)
    return 0 if row['state'].startswith('PASS_') and cleanup else 2


if __name__=='__main__':raise SystemExit(main())
