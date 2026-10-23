"""Original run011 worker from declared inherited sources, not a dispatcher.

The parent must supply the actual current source Frame, owned Job and GO. This
entry never creates a Native parent, writes GO, consumes intent or accepts a case.
No execution authority is supplied merely by these CLI arguments or source pins.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_product_worker_entry.py'
TEST='tools/p09/tests/test_native011_product_worker_entry.py'
TASK='case165-current-r011-tests'


def require(ok,code):
    if not ok:raise ValueError('PRODUCT_WORKER_ENTRY_'+code)


def arguments(argv):
    require(type(argv) is list and len(argv)==8 and argv[::2][:2]==['--ready-handle','--task']
        and argv[3]==TASK and argv[4]=='--source-mapping','CLOSED_RUN011_WORKER_ARGUMENTS')
    require(type(argv[1]) is str and re.fullmatch('[1-9][0-9]{0,19}',argv[1]) is not None
        and int(argv[1])<2**64,'ORIGINAL_READY_HANDLE_INTEGER')
    require(all(type(value) is str for value in argv[5:])
        and re.fullmatch('[1-9][0-9]{0,19}',argv[5]) is not None and int(argv[5])<2**64
        and re.fullmatch('[1-9][0-9]{0,5}',argv[6]) is not None and int(argv[6])<=262144
        and re.fullmatch('[0-9a-f]{64}',argv[7]) is not None and argv[1]!=argv[5],
        'BOUNDED_DISTINCT_READONLY_SOURCE_MAPPING')
    return int(argv[1]),['--source-mapped-probe',*argv[5:]]


class OriginalInput:
    def __init__(self,original,observe=None):self.original=original;self.reads=0;self.go=False;self.observe=observe
    def __getattr__(self,name):return getattr(self.original,name)
    def readline(self,*args,**kwargs):
        require(self.reads==0,'ONE_ORIGINAL_GO_OR_EOF_READ');self.reads+=1
        if self.observe is not None:self.observe('original_readline_entered')
        value=self.original.readline(*args,**kwargs)
        require(type(value) is str,'ORIGINAL_TEXT_STDIN_RESULT')
        self.go=value=='P149_GO\n'
        return value  # EOF/invalid text is rejected by the original worker.


def pin_digest(rows):
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,allow_nan=False,sort_keys=True,
        separators=(',',':')).encode('ascii')).hexdigest()


def source_declaration(q,a,scope,control):
    """Original EOF201 provenance plus the explicitly fresh new child source.

    This is a declaration for a NEW qualification, not a reclassification of
    the old worker201 as product-ready or as a current Native byte boundary.
    """
    record=a.read_exact(q,control.READY);prior=control.declarations(record,scope)
    require(type(prior) is dict and len(prior)==201 and SELF not in prior,'ORIGINAL_EOF201_DECLARATION_UNCHANGED')
    entry=q.pin(SELF);required=scope.extend(prior,scope.pins([entry]))
    require(len(required)==202 and required[SELF]==entry,'EXPLICIT_PRODUCT_CHILD202_DECLARATION')
    for name,pin in required.items():a.exact(q.pin(name),pin,'FRESH_DECLARED_WORKER_SOURCE_BEFORE_QUALIFICATION')
    return NS(required=required,entry_pin=dict(entry),proof=dict(original_EOF_source_count=201,new_child_source_count=202,
        new_child_entry_pin=dict(entry),previous_EOF201_reclassified=False,source_declaration_only=True,
        actual_child_READY15_or_Native_or_product_qualified=False,GO_authorized=False))


def prepare_actual(worker,root,q,a,scope,pressure,loader,cap,prepared,checkpoint,*,observe=None):
    require(not prepared,'ONE_ORIGINAL_WORKER_PREPARATION');prepared.append(None)
    if observe is not None:observe('constructor_started')
    value=worker.prepare(root,q,a,scope,pressure,loader)
    if observe is not None:observe('constructor_returned')
    q.finish();checkpoint()
    if observe is not None:observe('closing_complete')
    require(q.final_fresh_hashes==len(q.snapshots) and set(q.snapshots)==set(cap.rows)
        and value.linked.state.attempts==value.linked.state.calls==0
        and value.linked.window.WINDOW.SECONDS==10
        and callable(value.linked.original_worker.__globals__.get('arguments')),
        'COMPLETE_DECLARED_CLOSING_BEFORE_ORIGINAL_READY15')
    prepared[0]=value
    return value


def product_attempt(values,root,scope,prepared,stdin,attempts):
    require(stdin.reads==1 and stdin.go and len(prepared)==1 and prepared[0] is not None and not attempts,
        'NO_PRODUCT_CREATION_BEFORE_ACTUAL_GO_OR_RETRY')
    worker=prepared[0].linked.original_worker;env=worker.__globals__
    require(callable(env.get('arguments')),'ORIGINAL_WORKER_ARGUMENTS_DEPENDENCY')
    expected=[str(root/scope.EXE_PIN['path']),*env['arguments']()]
    require(len(values)>=4 and values[0]==expected[0] and values[2] in (root,str(root))
        and values[1] in (expected,subprocess.list2cmdline(expected)),
        'ONE_EXACT_ORIGINAL_WORKER_PRODUCT_COMMAND')
    attempts.append(1)  # Creation attempt, not proof of an OS-created product.


def cleanup_sources(finder,source,meta_path):
    restored=True;closed=False
    try:
        if finder is not None:
            require(meta_path and meta_path[0] is finder,'RESTORE_EXACT_IMPORT_FINDER')
            meta_path.pop(0)
    except BaseException:restored=False
    finally:
        try:closed=source is not None and source.close() is True
        except BaseException:closed=False
    return dict(import_finder_restored=restored,inherited_source_cleanup_confirmed=closed,
        cleanup_confirmed=restored and closed)


def main():
    sys.dont_write_bytecode=True;event_handle,mapping_args=arguments(sys.argv[1:])
    import native011_inherited_source_probe_child as bridge
    root=Path(__file__).resolve().parents[2];started=time.monotonic();cpu_started=time.process_time();phase_times={}
    def stamp(phase):phase_times[phase]=dict(wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu_started)
    source=finder=cap=q=pace=None;prepared=[];attempts=[];stdin=OriginalInput(sys.stdin,stamp);primary=None;exit_code=2;clean=False
    row=dict(state='FAILED_INHERITED_PRODUCT_WORKER_NOT_ACCEPTED',accepted_count_delta=0,
        Native_or_product_acceptance_qualified=False,GO_written_by_child=False)
    def checkpoint():require(time.monotonic()-started<600,'ORIGINAL_WORKER_PREPARATION600')
    def process_audit(event,values):
        if event=='subprocess.Popen':
            require('scope' in locals_state,'PREPARATION_CANNOT_CREATE_PRODUCT')
            product_attempt(values,root,locals_state['scope'],prepared,stdin,attempts)
        elif event in ('os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            raise ValueError('PRODUCT_WORKER_ENTRY_OTHER_PROCESS_DENIED')
    locals_state={};sys.addaudithook(process_audit)
    try:
        token=bytearray()
        while len(token)<len(bridge.START):
            value=os.read(sys.stdin.fileno(),1);require(bool(value),'ACTUAL_PARENT_START_REQUIRED');token.extend(value)
        require(bytes(token)==bridge.START,'EXACT_PREPARATION_START_NOT_GO')
        stamp('actual_START_received')
        packet=json.loads(bridge.mapped_descriptor(bridge.Kernel(),mapping_args,checkpoint))
        require(type(packet) is dict and set(packet)=={'schema_version','parent_pid','sources'}
            and packet['schema_version']==bridge.SCHEMA and type(packet['parent_pid']) is int
            and packet['parent_pid']==os.getppid(),'EXACT_ACTUAL_PARENT_DESCRIPTOR')
        pace=bridge.BytePacer(checkpoint);source=bridge.SourceReader(packet['sources'],bridge.Kernel(),checkpoint,pace.reserve)
        source.admit();stamp('source_admitted')
        capabilities=bridge.bootstrap_capability(source,'tools/p09/native011_inherited_audit_reader.py',pace.reserve)
        cap=capabilities['HeldSources'](source)
        require(SELF in cap.rows and bridge.SELF in cap.rows,'NEW_CHILD_AND_BOOTSTRAP_EXPLICITLY_SOURCE_COVERED')
        finder=capabilities['SourceImports'](root,cap,pace.reserve);sys.meta_path.insert(0,finder)
        def audit_open(event,values):
            if event!='open' or not values or not isinstance(values[0],(str,bytes)):return
            path=Path(os.fsdecode(values[0])).absolute()
            if not path.is_relative_to(root):return
            name=path.relative_to(root).as_posix();mode=values[1] if len(values)>1 else None;flags=values[2] if len(values)>2 else 0
            require(name in cap.rows and not(isinstance(mode,str) and any(v in mode for v in 'wax+'))
                and not(isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)),
                'DECLARED_READONLY_PROJECT_SOURCE_OPEN_ONLY')
            cap.read_bytes(name,16*1048576,pace.reserve)
        sys.addaudithook(audit_open)
        import accept_case112_current_epoch as a,conservative_maintenance as c
        import prepared_run_closure_v1 as host,current_stored_runtime_scope as scope
        import owned_source_read_pressure as pressure,audit_evidence_io as audit
        import native011_ready_worker as entry,runtime_envelope_namespace_bundle_v1 as loader
        locals_state['scope']=scope;host.configure_host_policy(c);require(c.ROOT==root,'SAME_ORIGINAL_ROOT')
        stamp('default_imports_ready')
        Reader=capabilities['reader_type'](a.AcceptanceReader,audit,pressure,cap);q=Reader(root,checkpoint)
        for name in (SELF,bridge.SELF,entry.SELF,entry.LOADER['path'],
            'tools/p09/native011_inherited_audit_reader.py','tools/p09/native011_worker_source_inheritance.py'):q.pin(name)
        names=('tools/p09/native011_preparation.py','tools/p09/native011_worker_transport.py',
            'tools/p09/native011_zlib_binding.py','tools/p09/native011_worker_preparation.py')
        pins=[q.pin(name) for name in names]+[entry.ORIGINAL,entry.COMMON,entry.PROTOCOL,entry.PUBLISHER]
        allowed={p['path']:p for p in pins}
        class Source:
            def __init__(self,name):self.name=name
            def __fspath__(self):return os.fspath(root/self.name)
            def open(self,mode):
                require(mode=='rb' and self.name in allowed,'ONE_DECLARED_NAMESPACE_SOURCE')
                pin=allowed[self.name];before=q.maximum_parse_bytes
                try:
                    q.maximum_parse_bytes=min(before,pin['bytes']+1);actual,raw=q._read(self.name,parse=True);q._bind(self.name,actual)
                finally:q.maximum_parse_bytes=before
                a.exact(actual,pin,'FRESH_ENTIRE_NAMESPACE_SOURCE');return io.BytesIO(raw)
        class Root:
            def __fspath__(self):return os.fspath(root)
            def __truediv__(self,name):return Source(name)
        libs,_=loader.load(Root(),pins,{});worker=libs.native011_worker_preparation;protocol=libs.worker_readiness_v1
        api=libs.batch_worker_launch.family(libs.native009_worker_entry_v1,
            dict(__file__=str(root/SELF),SELF=SELF,TASK=TASK,STEP=worker.STEP))
        def prepare(actual):
            require(actual==root,'ORIGINAL_WORKER_ROOT')
            value=prepare_actual(worker,root,q,a,scope,pressure,loader,cap,prepared,checkpoint,observe=stamp)
            return value.linked,protocol
        api.main.__globals__['prepare']=prepare
        previous_argv=sys.argv;previous_stdin=sys.stdin
        try:
            sys.argv=[str(root/SELF),'--ready-handle',str(event_handle),'--task',TASK];sys.stdin=stdin
            exit_code=api.main()
        finally:sys.argv=previous_argv;sys.stdin=previous_stdin
        require(type(exit_code) is int and len(prepared)==1 and prepared[0] is not None
            and prepared[0].linked.policy.restored is True,'ORIGINAL_WORKER_POLICY_RESTORED')
        row.update(state='COMPLETED_ORIGINAL_INHERITED_WORKER_NOT_PRODUCT_ACCEPTANCE',original_worker_exit_code=exit_code,
            source_count=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            source_pin_sha256=pin_digest(q.snapshots),source_closing_before_original_READY=True,
            original_product_window_seconds=10,whole_original_worker_and_GO_Job_checks_retained=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError,ImportError,RuntimeError) as error:
        value=error.args[0] if error.args else None
        primary=value if type(value) is str and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_INHERITED_PRODUCT_WORKER_FAILURE'
    finally:
        cleanup=cleanup_sources(finder,source,sys.meta_path);clean=cleanup['cleanup_confirmed']
        if not clean and primary is None:primary='INHERITED_SOURCE_OR_IMPORT_FINDER_CLEANUP_FAILED'
        completed={} if cap is None else cap.completed
        row.update(error_code=primary,cleanup_confirmed=clean,cleanup=cleanup,original_GO_observed=stdin.go,original_input_reads=stdin.reads,
            product_creation_attempts=len(attempts),inherited_sources_closed=0 if source is None else source.summary()['inherited_source_handles_closed'],
            every_declared_source_read_at_least_twice=cap is not None and set(completed)==set(cap.rows) and all(n>=2 for n in completed.values()),
            original_default_helper_limit_changed=False,elapsed_seconds=time.monotonic()-started,phase_times=phase_times,
            source_streams=0 if cap is None else sum(cap.completed.values()),source_actual_bytes=0 if cap is None else cap.actual_bytes,
            source_ReadFile_calls=0 if cap is None else cap.actual_reads,
            capability_reserved_bytes=0 if pace is None else pace.reserved_bytes,
            reader_requested_sleep_seconds=None if q is None else q.pacer.requested_sleep_seconds,
            reader_paced_bytes=None if q is None else q.pacer.bytes_paced)
        print(json.dumps(row,ensure_ascii=True,allow_nan=False,separators=(',',':')),flush=True)
    return exit_code if primary is None and clean else 2


if __name__=='__main__':raise SystemExit(main())
