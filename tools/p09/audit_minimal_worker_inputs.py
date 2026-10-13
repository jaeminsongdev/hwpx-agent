"""P204 source-only import and selection probe; never a Job/product execution.

별도 Python 프로세스에서 import read를 관측한다. 외부 이름/환경/내용은 저장하지
않으며 subprocess와 쓰기를 차단한다. CPython hook은 보안 sandbox가 아니다.
실제 GO/Job/제품 실행은 수행하지 않고 새 worker 연결의 입력 근거만 만든다.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
SELF='tools/p09/audit_minimal_worker_inputs.py';TEST='tools/p09/tests/test_minimal_worker_input_audit.py'
SCHEMA='hwpx-agent.p09-minimal-worker-input-probe/v1'
PASS='PASS_SOURCE_ONLY_MINIMAL_WORKER_IMPORT_SELECTION_NOT_JOB_PRODUCT_OR_GATE'
MAX_EVENTS=2048;MAX_DECLARED_BYTES=8*1024*1024
REFERENCES=['https://docs.python.org/3/library/sys.html#sys.addaudithook',
    'https://docs.python.org/3/library/audit_events.html',
    'https://docs.python.org/3/library/importlib.html#importlib.machinery.SourceFileLoader']


def require(ok,code):
    if not ok:raise ValueError('P204_AUDIT_'+code)


class Trace:
    def __init__(self,target):
        self.target=target;self.phase='import';self.events=0;self.declared=0
        self.code=set();self.data=set();self.source_pins={};self.outside_code_reads=0
        self.blocked_child_events=0;self.blocked_writes=0;self.started=time.monotonic()
    def hook(self,event,args):
        if event.startswith(('subprocess.','os.exec','os.spawn','os.fork')) or event in ('os.system','_winapi.CreateProcess'):
            self.blocked_child_events+=1;raise PermissionError('P204_AUDIT_CHILD_CREATION_DENIED')
        if event.startswith('socket.') or event in ('os.remove','os.rename','os.rmdir','os.mkdir','os.link','os.symlink'):
            raise PermissionError('P204_AUDIT_MUTATION_OR_NETWORK_DENIED')
        if event!='open':return
        path,mode,flags=args
        require(type(flags) is int,'OPEN_FLAGS_TYPE')
        writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if writing:
            if self.phase=='publish' and isinstance(path,(str,bytes,os.PathLike)) and Path(os.fsdecode(path)).resolve()==self.target:
                require(bool(flags & os.O_EXCL),'EXCLUSIVE_RECEIPT_WRITE');return
            self.blocked_writes+=1;raise PermissionError('P204_AUDIT_WRITE_DENIED')
        if self.phase=='publish':return
        require(time.monotonic()-self.started<=60,'TRACE_DEADLINE')
        require(isinstance(path,(str,bytes,os.PathLike)),'TRACE_PATH_TYPE')
        source=Path(os.fsdecode(path)).resolve();self.events+=1;require(self.events<=MAX_EVENTS,'EVENT_BOUND')
        size=source.stat().st_size;self.declared+=size;require(self.declared<=MAX_DECLARED_BYTES,'DECLARED_READ_BOUND')
        if source.is_relative_to(ROOT):
            name=source.relative_to(ROOT).as_posix()
            require(not name.lower().endswith(('.exe','.pyc')),'REPO_EXE_OR_BYTECODE_READ_DENIED')
            if name.endswith('.py'):self.code.add(name)
            else:self.data.add(name)
        else:
            require(source.suffix.lower() in ('.py','.pyc','.pyd','.dll'),'OUTSIDE_DATA_READ_DENIED')
            self.outside_code_reads+=1


def own_limits():
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    for name,args,result in (
        ('GetCurrentProcess',[],w.HANDLE),('GetProcessAffinityMask',[w.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)],w.BOOL),
        ('SetProcessAffinityMask',[w.HANDLE,ctypes.c_size_t],w.BOOL),('SetPriorityClass',[w.HANDLE,w.DWORD],w.BOOL),
        ('GetPriorityClass',[w.HANDLE],w.DWORD)):
        fn=getattr(kernel,name);fn.argtypes=args;fn.restype=result
    handle=kernel.GetCurrentProcess();allowed=ctypes.c_size_t();system=ctypes.c_size_t()
    require(kernel.GetProcessAffinityMask(handle,ctypes.byref(allowed),ctypes.byref(system)),'OWN_AFFINITY_READ')
    mask=allowed.value & -allowed.value
    require(mask and kernel.SetProcessAffinityMask(handle,mask) and kernel.SetPriorityClass(handle,0x4000),'OWN_LIMIT_APPLY')
    require(kernel.GetPriorityClass(handle)==0x4000,'OWN_PRIORITY_READBACK')
    return dict(own_affinity_mask=mask,own_priority='BelowNormal',foreign_process_modified=False)


def source_imports(trace):
    loader=importlib.machinery.SourceFileLoader;old=loader.get_code
    def source_only(instance,fullname):
        path=Path(instance.path).resolve()
        if path.is_relative_to(ROOT):
            raw=instance.get_data(str(path));name=path.relative_to(ROOT).as_posix()
            if trace.phase!='publish':trace.source_pins[name]=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            return instance.source_to_code(raw,str(path))
        return old(instance,fullname)
    loader.get_code=source_only
    return old


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);ap.add_argument('--index',type=int,default=11)
    args=ap.parse_args();require(Path.cwd().resolve()==ROOT and 1<=args.run<=99,'CWD_RUN')
    target=ROOT/f'implementation/p09/evidence/runtime-r07/p09-204-minimal-worker-input-probe-run{args.run:02}.v1.json'
    require(not target.exists() and target.parent.is_dir(),'FRESH_EXISTING_RECEIPT_DIRECTORY')
    limits=own_limits();trace=Trace(target);loader=importlib.machinery.SourceFileLoader
    old=source_imports(trace);sys.addaudithook(trace.hook);owner=q=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',product_complete=False,P09_gate='OPEN',
        actual_Job_GO_or_product_child_executed=False,actual_Cargo_SQL_Hangul_executed=False,
        runtime_scope_changed=False,PC_freeze_resolved=False,audit_hook_not_security_sandbox=True,**limits)
    try:
        import minimal_r07_worker as worker
        worker.load_maintenance();trace.phase='selection';name,arguments=worker.select(args.index)
        require(trace.code=={worker.SELF,*worker.CORE_PINS} and trace.data=={worker.PARENT['path']},'EXACT_MINIMAL_REPOSITORY_READS')
        # 실제 생성 API는 호출하지 않는다. 이벤트 차단 경로만 명시적으로 확인한다.
        try:sys.audit('subprocess.Popen',None,None,None,None)
        except PermissionError:pass
        else:require(False,'CHILD_EVENT_DENIAL_MISSING')
        trace.phase='publish'
        import joined_runtime_resume_progress as previous
        import io
        import unittest
        from unittest.mock import patch
        r=previous.r;b=previous.b;c=previous.c
        context=r.observation.Context();owner=r.observation.Resources(context);owner.admit();q=r.Reader(owner,context)
        for source in (SELF,TEST,worker.SELF,worker.TEST):q.pin(source)
        sys.path.insert(0,str(ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_minimal_r07_worker','test_minimal_worker_input_audit'))
        with patch('subprocess.Popen',side_effect=AssertionError('P204_NO_CHILD')), \
                patch('subprocess.run',side_effect=AssertionError('P204_NO_CHILD')), \
                patch('threading.Thread.start',side_effect=AssertionError('P204_NO_THREAD')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        out['failed_contract_ids']=[test.id() for test,_ in checked.failures+checked.errors]
        require(checked.wasSuccessful() and checked.testsRun==20 and not checked.skipped,'CONTRACT20')
        expected,names,exe=b.baseline(q)
        require(worker.TASK_ARGS==b.core.run.original.TASK_ARGS and worker.TARGET==b.core.run.b.TARGET
            and worker.PARENT==b.run.PARENT and worker.EXE==exe,'ORIGINAL_WORKER_ARGUMENT_ENV_TARGET_PARITY')
        require(arguments==previous.v.arguments(names[args.index-1]) and name==names[args.index-1],'ORIGINAL_EXACT_SELECTION_PARITY')
        executed_pins=dict(trace.source_pins)
        # 두 core는 worker의 고정 hash loader가 확인한 후 compile했다. 바깥 loader가 기록한 것으로 표현하지 않는다.
        for source,pin in worker.CORE_PINS.items():executed_pins[source]=dict(path=source,**pin)
        require(set(executed_pins)==trace.code,'ALL_EXECUTED_REPOSITORY_SOURCES_BOUND')
        for source,pin in executed_pins.items():require(q.pin(source)==pin,'EXECUTED_SOURCE_PIN_UNCHANGED')
        require(q.pin(worker.PARENT['path'])==worker.PARENT,'READ_INVENTORY_PIN_UNCHANGED')
        q.finish();out.update(state=PASS,worker_input_contract_tests_passed=20,
            selected_public_test_name=name,selected_test_arguments=arguments,
            observed_repository_code_reads=sorted(trace.code),observed_repository_data_reads=sorted(trace.data),
            observed_source_only_import_pins=list(trace.source_pins.values()),declared_open_size_bytes=trace.declared,
            executed_repository_source_pins=list(executed_pins.values()),
            core_source_strategy='fixed-byte-hash-before-source-compile',
            declared_size_is_not_actual_bytes_consumed=True,observed_open_events=trace.events,
            outside_runtime_code_read_count=trace.outside_code_reads,blocked_child_creation_test_events=trace.blocked_child_events,
            blocked_write_events=trace.blocked_writes,repository_bytecode_read_or_write_used=False,
            runtime_import_probe_not_all_native_or_product_IO=True,original_task_target_and_selected_argv_parity=True,
            known_worker_direct_inventory_pin=worker.PARENT,official_references=REFERENCES)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,ImportError,KeyboardInterrupt) as error:
        out['error_code']=str(error) if re.fullmatch(r'P204_(AUDIT|MINIMAL)_[A-Z0-9_]+',str(error)) else 'P204_AUDIT_REDACTED_FAILURE'
    finally:
        trace.phase='publish';loader.get_code=old
        if owner is not None:
            b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
            if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
            out['metadata_observation']=r.observation.summary(owner)
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with target.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','worker_input_contract_tests_passed','error_code','resource_stop_reason')}),flush=True)
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
