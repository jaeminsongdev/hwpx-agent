import io
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

MODULE=PROTOCOL=CONNECTION=WINDOW=ENTRY=ROOT=PIN=None


class Clock:
    def __init__(self):self.value=0.
    def __call__(self):return self.value


class Event:
    def __init__(self,clock,fail_reset=False):self.clock=clock;self.handle=123;self.closed=False;self.flags=[];self.fail_reset=fail_reset
    def inheritable(self,value):
        self.flags.append(value)
        if value is False and self.fail_reset:raise OSError('SYNTHETIC_RESET_FAILURE')
    def wait(self,ms):self.clock.value+=.01;return True
    def close(self):self.closed=True


class Capture:
    def __init__(self,process):self.process=process;process.stdin.close()
    def communicate(self,timeout):return ('exact','result')


def setup(*,verify=lambda p:True,fail_reset=False,fail_launch=False):
    clock=Clock();event=Event(clock,fail_reset);pipe=io.BytesIO();process=NS(stdin=pipe,pid=123,poll=lambda:None)
    calls=[]
    def factory(*args,**kwargs):
        calls.append((args,kwargs))
        if fail_launch:raise OSError('SYNTHETIC_LAUNCH_FAILURE')
        return process
    import subprocess
    api=MODULE.connect(ROOT,PIN,WINDOW,PROTOCOL,CONNECTION,factory,Capture,subprocess,verify,lambda:None,
        event_factory=lambda:event,clock=clock)
    command=[MODULE.sys.executable,str(ROOT/'tools/p09/current_queue_successor_runtime.py'),'--owned-worker','--task',MODULE.TASK]
    kwargs=dict(cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
    return api,command,kwargs,process,event,pipe,calls,clock


class Tests(unittest.TestCase):
    def test_closed_production_arguments(self):
        self.assertEqual(ENTRY.arguments(['--ready-handle','123','--task',MODULE.TASK]),123)
        for value in ('0','-1','1.0',' 1',str(2**64)):
            with self.assertRaises(ValueError):ENTRY.arguments(['--ready-handle',value,'--task',MODULE.TASK])
        for task in ('case165-current-r008-tests','case164-current-r009-tests'):
            with self.assertRaises(ValueError):ENTRY.arguments(['--ready-handle','123','--task',task])

    def test_exact_new_command_and_only_one_inherited_event(self):
        api,command,kwargs,process,event,_,calls,_=setup();self.assertIs(api.Popen(command,**kwargs),process)
        argv=calls[0][0][0];actual=calls[0][1]
        self.assertEqual(argv,[MODULE.sys.executable,'-B',str(ROOT/MODULE.ENTRY),'--ready-handle','123','--task',MODULE.TASK])
        self.assertEqual(actual['startupinfo'].lpAttributeList,{'handle_list':[123]});self.assertIs(actual['close_fds'],True)
        self.assertEqual(event.flags,[True,False]);process.stdin.close()

    def test_other_commands_rejected_without_spawn(self):
        for index,value in ((0,'other-python'),(1,'other-entry.py'),(4,'case165-current-r008-tests')):
            api,command,kwargs,_,event,_,calls,_=setup();command[index]=value
            with self.assertRaises(ValueError):api.Popen(command,**kwargs)
            self.assertEqual(calls,[]);self.assertTrue(event.closed)

    def test_extra_or_changed_launch_options_rejected(self):
        for key,value in (('creationflags',0),('cwd',ROOT.parent),('shell',True),('startupinfo',object())):
            api,command,kwargs,_,event,_,calls,_=setup();kwargs[key]=value
            with self.assertRaises(ValueError):api.Popen(command,**kwargs)
            self.assertEqual(calls,[]);self.assertTrue(event.closed)

    def test_bad_entry_hash_rejected_before_spawn(self):
        for pin in (dict(PIN,sha256='0'*64),dict(PIN,path='tools/p09/other.py'),dict(PIN,bytes=True)):
            with self.assertRaises(ValueError):MODULE.source(ROOT,pin)

    def test_readiness_outside_original10_with_original_GO(self):
        api,command,kwargs,process,event,pipe,_,clock=setup();api.Popen(command,**kwargs)
        self.assertIsNone(api.state.started);process.stdin.write(PROTOCOL.GO);process.stdin.flush()
        self.assertEqual(pipe.getvalue(),PROTOCOL.GO);self.assertEqual(api.state.started,.01)
        capture=api.Capture(process);self.assertEqual(capture.communicate(1),('exact','result'))
        self.assertTrue(api.state.completed is not None);self.assertTrue(event.closed)
        self.assertEqual(api.state.diagnostics()['worker_readiness']['readiness_limit_seconds'],15)

    def test_wrong_owned_Job_cannot_write_GO(self):
        api,command,kwargs,process,_,pipe,_,_=setup(verify=lambda p:False);api.Popen(command,**kwargs)
        with self.assertRaises(ValueError):process.stdin.write(PROTOCOL.GO)
        self.assertEqual(pipe.getvalue(),b'');self.assertEqual(api.state.go_writes,0);process.stdin.close()

    def test_postspawn_inheritance_failure_keeps_process_but_denies_GO(self):
        api,command,kwargs,process,event,pipe,calls,_=setup(fail_reset=True)
        self.assertIs(api.Popen(command,**kwargs),process);self.assertEqual(len(calls),1)
        self.assertTrue(api.launch_state.postspawn_inheritance_error)
        with self.assertRaisesRegex(ValueError,'POSTSPAWN_EVENT_INHERITANCE'):process.stdin.write(PROTOCOL.GO)
        self.assertEqual(pipe.getvalue(),b'');self.assertEqual(api.state.go_writes,0)
        process.stdin.close();self.assertTrue(event.closed)

    def test_launch_failure_restores_event_and_cannot_retry(self):
        api,command,kwargs,_,event,_,calls,_=setup(fail_launch=True)
        with self.assertRaises(OSError):api.Popen(command,**kwargs)
        self.assertEqual(event.flags,[True,False]);self.assertTrue(event.closed)
        with self.assertRaises(ValueError):api.Popen(command,**kwargs)
        self.assertEqual(len(calls),1)

    def test_original_strict10_still_stops_capture(self):
        api,command,kwargs,process,_,_,_,clock=setup();api.Popen(command,**kwargs)
        process.stdin.write(PROTOCOL.GO);capture=api.Capture(process);clock.value+=10
        with self.assertRaisesRegex(ValueError,'STOP_STRICT_PRODUCT_WINDOW'):capture.communicate(1)

    def test_entry_run9_graph_source_and_no_diagnostic_denial_in_production(self):
        self.assertEqual(ENTRY.TASK,MODULE.TASK);self.assertEqual(ENTRY.HINT['path'].split('/')[-1],'p09-361-case165-successor-worker-bootstrap009.v3.json')
        self.assertEqual(ENTRY.CONSTRUCTION['sha256'],'2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
        self.assertFalse(getattr(ENTRY,'GO_authorized',False))

    def test_same_original_job_query_not_any_job_membership(self):
        seen=[];process=NS(_handle=123)
        def query(handle,job,member):seen.append((handle,job));member._obj.value=1;return 1
        windows=NS(k=NS(IsProcessInJob=query))
        self.assertTrue(MODULE.same_owned_job(windows,456,process,process));self.assertEqual(seen,[(123,456)])
        with self.assertRaises(ValueError):MODULE.same_owned_job(windows,None,process,process)
        with self.assertRaises(ValueError):MODULE.same_owned_job(windows,456,process,NS(_handle=123))
