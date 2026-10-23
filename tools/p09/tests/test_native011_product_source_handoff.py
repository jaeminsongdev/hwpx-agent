import io
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_product_source_handoff as m
import native011_worker_source_inheritance as inheritance
import native011_inherited_source_probe_child as bridge
import worker_readiness_v1 as protocol
import worker_readiness_connection_v1 as ready_connection
import native009_worker_launch_v1 as original_launch
import batch_worker_launch as families
import strict_product_window_v1 as strict_window
import post_product_recovery_window_v1 as recovery


class Tests(unittest.TestCase):
    def fixture(self):
        events=[];flags={11:0,22:0};failure=NS(restore=False,descriptor=False);payload=[];created=[]
        root=Path('model-root');pins={name:dict(path=name,bytes=2,sha256='0'*64) for name in ('worker.py','helper.py')}
        class Flags:
            def flags(self,handle):return flags[handle]
            def inheritable(self,handle,value):
                if failure.restore and not value:raise ValueError('MODEL_FLAG_RESTORE_FAILURE')
                flags[handle]=int(value);events.append(('flag',handle,value))
        class Kernel:
            def create_descriptor(self,raw):payload.append(raw);return 55
            def duplicate_descriptor_reader(self,handle):return 44
            def deny_descriptor_write(self,*args):pass
            def flags(self,handle):return 1
            def clear_inheritance(self,handle):pass
            def close(self,handle):return not(failure.descriptor and handle==44)
        held=NS(root=root,acquired=True,closed=False,releasing=False,stream_read_counts={name:1 for name in pins},
            files={'model':{'identity':[1,2]}},owned=[('worker.py',None,11,False),('helper.py',None,22,False)],
            api=NS(inspect=lambda handle:dict(identity=[1,handle]),pacer=NS(reserve=lambda:events.append('reserve'))))
        frame=NS(state='BEFORE_READ',registered=True,reading=False,held=held,check=lambda:events.append('frame-check'))
        coverage=NS(verify=lambda *args,**kwargs:(events.append('full-coverage') or {}))
        loans=[]
        def loan(*args,**kwargs):
            value=inheritance.SourceInheritance(*args,**kwargs,api=Flags());loans.append(value);return value
        selected_bridge=NS(**{**vars(bridge),'Kernel':Kernel})
        handoff=m.Handoff(root,pins['worker.py'],frame,pins,coverage,NS(SourceInheritance=loan),selected_bridge,
            protocol,lambda:events.append('guard'),frame_type=object)
        process=NS(pid=123,stdin=io.BytesIO(),poll=lambda:None)
        command=[m.sys.executable,'-B',str(root/'worker.py'),'--ready-handle','33','--task',m.TASK]
        startup=NS(lpAttributeList={'handle_list':[33]})
        options=dict(cwd=root,startupinfo=startup,close_fds=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
        def factory(command,**kwargs):created.append((command,kwargs));return process
        return NS(handoff=handoff,events=events,flags=flags,failure=failure,payload=payload,created=created,
            pins=pins,frame=frame,process=process,command=command,options=options,factory=factory,loans=loans)
    def gate(self,f,*,owned=True,waits=1):
        clock=[0.];waiting=[];sent=[]
        def now():clock[0]+=.001;return clock[0]
        def wait(milliseconds):waiting.append(milliseconds);return len(waiting)>=waits
        sink=NS(write=lambda value:(sent.append(value) or len(value)),flush=lambda:None,close=lambda:None)
        gate=protocol.Gate(sink,NS(wait=wait),f.process,
            lambda process:f.handoff.verify_owned(process,lambda actual:owned),f.handoff.gate_checkpoint,clock=now)
        f.handoff.bind_gate(gate);return gate,sent,waiting
    def test_construction_never_opens_handles_spawns_or_writes(self):
        f=self.fixture();self.assertEqual(f.events,[]);self.assertEqual(f.created,[])
        self.assertFalse(f.handoff.summary()['GO_authorized']);self.assertFalse(f.handoff.summary()['actual_worker_or_Native_or_product_qualified'])
    def test_exact_inherited_list_metadata_packet_and_original_flags_restored_before_return(self):
        f=self.fixture();result=f.handoff.spawn(f.factory,f.command,**f.options)
        self.assertIs(result,f.process);self.assertEqual(f.flags,{11:0,22:0})
        command,options=f.created[0];self.assertEqual(options['startupinfo'].lpAttributeList,{'handle_list':[11,22,44,33]})
        self.assertEqual(f.options['startupinfo'].lpAttributeList,{'handle_list':[33]});self.assertEqual(command[:7],f.command)
        self.assertEqual(command[7:9],['--source-mapping','44']);self.assertEqual(len(command),11)
        packet=json.loads(f.payload[0]);self.assertEqual({r['pin']['path'] for r in packet['sources']},set(f.pins))
        self.assertEqual(f.process.stdin.getvalue(),b'');self.assertTrue(f.loans[0].summary()['restore_confirmed'])
    def test_original_gate_sends_start_once_after_clock_and_job_before_original_go(self):
        f=self.fixture();f.handoff.spawn(f.factory,f.command,**f.options);gate,sent,waiting=self.gate(f,waits=4)
        self.assertEqual(gate.write(protocol.GO),len(protocol.GO));self.assertTrue(gate.ready);self.assertTrue(gate.written)
        self.assertEqual(f.process.stdin.getvalue(),bridge.START);self.assertEqual(sent,[protocol.GO])
        self.assertEqual(len(waiting),4);self.assertEqual(f.events.count('full-coverage'),2)
        self.assertTrue(f.handoff.started);self.assertFalse(f.handoff.summary()['product_GO_written_by_handoff'])
    def test_no_prewarm_before_actual_gate_attempt_and_original_guard_failure_sticks(self):
        f=self.fixture();f.handoff.spawn(f.factory,f.command,**f.options);gate,sent,waiting=self.gate(f)
        with self.assertRaisesRegex(ValueError,'NO_START_BEFORE'):f.handoff.gate_checkpoint()
        self.assertTrue(f.handoff.failed);self.assertEqual(f.process.stdin.getvalue(),b'');self.assertEqual(sent,[])
    def test_foreign_or_unassigned_job_cannot_receive_start_or_go(self):
        f=self.fixture();f.handoff.spawn(f.factory,f.command,**f.options);gate,sent,waiting=self.gate(f,owned=False)
        with self.assertRaises(ValueError):gate.write(protocol.GO)
        self.assertTrue(gate.stopped);self.assertTrue(f.handoff.failed);self.assertEqual(f.process.stdin.getvalue(),b'')
        self.assertEqual(sent,[]);self.assertEqual(waiting,[])
    def test_postspawn_restore_or_descriptor_failure_returns_child_for_cleanup_and_denies_gate(self):
        for kind in ('restore','descriptor'):
            f=self.fixture();setattr(f.failure,kind,True)
            self.assertIs(f.handoff.spawn(f.factory,f.command,**f.options),f.process);self.assertTrue(f.handoff.failed)
            gate,sent,_=self.gate(f)
            with self.assertRaises(ValueError):gate.write(protocol.GO)
            self.assertEqual(f.process.stdin.getvalue(),b'');self.assertEqual(sent,[])
    def test_prespawn_error_preserved_all_source_flags_restored_and_no_retry(self):
        f=self.fixture()
        def fail(*args,**kwargs):raise ValueError('MODEL_ORIGINAL_SPAWN_FAILURE')
        with self.assertRaisesRegex(ValueError,'MODEL_ORIGINAL_SPAWN_FAILURE'):f.handoff.spawn(fail,f.command,**f.options)
        self.assertEqual(f.flags,{11:0,22:0});self.assertTrue(f.handoff.failed);self.assertIsNone(f.handoff.process)
        with self.assertRaises(ValueError):f.handoff.spawn(f.factory,f.command,**f.options)
        self.assertEqual(f.created,[])
    def test_parent_byte_count_drift_before_start_is_never_accepted_as_cached_coverage(self):
        f=self.fixture();f.handoff.spawn(f.factory,f.command,**f.options);gate,sent,_=self.gate(f)
        f.frame.held.stream_read_counts['helper.py']=2
        with self.assertRaisesRegex(ValueError,'UNCHANGED_PARENT_READ_COUNTS'):gate.write(protocol.GO)
        self.assertTrue(gate.stopped);self.assertEqual(sent,[]);self.assertEqual(f.process.stdin.getvalue(),b'')
    def test_original_launch_and_readiness_connectors_receive_only_scoped_dependencies(self):
        f=self.fixture();calls=[];component=object();capture=object();subprocess=object();owned=lambda process:True
        checkpoint=lambda:None
        def ready(*args,**kwargs):
            calls.append((args,kwargs));return NS(Popen=lambda:None,gates=[])
        def launch(root,pin,actual_component,actual_protocol,connection,factory,actual_capture,sp,verify,check,**options):
            self.assertIs(actual_component,component);self.assertIs(actual_protocol,protocol);self.assertIs(check,checkpoint)
            return connection.connect(component,protocol,factory,capture,object(),verify,check,seconds=15)
        api=m.connect(f.handoff,NS(connect=launch),f.handoff.root,f.pins['worker.py'],component,protocol,
            NS(connect=ready),f.factory,capture,subprocess,owned,checkpoint)
        self.assertEqual(calls[0][0][-1],f.handoff.gate_checkpoint);self.assertEqual(calls[0][1],{'seconds':15})
        self.assertIs(api.source_handoff,f.handoff);self.assertEqual(f.created,[]);self.assertEqual(f.events,[])
    def test_worker_handle_integer_is_bounded_and_source_declaration_is_not_mutable_alias(self):
        f=self.fixture();f.pins['helper.py']['bytes']=999
        self.assertEqual(f.handoff.required['helper.py']['bytes'],2)
        f.command[4]='9'*21
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_WORKER_COMMAND'):
            f.handoff.spawn(f.factory,f.command,**f.options)
        self.assertEqual(f.created,[]);self.assertEqual(f.flags,{11:0,22:0})
    def test_custom_gate_method_cannot_substitute_original_readiness_or_job_checks(self):
        f=self.fixture();f.handoff.spawn(f.factory,f.command,**f.options)
        class Unsafe(protocol.Gate):
            def owned(self):return None
        gate=Unsafe(NS(write=lambda value:len(value)),NS(wait=lambda milliseconds:True),f.process,lambda process:True,lambda:None)
        with self.assertRaisesRegex(ValueError,'ONE_ORIGINAL_GATE15'):f.handoff.bind_gate(gate)
        self.assertEqual(f.process.stdin.getvalue(),b'')
    def test_original_launch_gate_and_real_input10_bodies_keep_start_outside_product_clock(self):
        import subprocess
        f=self.fixture();clock=NS(value=0.);pipe=f.process.stdin
        component=recovery.tighten_window(strict_window,(Path(__file__).resolve().parents[3]/recovery.WINDOW_PIN['path']).read_bytes())
        class Event:
            handle=33;closed=False
            def inheritable(self,value):pass
            def wait(self,milliseconds):clock.value+=.01;return True
            def close(self):self.closed=True
        event=Event()
        class Capture:
            def __init__(self,process):process.stdin.close()
            def communicate(self,timeout):clock.value+=.1;return ('model-output','')
        launch=families.family(original_launch,dict(ENTRY='worker.py',TASK=m.TASK))
        # Explicit source predicate stub is confined to this model namespace.
        # The original launch/connect, Gate and Input10 bodies are all real.
        launch.connect.__globals__['source']=lambda root,pin:self.assertEqual(pin,f.pins['worker.py'])
        api=m.connect(f.handoff,launch,f.handoff.root,f.pins['worker.py'],component,protocol,ready_connection,
            f.factory,Capture,subprocess,lambda process:process is f.process,lambda:None,
            event_factory=lambda:event,clock=lambda:clock.value)
        command=[m.sys.executable,str(f.handoff.root/'tools/p09/current_queue_successor_runtime.py'),'--owned-worker','--task',m.TASK]
        kwargs=dict(cwd=f.handoff.root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
        process=api.Popen(command,**kwargs)
        self.assertIsNone(api.state.started);self.assertEqual(pipe.getvalue(),b'')
        self.assertEqual(process.stdin.write(protocol.GO),len(protocol.GO));process.stdin.flush()
        self.assertEqual(pipe.getvalue(),bridge.START+protocol.GO);self.assertEqual(api.state.started,.01)
        capture=api.Capture(process);self.assertEqual(capture.communicate(1),('model-output',''))
        self.assertTrue(event.closed);self.assertIsNotNone(api.state.completed)
        self.assertEqual(api.state.diagnostics()['maximum_GO_to_complete_capture_seconds'],10)
        self.assertEqual(api.state.diagnostics()['worker_readiness']['readiness_limit_seconds'],15)
    def test_original_resource_failure_latches_without_start_or_go(self):
        f=self.fixture();f.handoff.spawn(f.factory,f.command,**f.options);gate,sent,_=self.gate(f)
        def fail():raise ValueError('MODEL_ORIGINAL_RESOURCE_STOP')
        f.handoff.checkpoint=fail
        with self.assertRaisesRegex(ValueError,'MODEL_ORIGINAL_RESOURCE_STOP'):gate.write(protocol.GO)
        self.assertTrue(gate.stopped);self.assertTrue(f.handoff.failed);self.assertEqual(sent,[])
        self.assertEqual(f.process.stdin.getvalue(),b'');self.assertEqual(f.flags,{11:0,22:0})
    def test_wrong_root_cannot_be_used_for_source_covered_worker_command(self):
        f=self.fixture();h=f.handoff
        with self.assertRaisesRegex(ValueError,'SAME_ACTUAL_HELD_FRAME_ROOT'):
            m.Handoff(h.root/'other',h.entry_pin,h.frame,h.required,h.coverage,h.inheritance,h.bridge,h.protocol,h.checkpoint,frame_type=object)
        self.assertEqual(f.created,[]);self.assertEqual(f.events,[])
    def test_other_process_options_are_rejected_before_native_flags_or_spawn(self):
        for options in (dict(shell=True),dict(creationflags=0),dict(close_fds=False)):
            f=self.fixture();kwargs=dict(f.options,**options)
            with self.assertRaisesRegex(ValueError,'ORIGINAL_EXPLICIT_EVENT_HANDLE_LIST'):
                f.handoff.spawn(f.factory,f.command,**kwargs)
            self.assertEqual(f.created,[]);self.assertEqual(f.flags,{11:0,22:0})
    def test_confirmed_cleanup_does_not_requery_closed_parent_frame_handles(self):
        f=self.fixture();f.handoff.spawn(f.factory,f.command,**f.options)
        before=list(f.events);f.frame.held.closed=True
        self.assertTrue(f.handoff.cleanup_handles());self.assertEqual(f.events,before)
        self.assertFalse(f.handoff.failed)
